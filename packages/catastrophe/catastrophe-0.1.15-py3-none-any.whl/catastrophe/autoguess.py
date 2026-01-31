from .bruteforce import brute_force_caesar
from .rot13 import rot13
from .atbash import atbash
from .langdetect import detect_language_score

def auto_guess(text: str, top: int = 5):
    guesses = []

    # ROT13
    guesses.append(("rot13", rot13(text), detect_language_score(rot13(text))))

    # Atbash
    guesses.append(("atbash", atbash(text), detect_language_score(atbash(text))))

    # Caesar brute force
    for shift, decoded, score in brute_force_caesar(text, top=top):
        guesses.append((f"caesar({shift})", decoded, score))

    guesses.sort(key=lambda x: x[2], reverse=True)
    return guesses[:top]
