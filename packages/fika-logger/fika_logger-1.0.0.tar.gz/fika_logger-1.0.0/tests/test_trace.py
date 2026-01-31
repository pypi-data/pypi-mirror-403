import asyncio
import pytest
from fika_logger.core.context import context, get_current_context, is_inside_trace
from fika_logger.core.trace import trace


async def test_trace_sets_flag():
    @trace
    async def my_func():
        return is_inside_trace()

    result = await my_func()
    assert result is True


async def test_trace_resets_flag():
    @trace
    async def my_func():
        pass

    await my_func()
    assert is_inside_trace() is False


async def test_trace_propagates_context():
    results = []

    async def child_task():
        ctx = get_current_context()
        results.append(ctx.get("client"))

    @trace
    async def entry_point():
        with context(client="test_client"):
            task = asyncio.create_task(child_task())
            await task

    await entry_point()
    assert results == ["test_client"]


async def test_trace_propagates_nested():
    results = []

    async def level2():
        ctx = get_current_context()
        results.append(ctx.get("client"))

    async def level1():
        ctx = get_current_context()
        results.append(ctx.get("client"))
        task = asyncio.create_task(level2())
        await task

    @trace
    async def entry():
        with context(client="nested_test"):
            task = asyncio.create_task(level1())
            await task

    await entry()
    assert results == ["nested_test", "nested_test"]
