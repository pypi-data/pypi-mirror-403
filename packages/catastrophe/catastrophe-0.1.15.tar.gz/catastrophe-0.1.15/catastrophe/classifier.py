# destruction/classifier.py

from destruction.entropy import shannon_entropy

def classify_cipher(text: str) -> str:
    e = shannon_entropy(text)

    if e < 3.0:
        return "substitution (likely Caesar / Atbash)"
    if 3.0 <= e <= 4.5:
        return "polyalphabetic (Vigenere / Enigma)"
    if e > 4.8:
        return "XOR / random stream"

    return "unknown"
