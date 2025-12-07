# schemas/effects.py
from typing import Dict, Any

EFFECT_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID эффекта (type: \"effect_type\").",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя эффекта (может быть списком по интенсивности).",
    },
    "desc": {
        "label": "desc",
        "type": "string_or_translation",
        "help": "Описание эффекта (также может зависеть от интенсивности).",
    },
    "max_intensity": {
        "label": "max_intensity",
        "type": "int",
        "help": "Максимальная интенсивность эффекта.",
    },
    "rating": {
        "label": "rating",
        "type": "string",
        "help": "good / bad / mixed и т.п. для отображения.",
    },
    "show_in_info": {
        "label": "show_in_info",
        "type": "bool",
        "help": "Показывать ли эффект в интерфейсе.",
    },
    "immune_flags": {
        "label": "immune_flags",
        "type": "list_string",
        "help": "Флаги, дающие иммунитет к эффекту.",
    },
    "resist_traits": {
        "label": "resist_traits",
        "type": "list_string",
        "help": "Мутации/трейты, уменьшающие эффект.",
    },
    "resist_effects": {
        "label": "resist_effects",
        "type": "list_string",
        "help": "Другие эффекты, дающие сопротивление.",
    },
    "removes_effects": {
        "label": "removes_effects",
        "type": "list_string",
        "help": "Эффекты, которые снимает данный.",
    },
    "blocks_effects": {
        "label": "blocks_effects",
        "type": "list_string",
        "help": "Эффекты, которые не могут действовать одновременно.",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Всё остальное: base_mods, scaling_mods, eocs и т.п.",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "effect_type": {
        "label": "Эффекты (effect_type)",
        "json_type": "effect_type",
        "id_field": "id",
        "display_field": "id",
        "fields": EFFECT_FIELDS,
    }
}
