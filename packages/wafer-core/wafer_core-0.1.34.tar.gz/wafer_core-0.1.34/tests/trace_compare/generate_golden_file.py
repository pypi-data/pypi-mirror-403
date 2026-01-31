"""Generate golden file for trace comparison correctness tests.

Run this script to regenerate the expected output file when the implementation
changes in expected ways (e.g., adding new fields, fixing bugs).

Usage:
    python -m tests.trace_compare.generate_golden_file
"""

import json
import sys
from pathlib import Path

from wafer_core.lib.trace_compare.loader import load_trace


TRACE_PATH = Path("/root/wafer/experiments/ian/vllm-trace-compare/examples/amd_llama.json")
GOLDEN_FILE = Path(__file__).parent / "expected_output_amd_llama.json"


def main() -> None:
    """Generate golden file from trace."""
    if not TRACE_PATH.exists():
        print(f"❌ Trace file not found: {TRACE_PATH}")
        sys.exit(1)
    
    print(f"Loading trace: {TRACE_PATH.name}")
    platform, gpu, dev_props, df, patterns, layers = load_trace(TRACE_PATH, include_stacks=True)
    
    df_dict = {
        "row_count": len(df),
        "columns": list(df.columns),
        "sample_rows": df.head(100).to_dict("records"),
        "summary": {
            "total_kernels": len(df),
            "unique_ops": df["op"].nunique(),
            "unique_phases": df["phase"].nunique(),
            "total_time_us": int(df["dur_us"].sum()),
        },
    }
    
    patterns_json = {
        f"{op}_{phase}": list(pattern_set)
        for (op, phase), pattern_set in patterns.items()
    }
    
    expected_output = {
        "platform": platform,
        "gpu": gpu,
        "device_props": dev_props,
        "dataframe": df_dict,
        "patterns": patterns_json,
        "layers": {str(k): v for k, v in layers.items()},
    }
    
    with open(GOLDEN_FILE, "w") as f:
        json.dump(expected_output, f, indent=2)
    
    print(f"✅ Golden file generated: {GOLDEN_FILE}")
    print(f"   Platform: {platform}, GPU: {gpu}")
    print(f"   Kernels: {len(df):,}, Layers: {len(layers)}, Patterns: {len(patterns)}")


if __name__ == "__main__":
    main()
