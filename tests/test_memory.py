import tempfile
from pathlib import Path
import unittest
from memory import ShortTermMemory, LongTermMemory


class TestShortTermMemory(unittest.TestCase):

    def test_set_and_get(self):
        m = ShortTermMemory()
        m.set("key", "value")
        self.assertEqual(m.get("key"), "value")

    def test_get_default(self):
        m = ShortTermMemory()
        self.assertIsNone(m.get("missing"))
        self.assertEqual(m.get("missing", 42), 42)

    def test_eviction(self):
        m = ShortTermMemory(max_entries=3)
        for i in range(5):
            m.set(f"k{i}", i)
        self.assertFalse(m.has("k0"))
        self.assertFalse(m.has("k1"))
        self.assertTrue(m.has("k4"))

    def test_clear(self):
        m = ShortTermMemory()
        m.set("a", 1)
        m.clear()
        self.assertEqual(m.keys(), [])


class TestLongTermMemory(unittest.TestCase):

    def test_store_and_recall(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        m = LongTermMemory(store_path=path)
        m.store("test", {"value": 42}, tags=["tag1"])
        entries = m.recall("test")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["content"]["value"], 42)
        path.unlink()

    def test_search(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        m = LongTermMemory(store_path=path)
        m.store("report", {"client": "Alice"})
        m.store("report", {"client": "Bob"})
        results = m.search("Alice")
        self.assertEqual(len(results), 1)
        path.unlink()

    def test_persistence_across_instances(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        m1 = LongTermMemory(store_path=path)
        m1.store("x", "data1")

        m2 = LongTermMemory(store_path=path)
        self.assertEqual(m2.entry_count(), 1)
        path.unlink()


if __name__ == "__main__":
    unittest.main()
