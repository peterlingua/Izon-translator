"""English to Izon translation entry point."""
from translator import translate

def translate_english_to_izon(sentence):
    """Translate an English word, phrase, or sentence using available resources."""
    return translate(sentence, "english_to_izon")

if __name__ == "__main__":
    print("Izon translation:", translate_english_to_izon(input("Enter an English sentence: ")))
