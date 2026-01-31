from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

def _safe_score(text: str) -> float:
    # Prefer your existing wordscore if you have it
    try:
        from destruction.wordscore import score_text  # type: ignore
        return float(score_text(text))
    except Exception:
        # fallback heuristic: more letters/spaces and fewer weird symbols
        letters = sum(c.isalpha() for c in text)
        spaces = text.count(" ")
        weird = sum(bool(re.match(r"[^a-zA-Z0-9\s\.\,\!\?\-']", c)) for c in text)
        return letters * 1.0 + spaces * 0.2 - weird * 0.7

def _try(name: str, fn, *args, **kwargs):
    try:
        out = fn(*args, **kwargs)
        return (name, out, _safe_score(out))
    except Exception:
        return None

def auto(text: str, top: int = 5) -> List[Dict[str, Any]]:
    """
    Returns top candidates:
      [{cipher:..., score:..., output:..., meta:{...}}, ...]
    """
    candidates: List[Tuple[str, str, float, Dict[str, Any]]] = []

    # atbash
    try:
        from destruction.atbash import atbash
        r = _try("atbash", atbash, text)
        if r: candidates.append((r[0], r[1], r[2], {}))
    except Exception:
        pass

    # rot13
    try:
        from destruction.rot13 import rot13
        r = _try("rot13", rot13, text)
        if r: candidates.append((r[0], r[1], r[2], {}))
    except Exception:
        pass

    # caesar brute 0..25 (use your caesar)
    try:
        from destruction.caesar import caesar
        for s in range(26):
            r = _try(f"caesar({s})", caesar, text, s)
            if r: candidates.append((r[0], r[1], r[2], {"shift": s}))
    except Exception:
        pass

    # morse decode if it looks like morse
    if set(text.strip()) <= set(".-/ \n\t"):
        try:
            from destruction.morse import morse_decode
            r = _try("morse_decode", morse_decode, text)
            if r: candidates.append((r[0], r[1], r[2], {}))
        except Exception:
            pass

    # polybius decode if it looks like digits pairs
    if re.fullmatch(r"[\d\s/]+", text.strip() or "X"):
        try:
            from destruction.polybius import polybius_decode
            r = _try("polybius_decode", polybius_decode, text)
            if r: candidates.append((r[0], r[1], r[2], {}))
        except Exception:
            pass

    # Sort best score first
    candidates.sort(key=lambda x: x[2], reverse=True)
    out = []
    for cipher, s, score, meta in candidates[:top]:
        out.append({"cipher": cipher, "score": score, "output": s, "meta": meta})
    return out
