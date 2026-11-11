# Upgrade notes

## Integration of project-owner Izon rules and examples

- Added all 90 sentence pairs from the owner's `ijaw machine translation.docx`: 30 simple, 30 compound, and 30 compound-complex sentences. Kept all 13 original research seed pairs; the active corpus now contains 103 pairs.
- Added `data/izon_morphology.csv` with 47 source-derived noun, adjective, verb, and pronoun entries, and added 23 source-derived grammar-rule rows to `data/grammar_rules.csv`.
- Added `morphology.py` for the supplied noun-marker examples, the four adjective paradigms, English adjective phrase mappings, and explicit Bii/Gẹẹ/Mu forms.
- Updated the default pronoun mappings to prefer the forms in the owner's subjective, objective, genitive, possessive, and reflexive tables.
- Added morphology-aware lookup to both translation directions, including selected noun plural forms and adjective degree/intensifier forms; added TAM recognition for the suffix examples.
- Improved `evaluator.py` so English sentences with more than one source-supplied Izon variant are evaluated against the allowed variant set.
- Retained the original Word reference documents under `references/` for traceability and documented source ambiguities.
- Added tests for every supplied sentence pair in both directions and for the implemented morphology. Test suite currently contains 26 tests.

## Important caveat

The translator remains a research prototype. Exact sentence pairs can translate compound and compound-complex inputs only when those examples (or exact variants) are present in the corpus. Generative transfer of arbitrary multi-clause sentences still needs a clause parser and extensive speaker-reviewed minimal pairs. Morphological alternations and the ambiguous Bii future form need review by a fluent Kolokuma speaker; they were preserved rather than silently corrected.

## 2026-10-21 — Interrogatives and pronouns
- Added phrase-level source-backed rules for which/who/for whom/whose and demonstrative examples in the uploaded grammar references.
- Added grammar CSV records describing interrogative, pronoun, demonstrative, and passive-voice structures.
- Added focused regression tests.
- Kept unsupported standalone wh-word translations conservative rather than inventing an Izon equivalent.

## Productive interrogative fix
- Added `who` to the English interrogative-pronoun fallback so it is not marked unknown.
- Added a compositional `Who is [known noun phrase]?` question frame that translates the noun phrase through the dictionary instead of requiring an exact stored sentence.
- Preserved the supplied `Who is that?` → `Tịbọ kị Anị?` example explicitly.
- Added regression tests for unseen noun combinations. Generated forms are provisional and need fluent Kolokuma review.

### Follow-up fix: `Who is the girl` without a question mark
- The generated `Who is ...` rule previously required a trailing `?`, so plain menu input such as `who is the girl` fell through to word-by-word translation and left `who`/`is`/`the` untranslated.
- The pattern now recognizes the interrogative by its opening words even when punctuation is omitted.
- The generated person-noun phrases `girl` and `boy` retain the `ụ́ bi` and `yaị́ bi` forms seen in the user's reported output.
- Regression tests cover both punctuated and unpunctuated inputs. These generated forms still need confirmation by a fluent Kolokuma Izon speaker.

## Interrogative copula patterns: who am I / who are you
- Added sentence-level handling for `who am I` and `who are you`, with or without a trailing question mark.
- The English copula `am`/`are` is handled as part of the question frame instead of being emitted as `[UNKNOWN: ...]`.
- The current outputs use the project's existing subject forms: `Tịbọ kị arị́` and `Tịbọ kị iné`. Please validate the complete constructions with a fluent Kolokuma speaker.

## 2026-10-21 — sentence structure rule inventory and simple copular clause
- Added 18 sentence-structure planning rows to `data/grammar_rules.csv` covering simple clauses, questions, coordination, subordination, clause boundaries, clause-by-clause transfer, and punctuation.
- These new inventory rows are explicitly marked unverified and do not invent Izon conjunction translations or target examples. Compound/complex/compound-complex rules still require implementation and Kolokuma-speaker validation before they can safely generate translations.
- Added a conservative executable English copular-clause path in `sentence_engine.py`. When the subject and complement are recognized and there is no lexical verb, it omits the English copula and preserves the translated subject/complement sequence, following the project’s documented verbless subject–complement pattern.
- Added regression coverage for `The boy is a child.`
- Validation: 46 automated tests passed. This is not a claim of general translation accuracy; unknown vocabulary and unsupported grammar remain visible limitations.


## 2026-11-10 — Full dictionary, noun phrase and browser audit
- Audited the full project archive, Python modules, CSV resources, grammar inventory, sentence corpus, launch scripts, reference documents and automated tests.
- Confirmed that the supplied dictionary already contains the noun `ụ́` with the English gloss “daughter; girl”; the English reverse lookup now has explicit regression coverage for `girl` → `ụ́`.
- Added a narrow noun-phrase transfer rule: `the girl` → `Ụ́ bi`; `a girl` → `Ụ́`. The reverse phrase `ụ́ bi` is contextually translated as `The girl`, including in supported simple clauses such as `ụ́ bi burú ị́ị.` → `The girl eats yam.`.
- The dictionary has several homonymous entries for bare `ụ́` (including fish, moon, daughter/girl and two). Bare Izon lookup now reports ambiguity instead of silently selecting the first entry.
- Prevented an unsupported copular adjective such as `The girl is beautiful` from being misgenerated as a progressive verb form. It is marked unsupported until a source-backed Kolokuma adjective construction is available.
- Added `/api/health`, `/api/lookup` and `/api/translate` routes; tested both the browser HTML form and JSON translation API against the same shared engine.
- Added the uploaded pronoun and Izon/English grammar reference documents to `references/`.
- Validation: 62 automated tests pass, including all 103 supplied corpus pairs in both directions and browser HTTP route tests. This validates the tested software paths, not general linguistic accuracy.

## 10 November 2026 — compound and complex sentence composition

- Added `clause_engine.py`. It splits a compound or complex sentence at a recognized connective, translates each clause with the single-clause engine, and recombines the clauses in both directions.
- Connectives come only from the owner-supplied corpus (counts in the module docstring): `gbá` (and), `ọ̀kpọ̀` (but), `ọ́bọ́` (so), `Bárá … fịẹ́ị` (because, clause-initial), `… bá … fịẹ́ị` (because, clause-final), and `… ásáìn` (while). An online search found no accessible Kolokuma conjunction rules, so these are not independently verified.
- A non-final "because" clause is declined, because the corpus attests it only in final position. Questions are declined. Any clause the engine cannot translate causes the whole sentence to decline, so existing flagged fallbacks still apply.
- Clause translation first consults the verified corpus for an exact simple sentence, then the rule engine.
- Dictionary usage labels (`loc.`, `aux.`, `fig.`, and similar) are stripped from glosses. Previously `bòyèmí` produced "loc.ing come".
- Verb homonym selection now prefers the entry whose head sense is the English word. "come" selects `bó` (loc. come) rather than `kóro¹` (fall; … come down).
- Clause output containing a stray combining mark (a malformed headword) is declined rather than emitted.
- Added `tests/test_compound_composition.py` (25 tests). The full suite now has 87 passing tests. The exact-pair evaluator remains at 100% in both directions.
- Noun homonym ranking was tried and reverted because it broke the adjective-copula decline ("beautiful"). "man" still resolves to the first dictionary homonym ("human being").

## Lexicon enrichment: family terms and basic vocabulary

- Added `data/lexicon_supplement.csv` (about 40 rows). Each row records its source (dictionary, owner corpus) and status (dictionary-attested, corpus-attested, or dictionary-attested-unconfirmed).
- `load_lexicon` loads the supplement and places its rows first in English lookups, so curated glosses beat unrelated senses ("man" now gives kìmí, not "human being").
- Family terms now resolved: uncle (da ụ́, paternal), brother (bịnaowéi), sister (bịnaará ụ), elder brother/sister, grandmother, widow, orphan, family, friend, male/female friend, son-in-law/father-in-law, sister-in-law (flagged by dictionary editors), elderly person/old man.
- Basic vocabulary added: man, woman, wife, pot, shirt, farm, plantain, evening, song, this, that, good, bad, old, new, long, tall.
- Core 171-word audit: missing words fell from 29 to 12. Remaining: what, where, how, many (interrogatives/quantifiers, intentionally unmapped), short (handled by morphology), aunt, cousin, nephew, niece, meat, sing, bed (no attested forms found in dictionary, owner corpus, or online sources).
- Known conflicts to resolve with a speaker: wife (dictionary ta(á) vs corpus éré); woman (dictionary eré vs corpus ìyó); boy (existing yaị́ bi vs corpus tọ́bọ́ú); this/that need noun-class agreement (Bèí/Ú for masculine, Ú má for feminine), which is not yet implemented.

## Verb constructions: inventory and diagnostics

- Added `verb_rules.py`, an explicit inventory of English verbal constructions. Each entry records the Izon form, its source, and a status (attested, attested-flag, or unsupported).
- Attested and applied by the existing morphology layer: progressive (-yemi / -timimi), past (-mi), present perfect (-dọụ, flagged), future (-nghimi, flagged), negation (-agha).
- Unsupported, with no source in the project materials: modals can/could/must/should/may/might, want/need/wish/hope + to (infinitive complement), past perfect (had + V), and English-to-Izon passive. The one documented passive example (IZ-VOICE-001) is Izon-to-English only.
- Unsupported sentences now name the construction and the reason, instead of a generic message. Outputs containing [UNKNOWN] from a modal or infinitive are no longer returned as-is.
- Added `tests/test_verb_rules.py`. Existing tests and the exact-pair evaluator still pass.
- Open for speaker validation: whether simple present takes -nimi (USR-TAM-001 says yes, but corpus sentences such as "The girl eats yam" show none); the perfect and future labels; modal and infinitive forms.
