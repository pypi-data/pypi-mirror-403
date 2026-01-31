# Wafer CLI Guide

GPU development primitives for LLM agents.

## Quick Start: Cloud GPU (No Setup)

Run code on cloud GPUs instantly with workspaces:

```bash
wafer login                              # One-time auth
wafer workspaces create dev --gpu B200   # Create workspace (NVIDIA B200)
wafer workspaces exec dev -- python -c "import torch; print(torch.cuda.get_device_name(0))"
wafer workspaces sync dev ./my-project   # Sync files
wafer workspaces exec dev -- python train.py
```

**Available GPUs:**

- `MI300X` - AMD Instinct MI300X (192GB HBM3, ROCm)
- `B200` - NVIDIA Blackwell B200 (180GB HBM3e, CUDA) - default

## Documentation Lookup

Answer GPU programming questions from indexed documentation.

```bash
# Download corpus (one-time)
wafer corpus download cuda
wafer corpus download cutlass
wafer corpus download hip

# Query documentation
wafer agent -t ask-docs --corpus cuda "What is warp divergence?"
wafer agent -t ask-docs --corpus cutlass "What is a TiledMma?"
```

## Trace Analysis

Analyze performance traces from NCU, NSYS, or PyTorch profiler.

```bash
# AI-assisted analysis
wafer agent -t trace-analyze --args trace=./profile.ncu-rep "Why is this kernel slow?"
wafer agent -t trace-analyze --args trace=./trace.json "What's the bottleneck?"

# Direct trace queries (PyTorch/Perfetto JSON)
wafer nvidia perfetto tables trace.json
wafer nvidia perfetto query trace.json \
  "SELECT name, dur/1e6 as ms FROM slice WHERE cat='kernel' ORDER BY dur DESC LIMIT 10"

# NCU/NSYS analysis
wafer nvidia ncu analyze profile.ncu-rep
wafer nvidia nsys analyze profile.nsys-rep
```

## Kernel Evaluation

Test kernel correctness and measure speedup against a reference.

```bash
# Using workspaces (no target setup required):
wafer workspaces create dev --gpu B200
wafer workspaces exec --sync ./my-kernel dev -- python test_kernel.py

# Or using configured targets (for your own hardware):
wafer evaluate make-template ./my-kernel
wafer evaluate \
  --impl ./my-kernel/kernel.py \
  --reference ./my-kernel/reference.py \
  --test-cases ./my-kernel/test_cases.json \
  --target <target-name>
```

For target setup, see `wafer config targets --help`.

## Kernel Optimization (AI-assisted)

Iteratively optimize a kernel with evaluation feedback.

```bash
wafer agent -t optimize-kernel \
  --args kernel=./my_kernel.cu \
  --args target=H100 \
  "Optimize this GEMM for memory bandwidth"
```

## Workspaces

Cloud GPU environments with no setup required.

**Available GPUs:**

- `MI300X` - AMD Instinct MI300X (192GB HBM3, ROCm)
- `B200` - NVIDIA Blackwell B200 (180GB HBM3e, CUDA) - default

```bash
wafer workspaces create dev --gpu B200 --wait     # NVIDIA B200
wafer workspaces create amd-dev --gpu MI300X      # AMD MI300X
wafer workspaces list                             # List all
wafer workspaces sync dev ./project               # Sync files
wafer workspaces exec dev -- ./run.sh             # Run commands
wafer workspaces ssh dev                          # Interactive SSH
wafer workspaces delete dev                       # Cleanup
```

See `wafer workspaces --help` for details.

## Command Reference

```bash
wafer corpus list|download|path   # Manage documentation corpora
wafer workspaces                  # Cloud GPU environments (no setup)
wafer evaluate                    # Test kernel correctness/performance
wafer nvidia ncu|nsys|perfetto    # NVIDIA profiling tools
wafer amd isa|rocprof-compute     # AMD profiling tools
wafer agent -t <template>         # AI-assisted workflows
wafer config targets              # Configure your own GPU targets
```
