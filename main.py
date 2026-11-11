"""Interactive command-line interface for the bidirectional translator."""
from english_to_izon import translate_english_to_izon
from izon_to_english import translate_izon_to_english
from lexicon import load_lexicon


def main():
    print("=" * 58)
    print("KOLOKUMA IZON ↔ ENGLISH RULE-BASED TRANSLATOR")
    print("Rule-based sentence translation with dictionary and morphology; unknown words are marked.")
    print("=" * 58)
    try:
        lexicon = load_lexicon(verbose=True)
        print(f"Ready: {len(lexicon['entries'])} dictionary entries loaded.")
    except (FileNotFoundError, ValueError) as error:
        print(f"Cannot start: {error}")
        return
    while True:
        print("\n1. English -> Izon\n2. Izon -> English\n3. Look up an Izon word\nQ. Quit")
        choice = input("Select an option: ").strip().casefold()
        if choice == "q":
            print("Goodbye!"); break
        if choice == "1":
            print("Izon:", translate_english_to_izon(input("Enter English: ")))
        elif choice == "2":
            print("English:", translate_izon_to_english(input("Enter Izon: ")))
        elif choice == "3":
            from lexicon import lookup_izon_word
            word = input("Enter an Izon word or phrase: ").strip()
            matches = lookup_izon_word(word, lexicon)
            if matches:
                for entry in matches:
                    print(f"{entry['izon']} -> {entry['english']} [{entry['part_of_speech']}]")
            else:
                # Also explain forms generated/recognized by the supplied morphology rules.
                from morphology import analyze_izon_morphology
                from sentence_engine import _lookup_base
                morphological = analyze_izon_morphology(word, lexicon, _lookup_base)
                if morphological:
                    print(f"{word} -> {morphological['target']} [{morphological['pos']}; {morphological.get('feature', 'morphology')}]")
                else:
                    print("No dictionary or recognized morphology entry found.")
        else:
            print("Invalid choice. Select 1, 2, 3, or Q.")

if __name__ == "__main__":
    main()
