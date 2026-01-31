"""Unified ISA Analyzer - CLI for static ISA analysis of AMD GPU kernels.

This module provides the CLI wrapper for the `wafer amd isa` command.
It supports analysis of:
- AMD GPU code objects (.co) - Via API server with ROCm tools
- AMDGCN ISA files (.s, .gcn, .asm) - Local parsing
- LLVM-IR files (.ll) - Local parsing
- TTGIR files (.ttgir, .ttir, .mlir) - Local parsing

Design: Wafer-436 - AMD Kernel Scope / ISA Analyzer
"""

import sys
from pathlib import Path


def print_usage() -> None:
    """Print CLI usage information."""
    print("Usage: wafer amd isa <subcommand> [options]", file=sys.stderr)
    print("", file=sys.stderr)
    print("Subcommands:", file=sys.stderr)
    print("  analyze <file|directory>   Analyze ISA files (.co, .s, .ll, .ttgir)", file=sys.stderr)
    print("  metrics                    List available metrics", file=sys.stderr)
    print("  targets                    List supported GPU targets", file=sys.stderr)
    print("", file=sys.stderr)
    print("Supported File Types:", file=sys.stderr)
    print("  .co                        AMD GPU code objects (requires API authentication)", file=sys.stderr)
    print("  .s, .gcn, .asm             AMDGCN ISA assembly (local parsing)", file=sys.stderr)
    print("  .ll, .bc                   LLVM-IR (local parsing)", file=sys.stderr)
    print("  .ttgir, .ttir, .mlir       TTGIR / Triton IR (local parsing)", file=sys.stderr)
    print("", file=sys.stderr)
    print("Analyze Options:", file=sys.stderr)
    print("  --json                     Output as JSON", file=sys.stderr)
    print("  --csv                      Output as CSV", file=sys.stderr)
    print("  --recursive / -r           Scan directories recursively", file=sys.stderr)
    print("  --filter EXPR              Filter results (e.g., 'spills > 0')", file=sys.stderr)
    print("  --output / -o FILE         Write output to file", file=sys.stderr)
    print("  --kernel INDEX             Kernel index if multiple in file", file=sys.stderr)
    print("", file=sys.stderr)
    print("Examples:", file=sys.stderr)
    print("  wafer amd isa analyze kernel.co           # Analyze code object (requires login)", file=sys.stderr)
    print("  wafer amd isa analyze kernel.s            # Analyze ISA assembly", file=sys.stderr)
    print("  wafer amd isa analyze kernel.s --json     # Output as JSON", file=sys.stderr)
    print("  wafer amd isa analyze ~/.triton/cache/ --filter 'spills > 0'", file=sys.stderr)
    print("  wafer amd isa analyze . -r --csv -o metrics.csv", file=sys.stderr)
    print("  wafer amd isa metrics                     # List available metrics", file=sys.stderr)
    print("  wafer amd isa targets                     # List supported GPU targets", file=sys.stderr)


def analyze_command(
    path: str,
    json_output: bool = False,
    csv_output: bool = False,
    recursive: bool = True,
    filter_expr: str | None = None,
    output_file: str | None = None,
    kernel_index: int = 0,
    api_url: str | None = None,
    auth_headers: dict[str, str] | None = None,
) -> str:
    """Analyze ISA/LLVM-IR/TTGIR/.co file or directory.

    Args:
        path: Path to file or directory
        json_output: Output as JSON
        csv_output: Output as CSV
        recursive: Scan directories recursively
        filter_expr: Filter expression (e.g., "spills > 0")
        output_file: Write output to file
        kernel_index: Kernel index for multi-kernel files
        api_url: API URL for .co file analysis (required for .co files)
        auth_headers: Auth headers for .co file analysis

    Returns:
        Analysis output string
    """
    from wafer_core.lib.kernel_scope import (
        analyze_code_object,
        analyze_directory,
        analyze_file,
        analyze_isa_file,
    )

    target_path = Path(path).expanduser()

    if not target_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    # Single file analysis
    if target_path.is_file():
        suffix = target_path.suffix.lower()

        # Code object files (.co) - need API
        if suffix == ".co":
            if not api_url or not auth_headers:
                raise RuntimeError(
                    "API authentication required for .co file analysis. "
                    "Run 'wafer login' first."
                )
            result = analyze_code_object(target_path, api_url, auth_headers)
        # ISA files - use kernel_index parameter
        elif suffix in (".s", ".gcn", ".asm"):
            result = analyze_isa_file(target_path, kernel_index=kernel_index)
        else:
            result = analyze_file(target_path, api_url=api_url, auth_headers=auth_headers)

        if not result.success:
            raise RuntimeError(f"Analysis failed: {result.error}")

        output = _format_single_result(result, json_output, csv_output)

    # Directory analysis
    else:
        batch_result = analyze_directory(
            target_path,
            recursive=recursive,
            api_url=api_url,
            auth_headers=auth_headers,
        )

        # Apply filter if specified
        if filter_expr:
            batch_result = _apply_filter(batch_result, filter_expr)

        output = _format_batch_result(batch_result, json_output, csv_output)

    # Write to file if specified
    if output_file:
        Path(output_file).write_text(output)
        print(f"Output written to {output_file}", file=sys.stderr)
        return f"Results saved to {output_file}"

    return output


def metrics_command() -> str:
    """List available metrics.

    Returns:
        Metrics list output
    """
    metrics = [
        ("vgpr_count", "Vector GPR allocation", "From .amdhsa_next_free_vgpr directive"),
        ("sgpr_count", "Scalar GPR allocation", "From .amdhsa_next_free_sgpr directive"),
        ("agpr_count", "Accumulator GPR count", "For MFMA operations (MI100+)"),
        ("lds_size", "LDS allocation (bytes)", "From .amdhsa_group_segment_fixed_size"),
        ("scratch_size", "Scratch memory (bytes)", "From .amdhsa_private_segment_fixed_size"),
        ("spill_count", "Register spill operations", "Count of scratch_store/load instructions"),
        ("mfma_count", "MFMA instructions", "Count of v_mfma_* instructions"),
        ("mfma_density_pct", "MFMA density (%)", "MFMA / total VALU * 100"),
        ("packed_ops_count", "Packed instructions", "Count of v_pk_* instructions"),
        ("fma_count", "FMA instructions", "Count of v_fma_* instructions"),
        ("barrier_count", "Barriers", "Count of s_barrier instructions"),
        ("full_stall_count", "Full stalls", "Count of waitcnt 0 instructions"),
        ("global_load_count", "Global loads", "Count of global_load_* instructions"),
        ("global_store_count", "Global stores", "Count of global_store_* instructions"),
        ("lds_ops_count", "LDS operations", "Count of ds_read/write instructions"),
        ("theoretical_occupancy", "Max waves/CU", "Limited by VGPR/SGPR/LDS"),
    ]

    lines = [
        "Available Metrics for Kernel Scope Analysis",
        "=" * 60,
        "",
    ]

    for name, description, derivation in metrics:
        lines.append(f"  {name:<25} {description}")
        lines.append(f"  {'':<25} Derivation: {derivation}")
        lines.append("")

    lines.extend([
        "Instruction Categories:",
        "  VALU   - Vector ALU (v_add_*, v_mul_*, v_fma_*)",
        "  SALU   - Scalar ALU (s_add_*, s_mul_*)",
        "  VMEM   - Vector memory (global_load_*, global_store_*)",
        "  SMEM   - Scalar memory (s_load_*, s_buffer_load_*)",
        "  LDS    - Local Data Share (ds_read_*, ds_write_*)",
        "  MFMA   - Matrix FMA (v_mfma_f32_*, v_mfma_f16_*)",
        "  SYNC   - Synchronization (s_barrier, s_waitcnt)",
        "  SPILL  - Spill operations (scratch_store_*, scratch_load_*)",
    ])

    return "\n".join(lines)


def targets_command() -> str:
    """List supported GPU targets.

    Returns:
        Targets list output
    """
    from wafer_core.lib.kernel_scope.targets import SUPPORTED_TARGETS, get_target_specs

    lines = [
        "Supported GPU Targets",
        "=" * 60,
        "",
        f"{'Architecture':<12} {'Series':<10} {'VGPRs/CU':<10} {'SGPRs/CU':<10} {'LDS/CU':<10} {'Max Waves':<10}",
        "-" * 60,
    ]

    for target in SUPPORTED_TARGETS:
        specs = get_target_specs(target)
        lines.append(
            f"{specs.name:<12} {specs.series:<10} {specs.vgprs_per_cu:<10} "
            f"{specs.sgprs_per_cu:<10} {specs.lds_per_cu:<10} {specs.max_waves_per_cu:<10}"
        )

    lines.extend([
        "",
        "Note: Default values are used for unknown architectures.",
    ])

    return "\n".join(lines)


def _format_single_result(result, json_output: bool, csv_output: bool) -> str:
    """Format a single analysis result."""
    if json_output:
        return result.to_json()

    if csv_output:
        return _result_to_csv(result)

    return _result_to_text(result)


def _format_batch_result(batch_result, json_output: bool, csv_output: bool) -> str:
    """Format batch analysis results."""
    if json_output:
        return batch_result.to_json()

    if csv_output:
        return _batch_to_csv(batch_result)

    return _batch_to_text(batch_result)


def _result_to_text(result) -> str:
    """Format single result as human-readable text."""
    lines = []

    if result.code_object_analysis:
        # .co file analysis (via API)
        a = result.code_object_analysis
        lines.extend([
            f"Kernel: {a.kernel_name}",
            f"Architecture: {a.architecture}",
            "Source: Code Object (.co)",
            "",
            "=== Registers ===",
            f"  VGPRs: {a.vgpr_count}",
            f"  SGPRs: {a.sgpr_count}",
            f"  AGPRs: {a.agpr_count}",
        ])

        if a.vgpr_spill_count > 0 or a.sgpr_spill_count > 0:
            lines.extend([
                "",
                "!!! SPILLS DETECTED !!!",
                f"  VGPR spills: {a.vgpr_spill_count}",
                f"  SGPR spills: {a.sgpr_spill_count}",
            ])
        else:
            lines.append("  Spills: None (good)")

        lines.extend([
            "",
            "=== Memory ===",
            f"  LDS: {a.lds_bytes} bytes",
            f"  Global loads: {a.global_loads}",
            f"  Global stores: {a.global_stores}",
            f"  LDS ops: {a.lds_ops}",
            "",
            "=== Instructions ===",
            f"  MFMA: {a.mfma_count}",
            f"  FMA: {a.fma_count}",
            f"  Packed (v_pk_*): {a.packed_ops_count}",
            f"  Full stalls (waitcnt 0): {a.waitcnt_full_stalls}",
            f"  Barriers: {a.barriers}",
        ])

    elif result.isa_analysis:
        # .s/.gcn/.asm file analysis (local parsing)
        a = result.isa_analysis
        lines.extend([
            f"Kernel: {a.kernel_name}",
            f"Architecture: {a.architecture}",
            "Source: ISA Assembly (.s)",
            "",
            "=== Registers ===",
            f"  VGPRs: {a.vgpr_count}",
            f"  SGPRs: {a.sgpr_count}",
            f"  AGPRs: {a.agpr_count}",
        ])

        if a.spill_count > 0:
            lines.extend([
                "",
                "!!! SPILLS DETECTED !!!",
                f"  Total spills: {a.spill_count}",
                f"  VGPR spills: {a.vgpr_spill_count}",
                f"  SGPR spills: {a.sgpr_spill_count}",
            ])
        else:
            lines.append("  Spills: None (good)")

        lines.extend([
            "",
            "=== Memory ===",
            f"  LDS: {a.lds_size} bytes",
            f"  Scratch: {a.scratch_size} bytes",
            f"  Global loads: {a.global_load_count}",
            f"  Global stores: {a.global_store_count}",
            f"  LDS ops: {a.lds_ops_count}",
            "",
            "=== Instructions ===",
            f"  MFMA: {a.mfma_count} ({a.mfma_density_pct:.1f}% density)",
            f"  FMA: {a.fma_count}",
            f"  Packed (v_pk_*): {a.packed_ops_count}",
            f"  Barriers: {a.barrier_count}",
            f"  Full stalls: {a.full_stall_count}",
            "",
            "=== Instruction Mix ===",
            f"  VALU: {a.instruction_mix.valu_count}",
            f"  SALU: {a.instruction_mix.salu_count}",
            f"  VMEM: {a.instruction_mix.vmem_count}",
            f"  SMEM: {a.instruction_mix.smem_count}",
            f"  LDS: {a.instruction_mix.lds_count}",
            f"  MFMA: {a.instruction_mix.mfma_count}",
            f"  Sync: {a.instruction_mix.sync_count}",
            f"  Total: {a.instruction_mix.total_count}",
            "",
            "=== Occupancy ===",
            f"  Max waves (VGPR): {a.max_waves_vgpr}",
            f"  Max waves (SGPR): {a.max_waves_sgpr}",
            f"  Max waves (LDS): {a.max_waves_lds}",
            f"  Theoretical: {a.theoretical_occupancy} waves/CU",
        ])

        if a.warnings:
            lines.extend([
                "",
                "=== Warnings ===",
            ])
            for warning in a.warnings:
                lines.append(f"  {warning}")

    elif result.ttgir_analysis:
        a = result.ttgir_analysis
        lines.extend([
            "TTGIR Analysis",
            "",
            "=== Operations ===",
            f"  tt.dot: {a.dot_count}",
            f"  tt.load: {a.load_count}",
            f"  tt.store: {a.store_count}",
            f"  tt.reduce: {a.reduce_count}",
            f"  Barriers: {a.barrier_count}",
        ])

        if a.tile_info:
            lines.extend([
                "",
                "=== Tiling ===",
                f"  BLOCK_M: {a.tile_info.block_m}",
                f"  BLOCK_N: {a.tile_info.block_n}",
                f"  BLOCK_K: {a.tile_info.block_k}",
                f"  num_warps: {a.tile_info.num_warps}",
                f"  num_stages: {a.tile_info.num_stages}",
            ])

        if a.has_software_pipelining:
            lines.append("  Software pipelining: enabled")

        if a.estimated_compute_intensity:
            lines.append(f"  Compute intensity: {a.estimated_compute_intensity:.1f} FLOPs/byte")

    elif result.llvm_ir_analysis:
        a = result.llvm_ir_analysis
        lines.extend([
            "LLVM-IR Analysis",
            "",
            f"  Functions: {a.function_count}",
            f"  Total instructions: {a.total_instructions}",
            f"  Functions with loops: {a.functions_with_loops}",
            f"  Has vector ops: {a.has_vector_ops}",
        ])

        if a.kernel_functions:
            lines.append(f"  Kernel functions: {', '.join(a.kernel_functions)}")

    return "\n".join(lines)


def _result_to_csv(result) -> str:
    """Format single result as CSV."""
    header = "kernel_name,architecture,source_type,vgpr_count,sgpr_count,vgpr_spills,sgpr_spills,mfma_count,lds_bytes,global_loads,global_stores"

    if result.code_object_analysis:
        a = result.code_object_analysis
        row = f"{a.kernel_name},{a.architecture},code_object,{a.vgpr_count},{a.sgpr_count},{a.vgpr_spill_count},{a.sgpr_spill_count},{a.mfma_count},{a.lds_bytes},{a.global_loads},{a.global_stores}"
        return f"{header}\n{row}"

    if result.isa_analysis:
        a = result.isa_analysis
        row = f"{a.kernel_name},{a.architecture},isa_assembly,{a.vgpr_count},{a.sgpr_count},{a.vgpr_spill_count},{a.sgpr_spill_count},{a.mfma_count},{a.lds_size},{a.global_load_count},{a.global_store_count}"
        return f"{header}\n{row}"

    return "# Unsupported format for CSV"


def _batch_to_text(batch_result) -> str:
    """Format batch results as text."""
    lines = [
        f"Analyzed {batch_result.total_files} files",
        f"  Successful: {batch_result.successful}",
        f"  Failed: {batch_result.failed}",
        "",
    ]

    if batch_result.summary:
        lines.extend([
            "=== Summary ===",
            f"  Avg VGPRs: {batch_result.summary.get('total_vgpr_avg', 0):.1f}",
            f"  Avg SGPRs: {batch_result.summary.get('total_sgpr_avg', 0):.1f}",
            f"  Total spills: {batch_result.summary.get('total_spills', 0)}",
            f"  Files with spills: {batch_result.summary.get('files_with_spills', 0)}",
            f"  Total MFMA: {batch_result.summary.get('total_mfma', 0)}",
            f"  Avg MFMA density: {batch_result.summary.get('avg_mfma_density', 0):.1f}%",
            "",
        ])

    # Show individual results
    for result in batch_result.results:
        if result.success and result.code_object_analysis:
            a = result.code_object_analysis
            spills = a.vgpr_spill_count + a.sgpr_spill_count
            status = "⚠️" if spills > 0 else "✓"
            lines.append(
                f"  {status} {result.file_path}: "
                f"VGPRs={a.vgpr_count}, spills={spills}, MFMA={a.mfma_count}"
            )
        elif result.success and result.isa_analysis:
            a = result.isa_analysis
            status = "⚠️" if a.spill_count > 0 else "✓"
            lines.append(
                f"  {status} {result.file_path}: "
                f"VGPRs={a.vgpr_count}, spills={a.spill_count}, MFMA={a.mfma_count}"
            )
        elif not result.success:
            lines.append(f"  ✗ {result.file_path}: {result.error}")

    return "\n".join(lines)


def _batch_to_csv(batch_result) -> str:
    """Format batch results as CSV."""
    lines = ["file_path,kernel_name,architecture,source_type,vgpr_count,sgpr_count,vgpr_spills,sgpr_spills,mfma_count,lds_bytes"]

    for result in batch_result.results:
        if result.success and result.code_object_analysis:
            a = result.code_object_analysis
            lines.append(
                f"{result.file_path},{a.kernel_name},{a.architecture},code_object,"
                f"{a.vgpr_count},{a.sgpr_count},{a.vgpr_spill_count},{a.sgpr_spill_count},"
                f"{a.mfma_count},{a.lds_bytes}"
            )
        elif result.success and result.isa_analysis:
            a = result.isa_analysis
            lines.append(
                f"{result.file_path},{a.kernel_name},{a.architecture},isa_assembly,"
                f"{a.vgpr_count},{a.sgpr_count},{a.vgpr_spill_count},{a.sgpr_spill_count},"
                f"{a.mfma_count},{a.lds_size}"
            )

    return "\n".join(lines)


def _apply_filter(batch_result, filter_expr: str):
    """Apply filter expression to batch results."""
    # Simple filter parsing: "metric op value"
    # Supported: spills > 0, vgpr_count > 128, mfma_count == 0
    import re

    match = re.match(r"(\w+)\s*(>|<|>=|<=|==|!=)\s*(\d+)", filter_expr)
    if not match:
        print(f"Warning: Invalid filter expression: {filter_expr}", file=sys.stderr)
        return batch_result

    metric = match.group(1)
    op = match.group(2)
    value = int(match.group(3))

    # Map common aliases
    metric_map = {
        "spills": "spill_count",
        "vgpr": "vgpr_count",
        "sgpr": "sgpr_count",
        "mfma": "mfma_count",
        "occupancy": "theoretical_occupancy",
    }
    metric = metric_map.get(metric, metric)

    # Filter function - supports both isa_analysis and code_object_analysis
    def passes_filter(result):
        if not result.success:
            return False

        # Try to get metric from either analysis type
        actual = None
        if result.isa_analysis:
            actual = getattr(result.isa_analysis, metric, None)
        elif result.code_object_analysis:
            # Map isa_analysis metric names to code_object_analysis equivalents
            co_metric_map = {
                "spill_count": "vgpr_spill_count",  # Use vgpr_spill_count as proxy
                "lds_size": "lds_bytes",
            }
            co_metric = co_metric_map.get(metric, metric)
            actual = getattr(result.code_object_analysis, co_metric, None)

        if actual is None:
            return False

        if op == ">":
            return actual > value
        elif op == "<":
            return actual < value
        elif op == ">=":
            return actual >= value
        elif op == "<=":
            return actual <= value
        elif op == "==":
            return actual == value
        elif op == "!=":
            return actual != value

        return False

    filtered_results = [r for r in batch_result.results if passes_filter(r)]

    from wafer_core.lib.kernel_scope.api import BatchAnalysisResult

    return BatchAnalysisResult(
        total_files=len(filtered_results),
        successful=sum(1 for r in filtered_results if r.success),
        failed=sum(1 for r in filtered_results if not r.success),
        results=tuple(filtered_results),
        summary=batch_result.summary,
    )
