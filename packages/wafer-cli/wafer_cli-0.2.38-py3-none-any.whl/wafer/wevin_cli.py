"""Wafer Wevin CLI - thin wrapper that calls rollouts in-process.

Adds:
- Wafer auth (proxy token from ~/.wafer/credentials.json)
- Wafer templates (ask-docs, optimize-kernel, trace-analyze)
- Corpus path resolution (--corpus cuda -> ~/.cache/wafer/corpora/cuda)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from wafer_core.rollouts import Endpoint, Environment
    from wafer_core.rollouts.dtypes import StreamEvent, ToolCall
    from wafer_core.rollouts.templates import TemplateConfig


class StreamingChunkFrontend:
    """Frontend that emits real-time JSON chunk events.

    Designed for programmatic consumption by extensions/UIs.
    Emits events in the format expected by wevin-extension handleWevinEvent:
    - {type: 'session_start', session_id: '...', model: '...'}
    - {type: 'text_delta', delta: '...'}
    - {type: 'tool_call_start', tool_name: '...'}
    - {type: 'tool_call_end', tool_name: '...', args: {...}}
    - {type: 'tool_result', is_error: bool}
    - {type: 'session_end'}
    - {type: 'error', error: '...'}
    """

    def __init__(self, session_id: str | None = None, model: str | None = None) -> None:
        self._current_tool_call: dict | None = None
        self._session_id = session_id
        self._model = model

    def _emit(self, obj: dict) -> None:
        """Emit a single NDJSON line."""
        print(json.dumps(obj, ensure_ascii=False), flush=True)

    async def start(self) -> None:
        """Initialize frontend and emit session_start if session_id is known."""
        if self._session_id:
            self._emit({
                "type": "session_start",
                "session_id": self._session_id,
                "model": self._model,
            })

    def emit_session_start(self, session_id: str, model: str | None = None) -> None:
        """Emit session_start event (for new sessions created during run)."""
        self._emit({
            "type": "session_start",
            "session_id": session_id,
            "model": model or self._model,
        })

    async def stop(self) -> None:
        """Emit session_end event."""
        self._emit({"type": "session_end"})

    async def handle_event(self, event: StreamEvent) -> None:
        """Handle streaming event by emitting JSON."""
        from wafer_core.rollouts.dtypes import (
            StreamDone,
            StreamError,
            TextDelta,
            ThinkingDelta,
            ToolCallEnd,
            ToolCallStart,
            ToolResultReceived,
        )

        if isinstance(event, TextDelta):
            # Emit text delta immediately for real-time streaming
            self._emit({"type": "text_delta", "delta": event.delta})

        elif isinstance(event, ThinkingDelta):
            # Skip thinking tokens (they clutter the output)
            pass

        elif isinstance(event, ToolCallStart):
            # Emit tool_call_start event (ToolCallStart has flat attributes)
            self._current_tool_call = {
                "id": event.tool_call_id,
                "name": event.tool_name,
            }
            self._emit({"type": "tool_call_start", "tool_name": event.tool_name})

        elif isinstance(event, ToolCallEnd):
            # Emit tool_call_end event with tool name and args
            tool_call = event.tool_call
            self._emit({
                "type": "tool_call_end",
                "tool_name": tool_call.name,
                "args": tool_call.args if tool_call.args else {},
            })

        elif isinstance(event, ToolResultReceived):
            # Emit tool_result event with error details
            result_event = {"type": "tool_result", "is_error": event.is_error}
            # Include error message and content if available
            if event.error:
                result_event["error"] = event.error
            if event.content:
                # Convert content to string if it's a list
                if isinstance(event.content, list):
                    result_event["content"] = "\n".join(
                        str(item) if not isinstance(item, dict) else item.get("text", str(item))
                        for item in event.content
                    )
                else:
                    result_event["content"] = str(event.content)
            self._emit(result_event)

        elif isinstance(event, StreamDone):
            # Will be handled by stop()
            pass

        elif isinstance(event, StreamError):
            self._emit({"type": "error", "error": str(event.error)})

    async def get_input(self, prompt: str = "") -> str:
        """Get user input - not supported in JSON mode."""
        raise RuntimeError(
            "StreamingChunkFrontend does not support interactive input. "
            "Use -p to provide input or use -s for single-turn mode."
        )

    async def confirm_tool(self, tool_call: ToolCall) -> bool:
        """Auto-approve all tools in JSON mode."""
        return True

    def show_loader(self, text: str) -> None:
        """No-op for JSON mode."""
        pass

    def hide_loader(self) -> None:
        """No-op for JSON mode."""
        pass


def _make_wafer_token_refresh() -> Callable[[], Awaitable[str | None]]:
    """Create an async callback that refreshes the wafer proxy token via Supabase."""
    from .auth import load_credentials, refresh_access_token, save_credentials

    async def _refresh() -> str | None:
        creds = load_credentials()
        if not creds or not creds.refresh_token:
            return None
        try:
            new_access, new_refresh = refresh_access_token(creds.refresh_token)
            save_credentials(new_access, new_refresh, creds.email)
            return new_access
        except Exception:
            return None

    return _refresh


def _get_wafer_auth(
    *, no_proxy: bool = False
) -> tuple[str | None, str | None, Callable[[], Awaitable[str | None]] | None]:
    """Get wafer auth credentials with fallback chain.

    Returns:
        (api_base, api_key, api_key_refresh) or (None, None, None) if no auth found.
        api_key_refresh is an async callback for mid-session token refresh (only set
        when using wafer proxy via credentials file).
    """
    from .auth import get_valid_token, load_credentials
    from .global_config import get_api_url

    if no_proxy:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            # Try auth.json stored key
            from wafer_core.auth import get_api_key

            api_key = get_api_key("anthropic") or ""
        if api_key:
            print("🔑 Using ANTHROPIC_API_KEY (--no-proxy)\n", file=sys.stderr)
            return "https://api.anthropic.com", api_key, None
        print(
            "❌ --no-proxy requires ANTHROPIC_API_KEY env var or `wafer auth login anthropic`\n",
            file=sys.stderr,
        )
        return None, None, None

    # Check WAFER_AUTH_TOKEN env var first
    wafer_token = os.environ.get("WAFER_AUTH_TOKEN", "")
    token_source = "WAFER_AUTH_TOKEN" if wafer_token else None

    # Try credentials file with automatic refresh
    had_credentials = False
    uses_credentials_file = False
    if not wafer_token:
        try:
            creds = load_credentials()
            had_credentials = creds is not None and bool(creds.access_token)
        except Exception:
            pass
        wafer_token = get_valid_token()
        if wafer_token:
            token_source = "~/.wafer/credentials.json"
            uses_credentials_file = True

    # If we have a valid wafer token, use it
    if wafer_token:
        api_url = get_api_url()
        print(f"🔑 Using wafer proxy ({token_source})\n", file=sys.stderr)
        # Only provide refresh callback when token came from credentials file
        # (env var tokens are managed externally)
        refresh = _make_wafer_token_refresh() if uses_credentials_file else None
        return f"{api_url}/v1/anthropic", wafer_token, refresh

    # Fall back to direct anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        if had_credentials:
            print(
                "⚠️  Wafer credentials expired/invalid, falling back to ANTHROPIC_API_KEY\n",
                file=sys.stderr,
            )
        else:
            print("🔑 Using ANTHROPIC_API_KEY\n", file=sys.stderr)
        return "https://api.anthropic.com", api_key, None

    return None, None, None


def _get_session_preview(session: object) -> str:
    """Extract first user message preview from a session."""
    messages = getattr(session, "messages", None)
    if not messages:
        return ""
    for msg in messages:
        if msg.role == "user" and isinstance(msg.content, str):
            preview = msg.content[:50].replace("\n", " ")
            if len(msg.content) > 50:
                preview += "..."
            return preview
    return ""


def _get_log_file_path() -> Path:
    """Get user-specific log file path, creating directory if needed.

    Uses ~/.wafer/logs/ to avoid permission issues with shared /tmp.
    """
    log_dir = Path.home() / ".wafer" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "wevin_debug.log"


def _setup_logging() -> None:
    """Configure logging to file only (no console spam)."""
    import logging.config

    log_file = _get_log_file_path()

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": '{"ts": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "msg": "%(message)s"}',
            },
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_file),
                "maxBytes": 10_000_000,
                "backupCount": 3,
                "formatter": "json",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["file"]},
    })


def _unwrap_exception(e: BaseException) -> BaseException:
    """Unwrap ExceptionGroup from Trio to get the actual error."""
    actual = e
    while isinstance(actual, ExceptionGroup) and actual.exceptions:
        actual = actual.exceptions[0]
    return actual


def _build_endpoint(
    tpl: TemplateConfig,
    model_override: str | None,
    api_base: str,
    api_key: str,
    api_key_refresh: Callable[[], Awaitable[str | None]] | None = None,
) -> Endpoint:
    """Build an Endpoint from template config and auth."""
    from wafer_core.rollouts import Endpoint

    resolved_model = model_override or tpl.model
    provider, model_id = resolved_model.split("/", 1)
    thinking_config = (
        {"type": "enabled", "budget_tokens": tpl.thinking_budget} if tpl.thinking else None
    )
    return Endpoint(
        provider=provider,
        model=model_id,
        api_base=api_base,
        api_key=api_key,
        api_key_refresh=api_key_refresh,
        thinking=thinking_config,
        max_tokens=tpl.max_tokens,
    )


def _build_environment(
    tpl: TemplateConfig,
    tools_override: list[str] | None,
    corpus_path: str | None,
    no_sandbox: bool = False,
) -> Environment:
    """Build a CodingEnvironment from template config."""
    from wafer_core.environments.coding import CodingEnvironment
    from wafer_core.rollouts.templates import DANGEROUS_BASH_COMMANDS
    from wafer_core.sandbox import SandboxMode

    working_dir = Path(corpus_path) if corpus_path else Path.cwd()
    resolved_tools = list(tools_override or tpl.tools)

    # Add skill tool if skills are enabled
    if tpl.include_skills and "skill" not in resolved_tools:
        resolved_tools.append("skill")

    sandbox_mode = SandboxMode.DISABLED if no_sandbox else SandboxMode.ENABLED
    env: Environment = CodingEnvironment(
        working_dir=working_dir,
        enabled_tools=resolved_tools,
        bash_allowlist=tpl.bash_allowlist,
        bash_denylist=DANGEROUS_BASH_COMMANDS,
        sandbox_mode=sandbox_mode,
    )  # type: ignore[assignment]
    return env


def _resolve_session_id(resume: str | None, session_store: object) -> str | None:
    """Resolve session ID from resume arg. Exits on error."""
    if not resume:
        return None
    session_id = resume if resume != "last" else session_store.get_latest_id_sync()  # type: ignore[union-attr]
    if not session_id:
        print("Error: No session to resume", file=sys.stderr)
        sys.exit(1)
    return session_id


def _get_default_template() -> TemplateConfig:
    """Return the default agent template with full wafer tooling."""
    from wafer_core.rollouts.templates import TemplateConfig

    return TemplateConfig(
        name="default",
        description="GPU kernel development assistant",
        system_prompt="""You are a GPU kernel development assistant. You help with CUDA/Triton kernel optimization, profiling, and debugging.

You have access to these tools:

**File tools:**
- read: Read file contents
- write: Create new files
- edit: Modify existing files
- glob: Find files by pattern
- grep: Search file contents

**Bash:** Run shell commands including wafer CLI tools:
- `wafer evaluate --impl kernel.py --reference ref.py --test-cases tests.json` - Test kernel correctness and performance
- `wafer nvidia ncu analyze <file.ncu-rep>` - Analyze NCU profiling reports
- `wafer nvidia nsys analyze <file.nsys-rep>` - Analyze Nsight Systems traces
- `wafer nvidia perfetto tables <trace.json>` - Query Perfetto traces
- `wafer config targets list` - List available GPU targets

When asked to profile or analyze kernels, use the appropriate wafer commands. Be concise and focus on actionable insights.""",
        tools=["read", "write", "edit", "glob", "grep", "bash"],
    )


def _load_template(
    template_name: str, template_args: dict[str, str] | None = None
) -> tuple[TemplateConfig | None, str | None]:
    """Load a wafer template. Returns (template, error)."""
    try:
        from wafer_core.rollouts.templates import load_template
        from wafer_core.rollouts.templates.loader import _get_search_paths

        # Prepend wafer-cli bundled templates to default search paths
        bundled_templates = Path(__file__).parent / "templates"
        search_paths = _get_search_paths()
        if bundled_templates.exists():
            search_paths = [bundled_templates] + search_paths

        template: TemplateConfig = load_template(template_name, search_paths=search_paths)
        # Interpolate prompt variables but keep the full config
        _ = template.interpolate_prompt(template_args or {})  # validates variables exist
        return template, None
    except Exception as e:
        return None, str(e)


def main(  # noqa: PLR0913, PLR0915
    prompt: str | None = None,
    interactive: bool = False,
    single_turn: bool | None = None,  # None = use template default
    model: str | None = None,
    resume: str | None = None,
    from_turn: int | None = None,
    tools: list[str] | None = None,
    allow_spawn: bool = False,
    max_tool_fails: int | None = None,
    max_turns: int | None = None,
    template: str | None = None,
    template_args: dict[str, str] | None = None,
    corpus_path: str | None = None,
    list_sessions: bool = False,
    get_session: str | None = None,
    json_output: bool = False,
    no_sandbox: bool = False,
    no_proxy: bool = False,
) -> None:
    """Run wevin agent in-process via rollouts."""
    from dataclasses import asdict

    import trio
    from wafer_core.rollouts import FileSessionStore

    session_store = FileSessionStore()

    # Handle --get-session: load session by ID and print
    if get_session:

        async def _get_session() -> None:
            try:
                session, err = await session_store.get(get_session)
                if err or not session:
                    if json_output:
                        print(json.dumps({"error": err or f"Session {get_session} not found"}))
                        sys.exit(1)
                    else:
                        print(f"Error: {err or 'Session not found'}", file=sys.stderr)
                        sys.exit(1)

                if json_output:
                    # Serialize messages to dicts
                    try:
                        messages_data = [asdict(msg) for msg in session.messages]
                    except Exception as e:
                        # If serialization fails, return error
                        error_msg = f"Failed to serialize messages: {e}"
                        print(json.dumps({"error": error_msg}))
                        sys.exit(1)

                    print(
                        json.dumps({
                            "session_id": session.session_id,
                            "status": session.status.value,
                            "model": session.endpoint.model if session.endpoint else None,
                            "created_at": session.created_at,
                            "updated_at": session.updated_at,
                            "messages": messages_data,
                            "tags": session.tags,
                        })
                    )
                else:
                    print(f"Session: {session.session_id}")
                    print(f"Status: {session.status.value}")
                    print(f"Messages: {len(session.messages)}")
                    for i, msg in enumerate(session.messages):
                        # Fail fast if message can't be converted to string - corrupted data is a bug
                        content_preview = str(msg.content)[:100] if msg.content else ""
                        print(f"  [{i}] {msg.role}: {content_preview}...")
            except KeyboardInterrupt:
                # User cancelled - exit cleanly
                sys.exit(130)  # Standard exit code for SIGINT
            except Exception as e:
                # Any other error - log and exit with error
                error_msg = f"Failed to load session {get_session}: {e}"
                if json_output:
                    print(json.dumps({"error": error_msg}))
                else:
                    print(f"Error: {error_msg}", file=sys.stderr)
                sys.exit(1)

        try:
            trio.run(_get_session)
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as e:
            error_msg = f"Failed to run session loader: {e}"
            if json_output:
                print(json.dumps({"error": error_msg}))
            else:
                print(f"Error: {error_msg}", file=sys.stderr)
            sys.exit(1)
        return

    # Handle --list-sessions: show recent sessions and exit
    if list_sessions:
        sessions = session_store.list_sync(limit=50)
        if json_output:
            # Return metadata only - messages loaded on-demand via --get-session
            sessions_data = []
            for s in sessions:
                sessions_data.append({
                    "session_id": s.session_id,
                    "status": s.status.value,
                    "model": s.endpoint.model if s.endpoint else None,
                    "created_at": s.created_at if hasattr(s, "created_at") else None,
                    "updated_at": s.updated_at if hasattr(s, "updated_at") else None,
                    "message_count": len(s.messages),
                    "preview": _get_session_preview(s),
                })
            print(json.dumps({"sessions": sessions_data}))
        else:
            if not sessions:
                print("No sessions found.")
            else:
                print("Recent sessions:")
                for s in sessions:
                    preview = _get_session_preview(s)
                    print(f"  {s.session_id}  {preview}")
        return

    # Emit early event for JSON mode before heavy imports
    # This gives immediate feedback that the CLI started correctly
    if json_output:
        print(json.dumps({"type": "initializing"}), flush=True)

    from wafer_core.rollouts import Message, Trajectory
    from wafer_core.rollouts.frontends import NoneFrontend, RunnerConfig, run_interactive

    _setup_logging()

    # Auth
    api_base, api_key, api_key_refresh = _get_wafer_auth(no_proxy=no_proxy)
    if not api_base or not api_key:
        print("Error: No API credentials found", file=sys.stderr)
        print("  Run 'wafer login' or set ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    assert api_base is not None
    assert api_key is not None

    # Load template or use defaults
    if template:
        loaded_template, err = _load_template(template, template_args)
        if err or loaded_template is None:
            print(f"Error loading template: {err}", file=sys.stderr)
            sys.exit(1)
        tpl = loaded_template
        base_system_prompt = tpl.interpolate_prompt(template_args or {})
        # Show template info when starting without a prompt
        if not prompt and tpl.description:
            print(f"Template: {tpl.name}", file=sys.stderr)
            print(f"  {tpl.description}", file=sys.stderr)
            print(file=sys.stderr)
    else:
        tpl = _get_default_template()
        base_system_prompt = tpl.system_prompt

    # Append skill metadata if skills are enabled
    if tpl.include_skills:
        from wafer_core.rollouts.skills import discover_skills, format_skill_metadata_for_prompt

        skill_metadata = discover_skills()
        if skill_metadata:
            skill_section = format_skill_metadata_for_prompt(skill_metadata)
            system_prompt = base_system_prompt + "\n\n" + skill_section
        else:
            system_prompt = base_system_prompt
    else:
        system_prompt = base_system_prompt

    # CLI args override template values
    resolved_single_turn = single_turn if single_turn is not None else tpl.single_turn

    # Build endpoint and environment
    endpoint = _build_endpoint(tpl, model, api_base, api_key, api_key_refresh)
    environment = _build_environment(tpl, tools, corpus_path, no_sandbox)

    # Session store
    session_store = FileSessionStore()
    session_id = _resolve_session_id(resume, session_store)

    async def run() -> None:
        nonlocal session_id

        # Load trajectory - either from resumed session or fresh
        if session_id:
            existing_session, err = await session_store.get(session_id)
            if err:
                print(f"Error loading session: {err}", file=sys.stderr)
                sys.exit(1)
            assert existing_session is not None
            trajectory = Trajectory(messages=existing_session.messages)
        else:
            trajectory = Trajectory(messages=[Message(role="system", content=system_prompt)])

        try:
            if interactive:
                from wafer_core.rollouts.frontends.tui.interactive_agent import (
                    run_interactive_agent,
                )

                await run_interactive_agent(
                    trajectory,
                    endpoint,
                    environment,
                    session_store,
                    session_id,
                    theme_name="minimal",
                    debug=False,
                    debug_layout=False,
                    initial_prompt=prompt,
                )
            else:
                if json_output:
                    # Emit session_start if we have a session_id (from --resume)
                    model_name = endpoint.model if hasattr(endpoint, "model") else None
                    frontend = StreamingChunkFrontend(session_id=session_id, model=model_name)
                else:
                    frontend = NoneFrontend(show_tool_calls=True, show_thinking=False)
                config = RunnerConfig(
                    session_store=session_store,
                    session_id=session_id,
                    initial_prompt=prompt,
                    single_turn=resolved_single_turn,
                    hide_session_info=True,  # We print our own resume command
                )
                states = await run_interactive(trajectory, endpoint, frontend, environment, config)
                # Emit session_start for new sessions (if session_id was None and we got one)
                # Check first state to emit as early as possible
                if json_output and isinstance(frontend, StreamingChunkFrontend):
                    first_session_id = (
                        states[0].session_id if states and states[0].session_id else None
                    )
                    if first_session_id and not session_id:  # New session created
                        model_name = endpoint.model if hasattr(endpoint, "model") else None
                        frontend.emit_session_start(first_session_id, model_name)
                # Print resume command with full wafer agent prefix
                if states and states[-1].session_id:
                    print(f"\nResume with: wafer agent --resume {states[-1].session_id}")
        except KeyboardInterrupt:
            pass
        except BaseException as e:
            actual_error = _unwrap_exception(e)
            print(f"\n{type(actual_error).__name__}: {actual_error}", file=sys.stderr)
            sys.exit(1)

    trio.run(run)
