"""Streamlit interface for the Kolokuma Izon <-> English translator.

Run locally:   streamlit run app.py
Run on a host: streamlit run app.py --server.address 0.0.0.0 --server.port $PORT

It uses the same translator and lexicon as web_app.py, so the results match.
"""
import streamlit as st

from lexicon import load_lexicon, lookup_english_word, lookup_izon_word
from translator import translate

DIRECTIONS = {
    "English → Izon": "english_to_izon",
    "Izon → English": "izon_to_english",
}


@st.cache_resource(show_spinner="Loading dictionary...")
def get_lexicon():
    return load_lexicon(verbose=False)


def is_flagged(output: str) -> bool:
    """True when the translator declined or could not translate a word."""
    return output.startswith("[UNSUPPORTED") or "[UNKNOWN" in output


def clean_output(output: str) -> str:
    return output.strip()


st.set_page_config(page_title="Izon ↔ English Translator", page_icon="🗣️", layout="centered")
st.title("Kolokuma Izon ↔ English Translator")
st.caption("Simple, compound and compound-complex sentences, plus word lookup.")

label = st.radio("Direction", list(DIRECTIONS), horizontal=True)
direction = DIRECTIONS[label]

tab_sentence, tab_word = st.tabs(["Translate a sentence", "Look up a word"])

with tab_sentence:
    sentence = st.text_area(
        "Enter a sentence",
        placeholder="e.g. The girl eats yam, and the boy is sleeping." if direction == "english_to_izon"
        else "e.g. Érí bòyèmí, gbá ụ́ bi burú ị́ị.",
        height=110,
    )
    if st.button("Translate", type="primary", width="stretch"):
        if not sentence.strip():
            st.info("Please enter a sentence.")
        else:
            with st.spinner("Translating..."):
                output = clean_output(translate(sentence, direction))
            if is_flagged(output):
                st.warning(output)
            else:
                st.success(output)
                st.code(output, language=None)

with tab_word:
    word = st.text_input(
        "Enter a word",
        placeholder="e.g. mother, uncle, girl" if direction == "english_to_izon" else "e.g. dádà",
    )
    if word.strip():
        loaded = get_lexicon()
        if direction == "english_to_izon":
            matches = lookup_english_word(word.strip(), loaded)
        else:
            matches = lookup_izon_word(word.strip(), loaded)
        if not matches:
            st.info("No entry found for that word.")
        else:
            rows = [
                {
                    "Izon": row.get("izon", ""),
                    "English": row.get("english", ""),
                    "Meaning": row.get("full_english", ""),
                    "Part of speech": row.get("part_of_speech", ""),
                }
                for row in matches
            ]
            st.dataframe(rows, width="stretch", hide_index=True)

with st.sidebar:
    st.header("About")
    st.write(
        "Rule-based translation from the Williamson & Blench dictionary and the "
        "owner-supplied sentence corpus."
    )
    st.write(
        "Where a sentence or word has no attested form, the app says so instead of guessing. "
        "Verified corpus sentences are returned exactly as recorded."
    )
