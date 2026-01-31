from __future__ import annotations

import argparse
import json
import destruction as d

def main():
    p = argparse.ArgumentParser(prog="destruction", description="destruction crypto toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_auto = sub.add_parser("auto", help="auto-detect/decrypt common ciphers")
    p_auto.add_argument("text")
    p_auto.add_argument("--top", type=int, default=5)

    p_freq = sub.add_parser("freq", help="frequency analysis (ASCII)")
    p_freq.add_argument("text")

    p_enigma = sub.add_parser("enigma", help="Enigma I (3 rotors) with plugboard")
    p_enigma.add_argument("text")
    p_enigma.add_argument("--rotors", nargs=3, default=["I","II","III"])
    p_enigma.add_argument("--reflector", default="B")
    p_enigma.add_argument("--pos", nargs=3, default=["A","A","A"])
    p_enigma.add_argument("--rings", nargs=3, default=["A","A","A"])
    p_enigma.add_argument("--plug", default=None)

    args = p.parse_args()

    if args.cmd == "auto":
        print(json.dumps(d.auto(args.text, top=args.top), indent=2, ensure_ascii=False))
    elif args.cmd == "freq":
        print(d.frequency_ascii(args.text))
    elif args.cmd == "enigma":
        print(d.enigma(
            args.text,
            rotors=tuple(args.rotors),
            reflector=args.reflector,
            positions=tuple(args.pos),
            rings=tuple(args.rings),
            plugboard=args.plug,
        ))

if __name__ == "__main__":
    main()
