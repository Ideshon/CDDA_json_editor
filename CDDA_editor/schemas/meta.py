# schemas/meta.py
from typing import Dict, Any

PROFESSION_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "ident",
        "type": "string",
        "required": True,
        "help": "ID профессии (0.G формат).",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Название профессии.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание профессии.",
    },
    "points": {
        "label": "points",
        "type": "int",
        "help": "Стоимость профессии в очках.",
    },
    "skills": {
        "label": "skills",
        "type": "json",
        "help": "Стартовые навыки.",
    },
    "traits": {
        "label": "traits",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Стартовые черты.",
    },
    "items": {
        "label": "items",
        "type": "json",
        "help": "Стартовое снаряжение.",
    },
    "CBMs": {
        "label": "CBMs",
        "type": "list_string",
        "help": "Список ID биоников.",
    },
}

SCENARIO_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "ident",
        "type": "string",
        "required": True,
        "help": "ID сценария.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя сценария.",
    },
    "start_name": {
        "label": "start_name",
        "type": "string_or_translation",
        "help": "Стартовое имя?.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание стартовой ситуации.",
    },
    "points": {
        "label": "points",
        "type": "int",
        "help": "Модификатор очков.",
    },
    "allowed_locs": {
        "label": "allowed_locs",
        "type": "list_string",
        "help": "Разрешённые стартовые локации.",
    },
    "professions": {
        "label": "professions",
        "type": "ref_list",
        "ref_type": "profession",
        "help": "Профессии, доступные в этом сценарии.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги сценария.",
    },
    "traits": {
        "label": "traits",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Стартовые черты.",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Остальное (hobbies, forced_traits...).",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
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
