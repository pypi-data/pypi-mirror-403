"""CLI commands for wafer specs — TargetSpec TOML management.

These are the local config commands (no API calls).
Registered as: wafer specs list|show|add|remove|default|init
"""

from __future__ import annotations

from pathlib import Path

import typer

specs_app = typer.Typer(
    help="""Manage GPU target specs (provisioning blueprints).

Specs define how to access or provision GPUs. They are TOML files in ~/.wafer/specs/.

  wafer specs list                        # List all specs
  wafer specs show runpod-mi300x          # Show one spec
  wafer specs add /path/to/spec.toml      # Add from file
  wafer specs remove old-target           # Remove a spec
  wafer specs default runpod-mi300x       # Set default

To create a new spec interactively:
  wafer config targets init ssh           # (legacy, still works)
  wafer config targets init runpod
"""
)


@specs_app.command("list")
def specs_list() -> None:
    """List all configured specs.

    Example:
        wafer specs list
    """
    from wafer_core.targets.spec_store import list_spec_names, load_spec

    from .targets import get_default_target

    names = list_spec_names()
    default = get_default_target()

    if not names:
        typer.echo("No specs configured.")
        typer.echo("Add one with: wafer specs add <path/to/spec.toml>")
        typer.echo("Or interactively: wafer config targets init ssh")
        return

    typer.echo("Configured specs:")
    for name in names:
        marker = " (default)" if name == default else ""
        try:
            spec = load_spec(name)
            type_name = type(spec).__name__.replace("Target", "")
            typer.echo(f"  {name}{marker}  [{type_name}]  gpu={spec.gpu_type}")
        except Exception as e:
            typer.echo(f"  {name}{marker}  [error: {e}]")


@specs_app.command("show")
def specs_show(
    name: str = typer.Argument(..., help="Spec name"),
) -> None:
    """Show details for a spec.

    Example:
        wafer specs show runpod-mi300x
    """
    from wafer_core.targets.spec_store import load_spec

    from .targets import get_target_info

    try:
        spec = load_spec(name)
    except FileNotFoundError:
        typer.echo(f"Spec not found: {name}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Spec: {name}")
    for key, value in get_target_info(spec).items():
        typer.echo(f"  {key}: {value}")


@specs_app.command("add")
def specs_add(
    file_path: Path = typer.Argument(..., help="Path to TOML spec file"),
) -> None:
    """Add a spec from a TOML file.

    Example:
        wafer specs add ./my-target.toml
    """
    import tomllib

    from wafer_core.targets.spec_store import parse_spec, save_spec

    if not file_path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1) from None

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        spec = parse_spec(data)
        save_spec(spec)
        typer.echo(f"Added spec: {spec.name}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@specs_app.command("remove")
def specs_remove(
    name: str = typer.Argument(..., help="Spec name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Remove a spec.

    Example:
        wafer specs remove old-target
    """
    from wafer_core.targets.spec_store import remove_spec

    if not force:
        confirm = typer.confirm(f"Remove spec '{name}'?")
        if not confirm:
            return

    try:
        remove_spec(name)
        typer.echo(f"Removed spec: {name}")
    except FileNotFoundError:
        typer.echo(f"Spec not found: {name}", err=True)
        raise typer.Exit(1) from None


@specs_app.command("default")
def specs_default(
    name: str = typer.Argument(..., help="Spec name to set as default"),
) -> None:
    """Set the default spec.

    Example:
        wafer specs default runpod-mi300x
    """
    from wafer_core.targets.spec_store import list_spec_names

    from .targets import set_default_target

    if name not in list_spec_names():
        typer.echo(f"Spec not found: {name}", err=True)
        raise typer.Exit(1) from None

    set_default_target(name)
    typer.echo(f"Default spec set to: {name}")
