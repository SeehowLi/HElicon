#!/usr/bin/env python3
"""Flag common literal or overclaiming expressions in paper drafts.

This is intentionally conservative. It does not judge correctness; it only surfaces phrases HElicon should review.
"""
from pathlib import Path
import re
import sys

PHRASES = {
    "technical packaging": "Prefer technical framing / contribution framing / positioning.",
    "large model privacy inference": "Prefer privacy-preserving LLM inference or private inference for large language models.",
    "homomorphic realization": "Prefer FHE-based <task>, encrypted <task>, or homomorphic <task> evaluation.",
    "full homomorphic encryption": "Prefer fully homomorphic encryption.",
    "significantly": "Check whether a quantified result immediately supports this word.",
    "dramatically": "Likely overclaim unless strongly quantified.",
    "secure and efficient": "Check whether threat model and metrics are specific.",
    "practical": "Scope practicality to workload, hardware, parameters, and baseline.",
    "scalable": "State the scaling dimension and evidence.",
}


def check(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    count = 0
    for phrase, msg in PHRASES.items():
        for m in re.finditer(re.escape(phrase), text, flags=re.IGNORECASE):
            line_no = text.count("\n", 0, m.start()) + 1
            print(f"{path}:{line_no}: '{m.group(0)}' -> {msg}")
            count += 1
    return count


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: check_style_rules.py <file-or-directory> [...]")
        return 2
    total = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            for child in p.rglob("*"):
                if child.suffix.lower() in {".tex", ".md", ".txt"}:
                    total += check(child)
        elif p.exists():
            total += check(p)
    print(f"Warnings: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
