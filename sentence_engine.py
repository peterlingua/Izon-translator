"""Conservative sentence-level reordering for Kolokuma Izon <-> English.

This is a small rule-based transfer component, not a statistical/LLM translator.
It applies only when it can identify one main verb. Exact verified sentence pairs
are handled first by grammar.py. Lexical ambiguity and Izon morphophonology mean
that generated forms still need native-speaker review.
"""
from __future__ import annotations

from typing import Any

from tokenizer import tokenize, detokenize, normalise_word
from lexicon import normalise_key, strip_diacritics, primary_english_meaning
from morphology import (analyze_izon_morphology, conjugate_izon_verb, match_english_adjective, merge_izon_morphology_tokens)


# English surface forms used for a small, deterministic fallback lemmatizer.
_EN_IRREGULAR_LEMMA = {
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be", "been": "be",
    "ate": "eat", "eaten": "eat", "went": "go", "gone": "go", "ran": "run",
    "gave": "give", "given": "give", "bought": "buy", "brought": "bring",
    "saw": "see", "seen": "see", "made": "make", "came": "come", "came": "come",
    "died": "die", "slept": "sleep", "sat": "sit", "wrote": "write", "written": "write",
    "left": "leave", "took": "take", "taken": "take", "did": "do", "does": "do",
    "had": "have", "has": "have", "held": "hold", "told": "tell", "said": "say",
    "cut": "cut", "put": "put", "read": "read", "knew": "know", "known": "know",
    "drank": "drink", "drunk": "drink", "spoke": "speak", "spoken": "speak",
    "found": "find", "thought": "think", "caught": "catch", "taught": "teach",
    "felt": "feel", "kept": "keep", "lost": "lose", "won": "win", "stood": "stand",
}

_EN_PAST = {
    "be": "was", "come": "came", "go": "went", "run": "ran", "eat": "ate",
    "give": "gave", "buy": "bought", "bring": "brought", "see": "saw", "make": "made",
    "die": "died", "sleep": "slept", "sit": "sat", "write": "wrote", "leave": "left",
    "take": "took", "do": "did", "have": "had", "hold": "held", "tell": "told",
    "say": "said", "cut": "cut", "put": "put", "read": "read", "know": "knew",
    "drink": "drank", "speak": "spoke", "find": "found", "think": "thought",
    "catch": "caught", "teach": "taught", "feel": "felt", "keep": "kept", "lose": "lost",
    "win": "won", "stand": "stood", "travel": "travelled",
}

_EN_ING = {
    "be": "being", "come": "coming", "go": "going", "run": "running", "eat": "eating",
    "give": "giving", "buy": "buying", "see": "seeing", "make": "making", "die": "dying",
    "sleep": "sleeping", "sit": "sitting", "write": "writing", "leave": "leaving",
    "take": "taking", "do": "doing", "have": "having", "cut": "cutting", "put": "putting",
    "read": "reading", "know": "knowing", "walk": "walking", "talk": "talking",
    "travel": "travelling",
}

_EN_AUX = {"am", "is", "are", "was", "were", "be", "been", "being", "do", "does", "did", "have", "has", "will", "shall"}
_EN_NEG = {"not", "n't", "dont", "don't", "doesnt", "doesn't", "didnt", "didn't", "cannot", "can't"}
_EN_PREPOSITIONS = {"in", "on", "at", "under", "over", "inside", "outside", "near", "from", "to", "with", "for", "by", "behind", "beside", "into", "onto", "through"}
_EN_ARTICLES = {"the", "a", "an"}
_EN_PRONOUNS = {
    # Preferred defaults are transcribed from the project owner's pronoun table.
    # English case/number ambiguity remains; see data/izon_morphology.csv.
    "i": "Àri", "me": "Ì", "my": "Ìnè", "mine": "Ìnei",
    "you": "Ári", "your": "Ínè", "yours": "Ìnei",
    "he": "Eri", "him": "Wò", "his": "Wòi",
    "she": "arau", "her": "árà", "hers": "árà",
    "it": "u", "we": "Woni", "us": "wó", "our": "Wó", "ours": "Woi",
    "they": "Ọ̀mịnị", "them": "Ò", "their": "oro", "theirs": "ọ̀rèi",
}
_IZON_INITIAL_PRONOUNS = {"ari": "I", "eri": "he", "omini": "they", "woni": "we", "wonì": "we", "ọmini": "they"}
_EN_BASE_VERBS = set(_EN_PAST) | set(_EN_ING) | set(_EN_IRREGULAR_LEMMA.values()) | {
    "eat", "kill", "love", "like", "want", "need", "see", "know", "work", "play", "read", "drink",
    "write", "walk", "talk", "say", "make", "give", "take", "open", "close", "help", "come", "leave",
}

# Tense endings are deliberately narrow. `-mi` is used only when the remaining
# stem is found as a verb in the dictionary; `-yemi` is based on an attested
# progressive example (e.g. bóyemi, “is coming”).
_IZON_SUFFIXES = (
    ("timimi", "past_progressive"), ("nghimi", "future"),
    ("dọụ", "perfect"), ("dọu", "perfect"),
    ("yemi", "progressive"), ("yemị", "progressive"),
    ("nimi", "present"), ("nimị", "present"),
    ("mé", "past"), ("me", "past"), ("mi", "past"), ("mị", "past"),
)


def _pos(record: dict[str, Any]) -> str:
    return (record.get("part_of_speech") or "").strip().casefold()


def _is_verb(record: dict[str, Any]) -> bool:
    return _pos(record).startswith("v.") or _pos(record).startswith("verb")


def _is_noun(record: dict[str, Any]) -> bool:
    return _pos(record).startswith("n.") or _pos(record).startswith("noun")


def _index_match(phrase_tokens: list[str], direction: str, lexicon: dict) -> list[dict] | None:
    strict_name = "english_index" if direction == "english_to_izon" else "izon_index"
    plain_name = "english_plain_index" if direction == "english_to_izon" else "izon_plain_index"
    strict_key = tuple(normalise_key(t) for t in phrase_tokens)
    strict = lexicon.get(strict_name, {}).get(strict_key)
    if strict:
        return strict
    plain_key = tuple(strip_diacritics(t) for t in phrase_tokens)
    return lexicon.get(plain_name, {}).get(plain_key)


def _joined_match(surface: str, direction: str, lexicon: dict) -> list[dict]:
    joined = "".join(ch for ch in strip_diacritics(surface) if ch.isalnum())
    key_name = "english_joined_plain_index" if direction == "english_to_izon" else "izon_joined_plain_index"
    return lexicon.get(key_name, {}).get(joined, [])


def _lookup_base(surface: str, direction: str, lexicon: dict) -> list[dict]:
    found = _index_match([surface], direction, lexicon)
    if found:
        return found
    return _joined_match(surface, direction, lexicon)


def _english_lemma(surface: str) -> tuple[str, str | None]:
    word = normalise_word(surface).strip("-'’")
    if word in _EN_IRREGULAR_LEMMA:
        lemma = _EN_IRREGULAR_LEMMA[word]
        feature = "progressive" if word in {"being"} else (
            "perfect" if word in {
                "been", "eaten", "gone", "given", "bought", "brought", "seen", "made",
                "written", "taken", "known", "drunk", "spoken", "found", "thought", "caught",
                "taught", "felt", "kept", "lost", "won", "stood", "done", "held", "told", "said"
            } else ("past" if word in {
                "was", "were", "ate", "went", "ran", "gave", "bought", "brought", "saw", "made",
                "came", "died", "slept", "sat", "wrote", "left", "took", "did", "had", "held",
                "told", "said", "knew", "drank", "spoke", "found", "thought", "caught", "taught",
                "felt", "kept", "lost", "won", "stood"
            } else None))
        return lemma, feature
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y", "present"
    if len(word) > 4 and word.endswith("ied"):
        return word[:-3] + "y", "past"
    if len(word) > 4 and word.endswith("ing"):
        stem = word[:-3]
        if stem.endswith(stem[-1:] * 2) and len(stem) > 2:
            stem = stem[:-1]
        if stem + "e" in {"make", "take", "write", "come", "give", "leave", "have", "drive", "ride", "use", "live", "die", "move", "breathe"}:
            stem += "e"
        return stem, "progressive"
    if len(word) > 3 and word.endswith("ed"):
        stem = word[:-2]
        if len(stem) > 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        return stem, "past"
    if len(word) > 3 and word.endswith("es"):
        return word[:-2], "present"
    if len(word) > 3 and word.endswith("s"):
        return word[:-1], "present"
    return word, None


def _head_rank(record: dict[str, Any], lemma: str) -> int:
    """0 when the English lemma is the record's head sense, else 1.

    The reverse index also contains entries where the word appears only as a
    later sense (e.g. "come" inside "fall; ...; come down"). Prefer the entry
    whose first sense is the word itself, so "come" selects "bó" (loc. come)
    rather than "kóro" (fall; ...; come down).
    """
    sense = primary_english_meaning(record.get("full_english") or record.get("english") or "")
    return 0 if sense.casefold() == lemma.casefold() else 1


def _choose_record(records: list[dict], direction: str, surface: str, expected: str | None = None) -> dict:
    if expected == "verb":
        verbs = [record for record in records if _is_verb(record)]
        if verbs:
            if direction == "english_to_izon":
                lemma = _english_lemma(surface)[0]
                return min(verbs, key=lambda record: _head_rank(record, lemma))
            return verbs[0]
    if expected == "noun":
        for record in records:
            if _is_noun(record):
                return record
    if direction == "english_to_izon":
        lemma, _ = _english_lemma(surface)
        # When a token is clearly an English verb, prefer a verb entry to a
        # homonymous noun/adjective in the large reverse dictionary index.
        if normalise_word(surface) in _EN_BASE_VERBS or lemma != normalise_word(surface):
            verbs = [record for record in records if _is_verb(record)]
            if verbs:
                return min(verbs, key=lambda record: _head_rank(record, lemma))
    else:
        plain = strip_diacritics(surface).casefold()
        if plain in {"ari", "eri", "omini", "woni", "ominì"}:
            for record in records:
                if _pos(record).startswith("pron."):
                    return record
        for record in records:
            if _is_verb(record):
                # Prefer verb homonyms only when the source form has a likely
                # verb ending; elsewhere keep dictionary order as the tie-break.
                if plain.endswith(("mi", "me", "yemi", "gha")):
                    return record
    return records[0]


def _inflected_match(surface: str, direction: str, lexicon: dict) -> tuple[dict, dict] | None:
    if direction == "english_to_izon":
        lemma, feature = _english_lemma(surface)
        if lemma != normalise_word(surface):
            records = _lookup_base(lemma, direction, lexicon)
            if records:
                record = _choose_record(records, direction, surface, "verb")
                if _is_verb(record):
                    return record, {"tense": feature, "surface": surface, "lemma": lemma}
        return None

    plain = strip_diacritics(surface)
    for suffix, feature in _IZON_SUFFIXES:
        suffix_plain = strip_diacritics(suffix)
        if len(plain) <= len(suffix_plain) + 1 or not plain.endswith(suffix_plain):
            continue
        # Use original-character slicing so tone marks in the stem are retained.
        stem = surface[:-len(suffix)]
        records = _lookup_base(stem, direction, lexicon)
        verbs = [r for r in (records or []) if _is_verb(r)]
        if verbs:
            return verbs[0], {"tense": feature, "surface": surface, "lemma": stem}
    # The user-supplied rule sheet lists -agha; also retain the earlier -gha fallback.
    for negative_suffix in ("agha", "gha"):
        suffix_plain = strip_diacritics(negative_suffix)
        if len(plain) <= len(suffix_plain) + 1 or not plain.endswith(suffix_plain):
            continue
        stem = surface[:-len(negative_suffix)]
        records = _lookup_base(stem, direction, lexicon)
        verbs = [r for r in (records or []) if _is_verb(r)]
        if verbs:
            return verbs[0], {"negative": True, "surface": surface, "lemma": stem}
    return None


def _make_units(tokens: list[str], direction: str, lexicon: dict) -> list[dict]:
    units: list[dict] = []
    i = 0
    max_len = max((len(key) for key in lexicon.get("english_index" if direction == "english_to_izon" else "izon_index", {})), default=1)
    while i < len(tokens):
        token = tokens[i]
        if not any(ch.isalnum() or ch == "_" for ch in token):
            units.append({"source": token, "target": token, "pos": "punct", "kind": "punct", "features": {}})
            i += 1
            continue
        low = normalise_word(token)
        if direction == "izon_to_english":
            morph = analyze_izon_morphology(token, lexicon, _lookup_base)
            if morph:
                units.append({"source": token, "target": morph["target"], "pos": morph["pos"],
                              "kind": "morphological", "features": {"morphology": morph.get("feature", "")}})
                i += 1
                continue
        if direction == "english_to_izon":
            adjective = match_english_adjective(tokens, i)
            if adjective:
                target, end, gloss = adjective
                units.append({"source": " ".join(tokens[i:end]), "target": target, "pos": "adjective",
                              "kind": "morphological", "features": {"adjective": gloss}})
                i = end
                continue
        # Frequent pronouns are closed-class items: explicitly map them so the
        # inverse gloss index cannot confuse "I" with an accidental dictionary fragment.
        if direction == "english_to_izon" and low in _EN_PRONOUNS:
            units.append({"source": token, "target": _EN_PRONOUNS[low], "pos": "pronoun", "kind": "pronoun", "features": {}})
            i += 1
            continue
        if direction == "izon_to_english" and i == 0 and strip_diacritics(token).casefold() in _IZON_INITIAL_PRONOUNS:
            units.append({"source": token, "target": _IZON_INITIAL_PRONOUNS[strip_diacritics(token).casefold()], "pos": "pronoun", "kind": "pronoun", "features": {}})
            i += 1
            continue
        # English function words require special transfer behavior, not dictionary glosses.
        if direction == "english_to_izon" and low in _EN_ARTICLES:
            units.append({"source": token, "target": "bi" if low == "the" else "", "pos": "det", "kind": "en_article_def" if low == "the" else "en_article_indef", "features": {}})
            i += 1
            continue
        if direction == "english_to_izon" and low in _EN_NEG:
            units.append({"source": token, "target": "gha", "pos": "neg", "kind": "neg", "features": {"negative": True}})
            i += 1
            continue
        # Treat have/has as perfect auxiliaries only before a recognized participle;
        # in noun phrases such as “has a book” they remain ordinary lexical candidates.
        if direction == "english_to_izon" and low in {"have", "has"} and i + 1 < len(tokens):
            next_lemma, next_feature = _english_lemma(tokens[i + 1])
            if next_feature in {"past", "perfect"}:
                units.append({"source": token, "target": "", "pos": "aux", "kind": "aux",
                              "features": {"aux": low, "tense": "perfect"}})
                i += 1
                continue
        # English auxiliaries before a lexical verb are not translated as separate words.
        if direction == "english_to_izon" and low in _EN_AUX and low not in {"is", "are", "am", "was", "were", "have", "has"}:
            units.append({"source": token, "target": "", "pos": "aux", "kind": "aux", "features": {"aux": low, "tense": "past" if low == "did" else ("future" if low in {"will", "shall"} else None)}})
            i += 1
            continue
        if direction == "english_to_izon" and low in {"is", "are", "am", "was", "were"}:
            units.append({"source": token, "target": "", "pos": "aux", "kind": "aux", "features": {"aux": low, "tense": "past" if low in {"was", "were"} else None, "progressive_aux": True}})
            i += 1
            continue

        # Analyze regular/irregular English verb inflections before consulting
        # the reverse gloss index. A surface form such as "eating" may also
        # occur inside a dictionary example for a noun; verb morphology should
        # win when its lemma is a listed Izon verb.
        if direction == "english_to_izon":
            inflected = _inflected_match(token, direction, lexicon)
            if inflected:
                record, features = inflected
                target = record.get("canonical_izon", record.get("izon", ""))
                units.append({"source": token, "target": target, "pos": "verb", "kind": "lexical",
                              "features": features, "record": record})
                i += 1
                continue

        matched = None
        end = i
        for j in range(min(len(tokens), i + max_len), i, -1):
            cand = tokens[i:j]
            if any(not any(ch.isalnum() or ch == "_" for ch in part) for part in cand):
                continue
            records = _index_match(cand, direction, lexicon)
            if records:
                matched = (_choose_record(records, direction, " ".join(cand)), j, {})
                break
        if matched:
            record, end, features = matched
            # Contextual homonym selection: the supplied dictionary contains
            # several homographs written ``ụ́`` (including a fish, moon, two,
            # and daughter/girl). In the attested noun phrase ``ụ́ bi``, the
            # post-nominal marker is used with the human noun in this project.
            # Prefer the dictionary sense whose full gloss explicitly includes
            # ``girl`` only in that context; never apply this choice to bare ``ụ́``.
            if direction == "izon_to_english" and i + 1 < len(tokens):
                next_marker = strip_diacritics(tokens[i + 1]).casefold()
                if next_marker == "bi":
                    candidates = _index_match([token], direction, lexicon) or []
                    human_girl = [candidate for candidate in candidates
                                  if strip_diacritics(candidate.get("canonical_izon", candidate.get("izon", ""))).casefold() == "u"
                                  and "girl" in (candidate.get("full_english") or "").casefold()]
                    if human_girl:
                        record = human_girl[0]
            source = " ".join(tokens[i:end])
        else:
            inflected = _inflected_match(token, direction, lexicon)
            if inflected:
                record, features = inflected
                end, source = i + 1, token
            else:
                # Treat the three common post-nominal class/article markers as such
                # only when a noun immediately precedes them and direct lookup failed.
                previous = units[-1] if units else {}
                plain_token = strip_diacritics(token)
                if direction == "izon_to_english" and plain_token in {"bi", "ma", "mi"} and previous.get("pos") == "noun":
                    units.append({"source": token, "target": "the", "pos": "det", "kind": "izon_article", "features": {}})
                    i += 1
                    continue
                units.append({"source": token, "target": f"[UNKNOWN: {token}]", "pos": "unknown", "kind": "unknown", "features": {}})
                i += 1
                continue
        target = record.get("canonical_izon", record.get("izon", "")) if direction == "english_to_izon" else record.get("english", "")
        if (direction == "izon_to_english" and i + 1 < len(tokens)
                and strip_diacritics(tokens[i + 1]).casefold() == "bi"
                and strip_diacritics(record.get("canonical_izon", record.get("izon", ""))).casefold() == "u"
                and "girl" in (record.get("full_english") or "").casefold()):
            # In the attested ``ụ́ bi`` phrase, choose the dictionary's girl
            # sense and use its contextual English label, not its first gloss
            # (daughter) or another homonymous headword (fish/moon/two).
            target = "girl"
        pos = "verb" if _is_verb(record) else ("noun" if _is_noun(record) else _pos(record))
        units.append({"source": source, "target": target, "pos": pos, "kind": "lexical", "features": features, "record": record})
        i = end
    return units


def _english_past(verb: str) -> str:
    low = normalise_word(verb)
    if low in _EN_PAST:
        return _EN_PAST[low]
    if low.endswith("e"):
        return low + "d"
    if len(low) > 2 and low[-1] not in "aeiou" and low[-2] in "aeiou" and low[-3] not in "aeiou":
        return low + low[-1] + "ed"
    return low + "ed"


def _english_ing(verb: str) -> str:
    low = normalise_word(verb)
    if low in _EN_ING:
        return _EN_ING[low]
    if low.endswith("e") and not low.endswith("ee"):
        return low[:-1] + "ing"
    if len(low) > 2 and low[-1] not in "aeiou" and low[-2] in "aeiou" and low[-3] not in "aeiou":
        return low + low[-1] + "ing"
    return low + "ing"


def _verb_target_izon(unit: dict, units: list[dict], direction: str) -> str:
    target = str(unit.get("target", ""))
    features = unit.get("features", {})
    if direction != "english_to_izon":
        return target

    tense = features.get("tense")
    negative = bool(features.get("negative")) or any(u.get("kind") == "neg" for u in units)
    aux_features = [u.get("features", {}) for u in units if u.get("kind") == "aux"]
    if any(f.get("tense") == "future" for f in aux_features):
        tense = "future"
    elif any(f.get("tense") == "perfect" for f in aux_features):
        tense = "perfect"
    elif any(f.get("progressive_aux") and f.get("tense") == "past" for f in aux_features):
        tense = "past_progressive"
    elif any(f.get("progressive_aux") for f in aux_features):
        tense = "progressive"
    elif any(f.get("tense") == "past" for f in aux_features):
        tense = "past"

    if negative:
        return conjugate_izon_verb(target, "negative") or target.rstrip("- ") + "agha"
    if tense:
        # Prefer the exact paradigms supplied for Bii, Gẹẹ, and Mu.
        source_form = conjugate_izon_verb(target, tense)
        if source_form:
            return source_form
    # Conservative productive defaults retained from the previous engine. The
    # user-supplied paradigms above override these when the stem is explicitly known.
    if tense == "past":
        return target.rstrip("- ") + "mi"
    if tense == "progressive":
        return target.rstrip("- ") + "yemi"
    if tense == "future":
        return target.rstrip("- ") + "nghimi"
    if tense == "perfect":
        return target.rstrip("- ") + "dọụ"
    if tense == "past_progressive":
        return target.rstrip("- ") + "timimi"
    return target


def _is_third_person_singular(subject_units: list[dict]) -> bool:
    subject = " ".join(str(u.get("target", "")) for u in subject_units if u.get("target")).strip().casefold()
    if not subject:
        return False
    if subject in {"i", "we", "you", "they", "me", "us", "them", "wó", "wónì", "ọmịnị́", "ẹ", "wo", "oni"}:
        return False
    if subject in {"he", "she", "it", "erí", "arị́", "u"}:
        return True
    # For a single lexical noun/name, English defaults to third-person singular;
    # plural-looking English subjects ending in -s are treated as plural.
    last = subject.split()[-1]
    return not last.endswith("s")


def _english_present_singular(verb: str) -> str:
    low = normalise_word(verb)
    if low == "be":
        return "is"
    if low == "have":
        return "has"
    if low == "do":
        return "does"
    if len(low) > 1 and low.endswith("y") and low[-2] not in "aeiou":
        return low[:-1] + "ies"
    if low.endswith(("s", "x", "z", "ch", "sh", "o")):
        return low + "es"
    return low + "s"


def _english_participle(verb: str) -> str:
    low = normalise_word(verb)
    irregular = {"be": "been", "go": "gone", "eat": "eaten", "write": "written",
                 "ask": "asked", "come": "come", "do": "done", "see": "seen",
                 "give": "given", "take": "taken", "make": "made", "run": "run"}
    return irregular.get(low, _english_past(verb))


def _verb_target_english(unit: dict, subject_units: list[dict]) -> str:
    target = str(unit.get("target", ""))
    features = unit.get("features", {})
    target_words = target.split()
    if not target_words:
        return target
    verb = target_words[0]
    subject = " ".join(u.get("target", "") for u in subject_units if u.get("target")).casefold()
    third_singular = _is_third_person_singular(subject_units)
    plural_or_first = subject in {"i", "we", "you", "they", "woni", "wó", "òmịnị", "ọ̀mịnị"}

    if features.get("negative"):
        aux = "does not" if third_singular else "do not"
        return " ".join([aux, *target_words])
    tense = features.get("tense")
    if tense == "past_progressive":
        be = "were" if plural_or_first else "was"
        return " ".join([be, _english_ing(verb), *target_words[1:]])
    if tense == "future":
        return " ".join(["will", verb, *target_words[1:]])
    if tense == "perfect":
        aux = "has" if third_singular else "have"
        return " ".join([aux, _english_participle(verb), *target_words[1:]])
    if tense == "past":
        target_words[0] = _english_past(verb)
    elif tense == "progressive":
        be = "am" if subject in {"i", "àri", "ari"} else ("are" if plural_or_first or subject.endswith("s") else "is")
        target_words = [be, _english_ing(verb), *target_words[1:]]
    elif tense == "present":
        if third_singular:
            target_words[0] = _english_present_singular(verb)
    elif third_singular:
        target_words[0] = _english_present_singular(verb)
    return " ".join(target_words)


def _move_english_articles(units: list[dict]) -> list[dict]:
    """Move Izon definite markers after their nominal head for English -> Izon."""
    result = list(units)
    i = 0
    while i < len(result):
        if result[i].get("kind") in {"en_article_def", "izon_article"}:
            marker = result.pop(i)
            if marker.get("kind") == "en_article_def":
                # Find next noun and place marker after it (Izon head + article).
                dest = next((j for j in range(i, len(result)) if result[j].get("pos") == "noun"), None)
                if dest is not None:
                    result.insert(dest + 1, marker)
                    i = dest + 2
                    continue
            else:
                # For Izon -> English, the marker is handled by a separate function.
                result.insert(i, marker)
                i += 1
        i += 1
    return result


def _move_izon_articles(units: list[dict]) -> list[dict]:
    """Move a post-nominal Izon definite marker before the noun in English."""
    result = list(units)
    i = 0
    while i < len(result):
        if result[i].get("kind") == "izon_article":
            marker = result.pop(i)
            dest = next((j for j in range(i - 1, -1, -1) if result[j].get("pos") == "noun"), None)
            if dest is not None:
                result.insert(dest, marker)
                i = dest + 2
                continue
            else:
                result.insert(i, marker)
        i += 1
    return result


def _final_punctuation(units: list[dict]) -> tuple[list[dict], list[str]]:
    body = list(units)
    punct = []
    while body and body[-1].get("kind") == "punct":
        punct.insert(0, body.pop()["target"])
    # Generic reordering is disabled for embedded punctuation / multiple clauses.
    if any(u.get("kind") == "punct" for u in body):
        return units, []
    return body, punct


def translate_sentence_by_rules(sentence: str, direction: str, lexicon: dict) -> str | None:
    """Reorder a simple one-clause sentence; return None if unsafe to transform."""
    tokens = tokenize(sentence)
    if direction == "izon_to_english":
        tokens = merge_izon_morphology_tokens(tokens)
    if not tokens:
        return None
    # Question inversion/particles and imperative morphology have not been
    # implemented as general transfer rules. Preserve the input order through
    # fallback rather than rewriting these moods as declarative clauses.
    if "?" in tokens:
        return None
    units = _make_units(tokens, direction, lexicon)
    body, punct = _final_punctuation(units)
    if not body or body is units:
        return None

    # Standalone noun phrases are valid translation units too. Previously the
    # sentence engine required a lexical verb, so ``the girl`` was rejected and
    # the safety guard displayed an unsupported-pattern message. Apply only a
    # narrow, fully recognized NP rule: one noun, optionally preceded by an
    # English article / supported Izon post-nominal marker. This is deliberately
    # not a general phrase guesser.
    if not any(u.get("pos") == "verb" and u.get("kind") == "lexical" for u in body):
        unknowns = [u for u in body if u.get("kind") == "unknown"]
        nouns = [u for u in body if u.get("pos") == "noun" and u.get("kind") == "lexical"]
        allowed_kinds = {"lexical", "en_article_def", "en_article_indef", "izon_article", "punct"}
        if not unknowns and len(nouns) == 1 and all(u.get("kind") in allowed_kinds for u in body):
            if direction == "english_to_izon":
                ordered = _move_english_articles(body)
                rendered = [u.get("target", "") for u in ordered
                            if u.get("target") and u.get("kind") != "en_article_indef"]
            else:
                ordered = _move_izon_articles(body)
                rendered = []
                for unit in ordered:
                    value = unit.get("target", "")
                    if unit.get("kind") == "lexical" and unit.get("pos") == "noun":
                        # Resolve the source-attested ``ụ́ bi`` phrase as
                        # ``the girl`` rather than selecting an unrelated
                        # homonymous dictionary sense for the bare word.
                        if "girl" in (unit.get("record", {}).get("full_english") or "").casefold():
                            value = "girl"
                    if value:
                        rendered.append(value)
            result = detokenize(rendered + punct)
            if result:
                return result[0].upper() + result[1:]

    # English verbless-predicate/copular clauses: the English copula is not
    # normally transferred as a standalone lexical word in the current Izon
    # grammar resource.  For a narrow, fully recognized pattern such as
    # "The boy is a child", preserve subject + complement and omit the copula.
    # This is intentionally conservative: unknown names/words decline this path.
    if direction == "english_to_izon":
        copula_positions = [i for i, u in enumerate(body)
                            if u.get("kind") == "aux" and u.get("features", {}).get("progressive_aux")]
        lexical_verbs = [u for u in body if u.get("pos") == "verb" and u.get("kind") == "lexical"]
        if len(copula_positions) == 1 and lexical_verbs:
            copula_i = copula_positions[0]
            # A progressive verb such as "is eating" carries an explicit
            # progressive feature from English morphology. A plain dictionary
            # verb gloss after "is" (e.g. the entry for "beautiful" resolves
            # to the verb "make beautiful") is not evidence for a progressive
            # clause. Decline instead of emitting an invented -yemi form.
            if any(u.get("features", {}).get("tense") != "progressive"
                   for u in lexical_verbs if body.index(u) > copula_i):
                return None
        if len(copula_positions) == 1 and not lexical_verbs:
            copula_i = copula_positions[0]
            before, after = body[:copula_i], body[copula_i + 1:]
            if before and after and all(u.get("kind") != "unknown" for u in before + after):
                # Drop only the grammatical copula and the English indefinite article.
                ordered = [u for u in before + after
                           if u is not body[copula_i] and u.get("kind") != "en_article_indef"]
                ordered = _move_english_articles(ordered)
                rendered = [u.get("target", "") for u in ordered if u.get("target")]
                result = detokenize(rendered + punct)
                if result:
                    return result[0].upper() + result[1:]

    # Require exactly one recognized lexical verb so coordination/subordination is not
    # accidentally flattened by a single-clause heuristic.
    verb_positions = [i for i, u in enumerate(body) if u.get("pos") == "verb" and u.get("kind") == "lexical"]
    if len(verb_positions) != 1:
        return None
    verb_i = verb_positions[0]
    verb_unit = body[verb_i]
    # Subjectless English clauses are commonly commands; their imperative
    # counterpart is not the same as a declarative SVO -> SOV rewrite.
    if direction == "english_to_izon" and verb_i == 0:
        return None
    if direction == "izon_to_english":
        # Core documented order: Izon is typically SOV/SAV; English is SVO/SVA.
        if any(u.get("kind") == "neg" for u in body):
            verb_unit.setdefault("features", {})["negative"] = True
        # Require a final main verb (ignoring post-verbal negative particles and punctuation).
        if any(u.get("kind") not in {"punct", "neg"} for u in body[verb_i + 1:]):
            return None
        before = body[:verb_i]
        # First lexical unit is the subject; an immediately following determiner belongs to it.
        subject_end = 1
        if len(before) > 1 and before[1].get("kind") == "izon_article":
            subject_end = 2
        subject = before[:subject_end]
        rest = before[subject_end:]
        ordered = subject + [verb_unit] + rest
        ordered = _move_izon_articles(ordered)
        rendered = []
        for unit in ordered:
            if unit.get("kind") == "aux" or unit.get("kind") == "en_article_indef":
                continue
            value = unit.get("target", "")
            if unit is verb_unit:
                value = _verb_target_english(unit, subject)
            if value:
                rendered.append(value)
        result = detokenize(rendered + punct)
    else:
        # Core documented order: English is usually SVO; Izon clauses are often SOV.
        # Ignore auxiliary do-support and article-less indefinites in transfer.
        if any(u.get("kind") == "neg" for u in body):
            verb_unit.setdefault("features", {})["negative"] = True
        before = body[:verb_i]
        after = body[verb_i + 1:]
        # Keep the English subject and its modifiers before the object/adjuncts.
        # Auxiliary tokens in the pre-verbal string are grammatical operators, not content.
        before = [u for u in before if u.get("kind") != "aux"]
        after = [u for u in after if u.get("kind") != "aux"]
        ordered = before + after + [verb_unit]
        # The negative marker is realized on the Izon verb in this narrow
        # statement heuristic. Do not also print it as a separate word.
        remove_kinds = {"en_article_indef"}
        if verb_unit.get("features", {}).get("negative"):
            remove_kinds.add("neg")
        ordered = [u for u in ordered if u.get("kind") not in remove_kinds]
        ordered = _move_english_articles(ordered)
        rendered = []
        for unit in ordered:
            value = unit.get("target", "")
            if unit is verb_unit:
                value = _verb_target_izon(unit, body, direction)
            if value:
                rendered.append(value)
        result = detokenize(rendered + punct)
    if not result:
        return None
    return result[0].upper() + result[1:]
