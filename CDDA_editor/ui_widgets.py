from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    from .project import ModProject
    from .schemas import SCHEMAS
except ImportError:
    from project import ModProject
    from schemas import SCHEMAS


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class RefListWidget(QWidget):
    def __init__(self, project: ModProject, ref_type: str,
                 initial: Optional[List[str]] = None,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.project = project
        self.ref_type = ref_type

        self.list_widget = QListWidget(self)
        self.list_widget.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked
        )

        for val in initial or []:
            if val:
                QListWidgetItem(str(val), self.list_widget)

        self.combo = QComboBox(self)
        self.combo.setEditable(True)

        json_type = SCHEMAS.get(ref_type, {}).get("json_type", ref_type)
        ids = self.project.get_ids_for_json_type(json_type)
        for ident in ids:
            self.combo.addItem(ident)

        add_btn = QPushButton("Добавить", self)
        del_btn = QPushButton("Удалить выбранное", self)

        add_btn.clicked.connect(self._on_add)
        del_btn.clicked.connect(self._on_delete)

        top = QHBoxLayout()
        top.addWidget(QLabel("ID:", self))
        top.addWidget(self.combo)
        top.addWidget(add_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.list_widget)
        layout.addWidget(del_btn)
        layout.setContentsMargins(0, 0, 0, 0)

    def _on_add(self) -> None:
        text = self.combo.currentText().strip()
        if not text:
            return
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == text:
                return
        QListWidgetItem(text, self.list_widget)

    def _on_delete(self) -> None:
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)

    def value(self) -> List[str]:
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]


class NewFieldDialog(QDialog):
    """Диалог для создания произвольного поля."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Новое поле")
        self.name_edit = QLineEdit(self)
        self.type_combo = QComboBox(self)
        self.type_combo.addItems([
            "string",
            "int",
            "float",
            "bool",
            "list_string",
            "flags",
            "ref_list",
            "json",
            "string_or_translation",
        ])

        form = QFormLayout()
        form.addRow("Имя поля:", self.name_edit)
        form.addRow("Тип:", self.type_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def get_result(self) -> Optional[Dict[str, Any]]:
        if self.exec_() != QDialog.Accepted:
            return None
        name = self.name_edit.text().strip()
        if not name:
            return None
        ftype = self.type_combo.currentText()
        return {"name": name, "type": ftype}


class ResizableRow(QWidget):
    """
    Строка формы: [editor + Удалить] + снизу тонкая ручка для ресайза.
    """

    def __init__(self, key: str, editor_widget: QWidget,
                 parent_editor: Any,
                 resizable: bool = True,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.key = key
        self.editor_widget = editor_widget
        self.parent_editor = parent_editor
        self.resizable = resizable

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.addWidget(editor_widget)

        btn = QPushButton("Удалить", self)
        btn.setToolTip("Удалить это поле из объекта JSON.")
        btn.setFixedHeight(28)
        btn.setFixedWidth(90)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hlayout.addWidget(btn)
        hlayout.setAlignment(btn, Qt.AlignTop)

        vlayout.addLayout(hlayout)

        self.handle = QWidget(self)
        self.handle.setFixedHeight(8)
        self.handle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.handle.setCursor(Qt.SizeVerCursor)
        vlayout.addWidget(self.handle)

        btn.clicked.connect(lambda _=False, k=key: self.parent_editor._delete_field(k))

        self._resizing = False
        self._drag_start_global_y = 0
        self._start_height = self.sizeHint().height()
        self._min_height = max(self.sizeHint().height(), 24)
        if self.resizable:
            self.setMinimumHeight(self._min_height)

        self.handle.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.handle and self.resizable:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._resizing = True
                self._drag_start_global_y = event.globalPos().y()
                self._start_height = self.height()
                return True
            elif event.type() == QEvent.MouseMove and self._resizing:
                dy = event.globalPos().y() - self._drag_start_global_y
                new_h = max(self._start_height + dy, self._min_height)
                self.setMinimumHeight(new_h)
                self.resize(self.width(), new_h)
                self.updateGeometry()
                return True
            elif event.type() == QEvent.MouseButtonRelease and self._resizing:
                if event.button() == Qt.LeftButton:
                    self._resizing = False
                    return True
        return super().eventFilter(obj, event)
