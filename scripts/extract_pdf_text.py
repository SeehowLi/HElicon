#!/usr/bin/env python3
"""Extract text from PDFs for HElicon workspace use.

The script prefers Poppler's pdftotext because it is usually better for
academic PDFs. It falls back to PyPDF2 when pdftotext is unavailable.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def extract_with_pdftotext(pdf: Path, output: Path) -> bool:
    exe = shutil.which("pdftotext")
    if not exe:
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [exe, "-layout", "-enc", "UTF-8", str(pdf), str(output)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0 and output.exists() and output.stat().st_size > 0


def extract_with_pypdf2(pdf: Path, output: Path) -> bool:
    try:
        import PyPDF2  # type: ignore
    except Exception:
        return False

    output.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    with pdf.open("rb") as fh:
        reader = PyPDF2.PdfReader(fh)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            parts.append(f"\n\n===== PAGE {i} =====\n\n{text}")
    output.write_text("\n".join(parts), encoding="utf-8")
    return output.stat().st_size > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    pdf = args.pdf.resolve()
    output = args.output.resolve()
    if not pdf.exists():
        print(f"PDF not found: {pdf}")
        return 2

    if extract_with_pdftotext(pdf, output):
        print(f"extracted_with=pdftotext output={output}")
        return 0
    if extract_with_pypdf2(pdf, output):
        print(f"extracted_with=PyPDF2 output={output}")
        return 0

    print("No PDF extractor succeeded. Install pdftotext or PyPDF2.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
