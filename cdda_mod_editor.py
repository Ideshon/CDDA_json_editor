import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QTextEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ModObject:
    def __init__(self, schema_key: str, json_type: str, file_path: Path, data: Dict[str, Any]):
        self.schema_key = schema_key
        self.json_type = json_type
        self.file_path = Path(file_path)
        self.data = data

    def get_id(self) -> str:
        schema = SCHEMAS[self.schema_key]
        id_field = schema["id_field"]
        value = self.data.get(id_field)
        if value is None:
            # Fallbacks for old content
            for key in ("id", "ident", "abstract"):
                if key in self.data:
                    value = self.data.get(key)
                    break
        return str(value) if value is not None else ""

    def get_display_name(self) -> str:
        schema = SCHEMAS[self.schema_key]
        display_field = schema.get("display_field", "id")
        value = self.data.get(display_field)
        if isinstance(value, dict):
            # translation object
            if "str" in value:
                return str(value["str"])
            # gendered or other forms: take first
            for v in value.values():
                if isinstance(v, str):
                    return v
        if value is not None:
            return str(value)
        # fallback to id
        return self.get_id() or "<без имени>"

    def label(self) -> str:
        obj_id = self.get_id()
        name = self.get_display_name()
        if obj_id and name and obj_id != name:
            return f"{obj_id} — {name}"
        return obj_id or name or "<объект>"


class ModProject:
    def __init__(self) -> None:
        self.root: Optional[Path] = None
        self.files: Dict[Path, List[Dict[str, Any]]] = {}
        self.objects_by_schema: Dict[str, List[ModObject]] = {}
        self.ids_by_type: Dict[str, set[str]] = {}

    def clear(self) -> None:
        self.root = None
        self.files.clear()
        self.objects_by_schema.clear()
        self.ids_by_type.clear()

    def load_from_dir(self, root_path: str) -> None:
        self.clear()
        self.root = Path(root_path)

        for path in self.root.rglob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[WARN] Не удалось прочитать {path}: {e}")
                continue

            if isinstance(data, dict):
                objs = [data]
            elif isinstance(data, list):
                objs = data
            else:
                continue

            self.files[path] = objs

            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                json_type = obj.get("type")
                if not isinstance(json_type, str):
                    continue
                schema_key = self._schema_for_type(json_type)
                if not schema_key:
                    continue
                mod_obj = ModObject(schema_key, json_type, path, obj)
                self.objects_by_schema.setdefault(schema_key, []).append(mod_obj)
                self._register_ids(mod_obj)

    def _schema_for_type(self, json_type: str) -> Optional[str]:
        for key, schema in SCHEMAS.items():
            if schema["json_type"] == json_type:
                return key
        return None

    def _register_ids(self, obj: ModObject) -> None:
        schema = SCHEMAS[obj.schema_key]
        id_field = schema["id_field"]
        obj_id = obj.data.get(id_field)
        if obj_id:
            self.ids_by_type.setdefault(obj.json_type, set()).add(str(obj_id))

    def get_ids_for_json_type(self, json_type: str) -> List[str]:
        return sorted(self.ids_by_type.get(json_type, set()))


class RefListWidget(QWidget):
    def __init__(self, project: ModProject, ref_type: str, initial: Optional[List[str]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.project = project
        self.ref_type = ref_type

        self.list_widget = QListWidget(self)
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

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("ID:", self))
        top_row.addWidget(self.combo)
        top_row.addWidget(add_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addWidget(self.list_widget)
        layout.addWidget(del_btn)
        layout.setContentsMargins(0, 0, 0, 0)

    def _on_add(self) -> None:
        text = self.combo.currentText().strip()
        if not text:
            return
        # avoid duplicates
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


class ObjectEditorWidget(QWidget):
    def __init__(self, project: ModProject, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.project = project
        self.current_obj: Optional[ModObject] = None
        self.current_schema: Optional[Dict[str, Any]] = None
        self.field_widgets: Dict[str, QWidget] = {}

        self.header_label = QLabel("Ничего не выбрано", self)

        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)

        inner = QWidget(self)
        inner.setLayout(self.form)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)

        layout = QVBoxLayout(self)
        layout.addWidget(self.header_label)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def clear_form(self) -> None:
        while self.form.rowCount():
            self.form.removeRow(0)
        self.field_widgets.clear()

    def set_object(self, obj: Optional[ModObject]) -> None:
        # сохранить изменения предыдущего объекта
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

        fields = self.current_schema.get("fields", {})
        for key, meta in fields.items():
            widget = self._create_field_widget(key, meta)
            label_text = meta.get("label", key)
            label = ClickableLabel(label_text)
            help_text = meta.get("help")
            if help_text:
                label.setToolTip(help_text)
            # store for callback
            label._field_key = key  # type: ignore[attr-defined]
            label._help_text = help_text  # type: ignore[attr-defined]
            label.clicked.connect(self._on_label_clicked)
            self.form.addRow(label, widget)
            self.field_widgets[key] = widget

    def _on_label_clicked(self) -> None:
        label = self.sender()
        if not isinstance(label, ClickableLabel):
            return
        field_name = getattr(label, "_field_key", None)
        help_text = getattr(label, "_help_text", None)
        if not help_text:
            help_text = f"Поле {field_name}.\nПодробности смотри в JSON_INFO.md и профильном документе (MUTATIONS, MAGIC, NPCs и т.п.)."
        QMessageBox.information(self, "Справка по полю", help_text)

    def _create_field_widget(self, key: str, meta: Dict[str, Any]) -> QWidget:
        field_type = meta.get("type", "string")
        value = self.current_obj.data.get(key) if self.current_obj else None

        if field_type == "string":
            w = QLineEdit(self)
            if value is not None:
                w.setText(str(value))
            return w

        if field_type == "int":
            w = QSpinBox(self)
            w.setMinimum(meta.get("min", -1000000))
            w.setMaximum(meta.get("max", 1000000))
            if isinstance(value, int):
                w.setValue(value)
            return w

        if field_type == "bool":
            w = QCheckBox(self)
            if isinstance(value, bool):
                w.setChecked(value)
            return w

        if field_type in ("list_string", "flags"):
            w = QTextEdit(self)
            if isinstance(value, list):
                lines = [str(v) for v in value]
                w.setPlainText("\n".join(lines))
            return w

        if field_type == "ref_list":
            ref_type = meta.get("ref_type")
            if not ref_type:
                # fallback: simple list of strings
                w = QTextEdit(self)
                if isinstance(value, list):
                    lines = [str(v) for v in value]
                    w.setPlainText("\n".join(lines))
                return w
            initial = value if isinstance(value, list) else []
            return RefListWidget(self.project, ref_type, initial, self)

        if field_type == "json":
            w = QTextEdit(self)
            if value is not None:
                try:
                    w.setPlainText(json.dumps(value, ensure_ascii=False, indent=2))
                except Exception:
                    w.setPlainText(str(value))
            return w

        if field_type == "string_or_translation":
            w = QLineEdit(self)
            if isinstance(value, dict):
                # translation object
                text = value.get("str")
                if text is None:
                    # gendered or other map: pick first string
                    for v in value.values():
                        if isinstance(v, str):
                            text = v
                            break
                if text is not None:
                    w.setText(str(text))
            elif value is not None:
                w.setText(str(value))
            return w

        # default fallback
        w = QLineEdit(self)
        if value is not None:
            w.setText(str(value))
        return w

    def apply_changes(self) -> None:
        if not self.current_obj or not self.current_schema:
            return

        fields = self.current_schema.get("fields", {})
        for key, meta in fields.items():
            widget = self.field_widgets.get(key)
            if widget is None:
                continue
            new_value = self._read_widget_value(key, meta, widget)
            if new_value is _UNCHANGED:
                continue
            self.current_obj.data[key] = new_value

    def _read_widget_value(self, key: str, meta: Dict[str, Any], widget: QWidget) -> Any:
        field_type = meta.get("type", "string")
        old_value = self.current_obj.data.get(key) if self.current_obj else None

        if field_type == "string":
            assert isinstance(widget, QLineEdit)
            return widget.text()

        if field_type == "int":
            assert isinstance(widget, QSpinBox)
            return int(widget.value())

        if field_type == "bool":
            assert isinstance(widget, QCheckBox)
            return bool(widget.isChecked())

        if field_type in ("list_string", "flags"):
            assert isinstance(widget, QTextEdit)
            text = widget.toPlainText().strip()
            if not text:
                return []
            return [line.strip() for line in text.splitlines() if line.strip()]

        if field_type == "ref_list":
            if isinstance(widget, RefListWidget):
                return widget.value()
            # fallback text mode
            if isinstance(widget, QTextEdit):
                text = widget.toPlainText().strip()
                if not text:
                    return []
                return [line.strip() for line in text.splitlines() if line.strip()]
            return old_value

        if field_type == "json":
            assert isinstance(widget, QTextEdit)
            text = widget.toPlainText().strip()
            if not text:
                return {}
            try:
                return json.loads(text)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Ошибка JSON",
                    f"Не удалось разобрать JSON в поле '{key}': {e}",
                )
                return old_value if old_value is not None else {}

        if field_type == "string_or_translation":
            assert isinstance(widget, QLineEdit)
            text = widget.text()
            # сохраняем формат: если было dict, остаётся dict
            if isinstance(old_value, dict):
                new_obj = dict(old_value)
                new_obj["str"] = text
                return new_obj
            return text

        # fallback
        if isinstance(widget, QLineEdit):
            return widget.text()
        if isinstance(widget, QTextEdit):
            return widget.toPlainText()
        return old_value


_UNCHANGED = object()


# --------- SCHEMAS & HELP TEXTS ---------

MUTATION_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "Уникальный ID мутации/трэйта. Используется в prereqs, cancels, leads_to и ссылках из других JSON. Не должен повторяться среди всех type: \"mutation\".",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "required": True,
        "help": "Отображаемое имя мутации. Может быть простой строкой или объектом перевода { \"str\": \"...\" }.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Текстовое описание мутации, выводится в интерфейсе. Поддерживает обычный текст и сниппеты.",
    },
    "points": {
        "label": "points",
        "type": "int",
        "help": "Стоимость/вознаграждение очков при выборе трэйта на старте. Положительное значение тратит очки, отрицательное даёт.",
    },
    "visibility": {
        "label": "visibility",
        "type": "int",
        "help": "Насколько заметен этот трэйт для NPC (0 — не заметен, большее число — легче заметить).",
    },
    "ugliness": {
        "label": "ugliness",
        "type": "int",
        "help": "Условная «уродливость» для реакции NPC: отрицательные значения делают персонажа более привлекательным, положительные — менее.",
    },
    "starting_trait": {
        "label": "starting_trait",
        "type": "bool",
        "help": "Можно ли брать этот трэйт при создании персонажа.",
    },
    "valid": {
        "label": "valid",
        "type": "bool",
        "help": "Можно ли получить эту мутацию обычными способами в игре (мутагены и т.п.).",
    },
    "purifiable": {
        "label": "purifiable",
        "type": "bool",
        "help": "Можно ли вывести эту мутацию очистителем / праймером.",
    },
    "player_display": {
        "label": "player_display",
        "type": "bool",
        "help": "Показывать ли мутацию в экране персонажа и списке мутаций.",
    },
    "vanity": {
        "label": "vanity",
        "type": "bool",
        "help": "Косметическая мутация, которую можно свободно менять без стоимости (цвет волос, глаз и т.п.).",
    },
    "types": {
        "label": "types",
        "type": "list_string",
        "help": "Список внутренних типов (групп) мутации, влияющих на совместимость других мутаций.",
    },
    "category": {
        "label": "category",
        "type": "list_string",
        "help": "Категории мутаций (птица, насекомое и т.д.), используются системой праймеров и порогов.",
    },
    "allowed_category": {
        "label": "allowed_category",
        "type": "list_string",
        "help": "Список категорий, в которые персонаж с этой мутацией может дальше мутировать.",
    },
    "prereqs": {
        "label": "prereqs",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Список мутаций-пререквизитов (достаточно одной из списка), необходимых для получения текущей.",
    },
    "prereqs2": {
        "label": "prereqs2",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Вторая группа пререквизитов. Условие: (одна из prereqs) И (одна из prereqs2).",
    },
    "threshreq": {
        "label": "threshreq",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Требуемые пороговые мутации (threshold traits), без которых мутация недоступна.",
    },
    "cancels": {
        "label": "cancels",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Список мутаций, которые удаляются при получении текущей.",
    },
    "changes_to": {
        "label": "changes_to",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Во что эта мутация может эволюционировать при дальнейшем мутагенезе.",
    },
    "leads_to": {
        "label": "leads_to",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Какие мутации могут эволюционировать из текущей (обратная связь к changes_to).",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Набор флагов мутации (например, NIGHTVISION, STR_UP). Список строк, по одному флагу на строку.",
    },
    "variants": {
        "label": "variants",
        "type": "json",
        "help": "Косметические варианты мутации. В 0.G могут использоваться и нестандартно, как у тебя с количеством грудей.",
    },
}

EFFECT_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "Уникальный ID эффекта (type: \"effect_type\"). Используется в заклинаниях, мутациях, предметах и т.п.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя эффекта, если оно вообще показывается игроку.",
    },
    "desc": {
        "label": "desc",
        "type": "string_or_translation",
        "help": "Описание эффекта. Часто не используется напрямую, но полезно для документации.",
    },
    "max_intensity": {
        "label": "max_intensity",
        "type": "int",
        "help": "Максимальная интенсивность эффекта (уровень стека).",
    },
    "duration": {
        "label": "duration",
        "type": "int",
        "help": "Базовая длительность эффекта в ходах (или 1/100 хода, в зависимости от контекста).",
    },
    "max_duration": {
        "label": "max_duration",
        "type": "int",
        "help": "Максимальная длительность эффекта.",
    },
    "permanent": {
        "label": "permanent",
        "type": "bool",
        "help": "Если true, эффект не спадает сам по себе.",
    },
    "resist_traits": {
        "label": "resist_traits",
        "type": "list_string",
        "help": "Список мутаций/трейтов, которые уменьшают или отменяют действие эффекта.",
    },
    "resist_effects": {
        "label": "resist_effects",
        "type": "list_string",
        "help": "ID других эффектов, которые дают сопротивление этому.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги эффекта: INTERNAL, PERMANENT, PAIN, BAD, GOOD и т.п.",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Прочие поля effect_type, которые редактор не знает по именам (base_mods, scaling_mods, eocs и т.п.).",
    },
}

ITEM_COMMON_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID предмета. Уникален внутри своего типа (GENERIC, ARMOR, TOOL и т.д.).",
    },
    "copy-from": {
        "label": "copy-from",
        "type": "string",
        "help": "ID другого предмета, у которого наследуются поля по умолчанию.",
    },
    "abstract": {
        "label": "abstract",
        "type": "string",
        "help": "Определение-шаблон без собственного появления в игре. Другие предметы могут делать copy-from на него.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя предмета. Обычный переводимый объект { \"str\": \"...\" }.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание предмета.",
    },
    "weight": {
        "label": "weight",
        "type": "string",
        "help": "Вес. В 0.G обычно указывается в граммах (числом) или со строкой единиц, см. JSON_INFO.",
    },
    "volume": {
        "label": "volume",
        "type": "string",
        "help": "Объём. В новых версиях это количество миллилитров, иногда как строка с единицами.",
    },
    "price": {
        "label": "price",
        "type": "int",
        "help": "Доколаптическая цена в цент-USD. 100 — 1 доллар.",
    },
    "price_postapoc": {
        "label": "price_postapoc",
        "type": "int",
        "help": "Постапокалиптическая цена. Используется торговцами в текущем мире.",
    },
    "material": {
        "label": "material",
        "type": "list_string",
        "help": "Материалы предмета (steel, cotton, plastic и т.п.).",
    },
    "category": {
        "label": "category",
        "type": "string",
        "help": "Категория предмета (ammo, armor, food...), влияет на меню и сортировку.",
    },
    "symbol": {
        "label": "symbol",
        "type": "string",
        "help": "Символ предмета в консольной версии.",
    },
    "color": {
        "label": "color",
        "type": "string",
        "help": "Цвет символа (red, light_red, green и т.д.).",
    },
    "looks_like": {
        "label": "looks_like",
        "type": "string",
        "help": "ID другого предмета, из которого брать вид/спрайт, если для этого предмета спрайта нет.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги предмета (STURDY, WATERPROOF, TRADER_AVOID, BIONIC_WEAPON...).",
    },
    "pocket_data": {
        "label": "pocket_data",
        "type": "json",
        "help": "Определения карманов (для контейнеров, разгрузок и т.п.). Сложная структура, править лучше вручную в JSON.",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Все дополнительные поля, которые не вынесены в форму (charges, use_action, qualities и прочее).",
    },
}

SPELL_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID заклинания (type: \"SPELL\"). Используется в списках заклинаний, мутациях, профессиях и т.п.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя заклинания, выводится в интерфейсе.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание заклинания.",
    },
    "effect": {
        "label": "effect",
        "type": "string",
        "help": "Тип эффекта (attack, targeted, teleport, summon, pain, area_attack и др.).",
    },
    "effect_str": {
        "label": "effect_str",
        "type": "string",
        "help": "Дополнительный параметр для эффекта (ID монстра, поля, эффекта и т.п.).",
    },
    "spell_class": {
        "label": "spell_class",
        "type": "string",
        "help": "Класс заклинания (для группировки, перков и баланса).",
    },
    "valid_targets": {
        "label": "valid_targets",
        "type": "list_string",
        "help": "Разрешённые типы целей: self, ally, hostile, ground и т.п.",
    },
    "min_range": {
        "label": "min_range",
        "type": "int",
        "help": "Минимальная дистанция применения заклинания.",
    },
    "max_range": {
        "label": "max_range",
        "type": "int",
        "help": "Максимальная дистанция применения на максимальном уровне.",
    },
    "min_damage": {
        "label": "min_damage",
        "type": "int",
        "help": "Урон/эффект на 0-м уровне.",
    },
    "max_damage": {
        "label": "max_damage",
        "type": "int",
        "help": "Урон/эффект на максимальном уровне.",
    },
    "damage_type": {
        "label": "damage_type",
        "type": "string",
        "help": "Тип урона: bash, cut, heat, cold, stab и т.п.",
    },
    "base_energy_cost": {
        "label": "base_energy_cost",
        "type": "int",
        "help": "Стоимость ресурса (мана, выносливость, движение) на старте.",
    },
    "energy_source": {
        "label": "energy_source",
        "type": "string",
        "help": "Источник энергии: mana, stamina, bionic, hp и др.",
    },
    "difficulty": {
        "label": "difficulty",
        "type": "int",
        "help": "Сложность изучения/прокачки заклинания.",
    },
    "max_level": {
        "label": "max_level",
        "type": "int",
        "help": "Максимальный уровень заклинания.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги заклинания (PERMANENT, NO_PROJECTILE, VERBAL и т.п.).",
    },
    "extra_effects": {
        "label": "extra_effects",
        "type": "json",
        "help": "Дополнительные эффекты, которые накладываются при касте.",
    },
    "raw": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Все прочие поля SPELL, которые редактор не знает по именам (field_id, sound_id, learn_spells...).",
    },
}

TALK_TOPIC_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID темы диалога (type: \"talk_topic\"). Ссылается из NPC, миссий и других talk_topic.",
    },
    "dynamic_line": {
        "label": "dynamic_line",
        "type": "json",
        "help": "Фраза NPC или динамическая структура из TALK_JSON (u_has_trait, npc_male, u_true и т.п.).",
    },
    "responses": {
        "label": "responses",
        "type": "json",
        "help": "Варианты ответов игрока, список объектов ответа (text, topic, trial, effect...).",
    },
    "speaker_effect": {
        "label": "speaker_effect",
        "type": "json",
        "help": "effect_on_condition, который выполняется, когда NPC произносит dynamic_line.",
    },
    "repeat_responses": {
        "label": "repeat_responses",
        "type": "json",
        "help": "Отдельные ответы для повторных заходов в эту тему диалога.",
    },
}

NPC_CLASS_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID класса NPC (type: \"npc_class\"). На него ссылаются конкретные NPC и генератор мира.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя класса NPC, используется в отладке и иногда в интерфейсе.",
    },
    "job_description": {
        "label": "job_description",
        "type": "string_or_translation",
        "help": "Описание профессии NPC.",
    },
    "traits": {
        "label": "traits",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Список мутаций/трейтов, которые даются NPC этого класса.",
    },
    "skills": {
        "label": "skills",
        "type": "json",
        "help": "Навыки NPC (карта skill → уровень).",
    },
    "spells": {
        "label": "spells",
        "type": "ref_list",
        "ref_type": "magic_spell",
        "help": "Список ID заклинаний, которыми владеет NPC этого класса.",
    },
    "worn_override": {
        "label": "worn_override",
        "type": "json",
        "help": "Одежда, которая гарантированно будет надета на NPC.",
    },
    "carry_override": {
        "label": "carry_override",
        "type": "json",
        "help": "Предметы в инвентаре NPC (override стандартной генерации).",
    },
}

NPC_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID конкретного NPC (type: \"npc\"). Используется в миссиях и спавне.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Отображаемое имя NPC.",
    },
    "class": {
        "label": "class",
        "type": "ref_list",
        "ref_type": "npc_class",
        "help": "ID npc_class для этого NPC. Обычно одна строка.",
    },
    "attitude": {
        "label": "attitude",
        "type": "string",
        "help": "Базовое отношение к игроку (alone, hostile, follower и т.п.).",
    },
    "mission": {
        "label": "mission",
        "type": "string",
        "help": "Тип миссии или mission_role (см. MISSIONS_JSON).",
    },
    "chat": {
        "label": "chat",
        "type": "ref_list",
        "ref_type": "talk_topic",
        "help": "ID начальной темы диалога (talk_topic). Обычно одна строка.",
    },
    "faction": {
        "label": "faction",
        "type": "string",
        "help": "ID фракции NPC (см. FACTIONS.md).",
    },
    "traits": {
        "label": "traits",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Дополнительные мутации/трейты конкретного NPC.",
    },
    "skills": {
        "label": "skills",
        "type": "json",
        "help": "Точные уровни навыков конкретного NPC.",
    },
    "inventory": {
        "label": "inventory",
        "type": "json",
        "help": "Определение предметов NPC (носит/держит).",
    },
    "raw": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Любые прочие поля NPC (opinion, personality, eoc и т.п.).",
    },
}

PROFESSION_FIELDS: Dict[str, Dict[str, Any]] = {
    "ident": {
        "label": "ident",
        "type": "string",
        "required": True,
        "help": "ID профессии (старый формат, 0.G). Используется в сценариях и при выборе персонажа.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя профессии для экрана создания персонажа.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание стартовой истории и набора профессии.",
    },
    "points": {
        "label": "points",
        "type": "int",
        "help": "Стоимость профессии в очках.",
    },
    "skills": {
        "label": "skills",
        "type": "json",
        "help": "Стартовые навыки профессии.",
    },
    "traits": {
        "label": "traits",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Стартовые трэйты / мутации профессии.",
    },
    "items": {
        "label": "items",
        "type": "json",
        "help": "Стартовое снаряжение профессии (одежда, инвентарь).",
    },
    "CBMs": {
        "label": "CBMs",
        "type": "list_string",
        "help": "ID вживлённых биоников, если есть.",
    },
}

SCENARIO_FIELDS: Dict[str, Dict[str, Any]] = {
    "ident": {
        "label": "ident",
        "type": "string",
        "required": True,
        "help": "ID сценария (type: \"scenario\"). Упоминается в сохранениях и модах.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя сценария в меню создания персонажа.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание стартовой ситуации сценария.",
    },
    "points": {
        "label": "points",
        "type": "int",
        "help": "Модификатор очков при выборе сценария.",
    },
    "allowed_locs": {
        "label": "allowed_locs",
        "type": "list_string",
        "help": "Разрешённые стартовые локации (shelter, evacuee, lmoe и т.п.).",
    },
    "professions": {
        "label": "professions",
        "type": "ref_list",
        "ref_type": "profession",
        "help": "Список профессий, доступных в этом сценарии (по ident).",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги сценария (LONE_START, SUR_START и т.п.).",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Прочие поля сценария (hobbies, traits, forced_traits и т.д.).",
    },
}

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "mutation": {
        "label": "Мутации (mutation)",
        "json_type": "mutation",
        "id_field": "id",
        "display_field": "id",
        "fields": MUTATION_FIELDS,
    },
    "effect_type": {
        "label": "Эффекты (effect_type)",
        "json_type": "effect_type",
        "id_field": "id",
        "display_field": "id",
        "fields": EFFECT_FIELDS,
    },
    "item_generic": {
        "label": "Предметы: GENERIC",
        "json_type": "GENERIC",
        "id_field": "id",
        "display_field": "name",
        "fields": ITEM_COMMON_FIELDS,
    },
    "item_armor": {
        "label": "Предметы: ARMOR",
        "json_type": "ARMOR",
        "id_field": "id",
        "display_field": "name",
        "fields": ITEM_COMMON_FIELDS,
    },
    "item_tool": {
        "label": "Предметы: TOOL",
        "json_type": "TOOL",
        "id_field": "id",
        "display_field": "name",
        "fields": ITEM_COMMON_FIELDS,
    },
    "magic_spell": {
        "label": "Магия: заклинания (SPELL)",
        "json_type": "SPELL",
        "id_field": "id",
        "display_field": "name",
        "fields": SPELL_FIELDS,
    },
    "talk_topic": {
        "label": "Диалоги (talk_topic)",
        "json_type": "talk_topic",
        "id_field": "id",
        "display_field": "id",
        "fields": TALK_TOPIC_FIELDS,
    },
    "npc_class": {
        "label": "Классы NPC (npc_class)",
        "json_type": "npc_class",
        "id_field": "id",
        "display_field": "id",
        "fields": NPC_CLASS_FIELDS,
    },
    "npc": {
        "label": "Конкретные NPC (npc)",
        "json_type": "npc",
        "id_field": "id",
        "display_field": "name",
        "fields": NPC_FIELDS,
    },
    "profession": {
        "label": "Профессии (profession)",
        "json_type": "profession",
        "id_field": "ident",
        "display_field": "name",
        "fields": PROFESSION_FIELDS,
    },
    "scenario": {
        "label": "Сценарии (scenario)",
        "json_type": "scenario",
        "id_field": "ident",
        "display_field": "name",
        "fields": SCENARIO_FIELDS,
    },
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CDDA 0.G JSON редактор модов")
        self.resize(1200, 800)

        self.project = ModProject()

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
        open_act = QAction("Открыть папку мода", self)
        open_act.triggered.connect(self._open_mod_folder)

        save_act = QAction("Сохранить всё", self)
        save_act.triggered.connect(self._save_all)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)

        toolbar = self.addToolBar("Основное")
        toolbar.addAction(open_act)
        toolbar.addAction(save_act)

    def _open_mod_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Выберите папку мода")
        if not path:
            return
        try:
            self.project.load_from_dir(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить мод: {e}")
            return
        self._rebuild_tree()
        self.statusBar().showMessage(f"Загружен мод из {path}", 5000)

    def _rebuild_tree(self) -> None:
        self.tree.clear()
        for schema_key, schema in SCHEMAS.items():
            objs = self.project.objects_by_schema.get(schema_key)
            if not objs:
                continue
            root = QTreeWidgetItem([schema.get("label", schema_key)])
            root.setData(0, Qt.UserRole, None)
            self.tree.addTopLevelItem(root)
            for obj in objs:
                item = QTreeWidgetItem([obj.label()])
                item.setData(0, Qt.UserRole, obj)
                root.addChild(item)
            root.setExpanded(True)

    def _on_tree_selection_changed(self, current: Optional[QTreeWidgetItem], _prev: Optional[QTreeWidgetItem]) -> None:
        if current is None:
            self.editor.set_object(None)
            return
        obj = current.data(0, Qt.UserRole)
        if isinstance(obj, ModObject):
            self.editor.set_object(obj)
        else:
            # категория
            self.editor.set_object(None)

    def _save_all(self) -> None:
        # сначала применяем изменения текущего объекта
        self.editor.apply_changes()

        errors: List[str] = []
        for path, objs in self.project.files.items():
            try:
                with path.open("w", encoding="utf-8") as f:
                    json.dump(objs, f, ensure_ascii=False, indent=2)
                    f.write("\n")
            except Exception as e:
                errors.append(f"{path}: {e}")

        if errors:
            QMessageBox.critical(
                self,
                "Ошибки при сохранении",
                "Некоторые файлы не удалось сохранить:\n\n" + "\n".join(errors),
            )
        else:
            QMessageBox.information(self, "Готово", "Все файлы сохранены.")


def main() -> None:
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
