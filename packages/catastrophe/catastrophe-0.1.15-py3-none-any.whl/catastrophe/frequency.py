from __future__ import annotations

import string
from typing import Dict, Tuple

ALPHA = string.ascii_uppercase

def frequency(text: str, top: int = 26) -> Dict[str, float]:
    counts = {c: 0 for c in ALPHA}
    total = 0
    for ch in text.upper():
        if ch in counts:
            counts[ch] += 1
            total += 1
    if total == 0:
        return {c: 0.0 for c in ALPHA}
    freqs = {c: counts[c] / total for c in ALPHA}
    # return sorted dict by freq desc (regular dict preserves insertion order in py3.7+)
    items = sorted(freqs.items(), key=lambda kv: kv[1], reverse=True)[:top]
    return dict(items)

def frequency_ascii(text: str, width: int = 40) -> str:
    freqs = frequency(text, top=26)
    if not freqs:
        return ""
    maxv = max(freqs.values()) if freqs else 1.0
    lines = []
    for k, v in freqs.items():
        bar = int((v / maxv) * width) if maxv > 0 else 0
        lines.append(f"{k} {v:6.2%} | " + ("#" * bar))
    return "\n".join(lines)
