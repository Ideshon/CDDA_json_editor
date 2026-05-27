# main.py
from __future__ import annotations
import logging
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QAbstractItemView,
    QInputDialog,
)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QPalette, QColor

try:
    from .app_logging import configure_app_logging
    from .app_paths import app_base_dir as get_app_base_dir, default_settings_path
    from .action_history import ProjectActionHistory
    from .project import ModProject, ModObject
    from .editor import ObjectEditorWidget
    from .relationships import ObjectRelationshipsWindow
    from .schemas import SCHEMAS
except ImportError:
    from app_logging import configure_app_logging
    from app_paths import app_base_dir as get_app_base_dir, default_settings_path
    from action_history import ProjectActionHistory
    from project import ModProject, ModObject
    from editor import ObjectEditorWidget
    from relationships import ObjectRelationshipsWindow
    from schemas import SCHEMAS


logger = logging.getLogger("CDDA_editor.main")


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
    def __init__(
        self,
        settings_path: Optional[Path] = None,
        app_base_dir: Optional[Path] = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("CDDA 0.G JSON редактор")
        self.resize(1300, 800)
        self.app_base_dir = Path(app_base_dir) if app_base_dir is not None else get_app_base_dir()
        self.settings = self._create_settings(settings_path)

        self.project = ModProject()
        self.action_history = ProjectActionHistory(self.project)
        self._relationships_window: Optional[ObjectRelationshipsWindow] = None
        self.autobackup_enabled = True
        self.autobackup_interval_minutes = 5
        self.autobackup_timer = QTimer(self)
        self.autobackup_timer.timeout.connect(self._run_autobackup)

        app = QApplication.instance()
        self._original_palette: Optional[QPalette] = app.palette() if app else None
        self.dark_enabled: bool = True
        if app:
            set_dark_palette(app)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Объекты")
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.currentItemChanged.connect(self._on_tree_selection_changed)

        self.editor = ObjectEditorWidget(self.project, self)
        self.editor.change_recorder = self._record_editor_change

        splitter = QSplitter(self)
        splitter.setObjectName("main_splitter")
        splitter.addWidget(self.tree)
        splitter.addWidget(self.editor)
        splitter.setStretchFactor(1, 1)
        self.main_splitter = splitter
        self.setCentralWidget(splitter)

        self._create_actions()
        self._restore_window_state()

    def _create_settings(self, settings_path: Optional[Path]) -> QSettings:
        resolved_settings_path = (
            Path(settings_path)
            if settings_path is not None
            else default_settings_path(self.app_base_dir)
        )
        resolved_settings_path.parent.mkdir(parents=True, exist_ok=True)
        return QSettings(str(resolved_settings_path), QSettings.IniFormat)

    def _create_actions(self) -> None:
        open_dir_act = QAction("Открыть папку", self)
        open_dir_act.triggered.connect(self._open_mod_folder)

        open_file_act = QAction("Открыть JSON", self)
        open_file_act.triggered.connect(self._open_mod_file)

        restore_backup_act = QAction("Восстановить бэкап...", self)
        restore_backup_act.triggered.connect(self._restore_latest_backup)

        autobackup_act = QAction("Автобэкап", self)
        autobackup_act.setCheckable(True)
        autobackup_act.setChecked(self.autobackup_enabled)
        autobackup_act.triggered.connect(self._toggle_autobackup)
        self._autobackup_act = autobackup_act

        autobackup_interval_act = QAction("Интервал автобэкапа...", self)
        autobackup_interval_act.triggered.connect(self._change_autobackup_interval)

        save_all_act = QAction("Сохранить все", self)
        save_all_act.triggered.connect(self._save_all)

        save_dirty_act = QAction("Сохранить изменённые", self)
        save_dirty_act.triggered.connect(self._save_dirty)

        save_current_act = QAction("Сохранить файл объекта", self)
        save_current_act.triggered.connect(self._save_current_file)

        undo_act = QAction("\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", self)
        undo_act.setShortcut("Ctrl+Z")
        undo_act.triggered.connect(self._undo_project_action)
        self._undo_action = undo_act

        redo_act = QAction("\u041f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u044c", self)
        redo_act.setShortcut("Ctrl+Y")
        redo_act.triggered.connect(self._redo_project_action)
        self._redo_action = redo_act

        dark_theme_act = QAction("Темная", self)
        dark_theme_act.setCheckable(True)
        dark_theme_act.setChecked(True)
        dark_theme_act.triggered.connect(self._toggle_dark_theme)
        self._dark_theme_act = dark_theme_act

        # НОВОЕ: создание / удаление объектов
        add_obj_act = QAction("Добавить объект", self)
        add_obj_act.triggered.connect(self._add_object)

        del_obj_act = QAction("Удалить объект", self)
        del_obj_act.triggered.connect(self._delete_object)

        move_obj_act = QAction("Переместить в файл...", self)
        move_obj_act.triggered.connect(self._move_selected_objects)

        rename_obj_act = QAction("Переименовать объект...", self)
        rename_obj_act.triggered.connect(self._rename_selected_object)

        relationships_act = QAction("Связи объекта...", self)
        relationships_act.triggered.connect(self._open_relationships_window)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction(open_dir_act)
        file_menu.addAction(open_file_act)
        file_menu.addAction(restore_backup_act)
        file_menu.addAction(autobackup_act)
        file_menu.addAction(autobackup_interval_act)
        file_menu.addSeparator()
        file_menu.addAction(save_all_act)
        file_menu.addAction(save_dirty_act)
        file_menu.addAction(save_current_act)

        view_menu = menubar.addMenu("Вид")
        view_menu.addAction(dark_theme_act)

        edit_menu = menubar.addMenu("\u041f\u0440\u0430\u0432\u043a\u0430")
        edit_menu.addAction(undo_act)
        edit_menu.addAction(redo_act)

        object_menu = menubar.addMenu("Объект")
        object_menu.addAction(add_obj_act)
        object_menu.addAction(del_obj_act)
        object_menu.addAction(move_obj_act)
        object_menu.addAction(rename_obj_act)
        object_menu.addAction(relationships_act)

        toolbar = self.addToolBar("Файл")
        toolbar.setObjectName("toolbar_file")
        toolbar.addAction(open_dir_act)
        toolbar.addAction(open_file_act)
        toolbar.addAction(restore_backup_act)
        toolbar.addAction(autobackup_act)
        toolbar.addSeparator()
        toolbar.addAction(save_all_act)
        toolbar.addAction(save_dirty_act)
        toolbar.addAction(save_current_act)

        toolbar = self.addToolBar("\u041f\u0440\u0430\u0432\u043a\u0430")
        toolbar.setObjectName("toolbar_edit")
        toolbar.addAction(undo_act)
        toolbar.addAction(redo_act)

        toolbar = self.addToolBar("Объект")
        toolbar.setObjectName("toolbar_object")
        toolbar.addAction(add_obj_act)
        toolbar.addAction(del_obj_act)
        toolbar.addAction(move_obj_act)
        toolbar.addAction(rename_obj_act)
        toolbar.addAction(relationships_act)

        toolbar = self.addToolBar("Вид")
        toolbar.setObjectName("toolbar_view")
        toolbar.addAction(dark_theme_act)

        self._refresh_undo_redo_actions()

    def _record_editor_change(self, label: str, change: Callable[[], bool]) -> bool:
        before = self.action_history.capture()
        changed = change()
        if changed:
            self._record_project_action(label, before)
        return changed

    def _record_project_action(self, label: str, before) -> bool:  # type: ignore[no-untyped-def]
        recorded = self.action_history.record(label, before)
        self._refresh_undo_redo_actions()
        if recorded:
            logger.info("Recorded project action: %s", label)
        return recorded

    def _refresh_undo_redo_actions(self) -> None:
        if hasattr(self, "_undo_action"):
            self._undo_action.setEnabled(self.action_history.can_undo)
        if hasattr(self, "_redo_action"):
            self._redo_action.setEnabled(self.action_history.can_redo)

    def _undo_project_action(self) -> None:
        if not self.action_history.can_undo:
            return
        self.editor.clear_selection_without_applying()
        action = self.action_history.undo()
        self._rebuild_tree()
        self._refresh_undo_redo_actions()
        logger.info("Undid project action: %s", action.label)
        self.statusBar().showMessage(f"\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e: {action.label}", 5000)

    def _redo_project_action(self) -> None:
        if not self.action_history.can_redo:
            return
        self.editor.clear_selection_without_applying()
        action = self.action_history.redo()
        self._rebuild_tree()
        self._refresh_undo_redo_actions()
        logger.info("Redid project action: %s", action.label)
        self.statusBar().showMessage(f"\u041f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u043e: {action.label}", 5000)

    def _save_window_state(self) -> None:
        if self._relationships_window is not None:
            self._relationships_window._save_window_state()
        self.settings.setValue("window/width", self.size().width())
        self.settings.setValue("window/height", self.size().height())
        self.settings.setValue("window/state", self.saveState())
        self.settings.setValue(
            "window/splitter_sizes",
            ",".join(str(size) for size in self.main_splitter.sizes()),
        )
        self.settings.sync()
        logger.info("Window state saved")

    def _restore_window_state(self) -> None:
        width = self._settings_int("window/width")
        height = self._settings_int("window/height")
        if width and height:
            self.resize(width, height)

        state = self.settings.value("window/state")
        if state:
            self.restoreState(state)

        splitter_sizes = self._settings_int_list("window/splitter_sizes")
        if splitter_sizes:
            self.main_splitter.setSizes(splitter_sizes)

    def _settings_int(self, key: str) -> int:
        value = self.settings.value(key, 0)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _settings_int_list(self, key: str) -> list[int]:
        value = self.settings.value(key, "")
        if not value:
            return []
        if isinstance(value, (list, tuple)):
            raw_items = value
        else:
            raw_items = str(value).split(",")
        result: list[int] = []
        for item in raw_items:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                return []
        return result

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._save_window_state()
        super().closeEvent(event)

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
        self._load_mod_folder_from_path(path)

    def _load_mod_folder_from_path(self, path: str) -> bool:
        try:
            backup = self.project.create_open_backup(Path(path))
            logger.info("Created open backup for mod folder %s at %s", path, backup.backup_path)
            self.project.load_from_dir(path)
            self.project.current_backup = backup
        except Exception as e:
            logger.exception("Failed to load mod folder %s", path)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить мод:\n{e}")
            return False
        self.action_history.clear()
        self._refresh_undo_redo_actions()
        self._rebuild_tree()
        self._restart_autobackup_timer()
        self._show_load_warnings_if_any()
        self._show_load_status(f"Загружен мод из {path}")
        logger.info("Loaded mod folder %s", path)
        return True

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
        self._load_mod_file_from_path(path)

    def _load_mod_file_from_path(self, path: str) -> bool:
        try:
            backup = self.project.create_open_backup(Path(path))
            logger.info("Created open backup for JSON file %s at %s", path, backup.backup_path)
            self.project.load_from_file(path)
            self.project.current_backup = backup
        except Exception as e:
            logger.exception("Failed to load JSON file %s", path)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{e}")
            return False
        self.action_history.clear()
        self._refresh_undo_redo_actions()
        self._rebuild_tree()
        self._restart_autobackup_timer()
        self._show_load_warnings_if_any()
        self._show_load_status(f"Загружен файл {path}")
        logger.info("Loaded JSON file %s", path)
        return True

    def _toggle_autobackup(self, checked: bool) -> None:
        self.autobackup_enabled = checked
        if hasattr(self, "_autobackup_act"):
            self._autobackup_act.setChecked(checked)
        self._restart_autobackup_timer()
        if checked:
            self.statusBar().showMessage("Автобэкап включён", 5000)
        else:
            self.statusBar().showMessage("Автобэкап отключён", 5000)

    def _change_autobackup_interval(self) -> None:
        minutes, ok = QInputDialog.getInt(
            self,
            "Интервал автобэкапа",
            "Минуты:",
            self.autobackup_interval_minutes,
            1,
            240,
            1,
        )
        if not ok:
            return
        self._set_autobackup_interval_minutes(minutes)

    def _set_autobackup_interval_minutes(self, minutes: int) -> None:
        self.autobackup_interval_minutes = max(1, int(minutes))
        self._restart_autobackup_timer()
        self.statusBar().showMessage(
            f"Интервал автобэкапа: {self.autobackup_interval_minutes} мин.",
            5000,
        )

    def _restart_autobackup_timer(self) -> None:
        self.autobackup_timer.stop()
        if not self.autobackup_enabled:
            return
        if self.project.current_backup is None:
            return
        self.autobackup_timer.start(self.autobackup_interval_minutes * 60 * 1000)

    def _run_autobackup(self) -> None:
        if not self.autobackup_enabled or self.project.current_backup is None:
            return
        self.editor.apply_changes()
        try:
            backup = self.project.create_autobackup()
        except Exception as e:
            logger.exception("Autobackup failed")
            QMessageBox.warning(self, "Ошибка автобэкапа", str(e))
            return
        logger.info("Created autobackup at %s", backup.backup_path)
        self.statusBar().showMessage(f"Создан автобэкап {backup.backup_path}", 5000)

    def _restore_latest_backup(self) -> None:
        backup = self.project.current_backup
        if backup is None:
            QMessageBox.information(self, "Восстановление бэкапа", "Нет текущего бэкапа.")
            return

        reply = QMessageBox.question(
            self,
            "Восстановление бэкапа",
            "Восстановить последний бэкап?\n\n"
            f"Источник:\n{backup.source_path}\n\n"
            f"Бэкап:\n{backup.backup_path}\n\n"
            "Текущие файлы будут заменены.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.editor.clear_selection_without_applying()
            restored = self.project.restore_current_backup()
        except Exception as e:
            logger.exception("Backup restore failed")
            QMessageBox.critical(self, "Ошибка восстановления", str(e))
            return

        self.action_history.clear()
        self._refresh_undo_redo_actions()
        self._rebuild_tree()
        self._show_load_warnings_if_any()
        logger.info("Restored backup from %s", restored.backup_path)
        self.statusBar().showMessage(f"Восстановлен бэкап {restored.backup_path}", 5000)

    def _show_load_warnings_if_any(self) -> None:
        summary = self.project.load_warning_summary()
        if not summary:
            return

        QMessageBox.warning(
            self,
            "Предупреждения загрузки",
            summary,
        )

    def _show_load_status(self, message: str) -> None:
        if self.project.load_warnings:
            message = f"{message}; предупреждений: {len(self.project.load_warnings)}"
        self.statusBar().showMessage(message, 5000)

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
            self._sync_relationships_window_with_selection(None)
            return
        data = current.data(0, Qt.UserRole)
        if isinstance(data, ModObject):
            self.editor.set_object(data)
            self._sync_relationships_window_with_selection(data)
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

    def _selected_objects(self) -> list[ModObject]:
        selected: list[ModObject] = []
        seen: set[int] = set()

        for item in self.tree.selectedItems():
            data = item.data(0, Qt.UserRole)
            if not isinstance(data, ModObject):
                continue
            marker = id(data)
            if marker in seen:
                continue
            seen.add(marker)
            selected.append(data)

        if selected:
            return selected

        item = self.tree.currentItem()
        if item is None:
            return []
        data = item.data(0, Qt.UserRole)
        if isinstance(data, ModObject):
            return [data]
        return []

    def _open_relationships_window(self) -> None:
        objects = self._selected_objects()
        if len(objects) != 1:
            QMessageBox.information(
                self,
                "Связи объекта",
                "Выбери один объект, чтобы открыть его связи.",
            )
            return

        obj = objects[0]
        if self._relationships_window is None:
            relationships_window = ObjectRelationshipsWindow(self.project, obj, self.settings, self)
            relationships_window.object_selected.connect(self._select_relationship_object)
            self._relationships_window = relationships_window
        else:
            self._relationships_window.set_object(obj)

        self._relationships_window.show()
        self._relationships_window.raise_()
        self._relationships_window.activateWindow()

    def _sync_relationships_window_with_selection(self, obj: Optional[ModObject]) -> None:
        window = self._relationships_window
        if window is None or not window.follows_main_selection():
            return
        window.set_object(obj)

    def _select_relationship_object(self, obj: ModObject) -> None:
        self._select_object_in_tree(obj)

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
        before = self.action_history.capture()
        try:
            new_obj = self.project.create_object(schema_key)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать объект:\n{e}")
            return

        self._record_project_action("Add object", before)
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
        self.editor.apply_changes()
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить объект {obj.label()} из файла {obj.file_path.name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        before = self.action_history.capture()
        self.project.delete_object(obj)
        self._record_project_action("Delete object", before)
        self.editor.clear_selection_without_applying()
        self._rebuild_tree()
        self.statusBar().showMessage("Объект удалён", 5000)

    def _move_selected_objects(self) -> None:
        self.editor.apply_changes()

        objects = self._selected_objects()
        if not objects:
            QMessageBox.information(
                self,
                "Перемещение объектов",
                "Сначала выбери один или несколько объектов в списке.",
            )
            return

        start_dir = str(self.project.root) if self.project.root is not None else ""
        target, _ = QFileDialog.getSaveFileName(
            self,
            "Выберите JSON-файл для перемещения",
            start_dir,
            "JSON файлы (*.json);;Все файлы (*.*)",
        )
        if not target:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение перемещения",
            f"Переместить объектов: {len(objects)}\nв файл:\n{target}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        before = self.action_history.capture()
        try:
            moved = self.project.move_objects_to_file(objects, Path(target))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка перемещения", str(e))
            return

        if moved:
            self._record_project_action("Move objects", before)
        self.editor.set_object(None)
        self._rebuild_tree()
        if moved:
            self._select_object_in_tree(moved[0])
        self.statusBar().showMessage(f"Перемещено объектов: {len(moved)}", 5000)

    def _rename_warning_text(self, obj: ModObject) -> str:
        incoming = self.project.incoming_references_for(obj)
        lines = [
            f"Переименовать объект {obj.json_type}/{obj.get_id()}?",
            f"Входящих ссылок: {len(incoming)}",
        ]

        for reference in incoming[:10]:
            lines.append(
                f"- {reference.source.json_type}/{reference.source.get_id()} "
                f"({reference.field_name})"
            )

        hidden_count = len(incoming) - 10
        if hidden_count > 0:
            lines.append(f"- ... ещё {hidden_count}")

        if incoming:
            lines.extend(
                [
                    "",
                    "Yes: переименовать и обновить найденные ref_list ссылки.",
                    "No: переименовать только объект.",
                    "Cancel: отменить.",
                ]
            )
        else:
            lines.extend(["", "Ссылки на этот объект в текущем индексе не найдены."])

        return "\n".join(lines)

    def _rename_selected_object(self) -> None:
        self.editor.apply_changes()

        objects = self._selected_objects()
        if len(objects) != 1:
            QMessageBox.information(
                self,
                "Переименование объекта",
                "Выбери ровно один объект для переименования.",
            )
            return

        obj = objects[0]
        old_id = obj.get_id()
        new_id, ok = QInputDialog.getText(
            self,
            "Переименование объекта",
            "Новый id:",
            text=old_id,
        )
        if not ok:
            return

        incoming_count = len(self.project.incoming_references_for(obj))
        update_references = False
        if incoming_count:
            reply = QMessageBox.question(
                self,
                "Ссылки на объект",
                self._rename_warning_text(obj),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                return
            update_references = reply == QMessageBox.Yes
        else:
            reply = QMessageBox.question(
                self,
                "Подтверждение переименования",
                self._rename_warning_text(obj),
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        before = self.action_history.capture()
        try:
            result = self.project.rename_object(
                obj,
                new_id,
                update_references=update_references,
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка переименования", str(e))
            return

        self._record_project_action("Rename object", before)
        self.editor.clear_selection_without_applying()
        self._rebuild_tree()
        self._select_object_in_tree(obj)
        self.editor.set_object(obj)
        self.statusBar().showMessage(
            f"Переименовано {result.old_id} -> {result.new_id}; ссылок обновлено: {result.updated_references}",
            5000,
        )

    # ---------- сохранение ----------

    def _save_all(self) -> None:
        self.editor.apply_changes()

        try:
            self.project.save_all_files()
        except Exception as e:
            logger.exception("Failed to save all files")
            QMessageBox.critical(
                self,
                "Ошибка при сохранении",
                f"Не удалось сохранить файлы:\n\n{e}",
            )
        else:
            logger.info("Saved all files")
            QMessageBox.information(self, "Готово", "Все файлы сохранены.")

    def _save_dirty(self) -> None:
        self.editor.apply_changes()

        if not self.project.dirty_files:
            QMessageBox.information(self, "Сохранение", "Нет изменённых файлов.")
            return

        try:
            self.project.save_dirty_files()
        except Exception as e:
            logger.exception("Failed to save dirty files")
            QMessageBox.critical(
                self,
                "Ошибка при сохранении",
                f"Не удалось сохранить изменённые файлы:\n\n{e}",
            )
        else:
            logger.info("Saved dirty files")
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
        try:
            self.project.save_file(path)
        except Exception as e:
            logger.exception("Failed to save current file %s", path)
            QMessageBox.critical(self, "Ошибка сохранения", str(e))
        else:
            logger.info("Saved current file %s", path)
            QMessageBox.information(self, "Готово", f"Файл {path} сохранён.")


def main() -> None:
    import sys

    base_dir = get_app_base_dir()
    configure_app_logging(base_dir=base_dir)
    logger.info("Starting CDDA JSON Mod Editor")
    app = QApplication(sys.argv)
    w = MainWindow(app_base_dir=base_dir)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
