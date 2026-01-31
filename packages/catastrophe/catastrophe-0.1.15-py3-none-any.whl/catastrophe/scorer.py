# destruction/scorer.py

from destruction.language import detect_language
from destruction.ngrams import score_ngrams
from destruction.entropy import shannon_entropy

def score_text(text: str) -> dict:
    lang_scores = detect_language(text)
    ngram_score = score_ngrams(text)
    entropy = shannon_entropy(text)

    final_score = (
        sum(lang_scores.values()) * 10
        + ngram_score * 2
        - abs(entropy - 4.2) * 3
    )

    return {
        "score": final_score,
        "languages": lang_scores,
        "entropy": entropy,
        "ngram_score": ngram_score,
    }
