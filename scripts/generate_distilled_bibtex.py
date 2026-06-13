#!/usr/bin/env python3
"""Generate BibTeX provenance for papers distilled into HElicon cards."""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:60] or "paper"


def bib_escape(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("&", "\\&")
    )


def parse_notes(notes: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for chunk in notes.split(";"):
        chunk = chunk.strip()
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def load_canonical_titles(audit_csv: Path) -> set[str]:
    if not audit_csv.exists():
        return set()
    titles: set[str] = set()
    with audit_csv.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row.get("action") == "KEEP_CANONICAL":
                title = (row.get("inferred_title") or "").strip()
                if title:
                    titles.add(title)
    return titles


def entry_type(venue: str) -> str:
    low = venue.lower()
    if "journal" in low or "transactions" in low or "access" in low:
        return "article"
    if any(token in low for token in ["crypto", "eurocrypt", "asiacrypt", "ccs", "ndss", "usenix", "ieee s&p", "sac", "ct-rsa", "wacv", "wahc"]):
        return "inproceedings"
    return "misc"


def bib_entry(row: dict[str, str], index: int) -> str:
    title = row["title"].strip()
    year = row["year"].strip()
    venue = row["venue"].strip()
    notes = parse_notes(row.get("notes", ""))
    key = f"helicon-{year}-{slug(title)}"

    fields: list[tuple[str, str]] = [
        ("title", title),
        ("year", year),
    ]

    typ = entry_type(venue)
    if typ == "article":
        fields.append(("journal", venue))
    elif typ == "inproceedings":
        fields.append(("booktitle", venue))
    else:
        fields.append(("howpublished", venue))

    if notes.get("doi"):
        fields.append(("doi", notes["doi"]))
    if notes.get("arxiv"):
        fields.append(("eprint", notes["arxiv"]))
        fields.append(("archivePrefix", "arXiv"))
    elif notes.get("eprint") or notes.get("also_eprint"):
        fields.append(("eprint", notes.get("eprint") or notes.get("also_eprint", "")))
        fields.append(("archivePrefix", "IACR Cryptology ePrint Archive"))

    direction = row.get("primary_direction", "").strip()
    secondary = row.get("secondary_directions", "").strip()
    note_parts = ["Distilled source for HElicon"]
    if direction:
        note_parts.append(f"primary direction: {direction}")
    if secondary:
        note_parts.append(f"secondary directions: {secondary}")
    fields.append(("note", "; ".join(note_parts)))

    lines = [f"@{typ}{{{key},"]
    for field, value in fields:
        if value:
            lines.append(f"  {field} = {{{bib_escape(value)}}},")
    lines.append(f"  heliconIndex = {{{index:03d}}}")
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    canonical_titles = load_canonical_titles(args.audit)
    rows: list[dict[str, str]] = []
    with args.registry.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row.get("status") != "card_created":
                continue
            title = (row.get("title") or "").strip()
            if canonical_titles and title not in canonical_titles:
                continue
            rows.append(row)

    rows.sort(key=lambda r: ((r.get("year") or ""), (r.get("title") or "").lower()))

    header = [
        "% HElicon distilled source bibliography.",
        "% Generated from HElicon_workspace/distilled/paper_registry.csv",
        "% and HElicon_workspace/distilled/paper_card_audit.csv.",
        "% These entries identify source papers for distilled writing patterns.",
        "% They are not HElicon core memory and do not contain paper-card content.",
        "",
    ]
    body = [bib_entry(row, i) for i, row in enumerate(rows, start=1)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(header) + "\n\n" + "\n\n".join(body) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
