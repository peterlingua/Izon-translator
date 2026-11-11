"""Exact-match evaluation for the bundled or manually prepared parallel corpus.

Exact-match scores measure reproduction of stored examples, not translation accuracy
on unseen sentences. When multiple Izon variants share one English gloss, English ->
Izon is scored against the set of supplied variants rather than one arbitrary row.
"""
import csv
from collections import defaultdict
from pathlib import Path
from english_to_izon import translate_english_to_izon
from izon_to_english import translate_izon_to_english
from tokenizer import normalise_text, normalise_word

ROOT = Path(__file__).resolve().parent
MANUAL_PAIRS = ROOT / "data" / "evaluation_pairs.csv"
SEED_PAIRS = ROOT / "data" / "parallel_corpus.csv"


def _key(value):
    return normalise_word(normalise_text(value)).rstrip(" .!?…;:").strip()


def evaluate():
    if MANUAL_PAIRS.exists():
        pairs_path = MANUAL_PAIRS
        print("Using manually prepared evaluation_pairs.csv.")
    elif SEED_PAIRS.exists():
        pairs_path = SEED_PAIRS
        print("Using bundled source-attested and project-owner-supplied sentence pairs.")
        print("Warning: exact-pair scores do not measure generalization to unseen sentences.")
    else:
        print("No evaluation_pairs.csv or parallel_corpus.csv found.")
        return

    pairs = []
    with pairs_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("verified") or "").strip().casefold() not in {"yes", "true", "1", "verified"}:
                continue
            en = (row.get("english") or "").strip()
            iz = (row.get("izon") or "").strip()
            if en and iz:
                pairs.append(row)

    if not pairs:
        print("No verified sentence pairs were found.")
        return

    valid_variants = defaultdict(set)
    for row in pairs:
        valid_variants[_key(row["english"])].add(_key(row["izon"]))

    i2e_correct = 0
    for row in pairs:
        i2e_correct += _key(translate_izon_to_english(row["izon"])) == _key(row["english"])

    e2i_correct = 0
    unique_english = sorted(valid_variants)
    for english_key in unique_english:
        # Preserve original case and punctuation from the first source row for input.
        english = next(row["english"] for row in pairs if _key(row["english"]) == english_key)
        output = _key(translate_english_to_izon(english))
        e2i_correct += output in valid_variants[english_key]

    user_count = sum(1 for row in pairs if (row.get("sentence_type") or "").strip() in {"simple", "compound", "compound_complex"})
    print(f"Verified/source-attested pairs loaded: {len(pairs)}")
    if user_count:
        print(f"Project-owner-supplied pairs included: {user_count}")
    print(f"English input forms (unique glosses): {len(unique_english)}")
    print(f"English -> Izon exact accuracy: {e2i_correct}/{len(unique_english)} ({100*e2i_correct/len(unique_english):.1f}%)")
    print(f"Izon -> English exact accuracy: {i2e_correct}/{len(pairs)} ({100*i2e_correct/len(pairs):.1f}%)")


if __name__ == "__main__":
    evaluate()
