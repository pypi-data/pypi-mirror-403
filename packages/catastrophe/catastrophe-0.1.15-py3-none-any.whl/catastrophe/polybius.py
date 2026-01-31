SQUARE = "ABCDEFGHIKLMNOPQRSTUVWXYZ"  # J merged into I

def polybius(text: str) -> str:
    # encode: A=11, B=12 ... (row,col) in 5x5
    out = []
    for ch in text.upper():
        if ch.isalpha():
            ch = "I" if ch == "J" else ch
            idx = SQUARE.index(ch)
            r, c = divmod(idx, 5)
            out.append(f"{r+1}{c+1}")
        elif ch == " ":
            out.append("/")
        else:
            out.append(ch)
    return " ".join(out)

def polybius_decode(code: str) -> str:
    out = []
    for tok in code.split():
        if tok == "/":
            out.append(" ")
        elif len(tok) == 2 and tok.isdigit():
            r = int(tok[0]) - 1
            c = int(tok[1]) - 1
            if 0 <= r < 5 and 0 <= c < 5:
                out.append(SQUARE[r * 5 + c])
            else:
                out.append("?")
        else:
            out.append(tok)
    return "".join(out)
