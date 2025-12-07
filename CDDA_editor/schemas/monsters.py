# schemas/monsters.py
from typing import Dict, Any

MONSTER_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID монстра (type: \"MONSTER\"). Обычно вида mon_XXX.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя монстра (может иметь множественное число и контекст).",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание монстра.",
    },
    "hp": {
        "label": "hp",
        "type": "int",
        "help": "Очки здоровья.",
    },
    "speed": {
        "label": "speed",
        "type": "int",
        "help": "Скорость (100 = человек).",
    },
    "volume": {
        "label": "volume",
        "type": "string",
        "help": "Объём тела (\"35 L\", \"1500 ml\").",
    },
    "weight": {
        "label": "weight",
        "type": "string",
        "help": "Вес (\"75 kg\", \"7500 g\").",
    },
    "symbol": {
        "label": "symbol",
        "type": "string",
        "help": "Символ монстра в консольной версии.",
    },
    "color": {
        "label": "color",
        "type": "string",
        "help": "Цвет символа.",
    },
    "default_faction": {
        "label": "default_faction",
        "type": "string",
        "help": "Фракция монстра.",
    },
    "bodytype": {
        "label": "bodytype",
        "type": "string",
        "help": "Тип тела (human, dog, bird, insect...).",
    },
    "categories": {
        "label": "categories",
        "type": "list_string",
        "help": "Категории (NULL, CLASSIC, WILDLIFE и т.п.).",
    },
    "species": {
        "label": "species",
        "type": "list_string",
        "help": "Вид (HUMAN, ZOMBIE, ROBOT и т.д.).",
    },
    "material": {
        "label": "material",
        "type": "list_string",
        "help": "Материалы тела (flesh, steel...).",
    },
    "aggression": {
        "label": "aggression",
        "type": "int",
        "help": "Базовая агрессия.",
    },
    "morale": {
        "label": "morale",
        "type": "int",
        "help": "Базовая мораль (при низкой монстр убегает).",
    },
    "melee_skill": {
        "label": "melee_skill",
        "type": "int",
        "help": "Навык ближнего боя монстра.",
    },
    "dodge": {
        "label": "dodge",
        "type": "int",
        "help": "Навык уклонения монстра.",
    },
    "melee_damage": {
        "label": "melee_damage",
        "type": "json",
        "help": "Список инстансов урона ближнего боя.",
    },
    "armor": {
        "label": "armor",
        "type": "json",
        "help": "Броня по типам урона.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги монстра (SEES, HEARS, GRABS, NO_BREATHE...).",
    },
    "death_drops": {
        "label": "death_drops",
        "type": "json",
        "help": "Loot при смерти (item_groups).",
    },
    "death_function": {
        "label": "death_function",
        "type": "list_string",
        "help": "Специальные функции при смерти (NORMAL, EXPLODE и т.п.).",
    },
    "special_attacks": {
        "label": "special_attacks",
        "type": "json",
        "help": "Особые атаки монстра (MONSTER_ATTACK).",
    },
    "upgrades": {
        "label": "upgrades",
        "type": "json",
        "help": "Эволюция монстра во времени.",
    },
    "reproduction": {
        "label": "reproduction",
        "type": "json",
        "help": "Параметры размножения монстра.",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Все остальные поля из MONSTERS.md.",
    },
}

MONSTERGROUP_FIELDS: Dict[str, Dict[str, Any]] = {
    "name": {
        "label": "name",
        "type": "string",
        "required": True,
        "help": "ID группы монстров (type: \"monstergroup\").",
    },
    "default": {
        "label": "default",
        "type": "string",
        "help": "Монстр по умолчанию для этой группы.",
    },
    "monsters": {
        "label": "monsters",
        "type": "json",
        "help": "Список монстров (monster, freq, cost_multiplier, pack_size...).",
    },
    "replace_monster": {
        "label": "replace_monster",
        "type": "json",
        "help": "Правила замены монстров.",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Остальные поля монстергруппы.",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "monster": {
        "label": "Монстры (MONSTER)",
        "json_type": "MONSTER",
        "id_field": "id",
        "display_field": "name",
        "fields": MONSTER_FIELDS,
    },
    "monstergroup": {
        "label": "Группы монстров (monstergroup)",
        "json_type": "monstergroup",
        "id_field": "name",
        "display_field": "name",
        "fields": MONSTERGROUP_FIELDS,
    },
}
