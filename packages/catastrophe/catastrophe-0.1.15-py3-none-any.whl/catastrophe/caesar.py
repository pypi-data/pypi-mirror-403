def caesar(text: str, shift: int) -> str:
    """
    Apply a Caesar cipher to `text` with the given `shift`.
    Supports uppercase and lowercase letters. Other characters are unchanged.
    """
    result = []
    shift = shift % 26

    for ch in text:
        if "a" <= ch <= "z":
            result.append(
                chr((ord(ch) - ord("a") + shift) % 26 + ord("a"))
            )
        elif "A" <= ch <= "Z":
            result.append(
                chr((ord(ch) - ord("A") + shift) % 26 + ord("A"))
            )
        else:
            result.append(ch)

    return "".join(result)
