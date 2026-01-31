"""
Launcher for ROCprof-Compute bundled GUI viewer.

This module provides a Python API to launch the bundled ROCprof-Compute GUI viewer
without requiring the external rocprof-compute binary to be installed.
"""

import multiprocessing
import os
import sys
import threading
from pathlib import Path
from typing import Optional

from wafer_core.lib.rocprofiler.compute.types import LaunchResult


def _run_dash_server(
    folder_path: str, port: int, supported_archs: dict
) -> None:  # pragma: no cover
    """
    Run Dash server in subprocess/thread.
    This is the entry point for multiprocessing.Process.
    """
    # Import here to avoid loading dash at module import time
    import argparse

    from wafer_core.lib.rocprofiler.compute.gui.analysis_webui import webui_analysis
    from wafer_core.lib.rocprofiler.compute.gui.utils.logger import setup_console_handler

    # Setup logging (required for AMD's code - adds custom TRACE level)
    setup_console_handler()

    # Set up config directory path (bundled analysis configs)
    import wafer_core.lib.rocprofiler.compute.gui
    gui_module_path = Path(wafer_core.lib.rocprofiler.compute.gui.__file__).parent
    config_dir = gui_module_path / "rocprof_compute_soc" / "analysis_configs"

    # Create argparse namespace to match rocprof-compute's expected args
    # This includes ALL possible args that might be accessed by the GUI code
    args = argparse.Namespace(
        # Primary args
        path=[[folder_path]],  # rocprof-compute expects nested list
        mode="analyze",  # Required for SoC to create roofline_obj
        gui=True,
        port=port,
        verbose=0,
        config_dir=config_dir,

        # Display/formatting args
        time_unit="ns",  # Display time unit (s, ms, us, ns)
        normal_unit="per_kernel",  # Default normalization unit
        decimal=2,  # Decimal places for display
        max_stat_num=10,  # Maximum number of stats shown in "Top Stats" tables
        kernel_verbose=5,  # Kernel name verbose level (1-5, default: 5)
        cols=None,  # Column indices to display

        # Filter args
        filter_metrics=None,
        gpu_id=None,
        gpu_kernel=None,
        gpu_dispatch_id=None,
        nodes=None,
        filter_blocks={},

        # Roofline/profiling args
        roofline_data_type=["FP32"],  # Default roofline data type (must be a list)
        mem_level="ALL",  # Memory level
        no_roof=True,  # Set to True for GUI mode (not standalone roofline)
        roof_only=False,

        # PC sampling args
        pc_sampling_method="stochastic",  # PC sampling method
        pc_sampling_interval=1048576,  # PC sampling interval
        pc_sampling_sorting_type="offset",  # PC sampling sorting type (offset or count)

        # Mode flags
        list_metrics=None,
        list_stats=None,
        list_nodes=None,
        spatial_multiplexing=False,
        specs_correction=False,  # Disable specs correction for GUI (doesn't need SoC objects)
        debug=False,  # Debug single metric
        tui=False,
        random_port=False,  # Random port selection (only used in GUI mode)

        # Output args
        output_file=None,
        format_rocprof_output="csv",

        # Trace args
        hip_trace=False,
        kokkos_trace=False,

        # Additional args (set to defaults to avoid AttributeError)
        sort="kernels",
        join_type="grid",
        kernel_names=False,
        dependency=False,
        specs=False,
        quiet=False,
        report_diff=0,
    )

    try:
        # Initialize GUI analyzer
        analyzer = webui_analysis(args, supported_archs)

        # Read sysinfo to get actual architecture and specs BEFORE initializing runs
        import pandas as pd
        import importlib
        from wafer_core.lib.rocprofiler.compute.gui.utils.specs import generate_machine_specs

        sysinfo_path = Path(folder_path) / "sysinfo.csv"
        if sysinfo_path.exists():
            sys_info_df = pd.read_csv(sysinfo_path)
            sys_info = sys_info_df.to_dict("list")
            sys_info = {key: value[0] for key, value in sys_info.items()}
            arch = sys_info.get("gpu_arch", "gfx942")

            # Generate machine specs from actual sysinfo
            mspec = generate_machine_specs(args, sys_info)

            # Create proper SoC object for the actual architecture
            soc_objects = {}
            try:
                soc_module = importlib.import_module(
                    f"wafer_core.lib.rocprofiler.compute.gui.rocprof_compute_soc.soc_{arch}"
                )
                soc_class = getattr(soc_module, f"{arch}_soc")
                soc_objects[arch] = soc_class(args, mspec)
            except (ImportError, AttributeError) as e:
                # Fallback to minimal SoC if architecture-specific class not found
                from types import SimpleNamespace
                minimal_soc = SimpleNamespace()
                minimal_soc._mspec = mspec
                soc_objects[arch] = minimal_soc
        else:
            # No sysinfo found, create minimal SoCs for all supported architectures
            from types import SimpleNamespace
            soc_objects = {}
            for arch_name in supported_archs.keys():
                minimal_soc = SimpleNamespace()
                minimal_soc._mspec = SimpleNamespace()
                soc_objects[arch_name] = minimal_soc

        # Set SoC objects BEFORE initializing runs
        analyzer.set_soc(soc_objects)

        # Sanitize inputs (validates paths and workload directory)
        analyzer.sanitize()

        # Load and preprocess data
        # NOTE: pre_processing() internally calls initalize_runs(), so we don't call it separately
        analyzer.pre_processing()

        # Get input filters from loaded data
        # IMPORTANT: sanitize() converts paths to absolute, so we must use the sanitized path
        dest_dir = args.path[0][0]  # Get the absolute path set by sanitize()

        # Check if data was loaded successfully
        if dest_dir not in analyzer._runs:
            raise RuntimeError(f"Failed to load profiling data from {dest_dir}")

        run_data = analyzer._runs[dest_dir]
        if run_data is None:
            raise RuntimeError(f"Run data is None for {dest_dir}")

        if run_data.sys_info is None or run_data.sys_info.empty:
            raise RuntimeError(f"System info is missing or empty for {dest_dir}")

        input_filters = {
            "kernel": run_data.filter_kernel_ids,
            "gpu": run_data.filter_gpu_ids,
            "dispatch": run_data.filter_dispatch_ids,
            "normalization": args.roofline_data_type,
            "top_n": None,
        }

        # Build layout and run
        # Get the arch for the current workload
        workload_arch = run_data.sys_info.iloc[0]["gpu_arch"]

        if workload_arch not in analyzer._arch_configs:
            raise RuntimeError(f"Architecture config not found for {workload_arch}")

        arch_config = analyzer._arch_configs[workload_arch]
        analyzer.build_layout(input_filters, arch_config)

        # Configure Flask server for CORS (needed for VS Code webview access)
        analyzer.app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        @analyzer.app.server.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            # Add header for private network access
            response.headers['Access-Control-Allow-Private-Network'] = 'true'
            return response

        # Run Dash server (blocking call)
        analyzer.app.run(debug=False, host="0.0.0.0", port=port)
    except Exception as e:
        import traceback
        print(f"Error launching GUI server: {e}", file=sys.stderr)
        traceback.print_exc()
        raise


def launch_gui_server(
    folder_path: str, port: int = 8050, background: bool = True
) -> LaunchResult:
    """
    Launch the bundled ROCprof-Compute GUI viewer.

    This function launches a Dash web server to visualize rocprof-compute profiling results.
    The GUI viewer is GPU-agnostic and only reads CSV/YAML data files.

    Args:
        folder_path: Path to folder containing rocprof-compute results
                    (must contain sysinfo.csv, pmc_kernel_top.csv, etc.)
        port: Port to run the web server on (default: 8050)
        background: If True, run server in background process (default: True)
                   If False, run in foreground (blocking)

    Returns:
        LaunchResult with success status, URL, and error info

    Example:
        >>> result = launch_gui_server("/path/to/results", port=8050)
        >>> if result.success:
        ...     print(f"GUI available at {result.url}")
    """
    # Validate folder path
    folder = Path(folder_path).absolute()
    if not folder.exists():
        return LaunchResult(
            success=False,
            command=None,
            url=None,
            port=port,
            folder=str(folder),
            error=f"Results folder not found: {folder}",
        )

    # Check for required files
    required_files = ["sysinfo.csv"]
    missing_files = [f for f in required_files if not (folder / f).exists()]
    if missing_files:
        return LaunchResult(
            success=False,
            command=None,
            url=None,
            port=port,
            folder=str(folder),
            error=f"Missing required files: {', '.join(missing_files)}",
        )

    # Load supported architectures (minimal set for GUI viewer)
    # The GUI doesn't need full arch specs, just needs to know supported archs
    # Must match the arch folders in analysis_configs directory
    supported_archs = {
        "gfx908": {"name": "MI100"},
        "gfx90a": {"name": "MI200 Series"},
        "gfx940": {"name": "MI300 Series"},
        "gfx941": {"name": "MI300 Series"},
        "gfx942": {"name": "MI300 Series"},
        "gfx950": {"name": "MI350 Series"},
    }

    url = f"http://0.0.0.0:{port}"

    try:
        if background:
            # Run in background process
            process = multiprocessing.Process(
                target=_run_dash_server,
                args=(str(folder), port, supported_archs),
                daemon=True,
            )
            process.start()

            return LaunchResult(
                success=True,
                command=["python", "-m", "dash"],  # Conceptual command
                url=url,
                port=port,
                folder=str(folder),
                error=None,
            )
        else:
            # Run in foreground (blocking)
            _run_dash_server(str(folder), port, supported_archs)

            # This return is only reached if server exits
            return LaunchResult(
                success=True,
                command=["python", "-m", "dash"],
                url=url,
                port=port,
                folder=str(folder),
                error=None,
            )

    except Exception as e:
        return LaunchResult(
            success=False,
            command=None,
            url=None,
            port=port,
            folder=str(folder),
            error=f"Failed to launch GUI server: {str(e)}",
        )


def launch_gui_server_threaded(folder_path: str, port: int = 8050) -> LaunchResult:
    """
    Launch GUI server in a background thread (alternative to process-based).

    This is useful when multiprocessing is problematic (e.g., on macOS with spawn method).

    Args:
        folder_path: Path to folder containing rocprof-compute results
        port: Port to run the web server on

    Returns:
        LaunchResult with success status and URL
    """
    folder = Path(folder_path).absolute()
    if not folder.exists():
        return LaunchResult(
            success=False,
            command=None,
            url=None,
            port=port,
            folder=str(folder),
            error=f"Results folder not found: {folder}",
        )

    supported_archs = {
        "gfx908": {"name": "MI100"},
        "gfx90a": {"name": "MI200 Series"},
        "gfx940": {"name": "MI300 Series"},
        "gfx941": {"name": "MI300 Series"},
        "gfx942": {"name": "MI300 Series"},
        "gfx950": {"name": "MI350 Series"},
    }

    url = f"http://0.0.0.0:{port}"

    try:
        thread = threading.Thread(
            target=_run_dash_server,
            args=(str(folder), port, supported_archs),
            daemon=True,
        )
        thread.start()

        return LaunchResult(
            success=True,
            command=["python", "-m", "dash"],
            url=url,
            port=port,
            folder=str(folder),
            error=None,
        )
    except Exception as e:
        return LaunchResult(
            success=False,
            command=None,
            url=None,
            port=port,
            folder=str(folder),
            error=f"Failed to launch GUI server: {str(e)}",
        )
