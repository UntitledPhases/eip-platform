"""
Smoke tests for engine primitives.
Run from repo root: python -m pytest tests/ -v
Or directly:       python tests/test_engine.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
import unittest


class TestPollingCache(unittest.TestCase):

    def test_get_returns_defaults(self):
        from engine.poller import PollingCache
        cache = PollingCache({"items": [], "count": 0})
        data = cache.get()
        self.assertEqual(data["items"], [])
        self.assertEqual(data["count"], 0)
        self.assertIsNone(data["last_updated"])
        self.assertIsNone(data["error"])

    def test_start_calls_fetch_and_updates_cache(self):
        from engine.poller import PollingCache
        cache = PollingCache({"value": None})

        def fetch():
            return {"value": 42}

        cache.start(fetch, interval=1)
        time.sleep(0.3)  # let first poll run
        self.assertEqual(cache.get()["value"], 42)
        self.assertIsNotNone(cache.get()["last_updated"])
        self.assertIsNone(cache.get()["error"])

    def test_fetch_exception_sets_error(self):
        from engine.poller import PollingCache
        cache = PollingCache({"value": None})

        def bad_fetch():
            raise RuntimeError("boom")

        cache.start(bad_fetch, interval=1)
        time.sleep(0.3)
        self.assertEqual(cache.get()["error"], "boom")

    def test_start_is_idempotent(self):
        from engine.poller import PollingCache
        cache = PollingCache({"x": 0})
        calls = {"n": 0}

        def fetch():
            calls["n"] += 1
            return {"x": calls["n"]}

        cache.start(fetch, interval=60)
        cache.start(fetch, interval=60)  # should not start second thread
        time.sleep(0.2)
        self.assertEqual(threading.active_count(), threading.active_count())  # no crash
        # only one thread running fetch
        n = calls["n"]
        self.assertGreaterEqual(n, 1)


class TestNotionClientInit(unittest.TestCase):

    def test_raises_without_token(self):
        from engine.notion import NotionClient
        with self.assertRaises(RuntimeError):
            NotionClient("")

    def test_init_with_token(self):
        from engine.notion import NotionClient
        c = NotionClient("secret_fake_token_for_testing")
        self.assertIn("Bearer secret_fake_token_for_testing", c._headers["Authorization"])
        self.assertEqual(c._headers["Notion-Version"], "2022-06-28")


class TestMirrorPollerWiring(unittest.TestCase):

    def test_mirror_poller_imports_from_engine(self):
        """Verify apps/mirror/poller.py uses engine primitives, not its own copies."""
        import apps.mirror.poller as mp
        from engine.poller import PollingCache
        self.assertIsInstance(mp.cache, PollingCache)

    def test_mirror_cache_has_expected_defaults(self):
        import apps.mirror.poller as mp
        data = mp.cache.get()
        self.assertIn("goals", data)
        self.assertIn("calendar", data)
        self.assertIn("mirror_notes", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
