import unittest
from lexicon import load_lexicon, lookup_izon_word, lookup_english_word
from izon_to_english import translate_izon_to_english
from english_to_izon import translate_english_to_izon
from tokenizer import tokenize, detokenize

class TranslatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_lexicon()

    def test_dictionary_loaded(self):
        self.assertGreater(len(self.lex['entries']), 5000)

    def test_known_izon_lookup(self):
        self.assertTrue(lookup_izon_word('áàa', self.lex))

    def test_known_english_lookup(self):
        self.assertTrue(lookup_english_word('ocean', self.lex))
        # A compact secondary gloss such as `book` should remain searchable
        # without turning the entire explanatory dictionary paragraph into aliases.
        self.assertTrue(lookup_english_word('book', self.lex))

    def test_izon_to_english_word(self):
        result = translate_izon_to_english('áàa')
        self.assertNotIn('[UNKNOWN:', result)
        self.assertTrue(result.strip())

    def test_english_to_izon_word(self):
        result = translate_english_to_izon('ocean')
        self.assertNotIn('[UNKNOWN:', result)
        self.assertTrue(result.strip())

    def test_empty_input(self):
        self.assertEqual(translate_izon_to_english('  '), 'Please enter a sentence.')
        self.assertEqual(translate_english_to_izon(''), 'Please enter a sentence.')

    def test_short_glosses_are_not_truncated(self):
        self.assertEqual(translate_izon_to_english('ába').casefold(), 'if')
        thank_you = translate_english_to_izon('thank you')
        self.assertNotIn('[UNKNOWN:', thank_you)
        self.assertNotIn('(', thank_you)
        self.assertFalse(translate_english_to_izon('if').startswith('-'))

    def test_dictionary_reference_suffix_is_ignored(self):
        self.assertNotIn('[UNKNOWN:', translate_izon_to_english('agbaá¹'))

    def test_unknown_marked(self):
        self.assertIn('[UNKNOWN:', translate_izon_to_english('zzzzunknownword'))

    def test_tokenizer_roundtrip_punctuation(self):
        self.assertEqual(detokenize(tokenize('Hello, world!')), 'Hello, world!')

if __name__ == '__main__': unittest.main()
