import base64

def b64encode(text: str) -> str:
    return base64.b64encode(text.encode()).decode()

def b64decode(text: str) -> str:
    return base64.b64decode(text.encode()).decode(errors="ignore")
