"""Load and apply only explicitly verified sentence-level rules."""
import csv
from pathlib import Path
from tokenizer import normalise_text, normalise_word

DATA_DIR = Path(__file__).resolve().parent / "data"
RULES_FILE = DATA_DIR / "grammar_rules.csv"
CORPUS_FILE = DATA_DIR / "parallel_corpus.csv"
_TRUE = {"yes", "true", "1", "verified"}


def _read_verified(path, required):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            return []
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        if not required.issubset(reader.fieldnames):
            return []
        out = []
        for row in reader:
            row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            if row.get("verified", "").casefold() in _TRUE:
                out.append(row)
        return out


def load_grammar_rules(verified_only=False):
    """Load documented rules; optionally restrict to explicitly verified examples.

    General rule descriptions can be useful even before a native speaker validates
    them. Only rows marked verified=yes are eligible for exact-string overrides.
    """
    required = {"rule_id", "direction", "pattern", "description", "example_input", "expected_output", "source", "verified"}
    if verified_only:
        return _read_verified(RULES_FILE, required)
    if not RULES_FILE.exists():
        return []
    with RULES_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            return []
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        if not required.issubset(reader.fieldnames):
            return []
        return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def get_rules_by_direction(rules, direction):
    direction = direction.strip().casefold()
    return [r for r in rules if r.get("direction", "").casefold() in {direction, "both"}]


def load_parallel_pairs():
    rows = _read_verified(CORPUS_FILE, {"english", "izon", "verified"})
    return rows


def _sentence_key(text):
    value = normalise_word(normalise_text(text))
    # Sentence-final punctuation should not prevent an exact pair from matching.
    return value.rstrip(" .!…;:").strip()


def _restore_terminal_punctuation(source, target):
    import re
    match = re.search(r"([.!?…]+)[\s]*$", normalise_text(source))
    if not match:
        return target
    punctuation = match.group(1)
    target = re.sub(r"[.!?…]+$", "", target.rstrip())
    return target + punctuation


def exact_rule_translation(sentence, direction):
    """Apply verified exact sentence pairs/rule examples before word lookup."""
    key = _sentence_key(sentence)
    if not key:
        return None
    # Exact parallel-corpus pairs are strongest when explicitly verified.
    for row in load_parallel_pairs():
        source = row.get("english", "") if direction == "english_to_izon" else row.get("izon", "")
        target = row.get("izon", "") if direction == "english_to_izon" else row.get("english", "")
        if source and target and _sentence_key(source) == key:
            return _restore_terminal_punctuation(sentence, target)
    for row in get_rules_by_direction(load_grammar_rules(verified_only=True), direction):
        source, target = row.get("example_input", ""), row.get("expected_output", "")
        if source and target and _sentence_key(source) == key:
            return _restore_terminal_punctuation(sentence, target)
    return None


def display_rules(rules):
    if not rules:
        print("No verified grammar rules are available yet.")
        return
    for rule in rules:
        print(f"\nRule ID: {rule.get('rule_id', '')}")
        print(f"Direction: {rule.get('direction', '')}")
        print(f"Description: {rule.get('description', '')}")
        print(f"Example: {rule.get('example_input', '')}")
        print(f"Expected output: {rule.get('expected_output', '')}")
        print(f"Evidence status: {rule.get('evidence_status', 'unspecified')}")


if __name__ == "__main__":
    rules = load_grammar_rules()
    verified = load_grammar_rules(verified_only=True)
    print(f"Loaded {len(rules)} documented grammar rules ({len(verified)} with verified exact examples).")
    display_rules(rules)
