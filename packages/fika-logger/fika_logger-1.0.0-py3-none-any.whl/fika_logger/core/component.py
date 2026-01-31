import inspect


def get_component_from_caller() -> str:
    """
    Auto-detect component from caller's full file path.
    Returns the full file path of the calling code.
    Example: /app/src/integrations/zoho/client.py
    """
    stack = inspect.stack()
    for frame in stack:
        filepath = frame.filename
        if "fika_logger" in filepath:
            continue
        if "site-packages" in filepath:
            continue
        if "lib/python" in filepath:
            continue
        return filepath
    return "unknown"
