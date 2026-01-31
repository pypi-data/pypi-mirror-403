# destruction/language.py

from destruction.wordscore import LANG_WORDS

def detect_language(text: str) -> dict[str, float]:
    text = text.lower()
    scores = {}

    for lang, words in LANG_WORDS.items():
        score = 0
        for w in words:
            if w in text:
                score += len(w)
        if score > 0:
            scores[lang] = score

    total = sum(scores.values())
    if total == 0:
        return {}

    # Normalize
    return {k: v / total for k, v in scores.items()}
