"""Tests for web-enhanced FastAPI server: STAB-01, STAB-03, BACK-01.

Note: FastAPI >= 0.135.1 (with fastapi.sse module) is not yet available on PyPI.
Tests verify source-level correctness and asyncio task lifecycle behavior.
Behavioral SSE tests requiring the actual EventSourceResponse are deferred
until the FastAPI release ships.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# --- Source-level verification (no fastapi.sse import needed) ---

def _read_server_source():
    server_path = os.path.join(os.path.dirname(__file__), "..", "server.py")
    with open(server_path) as f:
        return f.read()


# --- BACK-01: EventSourceResponse used ---

def test_no_streaming_response_import():
    """server.py must not import StreamingResponse."""
    source = _read_server_source()
    assert "StreamingResponse" not in source, "StreamingResponse should be replaced by EventSourceResponse"


def test_event_source_response_import():
    """server.py must import EventSourceResponse from fastapi.sse."""
    source = _read_server_source()
    assert "from fastapi.sse import EventSourceResponse" in source


def test_server_sent_event_import():
    """server.py must import ServerSentEvent from fastapi.sse."""
    source = _read_server_source()
    assert "ServerSentEvent" in source


# --- STAB-01: No GeneratorExit handling ---

def test_no_generator_exit_handling():
    """Generator should not catch GeneratorExit — let EventSourceResponse handle teardown."""
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


# --- STAB-03: asyncio task lifecycle (unit tests, no FastAPI import needed) ---

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
