"""Dictionary loading and bidirectional phrase lookup.

The main source is data/izon_dictionary_a_z.csv, with columns:
Izon Word, Part of Speech, English Meaning.
"""
import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict
from tokenizer import tokenize, normalise_word

DATA_DIR = Path(__file__).resolve().parent / "data"
DICTIONARY_FILE = DATA_DIR / "izon_dictionary_a_z.csv"
LEGACY_LEXICON_FILE = DATA_DIR / "lexicon.csv"

# Superscript numerals and editorial reference numbers distinguish dictionary
# entries, but are not normally typed as part of the word in running text.
_SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
_SUPERSCRIPT_TABLE = str.maketrans({c: "" for c in _SUPERSCRIPT_DIGITS})


def normalise_key(text: str) -> str:
    return normalise_word(text).translate(_SUPERSCRIPT_TABLE)


def strip_diacritics(text: str) -> str:
    """Return a tone/diacritic-insensitive key for typing without tone marks.

    Exact, tone-aware lookup is always preferred. This key is a fallback only:
    Izon tone and vowel quality can distinguish words, so a fallback can be
    ambiguous and should not replace the source spelling in the dictionary.
    """
    value = unicodedata.normalize("NFD", normalise_key(text))
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def _token_key(text: str) -> tuple[str, ...]:
    return tuple(normalise_key(t) for t in tokenize(text))


def _plain_token_key(text: str) -> tuple[str, ...]:
    return tuple(strip_diacritics(t) for t in tokenize(text))


def _clean_headword(headword: str) -> str:
    """Remove editorial footnote markers while preserving tone/diacritics."""
    value = unicodedata.normalize("NFC", (headword or "").strip())
    # Drop square-bracketed reference/tone annotations.
    value = re.sub(r"\s*\[[^\]]*\]", "", value)
    # Editorial parenthetical aliases are handled separately; remove the note first.
    value = re.sub(r"\s*\([^)]*\)\s*$", "", value).strip()
    # Drop superscript and ordinary reference numerals at the end of headwords.
    value = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+$", "", value).strip()
    value = re.sub(r"\s*\d+$", "", value).strip()
    return value.strip(" \t\r\n,;.!?")


def _repair_split_final_vowel(value: str) -> str:
    """Repair a common source-formatting artefact like ``wár ị`` -> ``wárị``.

    Only a final one-letter token that has combining-mark spelling in NFD is
    joined. Ordinary multiword entries and grammatical particles remain apart.
    The original headword is still preserved in each dictionary record.
    """
    value = unicodedata.normalize("NFC", (value or "").strip())
    parts = value.split()
    if len(parts) == 2 and len(strip_diacritics(parts[-1])) == 1:
        decomposed = unicodedata.normalize("NFD", parts[-1])
        if any(unicodedata.category(ch) == "Mn" for ch in decomposed):
            return parts[0] + parts[-1]
    return value


def _headword_aliases(headword: str) -> list[str]:
    raw = unicodedata.normalize("NFC", (headword or "").strip())
    aliases = []
    primary = _clean_headword(raw)
    if primary:
        aliases.append(_repair_split_final_vowel(primary))
        # Retain the literal spaced source form as an input alias when a source
        # export has split off a marked final vowel.
        if primary != aliases[0]:
            aliases.append(primary)
        if primary.startswith("-") and len(primary) > 1:
            aliases.append(primary[1:])
    # Recognize common dictionary synonym notation, e.g. (= bá).
    for match in re.finditer(r"\(\s*=\s*([^)]*?)\s*\)", raw):
        alias = _clean_headword(match.group(1))
        if alias:
            aliases.append(alias)
    # Deduplicate case-insensitively but keep original spellings for display.
    result, seen = [], set()
    for alias in aliases:
        key = normalise_key(alias)
        if key and key not in seen:
            seen.add(key); result.append(alias)
    return result


def _strip_editorial_gloss(gloss: str) -> str:
    value = unicodedata.normalize("NFC", (gloss or "").strip())
    # Editorial parenthetical introductions sometimes precede the real senses
    # after a colon, as in "(a greeting): A. welcome; B. thank you".
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"\[[^]]*\]", "", value)
    if ":" in value:
        before, after = value.split(":", 1)
        before_clean = re.sub(
            r"^(?:(?:t|i|p|a|cs|ben|dir|id|pl|acc|emph|m\.f|m|f|n|masc|fem|neut|loc|aux|fig|usu|esp|lit|arch|rare)\.\s*)+",
            "", before, flags=re.I
        )
        before_clean = re.sub(r"^(?:[A-Z]\.\s*)+", "", before_clean)
        # Usually the pre-colon material is a gloss and the post-colon material
        # is an example. But if annotations left no gloss before the colon,
        # retain the compact definition after it.
        value = before_clean if before_clean.strip(" ,;:-") else after
    # Dictionary usage labels ("loc. come", "aux. begin to", "fig. ...") are
    # not part of the English gloss and must not reach the output.
    value = re.sub(
        r"^(?:(?:t|i|p|a|cs|ben|dir|id|pl|acc|emph|m\.f|m|f|n|masc|fem|neut|loc|aux|fig|usu|esp|lit|arch|rare)\.\s*)+",
        "", value, flags=re.I
    )
    value = re.sub(r"^(?:[A-Z]\.\s*)+", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ,;:-()")
    return value


def primary_english_meaning(gloss: str) -> str:
    """Return the first compact gloss rather than an entire definition clause."""
    value = _strip_editorial_gloss(gloss)
    if not value:
        return ""
    # The semicolon commonly separates independent senses/derived expressions.
    value = re.split(r"\s*;\s*", value, maxsplit=1)[0].strip()
    # The first comma-delimited item is normally the short head gloss. This
    # avoids returning editorial expansions such as "bird, the curlew".
    if "," in value:
        value = value.split(",", 1)[0].strip()
    value = re.sub(r"\s+", " ", value).strip(" ,;:-()")
    return value


def _english_variants(gloss: str) -> list[str]:
    """Build inverse aliases from compact senses while excluding examples.

    The dictionary often follows a short gloss with Izon phrases and example
    sentences. Do not mine every later English word from that explanatory text:
    it creates bad homonym choices (e.g. a verb whose example merely says
    "give" becoming the first translation for English *give*).
    """
    cleaned = _strip_editorial_gloss(gloss)
    if not cleaned:
        return []

    candidates: list[str] = []
    saw_example = False
    for segment in cleaned.split(";"):
        raw_segment = segment.strip()
        section_label = bool(re.match(r"^(?:[A-Z]|[ivx]+)\.\s*", raw_segment, flags=re.I))
        segment = re.sub(r"^(?:(?:[A-Z]|[ivx]+)\.\s*)+", "", raw_segment, flags=re.I).strip()
        segment = re.sub(r"^\([^)]*\)\s*", "", segment).strip()
        if not segment:
            continue
        words = tokenize(segment)
        contains_marked_izon = any(ch in segment for ch in "ịọụẹ" ) or any(
            unicodedata.category(ch) == "Mn" for ch in unicodedata.normalize("NFD", segment)
        )
        if len(words) > 6 or contains_marked_izon:
            # A subsequent explicitly-labelled A./B./C. sense can still be a
            # compact dictionary definition (e.g. "B. book, paper"). Other
            # later segments are usually just continuations of the example.
            saw_example = True
            continue
        if saw_example and not section_label:
            break
        for part in segment.split(","):
            candidate = re.sub(r"\([^)]*\)|\[[^]]*\]", "", part).strip(" ,;:-")
            candidate = re.sub(r"\s+", " ", candidate)
            part_words = tokenize(candidate)
            if not candidate or not part_words or len(part_words) > 4:
                continue
            if candidate.casefold().startswith(("the ", "a ", "an ", "usu ", "esp ", "e.g. ", "of ", "as ")):
                continue
            if any(ch in candidate for ch in "=<>[]") or ":" in candidate:
                continue
            if candidate.casefold() in {"a", "an", "the", "of", "to", "in", "on", "at", "or", "and"}:
                continue
            candidates.append(candidate)

    variants, seen = [], set()
    for candidate in candidates:
        key = tuple(normalise_word(t) for t in tokenize(candidate))
        if key and key not in seen:
            seen.add(key)
            variants.append(candidate)
    return variants


def _read_dictionary_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"Dictionary has no header: {path}")
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        required = {"Izon Word", "Part of Speech", "English Meaning"}
        if not required.issubset(reader.fieldnames):
            raise ValueError(f"Expected dictionary columns {sorted(required)}; found {reader.fieldnames}")
        for row in reader:
            yield {str(k or "").strip(): (v or "").strip() for k, v in row.items()}


def load_lexicon(verbose: bool = False):
    """Load source dictionary into an indexed lexicon; preserves all senses.

    Returned object is a dict with `entries`, `izon_index`, and `english_index`.
    Entries are dictionary records with aliases and compact glosses.
    """
    entries, izon_index, english_index = [], defaultdict(list), defaultdict(list)
    izon_plain_index, english_plain_index = defaultdict(list), defaultdict(list)
    izon_joined_plain_index, english_joined_plain_index = defaultdict(list), defaultdict(list)
    if DICTIONARY_FILE.exists():
        total = 0
        for row in _read_dictionary_csv(DICTIONARY_FILE):
            total += 1
            headword = row.get("Izon Word", "").strip()
            full_gloss = row.get("English Meaning", "").strip()
            pos = row.get("Part of Speech", "").strip()
            if not headword or not full_gloss:
                continue
            compact = primary_english_meaning(full_gloss)
            canonical_izon = next(iter(_headword_aliases(headword)), headword)
            if not any(unicodedata.category(ch).startswith("L") for ch in canonical_izon):
                # The source export contains occasional reference-only rows
                # (e.g. headword "4") that are not lexical entries.
                continue
            record = {"izon": headword, "canonical_izon": canonical_izon, "english": compact or full_gloss,
                      "full_english": full_gloss, "part_of_speech": pos,
                      "notes": "", "source": "izon_dictionary_a_z.csv"}
            entries.append(record)
            for alias in _headword_aliases(headword):
                key = tuple(normalise_word(t) for t in tokenize(alias))
                if key:
                    izon_index[key].append(record)
                    izon_plain_index[tuple(strip_diacritics(t) for t in key)].append(record)
                    joined = "".join(ch for ch in strip_diacritics(" ".join(key)) if ch.isalnum())
                    if joined:
                        izon_joined_plain_index[joined].append(record)
            # Leading-hyphen headwords are affixes/clitics; do not present them
            # as standalone outputs for ordinary English word lookup.
            if not canonical_izon.startswith("-"):
                for variant in _english_variants(full_gloss):
                    key = tuple(normalise_key(t) for t in tokenize(variant))
                    if key:
                        english_index[key].append(record)
                        english_plain_index[tuple(strip_diacritics(t) for t in key)].append(record)
                        joined = "".join(ch for ch in strip_diacritics(" ".join(key)) if ch.isalnum())
                        if joined:
                            english_joined_plain_index[joined].append(record)
        source_name = DICTIONARY_FILE.name
    elif LEGACY_LEXICON_FILE.exists():
        total = 0
        with LEGACY_LEXICON_FILE.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                total += 1
                izon = (row.get("izon") or "").strip()
                english = (row.get("english") or "").strip()
                if not izon or not english:
                    continue
                record = {"izon": izon, "canonical_izon": izon, "english": english, "full_english": english,
                          "part_of_speech": (row.get("part_of_speech") or "").strip(),
                          "notes": (row.get("notes") or "").strip(), "source": "lexicon.csv"}
                entries.append(record)
                izon_key = tuple(normalise_word(t) for t in tokenize(izon))
                english_key = tuple(normalise_word(t) for t in tokenize(english))
                izon_index[izon_key].append(record)
                english_index[english_key].append(record)
                izon_plain_index[tuple(strip_diacritics(t) for t in izon_key)].append(record)
                english_plain_index[tuple(strip_diacritics(t) for t in english_key)].append(record)
                izon_joined = "".join(ch for ch in strip_diacritics(" ".join(izon_key)) if ch.isalnum())
                english_joined = "".join(ch for ch in strip_diacritics(" ".join(english_key)) if ch.isalnum())
                if izon_joined:
                    izon_joined_plain_index[izon_joined].append(record)
                if english_joined:
                    english_joined_plain_index[english_joined].append(record)
        source_name = LEGACY_LEXICON_FILE.name
    else:
        raise FileNotFoundError(f"No dictionary found. Expected {DICTIONARY_FILE}")

    # Curated supplement (family terms and basic vocabulary). Each row carries
    # its source and status. Supplement records are placed FIRST in English
    # lookups so a curated gloss beats an unrelated dictionary sense
    # (e.g. "man" -> kìmí rather than "human being").
    supplement_file = DICTIONARY_FILE.parent / "lexicon_supplement.csv"
    if supplement_file.exists():
        with supplement_file.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                english = (row.get("english") or "").strip()
                izon = (row.get("izon") or "").strip()
                if not english or not izon:
                    continue
                record = {"izon": izon, "canonical_izon": izon, "english": english,
                          "full_english": english,
                          "part_of_speech": (row.get("part_of_speech") or "").strip(),
                          "notes": (row.get("notes") or "").strip(),
                          "status": (row.get("status") or "").strip(),
                          "source": "lexicon_supplement.csv"}
                entries.append(record)
                key = tuple(normalise_key(t) for t in tokenize(english))
                if key:
                    english_index[key].insert(0, record)
                    english_plain_index[tuple(strip_diacritics(t) for t in key)].insert(0, record)
                    joined = "".join(ch for ch in strip_diacritics(" ".join(key)) if ch.isalnum())
                    if joined:
                        english_joined_plain_index[joined].insert(0, record)
                izon_key = tuple(normalise_word(t) for t in tokenize(izon))
                if izon_key:
                    izon_index[izon_key].append(record)
                    izon_plain_index[tuple(strip_diacritics(t) for t in izon_key)].append(record)
                    joined_i = "".join(ch for ch in strip_diacritics(" ".join(izon_key)) if ch.isalnum())
                    if joined_i:
                        izon_joined_plain_index[joined_i].append(record)

    result = {"entries": entries, "izon_index": dict(izon_index),
              "english_index": dict(english_index),
              "izon_plain_index": dict(izon_plain_index),
              "english_plain_index": dict(english_plain_index),
              "izon_joined_plain_index": dict(izon_joined_plain_index),
              "english_joined_plain_index": dict(english_joined_plain_index),
              "source": source_name, "row_count": total}
    if verbose:
        print(f"Dictionary source: {source_name}")
        print(f"Source rows: {total}; usable entries: {len(entries)}")
        print(f"Unique Izon lookup forms: {len(izon_index)}")
        print(f"Unique English lookup forms: {len(english_index)}")
        print(f"Tone-insensitive Izon fallback forms: {len(izon_plain_index)}")
    return result


def lookup_izon_word(word, lexicon):
    """Find an Izon word/phrase, falling back to an accentless key if needed."""
    key = tuple(normalise_key(t) for t in tokenize(word))
    exact = lexicon.get("izon_index", {}).get(key, [])
    if exact:
        return exact
    plain_key = tuple(strip_diacritics(t) for t in tokenize(word))
    return lexicon.get("izon_plain_index", {}).get(plain_key, [])


def lookup_english_word(word, lexicon):
    """Find English wording with an exact lookup before fallback lookup."""
    key = tuple(normalise_key(t) for t in tokenize(word))
    exact = lexicon.get("english_index", {}).get(key, [])
    if exact:
        return exact
    plain_key = tuple(strip_diacritics(t) for t in tokenize(word))
    return lexicon.get("english_plain_index", {}).get(plain_key, [])


if __name__ == "__main__":
    lexicon = load_lexicon(verbose=True)
    word = input("Enter an Izon word or phrase (Enter to skip): ").strip()
    if word:
        for entry in lookup_izon_word(word, lexicon):
            print(f'{entry["izon"]} -> {entry["english"]} [{entry["part_of_speech"]}]')
