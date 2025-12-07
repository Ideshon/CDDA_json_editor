# schemas/magic.py
from typing import Dict, Any

SPELL_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID заклинания (type: \"SPELL\").",
    },
    "name": {
        "label": "name",
        "type": "string_or_translation",
        "help": "Имя заклинания.",
    },
    "description": {
        "label": "description",
        "type": "string_or_translation",
        "help": "Описание заклинания.",
    },
    "effect": {
        "label": "effect",
        "type": "string",
        "help": "Тип эффекта (attack, targeted, summon, teleport и т.п.).",
    },
    "effect_str": {
        "label": "effect_str",
        "type": "string",
        "help": "Доп. параметр для эффекта (ID монстра, эффекта, поля и т.д.).",
    },
    "spell_class": {
        "label": "spell_class",
        "type": "string",
        "help": "Класс заклинания / школа магии.",
    },
    "valid_targets": {
        "label": "valid_targets",
        "type": "list_string",
        "help": "Типы целей: self, ally, hostile, ground и т.п.",
    },
    "min_range": {
        "label": "min_range",
        "type": "int",
        "help": "Минимальная дистанция.",
    },
    "max_range": {
        "label": "max_range",
        "type": "int",
        "help": "Максимальная дистанция.",
    },
    "min_damage": {
        "label": "min_damage",
        "type": "int",
        "help": "Урон/эффект на 0 уровне.",
    },
    "max_damage": {
        "label": "max_damage",
        "type": "int",
        "help": "Урон/эффект на максимальном уровне.",
    },
    "damage_type": {
        "label": "damage_type",
        "type": "string",
        "help": "Тип урона: bash, cut, heat и т.п.",
    },
    "base_energy_cost": {
        "label": "base_energy_cost",
        "type": "int",
        "help": "Базовая стоимость ресурса.",
    },
    "energy_source": {
        "label": "energy_source",
        "type": "string",
        "help": "mana, stamina, bionic, hp и прочее.",
    },
    "difficulty": {
        "label": "difficulty",
        "type": "int",
        "help": "Сложность изучения.",
    },
    "max_level": {
        "label": "max_level",
        "type": "int",
        "help": "Максимальный уровень заклинания.",
    },
    "flags": {
        "label": "flags",
        "type": "flags",
        "help": "Флаги SPELL (VERBAL, SOMATIC, NO_PROJECTILE и т.п.).",
    },
    "extra_effects": {
        "label": "extra_effects",
        "type": "json",
        "help": "Дополнительные эффекты при касте.",
    },
    "raw": {
        "label": "extra (raw JSON)",
        "type": "json",
        "help": "Всё, что не засунуто в форму (field_id, sound_id, learn_spells...).",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "magic_spell": {
        "label": "Магия: заклинания (SPELL)",
        "json_type": "SPELL",
        "id_field": "id",
        "display_field": "name",
        "fields": SPELL_FIELDS,
    }
}
