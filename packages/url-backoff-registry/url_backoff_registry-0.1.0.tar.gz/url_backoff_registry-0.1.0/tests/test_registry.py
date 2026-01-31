from datetime import datetime, timedelta

from url_backoff_registry import BackoffRegistry


def test_backoff_triggers():
    now = datetime(2024, 1, 1, 12, 0, 0)
    clock = lambda: now
    registry = BackoffRegistry(window_seconds=30, threshold=2, backoff_seconds=60, clock=clock)

    registry.record_failure("a")
    assert registry.should_backoff("a") is False

    registry.record_failure("a")
    assert registry.should_backoff("a") is True


def test_backoff_expires():
    now = datetime(2024, 1, 1, 12, 0, 0)
    times = [now, now, now + timedelta(seconds=1), now + timedelta(seconds=61)]
    clock = lambda: times.pop(0)
    registry = BackoffRegistry(window_seconds=30, threshold=2, backoff_seconds=60, clock=clock)

    registry.record_failure("a")
    registry.record_failure("a")
    assert registry.should_backoff("a") is True
    assert registry.should_backoff("a") is False


def test_clear():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(clock=lambda: now)
    registry.record_failure("a")
    registry.clear("a")
    assert registry.should_backoff("a") is False
