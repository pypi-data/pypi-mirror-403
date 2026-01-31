"""Template for optimizing GPU kernels.

Usage:
    wafer wevin -t optimize-kernel --args kernel=./matmul.cu "Optimize for H100"
    wafer wevin -t optimize-kernel --args kernel=./attention.cu --args target=A100 "Reduce memory bandwidth"
"""

try:
    from wafer_core.rollouts.templates import TemplateConfig
except ImportError:
    from rollouts.templates import TemplateConfig

template = TemplateConfig(
    # Identity
    name="optimize-kernel",
    description="Optimize GPU kernel implementations for performance",
    # System prompt
    system_prompt="""You are a GPU kernel optimization expert. Your task is to optimize kernel code for maximum performance.

Kernel file(s): $kernel
Target GPU: $target

Strategy:
1. Read and understand the current implementation
2. Run `wafer evaluate` to get baseline performance metrics
3. Identify optimization opportunities:
   - Memory access patterns (coalescing, bank conflicts)
   - Occupancy and register usage
   - Warp divergence
   - Instruction-level parallelism
4. Implement optimizations using edit tool
5. Re-run `wafer evaluate` to verify improvements
6. Iterate until target performance is achieved

Commands:
- `wafer evaluate --impl <file> --reference <ref> --test-cases <tests>` - Run evaluation
- `wafer evaluate --impl <file> --reference <ref> --test-cases <tests> --profile` - With NCU profiling
- `wafer remote-run "<command>"` - Run arbitrary commands on remote GPU

Output:
- Summary of optimizations applied
- Before/after performance comparison
- Explanation of key changes

IMPORTANT: Always verify correctness with wafer evaluate before claiming success.
""",
    # Tools
    tools=["read", "write", "edit", "glob", "grep", "bash"],
    bash_allowlist=[
        "wafer evaluate",
        "wafer remote-run",
        "wafer nvidia ncu",
        "wafer nvidia nsys",
        "wafer nvidia perfetto",
        "jq",
        "python -c",
    ],
    # Model config - use thinking for complex optimization reasoning
    model="anthropic/claude-opus-4-5-20251101",
    max_tokens=16384,
    # Thinking config - enabled for complex kernel optimization
    thinking=True,
    thinking_budget=10000,
    # Execution mode - multi-turn for iterative optimization
    single_turn=False,
    # Template variables
    defaults={
        "kernel": "./kernel.cu",
        "target": "H100",
    },
    # Enable skill discovery (agent can load wafer-guide, etc.)
    include_skills=True,
)
