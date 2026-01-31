import string

ALPHA = string.ascii_uppercase

def polyalphabetic(text: str, key: str, decrypt: bool = False) -> str:
    if not key:
        raise ValueError("key must not be empty")

    key = [ALPHA.index(c) for c in key.upper() if c.isalpha()]
    if not key:
        raise ValueError("key must contain letters")

    out = []
    ki = 0

    for ch in text:
        if ch.isalpha():
            shift = key[ki % len(key)]
            if decrypt:
                shift = -shift
            base = ord("A") if ch.isupper() else ord("a")
            out.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            out.append(ch)

    return "".join(out)
