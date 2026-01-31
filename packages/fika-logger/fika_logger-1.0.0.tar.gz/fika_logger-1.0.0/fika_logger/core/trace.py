import asyncio
import contextvars
import functools
from typing import Callable, TypeVar, Coroutine, Any

from .context import is_inside_trace, set_inside_trace, reset_inside_trace

F = TypeVar('F', bound=Callable[..., Coroutine[Any, Any, Any]])

_original_create_task = asyncio.create_task
_patched = False

def _patched_create_task(coro, *, name=None, context=None):
    if is_inside_trace() and context is None:
        context = contextvars.copy_context()
    return _original_create_task(coro, name=name, context=context)

def _ensure_patched() -> None:
    global _patched
    if not _patched:
        asyncio.create_task = _patched_create_task
        _patched = True

def trace(func: F) -> F:
    _ensure_patched()
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        token = set_inside_trace(True)
        try:
            return await func(*args, **kwargs)
        finally:
            reset_inside_trace(token)
    return wrapper  # type: ignore
