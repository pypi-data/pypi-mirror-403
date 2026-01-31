"""In-memory URL backoff registry with sliding window thresholds."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

ClockFn = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.utcnow()


@dataclass
class BackoffRule:
    window_seconds: int = 30
    threshold: int = 3
    backoff_seconds: int = 120


@dataclass
class BackoffRegistry:
    window_seconds: int = 30
    threshold: int = 3
    backoff_seconds: int = 120
    clock: ClockFn = _utc_now
    _issues: Dict[str, List[datetime]] = field(default_factory=dict)
    _backoff_until: Dict[str, datetime] = field(default_factory=dict)

    def _rule(self) -> BackoffRule:
        return BackoffRule(
            window_seconds=self.window_seconds,
            threshold=self.threshold,
            backoff_seconds=self.backoff_seconds,
        )

    def record_failure(self, key: str) -> None:
        """Record a failure for the given key and register backoff if needed."""
        rule = self._rule()
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
