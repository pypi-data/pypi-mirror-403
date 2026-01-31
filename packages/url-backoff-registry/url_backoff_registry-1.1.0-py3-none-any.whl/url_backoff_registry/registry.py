"""In-memory URL backoff registry with sliding window thresholds."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Dict, List, Optional, TypedDict, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

ClockFn = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.utcnow()


@dataclass
class BackoffRule:
    window_seconds: int = 30
    threshold: int = 3
    backoff_seconds: int = 120


class BackoffStats(TypedDict):
    failures_in_window: int
    in_backoff: bool
    backoff_until: Optional[datetime]


class BackoffError(Exception):
    """Raised when a call is attempted while in backoff."""

    def __init__(self, key: str, until: datetime):
        self.key = key
        self.until = until
        super().__init__(f"Backing off from {key} until {until}")


@dataclass
class BackoffRegistry:
    window_seconds: int = 30
    threshold: int = 3
    backoff_seconds: int = 120
    clock: ClockFn = _utc_now
    _issues: Dict[str, List[datetime]] = field(default_factory=dict)
    _backoff_until: Dict[str, datetime] = field(default_factory=dict)
    _rules: Dict[str, BackoffRule] = field(default_factory=dict)

    def _rule(self, key: str) -> BackoffRule:
        if key in self._rules:
            return self._rules[key]
        return BackoffRule(
            window_seconds=self.window_seconds,
            threshold=self.threshold,
            backoff_seconds=self.backoff_seconds,
        )

    def set_rule(
        self,
        key: str,
        window_seconds: Optional[int] = None,
        threshold: Optional[int] = None,
        backoff_seconds: Optional[int] = None,
    ) -> None:
        """Set custom backoff rules for a specific key."""
        self._rules[key] = BackoffRule(
            window_seconds=window_seconds if window_seconds is not None else self.window_seconds,
            threshold=threshold if threshold is not None else self.threshold,
            backoff_seconds=backoff_seconds if backoff_seconds is not None else self.backoff_seconds,
        )

    def clear_rule(self, key: str) -> None:
        """Remove custom rules for a key, reverting to defaults."""
        self._rules.pop(key, None)

    def record_failure(self, key: str) -> None:
        """Record a failure for the given key and register backoff if needed."""
        rule = self._rule(key)
        window = timedelta(seconds=rule.window_seconds)
        now = self.clock()

        issues = [
            stamp
            for stamp in self._issues.get(key, [])
            if now <= stamp + window
        ]
        issues.append(now)
        self._issues[key] = issues

        if len(issues) >= rule.threshold:
            self._backoff_until[key] = now + timedelta(seconds=rule.backoff_seconds)

    def should_backoff(self, key: str) -> bool:
        """Return True if the key is currently in a backoff window."""
        until = self._backoff_until.get(key)
        if until is None:
            return False
        return self.clock() < until

    def next_retry_at(self, key: str) -> Optional[datetime]:
        """Return the time when backoff ends, if any."""
        return self._backoff_until.get(key)

    def clear(self, key: str) -> None:
        """Clear backoff and issue history for the key."""
        self._issues.pop(key, None)
        self._backoff_until.pop(key, None)

    def stats(self, key: str) -> BackoffStats:
        """Return statistics for a key."""
        rule = self._rule(key)
        window = timedelta(seconds=rule.window_seconds)
        now = self.clock()

        failures_in_window = len([
            stamp
            for stamp in self._issues.get(key, [])
            if now <= stamp + window
        ])

        return BackoffStats(
            failures_in_window=failures_in_window,
            in_backoff=self.should_backoff(key),
            backoff_until=self._backoff_until.get(key),
        )

    def keys(self) -> List[str]:
        """Return all keys that have recorded failures or are in backoff."""
        return list(set(self._issues.keys()) | set(self._backoff_until.keys()))

    def track(
        self,
        key: str,
        clear_on_success: bool = True,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Decorator to track failures and optionally clear on success.

        Raises BackoffError if the key is in backoff when the function is called.
        """

        def decorator(fn: Callable[P, R]) -> Callable[P, R]:
            @wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                if self.should_backoff(key):
                    raise BackoffError(key, self._backoff_until[key])
                try:
                    result = fn(*args, **kwargs)
                    if clear_on_success:
                        self.clear(key)
                    return result
                except Exception:
                    self.record_failure(key)
                    raise

            return wrapper

        return decorator
