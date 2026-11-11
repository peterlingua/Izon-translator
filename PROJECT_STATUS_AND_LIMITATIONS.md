# Project status: consolidated rule-based Kolokuma Izon ↔ English translator

## What is implemented

- A local browser interface (`web_app.py`) and Windows launcher (`Launch_Translator.bat`).
- A terminal interface (`main.py`, `run_translator.bat`).
- A lexicon with phrase matching and tone-insensitive fallback. The supplied A–Z dictionary has 5,878 data rows; 5,870 entries are usable after empty/reference-only records are excluded.
- English noun-phrase transfer for a recognized definite noun such as `the girl` → `Ụ́ bi`, and an indefinite phrase such as `a girl` → `Ụ́`.
- Contextual Izon homograph handling for `ụ́ bi` → `The girl`; bare `ụ́` is explicitly reported as ambiguous because the dictionary has multiple homonymous entries.
- Browser HTTP regression tests and JSON endpoints for translation, dictionary lookup, and server health.
- Exact verified/supplied sentence-pair lookup in both directions.
- A conservative sentence transfer engine for a limited range of simple clauses, word order, selected tense/aspect, negation, and morphology.
- Source-backed interrogative examples and two productive English-to-Izon templates:
  - `Which + known noun phrase?` → `Tị + translated noun phrase + nị?`
  - `Who did + known object?` → `Tịbọ kị + translated object + mịẹ nị?`
- Pronoun defaults, morphology helpers, a grammar-rule inventory, and automated regression tests.
- Unsupported `What is ...?` question structures are flagged rather than rendered as a misleading word-by-word output, unless an exact source-backed sentence pair exists.

## What this does not mean

This is not a complete or independently validated machine translation system. The program can generalize only where a rule and the needed lexical entries exist. It does not yet have a full syntactic parser for arbitrary clauses, embedded questions, all wh-words, all pronoun cases, every tense/aspect, or all compound and compound-complex sentences. The supplied general Ịzọn/Ijaw material may not always reflect Kolokuma usage. Generated forms must be reviewed by a fluent Kolokuma speaker.

## Why unseen sentences fail

An unseen sentence may fail if its word is absent/ambiguous in the dictionary, its grammar structure is not implemented, the source rule does not specify enough information, or the sentence needs agreement/tonal/morphological changes not encoded in the program. Adding more stored sentence pairs improves those examples only; adding a productive rule with clear constraints and tests is what supports new combinations.

## Current tests

Run `python -m unittest discover -s tests -v` from this folder. The current suite contains 62 automated tests covering dictionary loading, supplied sentence pairs, simple clause transfer, noun phrases, homograph handling, pronouns, generated questions, and real HTTP requests to the browser routes. Passing software tests confirms code behavior, not that every generated Izon sentence is correct.

## Next linguistic validation required

A fluent Kolokuma speaker should validate at least one positive and one negative example for each productive rule, especially the interrogative marker/order, pronoun forms by subject/object/possessive position, and tense/aspect suffixes. The project intentionally does not invent a translation for `What is my name?` without a reliable target-language example and a rule for the construction.

## Sentence-structure expansion (2026-10-21)
The grammar inventory now includes proposed patterns for simple, compound, complex, and compound-complex English sentence structures. The 18 newly added inventory entries are marked unverified and have blank target outputs by design; they describe implementation targets rather than claiming that Izon conjunctions or clause structures are confirmed. Do not treat their presence in the CSV as proof that the web app executes them.

The Python sentence engine now handles one additional narrow simple-sentence case: an English copular clause with a recognized subject and complement (for example, `The boy is a child.`) can be transferred as subject + complement without translating English `is` as a lexical word. The rest of simple-clause transfer remains limited to recognized vocabulary and the implemented patterns. Compound, complex, and compound-complex generation still needs executable clause parsing, verified Izon conjunctions/subordination markers, and fluent-speaker review.

## Dictionary and browser integration update (2026-11-10)

The A–Z dictionary was audited and its existing `ụ́` noun entry was confirmed to include “daughter; girl”. The English reverse index recognizes `girl` and returns `ụ́`. A productive noun-phrase path was added so `the girl` returns `Ụ́ bi` and `a girl` returns `Ụ́`. In the reverse direction, the context `ụ́ bi` selects the girl sense and returns `The girl`; a complete supported clause such as `ụ́ bi burú ị́ị.` returns `The girl eats yam.`. A bare `ụ́` remains ambiguous because the source dictionary contains multiple homonymous entries; the translator now reports that ambiguity rather than choosing an arbitrary sense.

The browser application was audited and now exposes `/api/health`, `/api/lookup`, and `/api/translate` in addition to its HTML form. All routes use the same shared lexicon and translation engine. The regression suite now contains 62 passing tests, including browser HTTP tests. Copular adjective inputs whose dictionary match is only a verb gloss are declined rather than incorrectly receiving a progressive suffix. This is still a research prototype: generated forms and the use of `bi` in new noun phrases require Kolokuma speaker validation.

## Compound and complex sentences (10 November 2026)

`clause_engine.py` composes compound and complex sentences from the connectives attested in the owner-supplied corpus, in both directions. Each clause is translated by the single-clause engine (or by an exact verified corpus pair), and any clause that cannot be translated causes the whole sentence to decline.

Measured honestly on the 60 owner-supplied compound and complex sentences, with whole-sentence exact lookup bypassed:
- English → Izon: 1 of 60 composed; 0 matched the owner translation exactly. The composer declines the rest because clause vocabulary (for example "washing", "hungry", "big woman", "greeting") is missing or ambiguous in the lexicon.
- Izon → English: 0 of 60 composed, because the Izon clauses use vocabulary the Izon-side clause engine does not handle.

Constructed sentences whose clauses are in the engine's vocabulary do compose correctly (for example "He is coming, but the girl eats yam." ↔ "Érí bòyèmí, ọ̀kpọ̀ ụ́ bi burú ị́ị."). The owner-supplied corpus and the exact-pair evaluator still determine every verified output.

Known open problems:
- The lexicon is the bottleneck: "man", "that", "big", "greeting", "hungry", and similar words are missing or resolve to a homonym.
- Two progressive conventions appear in the owner corpus (`-yèmí` and `-ẹ̀mị`); the generator chooses one, so it can differ from the verified spelling of the same clause.
- Izon conjunctions and subordination are taken from the corpus only. Online sources did not give accessible Kolokuma conjunction rules (Williamson 1965 is the standard reference, but its text is not online).
- "Too" (`kpó`) and other adverbs are not yet placed by rule.

What a fluent Kolokuma speaker should validate next: the connective list (especially `ọ̀kpọ̀`/`kọ́`/`kọ̀`, and `ọ́bọ́`/`ọ̀bọ̀`), the placement of `bá … fịẹ́ị` and `Bárá … fịẹ́ị`, and the progressive suffix choice.
