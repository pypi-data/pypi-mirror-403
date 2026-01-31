import contextvars
from contextlib import contextmanager
from typing import Dict, Any, Generator

_context_var: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    'fika_context', default={}
)
_inside_trace: contextvars.ContextVar[bool] = contextvars.ContextVar(
    'inside_trace', default=False
)

@contextmanager
def context(**kwargs) -> Generator[None, None, None]:
    """Set context for all logs within this block"""
    current = _context_var.get().copy()
    current.update(kwargs)
    token = _context_var.set(current)
    try:
        yield
    finally:
        _context_var.reset(token)

def get_current_context() -> Dict[str, Any]:
    return _context_var.get().copy()

def add_context(**kwargs) -> None:
    current = _context_var.get().copy()
    current.update(kwargs)
    _context_var.set(current)

def update_context(**kwargs) -> None:
    add_context(**kwargs)

def is_inside_trace() -> bool:
    return _inside_trace.get()

def set_inside_trace(value: bool) -> contextvars.Token:
    return _inside_trace.set(value)

def reset_inside_trace(token: contextvars.Token) -> None:
    _inside_trace.reset(token)
