"""
tester.py
=========
Self-test runner for destruction package.

- Tests every known cipher/module
- Continues after failures
- Prints errors + reasons
- Never crashes
"""

from __future__ import annotations

import traceback
import importlib
from typing import Any, Callable, Dict, List, Tuple


# -------------------------------------------------
# Utilities
# -------------------------------------------------

def _safe_call(fn: Callable, *args, **kwargs) -> Tuple[bool, str]:
    try:
        result = fn(*args, **kwargs)
        if not isinstance(result, str):
            return False, f"Returned non-string type: {type(result)}"
        return True, result
    except Exception as e:
        return False, f"{e.__class__.__name__}: {e}"


# -------------------------------------------------
# Test definitions
# -------------------------------------------------

TESTS: Dict[str, Tuple[str, tuple]] = {
    # simple ciphers
    "atbash": ("atbash", ("hello",)),
    "caesar": ("caesar", ("hello", 3)),
    "rot13": ("caesar", ("hello", 13)),
    "vigenere": ("vigenere", ("attack at dawn", "lemon")),

    # transposition / algebraic
    "rail_fence": ("rail_fence", ("WEAREDISCOVERED", 3)),
    "affine": ("affine", ("hello", 5, 8)),
    "playfair": ("playfair", ("hide the gold", "monarchy")),

    # binary / modern
    "xor": ("xor_cipher", ("hello", "key")),
    "xor_dec": ("xor_dec", ("68656c6c6f", "key")),

    # enigma
    "enigma": ("enigma", ("HELLO", (1, 2, 3))),

    # transliteration
    "transliterate": ("transliterate", ("Καλημέρα κόσμε",)),

    # sandbox
    "sandbox": ("run_cipher", ("atbash", "hello")),
}


# -------------------------------------------------
# Tester
# -------------------------------------------------

def tester() -> None:
    print("=" * 60)
    print("DESTRUCTION SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    try:
        sandbox = importlib.import_module("destruction.sandbox")
    except Exception as e:
        print("[FATAL] Could not import sandbox:", e)
        return

    for label, (fn_name, args) in TESTS.items():
        print(f"\n[Test] {label}")

        try:
            # resolve function
            if fn_name == "run_cipher":
                fn = sandbox.run_cipher
            else:
                fn = getattr(sandbox, fn_name)

            ok, info = _safe_call(fn, *args)

            if ok:
                print("  ✔ PASS")
                print("    Output:", info[:120])
                passed += 1
            else:
                print("  ✖ FAIL")
                print("    Reason:", info)
                failed += 1

        except Exception as e:
            print("  ✖ ERROR")
            print("    Exception:", e)
            print("    Traceback:")
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)


# -------------------------------------------------
# Allow destruction.tester() directly
# -------------------------------------------------

__all__ = ["tester"]
