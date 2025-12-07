# schemas/missions.py
from typing import Dict, Any

MISSION_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID миссии (type: \"mission_definition\").",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Название миссии.",
    },
    "goal": {
        "label": "goal",
        "type": "string",
        "help": "Цель миссии (MISSION_GOAL_... из MISSIONS_JSON).",
    },
    "difficulty": {
        "label": "difficulty",
        "type": "int",
        "help": "Сложность миссии (для интерфейса и баланса).",
    },
    "value": {
        "label": "value",
        "type": "int",
        "help": "Награда/ценность миссии.",
    },
    "origins": {
        "label": "origins",
        "type": "list_string",
        "help": "Откуда берётся миссия (ORIGIN_OPENER_NPC и т.п.).",
    },
    "dialogue": {
        "label": "dialogue",
        "type": "json",
        "help": "Тексты диалога по этапам миссии.",
    },
    "place": {
        "label": "place",
        "type": "json",
        "help": "Условия размещения цели (om_terrain, om_terrain_match...).",
    },
    "followup": {
        "label": "followup",
        "type": "string",
        "help": "ID следующей миссии по цепочке.",
    },
    "deadline_low": {
        "label": "deadline_low",
        "type": "int",
        "help": "Минимальный срок выполнения (в минутах игрового времени).",
    },
    "deadline_high": {
        "label": "deadline_high",
        "type": "int",
        "help": "Максимальный срок выполнения.",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Остальное: monster_kill, item, effects_on_condition и т.д.",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "mission_definition": {
        "label": "Миссии (mission_definition)",
        "json_type": "mission_definition",
        "id_field": "id",
        "display_field": "name",
        "fields": MISSION_FIELDS,
    }
}
