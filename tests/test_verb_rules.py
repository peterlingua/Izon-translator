import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from verb_rules import diagnose, inventory  # noqa: E402
from translator import translate  # noqa: E402


class VerbRuleInventoryTests(unittest.TestCase):
    def test_every_construction_has_a_source_and_status(self):
        for item in inventory():
            self.assertTrue(item["source"], item["name"])
            self.assertIn(item["status"], {"attested", "attested-flag", "unsupported"}, item["name"])

    def test_unsupported_constructions_have_no_izon_form(self):
        for item in inventory():
            if item["status"] == "unsupported":
                self.assertIsNone(item["izon_form"], item["name"])


class VerbDiagnosisTests(unittest.TestCase):
    def test_modal_can_is_diagnosed(self):
        self.assertIn("modal_can", diagnose("He can eat yam."))

    def test_want_to_is_diagnosed(self):
        self.assertIn("want_need_to", diagnose("I want to eat yam."))

    def test_past_perfect_is_diagnosed(self):
        self.assertIn("past_perfect", diagnose("I had eaten yam."))

    def test_attested_progressive_is_not_diagnosed_as_unsupported(self):
        self.assertIsNone(diagnose("I am eating yam."))

    def test_izon_direction_is_not_diagnosed(self):
        self.assertIsNone(diagnose("He can eat yam.", "izon_to_english"))


class VerbTranslationTests(unittest.TestCase):
    def test_attested_progressive_still_translates(self):
        self.assertEqual(translate("I am eating yam.", "english_to_izon"), "Àri burú ị́ịyemi.")

    def test_modal_is_flagged_not_silently_returned(self):
        out = translate("He can eat yam.", "english_to_izon")
        self.assertTrue(out.startswith("[UNSUPPORTED SENTENCE PATTERN"), out)
        self.assertNotIn("[UNKNOWN", out)

    def test_want_to_is_flagged(self):
        out = translate("I want to eat yam.", "english_to_izon")
        self.assertTrue(out.startswith("[UNSUPPORTED SENTENCE PATTERN"), out)


if __name__ == "__main__":
    unittest.main()
