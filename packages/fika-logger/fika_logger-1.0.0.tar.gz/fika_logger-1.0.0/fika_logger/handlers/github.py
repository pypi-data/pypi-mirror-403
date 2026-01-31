from typing import Optional, Dict, Any, List

import httpx
from loguru import logger as loguru_logger

from ..formatters.github import format_github_issue


class GitHubHandler:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )

    async def get_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(
                f"{self.api_base}/repos/{self.repo}/issues/{issue_number}"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            loguru_logger.warning(f"GitHub get_issue failed: {e}")
        return None

    async def is_issue_open(self, issue_number: int) -> bool:
        issue = await self.get_issue(issue_number)
        if issue:
            return issue.get("state") == "open"
        return False

    async def create_issue(
        self,
        service_name: str,
        environment: str,
        error_type: str,
        error_message: str,
        location: str,
        function_name: str,
        full_traceback: str,
        context: Dict[str, Any],
        first_seen: str,
        occurrences: int,
        labels: List[str]
    ) -> Optional[int]:
        try:
            title, body = format_github_issue(
                service_name=service_name,
                environment=environment,
                error_type=error_type,
                error_message=error_message,
                location=location,
                function_name=function_name,
                full_traceback=full_traceback,
                context=context,
                first_seen=first_seen,
                occurrences=occurrences
            )
            response = await self.client.post(
                f"{self.api_base}/repos/{self.repo}/issues",
                json={"title": title, "body": body, "labels": labels}
            )
            response.raise_for_status()
            return response.json()["number"]
        except Exception as e:
            loguru_logger.warning(f"GitHub issue creation failed: {e}")
            return None

    async def close(self) -> None:
        await self.client.aclose()
