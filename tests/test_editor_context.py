from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from PyQt5.QtWidgets import QApplication
except ImportError:  # pragma: no cover - depends on local dev environment
    QApplication = None  # type: ignore[assignment]

from CDDA_editor.editor import ObjectEditorWidget
from CDDA_editor.project import ModProject


@unittest.skipIf(QApplication is None, "PyQt5 is not installed")
class TestObjectEditorContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_shows_selected_object_relative_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested_dir = root / "data"
            nested_dir.mkdir()
            object_file = nested_dir / "mutations.json"
            object_file.write_text(
                '[{ "type": "mutation", "id": "EDITOR_FILE_CONTEXT" }]',
                encoding="utf-8",
            )
            project = ModProject()
            project.load_from_dir(str(root))
            obj = project.get_object_by_type_id("mutation", "EDITOR_FILE_CONTEXT")
            self.assertIsNotNone(obj)
            editor = ObjectEditorWidget(project)

            editor.set_object(obj)

            self.assertIn("Файл:", editor.file_label.text())
            self.assertIn("data/mutations.json", editor.file_label.text().replace("\\", "/"))


if __name__ == "__main__":
    unittest.main()
