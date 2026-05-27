from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from CDDA_editor.action_history import ProjectActionHistory
from CDDA_editor.project import ModProject


class TestProjectActionHistory(unittest.TestCase):
    def test_undo_and_redo_restore_files_indexes_and_dirty_state(self) -> None:
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
            history = ProjectActionHistory(project)
            target = project.get_object_by_type_id("mutation", "TARGET_OLD")
            self.assertIsNotNone(target)

            before = history.capture()
            project.rename_object(target, "TARGET_NEW", update_references=True)
            recorded = history.record("rename object", before)

            self.assertTrue(recorded)
            self.assertTrue(history.can_undo)
            self.assertFalse(history.can_redo)
            self.assertIsNotNone(project.get_object_by_type_id("mutation", "TARGET_NEW"))
            self.assertEqual(project.dirty_files, {source_file})

            undone = history.undo()

            self.assertEqual(undone.label, "rename object")
            restored_source = project.get_object_by_type_id("mutation", "SOURCE")
            restored_target = project.get_object_by_type_id("mutation", "TARGET_OLD")
            self.assertIsNotNone(restored_source)
            self.assertIsNotNone(restored_target)
            self.assertEqual(restored_source.data["prereqs"], ["TARGET_OLD"])
            self.assertIsNone(project.get_object_by_type_id("mutation", "TARGET_NEW"))
            self.assertEqual(project.dirty_files, set())
            self.assertFalse(history.can_undo)
            self.assertTrue(history.can_redo)

            redone = history.redo()

            self.assertEqual(redone.label, "rename object")
            redone_source = project.get_object_by_type_id("mutation", "SOURCE")
            redone_target = project.get_object_by_type_id("mutation", "TARGET_NEW")
            self.assertIsNotNone(redone_source)
            self.assertIsNotNone(redone_target)
            self.assertEqual(redone_source.data["prereqs"], ["TARGET_NEW"])
            self.assertIsNone(project.get_object_by_type_id("mutation", "TARGET_OLD"))
            self.assertEqual(project.dirty_files, {source_file})

    def test_noop_record_does_not_create_undo_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                '[{ "type": "mutation", "id": "NOOP" }]',
                encoding="utf-8",
            )
            project = ModProject()
            project.load_from_dir(str(root))
            history = ProjectActionHistory(project)

            before = history.capture()
            recorded = history.record("noop", before)

            self.assertFalse(recorded)
            self.assertFalse(history.can_undo)
            self.assertFalse(history.can_redo)


if __name__ == "__main__":
    unittest.main()
