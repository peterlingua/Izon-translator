# Bilingual Kolokuma Izon–English sentence-structure rules

This rule set is based on the bilingual sentence examples supplied in `references/ijaw_sentence_translation_examples.docx`. The examples are stored as exact pairs in `parallel_corpus.csv` and can be looked up in both translation directions.

## 1. Simple sentences

**Izon (source-side analysis):** The supplied examples show several patterns rather than one fixed template: subject + predicate; subject + object/material/adjunct + final predicate; subject–complement expressions without an overt equivalent of English *be*; and imperative clauses. Verbal clauses often place the verb late or finally.

**English (target/source-side analysis):** A simple clause normally has `S + V + (O / C / A)`. Copular clauses use `S + BE + C`; imperatives may have an unspoken subject `(you)`. During Izon → English transfer, identify semantic roles and realize English SVO where appropriate. During English → Izon transfer, do not copy English word order mechanically.

## 2. Compound sentences

**Izon:** `[independent clause] + [Izon coordinator/linker] + [independent clause]`. The source examples use forms including `kọ̀`, `ọ̀bọ̀`, `gbá`, `kọ́`, and `ọ̀kpọ̀. Their relation is context-sensitive; the same form must not be assigned a single fixed English conjunction without validation.

**English:** `[independent S + V clause] + coordinating conjunction + [independent S + V clause]`. Parse both clauses separately; classify addition, contrast, result/reason, or alternative; then use an attested Izon linker.

## 3. Compound-complex sentences

**Izon:** At least two independent clauses plus at least one dependent clause. The supplied examples include cause/time-dependent material with forms such as `bárá`, `bá`, and `ásáìn`, alongside coordinating linkers. Clause order varies.

**English:** At least two independent clauses plus at least one dependent clause, e.g. `because/while + subordinate clause` together with coordination. Parse the dependency before translating; commas alone do not define clause boundaries.

## 4. Project implementation status

- 30 simple, 30 compound, and 30 compound-complex bilingual examples are stored in `data/parallel_corpus.csv` (90 user-supplied pairs).
- Exact pair lookup is available in both directions through `grammar.py`; this supports these listed examples, including punctuation restoration.
- Structural rules are also recorded in `data/grammar_rules.csv` as IZ-SS-001–003 and EN-SS-019–021.
- The structural inventory is documentation, not a complete syntactic parser. Unseen multi-clause generation still requires clause segmentation, semantic classification of linkers, and speaker-validated rules.
- The source examples are retained as supplied. They have not been independently adjudicated by a Kolokuma linguist; validate spelling, tone, glosses, and phrase/POS boundaries before treating the analysis as definitive.

## 5. Phrase-level labels for diagrams

`S` = sentence/clause; `NP` = noun phrase; `VP` = verb phrase/predicate; `AdjP` = adjective phrase; `PP` = prepositional phrase (English label); `AdvP` = adverb phrase; `CONJ` = coordinator; `SUB` = subordinator; `N` = noun; `V` = verb; `PRON` = pronoun. Izon postpositional phrases should be labelled separately from English prepositional phrases where the constituent analysis supports that distinction.
