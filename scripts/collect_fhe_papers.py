#!/usr/bin/env python3
"""Collect FHE/HE paper metadata and open PDFs for HElicon distillation.

This script is conservative: it records metadata placeholders when a public PDF
is not directly available and never attempts to bypass access controls.
"""
from __future__ import annotations

import argparse
import csv
import re
import socket
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


KEYWORDS = [
    "fully homomorphic",
    "homomorphic encryption",
    "fhe",
    "ckks",
    "bfv",
    "bgv",
    "bootstrapping",
    "encrypted computation",
]

VENUE_URLS: dict[str, dict[int, list[str]]] = {
    "usenix_security": {
        2023: ["https://www.usenix.org/conference/usenixsecurity23/technical-sessions"],
        2024: ["https://www.usenix.org/conference/usenixsecurity24/technical-sessions"],
        2025: ["https://www.usenix.org/conference/usenixsecurity25/technical-sessions"],
        2026: ["https://www.usenix.org/conference/usenixsecurity26/technical-sessions"],
    },
    "ndss": {
        2023: ["https://www.ndss-symposium.org/ndss2023/accepted-papers/"],
        2024: ["https://www.ndss-symposium.org/ndss2024/accepted-papers/"],
        2025: ["https://www.ndss-symposium.org/ndss2025/accepted-papers/"],
        2026: ["https://www.ndss-symposium.org/ndss2026/accepted-papers/"],
    },
    "ieee_sp": {
        2023: ["https://www.ieee-security.org/TC/SP2023/program-papers.html"],
        2024: ["https://www.ieee-security.org/TC/SP2024/program-papers.html"],
        2025: ["https://www.ieee-security.org/TC/SP2025/program-papers.html"],
        2026: ["https://www.ieee-security.org/TC/SP2026/program-papers.html"],
    },
    "acm_ccs": {
        2023: ["https://dblp.org/db/conf/ccs/ccs2023"],
        2024: ["https://dblp.org/db/conf/ccs/ccs2024"],
        2025: ["https://dblp.org/db/conf/ccs/ccs2025"],
        2026: ["https://dblp.org/db/conf/ccs/ccs2026"],
    },
    "crypto": {
        2023: [f"https://dblp.org/db/conf/crypto/crypto2023-{i}" for i in range(1, 6)],
        2024: [f"https://dblp.org/db/conf/crypto/crypto2024-{i}" for i in range(1, 6)],
        2025: [f"https://dblp.org/db/conf/crypto/crypto2025-{i}" for i in range(1, 6)],
        2026: [f"https://dblp.org/db/conf/crypto/crypto2026-{i}" for i in range(1, 6)],
    },
    "eurocrypt": {
        2023: [f"https://dblp.org/db/conf/eurocrypt/eurocrypt2023-{i}" for i in range(1, 6)],
        2024: [f"https://dblp.org/db/conf/eurocrypt/eurocrypt2024-{i}" for i in range(1, 6)],
        2025: [f"https://dblp.org/db/conf/eurocrypt/eurocrypt2025-{i}" for i in range(1, 6)],
        2026: [f"https://dblp.org/db/conf/eurocrypt/eurocrypt2026-{i}" for i in range(1, 6)],
    },
    "asiacrypt": {
        2023: [f"https://dblp.org/db/conf/asiacrypt/asiacrypt2023-{i}" for i in range(1, 6)],
        2024: [f"https://dblp.org/db/conf/asiacrypt/asiacrypt2024-{i}" for i in range(1, 6)],
        2025: [f"https://dblp.org/db/conf/asiacrypt/asiacrypt2025-{i}" for i in range(1, 6)],
        2026: [f"https://dblp.org/db/conf/asiacrypt/asiacrypt2026-{i}" for i in range(1, 6)],
    },
}


@dataclass
class Candidate:
    venue: str
    year: int
    title: str
    source_url: str
    pdf_url: str = ""
    status: str = "metadata_only"
    notes: str = ""


class LinkTextParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.in_a = False
        self.current_href = ""
        self.current_text: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.in_a = True
            self.current_href = ""
            self.current_text = []
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.current_href = urllib.parse.urljoin(self.base_url, value)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.in_a:
            text = " ".join("".join(self.current_text).split())
            if text or self.current_href:
                self.links.append((text, self.current_href))
            self.in_a = False

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)
        if self.in_a:
            self.current_text.append(data)


def fetch(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "HElicon-collector/1.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def keyword_hit(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in KEYWORDS)


def sanitize_name(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-").lower()
    return text[:140] or "paper"


def parse_candidates(venue: str, year: int, url: str, html: str) -> list[Candidate]:
    parser = LinkTextParser(url)
    parser.feed(html)
    candidates: list[Candidate] = []
    pdf_by_hint: dict[str, str] = {}
    for text, href in parser.links:
        combined = f"{text} {href}"
        if href.lower().endswith(".pdf") or "pdf" in text.lower():
            pdf_by_hint[text.lower()] = href
        if keyword_hit(combined):
            pdf_url = href if href.lower().endswith(".pdf") else ""
            candidates.append(Candidate(venue=venue, year=year, title=text or href, source_url=href or url, pdf_url=pdf_url))
    # Fallback for pages where keyword appears only in surrounding text.
    if not candidates and keyword_hit(" ".join(parser.text_parts)):
        candidates.append(Candidate(venue=venue, year=year, title="KEYWORD_HIT_PAGE_REVIEW_REQUIRED", source_url=url, notes="manual_review_page_keyword_hit"))
    return candidates


def discover_pdf_from_landing(candidate: Candidate, timeout: int) -> str:
    if candidate.pdf_url or not candidate.source_url.startswith(("http://", "https://")):
        return candidate.pdf_url
    try:
        html = fetch(candidate.source_url, timeout=timeout)
    except Exception:
        return ""
    parser = LinkTextParser(candidate.source_url)
    parser.feed(html)
    title_words = [w for w in re.split(r"\W+", candidate.title.lower()) if len(w) >= 4]
    best_pdf = ""
    for text, href in parser.links:
        low_href = href.lower()
        low_text = text.lower()
        if not low_href.endswith(".pdf"):
            continue
        if "slides" in low_text or "video" in low_text:
            continue
        if any(marker in low_href for marker in ("system/files", "ndss-paper")):
            return href
        if not best_pdf:
            best_pdf = href
        elif title_words and sum(1 for w in title_words if w in low_href) > 1:
            best_pdf = href
    return best_pdf


def empty_slot_candidate(venue: str, year: int, url: str, note: str) -> Candidate:
    return Candidate(
        venue=venue,
        year=year,
        title="NO_KEYWORD_HIT_REVIEW_REQUIRED",
        source_url=url,
        status="metadata_only",
        notes=note,
    )


def download_pdf(candidate: Candidate, output_root: Path, dry_run: bool, discover_pdf: bool, timeout: int) -> Candidate:
    if discover_pdf:
        candidate.pdf_url = discover_pdf_from_landing(candidate, timeout)
    if not candidate.pdf_url:
        candidate.status = "metadata_only"
        candidate.notes = candidate.notes or "no_direct_public_pdf_found"
        return candidate
    target_dir = output_root / "corpus" / "by_venue_year" / candidate.venue / str(candidate.year)
    target = target_dir / f"{sanitize_name(candidate.title)}.pdf"
    if dry_run:
        candidate.status = "dry_run_pdf_available"
        candidate.notes = str(target)
        return candidate
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(candidate.pdf_url, headers={"User-Agent": "HElicon-collector/1.1"})
        with urllib.request.urlopen(req, timeout=max(timeout, 20)) as resp:
            data = resp.read()
        if len(data) < 1024 or not data[:5].startswith(b"%PDF"):
            candidate.status = "metadata_only"
            candidate.notes = "pdf_url_not_pdf_or_too_small"
            return candidate
        target.write_bytes(data)
        candidate.status = "downloaded"
        candidate.notes = str(target)
    except Exception as exc:
        candidate.status = "metadata_only"
        candidate.notes = f"download_failed: {exc}"
    return candidate


def write_outputs(candidates: list[Candidate], output_root: Path) -> None:
    distilled = output_root / "distilled" / "fhe_2023_2026"
    logs = output_root / "distilled" / "batch_logs"
    distilled.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    csv_path = distilled / "paper_metadata.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["venue", "year", "title", "source_url", "pdf_url", "status", "notes"])
        writer.writeheader()
        for c in candidates:
            writer.writerow(c.__dict__)
    report = logs / "fhe_2023_2026_collection_report.md"
    by_status: dict[str, int] = {}
    for c in candidates:
        by_status[c.status] = by_status.get(c.status, 0) + 1
    lines = [
        "# FHE 2023-2026 Collection Report",
        "",
        "- scope: USENIX Security, IEEE S&P, ACM CCS, NDSS, CRYPTO, EUROCRYPT, ASIACRYPT",
        "- years: 2023-2026",
        "- filter: direct FHE/HE keyword relevance",
        "- access policy: download only direct public PDFs; otherwise record metadata placeholders",
        "",
        "## Status counts",
        "",
    ]
    lines.extend(f"- {k}: {v}" for k, v in sorted(by_status.items()))
    lines.extend(["", "## Venue-year coverage", ""])
    for venue in sorted({c.venue for c in candidates}):
        years = sorted({c.year for c in candidates if c.venue == venue})
        lines.append(f"- {venue}: {', '.join(str(y) for y in years)}")
    lines.extend(["", f"Metadata CSV: `{csv_path.as_posix()}`", ""])
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--discover-pdf", action="store_true", help="Follow candidate landing pages to find public PDFs.")
    parser.add_argument("--limit-per-venue-year", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--venue", choices=sorted(VENUE_URLS), help="Limit collection to one venue.")
    parser.add_argument("--year", type=int, choices=[2023, 2024, 2025, 2026], help="Limit collection to one year.")
    parser.add_argument("--max-urls-per-slot", type=int, default=0, help="Limit source URLs per venue-year slot.")
    args = parser.parse_args()
    socket.setdefaulttimeout(args.timeout)

    candidates: list[Candidate] = []
    for venue, years in VENUE_URLS.items():
        if args.venue and venue != args.venue:
            continue
        for year, urls in years.items():
            if args.year and year != args.year:
                continue
            found_for_slot = 0
            slot_candidates: list[Candidate] = []
            fetch_errors: list[str] = []
            urls_to_fetch = urls[:args.max_urls_per_slot] if args.max_urls_per_slot else urls
            for url in urls_to_fetch:
                try:
                    html = fetch(url, timeout=args.timeout)
                    slot_candidates.extend(parse_candidates(venue, year, url, html))
                except Exception as exc:
                    fetch_errors.append(f"{url}: {exc}")
            if not slot_candidates:
                note = "no_fhe_keyword_hit_on_source_page"
                if fetch_errors:
                    note = "fetch_failed_or_no_hit: " + " | ".join(fetch_errors[:3])
                slot_candidates = [empty_slot_candidate(venue, year, urls_to_fetch[0], note)]
            for c in slot_candidates:
                if args.limit_per_venue_year and found_for_slot >= args.limit_per_venue_year:
                    break
                candidates.append(download_pdf(c, args.output_root, args.dry_run, args.discover_pdf, args.timeout))
                found_for_slot += 1
    write_outputs(candidates, args.output_root)
    print(f"candidates={len(candidates)} output_root={args.output_root}")
    return 0 if candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
