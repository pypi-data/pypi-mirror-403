def rot13(text: str) -> str:
    """
    ROT13 cipher (Caesar shift of 13).
    """
    result = []

    for ch in text:
        if "a" <= ch <= "z":
            result.append(chr((ord(ch) - 97 + 13) % 26 + 97))
        elif "A" <= ch <= "Z":
            result.append(chr((ord(ch) - 65 + 13) % 26 + 65))
        else:
            result.append(ch)

    return "".join(result)
