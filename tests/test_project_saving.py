from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from CDDA_editor.json_io import json_load_relaxed
from CDDA_editor.project import ModObject, ModProject


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_MOD = ROOT / "Slaanesh"


def copy_reference_mod(tmp_path: Path) -> Path:
    mod_copy = tmp_path / "Slaanesh"
    shutil.copytree(REFERENCE_MOD, mod_copy)
    return mod_copy


def snapshot_json_files(root: Path) -> dict[Path, bytes]:
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*.json")}


class TestProjectSavingWithReferenceCopy(unittest.TestCase):
    def test_create_object_and_save_dirty_writes_only_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mod_copy = copy_reference_mod(Path(tmp))
            before = snapshot_json_files(mod_copy)
            project = ModProject()
            project.load_from_dir(str(mod_copy))

            new_obj = project.create_object("mutation")
            new_obj.data["id"] = "EDITOR_TEST_MUTATION"

            expected_path = mod_copy / "editor_mutation.json"
            self.assertEqual(project.dirty_files, {expected_path})

            written = project.save_dirty_files()

            self.assertEqual(written, [expected_path])
            self.assertEqual(project.dirty_files, set())
            self.assertTrue(expected_path.exists())
            saved_data = json_load_relaxed(expected_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_data[-1]["id"], "EDITOR_TEST_MUTATION")
            for rel_path, original_bytes in before.items():
                self.assertEqual((mod_copy / rel_path).read_bytes(), original_bytes)

    def test_delete_object_and_save_dirty_changes_only_owning_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mod_copy = copy_reference_mod(Path(tmp))
            before = snapshot_json_files(mod_copy)
            project = ModProject()
            project.load_from_dir(str(mod_copy))
            target = self._first_object_with_id(project, "mutation")
            target_id = target.get_id()
            target_rel_path = target.file_path.relative_to(mod_copy)

            project.delete_object(target)

            self.assertEqual(project.dirty_files, {target.file_path})

            written = project.save_dirty_files()

            self.assertEqual(written, [target.file_path])
            self.assertEqual(project.dirty_files, set())
            saved_data = json_load_relaxed(target.file_path.read_text(encoding="utf-8"))
            saved_ids = [obj.get("id") for obj in saved_data if isinstance(obj, dict)]
            self.assertNotIn(target_id, saved_ids)
            for rel_path, original_bytes in before.items():
                if rel_path == target_rel_path:
                    continue
                self.assertEqual((mod_copy / rel_path).read_bytes(), original_bytes)

    def test_save_file_clears_only_that_dirty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mod_copy = copy_reference_mod(Path(tmp))
            project = ModProject()
            project.load_from_dir(str(mod_copy))
            mutation = project.create_object("mutation")
            effect = project.create_object("effect_type")
            mutation.data["id"] = "EDITOR_SINGLE_SAVE_MUTATION"
            effect.data["id"] = "EDITOR_SINGLE_SAVE_EFFECT"

            self.assertEqual(
                project.dirty_files,
                {mutation.file_path, effect.file_path},
            )

            written = project.save_file(mutation.file_path)

            self.assertEqual(written, mutation.file_path)
            self.assertEqual(project.dirty_files, {effect.file_path})
            self.assertTrue(mutation.file_path.exists())
            self.assertFalse(effect.file_path.exists())

    def _first_object_with_id(self, project: ModProject, schema_key: str) -> ModObject:
        for obj in project.objects_by_schema[schema_key]:
            if obj.get_id():
                return obj
        raise AssertionError(f"No object with id found for schema {schema_key}")


if __name__ == "__main__":
    unittest.main()
