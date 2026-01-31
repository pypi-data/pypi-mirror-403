def playfair(text: str, key: str) -> str:
    key = "".join(dict.fromkeys(key.upper().replace("J","I")))
    alpha = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    square = key + "".join(c for c in alpha if c not in key)

    def pos(c): return divmod(square.index(c),5)

    text = "".join(c for c in text.upper() if c.isalpha()).replace("J","I")
    if len(text)%2: text += "X"

    res = []
    for i in range(0,len(text),2):
        a,b = text[i],text[i+1]
        ra,ca = pos(a)
        rb,cb = pos(b)
        if ra==rb:
            res+=square[ra*5+(ca+1)%5],square[rb*5+(cb+1)%5]
        elif ca==cb:
            res+=square[((ra+1)%5)*5+ca],square[((rb+1)%5)*5+cb]
        else:
            res+=square[ra*5+cb],square[rb*5+ca]
    return "".join(res)
