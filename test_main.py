import unittest
from main import IdempotencyStore, IdempotencyConflict, RequestInProgress


class IdempotencyTests(unittest.TestCase):
    def test_replay_returns_original_without_callback(self):
        store = IdempotencyStore()
        first = store.run("k", b"request", lambda: b"original", 0)
        second = store.run("k", b"request", lambda: self.fail("must not execute"), 1)
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(second.response, b"original")

    def test_payload_conflict(self):
        store = IdempotencyStore()
        store.run("k", b"a", lambda: b"ok", 0)
        with self.assertRaises(IdempotencyConflict):
            store.run("k", b"b", lambda: b"wrong", 1)

    def test_exact_expiry_allows_new_request(self):
        store = IdempotencyStore(5)
        store.run("k", b"a", lambda: b"old", 0)
        result = store.run("k", b"b", lambda: b"new", 5)
        self.assertFalse(result.replayed)
        self.assertEqual(result.response, b"new")

    def test_failure_does_not_cache(self):
        store = IdempotencyStore()
        def fail(): raise OSError("synthetic failure")
        with self.assertRaises(OSError): store.run("k", b"a", fail, 0)
        self.assertFalse(store.run("k", b"a", lambda: b"ok", 1).replayed)

    def test_pending_request_rejected_even_after_ttl(self):
        store = IdempotencyStore(1)
        def callback():
            with self.assertRaises(RequestInProgress):
                store.run("k", b"a", lambda: b"duplicate", 5)
            return b"done"
        self.assertEqual(store.run("k", b"a", callback, 0).response, b"done")

    def test_empty_response_is_cached(self):
        store = IdempotencyStore()
        store.run("k", b"", lambda: b"", 0)
        self.assertTrue(store.run("k", b"", lambda: b"wrong", 1).replayed)

    def test_bad_response_releases_key(self):
        store = IdempotencyStore()
        with self.assertRaises(TypeError): store.run("k", b"a", lambda: "text", 0)
        self.assertFalse(store.run("k", b"a", lambda: b"ok", 1).replayed)



if __name__ == '__main__':
    unittest.main()
