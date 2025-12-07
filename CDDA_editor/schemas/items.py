# schemas/items.py
from typing import Dict, Any

COMMON_ITEM_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID предмета.",
    },
    "copy-from": {
        "label": "copy-from",
        "type": "string",
        "help": "ID базового предмета для наследования.",
    },
    "abstract": {
        "label": "abstract",
        "type": "string",
        "help": "Определение-шаблон, не появляющееся в игре напрямую.",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя предмета.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание предмета.",
    },
    "weight": {
        "label": "weight",
        "type": "string",
        "help": "Вес (\"750 g\", \"2 kg\" или просто число для старых версий).",
    },
    "volume": {
        "label": "volume",
        "type": "string",
        "help": "Объём (\"1 L\", \"250 ml\").",
    },
    "price": {
        "label": "price",
        "type": "int",
        "help": "Цена в доапокалиптических деньгах (в цент-USD).",
    },
    "price_postapoc": {
        "label": "price_postapoc",
        "type": "int",
        "help": "Цена после апокалипсиса.",
    },
    "material": {
        "label": "material",
        "type": "list_string",
        "help": "Материалы предмета.",
    },
    "category": {
        "label": "category",
        "type": "string",
        "help": "Категория (armor, food, ammo и т.п.).",
    },
    "symbol": {
        "label": "symbol",
        "type": "string",
        "help": "Символ в консольном отображении.",
    },
    "color": {
        "label": "color",
        "type": "string",
        "help": "Цвет символа.",
    },
    "looks_like": {
        "label": "looks_like",
        "type": "string",
        "help": "ID предмета, внешний вид которого использовать по умолчанию.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги предмета (STURDY, WATERPROOF и т.п.).",
    },
    "extra": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Все остальные поля (use_action, qualities, armor_data, gun_data...).",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "item_generic": {
        "label": "Предметы: GENERIC",
        "json_type": "GENERIC",
        "id_field": "id",
        "display_field": "name",
        "fields": COMMON_ITEM_FIELDS,
    },
    "item_armor": {
        "label": "Предметы: ARMOR",
        "json_type": "ARMOR",
        "id_field": "id",
        "display_field": "name",
        "fields": COMMON_ITEM_FIELDS,
    },
    "item_tool": {
        "label": "Предметы: TOOL",
        "json_type": "TOOL",
        "id_field": "id",
        "display_field": "name",
        "fields": COMMON_ITEM_FIELDS,
    },
    "item_comestible": {
        "label": "Предметы: COMESTIBLE",
        "json_type": "COMESTIBLE",
        "id_field": "id",
        "display_field": "name",
        "fields": COMMON_ITEM_FIELDS,
    },
    "item_gun": {
        "label": "Предметы: GUN",
        "json_type": "GUN",
        "id_field": "id",
        "display_field": "name",
        "fields": COMMON_ITEM_FIELDS,
    },
}
