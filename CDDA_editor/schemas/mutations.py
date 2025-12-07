# schemas/mutations.py
from typing import Dict, Any

MUTATION_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "Уникальный ID мутации/трэйта. Используется в prereqs, cancels, leads_to и ссылках.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "required": True,
        "help": "Имя мутации. Может быть строкой или объектом перевода { \"str\": \"...\" }.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание мутации, показывается игроку.",
    },
    "points": {
        "label": "points",
        "type": "int",
        "help": "Стоимость/бонус очков при создании персонажа.",
    },
    "visibility": {
        "label": "visibility",
        "type": "int",
        "help": "Насколько заметна мутация для NPC.",
    },
    "ugliness": {
        "label": "ugliness",
        "type": "int",
        "help": "Влияет на восприятие внешности NPC.",
    },
    "starting_trait": {
        "label": "starting_trait",
        "type": "bool",
        "help": "Можно ли выбрать на старте.",
    },
    "valid": {
        "label": "valid",
        "type": "bool",
        "help": "Можно ли получить в текущей версии игры обычными способами.",
    },
    "purifiable": {
        "label": "purifiable",
        "type": "bool",
        "help": "Удаляется ли очистителем/праймером.",
    },
    "player_display": {
        "label": "player_display",
        "type": "bool",
        "help": "Показывать ли в списке мутаций.",
    },
    "vanity": {
        "label": "vanity",
        "type": "bool",
        "help": "Чисто косметическая мутация.",
    },
    "types": {
        "label": "types",
        "type": "list_string",
        "help": "Типы мутации (для совместимости и порогов).",
    },
    "category": {
        "label": "category",
        "type": "list_string",
        "help": "Категории мутации (bird, chimera и т.п.).",
    },
    "allowed_category": {
        "label": "allowed_category",
        "type": "list_string",
        "help": "Категории, в которые можно эволюционировать.",
    },
    "prereqs": {
        "label": "prereqs",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Первая группа пререквизитов (достаточно одного).",
    },
    "prereqs2": {
        "label": "prereqs2",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Вторая группа пререквизитов (AND с первой).",
    },
    "threshreq": {
        "label": "threshreq",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Пороговые мутации (threshold).",
    },
    "cancels": {
        "label": "cancels",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Мутации, которые отменяются этой.",
    },
    "changes_to": {
        "label": "changes_to",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Во что может превратиться эта мутация.",
    },
    "leads_to": {
        "label": "leads_to",
        "type": "ref_list",
        "ref_type": "mutation",
        "help": "Какие мутации могут эволюционировать из этой.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги мутации (NIGHTVISION, STR_UP и прочие из JSON_FLAGS).",
    },
    "variants": {
        "label": "variants",
        "type": "json",
        "help": "Косметические варианты мутации. Игровая логика их почти не видит.",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "mutation": {
        "label": "Мутации (mutation)",
        "json_type": "mutation",
        "id_field": "id",
        "display_field": "id",
        "fields": MUTATION_FIELDS,
    }
}
