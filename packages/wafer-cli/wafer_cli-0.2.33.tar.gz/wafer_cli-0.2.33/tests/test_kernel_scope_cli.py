"""Unit tests for Kernel Scope CLI commands.

Tests the wafer amd kernel-scope command using CliRunner.

Run with: PYTHONPATH=apps/wafer-cli uv run pytest apps/wafer-cli/tests/test_kernel_scope_cli.py -v
"""

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wafer.cli import app
from wafer.kernel_scope import (
    analyze_command,
    metrics_command,
    targets_command,
)

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


# Sample ISA for testing
SAMPLE_ISA = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx90a"

.text
.globl test_kernel

test_kernel:
    s_load_dwordx4 s[0:3], s[4:5], 0x0
    s_waitcnt lgkmcnt(0)
    global_load_dwordx4 v[0:3], v[4:5], off
    ds_read_b128 v[8:11], v12
    s_waitcnt vmcnt(0) lgkmcnt(0)
    v_mfma_f32_32x32x8f16 a[0:15], v[0:1], v[2:3], a[0:15]
    v_mfma_f32_32x32x8f16 a[16:31], v[4:5], v[6:7], a[16:31]
    v_add_f32 v0, v1, v2
    v_fma_f32 v3, v4, v5, v6
    global_store_dwordx4 v[20:21], v[0:3], off
    s_barrier
    s_endpgm

.amdhsa_kernel test_kernel
    .amdhsa_next_free_vgpr 64
    .amdhsa_next_free_sgpr 32
    .amdhsa_group_segment_fixed_size 16384
    .amdhsa_private_segment_fixed_size 0
.end_amdhsa_kernel
'''

SAMPLE_ISA_WITH_SPILLS = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx942"

.text
.globl spilling_kernel

spilling_kernel:
    s_load_dwordx4 s[0:3], s[4:5], 0x0
    s_waitcnt lgkmcnt(0)
    scratch_store_dwordx4 off, v[0:3], s0
    scratch_store_dwordx4 off, v[4:7], s0
    scratch_load_dwordx4 v[8:11], off, s0
    v_add_f32 v0, v1, v2
    s_waitcnt 0
    s_endpgm

.amdhsa_kernel spilling_kernel
    .amdhsa_next_free_vgpr 256
    .amdhsa_next_free_sgpr 100
    .amdhsa_group_segment_fixed_size 0
    .amdhsa_private_segment_fixed_size 1024
.end_amdhsa_kernel
'''


# ============================================================================
# Direct Function Tests
# ============================================================================

class TestAnalyzeCommandFunction:
    """Tests for analyze_command function directly."""

    def test_analyze_single_file(self, tmp_path: Path) -> None:
        """Should analyze a single ISA file."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file))

        assert "test_kernel" in output
        assert "gfx90a" in output
        assert "VGPRs:" in output or "vgpr" in output.lower()

    def test_analyze_file_not_found(self, tmp_path: Path) -> None:
        """Should raise error for missing file."""
        with pytest.raises(FileNotFoundError):
            analyze_command(str(tmp_path / "missing.s"))

    def test_analyze_json_output(self, tmp_path: Path) -> None:
        """Should output valid JSON when json_output=True."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file), json_output=True)
        data = json.loads(output)

        assert data["success"] is True
        assert data["isa_analysis"]["kernel_name"] == "test_kernel"
        assert data["isa_analysis"]["architecture"] == "gfx90a"
        assert data["isa_analysis"]["vgpr_count"] == 64
        assert data["isa_analysis"]["mfma_count"] == 2

    def test_analyze_csv_output(self, tmp_path: Path) -> None:
        """Should output CSV when csv_output=True."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file), csv_output=True)

        # Should have header and data row
        lines = output.strip().split("\n")
        assert len(lines) == 2
        assert "kernel_name" in lines[0]
        assert "vgpr_count" in lines[0]
        assert "test_kernel" in lines[1]

    def test_analyze_directory(self, tmp_path: Path) -> None:
        """Should analyze all files in directory."""
        (tmp_path / "kernel1.s").write_text(SAMPLE_ISA)
        (tmp_path / "kernel2.s").write_text(SAMPLE_ISA_WITH_SPILLS)

        output = analyze_command(str(tmp_path))

        assert "Analyzed 2 files" in output

    def test_analyze_with_filter(self, tmp_path: Path) -> None:
        """Should filter results based on expression."""
        (tmp_path / "kernel1.s").write_text(SAMPLE_ISA)
        (tmp_path / "kernel2.s").write_text(SAMPLE_ISA_WITH_SPILLS)

        output = analyze_command(str(tmp_path), filter_expr="spills > 0")

        # Should only show spilling kernel
        assert "1 files" in output or "kernel2" in output or "spilling" in output.lower()

    def test_analyze_output_to_file(self, tmp_path: Path) -> None:
        """Should write output to file."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)
        output_file = tmp_path / "output.json"

        analyze_command(
            str(isa_file),
            json_output=True,
            output_file=str(output_file)
        )

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["success"] is True


class TestMetricsCommandFunction:
    """Tests for metrics_command function."""

    def test_lists_metrics(self) -> None:
        """Should list available metrics."""
        output = metrics_command()

        assert "vgpr_count" in output
        assert "sgpr_count" in output
        assert "spill_count" in output
        assert "mfma_count" in output
        assert "mfma_density_pct" in output
        assert "theoretical_occupancy" in output

    def test_includes_instruction_categories(self) -> None:
        """Should include instruction category descriptions."""
        output = metrics_command()

        assert "VALU" in output
        assert "SALU" in output
        assert "VMEM" in output
        assert "MFMA" in output
        assert "LDS" in output
        assert "SPILL" in output


class TestTargetsCommandFunction:
    """Tests for targets_command function."""

    def test_lists_targets(self) -> None:
        """Should list supported GPU targets."""
        output = targets_command()

        assert "gfx90a" in output
        assert "gfx942" in output
        assert "gfx908" in output

    def test_includes_specs(self) -> None:
        """Should include hardware specs for targets."""
        output = targets_command()

        assert "MI200" in output or "MI300" in output
        assert "VGPRs" in output or "VGPR" in output


# ============================================================================
# CLI Integration Tests (using unified wafer amd isa command)
# ============================================================================

class TestISAAnalyzerCliCommands:
    """Tests for wafer amd isa CLI commands (unified ISA Analyzer)."""

    def test_analyze_command_help(self) -> None:
        """Should display help for analyze command."""
        result = runner.invoke(app, ["amd", "isa", "analyze", "--help"])

        assert result.exit_code == 0
        output = strip_ansi(result.stdout)
        assert "Analyze" in output or "analyze" in output

    def test_analyze_file_via_cli(self, tmp_path: Path) -> None:
        """Should analyze file via CLI."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        result = runner.invoke(app, [
            "amd", "isa", "analyze", str(isa_file)
        ])

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "test_kernel" in result.stdout

    def test_analyze_json_via_cli(self, tmp_path: Path) -> None:
        """Should output JSON via CLI."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        result = runner.invoke(app, [
            "amd", "isa", "analyze", str(isa_file), "--json"
        ])

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.stdout)
        assert data["success"] is True

    def test_analyze_csv_via_cli(self, tmp_path: Path) -> None:
        """Should output CSV via CLI."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        result = runner.invoke(app, [
            "amd", "isa", "analyze", str(isa_file), "--csv"
        ])

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "kernel_name" in result.stdout

    def test_analyze_missing_file_via_cli(self, tmp_path: Path) -> None:
        """Should fail for missing file."""
        result = runner.invoke(app, [
            "amd", "isa", "analyze", str(tmp_path / "missing.s")
        ])

        assert result.exit_code != 0

    def test_metrics_via_cli(self) -> None:
        """Should list metrics via CLI."""
        result = runner.invoke(app, ["amd", "isa", "metrics"])

        assert result.exit_code == 0
        assert "vgpr_count" in result.stdout

    def test_targets_via_cli(self) -> None:
        """Should list targets via CLI."""
        result = runner.invoke(app, ["amd", "isa", "targets"])

        assert result.exit_code == 0
        assert "gfx90a" in result.stdout or "gfx942" in result.stdout


class TestISAAnalyzerCliHelp:
    """Tests for ISA Analyzer command help text."""

    def test_isa_help(self) -> None:
        """Should display help for isa command group."""
        result = runner.invoke(app, ["amd", "isa", "--help"])

        assert result.exit_code == 0
        output = strip_ansi(result.stdout)
        assert "analyze" in output.lower() or "Analyze" in output
        assert "metrics" in output.lower()
        assert "targets" in output.lower()

    def test_amd_help_includes_isa(self) -> None:
        """AMD help should mention ISA analyzer."""
        result = runner.invoke(app, ["amd", "--help"])

        assert result.exit_code == 0
        assert "isa" in result.stdout.lower()


# ============================================================================
# Output Format Tests
# ============================================================================

class TestOutputFormats:
    """Tests for output formatting."""

    def test_text_output_spills_warning(self, tmp_path: Path) -> None:
        """Text output should show spills warning."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA_WITH_SPILLS)

        output = analyze_command(str(isa_file))

        assert "SPILLS" in output or "spills" in output.lower()

    def test_text_output_registers_section(self, tmp_path: Path) -> None:
        """Text output should have registers section."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file))

        assert "Registers" in output or "VGPRs" in output

    def test_text_output_memory_section(self, tmp_path: Path) -> None:
        """Text output should have memory section."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file))

        assert "Memory" in output or "LDS" in output

    def test_text_output_instructions_section(self, tmp_path: Path) -> None:
        """Text output should have instructions section."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file))

        assert "Instructions" in output or "MFMA" in output

    def test_text_output_occupancy_section(self, tmp_path: Path) -> None:
        """Text output should have occupancy section."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file))

        assert "Occupancy" in output or "waves" in output.lower()

    def test_json_output_has_all_fields(self, tmp_path: Path) -> None:
        """JSON output should include all analysis fields."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        output = analyze_command(str(isa_file), json_output=True)
        data = json.loads(output)
        analysis = data["isa_analysis"]

        # Check required fields
        assert "kernel_name" in analysis
        assert "architecture" in analysis
        assert "vgpr_count" in analysis
        assert "sgpr_count" in analysis
        assert "spill_count" in analysis
        assert "mfma_count" in analysis
        assert "mfma_density_pct" in analysis
        assert "instruction_mix" in analysis
        assert "theoretical_occupancy" in analysis
        assert "warnings" in analysis


# ============================================================================
# Filter Tests
# ============================================================================

class TestFiltering:
    """Tests for result filtering."""

    def test_filter_spills_greater_than_zero(self, tmp_path: Path) -> None:
        """Filter 'spills > 0' should only show files with spills."""
        (tmp_path / "no_spills.s").write_text(SAMPLE_ISA)
        (tmp_path / "has_spills.s").write_text(SAMPLE_ISA_WITH_SPILLS)

        output = analyze_command(str(tmp_path), filter_expr="spills > 0")

        # Should filter to only spilling kernel
        assert "1 files" in output or "Analyzed 1" in output

    def test_filter_vgpr_count(self, tmp_path: Path) -> None:
        """Filter on VGPR count should work."""
        (tmp_path / "small_vgpr.s").write_text(SAMPLE_ISA)  # 64 VGPRs
        (tmp_path / "large_vgpr.s").write_text(SAMPLE_ISA_WITH_SPILLS)  # 256 VGPRs

        output = analyze_command(str(tmp_path), filter_expr="vgpr_count > 128")

        # Should only show high-VGPR kernel
        assert "1 files" in output or "Analyzed 1" in output

    def test_filter_mfma_count(self, tmp_path: Path) -> None:
        """Filter on MFMA count should work."""
        (tmp_path / "has_mfma.s").write_text(SAMPLE_ISA)  # 2 MFMAs
        (tmp_path / "no_mfma.s").write_text(SAMPLE_ISA_WITH_SPILLS)  # 0 MFMAs

        output = analyze_command(str(tmp_path), filter_expr="mfma > 0")

        # Should show kernel with MFMA
        assert "1 files" in output or "has_mfma" in output

    def test_filter_invalid_expression(self, tmp_path: Path, capsys) -> None:
        """Invalid filter expression should warn."""
        (tmp_path / "kernel.s").write_text(SAMPLE_ISA)

        output = analyze_command(str(tmp_path), filter_expr="invalid filter")

        # Should still analyze, just warn about invalid filter
        # The function prints warning to stderr
        captured = capsys.readouterr()
        assert "Invalid" in captured.err or "Warning" in captured.err or "2 files" not in output


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_analyze_unsupported_file_type(self, tmp_path: Path) -> None:
        """Should handle unsupported file types gracefully."""
        txt_file = tmp_path / "file.xyz"
        txt_file.write_text("not ISA content")

        with pytest.raises(RuntimeError, match="Unsupported"):
            analyze_command(str(txt_file))

    def test_analyze_empty_directory(self, tmp_path: Path) -> None:
        """Should handle empty directories."""
        output = analyze_command(str(tmp_path))

        assert "0 files" in output or "No supported files" in output.lower()

    def test_analyze_directory_with_subdirs(self, tmp_path: Path) -> None:
        """Should scan subdirectories when recursive."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "kernel.s").write_text(SAMPLE_ISA)

        output = analyze_command(str(tmp_path), recursive=True)

        assert "1 files" in output or "test_kernel" in output


# ============================================================================
# Unified ISA Analyzer CLI Tests (supports .co, .s, .ll, .ttgir)
# ============================================================================


class TestUnifiedISAAnalyzerCLI:
    """Tests for unified ISA analyzer CLI command."""

    def test_cli_wafer_amd_isa_analyze_help(self) -> None:
        """wafer amd isa analyze --help should show help."""
        result = runner.invoke(app, ["amd", "isa", "analyze", "--help"])

        assert result.exit_code == 0
        assert "AMD GPU ISA" in result.output or "analyze" in result.output.lower()

    def test_cli_wafer_amd_isa_metrics(self) -> None:
        """wafer amd isa metrics should list available metrics."""
        result = runner.invoke(app, ["amd", "isa", "metrics"])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "vgpr_count" in output
        assert "spill_count" in output
        assert "mfma_count" in output

    def test_cli_wafer_amd_isa_targets(self) -> None:
        """wafer amd isa targets should list supported GPU targets."""
        result = runner.invoke(app, ["amd", "isa", "targets"])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "gfx90a" in output
        assert "gfx942" in output

    def test_cli_wafer_amd_isa_analyze_isa_file(self, tmp_path: Path) -> None:
        """wafer amd isa analyze should analyze .s files."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        result = runner.invoke(app, ["amd", "isa", "analyze", str(isa_file)])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "test_kernel" in output
        assert "gfx90a" in output

    def test_cli_wafer_amd_isa_analyze_json_output(self, tmp_path: Path) -> None:
        """wafer amd isa analyze --json should output JSON."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        result = runner.invoke(app, ["amd", "isa", "analyze", str(isa_file), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["file_type"] == "isa"
        assert data["isa_analysis"]["kernel_name"] == "test_kernel"

    def test_cli_wafer_amd_isa_analyze_csv_output(self, tmp_path: Path) -> None:
        """wafer amd isa analyze --csv should output CSV."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)

        result = runner.invoke(app, ["amd", "isa", "analyze", str(isa_file), "--csv"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2  # Header + data
        assert "kernel_name" in lines[0]
        assert "test_kernel" in lines[1]

    def test_cli_wafer_amd_isa_analyze_co_uses_api(self, tmp_path: Path) -> None:
        """wafer amd isa analyze on .co should attempt API call."""
        co_file = tmp_path / "kernel.co"
        co_file.write_bytes(b"fake code object")

        result = runner.invoke(app, ["amd", "isa", "analyze", str(co_file)])

        # Should exit with error (API call will fail in test environment)
        # The error could be auth-related or API unavailable
        assert result.exit_code != 0
        output = result.output.lower()
        assert "error" in output or "api" in output or "failed" in output

    def test_cli_wafer_amd_isa_analyze_nonexistent_file(self) -> None:
        """wafer amd isa analyze should error on nonexistent file."""
        result = runner.invoke(app, ["amd", "isa", "analyze", "/nonexistent/path.s"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_cli_wafer_amd_isa_analyze_directory(self, tmp_path: Path) -> None:
        """wafer amd isa analyze should analyze directories."""
        (tmp_path / "kernel1.s").write_text(SAMPLE_ISA)
        (tmp_path / "kernel2.s").write_text(SAMPLE_ISA_WITH_SPILLS)

        result = runner.invoke(app, ["amd", "isa", "analyze", str(tmp_path)])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "2 files" in output
        assert "Successful" in output or "successful" in output

    def test_cli_wafer_amd_isa_analyze_with_filter(self, tmp_path: Path) -> None:
        """wafer amd isa analyze --filter should filter results."""
        (tmp_path / "no_spills.s").write_text(SAMPLE_ISA)
        (tmp_path / "has_spills.s").write_text(SAMPLE_ISA_WITH_SPILLS)

        result = runner.invoke(
            app, 
            ["amd", "isa", "analyze", str(tmp_path), "--filter", "spills > 0"]
        )

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        # Should only show the file with spills
        assert "1 files" in output or "spilling_kernel" in output

    def test_cli_wafer_amd_isa_analyze_output_to_file(self, tmp_path: Path) -> None:
        """wafer amd isa analyze --output should write to file."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA)
        output_file = tmp_path / "output.json"

        result = runner.invoke(
            app, 
            ["amd", "isa", "analyze", str(isa_file), "--json", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["success"] is True

    def test_analyze_command_with_api_params(self, tmp_path: Path) -> None:
        """analyze_command should accept API params for .co files."""
        co_file = tmp_path / "kernel.co"
        co_file.write_bytes(b"fake code object")

        # Even with fake API params, should attempt to call API
        # (will fail because .co file doesn't exist at API, but params are passed)
        with pytest.raises(RuntimeError) as exc_info:
            analyze_command(
                str(co_file),
                api_url="https://fake.api.wafer.dev",
                auth_headers={"Authorization": "Bearer fake"}
            )
        
        # Should have tried to make API call (not just reject due to missing params)
        assert "API error" in str(exc_info.value) or "Request failed" in str(exc_info.value)
