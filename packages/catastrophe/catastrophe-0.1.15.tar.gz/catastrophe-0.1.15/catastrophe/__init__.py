from __future__ import annotations

__version__ = "0.1.15"

import importlib
import pkgutil
import sys
from typing import List
from destruction.scorer import score_text

# ---- automatic discovery of public submodules ----

def _discover_public_modules() -> List[str]:
    names: List[str] = []
    for m in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
        if not m.name.startswith("_"):
            names.append(m.name)
    return names


__all__ = _discover_public_modules()

# ---- editor support ----

def __dir__():
    return sorted(__all__)

# ---- lazy loading + callable modules (FIXED) ----
def __getattr__(name):
    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    # Case 1: callable command (preferred)
    attr = getattr(module, name, None)
    if callable(attr):
        setattr(sys.modules[__name__], name, attr)
        return attr

    # Case 2: value-style export (string, int, etc.)
    if name in module.__dict__:
        value = module.__dict__[name]
        setattr(sys.modules[__name__], name, value)
        return value

    # Case 3: expose module ONLY (no caching!)
    return module
