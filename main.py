"""In-memory idempotency keys bound to request bytes, with cached byte responses."""
import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import threading


class IdempotencyConflict(ValueError):
    pass


class RequestInProgress(RuntimeError):
    pass


@dataclass(frozen=True)
class Result:
    response: bytes
    replayed: bool


@dataclass
class Entry:
    digest: bytes
    expires_at: float
    response: object = None


class IdempotencyStore:
    def __init__(self, ttl_seconds=60):
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, (int, float)):
            raise ValueError("ttl_seconds must be positive and finite")
        if not math.isfinite(ttl_seconds) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive and finite")
        self.ttl_seconds = ttl_seconds
        self._entries = {}
        self._lock = threading.RLock()
        self._last_now = None

    def run(self, key, request, operation, now):
        if not isinstance(key, str) or not key or len(key) > 200:
            raise ValueError("key must contain 1 to 200 characters")
        if not isinstance(request, bytes):
            raise TypeError("request must be bytes")
        if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now):
            raise ValueError("now must be finite")
        digest = hashlib.sha256(request).digest()
        with self._lock:
            if self._last_now is not None and now < self._last_now:
                raise ValueError("clock must not move backwards")
            self._last_now = now
            expired = [k for k, entry in self._entries.items()
                       if entry.response is not None and now >= entry.expires_at]
            for expired_key in expired:
                del self._entries[expired_key]
            entry = self._entries.get(key)
            if entry is not None:
                if entry.digest != digest:
                    raise IdempotencyConflict("key was already used for different request bytes")
                if entry.response is None:
                    raise RequestInProgress("matching operation is still running")
                return Result(entry.response, True)
            entry = Entry(digest, now + self.ttl_seconds)
            self._entries[key] = entry
        try:
            response = operation()
            if not isinstance(response, bytes):
                raise TypeError("operation must return bytes")
        except BaseException:
            with self._lock:
                if self._entries.get(key) is entry:
                    del self._entries[key]
            raise
        with self._lock:
            entry.response = response
        return Result(response, False)
