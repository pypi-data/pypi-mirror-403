"""
FIKA Logger - Production-grade logging with Slack/GitHub alerting.

Usage:
    from fika_logger import FikaLogger

    logger = FikaLogger(
        service_name="my-service",
        environment="production",
        slack_webhook="https://hooks.slack.com/...",
        github_token="ghp_...",
        github_repo="owner/repo",
    )

    @app.post("/webhook")
    @logger.trace
    async def webhook():
        with logger.context(client="x"):
            logger.info("Processing")
"""

from .logger import FikaLogger, ChildLogger
from .core.context import (
    context,
    get_current_context,
    add_context,
    update_context,
)
from .core.trace import trace

__version__ = "1.0.0"
__all__ = [
    "FikaLogger",
    "ChildLogger",
    "context",
    "get_current_context",
    "add_context",
    "update_context",
    "trace",
]
