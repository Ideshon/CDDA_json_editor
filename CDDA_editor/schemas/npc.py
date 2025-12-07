# schemas/npc.py
from typing import Dict, Any

NPC_CLASS_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID npc_class (type: \"npc_class\").",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя/название класса NPC.",
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
        "help": "Мутации/трейты класса.",
    },
    "skills": {
        "label": "skills",
        "type": "json",
        "help": "Навыки NPC (skill → уровень).",
    },
    "spells": {
        "label": "spells",
        "type": "ref_list",
        "ref_type": "magic_spell",
        "help": "Заклинания NPC.",
    },
    "worn_override": {
        "label": "worn_override",
        "type": "json",
        "help": "Гарантированная одежда.",
    },
    "carry_override": {
        "label": "carry_override",
        "type": "json",
        "help": "Гарантированный инвентарь.",
    },
}

NPC_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID конкретного NPC (type: \"npc\").",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя NPC.",
    },
    "class": {
        "label": "class",
        "type": "ref_list",
        "ref_type": "npc_class",
        "help": "Класс NPC (обычно один ID).",
    },
    "attitude": {
        "label": "attitude",
        "type": "string",
        "help": "Базовое отношение к игроку (hostile, follower, neutral...).",
    },
    "mission": {
        "label": "mission",
        "type": "string",
        "help": "Роль в миссиях / тип миссии.",
    },
    "chat": {
        "label": "chat",
        "type": "ref_list",
        "ref_type": "talk_topic",
        "help": "Стартовый talk_topic.",
    },
    "faction": {
        "label": "faction",
        "type": "string",
        "help": "Фракция NPC.",
    },
    "traits": {
        "label": "traits",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Дополнительные трэйты конкретного NPC.",
    },
    "skills": {
        "label": "skills",
        "type": "json",
        "help": "Точные уровни навыков.",
    },
    "inventory": {
        "label": "inventory",
        "type": "json",
        "help": "Инвентарь NPC.",
    },
    "raw": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Остальное (opinion, personality, eoc_on_talk и пр.).",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
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
}
