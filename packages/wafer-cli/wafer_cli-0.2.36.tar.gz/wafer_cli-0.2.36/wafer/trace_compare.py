"""CLI wrapper for trace comparison commands.

This module provides the CLI interface for the `wafer compare` commands.
All core logic is in wafer_core.lib.trace_compare.
"""

import sys
from pathlib import Path

import typer

from wafer_core.lib.trace_compare import (
    analyze_fusion_differences,
    analyze_traces,
    format_csv,
    format_fusion_csv,
    format_fusion_json,
    format_fusion_text,
    format_json,
    format_text,
)


def compare_traces(
    trace1: Path,
    trace2: Path,
    output: Path | None = None,
    output_format: str = "text",
    phase: str = "all",
    show_layers: bool = False,
    show_all: bool = False,
    show_stack_traces: bool = False,
) -> None:
    """Compare two GPU traces and generate performance report.

    Args:
        trace1: Path to first trace file (AMD or NVIDIA)
        trace2: Path to second trace file (AMD or NVIDIA)
        output: Optional output file path (default: stdout)
        output_format: Output format ('text', 'text-layers', 'csv', 'csv-layers', or 'json')
        phase: Filter by phase ('all', 'prefill', or 'decode')
        show_layers: Show layer-wise performance breakdown (text format only)
        show_all: Show all items without truncation (applies to layers, operations, kernels)
        show_stack_traces: Show Python stack traces for operations
    """
    # Validate files exist
    if not trace1.exists():
        typer.secho(f"❌ File not found: {trace1}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not trace2.exists():
        typer.secho(f"❌ File not found: {trace2}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Analyze traces
    # Only show progress messages for non-JSON formats (JSON needs clean stdout)
    if output_format != 'json':
        typer.echo("📊 Loading traces...")

    # Determine how many stack traces to collect
    max_stacks = 0 if (show_stack_traces and show_all) else (3 if show_stack_traces else 3)

    try:
        results = analyze_traces(
            trace1,
            trace2,
            phase_filter=phase,
            max_stacks=max_stacks,
        )
    except ValueError as e:
        typer.secho(f"❌ {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"❌ Error analyzing traces: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Show loading confirmation
    if output_format != 'json':
        meta = results["metadata"]
        # Determine which trace is AMD and which is NVIDIA
        if meta['trace1_platform'] == 'AMD':
            amd_gpu, nvidia_gpu = meta['trace1_gpu'], meta['trace2_gpu']
        else:
            amd_gpu, nvidia_gpu = meta['trace2_gpu'], meta['trace1_gpu']
        typer.echo(f"✅ Loaded: AMD ({amd_gpu}) vs NVIDIA ({nvidia_gpu})")
    typer.echo()

    # Generate output based on format
    if output_format == "text":
        output_str = format_text(results, show_layers=show_layers, show_all=show_all, show_stack_traces=show_stack_traces)
    elif output_format == "text-layers":
        output_str = format_text(results, show_layers=True, show_all=show_all, show_stack_traces=show_stack_traces)
    elif output_format == "csv":
        output_str = format_csv(results, report_type="operations")
    elif output_format == "csv-layers":
        output_str = format_csv(results, report_type="layers")
    elif output_format == "json":
        output_str = format_json(results)
    else:
        typer.secho(f"❌ Unknown format: {output_format}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Write output
    if output:
        output.write_text(output_str)
        typer.secho(f"✅ Report saved to {output}", fg=typer.colors.GREEN)
    else:
        typer.echo(output_str)


def compare_fusion(
    trace1: Path,
    trace2: Path,
    output: Path | None = None,
    format_type: str = "text",
    min_group_size: int = 50,
) -> None:
    """Analyze kernel fusion differences between AMD and NVIDIA traces.

    Args:
        trace1: Path to first trace file (AMD or NVIDIA)
        trace2: Path to second trace file (AMD or NVIDIA)
        output: Optional output file path (default: stdout)
        format_type: Output format ('text', 'csv', or 'json')
        min_group_size: Minimum correlation group size to analyze
    """
    # Validate files exist
    if not trace1.exists():
        typer.secho(f"❌ File not found: {trace1}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not trace2.exists():
        typer.secho(f"❌ File not found: {trace2}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Analyze fusion
    # Only show progress messages for non-JSON formats (JSON needs clean stdout)
    if format_type != 'json':
        typer.echo("📊 Loading traces...")
    try:
        results = analyze_fusion_differences(
            trace1,
            trace2,
            min_group_size=min_group_size,
        )
    except Exception as e:
        typer.secho(
            f"❌ Error analyzing traces: {e}", fg=typer.colors.RED, err=True
        )
        import traceback

        traceback.print_exc()
        raise typer.Exit(1)

    # Show loading confirmation
    if format_type != 'json':
        meta = results["metadata"]
        # Note: fusion analyzer always uses trace1=AMD, trace2=NVIDIA
        typer.echo(f"✅ Loaded: {meta['trace1_gpu']} vs {meta['trace2_gpu']}")
        typer.echo(
            f"Found {meta['trace1_correlation_groups']} trace1 groups and "
            f"{meta['trace2_correlation_groups']} trace2 groups with ≥{min_group_size} kernels"
        )
        typer.echo(f"✅ Matched {meta['matched_groups']} correlation groups")
        typer.echo()

    # Generate output
    if format_type == "text":
        output_str = format_fusion_text(results)
    elif format_type == "csv":
        output_str = format_fusion_csv(results)
    elif format_type == "json":
        output_str = format_fusion_json(results)
    else:
        typer.secho(f"❌ Unknown format: {format_type}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Write output
    if output:
        output.write_text(output_str)
        typer.secho(f"✅ Report saved to {output}", fg=typer.colors.GREEN)
    else:
        typer.echo(output_str)
