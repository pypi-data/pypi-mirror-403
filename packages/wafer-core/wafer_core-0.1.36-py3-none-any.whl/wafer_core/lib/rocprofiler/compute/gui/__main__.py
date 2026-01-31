"""
CLI entry point for launching the bundled ROCprof-Compute GUI viewer.

Usage:
    python -m wafer_core.lib.rocprofiler.compute.gui <folder_path> [port]

Example:
    python -m wafer_core.lib.rocprofiler.compute.gui /path/to/results 8050
"""

import sys
from wafer_core.lib.rocprofiler.compute.gui.launcher import launch_gui_server


def main() -> int:
    """Main entry point for CLI execution."""
    if len(sys.argv) < 2:
        print("Usage: python -m wafer_core.lib.rocprofiler.compute.gui <folder_path> [port]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print("  python -m wafer_core.lib.rocprofiler.compute.gui /path/to/results 8050", file=sys.stderr)
        return 1

    folder_path = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8050

    print(f"Launching ROCprof-Compute GUI viewer...", file=sys.stderr)
    print(f"Folder: {folder_path}", file=sys.stderr)
    print(f"Port: {port}", file=sys.stderr)
    print(f"", file=sys.stderr)

    # Launch in foreground (blocking)
    result = launch_gui_server(folder_path, port, background=False)

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
