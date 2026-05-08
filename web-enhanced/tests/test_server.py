"""Tests for web-enhanced FastAPI server: STAB-01, STAB-03, BACK-01, BACK-02.

Covers: StreamingResponse SSE with disconnect handling, asyncio task GC,
requirements.txt validity.
"""
import asyncio
import os
import sys
from unittest.mock import MagicMock

import pytest

# Stub out maigret and its transitive deps before importing server/scanner,
# so the test file works without the full maigret dependency tree installed.
_maigret_stubs = {
    "maigret": MagicMock(),
    "maigret.sites": MagicMock(),
    "maigret.notify": MagicMock(),
    "maigret.result": MagicMock(),
    "maigret.checking": MagicMock(),
    "maigret.report": MagicMock(),
}
for _name, _mod in _maigret_stubs.items():
    sys.modules.setdefault(_name, _mod)

import enum as _enum
class _FakeStatus(_enum.Enum):
    CLAIMED = "claimed"
sys.modules["maigret.result"].MaigretCheckStatus = _FakeStatus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _read_server_source():
    server_path = os.path.join(os.path.dirname(__file__), "..", "server.py")
    with open(server_path) as f:
        return f.read()


# --- BACK-01: StreamingResponse SSE with proper formatting ---

def test_streaming_response_import():
    """server.py must import StreamingResponse from fastapi.responses."""
    source = _read_server_source()
    assert "StreamingResponse" in source

def test_no_fastapi_sse_import():
    """server.py must NOT import from fastapi.sse (module does not exist)."""
    source = _read_server_source()
    assert "from fastapi.sse" not in source

def test_sse_data_format():
    """server.py must yield SSE-formatted strings with 'data: ...\\n\\n' pattern."""
    source = _read_server_source()
    assert 'data: {json.dumps(event)}\\n\\n' in source

def test_sse_keepalive_comment():
    """server.py must yield SSE comment as keep-alive on timeout."""
    source = _read_server_source()
    assert '":\\n\\n"' in source


# --- BACK-02: requirements.txt validity ---

def test_requirements_fastapi_version_exists():
    """requirements.txt must pin fastapi to a version that exists on PyPI."""
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    with open(req_path) as f:
        content = f.read()
    assert "fastapi>=0.128.0" in content
    assert "0.135.1" not in content, "FastAPI 0.135.1 does not exist on PyPI"

def test_requirements_no_sse_starlette():
    """requirements.txt must not contain sse-starlette."""
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    with open(req_path) as f:
        content = f.read()
    assert "sse-starlette" not in content


# --- STAB-01: No GeneratorExit handling ---

def test_no_generator_exit_handling():
    """Generator should not catch GeneratorExit — let StreamingResponse handle teardown."""
    source = _read_server_source()
    assert "GeneratorExit" not in source


# --- STAB-03: _background_tasks set ---

def test_background_tasks_declaration():
    """server.py must declare _background_tasks as a module-level set."""
    source = _read_server_source()
    assert "_background_tasks: set[asyncio.Task] = set()" in source

def test_background_tasks_add_in_start_scan():
    """start_scan must add task to _background_tasks."""
    source = _read_server_source()
    assert "_background_tasks.add(task)" in source

def test_background_tasks_done_callback():
    """start_scan must register discard callback for automatic cleanup."""
    source = _read_server_source()
    assert "task.add_done_callback(_background_tasks.discard)" in source


# --- STAB-03: asyncio task lifecycle (unit tests) ---

@pytest.mark.asyncio
async def test_task_stored_in_set():
    """Task added to a set survives GC and is removed by done callback."""
    bg_tasks = set()

    async def fake_run():
        await asyncio.sleep(10)

    task = asyncio.create_task(fake_run())
    bg_tasks.add(task)
    task.add_done_callback(bg_tasks.discard)

    assert len(bg_tasks) == 1
    assert task in bg_tasks

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await asyncio.sleep(0.01)
    assert len(bg_tasks) == 0


@pytest.mark.asyncio
async def test_task_removed_after_completion():
    """Task removed from set after normal completion via done callback."""
    bg_tasks = set()

    async def quick_task():
        pass

    task = asyncio.create_task(quick_task())
    bg_tasks.add(task)
    task.add_done_callback(bg_tasks.discard)

    await task
    await asyncio.sleep(0.01)
    assert len(bg_tasks) == 0


# --- STAB-01: Behavioral SSE disconnect tests ---

@pytest.mark.asyncio
async def test_sse_disconnect_exits_generator_cleanly():
    """STAB-01: When client disconnects, the SSE generator exits cleanly and
    leaves no orphaned queue reader.

    StreamingResponse tears down the async generator via GeneratorExit when the
    client disconnects (Starlette task group cancellation). We simulate this by
    calling aclose() on the generator. After teardown, items put on the queue
    must remain unconsumed (no orphaned reader draining it)."""
    from server import scan_progress, jobs
    from scanner import ScanJob
    from starlette.responses import StreamingResponse

    job = ScanJob(id="disconnect-test", username="testuser")
    jobs["disconnect-test"] = job

    response = await scan_progress("disconnect-test")
    assert isinstance(response, StreamingResponse), \
        f"scan_progress must return StreamingResponse, got {type(response).__name__}"

    gen = response.body_iterator
    assert hasattr(gen, 'athrow') or hasattr(gen, 'aclose'), \
        "body_iterator must be an async generator"

    # Simulate client disconnect by closing the generator
    await gen.aclose()

    # Verify no orphaned reader: put an item and confirm it stays unconsumed
    await job.queue.put({"type": "progress", "completed": 1, "total": 10, "found": 0})
    await asyncio.sleep(0.05)
    assert job.queue.qsize() == 1, \
        "Queue item should remain unconsumed — no orphaned generator should be reading it"

    # Clean up
    del jobs["disconnect-test"]


@pytest.mark.asyncio
async def test_sse_disconnect_does_not_kill_scan_task():
    """STAB-01 + D-01: Disconnecting the SSE client must not cancel the
    background scan task. The scan task is owned by _background_tasks,
    not by the SSE generator."""
    from server import scan_progress, jobs, _background_tasks
    from scanner import ScanJob

    job = ScanJob(id="persist-test", username="testuser")
    jobs["persist-test"] = job

    scan_done = asyncio.Event()

    async def fake_scan():
        await scan_done.wait()

    task = asyncio.create_task(fake_scan())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    # Get SSE response and tear down the generator (simulate disconnect)
    response = await scan_progress("persist-test")
    gen = response.body_iterator
    await gen.aclose()

    # Verify the scan task is still alive
    assert not task.cancelled(), "Scan task must not be cancelled on SSE disconnect"
    assert not task.done(), "Scan task must still be running after SSE disconnect"
    assert task in _background_tasks, "Scan task must remain in _background_tasks"

    # Clean up
    scan_done.set()
    await task
    await asyncio.sleep(0.01)
    del jobs["persist-test"]


# --- STAB-03: Module-level set runtime check ---

def test_background_tasks_set_exists():
    """_background_tasks must be a module-level set in server.py."""
    from server import _background_tasks as bt
    assert isinstance(bt, set), "_background_tasks must be a set"


# --- Server importable (gap blocker resolved) ---

def test_server_importable():
    """server.py must import without error (the fastapi.sse blocker is resolved)."""
    import importlib
    import server
    importlib.reload(server)  # force re-import to catch import errors
    assert hasattr(server, 'app')
    assert hasattr(server, '_background_tasks')
    assert hasattr(server, 'scan_progress')
