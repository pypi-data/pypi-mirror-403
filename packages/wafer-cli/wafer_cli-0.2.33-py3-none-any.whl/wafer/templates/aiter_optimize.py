"""Template for optimizing AMD aiter operators.

Usage:
    wafer agent -t aiter-optimize --args op=gemm_a8w8 --args target=mi300x "Optimize this operator"
    wafer agent -t aiter-optimize --args op=mha --args target=runpod-mi300x-rocm7 "Improve MHA performance"
"""

try:
    from wafer.agent_defaults import (
        AITER_BASH_ALLOWLIST,
        AITER_ENABLED_TOOLS,
        AITER_SYSTEM_PROMPT,
    )
except ImportError:
    # Fallback for when wafer-cli package isn't installed
    AITER_ENABLED_TOOLS = ["read", "write", "edit", "glob", "grep", "bash"]
    AITER_BASH_ALLOWLIST = [
        "ls", "cat", "head", "tail", "wc", "find", "grep", "rg", "pwd", "tree",
        "which", "diff", "sort", "mkdir", "cp", "mv", "git diff", "git status",
        "git log", "hipcc", "g++", "gcc", "clang", "python", "python3", "pip",
        "pytest", "./", "wafer evaluate aiter", "wafer amd rocprof-compute",
        "wafer amd rocprof-sdk", "wafer amd rocprof-systems", "wafer amd isa",
        "wafer agent -t ask-docs", "timeout",
    ]
    AITER_SYSTEM_PROMPT = "You are a GPU kernel optimization expert for AMD MI300X and aiter."

try:
    from wafer_core.rollouts.templates import TemplateConfig
except ImportError:
    from rollouts.templates import TemplateConfig

# Format system prompt with template variables ($op, $target become {op}, {target})
# The template loader will substitute these at runtime
_SYSTEM_PROMPT = AITER_SYSTEM_PROMPT.replace("{op}", "$op").replace("{target_flag}", "--target $target")

template = TemplateConfig(
    # Identity
    name="aiter-optimize",
    description="Optimize AMD aiter operators for better performance on MI300X",
    # System prompt - uses shared prompt from agent_defaults
    system_prompt=_SYSTEM_PROMPT,
    # Tools - full coding environment
    tools=AITER_ENABLED_TOOLS,
    bash_allowlist=AITER_BASH_ALLOWLIST,
    # Network access required for wafer evaluate (connects to remote GPU)
    allow_network=True,
    # Model config - use thinking for optimization analysis
    model="anthropic/claude-sonnet-4-5-20250929",
    max_tokens=16384,
    thinking=True,
    thinking_budget=10000,
    # Multi-turn for iterative optimization
    single_turn=False,
    # Template variables
    defaults={
        "op": "gemm_a8w8",
        "target": "mi300x",  # Required - user must specify their target
    },
)
