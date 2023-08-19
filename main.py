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
