from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "CDDA_editor"
sys.path.insert(0, str(APP_DIR))

from project import ModProject, json_load_relaxed  # noqa: E402


class TestRelaxedJsonLoading(unittest.TestCase):
    def test_supports_cdda_line_and_block_comments_without_touching_strings(self) -> None:
        raw = """
        [
          // CDDA allows line comments in JSON files.
          {
            "type": "mutation",
            "id": "COMMENT_TEST",
            "description": "http://example.test/path//kept"
          },
          /* Block comments are common in draft data. */
          {
            "type": "mutation",
            "id": "BLOCK_COMMENT_TEST"
          }
        ]
        """

        data = json_load_relaxed(raw)

        self.assertEqual(data[0]["id"], "COMMENT_TEST")
        self.assertEqual(data[0]["description"], "http://example.test/path//kept")
        self.assertEqual(data[1]["id"], "BLOCK_COMMENT_TEST")

    def test_supports_top_level_object_stream_used_by_some_draft_files(self) -> None:
        raw = """
        {
          "type": "mutation",
          "id": "FIRST"
        },
        {
          "type": "mutation",
          "id": "SECOND"
        }
        """

        data = json_load_relaxed(raw)

        self.assertEqual([item["id"] for item in data], ["FIRST", "SECOND"])


class TestReferenceModLoading(unittest.TestCase):
    def test_slaanesh_reference_mod_loads_without_parse_warnings(self) -> None:
        project = ModProject()
        output = io.StringIO()

        with redirect_stdout(output):
            project.load_from_dir(str(ROOT / "Slaanesh"))

        self.assertNotIn("[WARN]", output.getvalue())
        expected_json_files = len(list((ROOT / "Slaanesh").rglob("*.json")))
        self.assertEqual(len(project.files), expected_json_files)
        self.assertIn("mutation", project.objects_by_schema)
        self.assertIn("npc", project.objects_by_schema)
        self.assertEqual(project.dirty_files, set())


if __name__ == "__main__":
    unittest.main()
