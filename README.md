# Kolokuma Izon ↔ English Rule-Based Sentence Translator

> **Consolidated build (21 October 2026).** This package includes the launchers, browser UI, lexicon, grammar and morphology resources, sentence-pair corpus, rule-based sentence transfer, interrogative generalization, and automated tests in one folder. It is a research prototype, not a claim of complete translation coverage.

## Start here

1. Extract the ZIP completely.
2. Double-click `Launch_Translator.bat` or `run_web_app.bat`.
3. Keep the terminal window open and use the browser app at `http://127.0.0.1:8000/`.
4. If the browser does not open, visit that address yourself. For the text menu, double-click `run_translator.bat`.
5. Run `run_tests.bat` or `python -m unittest discover -s tests -v` to check the code.

See `PROJECT_STATUS_AND_LIMITATIONS.md` for a plain-language list of implemented patterns and remaining linguistic limitations.

## What is included

- `Launch_Translator.bat` and `run_web_app.bat` — double-click to open the browser app on Windows.
- `web_app.py` — local browser interface (opens at `http://127.0.0.1:8000/`).
- `run_translator.bat` — command-line interface launcher.
- `main.py` — interactive command-line interface.
- `english_to_izon.py`, `izon_to_english.py` — translation entry points.
- `translator.py` — exact-pair precedence, morphology-aware matching, dictionary phrase lookup and fallback for unknown words.
- `sentence_engine.py` — conservative simple-clause transfer, limited SVO/SOV reordering and selected tense/aspect/negation handling.
- `clause_engine.py` — compound and complex sentence composition (`gbá`, `ọ̀kpọ̀`, `ọ́bọ́`, `Bárá … fịẹ́ị`, `bá … fịẹ́ị`, `ásáìn`), recombining clauses from the single-clause engine in both directions. Declines whenever a clause cannot be translated.
- `morphology.py` — source-grounded noun/adjective helpers and explicit paradigms for the three verbs in the supplied rule sheet. It avoids inventing a paradigm for an unlisted verb.
- `lexicon.py` — dictionary loading, compact glosses, phrase/sense indexes, tone-insensitive fallback and cleanup of malformed reference rows. The supplied A–Z dictionary contains 5,878 rows; 5,870 entries are usable after reference-only or incomplete rows are excluded.
- `tokenizer.py` — Unicode-aware tokenization that keeps Izon combining marks with their word.
- `grammar.py` — exact sentence-pair lookup and terminal punctuation handling.
- `data/izon_dictionary_a_z.csv` — original dictionary, preserved as supplied.
- `data/grammar_rules.csv` — general Izon and English rules, plus the rules from `ijaw rules (1).docx`, with source and implementation status.
- `data/izon_morphology.csv` — machine-readable inventory of the supplied noun markers, pronoun forms, adjective forms and verb examples.
- `data/parallel_corpus.csv` — 103 sentence pairs: the 13 existing research seed pairs plus 90 pairs supplied in `ijaw machine translation.docx` (30 simple, 30 compound, and 30 compound-complex).
- `data/grammar_reference.md` — grammar and implementation notes, including unresolved source-table ambiguities.
- `data/sentence_structure_rules.md` — bilingual Izon and English structures for simple, compound and compound-complex sentences.
- `references/` — original Word documents supplied for the rules and sentences.
- `tests/` — automated regression tests for the dictionary, source pairs, productive sentence rules, and the actual browser HTTP routes.
- `evaluator.py` — exact-match evaluator. It accepts alternate Izon outputs where the source gives the same English gloss with more than one Izon form.

## Run on Windows (PowerShell)

Extract this ZIP into a folder. Open PowerShell in the folder that contains `main.py`, then run:

```powershell
python main.py
```

Choose `1` for English → Izon, `2` for Izon → English, `3` for an Izon dictionary/morphology lookup, or `Q` to quit.

Check that the folder is correct before running:

```powershell
Get-ChildItem
```

You should see `main.py`, `translator.py`, `sentence_engine.py`, `lexicon.py`, `grammar.py`, `morphology.py`, and the `data` folder. If you only see another folder named `Kolokuma_Izon_Translator_Improved`, enter it with `cd .\Kolokuma_Izon_Translator_Improved` first.

## Run the tests

Python 3.10 or newer is recommended. The project uses only the Python standard library.

```powershell
python -m unittest discover -s tests -v
python evaluator.py
```

## Translation pipeline

1. **Exact pair lookup.** A supplied full sentence that matches `data/parallel_corpus.csv` is returned using its paired translation. This supports all 90 supplied examples in both directions, including questions, commands, compound sentences and compound-complex sentences.
2. **Morphology-aware handling.** The engine recognizes the four adjective roots and their supplied comparative/superlative/intensifier/negative forms, selected noun plural/title forms, and explicit verb paradigms for Bii, Gẹẹ and Mu. Pronoun defaults prefer the forms in the supplied pronoun table.
3. **Conservative generic sentence transfer.** Where a simple clause can be identified, the engine applies limited SVO/SOV reordering, function-word handling and selected verb features. It does not yet parse arbitrary multi-clause sentences generatively.
4. **Noun phrase transfer.** A recognized English definite noun phrase such as `the girl` is reordered to the project’s Izon noun + post-nominal marker pattern (`Ụ́ bi`). The indefinite article in `a girl` is omitted. In the reverse direction, the attested `ụ́ bi` context selects the dictionary’s girl sense.
5. **Dictionary fallback.** Single words and known phrases remain available for lookup. Unsupported multiword inputs are flagged instead of being collapsed into an unrelated dictionary homonym. A bare Izon homograph with multiple dictionary meanings is reported as ambiguous rather than silently choosing the first CSV row.

## Important accuracy note

The 90 sentence pairs from the project owner are marked as supplied/accepted examples because the owner presented them as correct translations. They are **not independently adjudicated by the software team or a second fluent speaker**. The exact-pair evaluator measures reproduction of stored examples, not generalization to new sentences. The user document's compound-complex heading says “15 Examples” while it actually lists 30 numbered examples; all 30 listed pairs were retained.

The rules document also has formatting and transcription ambiguities. For example, it gives two Izon spellings for some English glosses and the Bii future form appears as “biiịnghim” in a split table cell. These forms are preserved and flagged for review rather than silently corrected. Pronoun choices can depend on subject/object/genitive/standalone possessive context; the current English-to-Izon mappings are defaults, not a full contextual case resolver.

## Adding more data safely

Add reviewed sentence pairs to `data/parallel_corpus.csv` using the existing columns, and retain the source and review status in `notes`. Avoid placing conflicting translations under one identical source sentence unless both variants are explicitly allowed. Add morphology to `data/izon_morphology.csv` and `data/grammar_rules.csv`; only make it a generic code rule after adding regression tests for positives, negatives and exceptions.

For meaningful accuracy estimates, create `data/evaluation_pairs.csv` containing held-out sentences not already in the exact-match corpus, and have competent Kolokuma speakers independently check the output. The exact-match score on the bundled examples is not a measure of unseen-sentence translation quality.


## Interrogatives and pronouns update (21 October 2026)

The translator now includes phrase-level transfer rules for the interrogative and demonstrative examples in the supplied Ịzọn reference: “Which house?”, “Who did it?”, “For whom?”, and “Whose shirt is this?”, plus several demonstrative examples. These are intentionally phrase-level because the source says interrogative meanings are compositional and context-dependent. This update does **not** claim a verified standalone translation for every English wh-word (especially “what”); a native-speaker-confirmed example for “What is my name?” is still needed before encoding a reliable translation. Existing personal-pronoun overrides remain in place. Added `tests/test_pronoun_interrogative_rules.py` for regression coverage. Source spellings and structures are preserved, but the supplied materials are general Ịzọn/Ijaw references and should be checked with a Kolokuma speaker before treating all forms as confirmed Kolokuma.

## New compositional interrogative rules

The question handler now generalizes two source-backed structures to new phrases when the key noun/object is present in the dictionary:

- `Which + known noun?` follows the documented `Tị + noun + nị?` pattern.
- `Who did + known object?` follows the supplied `Tịbọ kị + object + mịẹ nị?` frame.

These are rule-based generalizations from the supplied examples, not proof that every generated sentence is idiomatic Kolokuma. In particular, the source materials do not establish a verified general form for `What is my name?`; the program should not pretend an unsupported translation is correct. Newly generated outputs should be reviewed by a Kolokuma speaker and added to the regression tests once confirmed.


## Important: make sure the browser uses the updated server

Start the browser interface using `Launch_Translator.bat` from this extracted project folder.
The server prints the exact `web_app.py`, `translator.py`, and dictionary CSV paths it is using,
plus a quick test result for `who is the girl`. Open the URL printed by that same window.

If an older translator is already using port 8000, this version automatically selects the next
available port and opens that new URL instead of failing to start while the browser keeps showing
the old process. Stop old translator windows with Ctrl+C when possible. Refresh the page after
launching the updated server.

The dictionary includes `Tịbọ,pronoun,who`. The browser form and the `/api/translate` JSON endpoint call the same `translator.translate()` function used by the command-line interface; they do not implement a separate translation algorithm. `/api/lookup` searches the supplied dictionary, and `/api/health` reports the dictionary and translator file paths currently loaded by the server.

The dictionary entry for `girl` is `ụ́` (noun; the source gloss includes “daughter; girl”). The bare Izon form `ụ́` is homographic with other entries in the dictionary, so the reverse translator does not guess a single meaning when it appears alone. The attested noun phrase `ụ́ bi` is contextually translated as `The girl`.

## Bilingual sentence-structure rules

The project includes 30 simple, 30 compound, and 30 compound-complex Kolokuma Izon–English sentence pairs supplied by the project owner. They are stored in `data/parallel_corpus.csv` and are available for exact sentence lookup in both directions. The corresponding Izon and English structural descriptions are in `data/grammar_rules.csv` (IZ-SS-001–003 and EN-SS-019–021), with fuller notes in `data/sentence_structure_rules.md`. These exact examples do not mean that unseen compound or compound-complex sentences are fully parsed or generated; the limitations and speaker-validation needs are documented.

## Put the app online (so a phone can open it)

The app runs on your computer at `127.0.0.1`, which a phone cannot reach. To get a link that works on a phone, deploy it to a hosting service. The project needs no packages and no database.

1. Put the project folder in a GitHub repository (create a free account at github.com, then upload the folder).
2. On a host such as Render (render.com) or Railway (railway.app), create a new **Web Service** from that repository.
3. Use these settings:
   - Build command: none (leave empty), or use the Dockerfile if the host offers it.
   - Start command: `python web_app.py`
   - Environment: Python 3.12 (or the Docker option, which uses the included `Dockerfile`).
4. The host gives you a public address such as `https://your-app.onrender.com`. Open it on your phone and submit that link.

The app reads `PORT` and `HOST` from the environment. On a host it listens on all interfaces and does not open a browser. Locally, nothing changes: `python web_app.py` still opens `http://127.0.0.1:8000/`.

Files added for deployment: `Procfile`, `Dockerfile`, `.dockerignore`, `requirements.txt`.

## Use it as a phone app (installable web app)

The app can be installed on a phone's home screen. It then opens full screen, with its own icon, like an app. This is a Progressive Web App: it uses the same hosted link, so there is nothing to publish to an app store.

1. Deploy the app as described above and open the link in the phone's browser (Chrome on Android, Safari on iPhone).
2. Android (Chrome): tap the menu (⋮) and choose **Install app** or **Add to Home screen**.
3. iPhone (Safari): tap the Share button and choose **Add to Home Screen**.
4. Open the new icon. The app runs full screen. Translation needs an internet connection because the translator runs on the server.

A native Android or iOS app would need Android Studio or Xcode and an app-store account. This web-app version avoids both.


## Streamlit version (current deployment)

The interface is now a Streamlit app (`app.py`). It uses the same translator and lexicon as the earlier web page, so results are identical.

Run locally:

```
pip install -r requirements.txt
streamlit run app.py
```

Then open the address Streamlit prints (usually `http://localhost:8501`).

On Render, use these settings for a Web Service:
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`

Streamlit apps are responsive, so the page works in a phone browser. Streamlit does not add a home-screen install icon by itself; users can open the link on the phone and bookmark it.
