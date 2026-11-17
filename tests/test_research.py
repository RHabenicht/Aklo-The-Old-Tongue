import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from io import BytesIO
from aklo_reference.__main__ import data, analyze
from aklo_reference import research

class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.core = data()["entries"]
        self.off = {"encWords": {"soul": "another", "blood": "sample-blood"},
                    "encPhrases": {"red blood": "sample-phrase"},
                    "decWords": {"another": ["soul", "spirit"]},
                    "decPhrases": {}, "gloss": {}}
        self.rc = [{"source_base": "toolmaker", "rc": "example-compound", "strategy": "offline_semantic_compound"},
                   {"source_base": "new", "rc": "example-coinage", "strategy": "frequency_seed_coined"}]

    def cache(self, name, obj):
        (self.path / (name + ".json")).write_text(json.dumps({
            "revision": research.SOURCES[name]["revision"], "data": obj}), encoding="utf-8")

    def test_core_unchanged(self):
        self.cache("offerings", self.off)
        self.assertEqual(research.translation_entries(self.core, False, self.path), self.core)
        self.assertEqual(research.search(self.core, "soul", path=self.path)["matches"][0]["form"], "orr'e")

    def test_expanded_conflict_and_phrase(self):
        self.cache("offerings", self.off)
        rows = research.search(self.core, "soul", expanded=True, path=self.path)
        self.assertTrue(rows["ambiguous"])
        self.assertEqual({r["source"] for r in rows["matches"]}, {"jldevops", "offerings"})
        terms = research.translation_entries(self.core, True, self.path)
        self.assertEqual(analyze("soul", terms)["issues"][0]["type"], "ambiguous")
        self.assertEqual(analyze("red blood!", terms)["gloss"], "sample-phrase!")

    def test_reverse_apostrophe_and_multiple_senses(self):
        self.cache("offerings", self.off)
        self.assertTrue(research.search(self.core, "another", reverse=True, expanded=True, path=self.path)["ambiguous"])
        self.assertTrue(research.search(self.core, "orr’e", reverse=True)["matches"])

    def test_generated_opt_in_and_never_auto_translate(self):
        self.cache("rc1", self.rc)
        self.assertTrue(research.search(self.core, "toolmaker", expanded=True, path=self.path)["matches"])
        self.assertFalse(research.search(self.core, "new", expanded=True, path=self.path)["matches"])
        self.assertTrue(research.search(self.core, "new", expanded=True, include_generated=True, path=self.path)["matches"])
        self.assertNotIn("toolmaker", research.translation_entries(self.core, True, self.path))

    def test_parse_and_sync(self):
        raw = "const LEX = " + json.dumps(self.off) + ";"
        self.assertEqual(research.parse_source("offerings", raw), self.off)
        with patch("aklo_reference.research.urlopen", return_value=BytesIO(raw.encode())):
            self.assertEqual(research.sync(self.path, ["offerings"])["offerings"]["status"], "cached")
        self.assertEqual(research.load("offerings", self.path), self.off)
        with self.assertRaises(ValueError):
            research.parse_source("offerings", "alert('bad')")

    def test_missing_sources_and_stale_revision(self):
        self.assertIsNone(research.load("offerings", self.path))
        self.assertTrue(research.search(self.core, "water", expanded=True, path=self.path)["matches"])
        (self.path / "rc1.json").write_text('{"revision":"old","data":[]}')
        with self.assertRaises(ValueError):
            research.load("rc1", self.path)

if __name__ == "__main__":
    unittest.main()
