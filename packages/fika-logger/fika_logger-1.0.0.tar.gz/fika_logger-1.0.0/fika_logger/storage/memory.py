from datetime import datetime
from typing import Optional, Dict, Any

from .base import StorageBase, ErrorRecord


class MemoryStorage(StorageBase):
    def __init__(self):
        self._store: Dict[str, ErrorRecord] = {}

    async def get_by_fingerprint(self, fingerprint: str) -> Optional[ErrorRecord]:
        return self._store.get(fingerprint)

    async def upsert(self, record: ErrorRecord) -> None:
        self._store[record.fingerprint] = record

    async def increment_count(self, fingerprint: str, context: Dict[str, Any], traceback: str) -> Optional[ErrorRecord]:
        record = self._store.get(fingerprint)
        if record:
            record.count += 1
            record.occurrences_since_alert += 1
            record.last_seen = datetime.utcnow()
            record.context = context
            record.full_traceback = traceback
            return record
        return None

    async def update_github_issue(self, fingerprint: str, issue_number: int, state: str) -> None:
        record = self._store.get(fingerprint)
        if record:
            record.github_issue_number = issue_number
            record.github_issue_state = state

    async def mark_alerted(self, fingerprint: str) -> None:
        record = self._store.get(fingerprint)
        if record:
            record.last_alerted = datetime.utcnow()
            record.occurrences_since_alert = 0

    async def close(self) -> None:
        self._store.clear()
