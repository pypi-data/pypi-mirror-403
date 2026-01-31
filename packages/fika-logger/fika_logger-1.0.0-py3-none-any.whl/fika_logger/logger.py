import sys
import asyncio
import traceback
import threading
from queue import Queue
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path

from loguru import logger as loguru_logger

from .config import get_environment_config, EnvironmentConfig
from .core.context import (
    context as context_manager,
    get_current_context,
    add_context as _add_context,
    update_context as _update_context,
)
from .core.trace import trace as trace_decorator
from .core.component import get_component_from_caller
from .core.fingerprint import (
    generate_fingerprint,
    extract_location_from_traceback,
    extract_function_from_traceback,
    shorten_traceback,
)
from .core.cooldown import should_alert
from .handlers.slack import SlackHandler
from .handlers.github import GitHubHandler
from .storage.base import StorageBase, ErrorRecord
from .middleware.fastapi import instrument_fastapi as _instrument_fastapi
from .formatters.github import extract_integration_from_path, filepath_to_component_label


# Background thread for processing alerts from sync code
_alert_queue: Queue = Queue()
_worker_thread: Optional[threading.Thread] = None
_worker_loop: Optional[asyncio.AbstractEventLoop] = None


def _start_worker() -> None:
    global _worker_thread, _worker_loop
    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_loop = asyncio.new_event_loop()
        _worker_thread = threading.Thread(target=_process_alerts, daemon=True)
        _worker_thread.start()


def _process_alerts() -> None:
    while True:
        coro = _alert_queue.get()
        if coro is None:
            break
        try:
            _worker_loop.run_until_complete(coro)
        except Exception as e:
            loguru_logger.warning(f"Alert processing failed: {e}")


def _make_error_file_sink(log_dir: str, service_name: str):
    """Create a custom sink function for the error log file."""
    error_log_path = f"{log_dir}/{service_name}.error.log"

    def sink(message):
        record = message.record
        separator = "=" * 80

        component = record["extra"].get("component", "unknown")
        context_str = record["extra"].get("context_str", "No context")

        # Format exception if present
        exception_str = ""
        if record["exception"] is not None:
            exc_type, exc_value, exc_tb = record["exception"]
            if exc_type is not None:
                exception_str = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_tb)
                )
            else:
                exception_str = "No traceback"
        else:
            exception_str = "No traceback"

        output = (
            f"\n{separator}\n"
            f"{record['time'].strftime('%Y-%m-%d %H:%M:%S')} | "
            f"{record['level'].name} | {component}\n\n"
            f"Message: {record['message']}\n\n"
            f"Context:\n{context_str}\n\n"
            f"{exception_str}\n"
            f"{separator}\n"
        )

        with open(error_log_path, "a") as f:
            f.write(output)

    return sink


class FikaLogger:
    """
    Production-grade logging library with Slack/GitHub alerting.

    Features:
    - Auto-detect component from file path
    - Context propagation through async tasks
    - Deduplication with cooldown
    - GitHub issue sync
    - Full traceback in error logs and GitHub
    - Optional child loggers with preset context
    """

    def __init__(
        self,
        service_name: str,
        environment: str,
        storage: Optional[str] = "memory",
        mongodb_uri: Optional[str] = None,
        redis_url: Optional[str] = None,
        slack_webhook: Optional[str] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        alert_cooldown_minutes: int = 15,
        alert_every_n_occurrences: int = 10,
        extra_labels: Optional[List[str]] = None,
        log_dir: str = "logs",
        integration_patterns: Optional[List[str]] = None,
    ):
        self.service_name = service_name
        self.environment = environment
        self.alert_cooldown_minutes = alert_cooldown_minutes
        self.alert_every_n_occurrences = alert_every_n_occurrences
        self.extra_labels = extra_labels or []
        self.log_dir = log_dir
        self.integration_patterns = integration_patterns or [
            "integrations/",
            "services/",
            "connectors/",
            "adapters/",
        ]

        # Get environment config
        self.config: EnvironmentConfig = get_environment_config(environment)

        # Create log directory
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        # Initialize storage
        self.storage: Optional[StorageBase] = None
        if storage and self.config.storage_enabled:
            self.storage = self._init_storage(storage, mongodb_uri, redis_url)
        elif storage and not self.config.storage_enabled:
            # Allow explicit override even when config disables storage
            if storage == "memory":
                from .storage.memory import MemoryStorage
                self.storage = MemoryStorage()
            elif storage == "mongodb" and mongodb_uri:
                from .storage.mongodb import MongoDBStorage
                self.storage = MongoDBStorage(mongodb_uri)
            elif storage == "redis" and redis_url:
                from .storage.redis import RedisStorage
                self.storage = RedisStorage(redis_url)

        # Initialize handlers
        self.slack: Optional[SlackHandler] = None
        if slack_webhook and self.config.slack_enabled:
            self.slack = SlackHandler(slack_webhook)

        self.github: Optional[GitHubHandler] = None
        if github_token and github_repo and self.config.github_enabled:
            self.github = GitHubHandler(github_token, github_repo)

        # Warn if Slack enabled without storage
        if self.slack and not self.storage:
            loguru_logger.warning(
                "Slack alerts enabled without storage. "
                "Every error will trigger an alert (no deduplication). "
                "Consider enabling storage='memory' for deduplication."
            )

        # Configure loguru
        self._configure_loguru()

    def _init_storage(
        self,
        storage: str,
        mongodb_uri: Optional[str],
        redis_url: Optional[str],
    ) -> Optional[StorageBase]:
        if storage == "mongodb" and mongodb_uri:
            from .storage.mongodb import MongoDBStorage
            return MongoDBStorage(mongodb_uri)
        elif storage == "redis" and redis_url:
            from .storage.redis import RedisStorage
            return RedisStorage(redis_url)
        elif storage == "memory":
            from .storage.memory import MemoryStorage
            return MemoryStorage()
        return None

    def _configure_loguru(self) -> None:
        loguru_logger.remove()

        # Console - colored output
        if self.config.console_enabled:
            loguru_logger.add(
                sink=sys.stderr,
                format=(
                    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{extra[component]}</cyan> | "
                    "<level>{message}</level>"
                ),
                level="DEBUG",
                colorize=True,
                filter=lambda record: "component" in record["extra"],
            )
            # Fallback for logs without component
            loguru_logger.add(
                sink=sys.stderr,
                format=(
                    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                    "<level>{level: <8}</level> | "
                    "<level>{message}</level>"
                ),
                level="DEBUG",
                colorize=True,
                filter=lambda record: "component" not in record["extra"],
            )

        # Main log file - all levels, JSON, reset on start
        if self.config.file_enabled:
            mode = "w" if self.config.file_reset_on_start else "a"
            loguru_logger.add(
                sink=f"{self.log_dir}/{self.service_name}.log",
                format="{message}",
                serialize=True,
                level="DEBUG",
                mode=mode,
            )

        # Error log file - custom sink, reset on start
        if self.config.error_file_enabled:
            if self.config.error_file_reset_on_start:
                error_path = f"{self.log_dir}/{self.service_name}.error.log"
                open(error_path, "w").close()

            loguru_logger.add(
                sink=_make_error_file_sink(self.log_dir, self.service_name),
                level="ERROR",
                backtrace=True,
                diagnose=True,
                filter=lambda record: "component" in record["extra"],
            )

    def _log(
        self,
        level: str,
        message: str,
        exc_info: Optional[BaseException] = None,
        **kwargs,
    ) -> None:
        # Auto-detect component from caller's file path
        component = kwargs.pop("component", None) or get_component_from_caller()

        # Get current context and merge with kwargs
        ctx = get_current_context()
        ctx.update(kwargs)
        ctx["component"] = component

        # Format context for error file
        context_str = "\n".join([f"  {k}: {v}" for k, v in ctx.items()])

        # Bind extras for loguru (component and context_str are already in ctx)
        bound_logger = loguru_logger.bind(
            context_str=context_str,
            **ctx,
        )

        # Log with loguru
        # Escape braces in context to avoid loguru format interpretation
        ctx_str = str(ctx).replace("{", "{{").replace("}", "}}")
        log_func = getattr(bound_logger, level)
        log_message = f"{message} | context={ctx_str}"
        if exc_info:
            log_func(log_message, exception=exc_info)
        else:
            log_func(log_message)

        # Handle error/critical - always call, let _handle_error decide internally
        if level in ("error", "critical"):
            self._queue_alert(level, message, exc_info, ctx, component)

    def _queue_alert(
        self,
        level: str,
        message: str,
        exc_info: Optional[BaseException],
        context: Dict[str, Any],
        component: str,
    ) -> None:
        coro = self._handle_error(level, message, exc_info, context, component)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            _start_worker()
            _alert_queue.put(coro)

    async def _handle_error(
        self,
        level: str,
        message: str,
        exc_info: Optional[BaseException],
        context: Dict[str, Any],
        component: str,
    ) -> None:
        # Get full traceback
        if exc_info:
            tb_str = "".join(
                traceback.format_exception(
                    type(exc_info), exc_info, exc_info.__traceback__
                )
            )
            error_type = exc_info.__class__.__name__
            error_message = str(exc_info)
        else:
            tb_str = "No traceback available"
            error_type = "Error"
            error_message = message

        # Extract location and function from traceback
        location = (
            extract_location_from_traceback(tb_str)
            if exc_info
            else f"{component}:0"
        )
        function_name = (
            extract_function_from_traceback(tb_str) if exc_info else "unknown"
        )
        short_tb = shorten_traceback(tb_str) if exc_info else "N/A"

        # Generate fingerprint for deduplication
        fingerprint = generate_fingerprint(error_type, location, self.service_name)

        # Check storage for existing error
        existing: Optional[ErrorRecord] = None
        if self.storage:
            existing = await self.storage.get_by_fingerprint(fingerprint)

        github_issue_number: Optional[int] = None
        first_seen = datetime.utcnow()
        occurrences = 1

        if existing:
            # Increment count
            updated = await self.storage.increment_count(
                fingerprint, context, tb_str
            )
            if updated:
                existing = updated
                occurrences = existing.count
                first_seen = existing.first_seen
                github_issue_number = existing.github_issue_number

            # Check if GitHub issue is still open
            if self.github and github_issue_number:
                is_open = await self.github.is_issue_open(github_issue_number)
                if not is_open:
                    github_issue_number = await self._create_github_issue(
                        error_type=error_type,
                        error_message=error_message,
                        location=location,
                        function_name=function_name,
                        full_traceback=tb_str,
                        context=context,
                        first_seen=first_seen,
                        occurrences=occurrences,
                        level=level,
                    )
                    if github_issue_number and self.storage:
                        await self.storage.update_github_issue(
                            fingerprint, github_issue_number, "open"
                        )

            # Check if should alert based on cooldown
            if should_alert(
                existing.last_alerted,
                existing.occurrences_since_alert,
                self.alert_cooldown_minutes,
                self.alert_every_n_occurrences,
            ):
                await self._send_slack_alert(
                    error_type=error_type,
                    error_message=error_message,
                    location=location,
                    function_name=function_name,
                    short_traceback=short_tb,
                    context=context,
                    first_seen=first_seen,
                    occurrences=occurrences,
                    github_issue_number=github_issue_number,
                )
                if self.storage:
                    await self.storage.mark_alerted(fingerprint)

        else:
            # New error - create GitHub issue first
            if self.github:
                github_issue_number = await self._create_github_issue(
                    error_type=error_type,
                    error_message=error_message,
                    location=location,
                    function_name=function_name,
                    full_traceback=tb_str,
                    context=context,
                    first_seen=first_seen,
                    occurrences=occurrences,
                    level=level,
                )

            # Insert into storage
            if self.storage:
                record = ErrorRecord(
                    fingerprint=fingerprint,
                    error_type=error_type,
                    message=error_message,
                    location=location,
                    function_name=function_name,
                    service=self.service_name,
                    environment=self.environment,
                    first_seen=first_seen,
                    last_seen=first_seen,
                    count=1,
                    last_alerted=first_seen,
                    occurrences_since_alert=0,
                    github_issue_number=github_issue_number,
                    github_issue_state="open" if github_issue_number else "",
                    status="open",
                    context=context,
                    full_traceback=tb_str,
                )
                await self.storage.upsert(record)

            # Send Slack alert for new errors
            await self._send_slack_alert(
                error_type=error_type,
                error_message=error_message,
                location=location,
                function_name=function_name,
                short_traceback=short_tb,
                context=context,
                first_seen=first_seen,
                occurrences=occurrences,
                github_issue_number=github_issue_number,
            )

    async def _create_github_issue(
        self,
        error_type: str,
        error_message: str,
        location: str,
        function_name: str,
        full_traceback: str,
        context: Dict[str, Any],
        first_seen: datetime,
        occurrences: int,
        level: str = "error",
    ) -> Optional[int]:
        if not self.github:
            return None

        component = context.get("component", "")
        component_label = (
            filepath_to_component_label(component) if component else "unknown"
        )

        integration = (
            extract_integration_from_path(component, self.integration_patterns)
            if component
            else None
        )

        labels = [
            f"service:{self.service_name}",
            f"error:{error_type}",
            f"env:{self.environment}",
            f"component:{component_label}",
            *self.extra_labels,
        ]

        if integration:
            labels.append(f"integration:{integration}")

        if level == "critical":
            labels.append("priority:critical")
        else:
            labels.append("priority:high")

        return await self.github.create_issue(
            service_name=self.service_name,
            environment=self.environment,
            error_type=error_type,
            error_message=error_message,
            location=location,
            function_name=function_name,
            full_traceback=full_traceback,
            context=context,
            first_seen=first_seen.isoformat(),
            occurrences=occurrences,
            labels=labels,
        )

    async def _send_slack_alert(
        self,
        error_type: str,
        error_message: str,
        location: str,
        function_name: str,
        short_traceback: str,
        context: Dict[str, Any],
        first_seen: datetime,
        occurrences: int,
        github_issue_number: Optional[int],
    ) -> None:
        if not self.slack:
            return

        await self.slack.send_alert(
            service_name=self.service_name,
            environment=self.environment,
            error_type=error_type,
            error_message=error_message,
            location=location,
            function_name=function_name,
            short_traceback=short_traceback,
            context=context,
            first_seen=first_seen,
            occurrences=occurrences,
            github_issue_number=github_issue_number,
            github_repo=self.github.repo if self.github else None,
        )

    # ==================== Public Logging Methods ====================

    def debug(self, message: str, **kwargs) -> None:
        self._log("debug", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log("warning", message, **kwargs)

    def error(
        self, message: str, exc_info: Optional[BaseException] = None, **kwargs
    ) -> None:
        self._log("error", message, exc_info=exc_info, **kwargs)

    def critical(
        self, message: str, exc_info: Optional[BaseException] = None, **kwargs
    ) -> None:
        self._log("critical", message, exc_info=exc_info, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        exc_info = sys.exc_info()[1]
        self._log("error", message, exc_info=exc_info, **kwargs)

    # ==================== Context Methods ====================

    def context(self, **kwargs):
        return context_manager(**kwargs)

    def get_current_context(self) -> Dict[str, Any]:
        return get_current_context()

    def add_context(self, **kwargs) -> None:
        _add_context(**kwargs)

    def update_context(self, **kwargs) -> None:
        _update_context(**kwargs)

    # ==================== Decorators ====================

    def trace(self, func: Callable) -> Callable:
        return trace_decorator(func)

    # ==================== Integrations ====================

    def instrument_fastapi(self, app) -> None:
        _instrument_fastapi(app, self)

    # ==================== Child Logger ====================

    def child(self, **default_context) -> "ChildLogger":
        return ChildLogger(parent=self, default_context=default_context)


class ChildLogger:
    """Child logger with preset default context"""

    def __init__(self, parent: FikaLogger, default_context: Dict[str, Any]):
        self._parent = parent
        self._default_context = default_context

    def _merge(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        merged = self._default_context.copy()
        merged.update(kwargs)
        return merged

    def debug(self, message: str, **kwargs) -> None:
        self._parent.debug(message, **self._merge(kwargs))

    def info(self, message: str, **kwargs) -> None:
        self._parent.info(message, **self._merge(kwargs))

    def warning(self, message: str, **kwargs) -> None:
        self._parent.warning(message, **self._merge(kwargs))

    def error(
        self, message: str, exc_info: Optional[BaseException] = None, **kwargs
    ) -> None:
        self._parent.error(message, exc_info=exc_info, **self._merge(kwargs))

    def critical(
        self, message: str, exc_info: Optional[BaseException] = None, **kwargs
    ) -> None:
        self._parent.critical(message, exc_info=exc_info, **self._merge(kwargs))

    def exception(self, message: str, **kwargs) -> None:
        self._parent.exception(message, **self._merge(kwargs))

    def context(self, **kwargs):
        return self._parent.context(**self._merge(kwargs))

    def get_current_context(self) -> Dict[str, Any]:
        return self._parent.get_current_context()

    def add_context(self, **kwargs) -> None:
        self._parent.add_context(**kwargs)

    def update_context(self, **kwargs) -> None:
        self._parent.update_context(**kwargs)
