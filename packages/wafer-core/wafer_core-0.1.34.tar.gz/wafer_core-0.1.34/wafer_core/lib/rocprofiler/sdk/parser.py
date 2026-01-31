"""Format parsing for rocprofv3 output files.

Supports CSV stats files, JSON trace files, and rocpd SQLite databases.
Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import csv
import json
import sqlite3
from pathlib import Path
from typing import Optional

from wafer_core.lib.rocprofiler.sdk.types import KernelMetrics


def parse_csv(file_path: Path) -> list[KernelMetrics]:
    """Parse rocprofv3 CSV trace file.

    CSV format (rocprofv3):
    Kind,Agent_Id,Queue_Id,Stream_Id,Thread_Id,Dispatch_Id,Kernel_Id,Kernel_Name,
    Correlation_Id,Start_Timestamp,End_Timestamp,LDS_Block_Size,Scratch_Size,
    VGPR_Count,Accum_VGPR_Count,SGPR_Count,Workgroup_Size_X,Workgroup_Size_Y,
    Workgroup_Size_Z,Grid_Size_X,Grid_Size_Y,Grid_Size_Z

    Args:
        file_path: Path to CSV trace file (*_kernel_trace.csv)

    Returns:
        List of KernelMetrics extracted from CSV

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If CSV format is invalid
    """
    kernels = []

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip non-kernel rows (rocprofv3 CSV includes different kinds of events)
            if row.get("Kind") != "KERNEL_DISPATCH":
                continue

            # Extract kernel name
            name = row.get("Kernel_Name", row.get("Name", ""))

            # Calculate duration from timestamps (in nanoseconds)
            duration_ns = None
            start_ts = row.get("Start_Timestamp")
            end_ts = row.get("End_Timestamp")
            if start_ts and end_ts:
                try:
                    duration_ns = float(end_ts) - float(start_ts)
                except (ValueError, TypeError):
                    pass

            # Extract grid and block sizes
            grid_x = row.get("Grid_Size_X", "0")
            grid_y = row.get("Grid_Size_Y", "0")
            grid_z = row.get("Grid_Size_Z", "0")
            grid_size = f"{grid_x},{grid_y},{grid_z}" if grid_x else None

            block_x = row.get("Workgroup_Size_X", "0")
            block_y = row.get("Workgroup_Size_Y", "0")
            block_z = row.get("Workgroup_Size_Z", "0")
            block_size = f"{block_x},{block_y},{block_z}" if block_x else None

            # Extract register and LDS info (rocprofv3 CSV columns)
            sgprs = None
            if "SGPR_Count" in row and row["SGPR_Count"]:
                try:
                    sgprs = int(row["SGPR_Count"])
                except (ValueError, TypeError):
                    pass

            vgprs = None
            if "VGPR_Count" in row and row["VGPR_Count"]:
                try:
                    vgprs = int(row["VGPR_Count"])
                except (ValueError, TypeError):
                    pass

            accum_vgprs = None
            if "Accum_VGPR_Count" in row and row["Accum_VGPR_Count"]:
                try:
                    accum_vgprs = int(row["Accum_VGPR_Count"])
                except (ValueError, TypeError):
                    pass

            lds = None
            if "LDS_Block_Size" in row and row["LDS_Block_Size"]:
                try:
                    lds = int(row["LDS_Block_Size"])
                except (ValueError, TypeError):
                    pass

            kernels.append(
                KernelMetrics(
                    name=name,
                    duration_ns=duration_ns,
                    grid_size=grid_size,
                    block_size=block_size,
                    registers_per_thread=sgprs,  # Use SGPRs as registers
                    lds_per_workgroup=lds,
                    vgprs=vgprs,
                    sgprs=sgprs,
                )
            )

    return kernels


def parse_json(file_path: Path) -> list[KernelMetrics]:
    """Parse rocprofv3 JSON results file.

    JSON format (rocprofv3):
    {
        "rocprofiler-sdk-tool": [{
            "kernel_dispatch": [{
                "dispatch_info": {
                    "kernel_id": 1,
                    "workgroup_size": {"x": 256, "y": 1, "z": 1},
                    "grid_size": {"x": 1024, "y": 1, "z": 1},
                    ...
                },
                "start_timestamp": ...,
                "end_timestamp": ...,
                ...
            }],
            ...
        }]
    }

    Args:
        file_path: Path to JSON results file (*_results.json)

    Returns:
        List of KernelMetrics extracted from JSON

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON format is invalid
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    kernels = []

    # Parse rocprofv3 JSON format
    tools = data.get("rocprofiler-sdk-tool", [])
    if not tools:
        return kernels

    tool_data = tools[0]

    # kernel_dispatch can be in buffer_records or directly as a key
    buffer_records = tool_data.get("buffer_records", {})
    kernel_dispatches = buffer_records.get("kernel_dispatch", [])
    if not kernel_dispatches:
        kernel_dispatches = tool_data.get("kernel_dispatch", [])

    # Build a map of kernel names from kernel symbols
    kernel_symbols = {}
    for symbol in tool_data.get("kernel_symbols", []):
        kernel_id = symbol.get("kernel_id")
        kernel_name = symbol.get("formatted_kernel_name") or symbol.get("kernel_name")
        if kernel_id is not None and kernel_name:
            kernel_symbols[kernel_id] = kernel_name

    for dispatch in kernel_dispatches:
        # Extract dispatch info
        dispatch_info = dispatch.get("dispatch_info", {})
        kernel_id = dispatch_info.get("kernel_id")

        # Get kernel name from symbols map
        name = kernel_symbols.get(kernel_id, f"kernel_{kernel_id}")

        # Calculate duration from timestamps (in nanoseconds)
        duration_ns = None
        start_ts = dispatch.get("start_timestamp")
        end_ts = dispatch.get("end_timestamp")
        if start_ts is not None and end_ts is not None:
            duration_ns = end_ts - start_ts

        # Extract grid and block sizes
        workgroup = dispatch_info.get("workgroup_size", {})
        grid = dispatch_info.get("grid_size", {})

        grid_size = f"{grid.get('x', 0)},{grid.get('y', 0)},{grid.get('z', 0)}"
        block_size = f"{workgroup.get('x', 0)},{workgroup.get('y', 0)},{workgroup.get('z', 0)}"

        # Extract LDS info
        lds = dispatch_info.get("group_segment_size")

        kernels.append(
            KernelMetrics(
                name=name,
                duration_ns=duration_ns,
                grid_size=grid_size,
                block_size=block_size,
                lds_per_workgroup=lds,
            )
        )

    return kernels


def parse_rocpd(file_path: Path) -> list[KernelMetrics]:
    """Parse rocpd SQLite database.

    rocpd is a SQLite database with profiling data generated by rocprofv3.

    Args:
        file_path: Path to rocpd database file

    Returns:
        List of KernelMetrics extracted from database

    Raises:
        FileNotFoundError: If file doesn't exist
        sqlite3.Error: If database format is invalid
    """
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()

    kernels = []

    try:
        # Query kernel info - schema may vary by ROCm version
        # Try common table/column names

        # First, check what tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        # Look for rocpd_kernel_dispatch table (ROCm 6.0+ format)
        kernel_dispatch_tables = [t for t in tables if t.startswith("rocpd_kernel_dispatch")]
        kernel_symbol_tables = [t for t in tables if t.startswith("rocpd_info_kernel_symbol")]

        if kernel_dispatch_tables and kernel_symbol_tables:
            dispatch_table = kernel_dispatch_tables[0]
            symbol_table = kernel_symbol_tables[0]

            # Join kernel_dispatch with kernel_symbol to get kernel names
            # Duration is calculated from (end - start) in nanoseconds
            query = f"""
                SELECT
                    ks.kernel_name,
                    ks.display_name,
                    (kd.end - kd.start) as duration_ns,
                    kd.grid_size_x,
                    kd.grid_size_y,
                    kd.grid_size_z,
                    kd.workgroup_size_x,
                    kd.workgroup_size_y,
                    kd.workgroup_size_z,
                    ks.sgpr_count,
                    ks.arch_vgpr_count,
                    kd.private_segment_size,
                    kd.group_segment_size
                FROM {dispatch_table} kd
                JOIN {symbol_table} ks ON kd.kernel_id = ks.id
            """
            cursor.execute(query)

            for row in cursor.fetchall():
                # Use display_name if available, otherwise kernel_name
                name = row[1] if row[1] else row[0]
                duration_ns = row[2]

                # Format grid and block sizes
                grid_size = f"{row[3]},{row[4]},{row[5]}"
                block_size = f"{row[6]},{row[7]},{row[8]}"

                kernels.append(
                    KernelMetrics(
                        name=name,
                        duration_ns=duration_ns,
                        grid_size=grid_size,
                        block_size=block_size,
                        sgprs=row[9],
                        vgprs=row[10],
                        registers_per_thread=row[9],  # Use SGPRs for registers
                        lds_per_workgroup=row[12],
                    )
                )

        # Fallback: Try legacy schema variations
        elif "kernel_info" in tables or "kernels" in tables:
            table_name = "kernel_info" if "kernel_info" in tables else "kernels"

            # Try to query with common column names
            try:
                cursor.execute(
                    f"SELECT name, duration, grid_size, block_size FROM {table_name}"
                )
                for row in cursor.fetchall():
                    kernels.append(
                        KernelMetrics(
                            name=row[0],
                            duration_ns=row[1] if row[1] else None,
                            grid_size=str(row[2]) if row[2] else None,
                            block_size=str(row[3]) if row[3] else None,
                        )
                    )
            except sqlite3.OperationalError:
                # Try simpler query
                cursor.execute(f"SELECT name, duration FROM {table_name}")
                for row in cursor.fetchall():
                    kernels.append(
                        KernelMetrics(name=row[0], duration_ns=row[1] if row[1] else None)
                    )

        # If no kernels found, try api_calls table (alternative schema)
        elif "api_calls" in tables:
            cursor.execute(
                "SELECT name, duration FROM api_calls WHERE name LIKE '%Kernel%'"
            )
            for row in cursor.fetchall():
                kernels.append(
                    KernelMetrics(name=row[0], duration_ns=row[1] if row[1] else None)
                )

    finally:
        conn.close()

    return kernels
