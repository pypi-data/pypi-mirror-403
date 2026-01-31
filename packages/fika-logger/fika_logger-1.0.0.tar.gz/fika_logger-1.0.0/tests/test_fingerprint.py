from fika_logger.core.fingerprint import (
    generate_fingerprint,
    extract_location_from_traceback,
    extract_function_from_traceback,
    shorten_traceback,
)


def test_same_error_same_fingerprint():
    fp1 = generate_fingerprint("ValueError", "/app/main.py:42", "my-service")
    fp2 = generate_fingerprint("ValueError", "/app/main.py:42", "my-service")
    assert fp1 == fp2


def test_different_error_different_fingerprint():
    fp1 = generate_fingerprint("ValueError", "/app/main.py:42", "my-service")
    fp2 = generate_fingerprint("TypeError", "/app/main.py:42", "my-service")
    assert fp1 != fp2


def test_different_location_different_fingerprint():
    fp1 = generate_fingerprint("ValueError", "/app/main.py:42", "my-service")
    fp2 = generate_fingerprint("ValueError", "/app/main.py:99", "my-service")
    assert fp1 != fp2


def test_fingerprint_length():
    fp = generate_fingerprint("ValueError", "/app/main.py:42", "my-service")
    assert len(fp) == 16


def test_extract_location():
    tb = '''Traceback (most recent call last):
  File "/app/src/api/webhooks.py", line 23, in webhook
    asyncio.create_task(process())
  File "/app/src/core/engine.py", line 89, in process
    raise ValueError("test")
ValueError: test'''
    location = extract_location_from_traceback(tb)
    assert location == "/app/src/core/engine.py:89"


def test_extract_location_skips_site_packages():
    tb = '''Traceback (most recent call last):
  File "/app/src/main.py", line 10, in handler
    result = call()
  File "/usr/lib/python3.11/site-packages/httpx/client.py", line 200, in send
    raise ConnectError()
httpx.ConnectError'''
    location = extract_location_from_traceback(tb)
    assert location == "/app/src/main.py:10"


def test_extract_function():
    tb = '''Traceback (most recent call last):
  File "/app/src/core/engine.py", line 89, in process_message
    raise ValueError("test")
ValueError: test'''
    func = extract_function_from_traceback(tb)
    assert func == "process_message"


def test_shorten_traceback():
    tb = '''Traceback (most recent call last):
  File "/app/src/api/webhooks.py", line 23, in webhook
    asyncio.create_task(process())
  File "/app/src/core/engine.py", line 89, in process
    raise ValueError("test")
ValueError: test'''
    short = shorten_traceback(tb)
    assert "webhooks.py:23" in short
    assert "engine.py:89" in short
    assert "→" in short
