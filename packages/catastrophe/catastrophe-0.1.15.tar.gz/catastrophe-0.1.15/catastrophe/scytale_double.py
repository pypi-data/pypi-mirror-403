def scytale_double(text: str, r1: int, r2: int) -> str:
    from destruction.scytale import scytale
    return scytale(scytale(text, r1), r2)
