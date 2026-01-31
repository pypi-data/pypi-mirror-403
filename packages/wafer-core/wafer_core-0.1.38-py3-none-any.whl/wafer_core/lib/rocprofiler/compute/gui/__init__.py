"""
ROCprof-Compute GUI Viewer

This module contains the GUI viewer for AMD ROCm profiling results.
Original implementation by Advanced Micro Devices, Inc.

The GUI viewer reads and visualizes profiling data collected by rocprof-compute.
It does NOT require AMD GPU or ROCm runtime - it only reads CSV/YAML result files.

Technology Stack:
- Dash (web framework)
- Plotly (charting)
- Pandas (data processing)

Original License: MIT
Copyright (c) 2021 - 2025 Advanced Micro Devices, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

Packaged and maintained by Wafer team for cross-platform GPU profiling visualization.
"""

from wafer_core.lib.rocprofiler.compute.gui.launcher import launch_gui_server

__all__ = ["launch_gui_server"]
