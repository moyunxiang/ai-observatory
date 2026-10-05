"""Manual validation sheet: export prompts, user pastes ChatGPT answers, parse back.

Sheet format (plain text, so pasted markdown cannot break it):

    MODEL: <model name shown in ChatGPT UI>
    DATE: <YYYY-MM-DD>
    WEB_SEARCH: <yes/no>
    TEMPORARY_CHAT: <yes/no>

    === robot_vacuum ===
    CATEGORY: Robot Vacuum
    PROMPT: What are the best brands for Robot Vacuum? List 10 brands.
    --- paste answer below ---
    <answer text>

    === next_category ===
    ...
"""

import re

META_KEYS = ["MODEL", "DATE", "WEB_SEARCH", "TEMPORARY_CHAT"]
_SECTION_RE = re.compile(r"^=== (\S+) ===\s*$", re.MULTILINE)
_ANSWER_MARK = "--- paste answer below ---"

INSTRUCTIONS = """\
# Instructions
# 1. Fill in the 4 header fields below.
# 2. For EACH category: open a NEW ChatGPT Temporary Chat, paste the PROMPT line
#    (text after "PROMPT: ") exactly, copy the full answer, paste it under the marker.
# 3. Do not edit the === ... === / CATEGORY / PROMPT lines.
"""


def render_sheet(items: list[dict]) -> str:
    """items: [{category_id, category_name, prompt}]"""
    parts = [INSTRUCTIONS, *(f"{k}: " for k in META_KEYS), ""]
    for it in items:
        parts += [
            f"=== {it['category_id']} ===",
            f"CATEGORY: {it['category_name']}",
            f"PROMPT: {it['prompt']}",
            _ANSWER_MARK,
            "",
            "",
        ]
    return "\n".join(parts)


def parse_sheet(text: str) -> tuple[dict, list[dict]]:
    """Return (meta, records). Records with no pasted answer get response=''."""
    first = _SECTION_RE.search(text)
    header = text[: first.start()] if first else text
    meta = {}
    for line in header.splitlines():
        for k in META_KEYS:
            if line.startswith(f"{k}:"):
                meta[k.lower()] = line[len(k) + 1:].strip()

    records = []
    matches = list(_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        fields = {}
        for line in body.splitlines():
            for key in ("CATEGORY", "PROMPT"):
                if line.startswith(f"{key}:") and key.lower() not in fields:
                    fields[key.lower()] = line[len(key) + 1:].strip()
        answer = body.split(_ANSWER_MARK, 1)[1] if _ANSWER_MARK in body else ""
        records.append({
            "category_id": m.group(1),
            "category_name": fields.get("category", ""),
            "prompt": fields.get("prompt", ""),
            "response": answer.strip(),
        })
    return meta, records
