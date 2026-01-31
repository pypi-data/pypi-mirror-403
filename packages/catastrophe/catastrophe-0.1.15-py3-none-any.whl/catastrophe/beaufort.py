def beaufort(text: str, key: str) -> str:
    if not key:
        raise ValueError("key must be non-empty")
    key = "".join(c for c in key.upper() if c.isalpha())
    if not key:
        raise ValueError("key must contain letters A-Z")

    out = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            base = 65 if ch.isupper() else 97
            t = ord(ch.upper()) - 65
            k = ord(key[ki % len(key)]) - 65
            # Beaufort: C = K - P (mod 26)
            c = (k - t) % 26
            out.append(chr(c + base))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)
