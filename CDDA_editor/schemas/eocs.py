# schemas/eocs.py
from typing import Dict, Any

EOC_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID effect_on_condition (type: \"effect_on_condition\").",
    },
    "EOC_TYPE": {
        "label": "EOC_TYPE",
        "type": "string",
        "help": "ACTIVATION, RECURRING, AVATAR_DEATH, NPC_DEATH, PREVENT_DEATH, EVENT.",
    },
    "recurrence": {
        "label": "recurrence",
        "type": "json",
        "help": "Как часто автоматически срабатывает (секунды или variable_object).",
    },
    "required_event": {
        "label": "required_event",
        "type": "json",
        "help": "Событие для EVENT EOC (cata_event).",
    },
    "condition": {
        "label": "condition",
        "type": "json",
        "help": "Условие (диалоговые условия: u_has_trait, npc_has_effect и т.п.).",
    },
    "deactivate_condition": {
        "label": "deactivate_condition",
        "type": "json",
        "help": "Условие деактивации рекуррентного EOC.",
    },
    "effect": {
        "label": "effect",
        "type": "json",
        "help": "Эффекты при true (диалоговые эффекты).",
    },
    "false_effect": {
        "label": "false_effect",
        "type": "json",
        "help": "Эффекты при false.",
    },
    "global": {
        "label": "global",
        "type": "bool",
        "help": "True: EOC глобален и прогоняется по всем NPC.",
    },
    "run_for_npcs": {
        "label": "run_for_npcs",
        "type": "bool",
        "help": "True: запускать и для NPC (только при global = true).",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "effect_on_condition": {
        "label": "Effect On Condition (effect_on_condition)",
        "json_type": "effect_on_condition",
        "id_field": "id",
        "display_field": "id",
        "fields": EOC_FIELDS,
    }
}
