"""Tests for structured output formatting (--json, --jsonl flags)."""

import json
from dataclasses import dataclass

import pytest

from wafer.output import (
    EvalOutput,
    OutputCollector,
    OutputFormat,
    format_evaluate_result,
    get_output_format,
    parse_compilation_error,
    parse_error_message,
)


@dataclass
class MockEvaluateResult:
    """Mock EvaluateResult for testing without importing the real class."""

    success: bool
    all_correct: bool
    correctness_score: float
    geomean_speedup: float
    passed_tests: int
    total_tests: int
    error_message: str | None = None


class TestOutputFormat:
    """Test OutputFormat enum."""

    def test_enum_values(self) -> None:
        assert OutputFormat.TEXT.value == "text"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.JSONL.value == "jsonl"


class TestGetOutputFormat:
    """Test get_output_format helper."""

    def test_default_is_text(self) -> None:
        assert get_output_format(False, False) == OutputFormat.TEXT

    def test_json_flag(self) -> None:
        assert get_output_format(True, False) == OutputFormat.JSON

    def test_jsonl_flag(self) -> None:
        assert get_output_format(False, True) == OutputFormat.JSONL

    def test_jsonl_takes_precedence(self) -> None:
        # If both are set, JSONL wins (streaming is more specific)
        assert get_output_format(True, True) == OutputFormat.JSONL


class TestEvalOutput:
    """Test EvalOutput dataclass."""

    def test_success_output(self) -> None:
        output = EvalOutput(
            status="success",
            target="runpod-mi300x",
            correctness={"passed": True, "tests_run": 1, "tests_passed": 1},
            benchmark={"speedup": 2.5},
        )
        data = json.loads(output.to_json())
        assert data["status"] == "success"
        assert data["target"] == "runpod-mi300x"
        assert data["correctness"]["passed"] is True
        assert data["benchmark"]["speedup"] == 2.5
        # None fields should not appear
        assert "phase" not in data
        assert "error" not in data

    def test_error_output(self) -> None:
        output = EvalOutput(
            status="error",
            target="runpod-mi300x",
            phase="compilation",
            error={"type": "CompilationError", "message": "syntax error"},
        )
        data = json.loads(output.to_json())
        assert data["status"] == "error"
        assert data["phase"] == "compilation"
        assert data["error"]["type"] == "CompilationError"


class TestOutputCollector:
    """Test OutputCollector class."""

    def test_text_emit(self, capsys: pytest.CaptureFixture[str]) -> None:
        collector = OutputCollector(format=OutputFormat.TEXT)
        collector.emit("started", status="connecting")
        captured = capsys.readouterr()
        assert "[wafer] started: connecting" in captured.out

    def test_json_emit_does_not_print(self, capsys: pytest.CaptureFixture[str]) -> None:
        collector = OutputCollector(format=OutputFormat.JSON)
        collector.emit("started", status="connecting")
        captured = capsys.readouterr()
        # JSON format should not print until finalize
        assert captured.out == ""

    def test_jsonl_emit_prints_immediately(self, capsys: pytest.CaptureFixture[str]) -> None:
        collector = OutputCollector(format=OutputFormat.JSONL)
        collector.emit("started", status="connecting")
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert data["event"] == "started"
        assert data["status"] == "connecting"
        assert "timestamp" in data

    def test_json_finalize(self, capsys: pytest.CaptureFixture[str]) -> None:
        collector = OutputCollector(format=OutputFormat.JSON, target="test-target")
        collector.set_result(
            status="success",
            correctness={"passed": True, "tests_run": 1, "tests_passed": 1},
        )
        collector.finalize()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "success"
        assert data["target"] == "test-target"

    def test_jsonl_finalize(self, capsys: pytest.CaptureFixture[str]) -> None:
        collector = OutputCollector(format=OutputFormat.JSONL, target="test-target")
        collector.set_result(
            status="success",
            correctness={"passed": True, "tests_run": 1, "tests_passed": 1},
        )
        collector.finalize()
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert data["event"] == "completed"
        assert data["result"]["status"] == "success"

    def test_text_finalize_does_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        collector = OutputCollector(format=OutputFormat.TEXT)
        collector.set_result(status="success")
        collector.finalize()
        captured = capsys.readouterr()
        # TEXT format relies on output_text_result, not finalize
        assert captured.out == ""

    def test_set_error(self) -> None:
        collector = OutputCollector(format=OutputFormat.JSON)
        collector.set_error("compilation", "CompilationError", line=10, message="syntax error")
        assert collector._result.status == "error"
        assert collector._result.phase == "compilation"
        assert collector._result.error["type"] == "CompilationError"
        assert collector._result.error["line"] == 10


class TestFormatEvaluateResult:
    """Test format_evaluate_result function."""

    def test_success_result(self) -> None:
        result = MockEvaluateResult(
            success=True,
            all_correct=True,
            correctness_score=1.0,
            geomean_speedup=2.5,
            passed_tests=3,
            total_tests=3,
        )
        output = format_evaluate_result(result, target="test-target")  # type: ignore[arg-type]
        assert output.status == "success"
        assert output.target == "test-target"
        assert output.correctness["passed"] is True
        assert output.correctness["tests_run"] == 3
        assert output.benchmark["speedup"] == 2.5

    def test_correctness_failure(self) -> None:
        result = MockEvaluateResult(
            success=True,
            all_correct=False,
            correctness_score=0.5,
            geomean_speedup=1.0,
            passed_tests=1,
            total_tests=2,
        )
        output = format_evaluate_result(result, target="test-target")  # type: ignore[arg-type]
        assert output.status == "failure"
        assert output.phase == "correctness"
        assert output.correctness["passed"] is False

    def test_error_result(self) -> None:
        result = MockEvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message="Compilation failed: syntax error at line 10",
        )
        output = format_evaluate_result(result, target="test-target")  # type: ignore[arg-type]
        assert output.status == "error"
        assert output.error is not None

    def test_no_speedup_excludes_benchmark(self) -> None:
        result = MockEvaluateResult(
            success=True,
            all_correct=True,
            correctness_score=1.0,
            geomean_speedup=0.0,  # No benchmark run
            passed_tests=1,
            total_tests=1,
        )
        output = format_evaluate_result(result, target="test-target")  # type: ignore[arg-type]
        assert output.benchmark is None


class TestParseCompilationError:
    """Test parse_compilation_error function."""

    def test_standard_compiler_error(self) -> None:
        raw = "kernel.hip:10:14: error: expected ';' at end of declaration"
        result = parse_compilation_error(raw)
        assert result is not None
        assert result["file"] == "kernel.hip"
        assert result["line"] == 10
        assert result["column"] == 14
        assert "expected ';'" in result["message"]

    def test_path_with_directories(self) -> None:
        raw = "src/kernels/conv2d.hip:42:8: error: unknown type 'float4'"
        result = parse_compilation_error(raw)
        assert result is not None
        assert result["file"] == "src/kernels/conv2d.hip"
        assert result["line"] == 42

    def test_no_match(self) -> None:
        raw = "Some other error message without line info"
        result = parse_compilation_error(raw)
        assert result is None


class TestParseErrorMessage:
    """Test parse_error_message function."""

    def test_compilation_error(self) -> None:
        result = parse_error_message("Compilation failed: kernel.hip:10:5: error: bad syntax")
        assert result["phase"] == "compilation"
        assert result["type"] == "CompilationError"
        assert result["file"] == "kernel.hip"

    def test_memory_error(self) -> None:
        result = parse_error_message("HSA_STATUS_ERROR_MEMORY_APERTURE_VIOLATION")
        assert result["phase"] == "runtime"
        assert result["type"] == "MemoryViolation"

    def test_timeout_error(self) -> None:
        result = parse_error_message("Evaluation timeout after 300 seconds")
        assert result["phase"] == "runtime"
        assert result["type"] == "Timeout"

    def test_unknown_error(self) -> None:
        result = parse_error_message("Something unexpected happened")
        assert result["phase"] == "unknown"
        assert result["type"] == "UnknownError"
