# schemas/__init__.py
from typing import Dict, Any

from . import (
    mutations,
    effects,
    items,
    magic,
    dialogue,
    npc,
    monsters,
    missions,
    eocs,
    meta,
)

SCHEMAS: Dict[str, Dict[str, Any]] = {}

for module in (
    mutations,
    effects,
    items,
    magic,
    dialogue,
    npc,
    monsters,
    missions,
    eocs,
    meta,
):
    SCHEMAS.update(module.SCHEMA)