"""Tests for user-supplied Kolokuma morphology and sentence examples."""
import unittest
from collections import defaultdict

from grammar import load_parallel_pairs
from tokenizer import normalise_text, normalise_word
from morphology import (
    analyze_izon_morphology,
    conjugate_izon_verb,
    inflect_izon_adjective,
    inflect_izon_noun,
    load_morphology_inventory,
)
from english_to_izon import translate_english_to_izon
from izon_to_english import translate_izon_to_english


def key(text):
    return normalise_word(normalise_text(text)).rstrip(" .!?…;:").strip()


class UserSuppliedRulesTests(unittest.TestCase):
    def test_all_90_user_sentence_pairs_are_preserved_and_match_both_directions(self):
        pairs = [p for p in load_parallel_pairs() if p.get("sentence_type") in {"simple", "compound", "compound_complex"}]
        self.assertEqual(len(pairs), 90)
        types = defaultdict(int)
        for pair in pairs:
            types[pair["sentence_type"]] += 1
        self.assertEqual(dict(types), {"simple": 30, "compound": 30, "compound_complex": 30})
        allowed = defaultdict(set)
        for pair in pairs:
            allowed[key(pair["english"])].add(key(pair["izon"]))
        for pair in pairs:
            with self.subTest(id=pair["id"], direction="Izon to English"):
                self.assertEqual(key(translate_izon_to_english(pair["izon"])), key(pair["english"]))
            with self.subTest(id=pair["id"], direction="English to Izon"):
                self.assertIn(key(translate_english_to_izon(pair["english"])), allowed[key(pair["english"])])

    def test_source_morphology_inventory_is_populated(self):
        rows = load_morphology_inventory()
        self.assertGreaterEqual(len(rows), 40)
        categories = {r["category"] for r in rows}
        self.assertTrue({"noun", "adjective", "verb", "pronoun"}.issubset(categories))

    def test_noun_suffixes_from_source(self):
        self.assertEqual(inflect_izon_noun("akasi", "-mo"), "akasimo")
        self.assertEqual(inflect_izon_noun("ekpeti", "-ama"), "ekpeti-ama")
        self.assertEqual(translate_izon_to_english("akasimo"), "The chairs")
        self.assertEqual(translate_izon_to_english("ekpeti-ama"), "Boxes")
        self.assertEqual(translate_izon_to_english("ogoni-otu"), "Visitors")
        self.assertEqual(translate_izon_to_english("oweiamini"), "The men")

    def test_adjective_degrees_from_source(self):
        self.assertEqual(inflect_izon_adjective("zau", "comparative"), "zau-dẹịn")
        self.assertEqual(inflect_izon_adjective("ganị", "superlative"), "ganị-fa")
        self.assertEqual(translate_izon_to_english("zau-dẹịn"), "Smaller")
        self.assertEqual(translate_izon_to_english("ganịkami"), "Very expensive")
        self.assertEqual(translate_english_to_izon("very small"), "Zau-kami")
        self.assertEqual(translate_english_to_izon("not short"), "Ikịságha")

    def test_explicit_verb_paradigms_are_source_grounded(self):
        self.assertEqual(conjugate_izon_verb("Mu", "present"), "munimi")
        self.assertEqual(conjugate_izon_verb("mú", "past"), "mumi")
        self.assertEqual(conjugate_izon_verb("Mu", "progressive"), "muyemi")
        self.assertEqual(conjugate_izon_verb("Mu", "perfect"), "mudọụ")
        self.assertEqual(conjugate_izon_verb("Mu", "future"), "munghimi")
        self.assertEqual(conjugate_izon_verb("Mu", "past_progressive"), "mutimimi")
        self.assertEqual(conjugate_izon_verb("Mu", "negative"), "muagha")
        self.assertIsNone(conjugate_izon_verb("some-unlisted-stem", "future"))
        self.assertEqual(translate_izon_to_english("Eri munghimi."), "He will go.")
        self.assertEqual(translate_izon_to_english("Eri mutimimi."), "He was going.")
        self.assertEqual(translate_izon_to_english("Eri muagha."), "He does not go.")
        self.assertEqual(translate_english_to_izon("He has gone."), "Eri mudọụ.")


if __name__ == "__main__":
    unittest.main()
