import unittest
from translator import translate

class TestSourceBackedInterrogatives(unittest.TestCase):
    def test_which_house_en_to_izon(self): self.assertEqual(translate("Which house?", "english_to_izon"), "Tị warị nị?")
    def test_who_did_it_en_to_izon(self): self.assertEqual(translate("Who did it?", "english_to_izon"), "Tịbọ kị o mịẹ nị?")
    def test_for_whom_en_to_izon(self): self.assertEqual(translate("For whom?", "english_to_izon"), "Tịbọ kọ ye nị?")
    def test_whose_shirt_en_to_izon(self): self.assertEqual(translate("Whose shirt is this?", "english_to_izon"), "Mị tịbọ kọ aru nị?")
    def test_who_did_it_izon_to_english(self): self.assertEqual(translate("Tịbọ kị o mịẹ nị?", "izon_to_english"), "Who did it?")
    def test_existing_pronoun_mapping(self): self.assertTrue(translate("we", "english_to_izon").casefold().startswith("woni"))

if __name__ == "__main__": unittest.main()



class TestGeneratedInterrogativePatterns(unittest.TestCase):
    def test_unseen_which_known_noun_uses_question_structure(self):
        # This phrase is not an exact stored sentence pair.
        self.assertEqual(translate("Which book?", "english_to_izon"), "Tị fún nị?")

    def test_unseen_who_did_known_object_uses_question_frame(self):
        # The noun is looked up compositionally; the sentence is not in the corpus.
        self.assertEqual(translate("Who did the dog?", "english_to_izon"), "Tịbọ kị obirí mịẹ nị?")

    def test_unknown_what_is_not_guessed(self):
        # Do not produce corrupt dictionary homonyms for a structure with no
        # confirmed Kolokuma transfer rule in the supplied reference.
        result = translate("What is my name?", "english_to_izon")
        self.assertEqual(result, "[UNSUPPORTED QUESTION PATTERN: What is my name?]")

    def test_which_dog_is_composed_without_sentence_pair(self):
        self.assertEqual(translate("Which dog?", "english_to_izon"), "Tị obirí nị?")

    def test_who_did_the_house_is_composed_without_sentence_pair(self):
        self.assertEqual(translate("Who did the house?", "english_to_izon"), "Tịbọ kị wárị mịẹ nị?")

    def test_who_is_known_noun_phrase_uses_productive_question_frame(self):
        # Not an exact stored sentence pair: the noun is translated compositionally.
        self.assertEqual(translate("Who is the boy?", "english_to_izon"), "Tịbọ kị yaị́ bi?")
        self.assertEqual(translate("Who is the boy", "english_to_izon"), "Tịbọ kị yaị́ bi")

    def test_who_is_girl_uses_productive_question_frame(self):
        self.assertEqual(translate("Who is the girl?", "english_to_izon"), "Tịbọ kị ụ́ bi?")
        self.assertEqual(translate("who is the girl", "english_to_izon"), "Tịbọ kị ụ́ bi")

    def test_who_fallback_is_not_unknown(self):
        result = translate("who", "english_to_izon")
        self.assertNotIn("[UNKNOWN:", result)

    def test_who_is_that_preserves_user_supplied_example(self):
        self.assertEqual(translate("Who is that?", "english_to_izon"), "Tịbọ kị Anị?")


class TestWhoAmIAndWhoAreYou(unittest.TestCase):
    def test_who_am_i_without_question_mark(self):
        self.assertEqual(translate("who am i", "english_to_izon"), "Tịbọ kị arị́")

    def test_who_am_i_with_question_mark(self):
        self.assertEqual(translate("who am I?", "english_to_izon"), "Tịbọ kị arị́?")

    def test_who_are_you_without_question_mark(self):
        self.assertEqual(translate("who are you", "english_to_izon"), "Tịbọ kị iné")

    def test_who_are_you_with_question_mark(self):
        self.assertEqual(translate("who are you?", "english_to_izon"), "Tịbọ kị iné?")
