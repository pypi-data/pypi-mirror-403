import pytest
from fika_logger import FikaLogger


def test_logger_init_development():
    logger = FikaLogger(
        service_name="test-service",
        environment="development",
        storage=None,
    )
    assert logger.service_name == "test-service"
    assert logger.environment == "development"
    assert logger.slack is None
    assert logger.github is None


def test_logger_init_with_memory_storage():
    logger = FikaLogger(
        service_name="test-service",
        environment="development",
        storage="memory",
    )
    # Dev has storage_enabled=False by default, but explicit storage should work
    assert logger.storage is not None


def test_logger_basic_logging(capsys):
    logger = FikaLogger(
        service_name="test-service",
        environment="development",
        storage=None,
    )
    logger.info("test message", key="value")
    # Should not raise


def test_logger_context():
    logger = FikaLogger(
        service_name="test-service",
        environment="development",
        storage=None,
    )
    with logger.context(client="x"):
        ctx = logger.get_current_context()
        assert ctx["client"] == "x"


def test_child_logger():
    logger = FikaLogger(
        service_name="test-service",
        environment="development",
        storage=None,
    )
    child = logger.child(component="/app/src/zoho/client.py")
    # Should not raise
    child.info("test from child")


def test_logger_exception_handling():
    logger = FikaLogger(
        service_name="test-service",
        environment="development",
        storage=None,
    )
    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("caught error")
    # Should not raise
