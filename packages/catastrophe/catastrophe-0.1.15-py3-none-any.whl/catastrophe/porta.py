def porta(text: str, key: str) -> str:
    if not key:
        raise ValueError("key must be non-empty")
    key = "".join(c for c in key.upper() if c.isalpha())
    if not key:
        raise ValueError("key must contain letters A-Z")

    out = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            p = ord(ch.upper()) - 65
            k = ord(key[ki % len(key)]) - 65
            # Porta uses 13 paired alphabets (A/B=0, C/D=1, ...)
            group = k // 2
            if p < 13:
                c = (p + group) % 13 + 13
            else:
                c = (p - 13 - group) % 13
            out.append(chr(c + (65 if ch.isupper() else 97)))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)
