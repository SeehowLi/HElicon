#!/usr/bin/env python3
"""Create a paper-local .helicon pack or a compatible legacy project pack."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


class UserError(Exception):
    """A concise command-line error."""


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except FileNotFoundError as exc:
        raise UserError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path} ({exc})") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc


def tex_files(paper_dir: Path) -> list[Path]:
    return sorted(
        (path for path in paper_dir.rglob("*.tex") if ".helicon" not in path.parts),
        key=lambda item: str(item).lower(),
    )


def plain_word_count(text: str) -> int:
    stripped = re.sub(r"(?<!\\)%.*", "", text)
    stripped = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", stripped)
    stripped = re.sub(r"[{}$\\]", " ", stripped)
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", stripped))


def fingerprint(paper_dir: Path, name: str) -> dict[str, Any]:
    files = tex_files(paper_dir)
    title = name
    sections: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for path in files:
        content = read_utf8(path)
        relative = path.relative_to(paper_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content.encode("utf-8"))
        digest.update(b"\0")
        title_match = re.search(r"\\title\s*\{([^{}]+)\}", content)
        if title_match and title == name:
            title = re.sub(r"\s+", " ", title_match.group(1)).strip()
        matches = list(re.finditer(r"\\(?:section|subsection|subsubsection)\*?\{([^{}]+)\}", content))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            sections.append({
                "title": re.sub(r"\s+", " ", match.group(1)).strip(),
                "words": plain_word_count(content[match.end():end]),
                "file": relative,
            })
    return {
        "title": title,
        "target_venue": "",
        "key_terms": [],
        "sections": sections,
        "content_hash": f"sha256:{digest.hexdigest()}",
    }


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def project_yaml(name: str, paper_dir: Path, fp: dict[str, Any], now: str) -> str:
    lines = [
        "schema: helicon-project-v1",
        f"name: {yaml_quote(name)}",
        f"paper_dir: {yaml_quote(str(paper_dir.resolve()))}",
        f"created_utc: {yaml_quote(now)}",
        f"last_action_utc: {yaml_quote(now)}",
        "fingerprint:",
        f"  title: {yaml_quote(str(fp['title']))}",
        f"  target_venue: {yaml_quote(str(fp['target_venue']))}",
        "  key_terms: []",
    ]
    if fp["sections"]:
        lines.append("  sections:")
        for section in fp["sections"]:
            lines.extend([
                f"    - title: {yaml_quote(section['title'])}",
                f"      words: {section['words']}",
                f"      file: {yaml_quote(section['file'])}",
            ])
    else:
        lines.append("  sections: []")
    lines.append(f"  content_hash: {yaml_quote(str(fp['content_hash']))}")
    return "\n".join(lines) + "\n"


def skeletons(name: str) -> dict[str, str]:
    template_root = Path(__file__).resolve().parent.parent / "templates"
    files = {
        output: read_utf8(template_root / template)
        for output, template in {
            "draft_map.md": "draft_map.md",
            "claim_ledger.md": "claim_ledger.md",
            "evidence_matrix.csv": "evidence_matrix.csv",
            "revision_queue.csv": "revision_queue.csv",
            "reviewer_risk_log.md": "reviewer_risk_log.md",
            "pass_log.md": "pass_log.md",
            "polish_ledger.csv": "polish_ledger.csv",
        }.items()
    }
    files["draft_map.md"] = files["draft_map.md"].replace(
        "- Intake status: complete | stale | [no intake]",
        "- Intake status: [no intake]",
    )
    files.update({
        "local_glossary.md": f"# {name} Local Glossary\n\n| Term | Preferred English | Avoid | Notes |\n|---|---|---|---|\n",
        "decisions.md": "# Decisions\n\n## Current Locked Decisions\n\n## Open Decisions\n\n## Recently Superseded\n",
    })
    return files


def write_new(path: Path, content: str, created: list[str]) -> None:
    if path.exists():
        return
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise UserError(f"cannot write {path}: {exc}") from exc
    created.append(str(path))


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": "helicon-registry-v1", "projects": []}
    try:
        data = json.loads(read_utf8(path))
    except json.JSONDecodeError as exc:
        raise UserError(f"invalid registry JSON: {path} ({exc})") from exc
    if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
        raise UserError(f"registry has unsupported structure: {path}")
    return data


def register(path: Path, paper_dir: Path, name: str, fp: dict[str, Any], now: str) -> None:
    data = load_registry(path)
    resolved = str(paper_dir.resolve())
    entry = {"path": resolved, "name": name, "fingerprint": {**fp, "last_action_utc": now}}
    projects = [item for item in data["projects"] if not isinstance(item, dict) or item.get("path") != resolved]
    projects.append(entry)
    data["projects"] = sorted(projects, key=lambda item: str(item.get("path", "")).lower() if isinstance(item, dict) else "")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        raise UserError(f"cannot update registry {path}: {exc}") from exc


def bootstrap(paper_dir: Path, pack_dir: Path, name: str, registry_path: Path, mode: str) -> dict[str, Any]:
    if not paper_dir.exists() or not paper_dir.is_dir():
        raise UserError(f"paper directory does not exist: {paper_dir}")
    now = datetime.now(timezone.utc).isoformat()
    fp = fingerprint(paper_dir, name)
    created: list[str] = []
    try:
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "style").mkdir(parents=True, exist_ok=True)
        (pack_dir / "style" / "exemplars").mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UserError(f"cannot create project pack {pack_dir}: {exc}") from exc
    write_new(pack_dir / "project.yaml", project_yaml(name, paper_dir, fp, now), created)
    for relative, content in skeletons(name).items():
        write_new(pack_dir / relative, content, created)
    register(registry_path, paper_dir, name, fp, now)
    return {
        "mode": mode,
        "paper_dir": str(paper_dir.resolve()),
        "pack_dir": str(pack_dir.resolve()),
        "registry": str(registry_path.resolve()),
        "created_files": created,
        "fingerprint": fp,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy_projects_root", nargs="?", help="v1.2 projects root")
    parser.add_argument("legacy_project_name", nargs="?", help="v1.2 project name")
    parser.add_argument("--paper-dir", help="paper directory for local .helicon layout")
    parser.add_argument("--name", help="project name; defaults to paper directory name")
    parser.add_argument("--registry", default=str(Path.home() / ".helicon" / "registry.json"), help="registry JSON path")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        registry = Path(args.registry)
        if args.paper_dir:
            if args.legacy_projects_root or args.legacy_project_name:
                raise UserError("do not combine --paper-dir with legacy positional arguments")
            paper_dir = Path(args.paper_dir)
            name = args.name or paper_dir.resolve().name
            result = bootstrap(paper_dir, paper_dir / ".helicon", name, registry, "paper-local")
        else:
            if not args.legacy_projects_root or not args.legacy_project_name:
                raise UserError("use --paper-dir <paper> [--name <name>] or legacy <projects_root> <project_name>")
            projects_root = Path(args.legacy_projects_root)
            try:
                projects_root.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise UserError(f"cannot create legacy projects root {projects_root}: {exc}") from exc
            paper_dir = projects_root / args.legacy_project_name
            try:
                paper_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise UserError(f"cannot create legacy project directory {paper_dir}: {exc}") from exc
            result = bootstrap(paper_dir, paper_dir, args.legacy_project_name, registry, "legacy-centralized")
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Created/updated project pack: {result['pack_dir']}")
            print(f"Registered: {result['registry']}")
            print(f"New files: {len(result['created_files'])}")
        return 0
    except UserError as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
