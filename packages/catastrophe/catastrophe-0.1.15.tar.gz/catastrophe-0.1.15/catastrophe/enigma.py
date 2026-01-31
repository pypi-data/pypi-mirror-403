from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

ALPHA = string.ascii_uppercase

# Enigma I rotors (wiring + notch position)
ROTORS: Dict[str, Tuple[str, str]] = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV":  ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V":   ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}

REFLECTORS: Dict[str, str] = {
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL",
}

def _idx(c: str) -> int:
    return ord(c) - 65

def _ch(i: int) -> str:
    return chr((i % 26) + 65)

def _clean_plugboard(pairs: str | None) -> Dict[str, str]:
    """
    pairs like: "AB CD EF" or "ABCD" (interpreted as AB CD)
    """
    mapping = {c: c for c in ALPHA}
    if not pairs:
        return mapping

    s = pairs.replace(" ", "").upper()
    if len(s) % 2 != 0:
        raise ValueError("plugboard pairs length must be even (e.g., 'AB CD EF')")

    used = set()
    for i in range(0, len(s), 2):
        a, b = s[i], s[i + 1]
        if a not in ALPHA or b not in ALPHA:
            raise ValueError("plugboard pairs must be A-Z only")
        if a == b:
            raise ValueError("plugboard cannot map a letter to itself")
        if a in used or b in used:
            raise ValueError("plugboard letter reused")
        used.add(a); used.add(b)
        mapping[a] = b
        mapping[b] = a
    return mapping

@dataclass
class Rotor:
    wiring: str
    notch: str
    pos: int = 0          # 0..25 (window letter)
    ring: int = 0         # 0..25 (ringstellung)

    def at_notch(self) -> bool:
        # notch is based on window letter; ring affects effective notch position
        # effective window letter is pos; notch triggers when window shows notch letter
        return _ch(self.pos) == self.notch

    def forward(self, c: str) -> str:
        # Apply position and ring offset
        i = (_idx(c) + self.pos - self.ring) % 26
        wired = self.wiring[i]
        o = (_idx(wired) - self.pos + self.ring) % 26
        return _ch(o)

    def backward(self, c: str) -> str:
        i = (_idx(c) + self.pos - self.ring) % 26
        wired_index = self.wiring.index(_ch(i))
        o = (wired_index - self.pos + self.ring) % 26
        return _ch(o)

def _parse_positions(positions: Iterable[int | str]) -> Tuple[int, int, int]:
    p = []
    for x in positions:
        if isinstance(x, int):
            p.append(x % 26)
        else:
            x = x.strip().upper()
            if len(x) != 1 or x not in ALPHA:
                raise ValueError("positions letters must be A-Z")
            p.append(_idx(x))
    if len(p) != 3:
        raise ValueError("positions must have exactly 3 values")
    return (p[0], p[1], p[2])

def _parse_rings(rings: Iterable[int | str]) -> Tuple[int, int, int]:
    r = []
    for x in rings:
        if isinstance(x, int):
            r.append(x % 26)
        else:
            x = x.strip().upper()
            if len(x) != 1 or x not in ALPHA:
                raise ValueError("rings letters must be A-Z")
            r.append(_idx(x))
    if len(r) != 3:
        raise ValueError("rings must have exactly 3 values")
    return (r[0], r[1], r[2])

def enigma(
    text: str,
    rotors: Tuple[str, str, str] = ("I", "II", "III"),
    reflector: str = "B",
    positions: Tuple[int | str, int | str, int | str] = (0, 0, 0),
    rings: Tuple[int | str, int | str, int | str] = (0, 0, 0),
    plugboard: str | None = None,
) -> str:
    """
    Enigma I (3-rotor) with:
      - real rotor wirings + notches
      - proper double-stepping
      - ring settings
      - reflector B/C
      - plugboard swaps

    Encrypt/decrypt are the same function with same settings.
    """

    if reflector not in REFLECTORS:
        raise ValueError("reflector must be 'B' or 'C'")

    for r in rotors:
        if r not in ROTORS:
            raise ValueError(f"unknown rotor '{r}'")

    p0, p1, p2 = _parse_positions(positions)
    r0, r1, r2 = _parse_rings(rings)

    left  = Rotor(*ROTORS[rotors[0]], pos=p0, ring=r0)
    mid   = Rotor(*ROTORS[rotors[1]], pos=p1, ring=r1)
    right = Rotor(*ROTORS[rotors[2]], pos=p2, ring=r2)

    pb = _clean_plugboard(plugboard)
    ref = REFLECTORS[reflector]

    out = []
    for ch in text.upper():
        if ch not in ALPHA:
            out.append(ch)
            continue

        # --- stepping (double-step behavior) ---
        # If middle at notch -> middle and left step
        if mid.at_notch():
            left.pos = (left.pos + 1) % 26
            mid.pos = (mid.pos + 1) % 26
        # If right at notch -> middle steps
        elif right.at_notch():
            mid.pos = (mid.pos + 1) % 26
        # Right always steps
        right.pos = (right.pos + 1) % 26

        # --- plugboard in ---
        c = pb[ch]

        # --- through rotors forward (right -> left) ---
        c = right.forward(c)
        c = mid.forward(c)
        c = left.forward(c)

        # --- reflector ---
        c = ref[_idx(c)]

        # --- back through rotors (left -> right) ---
        c = left.backward(c)
        c = mid.backward(c)
        c = right.backward(c)

        # --- plugboard out ---
        c = pb[c]

        out.append(c)

    return "".join(out)
