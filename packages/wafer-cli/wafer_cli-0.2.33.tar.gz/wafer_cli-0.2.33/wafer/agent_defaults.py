"""Shared agent defaults for kernel optimization tasks.

Single source of truth for bash allowlists and enabled tools used by both:
- CLI templates (apps/wafer-cli/wafer/templates/*.py)
- Eval configs (research/evals/*_eval/*.py)

Import from here instead of defining your own copy.
"""

from __future__ import annotations

# Tools available to the agent (coding environment tools)
ENABLED_TOOLS: list[str] = ["read", "write", "edit", "glob", "grep", "bash"]

# vLLM-specific tools (same as ENABLED_TOOLS for now)
VLLM_ENABLED_TOOLS: list[str] = ["read", "write", "edit", "glob", "grep", "bash"]

# Bash commands allowed for kernel optimization agents.
# Uses prefix matching — "wafer evaluate" also allows "wafer evaluate kernelbench".
KERNELBENCH_BASH_ALLOWLIST: list[str] = [
    # Kernel evaluation
    "wafer evaluate",
    # Profiling — AMD
    "wafer amd rocprof-compute",
    "wafer amd rocprof-sdk",
    "wafer amd rocprof-systems",
    # Profiling — NVIDIA
    "wafer nvidia ncu",
    "wafer nvidia nsys",
    # Analysis
    "wafer compiler-analyze",
    # Sub-agents
    "wafer agent -t ask-docs",
    # General utilities
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
]

# Tools available to aiter optimization agents (full coding environment)
AITER_ENABLED_TOOLS: list[str] = ["read", "write", "edit", "glob", "grep", "bash"]

# System prompt for aiter optimization (shared between eval and template)
# Uses {op_name}, {test_file}, {target_flag} placeholders
AITER_SYSTEM_PROMPT = """\
You are a GPU kernel optimization expert specializing in AMD MI300X and the aiter library.

## Context

aiter (ROCm/aiter) is AMD's centralized repository for high-performance AI operators.
Operators are implemented using Triton kernels, Composable Kernel (CK), or HIP/ROCm.

Each operator has a test in `op_tests/test_{{op}}.py` that validates correctness and
measures performance against a reference implementation.

## Your Task

1. **Understand the operator**: Read the test file and trace imports to find implementation
2. **Establish baseline**: Run the evaluation to measure current performance
   ```bash
   # Quick check with one shape (fast iteration)
   wafer evaluate aiter --aiter-dir . --cmd "python op_tests/test_{{op}}.py --mnk 128,32,8192" {target_flag}

   # Full test suite (final validation)
   wafer evaluate aiter --aiter-dir . --cmd "python op_tests/test_{{op}}.py" {target_flag}
   ```
3. **Identify optimizations**: Look for memory access patterns, occupancy, instruction selection
4. **Implement changes**: Modify the operator to improve performance
5. **Validate**: Re-run evaluation to verify correctness and measure speedup
6. **Iterate**: Use quick checks during development, full suite for final validation

## Finding Source Files

The aiter codebase structure varies by operator. To find implementation files:

1. **Start with the test file**: `op_tests/test_{{op}}.py`
   - Read imports to see what modules are used
   - Look for the main function being tested

2. **Check common locations** (not all ops have all of these):
   - `aiter/ops/{{op}}.py` — High-level Python API (some ops)
   - `aiter/triton_kernels/` — Triton kernel implementations
   - `csrc/kernels/` — CUDA/HIP kernel implementations
   - `csrc/py_itfs_cu/` — Python interface CUDA files
   - `csrc/cktile_*/` — Composable Kernel tile implementations

3. **Search for the op name**:
   ```bash
   find . -name "*{{op}}*" -type f | grep -v __pycache__
   grep -r "def {{function_name}}" aiter/ csrc/ --include="*.py" --include="*.cu"
   ```

## Key Directories

- `aiter/` — Main package with operator implementations
- `aiter/ops/` — High-level operator APIs (some ops)
- `aiter/triton_kernels/` — Triton kernel implementations
- `csrc/` — C++/CUDA/HIP implementations
- `op_tests/` — Tests for each operator
- `aiter/configs/` — Tuned configurations (CSV files)

## Output

Your goal is to produce:
1. Modified operator code with optimizations
2. Benchmark results showing correctness and speedup
3. A summary of what you changed and why

The optimization should be correct (pass the op_test) and faster than baseline."""

# Bash commands allowed for aiter optimization agents.
AITER_BASH_ALLOWLIST: list[str] = [
    # Read-only
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "find",
    "grep",
    "rg",
    "pwd",
    "tree",
    "which",
    "diff",
    "sort",
    # Filesystem
    "mkdir",
    "cp",
    "mv",
    # Git
    "git diff",
    "git status",
    "git log",
    # Compilation
    "hipcc",
    "g++",
    "gcc",
    "clang",
    "python",
    "python3",
    "pip",
    "pytest",
    # Execution — allows running compiled binaries and python scripts
    "./",
    # Kernel evaluation
    "wafer evaluate aiter",
    # Profiling — AMD
    "wafer amd rocprof-compute",
    "wafer amd rocprof-sdk",
    "wafer amd rocprof-systems",
    "wafer amd isa",
    # Sub-agents
    "wafer agent -t ask-docs",
    # Misc
    "timeout",
]

# Bash commands allowed for vLLM kernel optimization agents.
VLLM_BASH_ALLOWLIST: list[str] = [
    # vLLM evaluation
    "wafer evaluate vllm",
    # vLLM's own test and benchmark commands (run inside vllm dir)
    "pytest",
    # Profiling — AMD
    "wafer amd rocprof-compute",
    "wafer amd rocprof-sdk",
    "wafer amd rocprof-systems",
    # Profiling — NVIDIA
    "wafer nvidia ncu",
    "wafer nvidia nsys",
    # Analysis
    "wafer compiler-analyze",
    # Sub-agents
    "wafer agent -t ask-docs",
    # General utilities
    "python",
    "python3",
    "pip",
    "timeout",
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "pwd",
    "which",
    "cd",
    "git",
]
