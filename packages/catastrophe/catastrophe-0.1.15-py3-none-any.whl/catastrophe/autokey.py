def autokey(text: str, key: str) -> str:
    if not key:
        raise ValueError("key must be non-empty")
    key = "".join(c for c in key.upper() if c.isalpha())
    if not key:
        raise ValueError("key must contain letters A-Z")

    plaintext_letters = [c.upper() for c in text if c.isalpha()]
    stream = (key + "".join(plaintext_letters))  # autokey extends with plaintext

    out = []
    si = 0
    for ch in text:
        if ch.isalpha():
            base = 65 if ch.isupper() else 97
            p = ord(ch.upper()) - 65
            k = ord(stream[si]) - 65
            c = (p + k) % 26
            out.append(chr(c + base))
            si += 1
        else:
            out.append(ch)
    return "".join(out)
