#!/usr/bin/env python3
"""Merge markdown pattern cards into one markdown file.

Usage:
  merge_pattern_cards.py output.md card1.md card2.md ...
"""
from pathlib import Path
import sys
from datetime import date


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: merge_pattern_cards.py <output.md> <card1.md> [card2.md ...]")
        return 2
    output = Path(sys.argv[1])
    cards = [Path(p) for p in sys.argv[2:]]
    chunks = [f"# Merged Pattern Cards\n\nGenerated: {date.today().isoformat()}\n"]
    for card in cards:
        if not card.exists():
            print(f"Skip missing: {card}")
            continue
        chunks.append(f"\n---\n\n<!-- Source: {card} -->\n\n")
        chunks.append(card.read_text(encoding="utf-8", errors="ignore").strip())
        chunks.append("\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
