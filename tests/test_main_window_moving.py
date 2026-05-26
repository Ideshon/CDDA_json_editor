from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from PyQt5.QtWidgets import QApplication, QAbstractItemView
except ImportError:  # pragma: no cover - depends on local dev environment
    QApplication = None  # type: ignore[assignment]
    QAbstractItemView = None  # type: ignore[assignment]

from CDDA_editor.main import MainWindow


@unittest.skipIf(QApplication is None, "PyQt5 is not installed")
class TestMainWindowObjectMoving(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_tree_allows_extended_selection(self) -> None:
        window = MainWindow()

        self.assertEqual(window.tree.selectionMode(), QAbstractItemView.ExtendedSelection)

    def test_selected_objects_returns_multiple_selected_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                """
                [
                  { "type": "mutation", "id": "UI_MOVE_ONE" },
                  { "type": "mutation", "id": "UI_MOVE_TWO" }
                ]
                """,
                encoding="utf-8",
            )
            window = MainWindow()
            window.project.load_from_dir(str(root))
            window._rebuild_tree()
            category = window.tree.topLevelItem(0)
            first = category.child(0)
            second = category.child(1)

            first.setSelected(True)
            second.setSelected(True)

            selected = window._selected_objects()
            self.assertEqual([obj.get_id() for obj in selected], ["UI_MOVE_ONE", "UI_MOVE_TWO"])


if __name__ == "__main__":
    unittest.main()
