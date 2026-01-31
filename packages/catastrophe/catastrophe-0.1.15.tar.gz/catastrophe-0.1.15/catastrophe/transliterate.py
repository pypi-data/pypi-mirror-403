# destruction/transliterate.py

from __future__ import annotations
from destruction.translit_maps import *
from destruction.sandbox import sandbox_call

# ---- script detection ----

def detect_script(ch: str) -> str | None:
    o = ord(ch)
    if 0x0370 <= o <= 0x03FF: return "greek"
    if 0x0400 <= o <= 0x04FF: return "cyrillic"
    if 0x0600 <= o <= 0x06FF: return "arabic"
    if 0x0590 <= o <= 0x05FF: return "hebrew"
    if 0x0900 <= o <= 0x097F: return "devanagari"
    if 0x0250 <= o <= 0x02AF: return "ipa"
    if 0x4E00 <= o <= 0x9FFF: return "chinese"
    return None

# ---- hangul decomposition ----

def hangul_decompose(ch):
    BASE = ord(ch) - 0xAC00
    if BASE < 0 or BASE > 11171:
        return ch
    L = BASE // 588
    V = (BASE % 588) // 28
    T = BASE % 28
    return f"{chr(0x1100+L)}{chr(0x1161+V)}"

# ---- main transliterator ----

def transliterate(text: str, reverse: bool = False) -> str:
    out = []
    for ch in text:
        script = detect_script(ch)
        if script == "chinese":
            out.append(CHINESE_FALLBACK(ch))
        elif script == "hangul":
            out.append(hangul_decompose(ch))
        elif script and script in SCRIPTS:
            out.append(SCRIPTS[script].get(ch.lower(), ch))
        else:
            out.append(ch)
    return "".join(out)

# ---- callable safety ----
transliterate.__call__ = transliterate

# ---- sandbox wrapper ----
def safe(text: str):
    return sandbox_call(transliterate, text)
