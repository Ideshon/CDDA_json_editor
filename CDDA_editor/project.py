# project.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

from schemas import SCHEMAS


@dataclass
class ModObject:
    schema_key: str
    json_type: str
    file_path: Path
    data: Dict[str, Any]

    def get_id(self) -> str:
        schema = SCHEMAS[self.schema_key]
        id_field = schema["id_field"]
        val = self.data.get(id_field)
        if val is None:
            for k in ("id", "ident", "abstract"):
                if k in self.data:
                    val = self.data.get(k)
                    break
        return str(val) if val is not None else ""

    def get_display_name(self) -> str:
        schema = SCHEMAS[self.schema_key]
        disp = schema.get("display_field", "id")
        val = self.data.get(disp)
        if isinstance(val, dict):
            if "str" in val:
                return str(val["str"])
            for v in val.values():
                if isinstance(v, str):
                    return v
        if val is not None:
            return str(val)
        return self.get_id() or "<без имени>"

    def label(self) -> str:
        i = self.get_id()
        n = self.get_display_name()
        if i and n and i != n:
            return f"{i} — {n}"
        return i or n or "<объект>"


class ModProject:
    def __init__(self) -> None:
        self.root: Optional[Path] = None
        self.files: Dict[Path, List[Dict[str, Any]]] = {}
        self.objects_by_schema: Dict[str, List[ModObject]] = {}
        self.ids_by_type: Dict[str, set[str]] = {}
        self.dirty_files: set[Path] = set()

    def clear(self) -> None:
        self.root = None
        self.files.clear()
        self.objects_by_schema.clear()
        self.ids_by_type.clear()
        self.dirty_files.clear()

    def mark_dirty(self, path: Path) -> None:
        self.dirty_files.add(path)

    def load_from_dir(self, root_path: str) -> None:
        """Загружаем все json из папки."""
        self.clear()
        self.root = Path(root_path)

        for path in self.root.rglob("*.json"):
            self._load_single_json_file(path)

    def load_from_file(self, file_path: str) -> None:
        """Загружаем только один JSON-файл."""
        self.clear()
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        # корень считаем папкой файла
        self.root = path.parent
        self._load_single_json_file(path)

    def _load_single_json_file(self, path: Path) -> None:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json_load_relaxed(f.read())
        except Exception as e:
            print(f"[WARN] не могу прочитать {path}: {e}")
            return

        if isinstance(data, dict):
            objs = [data]
        elif isinstance(data, list):
            objs = data
        else:
            return

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
            mo = ModObject(schema_key=schema_key, json_type=json_type, file_path=path, data=obj)
            self.objects_by_schema.setdefault(schema_key, []).append(mo)
            self._register_id(mo)

    def _schema_for_type(self, json_type: str) -> Optional[str]:
        for key, schema in SCHEMAS.items():
            if schema["json_type"] == json_type:
                return key
        return None

    def _register_id(self, obj: ModObject) -> None:
        obj_id = obj.get_id()
        if not obj_id:
            return
        self.ids_by_type.setdefault(obj.json_type, set()).add(obj_id)

    def get_ids_for_json_type(self, json_type: str) -> List[str]:
        return sorted(self.ids_by_type.get(json_type, set()))

    def all_objects_for_schema(self, schema_key: str) -> List[ModObject]:
        return self.objects_by_schema.get(schema_key, [])

    # ---------- НОВОЕ: создание / удаление объектов ----------

    def create_object(self, schema_key: str) -> ModObject:
        """
        Создаёт новый объект указанной категории (schema_key).

        Объект попадает в файл:
            editor_<schema_key>.json

        - Если файла нет, он появится при сохранении.
        - Если есть, объект добавится в конец списка.
        """
        if self.root is None:
            raise RuntimeError("Неизвестен корень проекта. Сначала открой мод-папку или JSON-файл.")

        schema = SCHEMAS[schema_key]
        json_type = schema["json_type"]

        path = self.root / f"editor_{schema_key}.json"
        objs_list = self.files.get(path)
        if objs_list is None:
            objs_list = []
            self.files[path] = objs_list

        data: Dict[str, Any] = {"type": json_type}
        id_field = schema.get("id_field")
        if id_field:
            data.setdefault(id_field, "")

        objs_list.append(data)

        mo = ModObject(schema_key=schema_key, json_type=json_type, file_path=path, data=data)
        self.objects_by_schema.setdefault(schema_key, []).append(mo)

        # id пока пустой, в реестр добавлять смысла нет
        self.mark_dirty(path)
        return mo

    def delete_object(self, obj: ModObject) -> None:
        """
        Удаляет объект из:
        - списка объектов файла,
        - списка objects_by_schema,
        - реестра id-шников.
        """
        # 1) из файла
        objs_list = self.files.get(obj.file_path)
        if objs_list is not None:
            for i, d in enumerate(objs_list):
                if d is obj.data:   # по идентичности, а не по содержимому
                    del objs_list[i]
                    break

        # 2) из списка по схеме
        lst = self.objects_by_schema.get(obj.schema_key)
        if lst is not None:
            try:
                lst.remove(obj)
            except ValueError:
                pass

        # 3) из реестра id
        obj_id = obj.get_id()
        if obj_id:
            s = self.ids_by_type.get(obj.json_type)
            if s and obj_id in s:
                s.remove(obj_id)

        # 4) отметим файл как изменённый
        self.mark_dirty(obj.file_path)


# "расслабленный" JSON-парсер: убирает комментарии // и /* ... */
import json
import re
from typing import Any


def json_load_relaxed(text: str) -> Any:
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return json.loads(text)
