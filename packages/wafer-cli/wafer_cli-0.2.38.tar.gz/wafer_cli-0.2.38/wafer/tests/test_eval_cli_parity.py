"""Test that eval and CLI agent configs are in sync.

Run: python -m pytest apps/wafer-cli/wafer/tests/test_eval_cli_parity.py -v
  or: python apps/wafer-cli/wafer/tests/test_eval_cli_parity.py  (standalone)
  or: python apps/wafer-cli/wafer/tests/test_eval_cli_parity.py --dump  (side-by-side)

Checks:
- Same bash allowlist (identity check — must be the same object)
- Same enabled tools
- Same system prompt text (modulo runtime variables like pool name)
- CLI instructions generated from same allowlist

Coverage notes:
  These tests verify config-level parity. After composition, both paths
  flow through the same codepath (Actor → run_agent_step → rollout →
  anthropic.py provider) with no further system prompt modifications.

  Known infra-level differences NOT tested here:
  - Claude Code identity prefix: anthropic.py prepends "You are Claude Code..."
    when using OAuth/Claude Code API keys. Eval typically uses raw API keys,
    so eval agents may not get this prefix. This is an auth concern, not a
    prompt content concern.
  - Skills layer: CLI path (wevin_cli.py) can append skill metadata if
    template.include_skills is True. Currently False for optimize-kernelbench,
    so this is a no-op. Eval path doesn't have this layer at all.
"""

from __future__ import annotations

import difflib
import string
import sys


def _normalize_prompt(prompt: str) -> str:
    """Normalize runtime variables so eval and CLI prompts are comparable."""
    # Replace pool/target specifics with placeholders
    prompt = prompt.replace("--pool mi300x-pool", "--pool POOL")
    prompt = prompt.replace("--pool kernelbench-pool", "--pool POOL")
    prompt = prompt.replace("--target mi300x", "--target TARGET")
    return prompt


def test_bash_allowlist_parity() -> None:
    from wafer.agent_defaults import KERNELBENCH_BASH_ALLOWLIST
    from wafer.templates.optimize_kernelbench import template

    # Template should use the shared allowlist (same object)
    assert template.bash_allowlist is KERNELBENCH_BASH_ALLOWLIST, (
        "Template bash_allowlist is not the shared KERNELBENCH_BASH_ALLOWLIST. "
        "Import it from wafer.agent_defaults instead of defining a local copy."
    )

    # Eval should also alias to the shared allowlist
    from optimize_kernelbench_eval.base_config import BASH_ALLOWLIST

    assert BASH_ALLOWLIST is KERNELBENCH_BASH_ALLOWLIST, (
        "Eval BASH_ALLOWLIST is not the shared KERNELBENCH_BASH_ALLOWLIST. "
        "Import it from wafer.agent_defaults instead of defining a local copy."
    )


def test_enabled_tools_parity() -> None:
    from wafer.agent_defaults import ENABLED_TOOLS
    from wafer.templates.optimize_kernelbench import template

    assert template.tools == ENABLED_TOOLS, (
        f"Template tools {template.tools} != shared ENABLED_TOOLS {ENABLED_TOOLS}"
    )


def test_system_prompt_parity() -> None:
    """The task-specific system prompt should be identical between eval and CLI
    (after normalizing runtime variables like pool name)."""
    from optimize_kernelbench_eval.base_config import SYSTEM_PROMPT as EVAL_PROMPT

    from wafer.templates.optimize_kernelbench import template

    # Format eval prompt with HIP defaults (most common)
    eval_formatted = EVAL_PROMPT.format(
        backend="HIP",
        backend_lower="hip",
        target_flag="--pool POOL",
        reference_path="<reference_file>",
    )

    # Format CLI template prompt with matching defaults
    params = dict(template.defaults)
    params["target_flag"] = "--pool POOL"
    cli_formatted = string.Template(template.system_prompt).safe_substitute(**params)

    eval_normalized = _normalize_prompt(eval_formatted)
    cli_normalized = _normalize_prompt(cli_formatted)

    if eval_normalized != cli_normalized:
        diff = "\n".join(
            difflib.unified_diff(
                eval_normalized.splitlines(),
                cli_normalized.splitlines(),
                fromfile="eval (base_config.py)",
                tofile="cli (optimize_kernelbench.py template)",
                lineterm="",
                n=2,
            )
        )
        raise AssertionError(
            f"System prompts differ between eval and CLI template:\n\n{diff}\n\n"
            "Both should define the same task instructions. "
            "Edit one to match the other."
        )


def test_cli_instructions_identical() -> None:
    """Both paths should generate the same CLI instructions
    (since they use the same bash_allowlist)."""
    from wafer.agent_defaults import KERNELBENCH_BASH_ALLOWLIST
    from wafer.cli_instructions import build_cli_instructions
    from wafer.templates.optimize_kernelbench import template

    eval_instructions = build_cli_instructions(KERNELBENCH_BASH_ALLOWLIST)
    cli_instructions = build_cli_instructions(template.bash_allowlist)

    assert eval_instructions == cli_instructions, (
        "CLI instructions differ — this means the bash allowlists diverged."
    )
    assert len(eval_instructions) > 0, "CLI instructions should not be empty"


def _dump_full_prompts() -> None:
    """Standalone: dump both composed prompts for manual comparison."""
    from optimize_kernelbench_eval.base_config import SYSTEM_PROMPT as EVAL_PROMPT

    from wafer.agent_defaults import KERNELBENCH_BASH_ALLOWLIST
    from wafer.cli_instructions import build_cli_instructions
    from wafer.templates.optimize_kernelbench import template

    cli_instructions = build_cli_instructions(KERNELBENCH_BASH_ALLOWLIST)

    # Eval
    eval_sys = EVAL_PROMPT.format(
        backend="HIP",
        backend_lower="hip",
        target_flag="--pool mi300x-pool",
        reference_path="<reference_file>",
    )
    eval_sys += "\n\n" + cli_instructions

    # CLI
    params = dict(template.defaults)
    cli_sys = string.Template(template.system_prompt).safe_substitute(**params)
    cli_sys += "\n\n" + build_cli_instructions(template.bash_allowlist)

    print("=" * 60)
    print("EVAL SYSTEM PROMPT")
    print("=" * 60)
    print(eval_sys)
    print()
    print("=" * 60)
    print("CLI SYSTEM PROMPT")
    print("=" * 60)
    print(cli_sys)
    print()

    # Diff
    eval_norm = _normalize_prompt(eval_sys)
    cli_norm = _normalize_prompt(cli_sys)
    diff = list(
        difflib.unified_diff(
            eval_norm.splitlines(),
            cli_norm.splitlines(),
            fromfile="eval",
            tofile="cli",
            lineterm="",
            n=1,
        )
    )
    if diff:
        print("=" * 60)
        print("DIFFERENCES (after normalizing pool names)")
        print("=" * 60)
        for line in diff:
            print(line)
    else:
        print("IDENTICAL (after normalizing pool names)")


if __name__ == "__main__":
    if "--dump" in sys.argv:
        _dump_full_prompts()
    else:
        test_bash_allowlist_parity()
        print("PASS: bash_allowlist_parity")
        test_enabled_tools_parity()
        print("PASS: enabled_tools_parity")
        test_system_prompt_parity()
        print("PASS: system_prompt_parity")
        test_cli_instructions_identical()
        print("PASS: cli_instructions_identical")
        print("\nAll parity checks passed.")
