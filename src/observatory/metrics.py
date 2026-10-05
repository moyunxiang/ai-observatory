"""Brand Recall@K, as defined in the task (JIA_LIU_TASK.md, Task 3).

    Brand Recall@10 = |AI top-10 ∩ category brand table| / 10

i.e. "at least 8 of the AI's top 10 brands exist in the category's brand table".
The brand table may hold more than 10 brands; the denominator is always K.
"""

from .normalize import normalize_brand

PASS_THRESHOLD = 0.8


def _dedupe(keys: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def recall_at_k(
    brand_table: list[str],
    predicted: list[str],
    k: int = 10,
    alias_map: dict[str, str] | None = None,
) -> dict:
    """Share of the AI's top-K brands that appear in the brand table.

    - Predicted names are normalized and de-duplicated *before* truncating to K,
      so "Nike" and "NIKE" count as one slot.
    - Denominator is fixed at K: if the AI returns fewer than K brands, the
      missing slots count as misses (conservative).
    """
    table_keys = set(normalize_brand(b, alias_map) for b in brand_table) - {""}
    if not table_keys:
        raise ValueError("brand table is empty")
    pred_keys = _dedupe([normalize_brand(b, alias_map) for b in predicted])[:k]

    hits = [p for p in pred_keys if p in table_keys]
    return {
        "recall": len(hits) / k,
        "n_hits": len(hits),
        "n_predicted": len(pred_keys),
        "hits": hits,
        "extra": [p for p in pred_keys if p not in table_keys],
    }


def passes(recall: float, threshold: float = PASS_THRESHOLD) -> bool:
    return recall >= threshold
