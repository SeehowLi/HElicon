#!/usr/bin/env python3
"""Flag legacy Chinese-literal phrasing and sentence-level overclaims.

This script owns no numbered P5 rule. Rules 1-14, including all vocabulary
formerly duplicated here, belong to references/language_polish.md and are
implemented by check_ai_tells.py.
"""
from pathlib import Path
import re
import sys

PATTERNS = {
    r"\bunder the background of\b": "Prefer a direct causal or contextual statement.",
    r"\bin the aspect of\b": "Prefer in, for, regarding, or a precise technical relation.",
    r"\bwith the rapid development of\b": "State the concrete change that motivates the work.",
    r"\baccording to the above analysis\b": "Name the result or inference being used.",
    r"\bthe experiment result shows\b": "Use the experimental results show or name the measured result.",
    r"\bcompletely (?:solves?|eliminates?|prevents?)\b": "Scope the claim and identify residual limitations.",
    r"\bguarantees? (?:absolute|perfect) (?:privacy|security)\b": "Tie the guarantee to a formal model; absolute claims are usually invalid.",
    r"\bproves? that\b[^.!?]{0,100}\bis (?:secure|correct|optimal)\b": "Use proves only when a cited theorem establishes the exact property.",
}


def check(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    count = 0
    for pattern, msg in PATTERNS.items():
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
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
