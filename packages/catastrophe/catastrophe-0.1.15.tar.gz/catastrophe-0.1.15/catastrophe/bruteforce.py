# destruction/brute.py

from destruction.scorer import score_text

def brute_force(results: dict[str, str]):
    ranked = []
    for key, text in results.items():
        s = score_text(text)
        ranked.append((s["score"], key, text, s))

    ranked.sort(reverse=True)
    return ranked
