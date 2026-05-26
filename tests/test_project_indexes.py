from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from CDDA_editor.project import ModProject


class TestProjectIndexes(unittest.TestCase):
    def test_indexes_objects_by_type_id_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mutations_file = root / "mutations.json"
            mutations_file.write_text(
                """
                [
                  { "type": "mutation", "id": "IDX_ALPHA" },
                  { "type": "mutation", "id": "IDX_BETA" }
                ]
                """,
                encoding="utf-8",
            )
            project = ModProject()

            project.load_from_dir(str(root))

            alpha = project.get_object_by_type_id("mutation", "IDX_ALPHA")
            self.assertIsNotNone(alpha)
            self.assertEqual(alpha.file_path, mutations_file)
            self.assertEqual(project.objects_for_file(mutations_file), [alpha, project.get_object_by_type_id("mutation", "IDX_BETA")])
            self.assertEqual(project.relative_object_file(alpha), Path("mutations.json"))

    def test_indexes_existing_ref_list_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                """
                [
                  { "type": "mutation", "id": "IDX_SOURCE", "prereqs": [ "IDX_TARGET" ] },
                  { "type": "mutation", "id": "IDX_TARGET" },
                  { "type": "mutation", "id": "IDX_UNUSED" }
                ]
                """,
                encoding="utf-8",
            )
            project = ModProject()

            project.load_from_dir(str(root))

            source = project.get_object_by_type_id("mutation", "IDX_SOURCE")
            target = project.get_object_by_type_id("mutation", "IDX_TARGET")
            self.assertIsNotNone(source)
            self.assertIsNotNone(target)

            outgoing = project.outgoing_references_for(source)
            incoming = project.incoming_references_for(target)

            self.assertEqual(len(outgoing), 1)
            self.assertEqual(outgoing[0].field_name, "prereqs")
            self.assertEqual(outgoing[0].target_type, "mutation")
            self.assertEqual(outgoing[0].target_id, "IDX_TARGET")
            self.assertIs(outgoing[0].target, target)
            self.assertEqual(incoming, outgoing)


if __name__ == "__main__":
    unittest.main()
