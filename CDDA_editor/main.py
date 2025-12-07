# main.py
from __future__ import annotations
from typing import Optional, List

from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from project import ModProject, ModObject
from editor import ObjectEditorWidget, json_dumps_pretty
from schemas import SCHEMAS


# --------- ТЁМНАЯ/СВЕТЛАЯ ТЕМЫ --------- #

def set_dark_palette(app: QApplication) -> None:
    """Включает тёмную тему на основе Fusion."""
    app.setStyle("Fusion")

    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)

    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)

    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(120, 120, 120))

    app.setPalette(palette)
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #353535;
            border: 1px solid #2a82da;
        }
    """)


def set_light_palette(app: QApplication, original: Optional[QPalette] = None) -> None:
    """Возвращаем светлую тему. Если есть оригинальная палитра – используем её."""
    app.setStyle("Fusion")
    if original is not None:
        app.setPalette(original)
    else:
        app.setPalette(app.style().standardPalette())
    app.setStyleSheet("")


# --------- ГЛАВНОЕ ОКНО --------- #

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CDDA 0.G JSON редактор модов")
        self.resize(1300, 800)

        self.project = ModProject()

        app = QApplication.instance()
        self._original_palette: Optional[QPalette] = app.palette() if app else None
        self.dark_enabled: bool = True
        if app:
            set_dark_palette(app)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Объекты")
        self.tree.currentItemChanged.connect(self._on_tree_selection_changed)

        self.editor = ObjectEditorWidget(self.project, self)

        splitter = QSplitter(self)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.editor)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._create_actions()

    def _create_actions(self) -> None:
        open_dir_act = QAction("Открыть папку мода", self)
        open_dir_act.triggered.connect(self._open_mod_folder)

        open_file_act = QAction("Открыть JSON-файл…", self)
        open_file_act.triggered.connect(self._open_mod_file)

        save_all_act = QAction("Сохранить все файлы", self)
        save_all_act.triggered.connect(self._save_all)

        save_dirty_act = QAction("Сохранить изменённые файлы", self)
        save_dirty_act.triggered.connect(self._save_dirty)

        save_current_act = QAction("Сохранить файл текущего объекта", self)
        save_current_act.triggered.connect(self._save_current_file)

        dark_theme_act = QAction("Темная тема", self)
        dark_theme_act.setCheckable(True)
        dark_theme_act.setChecked(True)
        dark_theme_act.triggered.connect(self._toggle_dark_theme)
        self._dark_theme_act = dark_theme_act

        # НОВОЕ: создание / удаление объектов
        add_obj_act = QAction("Добавить объект", self)
        add_obj_act.triggered.connect(self._add_object)

        del_obj_act = QAction("Удалить объект", self)
        del_obj_act.triggered.connect(self._delete_object)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction(open_dir_act)
        file_menu.addAction(open_file_act)
        file_menu.addSeparator()
        file_menu.addAction(save_all_act)
        file_menu.addAction(save_dirty_act)
        file_menu.addAction(save_current_act)

        view_menu = menubar.addMenu("Вид")
        view_menu.addAction(dark_theme_act)

        object_menu = menubar.addMenu("Объект")
        object_menu.addAction(add_obj_act)
        object_menu.addAction(del_obj_act)

        toolbar = self.addToolBar("Основное")
        toolbar.addAction(open_dir_act)
        toolbar.addAction(open_file_act)
        toolbar.addSeparator()
        toolbar.addAction(save_all_act)
        toolbar.addAction(save_dirty_act)
        toolbar.addAction(save_current_act)
        toolbar.addSeparator()
        toolbar.addAction(add_obj_act)
        toolbar.addAction(del_obj_act)
        toolbar.addSeparator()
        toolbar.addAction(dark_theme_act)

    # ---------- тёмная тема ----------

    def _toggle_dark_theme(self, checked: bool) -> None:
        app = QApplication.instance()
        if not app:
            return
        if checked:
            set_dark_palette(app)
            self.dark_enabled = True
        else:
            set_light_palette(app, self._original_palette)
            self.dark_enabled = False

    # ---------- загрузка ----------

    def _warn_discard_changes(self) -> bool:
        if not self.project.dirty_files:
            return True
        reply = QMessageBox.question(
            self,
            "Есть несохранённые изменения",
            "Есть изменённые файлы. Загрузить другой мод/файл?\n"
            "Несохранённые изменения будут потеряны.",
            QMessageBox.Yes | QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _open_mod_folder(self) -> None:
        if not self._warn_discard_changes():
            return

        path = QFileDialog.getExistingDirectory(self, "Выберите папку мода")
        if not path:
            return
        try:
            self.project.load_from_dir(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить мод:\n{e}")
            return
        self._rebuild_tree()
        self.statusBar().showMessage(f"Загружен мод из {path}", 5000)

    def _open_mod_file(self) -> None:
        if not self._warn_discard_changes():
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите JSON-файл мода",
            "",
            "JSON файлы (*.json);;Все файлы (*.*)",
        )
        if not path:
            return
        try:
            self.project.load_from_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{e}")
            return
        self._rebuild_tree()
        self.statusBar().showMessage(f"Загружен файл {path}", 5000)

    # ---------- дерево ----------

    def _rebuild_tree(self) -> None:
        self.tree.clear()

        for schema_key, schema in SCHEMAS.items():
            objs = self.project.objects_by_schema.get(schema_key)
            if not objs:
                continue
            root = QTreeWidgetItem([schema.get("label", schema_key)])
            # в корне теперь храним schema_key, чтобы знать категорию
            root.setData(0, Qt.UserRole, schema_key)
            self.tree.addTopLevelItem(root)
            for obj in objs:
                item = QTreeWidgetItem([obj.label()])
                item.setData(0, Qt.UserRole, obj)
                root.addChild(item)
            root.setExpanded(True)

    def _on_tree_selection_changed(
        self,
        current: Optional[QTreeWidgetItem],
        _prev: Optional[QTreeWidgetItem],
    ) -> None:
        if current is None:
            self.editor.set_object(None)
            return
        data = current.data(0, Qt.UserRole)
        if isinstance(data, ModObject):
            self.editor.set_object(data)
        else:
            self.editor.set_object(None)

    def _current_schema_key(self) -> Optional[str]:
        """
        Понять, в какой категории мы сейчас: по выбранному объекту или корневому узлу.
        """
        item = self.tree.currentItem()
        if not item:
            return None
        data = item.data(0, Qt.UserRole)
        if isinstance(data, ModObject):
            return data.schema_key
        if isinstance(data, str):
            return data
        return None

    def _select_object_in_tree(self, target: ModObject) -> None:
        """
        Находит в дереве item, который хранит этот ModObject, и выделяет его.
        """
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            for j in range(root.childCount()):
                item = root.child(j)
                obj = item.data(0, Qt.UserRole)
                if obj is target:
                    self.tree.setCurrentItem(item)
                    return

    # ---------- создание / удаление объектов ----------

    def _add_object(self) -> None:
        schema_key = self._current_schema_key()
        if schema_key is None:
            QMessageBox.information(
                self,
                "Добавление объекта",
                "Выбери категорию или существующий объект, чтобы понять, куда добавлять новый.",
            )
            return
        try:
            new_obj = self.project.create_object(schema_key)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать объект:\n{e}")
            return

        self._rebuild_tree()
        self._select_object_in_tree(new_obj)
        self.editor.set_object(new_obj)
        self.statusBar().showMessage(
            f"Создан новый объект в editor_{schema_key}.json", 5000
        )

    def _delete_object(self) -> None:
        item = self.tree.currentItem()
        if not item:
            QMessageBox.information(self, "Удаление объекта", "Сначала выбери объект в списке.")
            return
        data = item.data(0, Qt.UserRole)
        if not isinstance(data, ModObject):
            QMessageBox.information(self, "Удаление объекта", "Нужно выбрать конкретный объект, а не категорию.")
            return

        obj: ModObject = data
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить объект {obj.label()} из файла {obj.file_path.name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.project.delete_object(obj)
        self.editor.set_object(None)
        self._rebuild_tree()
        self.statusBar().showMessage("Объект удалён", 5000)

    # ---------- сохранение ----------

    def _write_file(self, path: Path) -> Optional[str]:
        objs = self.project.files.get(path)
        if objs is None:
            return f"{path}: файл не найден в проекте"
        try:
            with path.open("w", encoding="utf-8") as f:
                f.write(json_dumps_pretty(objs))
                f.write("\n")
            return None
        except Exception as e:
            return f"{path}: {e}"

    def _save_all(self) -> None:
        self.editor.apply_changes()

        errors: List[str] = []
        written: set[Path] = set()
        for path in self.project.files.keys():
            err = self._write_file(path)
            if err:
                errors.append(err)
            else:
                written.add(path)

        self.project.dirty_files -= written

        if errors:
            QMessageBox.critical(
                self,
                "Ошибки при сохранении",
                "Не удалось сохранить некоторые файлы:\n\n" + "\n".join(errors),
            )
        else:
            QMessageBox.information(self, "Готово", "Все файлы сохранены.")

    def _save_dirty(self) -> None:
        self.editor.apply_changes()

        if not self.project.dirty_files:
            QMessageBox.information(self, "Сохранение", "Нет изменённых файлов.")
            return

        errors: List[str] = []
        written: set[Path] = set()
        for path in sorted(self.project.dirty_files):
            err = self._write_file(path)
            if err:
                errors.append(err)
            else:
                written.add(path)

        self.project.dirty_files -= written

        if errors:
            QMessageBox.critical(
                self,
                "Ошибки при сохранении",
                "Не удалось сохранить некоторые файлы:\n\n" + "\n".join(errors),
            )
        else:
            QMessageBox.information(self, "Готово", "Все изменённые файлы сохранены.")

    def _save_current_file(self) -> None:
        self.editor.apply_changes()

        item = self.tree.currentItem()
        if not item:
            QMessageBox.information(self, "Сохранение", "Не выбран объект.")
            return
        obj = item.data(0, Qt.UserRole)
        if not isinstance(obj, ModObject):
            QMessageBox.information(self, "Сохранение", "Нужно выбрать конкретный объект, а не категорию.")
            return

        path = obj.file_path
        err = self._write_file(path)
        if err:
            QMessageBox.critical(self, "Ошибка сохранения", err)
        else:
            if path in self.project.dirty_files:
                self.project.dirty_files.remove(path)
            QMessageBox.information(self, "Готово", f"Файл {path} сохранён.")


def main() -> None:
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
