from datetime import datetime, timedelta
from fika_logger.core.cooldown import should_alert


def test_should_alert_first_time():
    assert should_alert(None, 0, 15, 10) is True


def test_should_not_alert_within_cooldown():
    last = datetime.utcnow() - timedelta(minutes=5)
    assert should_alert(last, 3, 15, 10) is False


def test_should_alert_after_cooldown():
    last = datetime.utcnow() - timedelta(minutes=20)
    assert should_alert(last, 3, 15, 10) is True


def test_should_alert_on_count_threshold():
    last = datetime.utcnow() - timedelta(minutes=1)
    assert should_alert(last, 10, 15, 10) is True


def test_should_not_alert_below_threshold():
    last = datetime.utcnow() - timedelta(minutes=1)
    assert should_alert(last, 9, 15, 10) is False
