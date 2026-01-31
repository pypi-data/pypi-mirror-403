from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from loguru import logger as loguru_logger

from ..formatters.slack import format_slack_message


class SlackHandler:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send_alert(
        self,
        service_name: str,
        environment: str,
        error_type: str,
        error_message: str,
        location: str,
        function_name: str,
        short_traceback: str,
        context: Dict[str, Any],
        first_seen: datetime,
        occurrences: int,
        github_issue_number: Optional[int],
        github_repo: Optional[str]
    ) -> bool:
        try:
            blocks = format_slack_message(
                service_name=service_name,
                environment=environment,
                error_type=error_type,
                error_message=error_message,
                location=location,
                function_name=function_name,
                short_traceback=short_traceback,
                context=context,
                first_seen=first_seen,
                occurrences=occurrences,
                github_issue_number=github_issue_number,
                github_repo=github_repo
            )
            response = await self.client.post(self.webhook_url, json={"blocks": blocks})
            response.raise_for_status()
            return True
        except Exception as e:
            loguru_logger.warning(f"Slack alert failed: {e}")
            return False

    async def close(self) -> None:
        await self.client.aclose()
