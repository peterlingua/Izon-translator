"""Unicode-aware tokenization helpers for Kolokuma Izon and English."""
import re
import unicodedata

# Python's ``\w`` does not include all Unicode combining marks. Izon tone
# sequences can remain decomposed after NFC, so marks must stay attached to the
# preceding letter instead of becoming independent punctuation tokens.
_MARKS = "\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f"
_TOKEN_RE = re.compile(
    rf"\w[\w{_MARKS}]*(?:['’]\w[\w{_MARKS}]*)*|[^\w\s{_MARKS}]",
    flags=re.UNICODE,
)


def normalise_text(text: str) -> str:
    """Normalize Unicode to NFC and collapse repeated whitespace."""
    return " ".join(unicodedata.normalize("NFC", str(text or "")).strip().split())


def normalise_word(word: str) -> str:
    """Case-insensitive Unicode normalization; diacritics are preserved."""
    return unicodedata.normalize("NFC", str(word or "").strip()).casefold()


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalise_text(text))


def detokenize(tokens) -> str:
    """Join tokens while keeping punctuation attached to the preceding word."""
    text = " ".join(str(t) for t in tokens if t is not None and str(t) != "")
    text = re.sub(r"\s+([.,!?;:%…])", r"\1", text)
    text = re.sub(r"([¿¡])\s+", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\s+(['’])", r"\1", text)
    return text.strip()


if __name__ == "__main__":
    sentence = input("Enter a sentence: ")
    print("Tokens:", tokenize(sentence))
    print("Reconstructed:", detokenize(tokenize(sentence)))
