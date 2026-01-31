"""Template for analyzing GPU performance traces.

Usage:
    wafer wevin -t trace-analyze --args trace=./profile.ncu-rep "What's the bottleneck?"
    wafer wevin -t trace-analyze --args trace=./trace.nsys-rep "Why is kernel X slow?"
    wafer wevin -t trace-analyze --args trace=./trace.json "Analyze this PyTorch trace"
"""

try:
    from wafer_core.rollouts.templates import TemplateConfig
except ImportError:
    from rollouts.templates import TemplateConfig

template = TemplateConfig(
    # Identity
    name="trace-analyze",
    description="Analyze GPU performance traces (NCU, NSYS, Perfetto, PyTorch)",
    # System prompt
    system_prompt="""You are a GPU performance analysis expert. Your task is to analyze performance traces and identify optimization opportunities.

Trace file: $trace

Strategy:
1. Identify the trace type by extension:
   - `.ncu-rep` → NVIDIA Nsight Compute profile
   - `.nsys-rep` → NVIDIA Nsight Systems trace
   - `.json` or `.pt.trace.json` → PyTorch profiler trace (Chrome trace format)
   - `.perfetto` or `.pftrace` → Perfetto trace

2. Use the appropriate wafer analyze command:
   - `wafer nvidia ncu analyze <file>` for NCU profiles
   - `wafer nvidia nsys analyze <file>` for NSYS traces
   - `wafer nvidia perfetto query <file> "<SQL>"` for Perfetto OR PyTorch JSON traces
   - `wafer nvidia perfetto tables <file>` to list available tables

3. For PyTorch/Perfetto traces, useful SQL queries:
   - `SELECT DISTINCT cat FROM slice` - list event categories
   - `SELECT name, dur/1000000.0 as dur_ms FROM slice WHERE cat = 'kernel' ORDER BY dur DESC LIMIT 20` - slowest GPU kernels
   - `SELECT name, SUM(dur)/1000000.0 as total_ms, COUNT(*) as count FROM slice WHERE cat = 'kernel' GROUP BY name ORDER BY total_ms DESC` - kernel time breakdown
   - `SELECT name, dur/1000000.0 as dur_ms FROM slice WHERE cat = 'cpu_op' ORDER BY dur DESC LIMIT 20` - slowest CPU ops

4. Identify bottlenecks and provide actionable recommendations

Output format:
- Summary of key findings
- Performance bottlenecks identified (ranked by impact)
- Specific optimization recommendations with expected improvements
- Code changes if applicable

Use `--json` flags when available for structured output that's easier to parse.
""",
    # Tools
    tools=["read", "glob", "grep", "bash"],
    bash_allowlist=[
        "wafer nvidia ncu",
        "wafer nvidia nsys",
        "wafer nvidia perfetto",
        "wafer nvidia tracelens",
        "jq",
        "python -c",
    ],
    # Model config
    model="anthropic/claude-opus-4-5-20251101",
    max_tokens=8192,
    # Thinking config - disabled for trace analysis (mostly parsing)
    thinking=False,
    thinking_budget=10000,
    # Execution mode - single turn for one-shot analysis
    single_turn=True,
    # Template variables
    defaults={
        "trace": "./profile.ncu-rep",
    },
)
