# destruction/ngrams.py

ENGLISH_TRIGRAMS = {
    "the": 1.81, "and": 0.73, "ing": 0.72, "her": 0.36, "hat": 0.34,
    "his": 0.34, "tha": 0.33, "ere": 0.31, "for": 0.28,
}

def score_ngrams(text: str) -> float:
    text = text.lower()
    score = 0.0
    for i in range(len(text) - 2):
        tri = text[i:i+3]
        score += ENGLISH_TRIGRAMS.get(tri, 0.0)
    return score
