# editor.py
from __future__ import annotations
from typing import Dict, Any, Optional, List

from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QTextEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
    QScrollArea,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
    QAbstractItemView,
)
from PyQt5.QtGui import QTextOption

from schemas import SCHEMAS
from project import ModProject, ModObject


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
        # можно редактировать элементы вручную
        self.list_widget.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked
        )

        for val in initial or []:
            if val:
                QListWidgetItem(str(val), self.list_widget)

        self.combo = QComboBox(self)
        self.combo.setEditable(True)  # можно вбить свой ID

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
                 parent_editor: "ObjectEditorWidget",
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

        # ручка для перетаскивания высоты
        self.handle = QWidget(self)
        self.handle.setFixedHeight(4)
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


class ObjectEditorWidget(QWidget):
    def __init__(self, project: ModProject, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.project = project
        self.current_obj: Optional[ModObject] = None
        self.current_schema: Optional[Dict[str, Any]] = None
        self.field_widgets: Dict[str, QWidget] = {}
        self.fields_meta: Dict[str, Dict[str, Any]] = {}

        self.header_label = QLabel("Ничего не выбрано", self)

        self.add_combo = QComboBox(self)
        self.add_combo.setEditable(False)
        self.add_button = QPushButton("Добавить поле", self)
        self.add_button.clicked.connect(self._on_add_field_clicked)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Добавить поле:", self))
        controls.addWidget(self.add_combo)
        controls.addWidget(self.add_button)
        controls.addStretch()

        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)

        inner = QWidget(self)
        inner.setLayout(self.form)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)

        layout = QVBoxLayout(self)
        layout.addWidget(self.header_label)
        layout.addLayout(controls)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self._clear_add_combo()

    def clear_form(self) -> None:
        while self.form.rowCount():
            self.form.removeRow(0)
        self.field_widgets.clear()
        self.fields_meta.clear()
        self._clear_add_combo()

    def _clear_add_combo(self) -> None:
        self.add_combo.clear()
        self.add_combo.addItem("— выбери поле —", None)

    def set_object(self, obj: Optional[ModObject]) -> None:
        # применяем изменения перед сменой объекта
        self.apply_changes()

        self.current_obj = obj
        if obj is None:
            self.current_schema = None
            self.header_label.setText("Ничего не выбрано")
            self.clear_form()
            return

        self.current_schema = SCHEMAS[obj.schema_key]
        self.header_label.setText(
            f"{self.current_schema.get('label', obj.schema_key)}   (type: {obj.json_type})"
        )
        self._rebuild_form()

    def _rebuild_form(self) -> None:
        self.clear_form()
        if not self.current_obj or not self.current_schema:
            return

        schema_fields = self.current_schema.get("fields", {})
        obj_data = self.current_obj.data

        # реальные ключи объекта
        for key, value in obj_data.items():
            if key in schema_fields:
                meta = dict(schema_fields[key])
            else:
                meta = self._make_auto_meta(key, value)
            self.fields_meta[key] = meta

        # строим строки
        for key in sorted(self.fields_meta.keys()):
            meta = self.fields_meta[key]
            editor_widget = self._create_field_widget(key, meta)
            row_widget = ResizableRow(
                key=key,
                editor_widget=editor_widget,
                parent_editor=self,
                resizable=True,
                parent=self,
            )

            label_text = meta.get("label", key)
            label = ClickableLabel(label_text)
            help_text = meta.get("help")
            if help_text:
                label.setToolTip(help_text)
            label._field_key = key      # type: ignore[attr-defined]
            label._help_text = help_text  # type: ignore[attr-defined]
            label.clicked.connect(self._on_label_clicked)

            self.form.addRow(label, row_widget)
            self.field_widgets[key] = editor_widget

        self._rebuild_add_combo()

    def _rebuild_add_combo(self) -> None:
        self._clear_add_combo()
        if not self.current_schema or not self.current_obj:
            self.add_combo.addItem("Создать своё поле…", "__custom__")
            return

        schema_fields = self.current_schema.get("fields", {})
        existing_keys = set(self.current_obj.data.keys())

        available = sorted(k for k in schema_fields.keys() if k not in existing_keys)
        for key in available:
            self.add_combo.addItem(key, key)

        self.add_combo.addItem("Создать своё поле…", "__custom__")

    def _make_auto_meta(self, key: str, value: Any) -> Dict[str, Any]:
        if isinstance(value, bool):
            ftype = "bool"
        elif isinstance(value, int):
            ftype = "int"
        elif isinstance(value, float):
            ftype = "float"
        elif isinstance(value, list):
            if all(not isinstance(x, (dict, list)) for x in value):
                ftype = "list_string"
            else:
                ftype = "json"
        elif isinstance(value, dict):
            ftype = "json"
        else:
            ftype = "string"

        return {
            "label": key,
            "type": ftype,
            "help": (
                f"Авто-поле '{key}'. Это поле было в JSON, но не описано в схеме. "
                f"Тип выбран как {ftype}. Если сомневаешься, редактируй как JSON."
            ),
        }

    def _default_value_for_type(self, ftype: str) -> Any:
        if ftype == "string":
            return ""
        if ftype == "string_or_translation":
            return {"str": ""}
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        if ftype in ("list_string", "flags", "ref_list"):
            return []
        if ftype == "json":
            return {}
        if ftype == "enum":
            return ""
        return ""

    def _on_label_clicked(self) -> None:
        label = self.sender()
        if not isinstance(label, ClickableLabel):
            return
        field_name = getattr(label, "_field_key", None)
        help_text = getattr(label, "_help_text", None)
        if not help_text:
            help_text = f"Поле {field_name}. Подробности смотри в JSON_INFO и документации CDDA."
        QMessageBox.information(self, "Справка по полю", help_text)

    def _on_add_field_clicked(self) -> None:
        if not self.current_obj or not self.current_schema:
            return

        data = self.add_combo.currentData()
        if data is None:
            return

        # своё поле
        if data == "__custom__":
            dlg = NewFieldDialog(self)
            res = dlg.get_result()
            if not res:
                return
            key = res["name"]
            ftype = res["type"]
            if key in self.current_obj.data:
                QMessageBox.information(self, "Поле уже есть", f"Поле '{key}' уже существует.")
                return
            meta = {
                "label": key,
                "type": ftype,
                "help": f"Пользовательское поле '{key}' типа {ftype}.",
            }
        else:
            # поле из схемы
            key = str(data)
            schema_fields = self.current_schema.get("fields", {})
            if key not in schema_fields:
                meta = {
                    "label": key,
                    "type": "string",
                    "help": f"Поле '{key}' добавлено из схемы, но без описания.",
                }
            else:
                meta = dict(schema_fields[key])

        if key in self.current_obj.data:
            QMessageBox.information(self, "Поле уже есть", f"Поле '{key}' уже существует.")
            return

        ftype = meta.get("type", "string")
        default_val = self._default_value_for_type(ftype)
        self.current_obj.data[key] = default_val
        self.project.mark_dirty(self.current_obj.file_path)
        self._rebuild_form()

    def _delete_field(self, key: str) -> None:
        if not self.current_obj:
            return
        if key not in self.current_obj.data:
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить поле '{key}' из объекта?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        del self.current_obj.data[key]
        self.project.mark_dirty(self.current_obj.file_path)
        self._rebuild_form()

    def _make_vertical_expanding(self, w: QWidget) -> QWidget:
        sp = w.sizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Expanding)
        w.setSizePolicy(sp)
        return w

    # ---------- фабрика виджетов ----------

    def _create_field_widget(self, key: str, meta: Dict[str, Any]) -> QWidget:
        field_type = meta.get("type", "string")
        val = self.current_obj.data.get(key) if self.current_obj else None

        # ENUM / choices → комбобокс + ручной ввод
        choices = meta.get("choices") or meta.get("options")
        if field_type == "enum" or choices:
            w = QComboBox(self)
            w.setEditable(True)

            if isinstance(choices, (list, tuple)):
                for ch in choices:
                    w.addItem(str(ch))

            if val is not None:
                sval = str(val)
                idx = w.findText(sval)
                if idx >= 0:
                    w.setCurrentIndex(idx)
                else:
                    if sval:
                        w.addItem(sval)
                        w.setCurrentIndex(w.count() - 1)
                    else:
                        w.setEditText(sval)

            return self._make_vertical_expanding(w)

        # string → QTextEdit с переносом, по умолчанию в одну строку
        if field_type == "string":
            w = QTextEdit(self)
            w.setWordWrapMode(QTextOption.WordWrap)
            if val is not None:
                w.setPlainText(str(val))
            fm = w.fontMetrics()
            one_line = int(fm.height() * 1.6)
            w.setMinimumHeight(one_line)
            return self._make_vertical_expanding(w)

        # int
        if field_type == "int":
            w = QSpinBox(self)
            w.setMinimum(meta.get("min", -1_000_000))
            w.setMaximum(meta.get("max", 1_000_000))
            if isinstance(val, int):
                w.setValue(val)
            return self._make_vertical_expanding(w)

        # float
        if field_type == "float":
            w = QDoubleSpinBox(self)
            w.setMinimum(meta.get("min", -1_000_000.0))
            w.setMaximum(meta.get("max", 1_000_000.0))
            w.setDecimals(4)
            if isinstance(val, (int, float)):
                w.setValue(float(val))
            return self._make_vertical_expanding(w)

        # bool
        if field_type == "bool":
            w = QCheckBox(self)
            if isinstance(val, bool):
                w.setChecked(val)
            return self._make_vertical_expanding(w)

        # list_string / flags → многострочный, но стартует одной строкой
        if field_type in ("list_string", "flags"):
            w = QTextEdit(self)
            if isinstance(val, list):
                w.setPlainText("\n".join(str(v) for v in val))
            fm = w.fontMetrics()
            one_line = int(fm.height() * 1.6)
            w.setMinimumHeight(one_line)
            return self._make_vertical_expanding(w)

        # ref_list
        if field_type == "ref_list":
            ref_type = meta.get("ref_type")
            if not ref_type:
                w = QTextEdit(self)
                if isinstance(val, list):
                    w.setPlainText("\n".join(str(v) for v in val))
                fm = w.fontMetrics()
                one_line = int(fm.height() * 1.6)
                w.setMinimumHeight(one_line)
                return self._make_vertical_expanding(w)
            initial = val if isinstance(val, list) else []
            w = RefListWidget(self.project, ref_type, initial, self)
            return self._make_vertical_expanding(w)

        # json
        if field_type == "json":
            w = QTextEdit(self)
            if val is not None:
                try:
                    w.setPlainText(json_dumps_pretty(val))
                except Exception:
                    w.setPlainText(str(val))
            fm = w.fontMetrics()
            one_line = int(fm.height() * 1.6)
            w.setMinimumHeight(one_line)
            return self._make_vertical_expanding(w)

        # string_or_translation → тоже многострочный
        if field_type == "string_or_translation":
            w = QTextEdit(self)
            w.setWordWrapMode(QTextOption.WordWrap)
            if isinstance(val, dict):
                text = val.get("str")
                if text is None:
                    for v in val.values():
                        if isinstance(v, str):
                            text = v
                            break
                if text is not None:
                    w.setPlainText(str(text))
            elif val is not None:
                w.setPlainText(str(val))
            fm = w.fontMetrics()
            one_line = int(fm.height() * 1.6)
            w.setMinimumHeight(one_line)
            return self._make_vertical_expanding(w)

        # запасной вариант
        w = QLineEdit(self)
        if val is not None:
            w.setText(str(val))
        return self._make_vertical_expanding(w)

    # ---------- запись значений ----------

    def apply_changes(self) -> None:
        if not self.current_obj or not self.fields_meta:
            return

        for key, meta in self.fields_meta.items():
            widget = self.field_widgets.get(key)
            if widget is None:
                continue
            old_val = self.current_obj.data.get(key)
            new_val = self._read_widget_value(key, meta, widget, old_val)
            if new_val == old_val:
                continue
            self.current_obj.data[key] = new_val
            self.project.mark_dirty(self.current_obj.file_path)

    def _read_widget_value(self, key: str, meta: Dict[str, Any],
                           widget: QWidget, old_val: Any) -> Any:
        field_type = meta.get("type", "string")
        choices = meta.get("choices") or meta.get("options")

        # enum / choices
        if field_type == "enum" or choices:
            if isinstance(widget, QComboBox):
                return widget.currentText()
            return old_val

        # string
        if field_type == "string":
            if isinstance(widget, QTextEdit):
                return widget.toPlainText()
            if isinstance(widget, QLineEdit):
                return widget.text()
            return old_val

        # int
        if field_type == "int":
            if isinstance(widget, QSpinBox):
                return int(widget.value())
            return old_val

        # float
        if field_type == "float":
            if isinstance(widget, QDoubleSpinBox):
                return float(widget.value())
            return old_val

        # bool
        if field_type == "bool":
            if isinstance(widget, QCheckBox):
                return bool(widget.isChecked())
            return old_val

        # list_string / flags
        if field_type in ("list_string", "flags"):
            if isinstance(widget, QTextEdit):
                text = widget.toPlainText().strip()
                if not text:
                    return []
                return [line.strip() for line in text.splitlines() if line.strip()]
            return old_val

        # ref_list
        if field_type == "ref_list":
            if isinstance(widget, RefListWidget):
                return widget.value()
            if isinstance(widget, QTextEdit):
                text = widget.toPlainText().strip()
                if not text:
                    return []
                return [line.strip() for line in text.splitlines() if line.strip()]
            return old_val

        # json
        if field_type == "json":
            if isinstance(widget, QTextEdit):
                text = widget.toPlainText().strip()
                if not text:
                    return {}
                try:
                    return json_load_relaxed(text)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Ошибка JSON",
                        f"Поле '{key}': не удалось разобрать JSON:\n{e}",
                    )
                    return old_val if old_val is not None else {}
            return old_val

        # string_or_translation
        if field_type == "string_or_translation":
            if isinstance(widget, QTextEdit):
                text = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                text = widget.text()
            else:
                return old_val
            if isinstance(old_val, dict):
                new_obj = dict(old_val)
                new_obj["str"] = text
                return new_obj
            return text

        # запасной случай
        if isinstance(widget, QLineEdit):
            return widget.text()
        if isinstance(widget, QTextEdit):
            return widget.toPlainText()
        return old_val


# утилиты JSON
import json
import re
from typing import Any


def json_load_relaxed(text: str) -> Any:
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return json.loads(text)


def json_dumps_pretty(val: Any) -> str:
    return json.dumps(val, ensure_ascii=False, indent=2)
