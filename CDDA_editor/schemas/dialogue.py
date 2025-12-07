# schemas/dialogue.py
from typing import Dict, Any

TALK_TOPIC_FIELDS: Dict[str, Dict[str, Any]] = {
    "id": {
        "label": "id",
        "type": "string",
        "required": True,
        "help": "ID темы диалога (type: \"talk_topic\").",
    },
    "dynamic_line": {
        "label": "dynamic_line",
        "type": "json",
        "help": "Текст/структура фразы NPC (условия, переменные и т.д.).",
    },
    "responses": {
        "label": "responses",
        "type": "json",
        "help": "Список ответов игрока (text, topic, trial, effect...).",
    },
    "speaker_effect": {
        "label": "speaker_effect",
        "type": "json",
        "help": "effect_on_condition, вызываемый при реплике.",
    },
    "repeat_responses": {
        "label": "repeat_responses",
        "type": "json",
        "help": "Ответы при повторном входе в тему.",
    },
}

SCHEMA: Dict[str, Dict[str, Any]] = {
    "talk_topic": {
        "label": "Диалоги (talk_topic)",
        "json_type": "talk_topic",
        "id_field": "id",
        "display_field": "id",
        "fields": TALK_TOPIC_FIELDS,
    }
}
