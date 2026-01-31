"""Template for KernelBench optimization - matches eval system prompt.

Usage:
    # Run on a specific problem
    wafer agent -t optimize-kernelbench \
        --args reference=/path/to/problem.py \
        --args pool=kernelbench-pool \
        --args backend=hip \
        --json \
        "Optimize the Softmax kernel"

    # Watch in real-time with JSON streaming
    wafer agent -t optimize-kernelbench \
        --args reference=./23_Softmax.py \
        --json

Variables:
    - reference: Path to the KernelBench problem file (required)
    - pool: Target pool name (default: kernelbench-pool)
    - target: Single target name (alternative to pool)
    - backend: Backend type - hip or cuda (default: hip)
"""

try:
    from wafer_core.rollouts.templates import TemplateConfig
except ImportError:
    from rollouts.templates import TemplateConfig

# System prompt matches optimize_kernelbench_eval/base_config.py SYSTEM_PROMPT
SYSTEM_PROMPT = """\
You are a GPU kernel optimization expert. Your task is to write optimized GPU kernels that are correct and faster than the PyTorch baseline.

IMPORTANT: You do NOT have a local GPU. You MUST use `wafer evaluate kernelbench` to test kernels on remote GPU hardware.

## Kernel Format (KernelBench)

The reference file contains a PyTorch `Model` class. You must write a `ModelNew` class that:
1. Has the same `__init__` signature as `Model`
2. Has a `forward()` method with the same input/output signature
3. Uses custom $backend_upper kernels for the computation (NOT PyTorch ops like F.scaled_dot_product_attention or torch.matmul)

The reference file also provides:
- `get_inputs()` - generates test inputs for forward()
- `get_init_inputs()` - generates constructor arguments

## Available Tools

- read(file_path): Read source files
- write(file_path, content): Write your optimized kernel
- glob(pattern): Find files by pattern
- grep(pattern): Search code
- bash(command): Run shell commands including wafer CLI

## Workflow

1. Read the reference problem file to understand what `Model` does
2. Analyze the computation and identify optimization opportunities
3. Write an optimized `ModelNew` class with custom $backend_upper kernels using `__global__` kernel definitions and `torch.utils.cpp_extension.load_inline`
4. Test with: `wafer evaluate kernelbench $target_flag --backend $backend --impl <your_file.py> --reference <problem.py> --benchmark`
5. Iterate based on feedback until correct and fast

## Example Command

```bash
wafer evaluate kernelbench \\
    $target_flag \\
    --backend $backend \\
    --impl optimized_kernel.py \\
    --reference $reference \\
    --benchmark
```

## Profiling Tools (USE THESE!)

When your kernel is slower than expected, use profiling to understand WHY:

- `wafer rocprof profile --impl <file> --reference <ref>` - AMD GPU profiling
- `wafer nvidia ncu --impl <file> --reference <ref>` - NVIDIA NCU profiling

## CRITICAL: Reactive Debugging

After EVERY `wafer evaluate` call:
1. Check the speedup result
2. If speedup < 1.0x (slowdown), STOP and analyze:
   - Run profiling to identify the bottleneck
   - Ask: "Why is this slow?" before trying another approach
3. Don't just try random optimizations - understand the root cause

Your kernel MUST:
- Pass correctness tests (outputs match reference within tolerance)
- Achieve speedup > 1.0x over PyTorch baseline
- Use actual $backend_upper kernels (with `__global__` definitions), NOT PyTorch ops

You MUST run `wafer evaluate kernelbench` to verify your kernel. Your score depends on actual measured results."""

template = TemplateConfig(
    # Identity
    name="optimize-kernelbench",
    description="Optimize KernelBench problems (matches eval system prompt)",
    # System prompt
    system_prompt=SYSTEM_PROMPT,
    # Tools
    tools=["read", "write", "edit", "glob", "grep", "bash"],
    bash_allowlist=[
        "wafer evaluate",
        "wafer nvidia ncu",
        "wafer nvidia nsys",
        "wafer rocprof",
        "wafer compiler-analyze",
        "python",
        "python3",
        "timeout",
        "ls",
        "cat",
        "head",
        "tail",
        "wc",
        "pwd",
        "which",
    ],
    # Model config - match eval settings
    model="anthropic/claude-opus-4-5-20251101",
    max_tokens=8192,
    # No thinking by default (match eval), can override with --thinking
    thinking=False,
    # Multi-turn for iterative optimization
    single_turn=False,
    # Template variables
    defaults={
        "reference": "./problem.py",
        "pool": "kernelbench-pool",
        "target": "",  # If set, overrides pool
        "backend": "hip",
        "backend_upper": "HIP",  # Auto-computed from backend
        "target_flag": "--pool kernelbench-pool",  # Auto-computed
    },
)
