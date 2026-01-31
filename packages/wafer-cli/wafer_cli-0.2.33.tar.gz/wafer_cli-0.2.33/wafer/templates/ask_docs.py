"""Template for querying GPU documentation.

Usage:
    wafer wevin -t ask-docs "How do bank conflicts occur?"
    wafer wevin -t ask-docs --args corpus=./cuda-docs/ "Explain warp divergence"
"""

try:
    from wafer_core.rollouts.templates import TemplateConfig
except ImportError:
    from rollouts.templates import TemplateConfig

# NOTE: Agent tends to prefer bash (find, ls) over glob/grep tools despite system prompt
# guidance. Expanded allowlist so this works. TODO: improve error display when blocked
# commands are attempted (currently shows ❌ but error message not visible in TUI).
template = TemplateConfig(
    # Identity
    name="ask-docs",
    description="Query GPU documentation to answer technical questions",
    # System prompt
    system_prompt="""You are a GPU programming expert helping answer questions about CUDA, GPU architecture, and kernel optimization.

Your task: Answer the user's question using the available documentation and tools.

You have these tools available:
- **glob**: Find files by pattern (e.g., glob pattern="**/*.md")
- **grep**: Search file contents (e.g., grep pattern="shared memory" path=".")
- **read**: Read file contents (e.g., read file_path="./guide.md")
- **bash**: Run shell commands (ls, find, cat, head, tail, wc, jq, python -c)

Strategy:
1. Use the glob tool to find relevant documentation files (e.g., glob pattern="**/*.md")
2. Use the grep tool to search for relevant content (e.g., grep pattern="your topic")
3. Use the read tool to examine promising files
4. Synthesize a clear, accurate answer

Prefer glob/grep/read tools over bash equivalents when possible, but bash is available for common commands.

Output your answer directly. Be concise but thorough. Include code examples when relevant.
""",
    # Tools
    tools=["read", "glob", "grep", "bash"],
    bash_allowlist=[
        "ls",
        "find",
        "cat",
        "head",
        "tail",
        "wc",
        "jq",
        "python -c",
    ],
    # Model config
    model="anthropic/claude-opus-4-5-20251101",
    max_tokens=8192,
    # Thinking config - disabled for simple doc queries
    thinking=False,
    thinking_budget=10000,
    # Execution mode - multi-turn for follow-up questions
    single_turn=False,
)
