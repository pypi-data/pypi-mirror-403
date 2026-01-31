"""Structured output formatting for CLI commands.

Provides JSON and JSONL output formats for machine-readable CLI output.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal

import typer

if TYPE_CHECKING:
    from .evaluate import EvaluateResult


class OutputFormat(StrEnum):
    """Output format for CLI commands."""

    TEXT = "text"  # Human-readable (default)
    JSON = "json"  # Single JSON object at end
    JSONL = "jsonl"  # Streaming JSON Lines


@dataclass
class EvalOutput:
    """Structured evaluation result for JSON output."""

    status: Literal["success", "failure", "error"]
    target: str | None = None
    phase: str | None = None
    correctness: dict[str, Any] | None = None
    benchmark: dict[str, Any] | None = None
    profile: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    raw_compiler_output: str | None = None

    def to_json(self, indent: int | None = 2) -> str:
        """Serialize to JSON, excluding None values."""
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(data, indent=indent, default=str)


@dataclass
class OutputCollector:
    """Collects output events and formats them according to the output format."""

    format: OutputFormat
    target: str | None = None
    _result: EvalOutput = field(default_factory=lambda: EvalOutput(status="success"))

    def emit(self, event: str, **data: Any) -> None:
        """Emit an event.

        For JSONL format, prints immediately. For TEXT, prints human-readable.
        For JSON, events are collected and output at the end.
        """
        if self.format == OutputFormat.JSONL:
            obj = {
                "event": event,
                "timestamp": datetime.now(UTC).isoformat(),
                **data,
            }
            print(json.dumps(obj, default=str), flush=True)
        elif self.format == OutputFormat.TEXT:
            status = data.get("status", "")
            if status:
                typer.echo(f"[wafer] {event}: {status}")
            else:
                typer.echo(f"[wafer] {event}")

    def set_result(
        self,
        *,
        status: Literal["success", "failure", "error"],
        phase: str | None = None,
        correctness: dict[str, Any] | None = None,
        benchmark: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        raw_compiler_output: str | None = None,
    ) -> None:
        """Set the final result data."""
        self._result = EvalOutput(
            status=status,
            target=self.target,
            phase=phase,
            correctness=correctness,
            benchmark=benchmark,
            profile=profile,
            error=error,
            raw_compiler_output=raw_compiler_output,
        )

    def set_error(self, phase: str, error_type: str, **details: Any) -> None:
        """Set an error result."""
        self._result.status = "error"
        self._result.phase = phase
        self._result.error = {"type": error_type, **details}
        self._result.target = self.target

    def finalize(self) -> None:
        """Print final output based on format."""
        if self.format == OutputFormat.JSON:
            print(self._result.to_json())
        elif self.format == OutputFormat.JSONL:
            print(
                json.dumps(
                    {
                        "event": "completed",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "result": {k: v for k, v in asdict(self._result).items() if v is not None},
                    },
                    default=str,
                )
            )
        # TEXT format already printed incrementally

    def output_text_result(self, result: EvaluateResult) -> None:
        """Print human-readable result summary (TEXT format only)."""
        if self.format != OutputFormat.TEXT:
            return

        typer.echo("")
        typer.echo("=" * 60)
        # Handle None (correctness not run), True (pass), False (fail)
        if result.all_correct is None:
            status = "OK"  # Correctness wasn't checked (e.g., compile-only or prepare-only)
        elif result.all_correct:
            status = "PASS"
        else:
            status = "FAIL"
        typer.echo(f"Result: {status}")
        if result.total_tests > 0:
            score_pct = f"{result.correctness_score:.1%}"
            typer.echo(f"Correctness: {result.passed_tests}/{result.total_tests} ({score_pct})")
        if result.geomean_speedup > 0:
            typer.echo(f"Speedup: {result.geomean_speedup:.2f}x")
        typer.echo("=" * 60)

    def output_text_error(self, error_message: str) -> None:
        """Print error message (TEXT format only)."""
        if self.format == OutputFormat.TEXT:
            typer.echo(f"Error: {error_message}", err=True)


def format_evaluate_result(result: EvaluateResult, target: str | None = None) -> EvalOutput:
    """Convert EvaluateResult to structured EvalOutput."""
    if not result.success:
        # Error case
        error_info = parse_error_message(result.error_message or "Unknown error")
        return EvalOutput(
            status="error",
            target=target,
            phase=error_info.get("phase", "unknown"),
            error=error_info,
        )

    if not result.all_correct:
        # Correctness failure
        return EvalOutput(
            status="failure",
            target=target,
            phase="correctness",
            correctness={
                "passed": False,
                "tests_run": result.total_tests,
                "tests_passed": result.passed_tests,
            },
        )

    # Success
    output = EvalOutput(
        status="success",
        target=target,
        correctness={
            "passed": True,
            "tests_run": result.total_tests,
            "tests_passed": result.passed_tests,
        },
    )

    if result.geomean_speedup > 0:
        output.benchmark = {"speedup": result.geomean_speedup}

    return output


def parse_error_message(error_message: str) -> dict[str, Any]:
    """Parse error message to extract structured information."""
    error_info: dict[str, Any] = {"message": error_message}

    # Try to identify the phase and type from common patterns
    error_lower = error_message.lower()

    if "compilation" in error_lower or "compile" in error_lower:
        error_info["phase"] = "compilation"
        error_info["type"] = "CompilationError"
        # Try to parse compiler error format: file:line:col: error: message
        parsed = parse_compilation_error(error_message)
        if parsed:
            error_info.update(parsed)
    elif "hsa_status" in error_lower or "memory" in error_lower or "segfault" in error_lower:
        error_info["phase"] = "runtime"
        error_info["type"] = "MemoryViolation"
    elif "timeout" in error_lower:
        error_info["phase"] = "runtime"
        error_info["type"] = "Timeout"
    elif "correctness" in error_lower:
        error_info["phase"] = "correctness"
        error_info["type"] = "CorrectnessError"
    else:
        error_info["phase"] = "unknown"
        error_info["type"] = "UnknownError"

    return error_info


def parse_compilation_error(raw_output: str) -> dict[str, Any] | None:
    """Extract structured info from compiler error output.

    Matches patterns like: file.hip:10:14: error: message
    """
    match = re.search(
        r"(?P<file>[\w./]+):(?P<line>\d+):(?P<col>\d+): error: (?P<message>.+)",
        raw_output,
    )
    if match:
        return {
            "file": match.group("file"),
            "line": int(match.group("line")),
            "column": int(match.group("col")),
            "message": match.group("message").strip(),
        }
    return None


def get_output_format(json_flag: bool, jsonl_flag: bool) -> OutputFormat:
    """Determine output format from CLI flags."""
    if jsonl_flag:
        return OutputFormat.JSONL
    if json_flag:
        return OutputFormat.JSON
    return OutputFormat.TEXT
