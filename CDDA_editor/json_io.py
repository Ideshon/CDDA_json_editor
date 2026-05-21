from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any


def json_load_relaxed(text: str) -> Any:
    cleaned = _remove_trailing_commas(_strip_json_comments(text.lstrip("\ufeff")))

    try:
        return json.loads(cleaned)
    except JSONDecodeError as original_error:
        for candidate in _json_recovery_candidates(cleaned):
            try:
                return json.loads(candidate)
            except JSONDecodeError:
                continue
        raise original_error


def json_dumps_pretty(val: Any) -> str:
    return json.dumps(val, ensure_ascii=False, indent=2)


def _json_recovery_candidates(text: str) -> list[str]:
    stripped = text.strip()
    candidates: list[str] = []

    if stripped.startswith("{") and not stripped.endswith("}"):
        candidates.append(f"[{_repair_top_level_object_stream(stripped)}]")

    if stripped.startswith("{"):
        candidates.append(f"[{stripped}]")
        repaired = _repair_top_level_object_stream(stripped)
        if repaired != stripped:
            candidates.append(f"[{repaired}]")

    return candidates


def _strip_json_comments(text: str) -> str:
    result: list[str] = []
    i = 0
    in_string = False
    escaped = False

    while i < len(text):
        char = text[i]
        next_char = text[i + 1] if i + 1 < len(text) else ""

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            i += 1
            continue

        if char == "/" and next_char == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue

        if char == "/" and next_char == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2 if i + 1 < len(text) else 0
            continue

        result.append(char)
        i += 1

    return "".join(result)


def _remove_trailing_commas(text: str) -> str:
    result: list[str] = []
    i = 0
    in_string = False
    escaped = False

    while i < len(text):
        char = text[i]

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            i += 1
            continue

        if char == ",":
            j = i + 1
            while j < len(text) and text[j].isspace():
                j += 1
            if j < len(text) and text[j] in "]}":
                i += 1
                continue

        result.append(char)
        i += 1

    return "".join(result)


def _repair_top_level_object_stream(text: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    depth = 0
    previous_significant = ""

    for line in lines:
        stripped = line.lstrip()
        starts_next_object = stripped.startswith("{")

        if depth == 1 and starts_next_object and previous_significant == "}":
            indent = line[: len(line) - len(stripped)]
            result.append(indent + "},")
            depth -= 1

        result.append(line)
        depth += _brace_delta(line)

        significant = line.rstrip()
        if significant:
            previous_significant = significant[-1]

    return "\n".join(result)


def _brace_delta(line: str) -> int:
    depth = 0
    in_string = False
    escaped = False

    for char in line:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1

    return depth
