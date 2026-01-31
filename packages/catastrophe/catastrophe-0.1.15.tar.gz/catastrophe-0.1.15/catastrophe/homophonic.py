import random
import string

def homophonic(text: str, seed: int | None = None) -> str:
    rnd = random.Random(seed)
    mapping = {c: [f"{i}{j}" for j in range(3)] for i, c in enumerate(string.ascii_uppercase, 1)}

    out = []
    for ch in text.upper():
        if ch in mapping:
            out.append(rnd.choice(mapping[ch]))
        else:
            out.append(ch)
    return " ".join(out)
