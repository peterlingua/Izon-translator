# Kolokuma Izon–English Grammar Reference for the Rule-Based Translator

This is the documented grammar reference used to guide the transfer rules. It intentionally separates **research-backed observations** from **implementation heuristics**. A published description or one example does not establish a rule for every verb, noun class, aspect, or context. Have fluent Kolokuma speakers validate the generalizations and generated examples before using the system for high-stakes or public-facing translation.

## 1. Kolokuma Izon: rules relevant to sentence translation

### 1.1 Clause order

A 2025 study of the Kolokuma dialect describes multiple sentence patterns and gives examples where the finite/main verb occurs at the end of the clause. For simple transitive clauses, the useful starting generalization is **Subject–Object–Verb (SOV)**, while English normally uses Subject–Verb–Object (SVO). Adverbial material may occur before the final verb in Izon where English more often places it after the verb.

Examples reproduced from Isoun and Egbuson (2025):

| Kolokuma Izon | English rendering in the study | Pattern used here |
|---|---|---|
| `Ebi diibi pelemi` | Ebi cut the net. | SOV → SVO |
| `Eri bubaikoyo paami` | He travelled yesterday. | S-A-V → S-V-A |
| `Tobou bi banghimi` | The boy ran. | Subject + predicate + post-nominal marker |
| `Ari fun bi tebulu ongono werimi` | I left the book on the table. | S-O-A-V |
| `Wo dau aru u pirimi` | His father gave him a car. | Multiple-object pattern |

The engine applies generic reordering only when it detects exactly one likely lexical verb and a simple final-verb clause. Multiple clauses, embedded punctuation, and uncertain analyses are not mechanically reordered.

### 1.2 Noun phrases and determiners

The paper gives `Tobou bi` for “the boy”, illustrating a noun followed by a definite/class marker where English puts a determiner before the noun. The engine therefore uses post-nominal `bi` as a **default approximation** for English `the` in simple generation and moves recognized markers before the noun in English output. This is not a full determiner system: marker choice and demonstrative/noun-class distinctions need more contextual data and native-speaker review. English `a/an` is omitted by the current basic transfer rule instead of being assigned a false one-to-one Izon word.

### 1.3 Subject complements and copulas

Some Izon subject–complement examples do not have an overt word that corresponds to English *be*. The study renders `Diepreye inei binaowei` as “Diepreye is my brother” and `Omini ikiaotu` as “They are friends.” The exact pairs are stored in the parallel corpus; general copula insertion is not yet inferred safely for arbitrary sentences.

### 1.4 Tense, aspect, and verb morphology

A comparative morphological study of English and Izọn describes differences in how tense/aspect and number are expressed. Izon verbs should not be assumed to take the same English suffixes, and an English tense label cannot always be mapped to one Izon ending. The source dictionary itself records complex forms and aspectual examples. The code currently uses limited pattern heuristics such as English past → Izon `-mi` and progressive → `-yemi` only after identifying a dictionary verb. **These generated forms are provisional, not a complete conjugation system.** The Kolokuma corpus must be expanded by verb and aspect and checked with fluent speakers.

### 1.5 Negation

A Kolokuma-focused 2025 study describes `-gha` in negative statements and `kumo` with negative imperatives, and notes that perfective and future negative forms involve additional changes. The current engine only attempts a narrow statement-level `-gha` pattern. It does not claim to generate correct imperative, perfective-negative, or future-negative forms generally.

### 1.6 Agreement, pronouns, and tone

The comparative morphology study reports that Izon does not mark subject singular/plural agreement on verbs in the same way English does. The English output generator therefore adds English third-person singular present agreement where its simple subject heuristic supports that choice, but it does not add an English-style `-s` to Izon verbs.

Tone and vowel diacritics matter. The lookup layer first tries the source spelling and then uses a tone/diacritic-insensitive fallback for unmarked user input. Because tone and vowel quality may distinguish words, this fallback can select the wrong homonym; retain diacritics wherever possible.

### 1.7 Not yet covered by generic transfer

The current sentence rules are not a general parser for wh-questions, yes/no question formation, imperatives, relative clauses, coordinate/subordinate clauses, focus particles, reported speech, noun-class-sensitive determiners, or the full tense/aspect/negation system. Store each new pattern as multiple speaker-checked minimal pairs before generalizing it.

## 2. English grammar rules used for the target/source side

These are standard English rules that the translator must account for when transferring between English and Izon. The code implements only the subset described below.

### 2.1 Basic declarative clause: SVO

In ordinary English declarative clauses, the subject normally precedes the main verb and a direct object follows it: `The child ate yam.` English → Izon transfer moves the object/adjunct material before the main verb for a simple, confidently parsed Izon clause. Izon → English transfer moves a final Izon predicate immediately after the subject.

### 2.2 Determiner and noun order

English determiners precede nouns (`the child`, `a book`) and many attributive modifiers precede the noun (`the small child`). The current rule moves `the` to the post-nominal Izon marker position (default `bi`) and omits `a/an`. Complex adjective order, countability, definiteness, demonstratives, and number are not resolved reliably yet.

### 2.3 Subject–verb agreement

In the English simple present, a third-person singular subject generally selects an `-s`/`-es` verb form (`he runs`, `Ebi goes`), with irregular forms such as `has` and `does`. Other subjects use the base form (`I run`, `they run`). The Izon → English heuristic adds a simple third-person singular ending when the source predicate has no detected past/progressive feature. Subject number is inferred conservatively from the translated subject, and this rule should be checked against the actual tense/aspect intended by the Izon sentence.

### 2.4 Past and progressive forms

English past forms may be regular (`walked`) or irregular (`went`, `ate`, `gave`). The engine has a small lexicon-based lemmatizer for common regular and irregular forms and uses it to find a dictionary verb. For English progressive (`is eating`), it suppresses the English auxiliary and uses a narrow Izon `-yemi` heuristic. This is an engineering approximation, not evidence that all verbs take that ending.

### 2.5 Negation

Standard English declarative negatives often use auxiliary `do/does/did` plus `not` with the base verb (`I do not go`, `he does not go`). The engine collapses this into a provisional Izon negative-verb form rather than translating `do` as a lexical verb. More complex scope, tense, aspect, and negative imperatives are not covered.

### 2.6 Questions, commands, and multi-clause sentences

English questions can require auxiliary inversion or do-support; commands often omit an explicit subject; relative and subordinate clauses have their own word order and punctuation. These forms are documented as required English grammar but are not generically transformed yet. The parser declines most multi-clause/uncertain cases rather than pretending that word-level substitution is grammatical.

## 3. Implementation map

| File | Role |
|---|---|
| `data/izon_dictionary_a_z.csv` | Original supplied dictionary; kept intact |
| `data/grammar_rules.csv` | Sourced rules, evidence state, exact examples, and implementation notes |
| `data/parallel_corpus.csv` | 13 retained research seed pairs plus 90 project-owner-supplied sentence pairs; exact lookup in both directions |
| `lexicon.py` | Compact glosses, phrase/sense indexes, tone-insensitive fallback, repair for split final marked vowels, suppression of reference-only rows |
| `tokenizer.py` | Unicode-aware tokenization that keeps combining tone marks attached to their word |
| `sentence_engine.py` | Conservative one-main-verb reordering, morphology-aware unit analysis and limited English/Izon inflection/function-word handling |
| `grammar.py` | Exact sentence lookup and final punctuation restoration |
| `morphology.py` | Selected source-supplied noun and adjective patterns, explicit Bii/Gẹẹ/Mu paradigms, and English adjective mappings |
| `data/izon_morphology.csv` | Machine-readable morphology and pronoun inventory from the project owner’s rules document |
| `references/` | Original user-supplied Word documents retained for traceability |
| `tests/` | Regression, Unicode, published-example, and generic transfer tests |

## 4. Sources

1. Isoun, E. B. & Egbuson, G. (2025). “Sentence Patterns in Izon Using the ‘Kolokuma’ Dialect as a Case Study.” *International Journal of Education and Social Science*, 7(3), 27–36. [PDF](https://iigdpublishers.com/storage/9YWJhVs36tiJcZ3CvRaepAptCw1XER-metaU2VudGVuY2UgUGF0dGVybnMgaW4gSXpvbiAyNy0zNi5wZGY%3D-.pdf)
2. Okotori, B. & Simon, T. (2025). “Morphosyntax of Negation in Kolokuma.” *International Journal of Studies in Advanced Education*, 4(8). [Article](https://scholarsdigest.org/index.php/ijsae/article/view/1152)
3. Kwokwo, B. & Werigbelegha, A. (2017). “A Morphological Study of Inflectional Features in English and Izọn.” *Niger Delta Research Digest*, 12(2), 108–122. [DOI](https://doi.org/10.5281/zenodo.17319901)
4. University of Lagos Institutional Repository. “The Influence of Izon on the Syntax and Lexis of the English of Izon-English Bilinguals.” [Repository PDF](https://ir.unilag.edu.ng/bitstream/123456789/4305/1/The%20Influence%20of%20Izon%20on%20the%20Syntax%20and%20Lexis%20of%20Izon-%20English%20Bilinguals.pdf)

The 2025 sentence-pattern study is a useful starting point, but it uses a small sample; the 13 stored examples are not a substitute for a larger, independently speaker-validated parallel corpus.


## 1.8 Rules supplied by the project owner

The owner's document `references/ijaw_rules_reference.docx` is the authority for the source-derived morphology in this version. Its terminology and spellings are retained in `data/izon_morphology.csv` and `data/grammar_rules.csv`.

### Nouns and nominal forms

The source lists **-mo** as a definite plural marker (`akasi` → `akasimo`, “the chairs”), **-ama** as an indefinite plural marker (`ekpeti` → `ekpeti-ama`, “boxes”), and **-otu** as a plural marker (`ogoni` → `ogoni-otu`, “visitors”). It also lists `kimimo` (“the men”), `oweiamini` (“the men”), `ereabàu` (“girl/miss”), `erearau` (“Mrs/madam”), and `ereamini` / `ereaminimọ` (“the women”). Because some are not regular concatenations of a single suffix, the engine treats the exact listed examples as trusted forms and only generalizes a plural suffix when a dictionary noun base can be found.

### Pronoun cases

The table separates subjective, objective, genitive, predicative possessive and reflexive forms. Representative forms include Àri / Woni (I/we), Ári / Ọ́mịnị (you singular/plural as supplied), Eri / arau (he/she), Ì / wó (me/us), Í / ó (you object singular/plural), Wò/ù (him), árà/á (her), Ò (them), Ìnè (my), Wó (our), Ínè/ínè (your), oro (their), Wòi (his), árà (hers), ọ̀rèi (theirs), and ìnèọngọ / áràọngọ / wòọngọ (myself/herself/himself). The source also lists Ìnei for both “mine” and “yours”; this collision is preserved. Since English does not overtly mark every case contrast, the translator's mappings are provisional defaults rather than a context-complete pronoun system.

### Adjectives

The supplied roots are `zau` (small), `ganị` (expensive), `sụ` (lazy), and `Ikịsá` (short). The source uses **-dẹịn** for comparatives, **-fa** for superlatives, **-kami** for “very”, **-bọwẹmi** for “too”, and **-agha / -kumo** for negative forms. Hyphenation varies by example; `morphology.py` emits the documented form for each supplied root. For other roots it applies the pattern provisionally and does not claim that it has been validated for all adjective classes.

### Verb tense/aspect examples

The document labels **-nimi** as present, **-mi** as past, **-yemi** as present progressive, **-dọụ** as present perfect, **-nghimi** as future, **-timimi** as past progressive, and **-agha** as negation. Rather than deriving every form from a generic stem-plus-suffix recipe, `morphology.py` stores the individual examples for Bii, Gẹẹ and Mu. This matters because the document shows spelling/stem variation and a split-cell transcription: the Bii future example appears as `biiịnghim`, while the other examples include `gẹẹnghimi` and `munghimi`; the document's gloss for `gẹẹnghimi` also reads “will come” although the base is glossed “write”. These entries require review before being generalized to all verbs.

## 1.9 Owner-supplied sentence pairs and compound clauses

The project owner supplied 30 simple pairs, 30 compound pairs and 30 compound-complex pairs in `references/ijaw_sentence_translation_examples.docx`. All 90 are included in `data/parallel_corpus.csv` alongside the original 13 seed pairs. They are used as exact full-sentence overrides in both directions. Therefore, the examples demonstrate the system's ability to reproduce those supplied translations; they do **not** mean that the generic parser can currently generate arbitrary compound or compound-complex sentences.

One English rendering (“Because my head is paining me, I am sleeping, but they are eating plantain.”) is paired with two slightly different Izon forms in the source. Both Izon forms are preserved, and English-to-Izon exact matching uses the first stored form as the canonical output while the evaluator accepts either source-listed variant. The source heading says “Compound-Complex Sentences (15 Examples)” but the document actually lists 30 numbered examples; all 30 listed pairs are retained.
