from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from CDDA_editor.json_io import json_load_relaxed
from CDDA_editor.project import ModProject


class TestProjectObjectMoving(unittest.TestCase):
    def test_move_one_object_to_existing_file_marks_both_files_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "source.json"
            target_file = root / "target.json"
            source_file.write_text(
                """
                [
                  { "type": "mutation", "id": "MOVE_ALPHA" },
                  { "type": "mutation", "id": "MOVE_BETA" }
                ]
                """,
                encoding="utf-8",
            )
            target_file.write_text(
                '[{ "type": "mutation", "id": "MOVE_TARGET_EXISTING" }]',
                encoding="utf-8",
            )
            project = ModProject()
            project.load_from_dir(str(root))
            moved = project.get_object_by_type_id("mutation", "MOVE_ALPHA")
            self.assertIsNotNone(moved)

            moved_objects = project.move_objects_to_file([moved], target_file)

            self.assertEqual(moved_objects, [moved])
            self.assertEqual(moved.file_path, target_file)
            self.assertEqual(project.dirty_files, {source_file, target_file})
            self.assertIs(project.get_object_by_type_id("mutation", "MOVE_ALPHA"), moved)
            self.assertNotIn(moved, project.objects_for_file(source_file))
            self.assertIn(moved, project.objects_for_file(target_file))

            project.save_dirty_files()
            source_data = json_load_relaxed(source_file.read_text(encoding="utf-8"))
            target_data = json_load_relaxed(target_file.read_text(encoding="utf-8"))
            self.assertEqual([obj["id"] for obj in source_data], ["MOVE_BETA"])
            self.assertEqual(
                [obj["id"] for obj in target_data],
                ["MOVE_TARGET_EXISTING", "MOVE_ALPHA"],
            )

    def test_move_several_objects_to_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "source.json"
            target_file = root / "new" / "moved.json"
            source_file.write_text(
                """
                [
                  { "type": "mutation", "id": "MOVE_ONE" },
                  { "type": "mutation", "id": "MOVE_TWO" },
                  { "type": "mutation", "id": "MOVE_STAYS" }
                ]
                """,
                encoding="utf-8",
            )
            project = ModProject()
            project.load_from_dir(str(root))
            one = project.get_object_by_type_id("mutation", "MOVE_ONE")
            two = project.get_object_by_type_id("mutation", "MOVE_TWO")
            self.assertIsNotNone(one)
            self.assertIsNotNone(two)

            project.move_objects_to_file([one, two], target_file)

            self.assertEqual(one.file_path, target_file)
            self.assertEqual(two.file_path, target_file)
            self.assertEqual(project.dirty_files, {source_file, target_file})
            self.assertEqual(project.objects_for_file(target_file), [one, two])

            project.save_dirty_files()
            source_data = json_load_relaxed(source_file.read_text(encoding="utf-8"))
            target_data = json_load_relaxed(target_file.read_text(encoding="utf-8"))
            self.assertEqual([obj["id"] for obj in source_data], ["MOVE_STAYS"])
            self.assertEqual([obj["id"] for obj in target_data], ["MOVE_ONE", "MOVE_TWO"])


if __name__ == "__main__":
    unittest.main()
