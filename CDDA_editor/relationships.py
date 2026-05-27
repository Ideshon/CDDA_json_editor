from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QSettings, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from .project import ModObject, ModProject, ObjectReference
except ImportError:
    from project import ModObject, ModProject, ObjectReference


class ObjectRelationshipsWindow(QWidget):
    object_selected = pyqtSignal(object)

    def __init__(
        self,
        project: ModProject,
        obj: ModObject,
        settings: Optional[QSettings] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.settings = settings
        self.current_obj: Optional[ModObject] = None

        self.setWindowTitle("Связи объекта")
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.resize(820, 520)

        self.pin_button = QPushButton("Закрепить", self)
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Держать окно поверх основного")
        self.pin_button.toggled.connect(self._set_pinned)

        self.dynamic_selection_checkbox = QCheckBox(
            "Следовать за выбранным объектом",
            self,
        )
        self.dynamic_selection_checkbox.setChecked(True)

        self.header_label = QLabel("", self)
        self.file_label = QLabel("", self)

        self.incoming_table = QTableWidget(self)
        self.incoming_table.setColumnCount(4)
        self.incoming_table.setHorizontalHeaderLabels(["Источник", "Поле", "Файл", "Статус"])
        self._configure_table(self.incoming_table)
        self.incoming_table.cellClicked.connect(
            lambda row, column: self._activate_table_object(self.incoming_table, row, column)
        )

        self.outgoing_table = QTableWidget(self)
        self.outgoing_table.setColumnCount(4)
        self.outgoing_table.setHorizontalHeaderLabels(["Цель", "Поле", "Файл", "Статус"])
        self._configure_table(self.outgoing_table)
        self.outgoing_table.cellClicked.connect(
            lambda row, column: self._activate_table_object(self.outgoing_table, row, column)
        )

        controls = QHBoxLayout()
        controls.addWidget(self.pin_button)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.dynamic_selection_checkbox)
        layout.addWidget(self.header_label)
        layout.addWidget(self.file_label)
        layout.addWidget(QLabel("Входящие ссылки", self))
        layout.addWidget(self.incoming_table)
        layout.addWidget(QLabel("Исходящие ссылки", self))
        layout.addWidget(self.outgoing_table)
        self.setLayout(layout)

        self.set_object(obj)
        self._restore_window_state()

    def follows_main_selection(self) -> bool:
        return self.dynamic_selection_checkbox.isChecked()

    def set_object(self, obj: Optional[ModObject]) -> None:
        self.current_obj = obj
        if obj is None:
            self.header_label.setText("Объект не выбран")
            self.file_label.setText("Файл: -")
            self.incoming_table.setRowCount(0)
            self.outgoing_table.setRowCount(0)
            return

        self.header_label.setText(f"{obj.json_type}/{obj.get_id()}")
        self.file_label.setText(f"Файл: {self.project.relative_object_file(obj)}")
        self._fill_incoming_table(obj)
        self._fill_outgoing_table(obj)

    def _configure_table(self, table: QTableWidget) -> None:
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _fill_incoming_table(self, obj: ModObject) -> None:
        references = self.project.incoming_references_for(obj)
        self.incoming_table.setRowCount(len(references))
        for row, reference in enumerate(references):
            source = reference.source
            self._set_object_item(
                self.incoming_table,
                row,
                0,
                self._object_label(source),
                source,
            )
            self._set_text_item(self.incoming_table, row, 1, reference.field_name)
            self._set_text_item(
                self.incoming_table,
                row,
                2,
                str(self.project.relative_object_file(source)),
            )
            self._set_text_item(self.incoming_table, row, 3, "найден")

    def _fill_outgoing_table(self, obj: ModObject) -> None:
        references = self.project.outgoing_references_for(obj)
        self.outgoing_table.setRowCount(len(references))
        for row, reference in enumerate(references):
            target = reference.target
            self._set_object_item(
                self.outgoing_table,
                row,
                0,
                self._reference_target_label(reference),
                target,
            )
            self._set_text_item(self.outgoing_table, row, 1, reference.field_name)
            self._set_text_item(
                self.outgoing_table,
                row,
                2,
                str(self.project.relative_object_file(target)) if target is not None else "-",
            )
            self._set_text_item(
                self.outgoing_table,
                row,
                3,
                "найден" if target is not None else "не найден",
            )

    def _set_object_item(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        text: str,
        obj: Optional[ModObject],
    ) -> None:
        item = QTableWidgetItem(text)
        item.setData(Qt.UserRole, obj)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(row, column, item)

    def _set_text_item(self, table: QTableWidget, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(row, column, item)

    def _activate_table_object(self, table: QTableWidget, row: int, _column: int) -> None:
        item = table.item(row, 0)
        if item is None:
            return
        obj = item.data(Qt.UserRole)
        if isinstance(obj, ModObject):
            self.object_selected.emit(obj)

    def _set_pinned(self, pinned: bool) -> None:
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, pinned)
        if was_visible:
            self.show()
        if pinned:
            self.raise_()

    def _save_window_state(self) -> None:
        if self.settings is None:
            return
        self.settings.setValue("relationships_window/geometry", self.saveGeometry())
        self.settings.setValue("relationships_window/width", self.size().width())
        self.settings.setValue("relationships_window/height", self.size().height())
        self.settings.setValue("relationships_window/pinned", self.pin_button.isChecked())
        self.settings.setValue(
            "relationships_window/dynamic_selection",
            self.dynamic_selection_checkbox.isChecked(),
        )
        self.settings.sync()

    def _restore_window_state(self) -> None:
        if self.settings is None:
            return

        geometry = self.settings.value("relationships_window/geometry")
        if geometry:
            self.restoreGeometry(geometry)

        width = self._settings_int("relationships_window/width")
        height = self._settings_int("relationships_window/height")
        if width and height:
            self.resize(width, height)

        self.dynamic_selection_checkbox.setChecked(
            self._settings_bool("relationships_window/dynamic_selection", True)
        )
        self.pin_button.setChecked(self._settings_bool("relationships_window/pinned", False))

    def _settings_int(self, key: str) -> int:
        if self.settings is None:
            return 0
        value = self.settings.value(key, 0)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _settings_bool(self, key: str, default: bool) -> bool:
        if self.settings is None:
            return default
        value = self.settings.value(key, default)
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._save_window_state()
        super().closeEvent(event)

    def _object_label(self, obj: ModObject) -> str:
        return f"{obj.json_type}/{obj.get_id()}"

    def _reference_target_label(self, reference: ObjectReference) -> str:
        if reference.target is not None:
            return self._object_label(reference.target)
        return f"{reference.target_type}/{reference.target_id}"
