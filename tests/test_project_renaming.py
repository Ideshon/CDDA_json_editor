from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from CDDA_editor.json_io import json_load_relaxed
from CDDA_editor.project import ModProject


class TestProjectObjectRenaming(unittest.TestCase):
    def test_rename_object_updates_id_index_and_dirty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "mutations.json"
            source_file.write_text(
                '[{ "type": "mutation", "id": "RENAME_OLD" }]',
                encoding="utf-8",
            )
            project = ModProject()
            project.load_from_dir(str(root))
            obj = project.get_object_by_type_id("mutation", "RENAME_OLD")
            self.assertIsNotNone(obj)

            project.rename_object(obj, "RENAME_NEW", update_references=False)

            self.assertEqual(obj.get_id(), "RENAME_NEW")
            self.assertIsNone(project.get_object_by_type_id("mutation", "RENAME_OLD"))
            self.assertIs(project.get_object_by_type_id("mutation", "RENAME_NEW"), obj)
            self.assertEqual(project.dirty_files, {source_file})

            project.save_dirty_files()
            saved = json_load_relaxed(source_file.read_text(encoding="utf-8"))
            self.assertEqual(saved[0]["id"], "RENAME_NEW")

    def test_rename_object_can_update_incoming_ref_list_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "mutations.json"
            source_file.write_text(
                """
                [
                  { "type": "mutation", "id": "SOURCE", "prereqs": [ "TARGET_OLD" ] },
                  { "type": "mutation", "id": "TARGET_OLD" }
                ]
                """,
                encoding="utf-8",
            )
            project = ModProject()
            project.load_from_dir(str(root))
            target = project.get_object_by_type_id("mutation", "TARGET_OLD")
            source = project.get_object_by_type_id("mutation", "SOURCE")
            self.assertIsNotNone(target)
            self.assertIsNotNone(source)

            result = project.rename_object(target, "TARGET_NEW", update_references=True)

            self.assertEqual(result.updated_references, 1)
            self.assertEqual(source.data["prereqs"], ["TARGET_NEW"])
            self.assertIs(project.get_object_by_type_id("mutation", "TARGET_NEW"), target)
            self.assertEqual(project.dirty_files, {source_file})
            incoming = project.incoming_references_for(target)
            self.assertEqual(len(incoming), 1)
            self.assertEqual(incoming[0].target_id, "TARGET_NEW")

    def test_rename_object_rejects_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                """
                [
                  { "type": "mutation", "id": "FIRST" },
                  { "type": "mutation", "id": "SECOND" }
                ]
                """,
                encoding="utf-8",
            )
            project = ModProject()
            project.load_from_dir(str(root))
            first = project.get_object_by_type_id("mutation", "FIRST")
            self.assertIsNotNone(first)

            with self.assertRaises(ValueError):
                project.rename_object(first, "SECOND", update_references=False)


if __name__ == "__main__":
    unittest.main()
