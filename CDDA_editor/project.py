# project.py
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional

try:
    from .json_io import json_dumps_pretty, json_load_relaxed
    from .schemas import SCHEMAS
except ImportError:
    from json_io import json_dumps_pretty, json_load_relaxed
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


@dataclass(frozen=True)
class LoadWarning:
    path: Path
    message: str


@dataclass(frozen=True)
class ObjectReference:
    source: ModObject
    field_name: str
    target_type: str
    target_id: str
    target: Optional[ModObject]


@dataclass(frozen=True)
class RenameResult:
    old_id: str
    new_id: str
    updated_references: int


@dataclass(frozen=True)
class BackupInfo:
    source_path: Path
    backup_path: Path
    kind: str
    created_at_utc: str


@dataclass(frozen=True)
class ProjectEditState:
    root: Optional[Path]
    files: Dict[Path, List[Dict[str, Any]]]
    dirty_files: frozenset[Path]


class ModProject:
    def __init__(self) -> None:
        self.root: Optional[Path] = None
        self.files: Dict[Path, List[Dict[str, Any]]] = {}
        self.objects_by_schema: Dict[str, List[ModObject]] = {}
        self.ids_by_type: Dict[str, set[str]] = {}
        self.dirty_files: set[Path] = set()
        self.load_warnings: List[LoadWarning] = []
        self.object_index: Dict[tuple[str, str], ModObject] = {}
        self.objects_by_file: Dict[Path, List[ModObject]] = {}
        self._outgoing_references: Dict[int, List[ObjectReference]] = {}
        self._incoming_references: Dict[int, List[ObjectReference]] = {}
        self.current_backup: Optional[BackupInfo] = None

    def clear(self) -> None:
        self.root = None
        self.files.clear()
        self.objects_by_schema.clear()
        self.ids_by_type.clear()
        self.dirty_files.clear()
        self.load_warnings.clear()
        self.object_index.clear()
        self.objects_by_file.clear()
        self._outgoing_references.clear()
        self._incoming_references.clear()
        self.current_backup = None

    def mark_dirty(self, path: Path) -> None:
        self.dirty_files.add(path)

    def capture_edit_state(self) -> ProjectEditState:
        return ProjectEditState(
            root=self.root,
            files=deepcopy(self.files),
            dirty_files=frozenset(self.dirty_files),
        )

    def restore_edit_state(self, state: ProjectEditState) -> None:
        self.root = state.root
        self.files = deepcopy(state.files)
        self.dirty_files = set(state.dirty_files)
        self.objects_by_schema.clear()
        self.ids_by_type.clear()
        self.object_index.clear()
        self.objects_by_file.clear()
        self._outgoing_references.clear()
        self._incoming_references.clear()

        for path, objects in self.files.items():
            for obj in objects:
                if not isinstance(obj, dict):
                    continue
                json_type = obj.get("type")
                if not isinstance(json_type, str):
                    continue
                schema_key = self._schema_for_type(json_type)
                if not schema_key:
                    continue
                mod_object = ModObject(
                    schema_key=schema_key,
                    json_type=json_type,
                    file_path=path,
                    data=obj,
                )
                self.objects_by_schema.setdefault(schema_key, []).append(mod_object)
                self._register_id(mod_object)

        self.rebuild_indexes()

    def save_file(self, path: Path) -> Path:
        objs = self.files.get(path)
        if objs is None:
            raise FileNotFoundError(f"{path}: файл не найден в проекте")

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(json_dumps_pretty(objs))
            f.write("\n")

        self.dirty_files.discard(path)
        return path

    def save_dirty_files(self) -> List[Path]:
        written: List[Path] = []
        for path in sorted(self.dirty_files):
            written.append(self.save_file(path))
        return written

    def save_all_files(self) -> List[Path]:
        written: List[Path] = []
        for path in list(self.files.keys()):
            written.append(self.save_file(path))
        return written

    def load_from_dir(self, root_path: str) -> None:
        """Загружаем все json из папки."""
        self.clear()
        self.root = Path(root_path)

        for path in self.root.rglob("*.json"):
            if ".cdda_mod_editor_backups" in path.parts:
                continue
            self._load_single_json_file(path)
        self.rebuild_indexes()

    def load_from_file(self, file_path: str) -> None:
        """Загружаем только один JSON-файл."""
        self.clear()
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        # корень считаем папкой файла
        self.root = path.parent
        self._load_single_json_file(path)
        self.rebuild_indexes()

    def create_open_backup(self, source_path: Path) -> BackupInfo:
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(source_path)

        if source_path.is_dir():
            kind = "directory"
        elif source_path.is_file():
            kind = "file"
        else:
            raise ValueError(f"{source_path}: можно создать бэкап только папки или файла")

        backup_path = self._next_backup_path(source_path)
        if kind == "directory":
            shutil.copytree(
                source_path,
                backup_path,
                ignore=shutil.ignore_patterns(".cdda_mod_editor_backups"),
            )
        else:
            backup_path.mkdir(parents=True, exist_ok=False)
            shutil.copy2(source_path, backup_path / source_path.name)

        backup = BackupInfo(
            source_path=source_path,
            backup_path=backup_path,
            kind=kind,
            created_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self.current_backup = backup
        return backup

    def restore_current_backup(self) -> BackupInfo:
        backup = self.current_backup
        if backup is None:
            raise RuntimeError("Нет текущего бэкапа для восстановления")
        if not backup.backup_path.exists():
            raise FileNotFoundError(f"{backup.backup_path}: бэкап не найден")

        if backup.kind == "directory":
            self._restore_directory_backup(backup)
            self.load_from_dir(str(backup.source_path))
        elif backup.kind == "file":
            self._restore_file_backup(backup)
            self.load_from_file(str(backup.source_path))
        else:
            raise ValueError(f"Неизвестный тип бэкапа: {backup.kind}")

        self.current_backup = backup
        return backup

    def create_autobackup(self) -> BackupInfo:
        current = self.current_backup
        if current is None:
            raise RuntimeError("Нет открытого проекта для автобэкапа")

        backup_path = self._next_backup_path(current.source_path)
        if current.kind == "directory":
            if current.source_path.exists():
                shutil.copytree(
                    current.source_path,
                    backup_path,
                    ignore=shutil.ignore_patterns(".cdda_mod_editor_backups"),
                )
            else:
                backup_path.mkdir(parents=True, exist_ok=False)
            self._write_project_files_to_directory(backup_path, current.source_path)
        elif current.kind == "file":
            backup_path.mkdir(parents=True, exist_ok=False)
            self._write_project_file_backup(backup_path, current.source_path)
        else:
            raise ValueError(f"Неизвестный тип бэкапа: {current.kind}")

        backup = BackupInfo(
            source_path=current.source_path,
            backup_path=backup_path,
            kind=current.kind,
            created_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self.current_backup = backup
        return backup

    def _write_project_files_to_directory(self, backup_path: Path, source_root: Path) -> None:
        for path, objects in self.files.items():
            try:
                relative_path = path.relative_to(source_root)
            except ValueError:
                relative_path = Path(path.name)
            target_path = backup_path / relative_path
            self._write_objects_to_path(target_path, objects)

    def _write_project_file_backup(self, backup_path: Path, source_file: Path) -> None:
        objects = self.files.get(source_file)
        target_path = backup_path / source_file.name
        if objects is None:
            if source_file.exists():
                shutil.copy2(source_file, target_path)
                return
            raise FileNotFoundError(f"{source_file}: файл не найден в проекте")
        self._write_objects_to_path(target_path, objects)

    def _write_objects_to_path(self, path: Path, objects: List[Dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(json_dumps_pretty(objects))
            f.write("\n")

    def _restore_directory_backup(self, backup: BackupInfo) -> None:
        if backup.source_path.exists():
            if not backup.source_path.is_dir():
                raise ValueError(f"{backup.source_path}: ожидалась папка мода")
            shutil.rmtree(backup.source_path)
        shutil.copytree(backup.backup_path, backup.source_path)

    def _restore_file_backup(self, backup: BackupInfo) -> None:
        backup_file = backup.backup_path / backup.source_path.name
        if not backup_file.is_file():
            raise FileNotFoundError(f"{backup_file}: файл бэкапа не найден")
        if backup.source_path.exists() and backup.source_path.is_dir():
            raise ValueError(f"{backup.source_path}: ожидался JSON-файл, найдена папка")
        backup.source_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, backup.source_path)

    def _next_backup_path(self, source_path: Path) -> Path:
        backup_root = source_path.parent / ".cdda_mod_editor_backups"
        backup_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        base_name = f"{source_path.stem}_{timestamp}"
        candidate = backup_root / base_name
        suffix = 1
        while candidate.exists():
            candidate = backup_root / f"{base_name}_{suffix}"
            suffix += 1
        return candidate

    def _load_single_json_file(self, path: Path) -> None:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json_load_relaxed(f.read())
        except Exception as e:
            self._record_load_warning(path, e)
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

    def _record_load_warning(self, path: Path, error: Exception) -> None:
        message = f"не могу прочитать {path}: {error}"
        self.load_warnings.append(LoadWarning(path=path, message=message))
        print(f"[WARN] {message}")

    def load_warning_summary(self, max_items: int = 8) -> str:
        if not self.load_warnings:
            return ""

        shown = self.load_warnings[:max_items]
        lines = [
            f"Не удалось прочитать JSON-файлы: {len(self.load_warnings)}.",
            "",
        ]
        lines.extend(f"- {warning.path.name}: {warning.message}" for warning in shown)

        hidden_count = len(self.load_warnings) - len(shown)
        if hidden_count > 0:
            lines.append(f"- ... ещё {hidden_count}")

        return "\n".join(lines)

    def rebuild_indexes(self) -> None:
        self.object_index.clear()
        self.objects_by_file.clear()
        self._outgoing_references.clear()
        self._incoming_references.clear()

        for objects in self.objects_by_schema.values():
            for obj in objects:
                self.objects_by_file.setdefault(obj.file_path, []).append(obj)
                obj_id = obj.get_id()
                if obj_id:
                    self.object_index[(obj.json_type, obj_id)] = obj

        for objects in self.objects_by_schema.values():
            for obj in objects:
                for reference in self._iter_object_references(obj):
                    self._outgoing_references.setdefault(id(obj), []).append(reference)
                    if reference.target is not None:
                        self._incoming_references.setdefault(id(reference.target), []).append(reference)

    def get_object_by_type_id(self, json_type: str, obj_id: str) -> Optional[ModObject]:
        return self.object_index.get((json_type, obj_id))

    def objects_for_file(self, path: Path) -> List[ModObject]:
        return list(self.objects_by_file.get(path, []))

    def move_objects_to_file(
        self,
        objects: List[ModObject],
        target_path: Path,
    ) -> List[ModObject]:
        if self.root is None:
            raise RuntimeError("Неизвестен корень проекта. Сначала открой мод-папку или JSON-файл.")

        unique_objects: List[ModObject] = []
        seen: set[int] = set()
        for obj in objects:
            obj_marker = id(obj)
            if obj_marker in seen:
                continue
            seen.add(obj_marker)
            unique_objects.append(obj)

        if not unique_objects:
            return []

        target_path = Path(target_path)
        target_objects = self.files.setdefault(target_path, [])
        moved: List[ModObject] = []

        for obj in unique_objects:
            source_path = obj.file_path
            if source_path == target_path:
                continue

            source_objects = self.files.get(source_path)
            if source_objects is None:
                raise FileNotFoundError(f"{source_path}: файл не найден в проекте")

            for index, data in enumerate(source_objects):
                if data is obj.data:
                    del source_objects[index]
                    break
            else:
                raise ValueError(f"{obj.label()}: объект не найден в исходном файле")

            target_objects.append(obj.data)
            obj.file_path = target_path
            self.mark_dirty(source_path)
            self.mark_dirty(target_path)
            moved.append(obj)

        self.rebuild_indexes()
        return moved

    def rename_object(
        self,
        obj: ModObject,
        new_id: str,
        update_references: bool = False,
    ) -> RenameResult:
        new_id = new_id.strip()
        if not new_id:
            raise ValueError("Новый id не может быть пустым")

        schema = SCHEMAS[obj.schema_key]
        id_field = schema["id_field"]
        old_id = obj.get_id()
        if not old_id:
            raise ValueError("У объекта нет id для переименования")
        if old_id == new_id:
            return RenameResult(old_id=old_id, new_id=new_id, updated_references=0)

        existing = self.get_object_by_type_id(obj.json_type, new_id)
        if existing is not None and existing is not obj:
            raise ValueError(f"{obj.json_type}/{new_id}: объект с таким id уже существует")

        incoming = self.incoming_references_for(obj)
        updated_references = 0

        obj.data[id_field] = new_id
        self.mark_dirty(obj.file_path)

        if update_references:
            for reference in incoming:
                updated_references += self._replace_reference_value(
                    reference.source,
                    reference.field_name,
                    old_id,
                    new_id,
                )

        self._rebuild_ids_by_type()
        self.rebuild_indexes()
        return RenameResult(
            old_id=old_id,
            new_id=new_id,
            updated_references=updated_references,
        )

    def _replace_reference_value(
        self,
        source: ModObject,
        field_name: str,
        old_id: str,
        new_id: str,
    ) -> int:
        value = source.data.get(field_name)
        updated = 0

        if isinstance(value, str):
            if value == old_id:
                source.data[field_name] = new_id
                updated = 1
        elif isinstance(value, list):
            new_values: List[Any] = []
            for item in value:
                if item == old_id:
                    new_values.append(new_id)
                    updated += 1
                else:
                    new_values.append(item)
            if updated:
                source.data[field_name] = new_values

        if updated:
            self.mark_dirty(source.file_path)
        return updated

    def relative_object_file(self, obj: ModObject) -> Path:
        if self.root is None:
            return obj.file_path
        try:
            return obj.file_path.relative_to(self.root)
        except ValueError:
            return obj.file_path

    def outgoing_references_for(self, obj: ModObject) -> List[ObjectReference]:
        return list(self._outgoing_references.get(id(obj), []))

    def incoming_references_for(self, obj: ModObject) -> List[ObjectReference]:
        return list(self._incoming_references.get(id(obj), []))

    def _iter_object_references(self, obj: ModObject) -> List[ObjectReference]:
        schema = SCHEMAS.get(obj.schema_key, {})
        fields = schema.get("fields", {})
        references: List[ObjectReference] = []

        for field_name, meta in fields.items():
            if meta.get("type") != "ref_list":
                continue

            target_type = self._json_type_for_ref_type(str(meta.get("ref_type", "")))
            if not target_type:
                continue

            for target_id in self._reference_values(obj.data.get(field_name)):
                target = self.get_object_by_type_id(target_type, target_id)
                references.append(
                    ObjectReference(
                        source=obj,
                        field_name=field_name,
                        target_type=target_type,
                        target_id=target_id,
                        target=target,
                    )
                )

        return references

    def _json_type_for_ref_type(self, ref_type: str) -> str:
        if not ref_type:
            return ""
        if ref_type in SCHEMAS:
            return str(SCHEMAS[ref_type]["json_type"])
        return ref_type

    def _reference_values(self, value: Any) -> List[str]:
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, list):
            return [item for item in value if isinstance(item, str) and item]
        return []

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

    def _rebuild_ids_by_type(self) -> None:
        self.ids_by_type.clear()
        for objects in self.objects_by_schema.values():
            for obj in objects:
                self._register_id(obj)

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
        self.objects_by_file.setdefault(path, []).append(mo)

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
        self.rebuild_indexes()

