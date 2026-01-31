BACON = {
    chr(65 + i): format(i, "05b").replace("0", "A").replace("1", "B")
    for i in range(26)
}
INV = {v: k for k, v in BACON.items()}


def baconian(text: str) -> str:
    return " ".join(BACON[c.upper()] for c in text if c.isalpha())


def baconian_decode(code: str) -> str:
    return "".join(INV.get(b, "?") for b in code.split())
