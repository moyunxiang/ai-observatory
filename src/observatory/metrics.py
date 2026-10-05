"""Recall@K between a reference brand set and an LLM's ranked brand list."""

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
    reference: list[str],
    predicted: list[str],
    k: int = 10,
    alias_map: dict[str, str] | None = None,
) -> dict:
    """Recall@K = |ref ∩ top-K(pred)| / |ref|, computed on normalized names.

    - Predicted names are normalized and de-duplicated *before* truncating to K,
      so "Nike" and "NIKE" count as one slot.
    - If the LLM returns fewer than K brands, only those are used (no padding).
    """
    ref_keys = _dedupe([normalize_brand(b, alias_map) for b in reference])
    if not ref_keys:
        raise ValueError("reference set is empty")
    pred_keys = _dedupe([normalize_brand(b, alias_map) for b in predicted])[:k]

    ref_set = set(ref_keys)
    hits = [p for p in pred_keys if p in ref_set]
    return {
        "recall": len(hits) / len(ref_keys),
        "n_reference": len(ref_keys),
        "n_predicted": len(pred_keys),
        "hits": hits,
        "missed": [r for r in ref_keys if r not in set(pred_keys)],
        "extra": [p for p in pred_keys if p not in ref_set],
    }


def passes(recall: float, threshold: float = PASS_THRESHOLD) -> bool:
    return recall >= threshold
