import hashlib
import re


def generate_fingerprint(error_type: str, location: str, service_name: str) -> str:
    content = f"{service_name}:{error_type}:{location}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def extract_location_from_traceback(traceback_str: str) -> str:
    pattern = r'File "([^"]+)", line (\d+)'
    matches = re.findall(pattern, traceback_str)
    for filepath, line in reversed(matches):
        if "site-packages" in filepath:
            continue
        if "lib/python" in filepath:
            continue
        if "fika_logger" in filepath:
            continue
        return f"{filepath}:{line}"
    return "unknown:0"


def extract_function_from_traceback(traceback_str: str) -> str:
    pattern = r'File "[^"]+", line \d+, in (\w+)'
    matches = re.findall(pattern, traceback_str)
    for func_name in reversed(matches):
        return func_name
    return "unknown"


def shorten_traceback(traceback_str: str, max_frames: int = 5) -> str:
    pattern = r'File "([^"]+)", line (\d+), in (\w+)'
    matches = re.findall(pattern, traceback_str)
    user_frames = []
    for filepath, line, func in matches:
        if "site-packages" in filepath or "lib/python" in filepath:
            continue
        filename = filepath.split("/")[-1]
        user_frames.append(f"{filename}:{line}")
    if len(user_frames) > max_frames:
        user_frames = user_frames[-max_frames:]
    return " → ".join(user_frames)
