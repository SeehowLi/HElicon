#!/usr/bin/env python3
"""Fail closed when mandatory mechanical-verification wiring drifts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ANCHOR_SELECTORS = (
    ("contract_heading", "references/pass_pipeline.md", ("### Mechanical verification contract",)),
    ("pass_scope_call", "references/pass_pipeline.md", ("scripts/check_pass_scope.py", "--pass <P3|P4|P5|P6|P7>")),
    ("p3_domain", "references/pass_pipeline.md", ("For P3 only,", "glossary_terms", "authorized output domain")),
    ("claim_strength_call", "references/pass_pipeline.md", ("scripts/check_claim_strength.py",)),
    ("terminology_call", "references/pass_pipeline.md", ("scripts/check_terminology_freeze.py",)),
    ("ai_tells_call", "references/pass_pipeline.md", ("scripts/check_ai_tells.py",)),
    ("skill_delivery", "SKILL.md", ("Before delivering", "Mechanical verification contract")),
)
WIRING_ANCHOR_SHA256 = {
    "contract_heading": "8aa70f5974f2ec908fcf1c1b80cda642233b8eb62095706dca2aa9da526f6575",
    "pass_scope_call": "faf2694e08cc0eaa9e9ea5aa0d8c2d7cfa3cc06255be2e4fa46f3573206840a6",
    "p3_domain": "9aa07f3e1489657c5503a1f63ab67e0332b6d543ffe3448b0d22c416a60f1eea",
    "claim_strength_call": "a5de6fd042273c3b3edbc5ddca5c04030dfae058ceccbf54584f9f6af9ecf88d",
    "terminology_call": "63575bd04c8f4ebcd4d9527aaae09d1d18c9cd68d39c7befd74ea0d4eb74b3c9",
    "ai_tells_call": "b4c5b3bfaf5e919dc18f6406ef892ce082fb337b2706f0619974e1ea132a65ae",
    "skill_delivery": "d654504ace25d968b1375ea48264d3af705d95e4e4c09a301ffd3ea5929c9739",
}
WIRING_ANCHOR_COUNT = 7
WIRING_ANCHOR_MANIFEST_SHA256 = "0c05adf3d1602f356a08fbffac4996d9688305dc505f80b747827886b3464ebb"


class WiringError(Exception):
    """A deterministic wiring or configuration failure."""


def canonical_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def anchor_manifest(values: dict[str, str]) -> str:
    payload = "".join(f"{name}:{values[name]}\n" for name in sorted(values))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def validate_anchor_config(
    values: dict[str, str] = WIRING_ANCHOR_SHA256,
    expected_count: int = WIRING_ANCHOR_COUNT,
    expected_manifest: str = WIRING_ANCHOR_MANIFEST_SHA256,
) -> None:
    if len(values) != expected_count or len(set(values.values())) != expected_count:
        raise WiringError("wiring anchor count mismatch")
    if any(re.fullmatch(r"[0-9a-f]{64}", digest) is None for digest in values.values()):
        raise WiringError("wiring anchor digest format mismatch")
    if anchor_manifest(values) != expected_manifest:
        raise WiringError("wiring anchor manifest mismatch")


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except (FileNotFoundError, UnicodeDecodeError, OSError) as exc:
        raise WiringError(f"cannot read wiring source: {path}") from exc


def extract_anchor_digests(texts: dict[str, str]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, relative, fragments in ANCHOR_SELECTORS:
        matches = [
            canonical_line(line)
            for line in texts[relative].splitlines()
            if all(fragment in line for fragment in fragments)
        ]
        if len(matches) != 1:
            raise WiringError(f"wiring anchor missing or ambiguous: {name}")
        observed[name] = hashlib.sha256(matches[0].encode("utf-8")).hexdigest()
    return observed


def validate_texts(skill_text: str, pipeline_text: str) -> dict[str, Any]:
    validate_anchor_config()
    observed = extract_anchor_digests({
        "SKILL.md": skill_text,
        "references/pass_pipeline.md": pipeline_text,
    })
    drifted = sorted(
        name for name, digest in observed.items()
        if digest != WIRING_ANCHOR_SHA256[name]
    )
    return {
        "schema": "helicon-wiring-integrity-v1",
        "passed": not drifted,
        "anchor_count": len(observed),
        "anchor_manifest_sha256": anchor_manifest(observed),
        "drifted_anchors": drifted,
        "errors": [f"wiring anchor drift: {name}" for name in drifted],
    }


def validate(root: Path) -> dict[str, Any]:
    return validate_texts(
        read_utf8(root / "SKILL.md"),
        read_utf8(root / "references/pass_pipeline.md"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    try:
        result = validate(Path(args.root))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["passed"] else 1
    except (WiringError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({
            "schema": "helicon-wiring-integrity-v1",
            "passed": False,
            "error": str(exc),
        }, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
