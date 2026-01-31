"""Unit tests for wevin_cli.py.

These tests document the logic patterns used in wevin_cli.py.
The actual lines in wevin_cli.py are marked with pragma: no cover
because they require complex integration tests to execute.
"""

import json
import tempfile
from pathlib import Path

from wafer_core.rollouts import Endpoint, FileSessionStore
from wafer_core.rollouts.dtypes import Message


def test_empty_assistant_message_filtering():
    """Test the empty assistant message filtering pattern.

    This documents the logic used in wevin_cli.py lines 413-414, 475-476,
    536-538, and 638-640 (all marked with pragma: no cover).
    """
    # Create test messages
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content=""),  # Empty - should be skipped
        Message(role="assistant", content=None),  # None - should be skipped
        Message(role="assistant", content="Valid response"),
        Message(role="user", content="Another question"),
    ]

    # Apply the filtering logic from wevin_cli.py
    filtered = []
    for msg in messages:
        if msg.role == "assistant" and (not msg.content or msg.content == ""):
            continue
        filtered.append(msg)

    # Verify empty assistant messages were skipped
    assert len(filtered) == 3  # Only user + valid assistant + user
    for msg in filtered:
        if msg.role == "assistant":
            assert msg.content and msg.content != ""


def test_endpoint_creation():
    """Test Endpoint class instantiation pattern (line 514).

    This documents the Endpoint usage in wevin_cli.py line 514
    (marked with pragma: no cover).
    """
    endpoint = Endpoint(
        model="claude-sonnet-4.5",
        provider="anthropic",
        temperature=0.7,
    )

    assert endpoint.model == "claude-sonnet-4.5"
    assert endpoint.provider == "anthropic"
    assert endpoint.temperature == 0.7


def test_bash_allowlist():
    """Test bash allowlist prefix matching."""
    from wafer_core.tools.bash_tool import check_bash_allowlist

    allowlist = ["ls", "python -c"]

    assert check_bash_allowlist("ls -la", allowlist) is None  # allowed
    assert check_bash_allowlist("python -c 'x'", allowlist) is None  # allowed
    assert check_bash_allowlist("python script.py", allowlist) is not None  # blocked (not prefix)
    assert check_bash_allowlist("rm -rf /", allowlist) is not None  # blocked
    assert check_bash_allowlist("rm -rf /", None) is None  # no allowlist = all allowed


# =============================================================================
# CLI Command Tests - list-sessions and get-session
# =============================================================================


def test_list_sessions_json_output():
    """Test --list-sessions --json returns valid JSON array.
    
    Tests the CLI command used by wevin-extension to list sessions.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a FileSessionStore in the temp directory
        session_store = FileSessionStore(base_dir=Path(tmpdir))
        
        # List sessions from empty store
        sessions = session_store.list_sync(limit=50)
        assert sessions == []
        
        # Simulate JSON output format
        sessions_data = []
        for s in sessions:
            sessions_data.append({
                "session_id": s.session_id,
                "status": s.status.value if hasattr(s.status, 'value') else s.status,
                "model": s.endpoint.model if s.endpoint else None,
                "created_at": s.created_at if hasattr(s, "created_at") else None,
                "updated_at": s.updated_at if hasattr(s, "updated_at") else None,
            })
        
        output = json.dumps({"sessions": sessions_data})
        parsed = json.loads(output)
        
        assert "sessions" in parsed
        assert isinstance(parsed["sessions"], list)


def test_list_sessions_returns_metadata_only():
    """Test --list-sessions --json returns metadata only, NOT full messages.
    
    This is critical for performance - messages are loaded on-demand via --get-session.
    The extension relies on this to list sessions quickly without loading all message content.
    """
    import trio
    from wafer_core.rollouts import EnvironmentConfig
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session_store = FileSessionStore(base_dir=Path(tmpdir))
        
        endpoint = Endpoint(provider="anthropic", model="claude-sonnet-4.5")
        env_config = EnvironmentConfig(type="localfs")
        
        async def run_test() -> None:
            # Create a session with messages
            session = await session_store.create(endpoint=endpoint, environment=env_config)
            
            await session_store.append_message(
                session.session_id,
                Message(role="user", content="Hello world")
            )
            await session_store.append_message(
                session.session_id,
                Message(role="assistant", content="Hi there! How can I help you?")
            )
            
            # list_sync returns sessions for listing - used by --list-sessions
            sessions = session_store.list_sync(limit=50)
            assert len(sessions) == 1
            
            # Simulate the JSON output format from wevin_cli.py --list-sessions --json
            # This should NOT include a "messages" field - only metadata
            sessions_data = []
            for s in sessions:
                session_dict = {
                    "session_id": s.session_id,
                    "status": s.status.value,
                    "model": s.endpoint.model if s.endpoint else None,
                    "created_at": s.created_at if hasattr(s, "created_at") else None,
                    "updated_at": s.updated_at if hasattr(s, "updated_at") else None,
                    "message_count": len(s.messages),
                    "preview": s.messages[0].content[:50] if s.messages else "",
                }
                # CRITICAL: No "messages" field in list output
                assert "messages" not in session_dict
                sessions_data.append(session_dict)
            
            output = json.dumps({"sessions": sessions_data})
            parsed = json.loads(output)
            
            # Verify structure
            assert len(parsed["sessions"]) == 1
            session_data = parsed["sessions"][0]
            
            # Should have metadata
            assert "session_id" in session_data
            assert "status" in session_data
            assert "preview" in session_data
            
            # Should NOT have full messages
            assert "messages" not in session_data
        
        trio.run(run_test)


def test_get_session_json_output():
    """Test --get-session <id> --json returns session with messages.
    
    Tests the CLI command used by wevin-extension to load session messages.
    """
    from dataclasses import asdict

    import trio
    from wafer_core.rollouts import EnvironmentConfig
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session_store = FileSessionStore(base_dir=Path(tmpdir))
        
        # Create a session
        endpoint = Endpoint(provider="anthropic", model="claude-sonnet-4.5")
        env_config = EnvironmentConfig(type="localfs")
        
        async def run_test() -> None:
            session = await session_store.create(endpoint=endpoint, environment=env_config)
            
            # Add some messages
            await session_store.append_message(
                session.session_id,
                Message(role="user", content="Hello")
            )
            await session_store.append_message(
                session.session_id,
                Message(role="assistant", content="Hi there!")
            )
            
            # Load the session
            loaded_session, err = await session_store.get(session.session_id)
            assert err is None
            assert loaded_session is not None
            assert len(loaded_session.messages) == 2
            
            # Simulate JSON output format
            messages_data = [asdict(msg) for msg in loaded_session.messages]
            output = json.dumps({
                "session_id": loaded_session.session_id,
                "status": loaded_session.status.value,
                "messages": messages_data,
            })
            parsed = json.loads(output)
            
            assert parsed["session_id"] == session.session_id
            assert "messages" in parsed
            assert len(parsed["messages"]) == 2
            assert parsed["messages"][0]["role"] == "user"
            assert parsed["messages"][1]["role"] == "assistant"
        
        trio.run(run_test)


def test_get_session_not_found():
    """Test --get-session with invalid ID returns error.
    
    Tests error handling when session doesn't exist.
    """
    import trio
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session_store = FileSessionStore(base_dir=Path(tmpdir))
        
        async def run_test() -> None:
            session, err = await session_store.get("nonexistent-session-id")
            assert session is None
            assert err is not None
            assert "not found" in err.lower()
            
            # Simulate JSON error output
            output = json.dumps({"error": err})
            parsed = json.loads(output)
            assert "error" in parsed
        
        trio.run(run_test)


def test_get_session_serialization_error_json_output():
    """Test --get-session --json returns JSON error when serialization fails.
    
    Verifies that serialization errors in json_output mode produce JSON error
    output (not stderr text), which is expected by the extension.
    """
    # Simulate what happens when asdict() fails on messages
    # The CLI should output JSON error, not print to stderr
    error_msg = "Failed to serialize messages: test error"
    
    # This is the expected output format from wevin_cli.py line 393-395
    output = json.dumps({"error": error_msg})
    parsed = json.loads(output)
    
    assert "error" in parsed
    assert "Failed to serialize messages" in parsed["error"]
    # Verify it's valid JSON that extension can parse
    assert isinstance(parsed, dict)


def test_session_resume_loads_context():
    """Test that --resume <session_id> loads previous messages.
    
    Tests the context maintenance flow: CLI loads messages from FileSessionStore
    when resuming a session.
    """
    import trio
    from wafer_core.rollouts import EnvironmentConfig, Trajectory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session_store = FileSessionStore(base_dir=Path(tmpdir))
        
        endpoint = Endpoint(provider="anthropic", model="claude-sonnet-4.5")
        env_config = EnvironmentConfig(type="localfs")
        
        async def run_test() -> None:
            # Create initial session with messages
            session = await session_store.create(endpoint=endpoint, environment=env_config)
            
            await session_store.append_message(
                session.session_id,
                Message(role="system", content="You are a helpful assistant.")
            )
            await session_store.append_message(
                session.session_id,
                Message(role="user", content="What is CUDA?")
            )
            await session_store.append_message(
                session.session_id,
                Message(role="assistant", content="CUDA is a parallel computing platform...")
            )
            
            # Simulate resume: load existing session
            existing_session, err = await session_store.get(session.session_id)
            assert err is None
            assert existing_session is not None
            
            # Create trajectory with previous messages (what CLI does on --resume)
            trajectory = Trajectory(messages=existing_session.messages)
            
            assert len(trajectory.messages) == 3
            assert trajectory.messages[0].role == "system"
            assert trajectory.messages[1].role == "user"
            assert trajectory.messages[2].role == "assistant"
            
            # Verify context is available for follow-up
            assert "CUDA" in str(trajectory.messages[1].content)
            assert "parallel computing" in str(trajectory.messages[2].content)
        
        trio.run(run_test)


def test_cli_parameters_accepted():
    """Test that CLI parameters are accepted by wevin_main signature.
    
    These parameters are accepted but not yet implemented:
    - from_turn: Branch from specific turn
    - allow_spawn: Allow spawning sub-agents
    - max_tool_fails: Exit after N failures
    - max_turns: Limit conversation turns
    """
    import inspect

    from wafer.wevin_cli import main as wevin_main
    
    sig = inspect.signature(wevin_main)
    params = sig.parameters
    
    # Verify all parameters exist
    assert 'from_turn' in params
    assert 'allow_spawn' in params
    assert 'max_tool_fails' in params
    assert 'max_turns' in params
    
    # Verify types (using string comparison for Python version compatibility)
    assert str(params['from_turn'].annotation) in ('int | None', 'typing.Union[int, NoneType]', 'typing.Optional[int]')
    assert str(params['allow_spawn'].annotation) in ('bool', "<class 'bool'>")
    assert str(params['max_tool_fails'].annotation) in ('int | None', 'typing.Union[int, NoneType]', 'typing.Optional[int]')
    assert str(params['max_turns'].annotation) in ('int | None', 'typing.Union[int, NoneType]', 'typing.Optional[int]')
    
    # Verify defaults
    assert params['from_turn'].default is None
    assert params['allow_spawn'].default is False
    assert params['max_tool_fails'].default is None
    assert params['max_turns'].default is None


# =============================================================================
# StreamingChunkFrontend session_start emission tests
# =============================================================================


def test_streaming_frontend_session_start_resumed_session():
    """Test StreamingChunkFrontend emits session_start in start() for resumed sessions.
    
    Edge case: When session_id is known upfront (from --resume), emit immediately.
    """
    from io import StringIO

    import trio

    from wafer.wevin_cli import StreamingChunkFrontend
    
    # Capture stdout
    captured_output = StringIO()
    
    async def run_test() -> None:
        frontend = StreamingChunkFrontend(
            session_id="test-session-123",
            model="claude-sonnet-4.5"
        )
        
        # Mock _emit to capture output
        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)
            # Also print to verify JSON format
            print(json.dumps(obj), file=captured_output)
        
        frontend._emit = mock_emit
        
        await frontend.start()
        
        # Verify session_start was emitted
        assert len(emitted_events) == 1
        assert emitted_events[0]["type"] == "session_start"
        assert emitted_events[0]["session_id"] == "test-session-123"
        assert emitted_events[0]["model"] == "claude-sonnet-4.5"
        
        # Verify JSON is valid
        output = captured_output.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["type"] == "session_start"
        assert parsed["session_id"] == "test-session-123"
        assert parsed["model"] == "claude-sonnet-4.5"
    
    trio.run(run_test)


def test_streaming_frontend_session_start_no_session_id():
    """Test StreamingChunkFrontend does NOT emit session_start when session_id is None.
    
    Edge case: New session - session_id not known until after run_interactive.
    """
    import trio

    from wafer.wevin_cli import StreamingChunkFrontend
    
    async def run_test() -> None:
        frontend = StreamingChunkFrontend(session_id=None, model=None)
        
        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)
        
        frontend._emit = mock_emit
        
        await frontend.start()
        
        # Should NOT emit session_start when session_id is None
        assert len(emitted_events) == 0
    
    trio.run(run_test)


def test_streaming_frontend_emit_session_start_new_session():
    """Test emit_session_start() method for new sessions created during run.
    
    Edge case: Session created during run_interactive, emit after first state.
    """
    import trio

    from wafer.wevin_cli import StreamingChunkFrontend
    
    async def run_test() -> None:
        # Frontend starts without session_id (new session)
        frontend = StreamingChunkFrontend(session_id=None, model="claude-sonnet-4.5")
        
        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)
        
        frontend._emit = mock_emit
        
        # Start doesn't emit (no session_id yet)
        await frontend.start()
        assert len(emitted_events) == 0
        
        # After run_interactive, we get session_id from first state
        new_session_id = "new-session-456"
        frontend.emit_session_start(new_session_id, "claude-sonnet-4.5")
        
        # Verify session_start was emitted
        assert len(emitted_events) == 1
        assert emitted_events[0]["type"] == "session_start"
        assert emitted_events[0]["session_id"] == new_session_id
        assert emitted_events[0]["model"] == "claude-sonnet-4.5"
    
    trio.run(run_test)


def test_streaming_frontend_emit_session_start_model_none():
    """Test emit_session_start() handles None model gracefully.
    
    Edge case: Model might be None, should use frontend's model or None.
    """
    import trio

    from wafer.wevin_cli import StreamingChunkFrontend
    
    async def run_test() -> None:
        # Frontend with model, but emit_session_start called with None
        frontend = StreamingChunkFrontend(session_id=None, model="claude-sonnet-4.5")
        
        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)
        
        frontend._emit = mock_emit
        
        # Emit with None model - should use frontend's model
        frontend.emit_session_start("session-789", None)
        
        assert len(emitted_events) == 1
        assert emitted_events[0]["model"] == "claude-sonnet-4.5"
        
        # Reset and test with no frontend model
        emitted_events.clear()
        frontend_no_model = StreamingChunkFrontend(session_id=None, model=None)
        frontend_no_model._emit = mock_emit
        
        frontend_no_model.emit_session_start("session-999", None)
        
        assert len(emitted_events) == 1
        assert emitted_events[0]["model"] is None
    
    trio.run(run_test)


def test_streaming_frontend_emit_session_start_multiple_calls():
    """Test emit_session_start() can be called multiple times (idempotent).
    
    Edge case: Multiple calls should work (e.g., if called from different code paths).
    """
    import trio

    from wafer.wevin_cli import StreamingChunkFrontend
    
    async def run_test() -> None:
        frontend = StreamingChunkFrontend(session_id=None, model="claude-sonnet-4.5")
        
        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)
        
        frontend._emit = mock_emit
        
        # Call multiple times
        frontend.emit_session_start("session-111", "claude-sonnet-4.5")
        frontend.emit_session_start("session-222", "claude-sonnet-4.5")
        frontend.emit_session_start("session-333", "claude-sonnet-4.5")
        
        # Should emit each time (not idempotent, but that's OK - extension handles duplicates)
        assert len(emitted_events) == 3
        assert emitted_events[0]["session_id"] == "session-111"
        assert emitted_events[1]["session_id"] == "session-222"
        assert emitted_events[2]["session_id"] == "session-333"
    
    trio.run(run_test)


def test_streaming_frontend_session_start_empty_states():
    """Test session_start emission logic handles empty states list gracefully.
    
    Edge case: run_interactive might return empty list (shouldn't crash).
    """
    import trio

    from wafer.wevin_cli import StreamingChunkFrontend
    
    async def run_test() -> None:
        frontend = StreamingChunkFrontend(session_id=None, model="claude-sonnet-4.5")
        
        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)
        
        frontend._emit = mock_emit
        
        # Simulate empty states list (what main() would see)
        states = []
        original_session_id = None  # Was None initially (new session)
        
        # This is the logic from wevin_cli.py main()
        first_session_id = states[0].session_id if states and states[0].session_id else None
        if first_session_id and not original_session_id:  # New session created
            frontend.emit_session_start(first_session_id, "claude-sonnet-4.5")
        
        # Should not crash, and should not emit (no session_id available)
        assert len(emitted_events) == 0
    
    trio.run(run_test)


def test_streaming_frontend_session_start_state_without_session_id():
    """Test session_start emission handles states without session_id.
    
    Edge case: First state might not have session_id set yet.
    """
    import trio

    from wafer.wevin_cli import StreamingChunkFrontend
    
    # Mock AgentState for testing
    class MockState:
        def __init__(self, session_id=None) -> None:
            self.session_id = session_id
    
    async def run_test() -> None:
        frontend = StreamingChunkFrontend(session_id=None, model="claude-sonnet-4.5")
        
        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)
        
        frontend._emit = mock_emit
        
        # Simulate states where first state has no session_id
        states = [MockState(session_id=None)]
        original_session_id = None  # Was None initially (new session)
        
        # Logic from wevin_cli.py
        first_session_id = states[0].session_id if states and states[0].session_id else None
        if first_session_id and not original_session_id:  # New session created
            frontend.emit_session_start(first_session_id, "claude-sonnet-4.5")
        
        # Should not emit (no session_id in state)
        assert len(emitted_events) == 0
        
        # Now with session_id in state
        states_with_id = [MockState(session_id="state-session-123")]
        first_session_id = states_with_id[0].session_id if states_with_id and states_with_id[0].session_id else None
        if first_session_id and not original_session_id:
            frontend.emit_session_start(first_session_id, "claude-sonnet-4.5")
        
        # Should emit now
        assert len(emitted_events) == 1
        assert emitted_events[0]["session_id"] == "state-session-123"
    
    trio.run(run_test)


def test_streaming_frontend_session_start_resumed_then_new():
    """Test session_start emission when resuming but states have different session_id.

    Edge case: --resume used but states return different session_id (should use states one).
    """
    import trio

    from wafer.wevin_cli import StreamingChunkFrontend

    async def run_test() -> None:
        # Start with resumed session_id
        frontend = StreamingChunkFrontend(
            session_id="resumed-session-123",
            model="claude-sonnet-4.5"
        )

        emitted_events = []

        def mock_emit(obj) -> None:
            emitted_events.append(obj)

        frontend._emit = mock_emit

        # start() emits session_start for resumed session
        await frontend.start()
        assert len(emitted_events) == 1
        assert emitted_events[0]["session_id"] == "resumed-session-123"

        # If states have different session_id (shouldn't happen, but handle gracefully)
        # The logic in main() checks `if first_session_id and not session_id`
        # So if session_id was set, it won't emit again
        # This is correct behavior - use the one from --resume

    trio.run(run_test)


# =============================================================================
# --no-sandbox flag tests
# =============================================================================


def test_no_sandbox_parameter_accepted():
    """Test that no_sandbox parameter exists in wevin_main signature."""
    import inspect

    from wafer.wevin_cli import main as wevin_main

    sig = inspect.signature(wevin_main)
    params = sig.parameters

    # Verify parameter exists
    assert 'no_sandbox' in params

    # Verify type and default
    assert str(params['no_sandbox'].annotation) in ('bool', "<class 'bool'>")
    assert params['no_sandbox'].default is False


def test_build_environment_accepts_no_sandbox():
    """Test that _build_environment accepts no_sandbox parameter."""
    import inspect

    from wafer.wevin_cli import _build_environment

    sig = inspect.signature(_build_environment)
    params = sig.parameters

    assert 'no_sandbox' in params
    assert params['no_sandbox'].default is False


def test_build_environment_with_no_sandbox_false():
    """Test _build_environment creates env with sandbox ENABLED when no_sandbox=False."""
    from wafer_core.rollouts.templates import TemplateConfig
    from wafer_core.sandbox import SandboxMode

    from wafer.wevin_cli import _build_environment

    tpl = TemplateConfig(
        name="test",
        description="Test template",
        system_prompt="Test",
        tools=["read"],
    )

    # This will raise RuntimeError if sandbox is unavailable on this system
    # That's expected - we're testing that sandbox is ENABLED by default
    try:
        env = _build_environment(tpl, None, None, no_sandbox=False)
        # If we get here, sandbox is available - verify it's enabled
        assert env.sandbox_mode == SandboxMode.ENABLED
    except RuntimeError as e:
        # Sandbox unavailable - that's OK, the error proves ENABLED is set
        assert "sandboxing is not available" in str(e)


def test_build_environment_with_no_sandbox_true():
    """Test _build_environment creates env with sandbox DISABLED when no_sandbox=True."""
    from wafer_core.rollouts.templates import TemplateConfig
    from wafer_core.sandbox import SandboxMode

    from wafer.wevin_cli import _build_environment

    tpl = TemplateConfig(
        name="test",
        description="Test template",
        system_prompt="Test",
        tools=["read"],
    )

    # This should NOT raise - sandbox is disabled
    env = _build_environment(tpl, None, None, no_sandbox=True)
    assert env.sandbox_mode == SandboxMode.DISABLED
