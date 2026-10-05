import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from observatory.metrics import passes, recall_at_k  # noqa: E402
from observatory.normalize import basic_normalize, build_alias_map, normalize_brand  # noqa: E402
from observatory.parse import parse_brand_list  # noqa: E402

# Synthetic placeholder names only; these are NOT reference data.
REF = [f"Brand {c}" for c in "ABCDEFGHIJ"]


class TestNormalize(unittest.TestCase):
    def test_case_punct_suffix(self):
        self.assertEqual(basic_normalize("NIKE, Inc."), "nike")
        self.assertEqual(basic_normalize("McDonald's"), "mcdonalds")
        self.assertEqual(basic_normalize("Häagen-Dazs"), "haagen dazs")
        self.assertEqual(basic_normalize("The North Face"), "north face")
        self.assertEqual(basic_normalize("Procter & Gamble Co."), "procter and gamble")

    def test_suffix_not_stripped_when_only_token(self):
        self.assertEqual(basic_normalize("Group"), "group")

    def test_alias(self):
        amap = build_alias_map({"Hewlett-Packard": ["HP", "HP Inc."]})
        self.assertEqual(normalize_brand("HP", amap), "hewlett packard")
        self.assertEqual(normalize_brand("hp inc", amap), "hewlett packard")


class TestRecall(unittest.TestCase):
    def test_perfect(self):
        self.assertEqual(recall_at_k(REF, list(reversed(REF)))["recall"], 1.0)

    def test_partial_and_threshold(self):
        pred = REF[:8] + ["Other 1", "Other 2"]
        r = recall_at_k(REF, pred)
        self.assertAlmostEqual(r["recall"], 0.8)
        self.assertTrue(passes(r["recall"]))
        self.assertFalse(passes(0.7))
        self.assertEqual(r["missed"], ["brand i", "brand j"])

    def test_truncates_to_k_after_dedupe(self):
        pred = ["Brand A", "BRAND A"] + [f"Other {i}" for i in range(9)] + ["Brand B"]
        r = recall_at_k(REF, pred)
        self.assertEqual(r["n_predicted"], 10)
        self.assertAlmostEqual(r["recall"], 0.1)  # Brand B is 11th unique -> cut

    def test_empty_reference_raises(self):
        with self.assertRaises(ValueError):
            recall_at_k([], ["x"])


class TestParse(unittest.TestCase):
    def test_numbered_markdown(self):
        text = "Here are 10 brands:\n\n1. **Brand A** - known for X\n2) Brand B: description\n3. Brand C (Germany)\n- Brand D — note"
        self.assertEqual(parse_brand_list(text), ["Brand A", "Brand B", "Brand C", "Brand D"])

    def test_hyphenated_name_kept(self):
        self.assertEqual(parse_brand_list("1. Coca-Cola\n2. Rolls-Royce"), ["Coca-Cola", "Rolls-Royce"])

    def test_comma_line(self):
        self.assertEqual(parse_brand_list("Brand A, Brand B, Brand C."), ["Brand A", "Brand B", "Brand C"])


if __name__ == "__main__":
    unittest.main()
