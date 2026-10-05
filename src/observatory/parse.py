"""Extract a ranked brand list from a free-text LLM answer.

Handles typical list formats:
    1. Nike            1) **Nike** - known for ...      - Nike: ...
    * Nike (USA)       Nike — description
If the answer has no list lines, falls back to splitting a single line on commas.
"""

import re

_LIST_PREFIX_RE = re.compile(r"^\s*(?:\d+\s*[.)\]:-]|[-*•])\s*")
_DESC_SPLIT_RE = re.compile(r"\s+[-–—]\s+|:\s+|\s*\(")


def _clean_item(line: str) -> str:
    s = _LIST_PREFIX_RE.sub("", line, count=1)
    s = s.replace("**", "").replace("__", "").strip()
    s = _DESC_SPLIT_RE.split(s, maxsplit=1)[0]  # drop " - description", ": ...", "(...)"
    return s.strip(" .,;*")


def parse_brand_list(text: str) -> list[str]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    list_lines = [ln for ln in lines if _LIST_PREFIX_RE.match(ln)]
    if list_lines:
        items = [_clean_item(ln) for ln in list_lines]
    elif len(lines) == 1:
        items = [p.strip(" .") for p in lines[0].split(",")]
    else:
        items = [_clean_item(ln) for ln in lines]
    return [i for i in items if i]
