# Autotuner Benchmarking Best Practices

## Ensuring Consistent Results

GPU benchmarking can have significant variance due to factors like thermal throttling, clock frequency changes, background processes, and measurement noise. Here's how to get more reliable results with the autotuner.

## 1. Multiple Runs Per Configuration

**Problem:** Running each configuration only once can lead to inconsistent results between sweeps.

**Solution:** Use the `trials_per_config` parameter to run each configuration multiple times:

```json
{
  "name": "My Sweep",
  "search_space": { ... },
  "command": "...",
  "metrics": { ... },
  "trials_per_config": 5,
  ...
}
```

This will:
- Run each parameter configuration 5 times
- Allow you to see variance in the UI (view all runs in the trials table)
- Make your results more statistically sound

**Recommended values:**
- `trials_per_config: 3` - Quick sweeps, moderate confidence
- `trials_per_config: 5` - Good balance (recommended)
- `trials_per_config: 10+` - High confidence, publication-quality results

## 2. Benchmark Script Best Practices

Your benchmark script (the command you're running) should follow these patterns:

### Warmup Runs
Always run your kernel/code multiple times before timing:

```python
# Bad: Cold start
result = run_kernel()
time_it()

# Good: Warmed up
for _ in range(3):
    run_kernel()  # Warmup to stabilize GPU clocks

# Now time it
for _ in range(10):
    time_it(run_kernel())
```

###  Multiple Iterations & Statistical Reporting

Take multiple measurements and report statistics:

```python
times = []
for _ in range(50):
    start = time()
    run_kernel()
    sync_gpu()
    times.append(time() - start)

# Report min (best case - common in GPU benchmarking)
print(f"Duration (min): {min(times):.3f} ms")

# Also helpful: report variance
print(f"Duration (avg): {statistics.mean(times):.3f} ms")
print(f"Std Dev: {statistics.stdev(times):.3f} ms")
```

The autotuner will parse these metrics if you configure them in your `metrics` patterns.

### Fixed Random Seeds

Use fixed seeds for reproducibility:

```python
# Ensures same input data across runs
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
```

## 3. Environmental Factors (Advanced)

For maximum consistency, consider these factors:

### GPU Clock Locking (Requires Root)
```bash
# Lock GPU clocks to max (NVIDIA)
sudo nvidia-smi -pm 1  # Enable persistence mode
sudo nvidia-smi -lgc 1410,1410  # Lock GPU clocks (adjust for your GPU)
```

⚠️ This requires root and may not be available in all environments.

### System Isolation
- Close other GPU applications
- Run sweeps when system is idle
- Consider running multiple sweeps at different times and comparing

## 4. Interpreting Results

When using `trials_per_config > 1`:

1. **Look at all runs**: In the UI, you'll see multiple trials for the same config. Check if variance is acceptable.

2. **Check coefficient of variation (CV)**: If your script reports it:
   - CV < 5%: Excellent consistency
   - CV 5-10%: Good, acceptable
   - CV > 10%: High variance, consider investigating

3. **Compare best-of-N**: The autotuner considers all trials when ranking. Configs that are consistently fast will rank higher than those with occasional good runs.

## Example Config

See `experiments/ian/autotuner/cuda_matmul/sweep_config_with_repeats.json` for a complete example using multiple runs.

## Summary

**Minimum for reliable results:**
- ✅ Add `"trials_per_config": 5` to your config
- ✅ Ensure your benchmark script does warmup runs
- ✅ Take multiple measurements (50+) within each trial

**For publication-quality results:**
- All of the above, plus:
- Lock GPU clocks if possible
- Run `trials_per_config: 10` or more
- Run entire sweeps multiple times on different days
- Report confidence intervals
