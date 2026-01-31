"""Template for vLLM kernel optimization.

Usage:
    # Optimize fused_moe kernel
    wafer agent -t optimize-vllm \
        --args vllm_dir=/path/to/vllm \
        --args op=fused_moe \
        --args target=my-gpu-server \
        "Optimize the fused MoE kernel for better throughput"

    # With custom test and benchmark commands
    wafer agent -t optimize-vllm \
        --args vllm_dir=./vllm \
        --args op=paged_attention \
        --args test_cmd="pytest tests/kernels/attention/test_attention.py -v" \
        --args bench_cmd="python benchmarks/kernels/benchmark_paged_attention.py" \
        --json

Variables:
    - vllm_dir: Path to vLLM repository (required)
    - op: Target op to optimize (required, e.g., fused_moe, paged_attention)
    - target: Target name (default: uses default target)
    - pool: Target pool name (alternative to target)
    - test_cmd: Pytest command for correctness (auto-generated from op if not provided)
    - bench_cmd: Kernel microbenchmark command (auto-generated from op if not provided)
"""

try:
    from wafer_core.rollouts.templates import TemplateConfig
except ImportError:
    from rollouts.templates import TemplateConfig

from wafer.agent_defaults import VLLM_BASH_ALLOWLIST, VLLM_ENABLED_TOOLS

# Default test commands per op (from vLLM's test structure)
DEFAULT_TEST_CMDS = {
    "fused_moe": "pytest tests/kernels/moe/test_moe.py -v",
    "paged_attention": "pytest tests/kernels/attention/test_attention.py -v",
    "flash_attn": "pytest tests/kernels/attention/test_flash_attn.py -v",
    "flashinfer": "pytest tests/kernels/attention/test_flashinfer.py -v",
    "rms_norm": "pytest tests/kernels/core/test_layernorm.py -v -k rms",
    "layernorm": "pytest tests/kernels/core/test_layernorm.py -v",
    "rotary_embedding": "pytest tests/kernels/core/test_rotary_embedding.py -v",
    "activation": "pytest tests/kernels/core/test_activation.py -v",
    "fused_topk": "pytest tests/kernels/moe/test_fused_topk.py -v",
    "fp8_quant": "pytest tests/kernels/quantization/test_fp8_quant.py -v",
    "int8_quant": "pytest tests/kernels/quantization/test_int8_quant.py -v",
}

# Default benchmark commands per op.
# Uses pytest with --durations to measure kernel execution time.
# vLLM v0.15+ kernel benchmarks require config context, so pytest
# (which sets up fixtures) is the reliable path.
DEFAULT_BENCH_CMDS = {
    "fused_moe": "pytest tests/kernels/moe/test_moe.py --timeout=300 --durations=0 -q",
    "paged_attention": "pytest tests/kernels/attention/test_attention.py --timeout=300 --durations=0 -q",
    "rms_norm": "pytest tests/kernels/core/test_layernorm.py -k rms --timeout=120 --durations=0 -q",
    "layernorm": "pytest tests/kernels/core/test_layernorm.py --timeout=120 --durations=0 -q",
    "rotary_embedding": "pytest tests/kernels/core/test_rotary_embedding.py --timeout=120 --durations=0 -q",
    "activation": "pytest tests/kernels/core/test_activation.py --timeout=120 --durations=0 -q",
    "fused_topk": "pytest tests/kernels/moe/test_fused_topk.py --timeout=120 --durations=0 -q",
    "fp8_quant": "pytest tests/kernels/quantization/test_fp8_quant.py --timeout=120 --durations=0 -q",
    "int8_quant": "pytest tests/kernels/quantization/test_int8_quant.py --timeout=120 --durations=0 -q",
}

SYSTEM_PROMPT = """\
You are a GPU kernel optimization expert. Your task is to improve the performance
of a specific vLLM kernel while maintaining correctness.

## Target

You are optimizing the `$op` kernel in vLLM.
- vLLM directory: `$vllm_dir`
- Correctness test: `$test_cmd`
- Benchmark: `$bench_cmd`

## Workflow

1. **Understand the kernel**: Read the kernel implementation in `$vllm_dir`
   - For MoE: `vllm/model_executor/layers/fused_moe/`
   - For attention: `vllm/attention/backends/`
   - For normalization: `vllm/_custom_ops.py` or specific layer files
   - For quantization: `vllm/_custom_ops.py`

2. **Run baseline benchmark**: Establish baseline performance
   ```bash
   cd $vllm_dir && $bench_cmd
   ```

3. **Analyze and optimize**: Identify optimization opportunities
   - Memory access patterns (coalescing, shared memory usage)
   - Occupancy and register pressure
   - Algorithm improvements
   - Hardware-specific optimizations (tensor cores, etc.)

4. **Modify the kernel**: Make your changes to improve performance

5. **Validate correctness**: Run the test suite
   ```bash
   cd $vllm_dir && $test_cmd
   ```

6. **Measure improvement**: Run benchmark again and compare

7. **Iterate**: If correctness fails or performance regresses, adjust and retry

## Evaluation

Use the wafer evaluate command to run both correctness and benchmark:
```bash
wafer evaluate vllm --vllm-dir $vllm_dir --op $op \\
    --test-cmd "$test_cmd" \\
    --bench-cmd "$bench_cmd" \\
    $target_flag --json
```

## Constraints

- The correctness test MUST pass after your changes
- Focus on the specific kernel identified (`$op`)
- Document your changes and reasoning
- Your score depends on actual measured throughput improvement

## Key Metrics

- **time_us**: kernel execution time in microseconds (lower is better)
- **tflops**: teraflops achieved (higher is better)
- **bandwidth_gbps**: memory bandwidth in GB/s (higher is better)"""

template = TemplateConfig(
    # Identity
    name="optimize-vllm",
    description="Optimize vLLM kernels for better inference performance",
    # System prompt (task-specific; CLI docs appended at runtime)
    system_prompt=SYSTEM_PROMPT,
    # Tools
    tools=VLLM_ENABLED_TOOLS,
    bash_allowlist=VLLM_BASH_ALLOWLIST,
    # Model config
    model="anthropic/claude-opus-4-5-20251101",
    max_tokens=8192,
    # No thinking by default, can override with --thinking
    thinking=False,
    # Multi-turn for iterative optimization
    single_turn=False,
    # Template variables
    defaults={
        "vllm_dir": "./vllm",
        "op": "fused_moe",
        "target": "",
        "pool": "",
        "test_cmd": "",  # Auto-filled from DEFAULT_TEST_CMDS[op] if empty
        "bench_cmd": "",  # Auto-filled from DEFAULT_BENCH_CMDS[op] if empty
        "target_flag": "",  # Auto-computed: --target X or --pool Y
    },
)
