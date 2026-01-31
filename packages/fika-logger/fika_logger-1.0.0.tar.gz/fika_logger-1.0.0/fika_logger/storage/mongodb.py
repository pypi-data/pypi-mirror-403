from datetime import datetime
from typing import Optional, Dict, Any

from .base import StorageBase, ErrorRecord


class MongoDBStorage(StorageBase):
    def __init__(self, uri: str, database: str = "fika_logger"):
        from motor.motor_asyncio import AsyncIOMotorClient
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database]
        self.collection = self.db["errors"]

    async def get_by_fingerprint(self, fingerprint: str) -> Optional[ErrorRecord]:
        doc = await self.collection.find_one({"fingerprint": fingerprint})
        if doc:
            doc.pop("_id", None)
            return ErrorRecord(**doc)
        return None

    async def upsert(self, record: ErrorRecord) -> None:
        data = {
            "fingerprint": record.fingerprint,
            "error_type": record.error_type,
            "message": record.message,
            "location": record.location,
            "function_name": record.function_name,
            "service": record.service,
            "environment": record.environment,
            "first_seen": record.first_seen,
            "last_seen": record.last_seen,
            "count": record.count,
            "last_alerted": record.last_alerted,
            "occurrences_since_alert": record.occurrences_since_alert,
            "github_issue_number": record.github_issue_number,
            "github_issue_state": record.github_issue_state,
            "status": record.status,
            "context": record.context,
            "full_traceback": record.full_traceback,
        }
        await self.collection.update_one(
            {"fingerprint": record.fingerprint},
            {"$set": data},
            upsert=True
        )

    async def increment_count(self, fingerprint: str, context: Dict[str, Any], traceback: str) -> Optional[ErrorRecord]:
        result = await self.collection.find_one_and_update(
            {"fingerprint": fingerprint},
            {
                "$inc": {"count": 1, "occurrences_since_alert": 1},
                "$set": {
                    "last_seen": datetime.utcnow(),
                    "context": context,
                    "full_traceback": traceback,
                }
            },
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return ErrorRecord(**result)
        return None

    async def update_github_issue(self, fingerprint: str, issue_number: int, state: str) -> None:
        await self.collection.update_one(
            {"fingerprint": fingerprint},
            {"$set": {"github_issue_number": issue_number, "github_issue_state": state}}
        )

    async def mark_alerted(self, fingerprint: str) -> None:
        await self.collection.update_one(
            {"fingerprint": fingerprint},
            {"$set": {"last_alerted": datetime.utcnow(), "occurrences_since_alert": 0}}
        )

    async def close(self) -> None:
        self.client.close()
