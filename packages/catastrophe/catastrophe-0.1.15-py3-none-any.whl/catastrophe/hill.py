def hill(text: str, key: tuple[int,int,int,int]) -> str:
    a,b,c,d = key
    res = []
    text = "".join(c for c in text.upper() if c.isalpha())
    if len(text)%2: text+="X"
    for i in range(0,len(text),2):
        x,y = ord(text[i])-65, ord(text[i+1])-65
        res.append(chr((a*x+b*y)%26+65))
        res.append(chr((c*x+d*y)%26+65))
    return "".join(res)
