"""Izon to English translation entry point."""
from translator import translate

def translate_izon_to_english(sentence):
    """Translate an Izon word, phrase, or sentence using available resources."""
    return translate(sentence, "izon_to_english")

if __name__ == "__main__":
    print("English translation:", translate_izon_to_english(input("Enter a Kolokuma Izon sentence: ")))
