"""Tests for context management."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from loguru_kit._context import (
    clear_context,
    context_scope,
    copy_context_to_thread,
    get_context,
    set_context,
)


class TestContextSetGet:
    """Test basic context set/get operations."""

    def test_set_and_get_context(self):
        """Test setting and getting context values."""
        clear_context()
        set_context(user_id=123, request_id="abc")
        ctx = get_context()
        assert ctx["user_id"] == 123
        assert ctx["request_id"] == "abc"

    def test_get_empty_context(self):
        """Test getting context when nothing is set."""
        clear_context()
        ctx = get_context()
        assert ctx == {}

    def test_clear_context(self):
        """Test clearing context."""
        set_context(key="value")
        clear_context()
        ctx = get_context()
        assert ctx == {}

    def test_update_context(self):
        """Test updating existing context."""
        clear_context()
        set_context(a=1)
        set_context(b=2)
        ctx = get_context()
        assert ctx["a"] == 1
        assert ctx["b"] == 2

    def test_overwrite_context_value(self):
        """Test overwriting an existing context value."""
        clear_context()
        set_context(key="old")
        set_context(key="new")
        ctx = get_context()
        assert ctx["key"] == "new"


class TestContextScope:
    """Test context_scope context manager."""

    def test_context_scope_adds_context(self):
        """Test that context_scope adds context within scope."""
        clear_context()
        with context_scope(request_id="req-123"):
            ctx = get_context()
            assert ctx["request_id"] == "req-123"

    def test_context_scope_restores_on_exit(self):
        """Test that context is restored after scope exits."""
        clear_context()
        set_context(existing="value")
        with context_scope(temporary="temp"):
            pass
        ctx = get_context()
        assert "temporary" not in ctx
        assert ctx["existing"] == "value"

    def test_nested_context_scope(self):
        """Test nested context scopes."""
        clear_context()
        with context_scope(level1="a"):
            with context_scope(level2="b"):
                ctx = get_context()
                assert ctx["level1"] == "a"
                assert ctx["level2"] == "b"
            ctx = get_context()
            assert ctx["level1"] == "a"
            assert "level2" not in ctx


class TestAsyncContextPropagation:
    """Test context propagation in async contexts."""

    @pytest.mark.asyncio
    async def test_context_propagates_to_coroutine(self):
        """Test that context propagates to coroutines."""
        clear_context()
        set_context(request_id="async-req")

        async def check_context():
            ctx = get_context()
            return ctx.get("request_id")

        result = await check_context()
        assert result == "async-req"

    @pytest.mark.asyncio
    async def test_context_propagates_to_create_task(self):
        """Test that context propagates through asyncio.create_task."""
        clear_context()
        set_context(task_id="main-task")

        async def subtask():
            ctx = get_context()
            return ctx.get("task_id")

        task = asyncio.create_task(subtask())
        result = await task
        assert result == "main-task"

    @pytest.mark.asyncio
    async def test_context_isolated_between_concurrent_tasks(self):
        """Test that concurrent tasks have isolated contexts."""
        clear_context()

        results = []

        async def task_with_context(task_id: str):
            set_context(task_id=task_id)
            await asyncio.sleep(0.01)  # Yield control
            ctx = get_context()
            results.append(ctx.get("task_id"))

        # Run tasks concurrently
        await asyncio.gather(
            task_with_context("task-1"),
            task_with_context("task-2"),
        )

        # Each task should have seen its own context
        assert "task-1" in results
        assert "task-2" in results


class TestThreadIsolation:
    """Test context isolation across threads."""

    def test_context_isolated_between_threads(self):
        """Test that threads have isolated contexts."""
        clear_context()
        set_context(main_thread="yes")

        thread_result = {}

        def thread_func():
            # Thread should not see main thread's context
            ctx = get_context()
            thread_result["saw_main"] = "main_thread" in ctx

            # Set own context
            set_context(in_thread="yes")
            thread_result["own_ctx"] = get_context()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(thread_func)
            future.result()

        # Thread should not have seen main thread context (contextvars are thread-local)
        # But with copy_context it can be propagated if needed
        assert thread_result["saw_main"] is False

    def test_copy_context_to_thread(self):
        """Test copying context to a thread."""
        clear_context()
        set_context(shared="value")

        thread_result = {}

        def thread_func():
            ctx = get_context()
            thread_result["ctx"] = ctx

        # Use copy_context_to_thread to propagate context
        wrapped = copy_context_to_thread(thread_func)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(wrapped)
            future.result()

        assert thread_result["ctx"].get("shared") == "value"
