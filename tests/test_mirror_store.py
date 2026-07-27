"""Tests for Smart Mirror local JSON storage."""

import json
import importlib.util
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_store_module():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "apps", "mirror", "store.py")
    spec = importlib.util.spec_from_file_location("mirror_store", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMirrorStore(unittest.TestCase):

    def test_missing_file_returns_frontend_shape_with_error(self):
        store = load_store_module()

        data = store.load_data("/tmp/definitely-not-a-smart-mirror-file.json")

        self.assertEqual(data["goals"], [])
        self.assertEqual(data["calendar"], [])
        self.assertEqual(data["mirror_notes"], [])
        self.assertIsNotNone(data["error"])

    def test_normalizes_partial_data(self):
        store = load_store_module()

        data = store.normalize_data({
            "goals": [{"goal": "Move body", "priority": "P1"}],
            "calendar": [{"event": "Deep work", "when": {"start": "2026-07-16"}, "days": ["Thu"]}],
            "mirror_notes": ["Drink water"],
        })

        self.assertEqual(data["goals"][0]["horizon"], "Daily")
        self.assertEqual(data["goals"][0]["target"], {"start": None, "end": None})
        self.assertEqual(data["calendar"][0]["event"], "Deep work")
        self.assertEqual(data["calendar"][0]["when"], {"start": "2026-07-16", "end": None})
        self.assertEqual(data["mirror_notes"], ["Drink water"])
        self.assertIn("last_updated", data)
        self.assertIn("error", data)

    def test_load_data_uses_file_mtime_when_timestamp_missing(self):
        store = load_store_module()

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"goals": [], "calendar": [], "mirror_notes": []}, f)
            path = f.name

        try:
            data = store.load_data(path)
        finally:
            os.unlink(path)

        self.assertIsNotNone(data["last_updated"])
        self.assertIsNone(data["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
