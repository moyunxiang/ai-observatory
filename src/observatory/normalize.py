"""Brand-name normalization.

Goal: map surface variants of the same brand to one comparable key, e.g.
"Nike, Inc." / "NIKE" / "nike" -> "nike", "Häagen-Dazs" -> "haagen dazs".

Normalization is deliberately conservative. Anything that is a judgment call
(e.g. "HP" == "Hewlett-Packard", "Meituan" == "Meituan Waimai") goes into the
explicit alias table (data/brand_aliases.json), not into these rules.
"""

import re
import unicodedata

# Legal / corporate suffixes stripped only when they are the trailing token(s).
_CORPORATE_SUFFIXES = {
    "inc", "incorporated", "corp", "corporation", "co", "company",
    "ltd", "limited", "llc", "plc", "gmbh", "ag", "sa", "group", "holdings",
    "com",  # "Booking.com" == "Booking", "JD.com" == "JD"
}

_PUNCT_RE = re.compile(r"[^\w\s]")
_SPACE_RE = re.compile(r"\s+")


def basic_normalize(name: str) -> str:
    """Rule-based normalization without aliases."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  # strip accents
    s = s.lower().strip()
    s = s.replace("&", " and ")
    s = s.replace("'", "").replace("’", "")  # "McDonald's" -> "mcdonalds"
    s = s.replace("®", "").replace("™", "")
    s = _PUNCT_RE.sub(" ", s)  # "-", ".", "," etc. -> space
    s = _SPACE_RE.sub(" ", s).strip()

    tokens = s.split(" ")
    if tokens and tokens[0] == "the" and len(tokens) > 1:
        tokens = tokens[1:]
    while len(tokens) > 1 and (tokens[-1] in _CORPORATE_SUFFIXES or tokens[-1] == "and"):
        tokens = tokens[:-1]  # "Poly Developments and Holdings" -> "poly developments"
    return " ".join(tokens)


def build_alias_map(aliases: dict[str, list[str]]) -> dict[str, str]:
    """{canonical: [variants]} -> {basic_normalize(variant): basic_normalize(canonical)}."""
    alias_map: dict[str, str] = {}
    for canonical, variants in aliases.items():
        key = basic_normalize(canonical)
        alias_map[key] = key
        for v in variants:
            alias_map[basic_normalize(v)] = key
    return alias_map


def normalize_brand(name: str, alias_map: dict[str, str] | None = None) -> str:
    """Full normalization: rules first, then alias lookup."""
    key = basic_normalize(name)
    if alias_map:
        for _ in range(3):  # follow short chains, e.g. global variant -> canonical -> category canonical
            nxt = alias_map.get(key, key)
            if nxt == key:
                break
            key = nxt
    return key
