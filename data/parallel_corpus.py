"""Convenience access to the CSV sentence corpus.

The actual corpus is stored in ``parallel_corpus.csv`` and loaded by ``grammar.py``.
This module remains as a small compatibility helper for scripts that import from
``data.parallel_corpus``.
"""
from grammar import load_parallel_pairs


def get_pairs():
    """Return rows marked verified=yes in the parallel-corpus CSV."""
    return load_parallel_pairs()


if __name__ == "__main__":
    rows = get_pairs()
    print(f"Loaded {len(rows)} source-attested sentence pairs.")
    for row in rows:
        print(f"{row['english']}  <->  {row['izon']}")
