def affine(text: str, a: int, b: int) -> str:
    if a % 2 == 0 or a % 13 == 0:
        raise ValueError("a must be coprime with 26")
    res = []
    for c in text:
        if c.isalpha():
            base = 97 if c.islower() else 65
            res.append(chr((a*(ord(c)-base)+b)%26 + base))
        else:
            res.append(c)
    return "".join(res)
