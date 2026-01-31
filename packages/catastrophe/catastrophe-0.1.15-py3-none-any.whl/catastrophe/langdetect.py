from __future__ import annotations
from collections import Counter
from math import sqrt

# Letter frequencies (approximate, normalized)
LETTER_FREQ = {
    "EN": {"E":12.0,"T":9.1,"A":8.1,"O":7.6,"I":7.3,"N":7.0},
    "IT": {"E":11.5,"A":11.7,"I":10.1,"O":9.8,"N":6.9},
    "FR": {"E":14.7,"A":7.6,"I":7.5,"S":7.9,"N":7.1},
    "ES": {"E":13.7,"A":12.5,"O":8.7,"S":8.0,"N":7.0},
    "DE": {"E":16.4,"N":9.8,"I":7.6,"S":7.3,"R":7.0},
}

def _vector(text: str):
    letters = [c for c in text.upper() if "A" <= c <= "Z"]
    if not letters:
        return {}
    total = len(letters)
    return {k: v/total*100 for k,v in Counter(letters).items()}

def _distance(v1, v2):
    keys = set(v1) | set(v2)
    return sqrt(sum((v1.get(k,0)-v2.get(k,0))**2 for k in keys))

def detect_language_score(text: str) -> float:
    v = _vector(text)
    if not v:
        return 0.0
    scores = []
    for freq in LETTER_FREQ.values():
        scores.append(_distance(v, freq))
    return 1 / (min(scores) + 1)

def detect_language(text: str) -> str | None:
    v = _vector(text)
    if not v:
        return None
    best, best_d = None, float("inf")
    for lang, freq in LETTER_FREQ.items():
        d = _distance(v, freq)
        if d < best_d:
            best, best_d = lang, d
    return best
