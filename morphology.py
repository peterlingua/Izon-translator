"""Source-grounded morphology helpers for the supplied Kolokuma Izon rules.

The functions in this module distinguish exact paradigms and examples supplied by
 the project owner from productive rules that still need fluent-speaker validation.
No rule here claims to cover every Izon noun, adjective, or verb class.
"""
from __future__ import annotations

import csv
import unicodedata
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MORPHOLOGY_FILE = DATA_DIR / "izon_morphology.csv"


def _plain(text: str) -> str:
    """Case-fold, remove combining diacritics, spaces, and separators for matching."""
    value = unicodedata.normalize("NFD", str(text or "").casefold())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return "".join(c for c in value if c.isalnum())


def load_morphology_inventory() -> list[dict[str, str]]:
    """Read the full, human-auditable morphology inventory from CSV."""
    if not MORPHOLOGY_FILE.exists():
        return []
    with MORPHOLOGY_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


# The roots and English meanings below are copied from the user-supplied adjective table.
_ADJECTIVES = {
    "small": {
        "root": "zau", "comparative": "zau-dẹịn", "superlative": "zau-fa",
        "very": "zau-kami", "too": "zaubọwẹmi", "negative": "zaugha", "negative_alt": "zaukumo",
    },
    "expensive": {
        "root": "ganị", "comparative": "ganị-dẹịn", "superlative": "ganị-fa",
        "very": "ganịkami", "too": "ganịbọwẹmi", "negative": "ganịgha", "negative_alt": "ganịkumo",
    },
    "lazy": {
        "root": "sụ", "comparative": "sụ-dẹịn", "superlative": "sụ-fa",
        "very": "sụkami", "too": "sụbọwẹmi", "negative": "sụagha", "negative_alt": "sụkumo",
    },
    "short": {
        "root": "Ikịsá", "comparative": "Ikịsá-dẹịn", "superlative": "Ikịsá-fa",
        "very": "Ikịsákami", "too": "Ikịsábọwẹmi", "negative": "Ikịságha", "negative_alt": "Ikịsákumo",
    },
}
_ADJ_ROOT_TO_ENGLISH = {_plain(v["root"]): k for k, v in _ADJECTIVES.items()}
_EN_ADJ_FORM_TO_TARGET: dict[tuple[str, ...], str] = {}
for _en, _forms in _ADJECTIVES.items():
    _EN_ADJ_FORM_TO_TARGET[(_en,)] = _forms["root"]
    if _en == "small":
        _EN_ADJ_FORM_TO_TARGET[("smaller",)] = _forms["comparative"]
        _EN_ADJ_FORM_TO_TARGET[("smallest",)] = _forms["superlative"]
    elif _en == "expensive":
        _EN_ADJ_FORM_TO_TARGET[("more", "expensive")] = _forms["comparative"]
        _EN_ADJ_FORM_TO_TARGET[("most", "expensive")] = _forms["superlative"]
    elif _en == "lazy":
        _EN_ADJ_FORM_TO_TARGET[("lazier",)] = _forms["comparative"]
        _EN_ADJ_FORM_TO_TARGET[("laziest",)] = _forms["superlative"]
    elif _en == "short":
        _EN_ADJ_FORM_TO_TARGET[("shorter",)] = _forms["comparative"]
        _EN_ADJ_FORM_TO_TARGET[("shortest",)] = _forms["superlative"]
    for _intensifier in ("very", "too", "not"):
        _EN_ADJ_FORM_TO_TARGET[(_intensifier, _en)] = _forms[{
            "very": "very", "too": "too", "not": "negative"
        }[_intensifier]]


def inflect_izon_adjective(base: str, degree: str) -> str:
    """Return a supplied adjective form or apply the documented marker provisionally.

    `degree` accepts positive, comparative, superlative, very, too, negative,
    or negative_alt. Unknown roots use the marker described in the source table;
    that generalization is provisional and should be speaker-checked.
    """
    degree = str(degree or "").casefold().replace(" ", "_")
    for english, forms in _ADJECTIVES.items():
        if _plain(base) == _plain(forms["root"]):
            if degree in {"positive", "base"}:
                return forms["root"]
            if degree in forms:
                return forms[degree]
    suffixes = {
        "comparative": "-dẹịn", "superlative": "-fa", "very": "-kami",
        "too": "bọwẹmi", "negative": "agha", "negative_alt": "kumo",
    }
    if degree in {"positive", "base"}:
        return base
    if degree not in suffixes:
        raise ValueError(f"Unsupported adjective degree: {degree}")
    marker = suffixes[degree]
    if marker.startswith("-"):
        return f"{base}{marker}"
    return f"{base}{marker}"


def match_english_adjective(tokens: list[str], start: int) -> tuple[str, int, str] | None:
    """Match a supplied English adjective/base phrase to its Izon form.

    Returns (Izon form, next token index, English adjective/gloss). This supports
    only the four roots and the forms represented in the supplied reference.
    """
    if start >= len(tokens):
        return None
    # Longest-first handles “more expensive” and “very small” before single words.
    max_n = min(2, len(tokens) - start)
    for n in range(max_n, 0, -1):
        chunk = tuple(str(t).casefold() for t in tokens[start:start+n])
        # Ignore neither punctuation nor word boundaries: a punctuation token won't match.
        target = _EN_ADJ_FORM_TO_TARGET.get(chunk)
        if target:
            gloss = chunk[-1] if chunk[-1] not in {"small", "expensive", "lazy", "short"} else chunk[-1]
            return target, start+n, gloss
    return None


def merge_izon_morphology_tokens(tokens: list[str]) -> list[str]:
    """Join only hyphenated forms whose suffix is explicitly in the supplied rules."""
    markers = {
        "dẹịn", "fa", "ama", "otu", "mo", "amini", "mini", "minimọ", "abàu", "arau", "agha", "kumo", "kami", "bọwẹmi",
    }
    merged: list[str] = []
    i = 0
    while i < len(tokens):
        if i + 2 < len(tokens) and tokens[i+1] in {"-", "‐", "‑"} and _plain(tokens[i+2]) in {_plain(m) for m in markers}:
            merged.append(f"{tokens[i]}-{tokens[i+2]}")
            i += 3
        else:
            merged.append(tokens[i])
            i += 1
    return merged


# Explicit noun examples from the supplied table take precedence over a generic suffix guess.
_EXACT_NOUN_FORMS = {
    "akasimo": ("the chairs", "noun"),
    "ekpetiama": ("boxes", "noun"),
    "ogon'otu": ("visitors", "noun"),
    "ogoniotu": ("visitors", "noun"),
    "kimimo": ("the men", "noun"),
    "oweiamini": ("the men", "noun"),
    "ereabau": ("girl/miss", "noun"),
    "erearau": ("Mrs/madam", "noun"),
    "ereamini": ("the women", "noun"),
    "ereaminimo": ("the women", "noun"),
}
_ADJ_SUFFIXES = [
    ("bọwẹmi", "too"), ("dẹịn", "comparative"), ("minimo", None),
    ("agha", "negative"), ("kumo", "negative"), ("kami", "very"), ("fa", "superlative"),
]
_NOUN_SUFFIXES = [
    ("minimọ", "definite_plural"), ("amini", "definite_plural"),
    ("abàu", "female_singular"), ("arau", "female_title"),
    ("otu", "plural"), ("ama", "indefinite_plural"), ("mini", "definite_plural"), ("mo", "definite_plural"),
]
_IRREGULAR_PLURALS = {
    "man": "men", "male": "men", "woman": "women", "child": "children",
    "person": "people", "foot": "feet", "tooth": "teeth", "mouse": "mice",
    "goose": "geese", "ox": "oxen",
}


def _pluralize_english(word: str) -> str:
    clean = word.strip()
    low = clean.casefold()
    if low in _IRREGULAR_PLURALS:
        result = _IRREGULAR_PLURALS[low]
    elif low.endswith("y") and len(low) > 1 and low[-2] not in "aeiou":
        result = clean[:-1] + "ies"
    elif low.endswith(("s", "x", "z", "ch", "sh")):
        result = clean + "es"
    else:
        result = clean + "s"
    return result


def split_izon_noun_morphology(surface: str) -> tuple[str, str] | None:
    """Separate a source-listed nominal marker from a possible noun base."""
    compact = _plain(surface)
    for marker, feature in _NOUN_SUFFIXES:
        marker_key = _plain(marker)
        if compact.endswith(marker_key) and len(compact) > len(marker_key) + 1:
            # Strip by the number of suffix letters from NFC input; then trim the example hyphen.
            base = surface[:-len(marker_key)]
            base = base.rstrip("-‐‑")
            if base and _plain(base) != compact:
                return base, feature
    return None


def analyze_izon_morphology(
    surface: str,
    lexicon: dict[str, Any] | None = None,
    lookup_records: Callable[[str, str, dict], list[dict]] | None = None,
) -> dict[str, str] | None:
    """Analyze source-listed Izon noun/adjective morphology.

    Exact forms in the supplied document are handled without dictionary guesses.
    For additional marked nouns, a suffix is accepted only when the dictionary
    supplies a noun base. Returns `target`, `pos`, and `feature` or None.
    """
    key = _plain(surface)
    if key in _EXACT_NOUN_FORMS:
        gloss, pos = _EXACT_NOUN_FORMS[key]
        return {"target": gloss, "pos": pos, "feature": "source_example"}

    # The four supplied adjective roots have a known English gloss and known forms.
    for english, forms in _ADJECTIVES.items():
        for degree, izon_form in forms.items():
            if _plain(izon_form) == key:
                if degree == "root":
                    gloss = english
                elif degree == "comparative":
                    gloss = {"small":"smaller", "expensive":"more expensive", "lazy":"lazier", "short":"shorter"}[english]
                elif degree == "superlative":
                    gloss = {"small":"smallest", "expensive":"most expensive", "lazy":"laziest", "short":"shortest"}[english]
                elif degree == "very":
                    gloss = f"very {english}"
                elif degree == "too":
                    gloss = f"too {english}"
                else:
                    gloss = f"not {english}"
                return {"target": gloss, "pos": "adjective", "feature": degree}

    if lexicon is None or lookup_records is None:
        return None
    split = split_izon_noun_morphology(surface)
    if not split:
        return None
    base, feature = split
    records = lookup_records(base, "izon_to_english", lexicon) or []
    noun = next((r for r in records if str(r.get("part_of_speech", "")).casefold().startswith(("n.", "noun"))), None)
    if not noun:
        return None
    english = str(noun.get("english", "")).strip()
    if not english:
        return None
    if feature in {"female_singular", "female_title"}:
        return None  # These forms are listed as titles/special forms, not generic productive inflection.
    plural = _pluralize_english(english)
    if feature == "definite_plural":
        target = "the " + plural
    else:
        target = plural
    return {"target": target, "pos": "noun", "feature": feature}


def inflect_izon_noun(base: str, marker: str) -> str:
    """Append a nominal marker from the source table, preserving its displayed form."""
    marker = str(marker or "").strip()
    supported = {"-mo", "-ama", "-otu", "-amini", "-mini", "-minimọ", "-abàu", "-arau"}
    if marker not in supported:
        raise ValueError(f"Unsupported noun marker: {marker}")
    if marker == "-ama":
        return f"{base}-ama"
    return base + marker[1:]


# Explicit paradigms are safer than pretending these spelling changes are universal.
_VERB_PARADIGMS = {
    "bii": {
        "present": "biinimi", "past": "biịmi", "progressive": "biịyemi",
        "perfect": "biịdọụ", "future": "biiịnghim", "past_progressive": "biitimimi",
        "negative": "biịagha",
    },
    "gee": {
        "present": "gẹẹnimi", "past": "gẹẹmi", "progressive": "gẹẹyemi",
        "perfect": "gẹẹdọụ", "future": "gẹẹnghimi", "past_progressive": "gẹẹtimimi",
        "negative": "gẹẹagha",
    },
    "mu": {
        "present": "munimi", "past": "mumi", "progressive": "muyemi",
        "perfect": "mudọụ", "future": "munghimi", "past_progressive": "mutimimi",
        "negative": "muagha",
    },
}


def conjugate_izon_verb(base: str, form: str) -> str | None:
    """Return a form only for the three explicit sample verb paradigms supplied.

    The Bii future form is transcribed as “biiịnghim” from a split table cell and
    is deliberately not corrected without the source owner/speaker confirming it.
    """
    form_key = str(form or "").casefold().replace("-", "_").replace(" ", "_")
    aliases = {"present_perfect": "perfect", "present_perfective": "perfect", "past_progressive_tense": "past_progressive"}
    form_key = aliases.get(form_key, form_key)
    paradigm = _VERB_PARADIGMS.get(_plain(base))
    if not paradigm:
        return None
    return paradigm.get(form_key)


def adjective_roots() -> dict[str, str]:
    """Return a copy of English adjective root -> supplied Izon root."""
    return {english: forms["root"] for english, forms in _ADJECTIVES.items()}
