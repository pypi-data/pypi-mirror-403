# Trace Compare Performance

## Current Performance (v2 - 4.6x speedup)

| Trace Size | Load Time |
|------------|-----------|
| 919MB | ~17s |
| 1.1GB | ~22s |
| 2GB | ~38s |

## Implemented Optimizations

1. **orjson** - Rust-based JSON parser (1.4x faster than stdlib)
2. **Binary search for phases** - O(log n) instead of O(n) per kernel
3. **CPU op caching by kernel name** - 779k lookups → 48 lookups
4. **Pre-computed parent chains** - O(1) instead of O(50) walk per kernel
5. **String interning** - Reduced memory, faster dict lookups

## Next Optimizations (Target: <5s)

### High Impact

#### 1. Remove Pandas DataFrame (~3-5s savings)

The DataFrame is only used for groupby aggregations. Replace with dict-based aggregation during kernel processing:

```python
# Current: Build DataFrame, then groupby
df = pd.DataFrame(kernel_data)  # ~3s for 810k rows
by_op = df.groupby("op").agg(...)  # ~2s

# Better: Aggregate during processing
by_op = defaultdict(lambda: {"total_us": 0, "count": 0, "kernels": []})
for kernel in kernels:
    by_op[kernel["op"]]["total_us"] += kernel["dur_us"]
    by_op[kernel["op"]]["count"] += 1
```

**Estimated savings**: 3-5s (DataFrame creation + groupby overhead)

#### 2. Lazy/Streaming JSON Parsing (~2-3s savings)

Don't parse the entire JSON upfront. Use ijson or orjson's streaming mode to process events as they're parsed:

```python
import ijson

def stream_events(file_path):
    with open(file_path, "rb") as f:
        for event in ijson.items(f, "traceEvents.item"):
            yield event
```

**Estimated savings**: 2-3s (avoid holding full JSON in memory)

#### 3. Parallel Processing (~40% savings)

Kernel classification and stack resolution are embarrassingly parallel:

```python
from concurrent.futures import ProcessPoolExecutor

# Split kernel_events into chunks
chunks = [kernel_events[i::8] for i in range(8)]

with ProcessPoolExecutor(max_workers=8) as pool:
    results = pool.map(process_chunk, chunks)
```

**Estimated savings**: 40% of processing time with 8 cores

### Medium Impact

#### 4. Skip Unused Data

Most use cases don't need full `python_stack` lists. Only resolve what's actually needed:

```python
def load_trace(file_path, include_full_stacks=False):
    # Only compute full stacks when explicitly requested
```

#### 5. Memory-Mapped File Reading

Use mmap for faster file I/O on large traces:

```python
import mmap

with open(file_path, "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    trace = orjson.loads(mm)
```

#### 6. Pre-compiled Regex for Classification

Compile regex patterns once at module load instead of per-call.

### Long-term (Target: <1s repeat loads)

#### 7. Binary Index Format

Create a pre-processed `.trace.idx` file on first load:

```python
# First load: Parse JSON (~17s), save index
# Subsequent loads: Load index (<1s)

def load_trace_with_index(trace_path):
    index_path = trace_path.with_suffix(".trace.idx")
    if index_path.exists() and is_valid(index_path, trace_path):
        return load_index(index_path)  # <1s
    
    data = load_trace(trace_path)  # ~17s
    save_index(data, index_path)
    return data
```

#### 8. Rust Extension (PyO3)

Port hot paths to Rust for 10-50x speedup:
- JSON event iteration
- Stack resolution
- Kernel classification

## Profiling Commands

```bash
# Run benchmark
cd packages/wafer-core
python -m tests.trace_compare.benchmark_trace_compare

# Profile with py-spy
py-spy record -o profile.svg -- python -c "
from wafer_core.lib.trace_compare.loader import load_trace
load_trace('/path/to/trace.json')
"
```

## Test Commands

```bash
# Run correctness tests
pytest tests/trace_compare/test_trace_compare_correctness.py -v

# Regenerate golden file (after expected changes)
python -m tests.trace_compare.generate_golden_file
```
