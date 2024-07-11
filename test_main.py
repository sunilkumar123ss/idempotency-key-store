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








if __name__ == '__main__':
    unittest.main()
