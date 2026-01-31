from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ErrorRecord:
    fingerprint: str
    error_type: str
    message: str
    location: str
    function_name: str
    service: str
    environment: str
    first_seen: datetime
    last_seen: datetime
    count: int
    last_alerted: Optional[datetime]
    occurrences_since_alert: int
    github_issue_number: Optional[int]
    github_issue_state: str
    status: str
    context: Dict[str, Any] = field(default_factory=dict)
    full_traceback: str = ""


class StorageBase(ABC):
    @abstractmethod
    async def get_by_fingerprint(self, fingerprint: str) -> Optional[ErrorRecord]:
        pass

    @abstractmethod
    async def upsert(self, record: ErrorRecord) -> None:
        pass

    @abstractmethod
    async def increment_count(self, fingerprint: str, context: Dict[str, Any], traceback: str) -> Optional[ErrorRecord]:
        pass

    @abstractmethod
    async def update_github_issue(self, fingerprint: str, issue_number: int, state: str) -> None:
        pass

    @abstractmethod
    async def mark_alerted(self, fingerprint: str) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
