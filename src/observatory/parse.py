"""Extract a ranked brand list from a free-text LLM answer.

Handles typical list formats:
    1. Nike            1) **Nike** - known for ...      - Nike: ...
    **1. Nike**        ### 1. Nike                      * Nike (USA)
If the answer has top-level numbered items, only those are used, so indented
sub-bullets ("- Best for: ...") and trailing notes/disclaimers are ignored.
Otherwise top-level bullets are used; if there are no list lines at all, a single
line is split on commas.
"""

import re

_MD_LEAD_RE = re.compile(r"^(?:#{1,6}\s*|>\s*|\*\*|__)+")
_NUM_RE = re.compile(r"^\d+\s*[.)\]:-]\s*")
_BULLET_RE = re.compile(r"^[-*•]\s+")
_DESC_SPLIT_RE = re.compile(r"\s+[-–—]\s+|:\s+|\s*\(|\s*（")
_MAX_INDENT = 3  # deeper lines are sub-items


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _strip_md(line: str) -> str:
    return _MD_LEAD_RE.sub("", line.strip())


def _clean_item(text: str) -> str:
    s = _NUM_RE.sub("", text, count=1)
    s = _BULLET_RE.sub("", s, count=1)
    s = s.replace("**", "").replace("__", "").strip()
    s = _DESC_SPLIT_RE.split(s, maxsplit=1)[0]  # drop " - description", ": ...", "(...)"
    s = s.split("/", 1)[0]  # "Sub-Zero/Wolf", "Haier / GE Appliances" -> first brand
    return s.strip(" .,;*:")


def parse_brand_list(text: str) -> list[str]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    top = [ln for ln in lines if _indent(ln) <= _MAX_INDENT]
    numbered = [_strip_md(ln) for ln in top if _NUM_RE.match(_strip_md(ln))]
    bullets = [_strip_md(ln) for ln in top if _BULLET_RE.match(ln.strip())]
    if numbered:
        items = [_clean_item(ln) for ln in numbered]
    elif bullets:
        items = [_clean_item(ln) for ln in bullets]
    elif len(lines) == 1:
        items = [p.strip(" .") for p in lines[0].split(",")]
    else:
        items = [_clean_item(_strip_md(ln)) for ln in lines]
    return [i for i in items if i]
