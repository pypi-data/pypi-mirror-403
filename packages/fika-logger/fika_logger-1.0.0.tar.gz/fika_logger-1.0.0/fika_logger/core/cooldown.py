from datetime import datetime, timedelta
from typing import Optional


def should_alert(
    last_alerted: Optional[datetime],
    occurrences_since_alert: int,
    cooldown_minutes: int,
    alert_every_n: int
) -> bool:
    if last_alerted is None:
        return True
    time_passed = datetime.utcnow() - last_alerted
    if time_passed > timedelta(minutes=cooldown_minutes):
        return True
    if occurrences_since_alert >= alert_every_n:
        return True
    return False
