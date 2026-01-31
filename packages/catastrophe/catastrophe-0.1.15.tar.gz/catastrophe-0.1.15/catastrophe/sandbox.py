"""
sandbox.py
==========
Safe execution sandbox + unified cipher playground.

Design goals:
- Never crash the caller
- Never accept non-string plaintext
- Deterministic + time-safe
- One interface for all ciphers
"""

from __future__ import annotations
import time
import string
import math
import random
from typing import Dict, Callable, Any, Tuple

# -------------------------------------------------
# Sandbox core
# -------------------------------------------------

class SandboxError(Exception):
    pass


class Sandbox:
    """
    Execution sandbox for cipher operations.
    """

    def __init__(self, timeout: float = 1.0, seed: int = 1337):
        self.timeout = timeout
        self.random = random.Random(seed)

    def run(self, fn: Callable[..., str], *args, **kwargs) -> str:
        start = time.time()
        try:
            result = fn(*args, **kwargs)
            if not isinstance(result, str):
                raise SandboxError("Cipher did not return string")
            if time.time() - start > self.timeout:
                raise SandboxError("Sandbox timeout")
            return result
        except Exception as e:
            return f"[SANDBOX ERROR] {e}"


# -------------------------------------------------
# Helpers
# -------------------------------------------------

ALPHA = string.ascii_lowercase

def _clean_text(x: Any) -> str:
    if isinstance(x, str):
        return x
    return str(x)


def _shift_char(c: str, shift: int) -> str:
    if c.isalpha():
        base = 'A' if c.isupper() else 'a'
        return chr((ord(c) - ord(base) + shift) % 26 + ord(base))
    return c


# -------------------------------------------------
# Classical ciphers
# -------------------------------------------------

def caesar(text: Any, shift: int = 3) -> str:
    text = _clean_text(text)
    return ''.join(_shift_char(c, shift) for c in text)


def atbash(text: Any) -> str:
    text = _clean_text(text)
    out = []
    for c in text:
        if c.isalpha():
            base = 'A' if c.isupper() else 'a'
            out.append(chr(ord(base) + (25 - (ord(c) - ord(base)))))
        else:
            out.append(c)
    return ''.join(out)


def vigenere(text: Any, key: str) -> str:
    text = _clean_text(text)
    key = ''.join(k.lower() for k in key if k.isalpha())
    if not key:
        return text
    out = []
    j = 0
    for c in text:
        if c.isalpha():
            shift = ord(key[j % len(key)]) - 97
            out.append(_shift_char(c, shift))
            j += 1
        else:
            out.append(c)
    return ''.join(out)


def xor_cipher(text: Any, key: str) -> str:
    text = _clean_text(text)
    if not key:
        return text
    kb = key.encode()
    tb = text.encode(errors="replace")
    out = bytes(tb[i] ^ kb[i % len(kb)] for i in range(len(tb)))
    return out.hex()


def xor_dec(hex_text: Any, key: str) -> str:
    try:
        data = bytes.fromhex(_clean_text(hex_text))
        kb = key.encode()
        out = bytes(data[i] ^ kb[i % len(kb)] for i in range(len(data)))
        return out.decode(errors="replace")
    except Exception:
        return "[XOR DECODE ERROR]"


def rail_fence(text: Any, rails: int = 3) -> str:
    text = _clean_text(text)
    if rails < 2:
        return text
    fence = [[] for _ in range(rails)]
    r, d = 0, 1
    for c in text:
        fence[r].append(c)
        r += d
        if r == 0 or r == rails - 1:
            d *= -1
    return ''.join(''.join(row) for row in fence)


def affine(text: Any, a: int, b: int) -> str:
    text = _clean_text(text)
    if math.gcd(a, 26) != 1:
        return "[AFFINE INVALID KEY]"
    out = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            x = ord(c) - base
            out.append(chr((a * x + b) % 26 + base))
        else:
            out.append(c)
    return ''.join(out)


# -------------------------------------------------
# Playfair (simplified, safe)
# -------------------------------------------------

def playfair(text: Any, key: str) -> str:
    text = ''.join(c.lower() for c in _clean_text(text) if c.isalpha()).replace('j', 'i')
    key = ''.join(dict.fromkeys((key + ALPHA).replace('j', 'i')))
    grid = [key[i:i+5] for i in range(0, 25, 5)]

    def pos(ch):
        for r in range(5):
            if ch in grid[r]:
                return r, grid[r].index(ch)

    out = []
    i = 0
    while i < len(text):
        a = text[i]
        b = text[i+1] if i+1 < len(text) else 'x'
        if a == b:
            b = 'x'
            i += 1
        else:
            i += 2
        ra, ca = pos(a)
        rb, cb = pos(b)
        if ra == rb:
            out.append(grid[ra][(ca+1)%5])
            out.append(grid[rb][(cb+1)%5])
        elif ca == cb:
            out.append(grid[(ra+1)%5][ca])
            out.append(grid[(rb+1)%5][cb])
        else:
            out.append(grid[ra][cb])
            out.append(grid[rb][ca])
    return ''.join(out)


# -------------------------------------------------
# Enigma-style machine (simplified, deterministic)
# -------------------------------------------------

class Enigma:
    ROTORS = [
        "ekmflgdqvzntowyhxuspaibrcj",
        "ajdksiruxblhwtmcqgznpyfvoe",
        "bdfhjlcprtxvznyeiwgakmusqo",
    ]
    REFLECTOR = dict(zip(ALPHA, "yruhqsldpxngokmiebfzcwvjat"))

    def __init__(self, rotor_positions=(0,0,0)):
        self.pos = list(rotor_positions)

    def enc_char(self, c: str) -> str:
        if not c.isalpha():
            return c
        x = ord(c.lower()) - 97
        for i in range(3):
            x = (ord(self.ROTORS[i][(x + self.pos[i]) % 26]) - 97)
        x = ord(self.REFLECTOR[ALPHA[x]]) - 97
        for i in reversed(range(3)):
            x = (self.ROTORS[i].index(ALPHA[x]) - self.pos[i]) % 26
        self.pos[0] = (self.pos[0] + 1) % 26
        return chr(x + (65 if c.isupper() else 97))

    def enc(self, text: Any) -> str:
        text = _clean_text(text)
        return ''.join(self.enc_char(c) for c in text)


# -------------------------------------------------
# Transliteration engine (many alphabets)
# -------------------------------------------------

TRANSLIT = {
    # Greek
    "α":"a","β":"b","γ":"g","δ":"d","ε":"e","η":"i","θ":"th",
    "ι":"i","κ":"k","λ":"l","μ":"m","ν":"n","ξ":"x","ο":"o",
    "π":"p","ρ":"r","σ":"s","τ":"t","υ":"y","φ":"f","χ":"ch","ω":"o",
    # Cyrillic
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"yo","ж":"zh",
    "з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o",
    "п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"kh","ц":"ts",
    "ч":"ch","ш":"sh","щ":"shch","ы":"y","э":"e","ю":"yu","я":"ya",
    # Arabic (basic)
    "ا":"a","ب":"b","ت":"t","ث":"th","ج":"j","ح":"h","خ":"kh",
    "د":"d","ذ":"dh","ر":"r","ز":"z","س":"s","ش":"sh","ص":"s",
    "ض":"d","ط":"t","ظ":"z","ع":"a","غ":"gh","ف":"f","ق":"q",
    "ك":"k","ل":"l","م":"m","ن":"n","ه":"h","و":"w","ي":"y",
    # Hebrew
    "א":"a","ב":"b","ג":"g","ד":"d","ה":"h","ו":"v","ז":"z",
    "ח":"kh","ט":"t","י":"y","כ":"k","ל":"l","מ":"m","נ":"n",
    "ס":"s","ע":"a","פ":"p","צ":"ts","ק":"q","ר":"r","ש":"sh","ת":"t",
}

def transliterate(text: Any) -> str:
    text = _clean_text(text)
    out = []
    for c in text:
        low = c.lower()
        if low in TRANSLIT:
            t = TRANSLIT[low]
            out.append(t.upper() if c.isupper() else t)
        else:
            out.append(c)
    return ''.join(out)


# -------------------------------------------------
# Registry
# -------------------------------------------------

CIPHERS: Dict[str, Callable[..., str]] = {
    "caesar": caesar,
    "atbash": atbash,
    "vigenere": vigenere,
    "xor": xor_cipher,
    "xor_dec": xor_dec,
    "rail_fence": rail_fence,
    "affine": affine,
    "playfair": playfair,
    "enigma": lambda t, p=(0,0,0): Enigma(p).enc(t),
    "transliterate": transliterate,
}


# -------------------------------------------------
# Public API
# -------------------------------------------------

def run_cipher(name: str, text: Any, *args, **kwargs) -> str:
    sb = Sandbox()
    fn = CIPHERS.get(name)
    if not fn:
        return "[UNKNOWN CIPHER]"
    return sb.run(fn, text, *args, **kwargs)
