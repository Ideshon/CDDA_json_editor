from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from CDDA_editor.project import ModProject


def write_mutation_file(path: Path, obj_id: str) -> None:
    path.write_text(
        f'[{{ "type": "mutation", "id": "{obj_id}" }}]\n',
        encoding="utf-8",
    )


class TestProjectBackups(unittest.TestCase):
    def test_create_open_backup_for_mod_directory_copies_files_outside_mod(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            write_mutation_file(root / "mutations.json", "BACKUP_ORIGINAL")

            project = ModProject()
            backup = project.create_open_backup(root)

            self.assertEqual(backup.source_path, root)
            self.assertEqual(backup.kind, "directory")
            self.assertEqual(project.current_backup, backup)
            self.assertTrue(backup.backup_path.is_dir())
            self.assertFalse(backup.backup_path.is_relative_to(root))
            self.assertEqual(
                (backup.backup_path / "mutations.json").read_text(encoding="utf-8"),
                (root / "mutations.json").read_text(encoding="utf-8"),
            )

    def test_restore_current_directory_backup_replaces_current_files_and_reloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            source_file = root / "mutations.json"
            write_mutation_file(source_file, "BACKUP_ORIGINAL")

            project = ModProject()
            project.create_open_backup(root)
            write_mutation_file(source_file, "BROKEN_EDIT")
            write_mutation_file(root / "new_file.json", "SHOULD_BE_REMOVED")

            restored = project.restore_current_backup()

            self.assertEqual(restored.source_path, root)
            self.assertIn("BACKUP_ORIGINAL", source_file.read_text(encoding="utf-8"))
            self.assertFalse((root / "new_file.json").exists())
            self.assertIsNotNone(project.get_object_by_type_id("mutation", "BACKUP_ORIGINAL"))
            self.assertIsNone(project.get_object_by_type_id("mutation", "BROKEN_EDIT"))
            self.assertEqual(project.dirty_files, set())

    def test_single_json_file_backup_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "single.json"
            write_mutation_file(source_file, "SINGLE_ORIGINAL")

            project = ModProject()
            backup = project.create_open_backup(source_file)
            write_mutation_file(source_file, "SINGLE_BROKEN")

            restored = project.restore_current_backup()

            self.assertEqual(backup.kind, "file")
            self.assertEqual(restored.source_path, source_file)
            self.assertIn("SINGLE_ORIGINAL", source_file.read_text(encoding="utf-8"))
            self.assertIsNotNone(project.get_object_by_type_id("mutation", "SINGLE_ORIGINAL"))
            self.assertIsNone(project.get_object_by_type_id("mutation", "SINGLE_BROKEN"))
            self.assertEqual(project.dirty_files, set())

    def test_autobackup_writes_unsaved_project_data_without_touching_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            source_file = root / "mutations.json"
            write_mutation_file(source_file, "AUTOBACKUP_ORIGINAL")

            project = ModProject()
            backup = project.create_open_backup(root)
            project.load_from_dir(str(root))
            project.current_backup = backup
            target = project.get_object_by_type_id("mutation", "AUTOBACKUP_ORIGINAL")
            self.assertIsNotNone(target)
            target.data["id"] = "AUTOBACKUP_DIRTY"
            project.mark_dirty(target.file_path)

            autobackup = project.create_autobackup()

            self.assertEqual(project.current_backup, autobackup)
            self.assertEqual(autobackup.kind, "directory")
            self.assertIn("AUTOBACKUP_ORIGINAL", source_file.read_text(encoding="utf-8"))
            saved_backup = (autobackup.backup_path / "mutations.json").read_text(
                encoding="utf-8"
            )
            self.assertIn("AUTOBACKUP_DIRTY", saved_backup)
            self.assertEqual(project.dirty_files, {source_file})


if __name__ == "__main__":
    unittest.main()
