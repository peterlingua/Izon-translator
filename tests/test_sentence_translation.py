"""Regression tests for sentence transfer and the published seed corpus."""
import unittest

from grammar import load_parallel_pairs
from lexicon import load_lexicon, lookup_english_word
from english_to_izon import translate_english_to_izon
from izon_to_english import translate_izon_to_english
from tokenizer import tokenize


def comparable(text):
    return str(text or "").casefold().rstrip(" .!?…;:").strip()


class SentenceTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_lexicon()

    def test_all_corpus_pairs_work_both_directions(self):
        pairs = load_parallel_pairs()
        self.assertGreaterEqual(len(pairs), 103)
        # Some English glosses intentionally have more than one Izon variant in the
        # supplied source. English -> Izon selects a canonical variant; Izon -> English
        # must accept every source-listed Izon variant.
        valid_izon_by_english = {}
        for pair in pairs:
            valid_izon_by_english.setdefault(comparable(pair["english"]), set()).add(comparable(pair["izon"]))
        for pair in pairs:
            with self.subTest(pair=pair["id"], direction="Izon to English"):
                result = translate_izon_to_english(pair["izon"])
                self.assertEqual(comparable(result), comparable(pair["english"]))
            with self.subTest(pair=pair["id"], direction="English to Izon"):
                result = translate_english_to_izon(pair["english"])
                self.assertIn(comparable(result), valid_izon_by_english[comparable(pair["english"])])

    def test_exact_pair_preserves_new_terminal_punctuation(self):
        self.assertEqual(
            translate_izon_to_english("Ebi diibi pelemi!"),
            "Ebi cut the net!",
        )
        self.assertEqual(
            translate_english_to_izon("Ebi cut the net!"),
            "Ebi diibi pelemi!",
        )
        from grammar import exact_rule_translation
        self.assertIsNone(exact_rule_translation("Ebi diibi pelemi?", "izon_to_english"))

    def test_combining_tone_marks_stay_in_one_token(self):
        tokens = tokenize("ọmịnị́")
        self.assertEqual(len(tokens), 1)
        self.assertTrue(tokens[0])

    def test_tone_insensitive_lookup_finds_common_unmarked_spelling(self):
        from lexicon import lookup_izon_word
        self.assertTrue(lookup_izon_word("buru", self.lex))

    def test_numeric_reference_artifacts_are_not_lexical_entries(self):
        matches = lookup_english_word("child", self.lex)
        self.assertTrue(matches)
        self.assertTrue(all(row.get("canonical_izon") != "4" for row in matches))
        self.assertTrue(translate_english_to_izon("The child ran.").startswith("Tọbọụ́"))

    def test_generic_english_svo_to_izon_sov(self):
        result = translate_english_to_izon("I ate yam.")
        self.assertNotIn("[UNKNOWN:", result)
        self.assertTrue(result.startswith("Àri burú"), result)
        self.assertTrue(result.endswith("ị́ịmi."), result)

    def test_generic_present_svo_to_izon_sov_and_article_order(self):
        result = translate_english_to_izon("The boy eats yam.")
        self.assertNotIn("[UNKNOWN:", result)
        self.assertTrue(result.startswith("Yaị́ bi burú"), result)
        self.assertTrue(result.endswith("ị́ị."), result)

    def test_generic_izon_sov_to_english_svo(self):
        self.assertEqual(translate_izon_to_english("Eri burú ị́ị."), "He eats yam.")
        self.assertEqual(translate_izon_to_english("Tobou bi burú ị́ị."), "The child eats yam.")

    def test_generic_progressive_uses_verb_lemma(self):
        result = translate_english_to_izon("I am eating yam.")
        self.assertNotIn("[UNKNOWN:", result)
        self.assertTrue(result.startswith("Àri burú"), result)
        self.assertTrue(result.endswith("ị́ịyemi."), result)

    def test_simple_english_copular_clause_uses_subject_complement_structure(self):
        result = translate_english_to_izon("The boy is a child.")
        self.assertNotIn("[UNKNOWN:", result)
        self.assertNotIn(" is ", result.casefold())
        self.assertIn("yaị́", result.casefold())
        self.assertIn("tọbọụ́", result.casefold())

    def test_simple_english_negative_is_not_duplicated(self):
        result = translate_english_to_izon("I do not go.")
        self.assertEqual(result, "Àri muagha.")
        self.assertEqual(result.casefold().count("gha"), 1)

    def test_generic_izon_intransitive_clause_and_english_agreement(self):
        self.assertEqual(translate_izon_to_english("Eri banghimi."), "He ran.")
        self.assertEqual(translate_izon_to_english("Eri banghi."), "He runs.")
        self.assertEqual(translate_izon_to_english("Ari banghi."), "I run.")

    def test_user_sentence_examples_cover_three_types_in_both_directions(self):
        from collections import Counter
        pairs = load_parallel_pairs()
        user_pairs = [p for p in pairs if p.get("id", "").startswith("USR-")]
        counts = Counter(p.get("sentence_type") for p in user_pairs)
        self.assertEqual(counts["simple"], 30)
        self.assertEqual(counts["compound"], 30)
        self.assertEqual(counts["compound_complex"], 30)
        valid_izon_by_english = {}
        for pair in user_pairs:
            valid_izon_by_english.setdefault(comparable(pair["english"]), set()).add(comparable(pair["izon"]))
        for pair in user_pairs:
            with self.subTest(pair=pair["id"], direction="Izon to English"):
                self.assertEqual(comparable(translate_izon_to_english(pair["izon"])), comparable(pair["english"]))
            with self.subTest(pair=pair["id"], direction="English to Izon"):
                self.assertIn(comparable(translate_english_to_izon(pair["english"])), valid_izon_by_english[comparable(pair["english"])])


    def test_dictionary_girl_entry_is_recognized(self):
        matches = lookup_english_word("girl", self.lex)
        self.assertTrue(matches)
        self.assertEqual(matches[0]["canonical_izon"], "ụ́")
        self.assertTrue(matches[0]["part_of_speech"].startswith("n."))

    def test_english_definite_girl_noun_phrase(self):
        from english_to_izon import translate_english_to_izon
        self.assertEqual(translate_english_to_izon("the girl"), "Ụ́ bi")

    def test_english_indefinite_girl_noun_phrase(self):
        from english_to_izon import translate_english_to_izon
        self.assertEqual(translate_english_to_izon("a girl"), "Ụ́")

    def test_izon_girl_noun_phrase_uses_contextual_dictionary_sense(self):
        from izon_to_english import translate_izon_to_english
        self.assertEqual(translate_izon_to_english("ụ́ bi"), "The girl")

    def test_izon_girl_svo_sentence_uses_contextual_dictionary_sense(self):
        from izon_to_english import translate_izon_to_english
        self.assertEqual(translate_izon_to_english("ụ́ bi burú ị́ị."), "The girl eats yam.")

    def test_bare_izon_homograph_is_reported_as_ambiguous(self):
        from izon_to_english import translate_izon_to_english
        self.assertTrue(translate_izon_to_english("ụ́").startswith("[AMBIGUOUS IZON WORD:"))

    def test_unsupported_copular_adjective_is_not_misgenerated_as_progressive(self):
        from english_to_izon import translate_english_to_izon
        self.assertTrue(translate_english_to_izon("The girl is beautiful.").startswith("[UNSUPPORTED SENTENCE PATTERN:"))

    def test_girl_in_unseen_simple_sentence(self):
        from english_to_izon import translate_english_to_izon
        result = translate_english_to_izon("The girl eats yam.")
        self.assertEqual(result, "Ụ́ bi burú ị́ị.")

    def test_bilingual_sentence_structure_rules_are_loaded(self):
        from grammar import load_grammar_rules
        ids = {r["rule_id"] for r in load_grammar_rules()}
        self.assertTrue({"IZ-SS-001", "IZ-SS-002", "IZ-SS-003", "EN-SS-019", "EN-SS-020", "EN-SS-021"}.issubset(ids))


if __name__ == "__main__":
    unittest.main()

class UnsupportedSentenceSafetyTests(unittest.TestCase):
    def test_multiword_sentence_does_not_collapse_to_dictionary_homonym(self):
        from translator import translate
        result = translate("The man sees the woman.", "english_to_izon")
        self.assertTrue(result.startswith("[UNSUPPORTED SENTENCE PATTERN:"), result)
        self.assertNotEqual(result.strip(), "Ụ́")

    def test_single_word_dictionary_lookup_still_works(self):
        from translator import translate
        result = translate("who", "english_to_izon")
        self.assertEqual(result, "Tịbọ")
