import json
from datetime import datetime
from typing import Optional, Dict, Any

from .base import StorageBase, ErrorRecord


class RedisStorage(StorageBase):
    def __init__(self, url: str, prefix: str = "fika_logger:error"):
        import redis.asyncio as aioredis
        self.client = aioredis.from_url(url)
        self.prefix = prefix
        self.ttl = 60 * 60 * 24 * 30  # 30 days

    def _key(self, fingerprint: str) -> str:
        return f"{self.prefix}:{fingerprint}"

    def _serialize(self, record: ErrorRecord) -> str:
        data = {
            "fingerprint": record.fingerprint,
            "error_type": record.error_type,
            "message": record.message,
            "location": record.location,
            "function_name": record.function_name,
            "service": record.service,
            "environment": record.environment,
            "first_seen": record.first_seen.isoformat(),
            "last_seen": record.last_seen.isoformat(),
            "count": record.count,
            "last_alerted": record.last_alerted.isoformat() if record.last_alerted else None,
            "occurrences_since_alert": record.occurrences_since_alert,
            "github_issue_number": record.github_issue_number,
            "github_issue_state": record.github_issue_state,
            "status": record.status,
            "context": record.context,
            "full_traceback": record.full_traceback,
        }
        return json.dumps(data)

    def _deserialize(self, data: str) -> ErrorRecord:
        obj = json.loads(data)
        obj["first_seen"] = datetime.fromisoformat(obj["first_seen"])
        obj["last_seen"] = datetime.fromisoformat(obj["last_seen"])
        if obj["last_alerted"]:
            obj["last_alerted"] = datetime.fromisoformat(obj["last_alerted"])
        return ErrorRecord(**obj)

    async def get_by_fingerprint(self, fingerprint: str) -> Optional[ErrorRecord]:
        data = await self.client.get(self._key(fingerprint))
        if data:
            return self._deserialize(data)
        return None

    async def upsert(self, record: ErrorRecord) -> None:
        await self.client.set(self._key(record.fingerprint), self._serialize(record), ex=self.ttl)

    async def increment_count(self, fingerprint: str, context: Dict[str, Any], traceback: str) -> Optional[ErrorRecord]:
        record = await self.get_by_fingerprint(fingerprint)
        if record:
            record.count += 1
            record.occurrences_since_alert += 1
            record.last_seen = datetime.utcnow()
            record.context = context
            record.full_traceback = traceback
            await self.upsert(record)
            return record
        return None

    async def update_github_issue(self, fingerprint: str, issue_number: int, state: str) -> None:
        record = await self.get_by_fingerprint(fingerprint)
        if record:
            record.github_issue_number = issue_number
            record.github_issue_state = state
            await self.upsert(record)

    async def mark_alerted(self, fingerprint: str) -> None:
        record = await self.get_by_fingerprint(fingerprint)
        if record:
            record.last_alerted = datetime.utcnow()
            record.occurrences_since_alert = 0
            await self.upsert(record)

    async def close(self) -> None:
        await self.client.close()
