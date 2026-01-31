import pytest
from datetime import datetime
from fika_logger.storage.memory import MemoryStorage
from fika_logger.storage.base import ErrorRecord


def _make_record(fingerprint="abc123", count=1):
    return ErrorRecord(
        fingerprint=fingerprint,
        error_type="ValueError",
        message="test error",
        location="/app/main.py:42",
        function_name="handler",
        service="test-service",
        environment="development",
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        count=count,
        last_alerted=None,
        occurrences_since_alert=0,
        github_issue_number=None,
        github_issue_state="",
        status="open",
        context={"client": "x"},
        full_traceback="Traceback...",
    )


@pytest.fixture
def storage():
    return MemoryStorage()


async def test_upsert_and_get(storage):
    record = _make_record()
    await storage.upsert(record)
    result = await storage.get_by_fingerprint("abc123")
    assert result is not None
    assert result.error_type == "ValueError"


async def test_get_nonexistent(storage):
    result = await storage.get_by_fingerprint("nonexistent")
    assert result is None


async def test_increment_count(storage):
    record = _make_record()
    await storage.upsert(record)
    updated = await storage.increment_count("abc123", {"client": "y"}, "new tb")
    assert updated is not None
    assert updated.count == 2
    assert updated.occurrences_since_alert == 1
    assert updated.context == {"client": "y"}


async def test_increment_nonexistent(storage):
    result = await storage.increment_count("nonexistent", {}, "")
    assert result is None


async def test_update_github_issue(storage):
    record = _make_record()
    await storage.upsert(record)
    await storage.update_github_issue("abc123", 42, "open")
    result = await storage.get_by_fingerprint("abc123")
    assert result.github_issue_number == 42
    assert result.github_issue_state == "open"


async def test_mark_alerted(storage):
    record = _make_record()
    record.occurrences_since_alert = 5
    await storage.upsert(record)
    await storage.mark_alerted("abc123")
    result = await storage.get_by_fingerprint("abc123")
    assert result.occurrences_since_alert == 0
    assert result.last_alerted is not None


async def test_close_clears(storage):
    record = _make_record()
    await storage.upsert(record)
    await storage.close()
    result = await storage.get_by_fingerprint("abc123")
    assert result is None
