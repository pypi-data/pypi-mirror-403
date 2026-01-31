MORSE = {
    "A": ".-","B": "-...","C": "-.-.","D": "-..","E": ".","F": "..-.","G": "--.",
    "H": "....","I": "..","J": ".---","K": "-.-","L": ".-..","M": "--","N": "-.",
    "O": "---","P": ".--.","Q": "--.-","R": ".-.","S": "...","T": "-","U": "..-",
    "V": "...-","W": ".--","X": "-..-","Y": "-.--","Z": "--..",
    "0": "-----","1": ".----","2": "..---","3": "...--","4": "....-",
    "5": ".....","6": "-....","7": "--...","8": "---..","9": "----.",
    ".": ".-.-.-",",": "--..--","?": "..--..","!": "-.-.--",":": "---...",
    ";": "-.-.-.","(": "-.--.",")": "-.--.-","/": "-..-.","-": "-....-",
    "'": ".----.","\"": ".-..-.","@": ".--.-.","=": "-...-","+": ".-.-.",
}

REV = {v: k for k, v in MORSE.items()}

def morse(text: str) -> str:
    # encode
    parts = []
    for ch in text.upper():
        if ch == " ":
            parts.append("/")  # word separator
        elif ch in MORSE:
            parts.append(MORSE[ch])
        else:
            parts.append("?")
    return " ".join(parts)

def morse_decode(code: str) -> str:
    # decode: letters separated by spaces, words by /
    out = []
    for token in code.split():
        if token == "/":
            out.append(" ")
        else:
            out.append(REV.get(token, "?"))
    return "".join(out)
