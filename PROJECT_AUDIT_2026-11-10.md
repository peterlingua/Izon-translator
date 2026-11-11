# Project file audit — 10 November 2026

## Scope checked

The latest `Kolokuma_Izon_Sentence_Engine_Safety_Fix` project archive was extracted and its complete file tree reviewed. All Python source files were compiled; CSV resources were parsed; dictionary, grammar-rule and corpus schemas/counts were checked; the automated tests were run; and the browser HTTP routes were exercised locally. Original pronoun and Izon–English grammar documents from the project Library were added to `references/` for traceability.

## Resource audit

| Resource | Result |
|---|---:|
| `data/izon_dictionary_a_z.csv` | 5,878 data rows; 5,870 usable lexicon entries |
| Unique Izon lookup forms | 5,783 |
| Unique English lookup forms | 4,165 |
| `data/grammar_rules.csv` | 74 documented rule records; 5 marked verified |
| `data/parallel_corpus.csv` | 103 verified bilingual sentence pairs (13 seed + 90 owner-supplied) |
| Owner-supplied sentence types | 30 simple, 30 compound, 30 compound-complex |
| `data/izon_morphology.csv` | 47 morphology records |

One dictionary row has an empty English Meaning (`ịde`, row 51 of the CSV); it is skipped by the lexicon loader. Other non-lexical/reference-only rows are also excluded from usable entries. The source dictionary was not rewritten or silently corrected.

## Key defect found and fixed

The dictionary already included `ụ́` with the gloss “daughter; girl”, and English lookup for `girl` could find it. However, the generic sentence engine required a lexical verb, so a noun phrase such as `the girl` was declined even though the corresponding sentence `the girl eats yam` could be generated. This led to inconsistent behavior between word lookup, noun phrases and complete sentences.

The project now applies a narrow noun-phrase transfer path: `girl` → `Ụ́`, `the girl` → `Ụ́ bi`, and `a girl` → `Ụ́`. In the reverse direction, the documented context `ụ́ bi` selects the girl sense and returns `The girl`; the complete clause `ụ́ bi burú ị́ị.` returns `The girl eats yam.`. A bare `ụ́` remains ambiguous because the same written form has other dictionary entries (including fish, moon and two); the system now reports that ambiguity rather than selecting the first CSV row.

A second unsafe behavior was found in copular adjective translation: `beautiful` could be selected as a dictionary verb gloss and then receive a progressive suffix after English `is`. The engine now declines that unsupported pattern instead of presenting the generated form as a valid translation.

## Browser audit

`web_app.py` serves the HTML interface and uses the shared `translator.translate()` function. It now also provides:

- `GET /api/health` — reports loaded dictionary and translator paths.
- `GET /api/lookup?word=girl&direction=english_to_izon` — returns dictionary matches.
- `POST /api/translate` — accepts JSON `{"source": ..., "direction": ...}` and returns the translation.
- `POST /translate` — retains the browser HTML form workflow.

## Validation

- `python -m compileall -q .` — passed.
- `python -m unittest discover -s tests -v` — 62 tests passed.
- All 103 supplied corpus pairs remain covered in both directions.
- Browser HTML form, JSON translation, dictionary lookup and health routes passed HTTP tests.

## Important limitation

This audit establishes that the delivered software is internally consistent on its tested cases. It does not prove that every generated sentence is idiomatic or correct Kolokuma Izon. The simple-clause engine is still limited to patterns it can recognize safely. Compound and compound-complex examples in the corpus are supported by exact pair matching; arbitrary unseen multi-clause generation is not complete. Generated noun markers, pronouns, tense/aspect and all provisional forms should be checked by fluent Kolokuma speakers.
