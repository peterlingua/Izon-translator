"""Shared longest-match, dictionary-based sentence translation engine."""
from functools import lru_cache
import re
from tokenizer import tokenize, detokenize, normalise_word
from lexicon import load_lexicon, normalise_key, strip_diacritics, lookup_izon_word
from grammar import exact_rule_translation
from sentence_engine import translate_sentence_by_rules, _lookup_base
from morphology import analyze_izon_morphology, match_english_adjective, merge_izon_morphology_tokens
from clause_engine import translate_compound
from verb_rules import diagnose as diagnose_verb_construction

UNKNOWN_PREFIX = "[UNKNOWN: "

# Closed-class pronouns must not be selected by the dictionary's first homonym.
# These are context-biased defaults: Izon pronouns can have positional/tonal
# variants, so the table is deliberately small and should be reviewed by speakers.
_EN_PRONOUN_OVERRIDES = {
    "i": "Àri", "me": "Ì", "my": "Ìnè", "mine": "Ìnei",
    "you": "Ári", "your": "Ínè", "yours": "Ìnei",
    "he": "Eri", "him": "Wò", "his": "Wòi",
    "she": "arau", "her": "árà", "hers": "árà",
    "it": "u", "we": "Woni", "us": "wó", "our": "Wó", "ours": "Woi",
    "they": "Ọ̀mịnị", "them": "Ò", "their": "oro", "theirs": "ọ̀rèi",
    # Interrogative pronoun: use the documented Kolokuma form in fallback too.
    "who": "Tịbọ",
}
_IZON_INITIAL_PRONOUN_OVERRIDES = {
    "ari": "I", "eri": "he", "omini": "they", "ọmini": "they",
    "woni": "we",
}

@lru_cache(maxsize=1)
def _lexicon():
    return load_lexicon(verbose=False)


def _preserve_case(source, target):
    if not target:
        return target
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


def _token_key(token):
    return normalise_key(token)


def _lookup_translate(sentence, direction):
    lex = _lexicon()
    index_name = "english_index" if direction == "english_to_izon" else "izon_index"
    plain_index_name = "english_plain_index" if direction == "english_to_izon" else "izon_plain_index"
    index = lex[index_name]
    plain_index = lex.get(plain_index_name, {})
    tokens = tokenize(sentence)
    if direction == "izon_to_english":
        tokens = merge_izon_morphology_tokens(tokens)
    if not tokens:
        return "Please enter a sentence."

    # Longest phrase match avoids translating parts of a known multiword term.
    max_len = max((len(k) for k in index.keys()), default=1)
    out, unknown = [], []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if direction == "english_to_izon":
            adjective = match_english_adjective(tokens, i)
            if adjective:
                target, end, _gloss = adjective
                source_chunk = " ".join(tokens[i:end])
                out.append(_preserve_case(source_chunk, target))
                i = end
                continue
        elif any(ch.isalnum() or ch == "_" for ch in token):
            morph = analyze_izon_morphology(token, lex, _lookup_base)
            if morph:
                out.append(_preserve_case(token, morph["target"]))
                i += 1
                continue
        if not any(ch.isalnum() or ch == "_" for ch in token):
            out.append(token); i += 1; continue
        # Prefer common pronouns over homonymous dictionary entries when they
        # occur at sentence start. This also improves safe word-wise fallback
        # if the sentence parser cannot identify a main verb.
        if i == 0 and direction == "english_to_izon":
            pronoun = _EN_PRONOUN_OVERRIDES.get(normalise_word(token))
            if pronoun:
                out.append(pronoun[:1].upper() + pronoun[1:])
                i += 1
                continue
        if i == 0 and direction == "izon_to_english":
            pronoun = _IZON_INITIAL_PRONOUN_OVERRIDES.get(strip_diacritics(token).casefold())
            if pronoun:
                out.append(pronoun)
                i += 1
                continue
        best_records, best_end = None, i
        limit = min(len(tokens), i + max_len)
        for end in range(limit, i, -1):
            candidate = tuple(_token_key(t) for t in tokens[i:end])
            if candidate in index:
                best_records, best_end = index[candidate], end
                break
            plain_candidate = tuple(strip_diacritics(t) for t in candidate)
            if plain_candidate in plain_index:
                best_records, best_end = plain_index[plain_candidate], end
                break
        if best_records:
            record = best_records[0]
            target = record.get("canonical_izon", record["izon"]) if direction == "english_to_izon" else record["english"]
            source_chunk = " ".join(tokens[i:best_end])
            out.append(_preserve_case(source_chunk, target))
            i = best_end
        else:
            unknown.append(token)
            # Keep unknown source words visible and explicitly marked.
            out.append(f"[UNKNOWN: {token}]")
            i += 1
    translated = detokenize(out)
    # Capitalize the first letter after sentence start, without altering tone marks.
    if translated:
        translated = translated[0].upper() + translated[1:]
    return translated


# Source-backed phrase-level transfer for interrogatives and demonstratives.
# These are the exact example pairs supplied in the user's Ịzọn grammar reference;
# they are kept as phrase rules because the source says interrogative meanings are
# compositional/context-dependent. Do not infer a universal one-word gloss for what/who.
_SOURCE_PHRASE_RULES = {
    "english_to_izon": {
        "which house": "Tị warị nị", "who is that": "Tịbọ kị Anị?",
        "who did it": "Tịbọ kị o mịẹ nị",
        "for whom": "Tịbọ kọ ye nị", "whose shirt is this": "Mị tịbọ kọ aru nị",
        "this is the house": "Mị warịmị", "that is alasa's mother": "Anị Alasa yin",
        "these belong to us": "Bo woyaj", "those belong to us": "Bo woyaj",
        "these are pere's things": "Mị Pẹrẹ eyeama", "those are our animals": "Anị wo namaama",
    },
    "izon_to_english": {
        "tị warị nị": "Which house?", "tịbọ kị anị": "Who is that?",
        "tịbọ kị o mịẹ nị": "Who did it?",
        "tịbọ kọ ye nị": "For whom?", "mị tịbọ kọ aru nị": "Whose shirt is this?",
        "mị warịmị": "This is the house.", "anị alasa yin": "That is Alasa's mother.",
        "bo woyaj": "These belong to us.", "mị pẹrẹ eyeama": "These are Pere's things.",
        "anị wo namaama": "Those are our animals/meat.",
    },
}

def _normalise_phrase(sentence):
    return " ".join(re.findall(r"[\wÀ-ž]+(?:['’][\wÀ-ž]+)?", str(sentence or "").casefold(), flags=re.UNICODE)).strip()

def _generated_interrogative(sentence, direction):
    """Apply productive question patterns grounded in the supplied examples.

    These rules generalize the documented structure to new lexical items where
    the lexicon can supply a translation. They intentionally do not guess a
    standalone Izon equivalent for English ``what`` or ``where``.
    """
    if direction != "english_to_izon":
        return None
    clean = str(sentence or "").strip()
    # Users often omit the final question mark when typing into the menu.
    # Recognize the question by its opening words as well as by punctuation.
    key = _normalise_phrase(clean)

    # Source-backed pattern: ``Which house?`` -> ``Tị warị nị?``.
    # Generalize only when the head noun is known to the lexicon.
    match = re.fullmatch(r"which\s+([\wÀ-ž]+(?:\s+[\wÀ-ž]+)*)", key, flags=re.UNICODE)
    if match:
        noun_phrase = match.group(1).strip()
        translated = _lookup_translate(noun_phrase, "english_to_izon")
        if translated and "[UNKNOWN:" not in translated:
            # Preserve the example's structure: interrogative + noun + nị.
            return f"Tị {translated[0].lower() + translated[1:]} nị?"

    # Identifying questions with English copula forms ``am`` and ``are``.
    # The copula is handled by the sentence rule, not translated as a standalone
    # dictionary word. These subject forms follow the project's current pronoun
    # mappings; confirm the complete constructions with a Kolokuma speaker.
    copula_match = re.fullmatch(r"who\s+(am|are)\s+(i|you)", key, flags=re.UNICODE)
    if copula_match:
        subject = copula_match.group(2)
        subject_forms = {"i": "arị́", "you": "iné"}
        result = f"Tịbọ kị {subject_forms[subject]}"
        return result + ("?" if clean.endswith("?") else "")

    # Source-backed frame: ``Who is that?`` -> ``Tịbọ kị Anị?``.
    # Apply the same question frame to known noun phrases. This is a provisional
    # productive rule: lexical choices and the final Izon form need speaker review.
    match = re.fullmatch(r"who\s+is\s+(.+)", key, flags=re.UNICODE)
    if match:
        noun_phrase = match.group(1).strip()
        noun_phrase = re.sub(r"^(?:the|a|an)\s+", "", noun_phrase)
        # The current dictionary's single-word gloss for these two common
        # person nouns omits the attested ``bi`` element found in the user's
        # observed phrase outputs (``yaị́ bi`` / ``ụ́ bi``). Preserve those
        # full noun phrases when generating the productive identifying frame.
        known_person_nouns = {
            "boy": "yaị́ bi",
            "girl": "ụ́ bi",
        }
        translated = known_person_nouns.get(noun_phrase)
        if translated is None:
            translated = _lookup_translate(noun_phrase, "english_to_izon")
        if translated and "[UNKNOWN:" not in translated:
            # The attested frame puts ``Tịbọ kị`` before the identifying phrase.
            # Do not translate English copula ``is`` as a standalone word.
            result = f"Tịbọ kị {translated[0].lower() + translated[1:]}"
            return result + ("?" if clean.endswith("?") else "")

    # Source-backed pattern: ``Who did it?`` -> ``Tịbọ kị o mịẹ nị?``.
    # Reuse the documented frame for other known object nouns/pronouns.
    match = re.fullmatch(r"who\s+did\s+([\wÀ-ž]+(?:\s+[\wÀ-ž]+)*)", key, flags=re.UNICODE)
    if match:
        obj = match.group(1).strip()
        if obj.startswith("the "):
            obj = obj[4:]
        if obj == "it":
            return "Tịbọ kị o mịẹ nị?"
        translated = _lookup_translate(obj, "english_to_izon")
        if translated and "[UNKNOWN:" not in translated:
            return f"Tịbọ kị {translated[0].lower() + translated[1:]} mịẹ nị?"
    return None


def translate(sentence, direction):
    if not str(sentence or "").strip():
        return "Please enter a sentence."
    # A bare Izon homograph can have several dictionary meanings. Do not
    # silently return whichever entry happens to appear first in the CSV.
    # Contextual phrases (for example ``ụ́ bi``) are handled by the sentence
    # engine, where the post-nominal marker provides additional information.
    if direction == "izon_to_english":
        lexical_tokens = [t for t in tokenize(sentence) if any(ch.isalnum() for ch in t)]
        if len(lexical_tokens) == 1:
            senses = lookup_izon_word(lexical_tokens[0], _lexicon())
            meanings = list(dict.fromkeys(
                (row.get("english") or "").strip() for row in senses if (row.get("english") or "").strip()
            ))
            if len(meanings) > 1:
                return f"[AMBIGUOUS IZON WORD: {lexical_tokens[0]} = {'; '.join(meanings)}]"
    phrase_key = _normalise_phrase(sentence)
    phrase_target = _SOURCE_PHRASE_RULES.get(direction, {}).get(phrase_key)
    if phrase_target is not None:
        if str(sentence).strip().endswith("?") and not phrase_target.endswith("?"):
            phrase_target += "?"
        return phrase_target
    generated_question = _generated_interrogative(sentence, direction)
    if generated_question is not None:
        return generated_question
    exact = exact_rule_translation(sentence, direction)
    if exact is not None:
        return exact
    # Do not let dictionary homonyms create a plausible-looking but unsupported
    # answer for an interrogative structure for which the supplied reference has
    # no transfer rule yet (for example, "What is my name?"). The marker makes
    # the missing grammar explicit instead of silently emitting a corrupt gloss.
    if direction == "english_to_izon" and str(sentence).strip().endswith("?"):
        key = _normalise_phrase(sentence)
        if re.fullmatch(r"what\s+is\s+.+", key):
            return f"[UNSUPPORTED QUESTION PATTERN: {str(sentence).strip()}]"
    # Compound and complex sentences: split at a recognized connective, translate
    # each clause with the single-clause engine, and recombine. Declines (None)
    # for simple sentences and for any clause the engine cannot translate.
    composed = translate_compound(sentence, direction, _lexicon())
    if composed is not None:
        return composed
    # Sentence transfer is attempted before falling back to phrase-by-phrase
    # substitution. It deliberately declines sentences it cannot parse safely.
    ruled = translate_sentence_by_rules(sentence, direction, _lexicon())
    if ruled is not None:
        if "[UNKNOWN" in ruled:
            reason = diagnose_verb_construction(sentence, direction)
            if reason:
                return f"[UNSUPPORTED SENTENCE PATTERN: {str(sentence).strip()}] {reason}"
        return ruled

    # Do not present word-by-word dictionary substitutions as a sentence
    # translation. A single ambiguous dictionary homonym can otherwise turn
    # a whole sentence into a misleading one-word output (for example, just
    # ``Ụ́``). Keep single-word dictionary lookup available, but require a
    # sentence-level rule or verified pair for multiword input.
    # Count whitespace-delimited lexical words so hyphenated Izon morphology
    # (e.g. noun + plural suffix) remains eligible for the morphology engine.
    source_tokens = re.findall(r"[^\W_]+(?:[-’'][^\W_]+)*", str(sentence), flags=re.UNICODE)
    if len(source_tokens) > 1:
        # Preserve complete multiword lexical entries and source-backed adjective
        # constructions (e.g. "very small"); reject only compositional sentence
        # fallback that would misleadingly concatenate unrelated homonyms.
        lex = _lexicon()
        idx_name = "english_index" if direction == "english_to_izon" else "izon_index"
        plain_name = "english_plain_index" if direction == "english_to_izon" else "izon_plain_index"
        phrase_tokens = tokenize(sentence)
        strict_key = tuple(normalise_key(t) for t in phrase_tokens)
        plain_key = tuple(strip_diacritics(t) for t in phrase_tokens)
        full_phrase_known = bool(lex.get(idx_name, {}).get(strict_key) or lex.get(plain_name, {}).get(plain_key))
        adjective_phrase = bool(direction == "english_to_izon" and phrase_tokens and
                                (match_english_adjective(phrase_tokens, 0) or ()))
        if not full_phrase_known and not adjective_phrase:
            reason = diagnose_verb_construction(sentence, direction)
            detail = reason or "Add/validate a sentence rule and its Izon/English lexical forms."
            return f"[UNSUPPORTED SENTENCE PATTERN: {str(sentence).strip()}] {detail}"
    result = _lookup_translate(sentence, direction)
    # A word-level fallback can leave an [UNKNOWN: ...] marker inside an
    # otherwise plausible string (e.g. "can"). When the unknown word belongs
    # to an unsupported verbal construction, say so rather than return it.
    if "[UNKNOWN" in result:
        reason = diagnose_verb_construction(sentence, direction)
        if reason:
            return f"[UNSUPPORTED SENTENCE PATTERN: {str(sentence).strip()}] {reason}"
    return result


def clear_dictionary_cache():
    _lexicon.cache_clear()
