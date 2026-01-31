import string

def keyword(text: str, key: str) -> str:
    alpha = string.ascii_uppercase
    key = "".join(dict.fromkeys(c for c in key.upper() if c.isalpha()))
    subst = key + "".join(c for c in alpha if c not in key)
    table = {alpha[i]: subst[i] for i in range(26)}

    out = []
    for ch in text:
        if ch.isalpha():
            out.append(table[ch.upper()] if ch.isupper() else table[ch.upper()].lower())
        else:
            out.append(ch)
    return "".join(out)
