"""Inventory of verbal constructions: what is attested, what is not, and why.

This module does not translate. The tense, aspect, and negation suffixes are
applied by morphology.py and sentence_engine.py, using the attested forms in
data/izon_morphology.csv. This module records, for each English verbal
construction, the Izon form the sources support (if any), the source, and a
status. The translator uses it to explain why a sentence is declined.

Statuses:
  attested       - the Izon form appears in a source and the engine applies it
  attested-flag  - the form is in a source but the source marks it for checking
  unsupported    - no attested Izon form exists in the supplied sources
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VerbConstruction:
    name: str
    pattern: str            # regex on lowercase English sentence
    izon_form: str | None   # attested suffix or pattern, or None
    status: str
    source: str
    reason: str


CONSTRUCTIONS: tuple[VerbConstruction, ...] = (
    VerbConstruction(
        "progressive", r"\b(am|is|are|was|were)\s+\w+ing\b", "-yemi (present); -timimi (past)",
        "attested", "USR-TAM-003, USR-TAM-006; EN-AUX-001 corpus example 'I am eating yam'",
        "Progressive suffix applied to the lexical verb."),
    VerbConstruction(
        "past", r"\b\w+ed\b|\bate\b|\bwent\b", "-mi",
        "attested", "USR-TAM-002 (biịmi 'asked')",
        "Past suffix applied; irregular English pasts depend on the verb lexicon."),
    VerbConstruction(
        "perfect", r"\b(have|has)\s+(\w+ed|eaten|gone|come)\b", "-dọụ",
        "attested-flag", "USR-TAM-004 (biịdọụ 'asked'); source marks the label for checking",
        "Present-perfect suffix applied to the lexical verb."),
    VerbConstruction(
        "past_perfect", r"\bhad\s+\w+", None,
        "unsupported", "no source gives a past-perfect Izon form",
        "Past perfect ('had eaten') has no attested Izon form in the supplied sources."),
    VerbConstruction(
        "future", r"\bwill\s+\w+", "-nghimi",
        "attested-flag", "USR-TAM-005 (munghimi 'will go'); source flags the Bii table cell",
        "Future suffix applied; the source marks some future forms for verification."),
    VerbConstruction(
        "negation", r"\b(do|does|did)\s+not\b|\bnot\b|\bn't\b", "-agha",
        "attested", "USR-TAM-007; IZ-NEG-001 (Kolokuma negative -gha)",
        "Negative suffix applied to the verb; do-support is dropped."),
    VerbConstruction(
        "modal_can", r"\bcan\b|\bcould\b", None,
        "unsupported", "no modal verb (can/could) appears in any supplied source",
        "Modal 'can' has no attested Izon form."),
    VerbConstruction(
        "modal_must", r"\bmust\b|\bshould\b|\bmay\b|\bmight\b", None,
        "unsupported", "no modal verb (must/should/may/might) appears in any supplied source",
        "Modal 'must/should/may' has no attested Izon form."),
    VerbConstruction(
        "want_need_to", r"\b(want|need|wish|like|hope)\s+to\b", None,
        "unsupported", "dictionary gives dọụ́ 'need; want' only with a noun object",
        "'want/need to + verb' (infinitive complement) has no attested Izon pattern."),
    VerbConstruction(
        "passive", r"\b(was|were|is|are|been|be)\s+\w+(ed|en)\b.*\bby\b", None,
        "unsupported", "IZ-VOICE-001 documents one Izon-to-English passive example only",
        "English-to-Izon passive is not attested; the single documented example is Izon-to-English."),
)


def diagnose(sentence: str, direction: str = "english_to_izon") -> str | None:
    """Return a reason string for the first unsupported construction found.

    Returns None when no unsupported construction is detected (the caller
    then keeps its generic message). Only English-to-Izon constructions are
    diagnosed here; Izon-to-English is handled by the Izon lexicon.
    """
    if direction != "english_to_izon":
        return None
    text = str(sentence or "").lower()
    for construction in CONSTRUCTIONS:
        if construction.status == "unsupported" and re.search(construction.pattern, text):
            return f"Construction '{construction.name}': {construction.reason}"
    return None


def inventory() -> list[dict]:
    """Return the full construction inventory as plain dictionaries."""
    return [construction.__dict__.copy() for construction in CONSTRUCTIONS]
