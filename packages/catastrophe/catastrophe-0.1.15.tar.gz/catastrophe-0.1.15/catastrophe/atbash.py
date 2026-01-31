def atbash(text: str) -> str:
    result = []
    for ch in text:
        if ch.islower():
            result.append(chr(122 - (ord(ch) - 97)))
        elif ch.isupper():
            result.append(chr(90 - (ord(ch) - 65)))
        else:
            result.append(ch)
    return "".join(result)
