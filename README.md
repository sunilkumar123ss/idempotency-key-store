# Idempotency Key Store

Replay successful byte responses while detecting conflicting key reuse.

All bundled examples use synthetic data.

## Run

Requires Python 3.9 or later; no third-party packages or network access are needed.

```sh
python3 main.py
python3 main.py --help
python3 -m unittest -v
```

Run these commands from this repository's directory. The demo can also be launched from any directory by passing the absolute path to `main.py`.

## How it works

A key is bound to a SHA-256 digest of the exact request bytes. The first call reserves an in-progress entry before executing its callback. Matching calls receive the stored byte response after completion; different request bytes raise `IdempotencyConflict`. Concurrent or reentrant matching calls while the callback runs raise `RequestInProgress`.

Successful responses expire at `admission_time + ttl_seconds`. Pending operations do not expire. A callback failure or non-byte response releases the key. A lock protects the mapping while callbacks run outside it. Expired completed entries are swept on each admission, costing O(number of stored keys).

## Reuse

```python
from main import IdempotencyStore

store = IdempotencyStore(ttl_seconds=60)
first = store.run("demo-key", b"quantity=2", lambda: b"order-001", now=0)
again = store.run("demo-key", b"quantity=2", lambda: b"unused", now=1)
assert not first.replayed
assert again.replayed and again.response == b"order-001"
```

## Demo behavior

The synthetic order callback runs once for the initial request, is replayed during its TTL, and runs again at expiry. Even an empty byte response is cacheable.

## Boundaries

This is in-memory coordination, not a durable transaction or an exactly-once guarantee. If the process stops after a side effect and before recording its response, retries can repeat that side effect. A callback that never returns retains its pending key. Time is explicitly supplied and must be globally nondecreasing for the store; TTL begins at admission, not completion. Entries have no maximum count. Semantically equal JSON with different byte encodings counts as a different request.

## Verification

`test_main.py` exercises boundary conditions, invalid inputs, and meaningful behavior specific to this implementation. The default demo is deterministic and completes without external services. See the collection's verification report for the recorded run; run the commands above to verify this repository independently.

## Repository checks

```sh
python3 verify.py
```

This runs the isolated test suite, synthetic example, and CLI help. The included GitHub Actions workflow repeats these checks when the repository is published. No hosted CI result is claimed by the local verification report.
