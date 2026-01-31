from datetime import datetime, timedelta

import pytest

from url_backoff_registry import BackoffError, BackoffRegistry


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


def test_per_key_rules():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(threshold=3, clock=lambda: now)

    # Default rule: 3 failures
    registry.record_failure("default")
    registry.record_failure("default")
    assert registry.should_backoff("default") is False

    # Custom rule: 1 failure
    registry.set_rule("sensitive", threshold=1)
    registry.record_failure("sensitive")
    assert registry.should_backoff("sensitive") is True

    # Clear custom rule
    registry.clear("sensitive")
    registry.clear_rule("sensitive")
    registry.record_failure("sensitive")
    assert registry.should_backoff("sensitive") is False  # Back to default (3)


def test_stats():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(threshold=3, backoff_seconds=60, clock=lambda: now)

    stats = registry.stats("a")
    assert stats["failures_in_window"] == 0
    assert stats["in_backoff"] is False
    assert stats["backoff_until"] is None

    registry.record_failure("a")
    registry.record_failure("a")
    stats = registry.stats("a")
    assert stats["failures_in_window"] == 2
    assert stats["in_backoff"] is False

    registry.record_failure("a")
    stats = registry.stats("a")
    assert stats["failures_in_window"] == 3
    assert stats["in_backoff"] is True
    assert stats["backoff_until"] == now + timedelta(seconds=60)


def test_keys():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(clock=lambda: now)

    assert registry.keys() == []

    registry.record_failure("a")
    registry.record_failure("b")
    assert set(registry.keys()) == {"a", "b"}


def test_track_decorator_records_failure():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(threshold=2, clock=lambda: now)

    @registry.track("api")
    def failing_call():
        raise ValueError("fail")

    with pytest.raises(ValueError):
        failing_call()

    assert registry.stats("api")["failures_in_window"] == 1

    with pytest.raises(ValueError):
        failing_call()

    assert registry.should_backoff("api") is True


def test_track_decorator_raises_backoff_error():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(threshold=1, clock=lambda: now)

    @registry.track("api")
    def call():
        raise ValueError("fail")

    with pytest.raises(ValueError):
        call()

    with pytest.raises(BackoffError) as exc_info:
        call()

    assert exc_info.value.key == "api"


def test_track_decorator_clears_on_success():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(threshold=3, clock=lambda: now)

    call_count = 0

    @registry.track("api")
    def call():
        nonlocal call_count
        call_count += 1
        return "ok"

    registry.record_failure("api")
    registry.record_failure("api")
    assert registry.stats("api")["failures_in_window"] == 2

    result = call()
    assert result == "ok"
    assert registry.stats("api")["failures_in_window"] == 0


def test_track_decorator_no_clear_on_success():
    now = datetime(2024, 1, 1, 12, 0, 0)
    registry = BackoffRegistry(threshold=3, clock=lambda: now)

    @registry.track("api", clear_on_success=False)
    def call():
        return "ok"

    registry.record_failure("api")
    registry.record_failure("api")

    call()
    assert registry.stats("api")["failures_in_window"] == 2
