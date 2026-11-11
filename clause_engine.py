"""Compound and complex sentence composition for Kolokuma Izon <-> English.

This module sits between the exact sentence-pair lookup and the single-clause
transfer engine (sentence_engine.py). It:

1. splits a sentence at a connective it recognizes,
2. translates each clause with the single-clause engine,
3. recombines the clauses using the connective pattern.

Connectives come only from the owner-supplied sentence-pair corpus
(data/parallel_corpus.csv). Their counts are noted below. Nothing here is a
general parser: anything outside the recognized patterns returns None so that
the caller can fall back to its existing, explicitly flagged behaviour.

Patterns (English -> Izon), as attested in the corpus:
    "X, and Y"          -> "X, gbá Y"           (and)
    "X, but Y"          -> "X, ọ̀kpọ̀ Y"          (but)   [18 corpus uses]
    "X, so Y"           -> "X, ọ́bọ́ Y"           (so)    [8 corpus uses]
    "Because X, Y"      -> "Bárá X fịẹ́ị, Y"      (because, clause-initial) [9]
    "While X, Y"        -> "X ásáìn, Y"         (while)  [7]
    "Y because X"       -> "Y bá X fịẹ́ị"         (because, clause-final)  [9]

The Izon-to-English direction applies the same patterns in reverse.

Known limits (documented, not hidden):
- Only one level of each pattern is combined per clause; deeper nesting is
  handled by recursion only where the pattern is unambiguous.
- A "because" clause that is not sentence-final is declined, because the
  corpus only attests it in final position.
- Clause translations come from sentence_engine, so unknown vocabulary still
  makes the whole compound decline.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Callable, Optional

from tokenizer import tokenize, detokenize


def _key(text: str) -> str:
    """Tone-exact, case-insensitive key (NFC). Never strips tone marks."""
    return unicodedata.normalize("NFC", str(text)).casefold()


# --- Connectives (tone-exact) ----------------------------------------------
EN_TO_IZON_COORDINATOR = {
    "and": "gbá",
    "but": "ọ̀kpọ̀",
    "so": "ọ́bọ́",
}
# Izon-side keys include every spelling attested in the corpus. ``ókpó`` (head)
# is deliberately NOT here: it shares the plain letters of ``ọ̀kpọ̀`` but has
# a different tone and meaning.
IZON_TO_EN_COORDINATOR = {
    _key("gbá"): "and",
    _key("gbà"): "and",
    _key("ọ̀kpọ̀"): "but",
    _key("kọ́"): "but",
    _key("kọ̀"): "but",
    _key("ọ́bọ́"): "so",
    _key("ọ̀bọ̀"): "so",
}
IZON_BECAUSE_OPEN = _key("bárá")
IZON_BECAUSE_CLOSE = _key("fịẹ́ị")
IZON_BECAUSE_MID = _key("bá")
IZON_WHILE = _key("ásáìn")

_CONNECTIVE_KEYS = set(IZON_TO_EN_COORDINATOR) | {IZON_BECAUSE_OPEN, IZON_BECAUSE_MID, IZON_WHILE, IZON_BECAUSE_CLOSE}

# --- English patterns (applied to raw text, final punctuation removed) ------
_EN_LEAD = re.compile(r"^(because|while)\s+(.+?),\s+(.+)$", re.IGNORECASE)
_EN_COORD = re.compile(r",\s+(and|but|so)\s+", re.IGNORECASE)
_EN_BECAUSE_MID = re.compile(r"^(.+?)\s+because\s+(.+)$", re.IGNORECASE)
_EN_SUBORDINATOR = re.compile(r"\b(because|while)\b", re.IGNORECASE)

ClauseFn = Callable[[str, str, dict], Optional[str]]


_COMBINING = "\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff"
# A combining tone/dot mark that is not attached to a letter (a space or the
# start of a token precedes it) indicates a malformed dictionary headword.
_STRAY_MARK = re.compile(rf"(^|\s)[{_COMBINING}]")


def _is_malformed(text: str) -> bool:
    return bool(_STRAY_MARK.search(text))


def _default_clause(text: str, direction: str, lexicon: dict) -> Optional[str]:
    """Translate one simple clause: verified corpus pair first, then the rule engine."""
    from grammar import exact_rule_translation
    from sentence_engine import translate_sentence_by_rules

    # A simple clause that is itself a verified corpus sentence (e.g. "She is
    # washing the plates.") is used as-is. This is owner-verified data, so it
    # is preferred to a rule-generated form.
    attested = exact_rule_translation(text, direction)
    if attested:
        return attested.rstrip(" .!…")

    out = translate_sentence_by_rules(text, direction, lexicon)
    if not out:
        return None
    if any(marker in out for marker in ("[UNKNOWN", "[UNSUPPORTED", "[AMBIGUOUS")):
        return None
    if _is_malformed(out):
        return None
    return out.rstrip(" .!…")


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _lower(text: str) -> str:
    """Lowercase the first letter of an embedded clause, keeping ``I`` as is."""
    if not text:
        return text
    first_word = text.split(" ", 1)[0]
    if first_word == "I" or first_word.startswith("I'"):
        return text
    return text[:1].lower() + text[1:]


def _split_final(sentence: str) -> tuple[str, str]:
    text = str(sentence or "").strip()
    if text and text[-1] in ".!…":
        return text[:-1].rstrip(), text[-1]
    return text, ""


# ---------------------------------------------------------------------------
# English -> Izon
# ---------------------------------------------------------------------------

def _has_english_structure(text: str) -> bool:
    return bool(_EN_LEAD.match(text) or _EN_COORD.search(text) or _EN_BECAUSE_MID.match(text))


def _en_to_izon(text: str, clause: ClauseFn, lexicon: dict) -> Optional[str]:
    text = text.strip()
    if not text or "?" in text:
        return None

    lead = _EN_LEAD.match(text)
    if lead:
        conj, sub, main = lead.group(1).lower(), lead.group(2), lead.group(3)
        if _EN_SUBORDINATOR.search(sub) or _EN_COORD.search(sub):
            return None
        sub_izon = clause(sub, "english_to_izon", lexicon)
        main_izon = _en_to_izon(main, clause, lexicon)
        if sub_izon is None or main_izon is None:
            return None
        if conj == "because":
            # Corpus: "Bárá fáí mị lá èmí fịẹ́ị, dádá bóẹ̀mị, ..."
            return f"Bárá {_lower(sub_izon)} fịẹ́ị, {_lower(main_izon)}"
        # Corpus: "Áràú séíẹ̀mị ásáìn, ówú béí kóró bóẹ̀mị, ..."
        return f"{_cap(sub_izon)} ásáìn, {_lower(main_izon)}"

    coord = _EN_COORD.search(text)
    if coord:
        left, conj, right = text[:coord.start()], coord.group(1).lower(), text[coord.end():]
        # A subordinate clause that is not sentence-final is not attested, so decline.
        if not left.strip() or not right.strip() or _EN_SUBORDINATOR.search(left):
            return None
        left_izon = _en_to_izon(left, clause, lexicon)
        right_izon = _en_to_izon(right, clause, lexicon)
        if left_izon is None or right_izon is None:
            return None
        return f"{_cap(left_izon)}, {EN_TO_IZON_COORDINATOR[conj]} {_lower(right_izon)}"

    because = _EN_BECAUSE_MID.match(text)
    if because:
        main, sub = because.group(1), because.group(2)
        if _EN_SUBORDINATOR.search(sub) or _EN_COORD.search(sub) or _EN_SUBORDINATOR.search(main):
            return None
        main_izon = _en_to_izon(main, clause, lexicon)
        sub_izon = clause(sub, "english_to_izon", lexicon)
        if main_izon is None or sub_izon is None:
            return None
        # Corpus: "... gbá ú búrú ké píríẹ̀mị bá áràú gbọ̀mọ́ èmí fịẹ́ị."
        return f"{main_izon} bá {_lower(sub_izon)} fịẹ́ị"

    return clause(text, "english_to_izon", lexicon)


# ---------------------------------------------------------------------------
# Izon -> English (token level, because Izon connectives are single words)
# ---------------------------------------------------------------------------

def _find(keys: list[str], target: str) -> Optional[int]:
    for index, key in enumerate(keys):
        if key == target:
            return index
    return None


def _iz_to_en_tokens(tokens: list[str], clause: ClauseFn, lexicon: dict) -> Optional[str]:
    if not tokens:
        return None
    keys = [_key(t) for t in tokens]

    # Clause-initial "Bárá X fịẹ́ị, Y" -> "Because x, y".
    if keys[0] == IZON_BECAUSE_OPEN:
        close = _find(keys, IZON_BECAUSE_CLOSE)
        if close is None or close + 1 >= len(tokens) or tokens[close + 1] != ",":
            return None
        sub, main = tokens[1:close], tokens[close + 2:]
        if not sub or not main:
            return None
        sub_en = clause(detokenize(sub), "izon_to_english", lexicon)
        main_en = _iz_to_en_tokens(main, clause, lexicon)
        if sub_en is None or main_en is None:
            return None
        return f"Because {_lower(sub_en)}, {_lower(main_en)}"

    # "X ásáìn, Y" -> "While x, y".
    while_index = _find(keys, IZON_WHILE)
    if while_index is not None:
        if while_index + 1 >= len(tokens) or tokens[while_index + 1] != ",":
            return None
        sub, main = tokens[:while_index], tokens[while_index + 2:]
        if not sub or not main:
            return None
        sub_en = clause(detokenize(sub), "izon_to_english", lexicon)
        main_en = _iz_to_en_tokens(main, clause, lexicon)
        if sub_en is None or main_en is None:
            return None
        return f"While {_lower(sub_en)}, {_lower(main_en)}"

    # Coordinators: "X, gbá Y" -> "X, and y".
    for index, key in enumerate(keys):
        if key in IZON_TO_EN_COORDINATOR:
            left = tokens[:index]
            if left and left[-1] == ",":
                left = left[:-1]
            right = tokens[index + 1:]
            if not left or not right:
                return None
            # Subordinate markers in the left conjunct are not attested here.
            if any(k in {IZON_BECAUSE_OPEN, IZON_BECAUSE_MID, IZON_WHILE} for k in keys[:index]):
                return None
            left_en = _iz_to_en_tokens(left, clause, lexicon)
            right_en = _iz_to_en_tokens(right, clause, lexicon)
            if left_en is None or right_en is None:
                return None
            return f"{_cap(left_en)}, {IZON_TO_EN_COORDINATOR[key]} {_lower(right_en)}"

    # Clause-final "Y bá X fịẹ́ị" -> "y because x".
    mid = _find(keys, IZON_BECAUSE_MID)
    if mid is not None:
        if keys[-1] != IZON_BECAUSE_CLOSE:
            return None
        main, sub = tokens[:mid], tokens[mid + 1:-1]
        if not main or not sub:
            return None
        main_en = _iz_to_en_tokens(main, clause, lexicon)
        sub_en = clause(detokenize(sub), "izon_to_english", lexicon)
        if main_en is None or sub_en is None:
            return None
        return f"{main_en} because {_lower(sub_en)}"

    return clause(detokenize(tokens), "izon_to_english", lexicon)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def translate_compound(sentence: str, direction: str, lexicon: dict,
                       clause: ClauseFn | None = None) -> Optional[str]:
    """Translate a compound or complex sentence, or return None to decline.

    Returns None for simple sentences, so the single-clause engine handles them.
    """
    clause = clause or _default_clause
    text, final = _split_final(sentence)
    if not text or "?" in text:
        return None

    if direction == "english_to_izon":
        if not _has_english_structure(text):
            return None
        result = _en_to_izon(text, clause, lexicon)
    elif direction == "izon_to_english":
        tokens = [t for t in tokenize(text)]
        if not tokens or "?" in tokens:
            return None
        if not any(_key(t) in _CONNECTIVE_KEYS for t in tokens):
            return None
        result = _iz_to_en_tokens(tokens, clause, lexicon)
    else:
        return None

    if not result:
        return None
    return _cap(result) + final
