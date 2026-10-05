import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from observatory.manual import parse_sheet, render_sheet  # noqa: E402
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

    def test_trailing_and_after_suffix(self):
        self.assertEqual(basic_normalize("Poly Developments and Holdings"), "poly developments")

    def test_dotcom_suffix(self):
        self.assertEqual(basic_normalize("Booking.com"), basic_normalize("Booking"))
        self.assertEqual(basic_normalize("JD.com"), "jd")

    def test_suffix_not_stripped_when_only_token(self):
        self.assertEqual(basic_normalize("Group"), "group")

    def test_alias_chain(self):
        amap = {"sony playstation": "playstation", "playstation": "sony interactive entertainment"}
        self.assertEqual(normalize_brand("Sony PlayStation", amap), "sony interactive entertainment")

    def test_alias(self):
        amap = build_alias_map({"Hewlett-Packard": ["HP", "HP Inc."]})
        self.assertEqual(normalize_brand("HP", amap), "hewlett packard")
        self.assertEqual(normalize_brand("hp inc", amap), "hewlett packard")


class TestRecall(unittest.TestCase):
    TABLE = REF + ["Brand K", "Brand L"]  # brand table may hold > 10 brands

    def test_perfect(self):
        r = recall_at_k(self.TABLE, list(reversed(REF)))
        self.assertEqual(r["recall"], 1.0)

    def test_denominator_is_k_not_table_size(self):
        pred = ["Brand K", "Brand L"] + REF[:6] + ["Other 1", "Other 2"]
        r = recall_at_k(self.TABLE, pred)
        self.assertAlmostEqual(r["recall"], 0.8)  # 8 of AI's 10 in a 12-brand table
        self.assertTrue(passes(r["recall"]))
        self.assertFalse(passes(0.7))
        self.assertEqual(r["extra"], ["other 1", "other 2"])

    def test_fewer_than_k_counts_as_miss(self):
        r = recall_at_k(self.TABLE, REF[:7])
        self.assertAlmostEqual(r["recall"], 0.7)
        self.assertEqual(r["n_predicted"], 7)

    def test_truncates_to_k_after_dedupe(self):
        pred = ["Brand A", "BRAND A"] + [f"Other {i}" for i in range(9)] + ["Brand B"]
        r = recall_at_k(self.TABLE, pred)
        self.assertEqual(r["n_predicted"], 10)
        self.assertAlmostEqual(r["recall"], 0.1)  # Brand B is 11th unique -> cut

    def test_empty_table_raises(self):
        with self.assertRaises(ValueError):
            recall_at_k([], ["x"])


class TestManualSheet(unittest.TestCase):
    def test_roundtrip(self):
        items = [
            {"category_id": "a", "category_name": "Cat A", "prompt": "What are the best brands for Cat A? List 10 brands."},
            {"category_id": "b", "category_name": "Cat B", "prompt": "P2"},
        ]
        sheet = render_sheet(items)
        sheet = sheet.replace("MODEL: ", "MODEL: GPT-test", 1)
        sheet = sheet.replace("--- paste answer below ---\n", "--- paste answer below ---\n1. **Brand A**\n2. Brand B\n\n=== not a header\n", 1)
        meta, recs = parse_sheet(sheet)
        self.assertEqual(meta["model"], "GPT-test")
        self.assertEqual([r["category_id"] for r in recs], ["a", "b"])
        self.assertEqual(recs[0]["category_name"], "Cat A")
        self.assertEqual(parse_brand_list(recs[0]["response"])[:2], ["Brand A", "Brand B"])
        self.assertEqual(recs[1]["response"], "")


class TestParse(unittest.TestCase):
    def test_numbered_markdown(self):
        text = "Here are 10 brands:\n\n1. **Brand A** - known for X\n2) Brand B: description\n3. Brand C (Germany)\n- a note"
        self.assertEqual(parse_brand_list(text), ["Brand A", "Brand B", "Brand C"])  # numbered items win

    def test_bullets_when_no_numbers(self):
        self.assertEqual(parse_brand_list("Top picks:\n- **Brand A** — note\n* Brand B: x\n• Brand C"), ["Brand A", "Brand B", "Brand C"])

    def test_hyphenated_name_kept(self):
        self.assertEqual(parse_brand_list("1. Coca-Cola\n2. Rolls-Royce"), ["Coca-Cola", "Rolls-Royce"])

    def test_gpt_style_with_intro_and_outro(self):
        text = ("Here are 10 of the best brands for robot vacuums:\n\n"
                "1. **Roborock** – Known for strong suction.\n"
                "2. **iRobot (Roomba)** – Pioneer of the category.\n"
                "3. **Ecovacs (Deebot)**: Wide range.\n\n"
                "Let me know if you want a comparison!")
        self.assertEqual(parse_brand_list(text), ["Roborock", "iRobot", "Ecovacs"])

    def test_bold_wrapped_numbers_and_headings(self):
        text = ("Intro:\n\n### Giants\n\n**1. Amazon**\nThe leader.\n\n**2. Alibaba (Taobao & Tmall)**\nAsia.\n\n"
                "### 3. eBay\nAuctions.\n\n---\n*Note: depends on region.*")
        self.assertEqual(parse_brand_list(text), ["Amazon", "Alibaba", "eBay"])

    def test_nested_sub_bullets_ignored(self):
        text = ("1.  **Nike**\n    - **Best for:** Innovation.\n    - **Why:** Leader.\n\n"
                "2.  **Adidas**\n    - **Best for:** Heritage.\n\n**Disclaimer:** consult a doctor.")
        self.assertEqual(parse_brand_list(text), ["Nike", "Adidas"])

    def test_chinese_parenthesis(self):
        self.assertEqual(parse_brand_list("1. **Tongrentang (同仁堂)**\n2. Yunnan Baiyao（云南白药）"), ["Tongrentang", "Yunnan Baiyao"])

    def test_comma_line(self):
        self.assertEqual(parse_brand_list("Brand A, Brand B, Brand C."), ["Brand A", "Brand B", "Brand C"])


if __name__ == "__main__":
    unittest.main()
