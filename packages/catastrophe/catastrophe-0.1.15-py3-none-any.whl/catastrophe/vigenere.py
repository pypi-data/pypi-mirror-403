def vigenere(text: str, key: str, decrypt: bool = False) -> str:
    """
    Vigenère cipher.
    Set decrypt=True to decrypt.
    """
    result = []
    key = [ord(c.lower()) - 97 for c in key if c.isalpha()]
    if not key:
        raise ValueError("Key must contain letters")

    ki = 0
    for ch in text:
        if ch.isalpha():
            base = 97 if ch.islower() else 65
            shift = key[ki % len(key)]
            if decrypt:
                shift = -shift
            result.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)

    return "".join(result)
