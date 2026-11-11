"""Tests for compound and complex sentence composition (clause_engine.py).

Two layers are tested:
1. Structure: a stub clause translator isolates the connective logic from
   vocabulary, so these tests check the pattern rules alone.
2. Integration: the real translator on sentences built from vocabulary the
   engine knows, plus decline cases that must stay flagged.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from clause_engine import translate_compound  # noqa: E402
from translator import translate  # noqa: E402
from lexicon import load_lexicon  # noqa: E402


# Stub clause table: English clauses -> Izon, and Izon clauses -> English.
EN_TO_IZ = {
    "he is coming": "Érí bòyèmí",
    "the girl eats yam": "Ụ́ bi burú ị́ị",
    "the boy is sleeping": "Yaị́ bi bụ́nụyemi",
    "the fire is hot": "Fáí mị lá èmí",
    "father is coming": "Dádá bóẹ̀mị",
}
IZ_TO_EN = {
    "Érí bòyèmí": "He is coming",
    "ụ́ bi burú ị́ị": "The girl eats yam",
    "yaị́ bi bụ́nụyemi": "The boy is sleeping",
    "fáí mị lá èmí": "the fire is hot",
    "dádá bóẹ̀mị": "Father is coming",
}


def stub_en(text, direction, lexicon):
    key = text.strip().rstrip(".").casefold()
    return EN_TO_IZ.get(key)


def stub_iz(text, direction, lexicon):
    return IZ_TO_EN.get(text.strip())


def _lex():
    return load_lexicon(verbose=False)


class StructureEnglishToIzonTests(unittest.TestCase):
    def compose(self, sentence):
        return translate_compound(sentence, "english_to_izon", {}, clause=stub_en)

    def test_coordinate_and_uses_gba(self):
        self.assertEqual(self.compose("He is coming, and the girl eats yam."),
                         "Érí bòyèmí, gbá ụ́ bi burú ị́ị.")

    def test_coordinate_but_uses_okpo(self):
        self.assertEqual(self.compose("He is coming, but the girl eats yam."),
                         "Érí bòyèmí, ọ̀kpọ̀ ụ́ bi burú ị́ị.")

    def test_coordinate_so_uses_obo(self):
        self.assertEqual(self.compose("He is coming, so the girl eats yam."),
                         "Érí bòyèmí, ọ́bọ́ ụ́ bi burú ị́ị.")

    def test_leading_because_wraps_reason_clause(self):
        self.assertEqual(self.compose("Because the fire is hot, father is coming."),
                         "Bárá fáí mị lá èmí fịẹ́ị, dádá bóẹ̀mị.")

    def test_leading_while_uses_asain(self):
        self.assertEqual(self.compose("While he is coming, the girl eats yam."),
                         "Érí bòyèmí ásáìn, ụ́ bi burú ị́ị.")

    def test_clause_final_because_uses_ba_and_fiei(self):
        self.assertEqual(self.compose("The girl eats yam because he is coming."),
                         "Ụ́ bi burú ị́ị bá érí bòyèmí fịẹ́ị.")

    def test_nested_coordinate_then_because(self):
        self.assertEqual(
            self.compose("He is coming, and the girl eats yam because the boy is sleeping."),
            "Érí bòyèmí, gbá ụ́ bi burú ị́ị bá yaị́ bi bụ́nụyemi fịẹ́ị.",
        )

    def test_question_is_declined(self):
        self.assertIsNone(self.compose("Is he coming, and the girl eats yam?"))

    def test_unknown_clause_declines_whole_sentence(self):
        self.assertIsNone(self.compose("He is coming, and the owl sings."))

    def test_simple_sentence_is_not_composed(self):
        self.assertIsNone(self.compose("He is coming."))

    def test_non_final_because_is_declined(self):
        # Corpus attests "because" only in final position.
        self.assertIsNone(self.compose("The girl eats yam because he is coming, and the boy is sleeping."))


class StructureIzonToEnglishTests(unittest.TestCase):
    def compose(self, sentence):
        return translate_compound(sentence, "izon_to_english", {}, clause=stub_iz)

    def test_gba_is_and(self):
        self.assertEqual(self.compose("Érí bòyèmí, gbá ụ́ bi burú ị́ị."),
                         "He is coming, and the girl eats yam.")

    def test_okpo_is_but(self):
        self.assertEqual(self.compose("Érí bòyèmí, ọ̀kpọ̀ ụ́ bi burú ị́ị."),
                         "He is coming, but the girl eats yam.")

    def test_obo_is_so(self):
        self.assertEqual(self.compose("Érí bòyèmí, ọ́bọ́ ụ́ bi burú ị́ị."),
                         "He is coming, so the girl eats yam.")

    def test_bara_is_because_clause_initial(self):
        self.assertEqual(self.compose("Bárá fáí mị lá èmí fịẹ́ị, dádá bóẹ̀mị."),
                         "Because the fire is hot, father is coming.")

    def test_asain_is_while(self):
        self.assertEqual(self.compose("Érí bòyèmí ásáìn, ụ́ bi burú ị́ị."),
                         "While he is coming, the girl eats yam.")

    def test_ba_fiei_is_because_clause_final(self):
        self.assertEqual(self.compose("ụ́ bi burú ị́ị bá Érí bòyèmí fịẹ́ị."),
                         "The girl eats yam because he is coming.")

    def test_okpo_with_tone_is_not_but_when_it_is_head(self):
        # "ókpó" (head, high tone) shares plain letters with "ọ̀kpọ̀" (but).
        # It must not be read as a conjunction.
        self.assertIsNone(self.compose("Íní ókpó mị gbẹ́lẹ́mọ́ẹ̀mị."))

    def test_unknown_clause_declines(self):
        self.assertIsNone(self.compose("Érí bòyèmí, gbá owl sings."))


class IntegrationTests(unittest.TestCase):
    """Real translator and real vocabulary."""

    def test_compound_with_known_vocabulary(self):
        out = translate("He is coming, and the girl eats yam.", "english_to_izon")
        self.assertNotIn("UNSUPPORTED", out)
        self.assertTrue(out.endswith(", gbá ụ́ bi burú ị́ị."), out)

    def test_compound_round_trip_english_to_izon_to_english(self):
        izon = translate("He is coming, but the girl eats yam.", "english_to_izon")
        self.assertEqual(translate(izon, "izon_to_english"),
                         "He is coming, but the girl eats yam.")

    def test_complex_round_trip(self):
        izon = translate("Because the girl eats yam, he is coming.", "english_to_izon")
        self.assertIn("Bárá", izon)
        self.assertIn("fịẹ́ị", izon)
        self.assertNotIn("UNSUPPORTED", izon)

    def test_compound_with_unknown_word_stays_flagged(self):
        out = translate("He is coming, and the owl sings.", "english_to_izon")
        self.assertTrue(out.startswith("[UNSUPPORTED") or "[UNKNOWN" in out, out)

    def test_head_sense_selects_come_not_come_down(self):
        # "bó"/"bò" = come (loc. come); "kóro" = fall; ... come down.
        out = translate("He is coming.", "english_to_izon")
        self.assertTrue("bò" in out or "bó" in out, out)
        self.assertNotIn("kóro", out)

    def test_corpus_compound_still_exact(self):
        # A verified corpus compound must still come from the exact-pair path.
        self.assertEqual(
            translate("That man is coming quickly, but the wife is greeting him.", "english_to_izon"),
            "Ú béì kìmí béì àsàsà bóẹ̀mị, kọ̀ éré má ú kíléẹ̀mị.",
        )


if __name__ == "__main__":
    unittest.main()
