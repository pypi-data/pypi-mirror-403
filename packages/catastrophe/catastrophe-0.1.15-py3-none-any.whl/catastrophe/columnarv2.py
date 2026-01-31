def columnar(text: str, key: str) -> str:
    order = sorted(range(len(key)), key=lambda i: key[i])
    cols = [""] * len(key)
    for i, ch in enumerate(text):
        cols[i % len(key)] += ch
    return "".join(cols[i] for i in order)
