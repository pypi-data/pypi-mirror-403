"""Generate agent system prompt instructions from the wafer CLI's own --help text.

Walks the typer/click command tree and extracts help text for commands
matching the bash_allowlist. This ensures agent instructions stay in sync
with the CLI — the --help text is the single source of truth for both
human users and AI agents.

Usage:
    from wafer.cli_instructions import build_cli_instructions

    instructions = build_cli_instructions([
        "wafer evaluate",
        "wafer nvidia ncu",
        "wafer rocprof profile",
        "python",  # non-wafer commands are skipped
    ])
"""

from __future__ import annotations

import click
import typer.main


def _resolve_command(root: click.BaseCommand, parts: list[str]) -> click.BaseCommand | None:
    """Walk the click command tree to find a (sub)command by name parts.

    Args:
        root: The root click command (from typer.main.get_command)
        parts: Command path segments, e.g. ["evaluate", "kernelbench"]

    Returns:
        The click command at that path, or None if not found.
    """
    cmd = root
    for part in parts:
        if not isinstance(cmd, click.MultiCommand):
            return None
        ctx = click.Context(cmd, info_name=part)
        child = cmd.get_command(ctx, part)
        if child is None:
            return None
        cmd = child
    return cmd


def _format_command_help(cmd_path: str, cmd: click.BaseCommand) -> str:
    """Format a single command's help text for inclusion in a system prompt.

    Extracts the description and option help text (skipping --help itself).
    """
    lines = [f"### `{cmd_path}`"]

    if cmd.help:
        lines.append(cmd.help.strip())

    # Extract option help
    option_lines = []
    for param in getattr(cmd, "params", []):
        if not isinstance(param, click.Option):
            continue
        # Skip --help
        if param.name == "help":
            continue
        name = "/".join(param.opts)
        type_name = param.type.name.upper() if hasattr(param.type, "name") else ""
        help_text = param.help or ""
        is_flag = type_name in ("BOOL", "BOOLEAN") or param.is_flag
        if type_name and not is_flag:
            option_lines.append(f"  {name} {type_name}  {help_text}")
        else:
            option_lines.append(f"  {name}  {help_text}")

    if option_lines:
        lines.append("")
        lines.append("Options:")
        lines.extend(option_lines)

    # List subcommands if this is a group
    if isinstance(cmd, click.MultiCommand):
        ctx = click.Context(cmd, info_name=cmd_path.split()[-1])
        subcmd_names = cmd.list_commands(ctx)
        if subcmd_names:
            subcmd_lines = []
            for name in subcmd_names:
                subcmd = cmd.get_command(ctx, name)
                if subcmd:
                    desc = (subcmd.help or subcmd.short_help or "").strip().split("\n")[0]
                    subcmd_lines.append(f"  {cmd_path} {name}  {desc}")
            if subcmd_lines:
                lines.append("")
                lines.append("Subcommands:")
                lines.extend(subcmd_lines)

    return "\n".join(lines)


def build_cli_instructions(bash_allowlist: list[str]) -> str:
    """Generate CLI instruction text from --help for allowed wafer commands.

    Walks the typer/click command tree and extracts help text for each
    wafer command in the bash_allowlist. Non-wafer commands (python, ls, etc.)
    are skipped.

    Args:
        bash_allowlist: List of allowed bash command prefixes.
            Example: ["wafer evaluate", "wafer nvidia ncu", "python"]

    Returns:
        Markdown-formatted CLI instructions, or empty string if no wafer
        commands are in the allowlist.
    """
    if not bash_allowlist:
        return ""

    # Filter to wafer commands only
    wafer_commands = [cmd for cmd in bash_allowlist if cmd.startswith("wafer ")]
    if not wafer_commands:
        return ""

    # Lazy import to avoid circular deps at module level
    from wafer.cli import app

    root = typer.main.get_command(app)

    sections = []
    for cmd_str in wafer_commands:
        # "wafer evaluate kernelbench" -> ["evaluate", "kernelbench"]
        parts = cmd_str.split()[1:]  # drop "wafer" prefix
        cmd = _resolve_command(root, parts)
        if cmd is None:
            # Command not found in tree — skip silently
            continue
        sections.append(_format_command_help(cmd_str, cmd))

    if not sections:
        return ""

    header = (
        "## Wafer CLI Commands\n\n"
        "You do not have a local GPU. Use the wafer CLI to run on remote GPU hardware.\n"
    )
    return header + "\n\n".join(sections)
