#!/usr/bin/env python3
"""Deterministic stack fingerprint for repo-stack-inspect (stdlib only)."""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".tox",
    "dist",
    "build",
    ".next",
}

MANIFEST_NAMES = [
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "composer.json",
    "Pipfile",
    "requirements.txt",
]

LANG_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".java": "Java",
    ".sh": "Shell",
    ".md": "Markdown",
}

PATTERN_TOKEN_RULES = [
    ("playwright", re.compile(r"playwright", re.IGNORECASE)),
    ("session_mode_cdp", re.compile(r"SESSION_MODE.*cdp|cdp.*SESSION_MODE", re.IGNORECASE)),
    ("user_data_dir", re.compile(r"user_data(?:_dir)?", re.IGNORECASE)),
    ("cdp", re.compile(r"\bcdp\b|remote-debugging", re.IGNORECASE)),
    ("headed", re.compile(r"\bHEADED\b|headed\s*=\s*true", re.IGNORECASE)),
    ("launch_persistent", re.compile(r"launch_persistent", re.IGNORECASE)),
]

LIVEOPS_DOC_PATTERNS = [
    re.compile(r"liveops", re.IGNORECASE),
    re.compile(r"runtime-layout", re.IGNORECASE),
    re.compile(r"research-.*-challenges", re.IGNORECASE),
]

AUTOMATION_SCRIPT_PATTERNS = [
    re.compile(r"start-chrome.*\.ps1$", re.IGNORECASE),
    re.compile(r"stop-broker.*\.ps1$", re.IGNORECASE),
    re.compile(r"smoke-cdp.*\.ps1$", re.IGNORECASE),
]

FOCUS_LENSES = {
    "playwright": {
        "label": "Playwright",
        "signals": frozenset({"playwright", "launch_persistent", "headed", "automation_scripts"}),
    },
    "cdp": {
        "label": "CDP",
        "signals": frozenset({"cdp", "session_mode_cdp", "automation_scripts", "liveops_docs"}),
    },
    "persistent-profile": {
        "label": "Persistent Profile",
        "signals": frozenset({"user_data_dir"}),
    },
    "ci": {
        "label": "CI",
        "signals": frozenset(),
        "uses_ci": True,
    },
    "all-patterns": {
        "label": "All Patterns",
        "signals": None,
    },
}


def walk_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".venv")]
        for name in filenames:
            yield Path(dirpath) / name


def normalize_lens_name(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def parse_focus_lenses(values: list[str]) -> list[str]:
    lenses = []
    for value in values:
        for part in value.split(","):
            part = normalize_lens_name(part)
            if part:
                lenses.append(part)
    return lenses


def apply_focus(data: dict, focus_lenses: list[str], strict: bool) -> dict:
    all_signals = set(data.get("pattern_signals") or [])
    ci_workflows = list(data.get("ci_workflows") or [])

    if not focus_lenses:
        required = bool(all_signals)
        return {
            "focus_lenses": [],
            "focus_mode": "auto",
            "pattern_signals": sorted(all_signals),
            "scoped_ci_workflows": [],
            "patterns_section": {
                "required": required,
                "title": "Patterns and Problems Solved" if required else None,
            },
        }

    unknown = [lens for lens in focus_lenses if lens not in FOCUS_LENSES]
    if unknown:
        raise ValueError(f"unknown focus lens(s): {', '.join(unknown)}")

    if "all-patterns" in focus_lenses:
        required = bool(all_signals or ci_workflows)
        return {
            "focus_lenses": ["all-patterns"],
            "focus_mode": "explicit",
            "pattern_signals": sorted(all_signals),
            "scoped_ci_workflows": ci_workflows,
            "patterns_section": {
                "required": required,
                "title": "All Patterns — Problems Solved" if required else None,
            },
        }

    allowed = set()
    labels = []
    uses_ci = False
    for lens in focus_lenses:
        meta = FOCUS_LENSES[lens]
        labels.append(meta["label"])
        signals = meta.get("signals")
        if signals is not None:
            allowed |= set(signals)
        if meta.get("uses_ci"):
            uses_ci = True

    filtered = sorted(all_signals & allowed) if allowed else []
    scoped_ci = ci_workflows if uses_ci else []
    has_scope = bool(filtered or scoped_ci)

    if strict and not has_scope:
        raise ValueError(
            "no signals matched focus lens(s): "
            + ", ".join(focus_lenses)
            + "; try --all-patterns or drop unused lens flags"
        )

    title = " + ".join(labels) + " — Patterns Solved"
    return {
        "focus_lenses": focus_lenses,
        "focus_mode": "explicit",
        "pattern_signals": filtered,
        "scoped_ci_workflows": scoped_ci,
        "patterns_section": {
            "required": True,
            "title": title,
        },
    }


def detect_manifests(root: Path):
    found = []
    for name in MANIFEST_NAMES:
        path = root / name
        if path.is_file():
            found.append(name)
    for pattern in ("requirements-*.txt", "docker-compose*.yml", "docker-compose*.yaml"):
        for match in sorted(root.glob(pattern)):
            if match.is_file():
                found.append(match.name)
    if (root / "Dockerfile").is_file():
        found.append("Dockerfile")
    return sorted(set(found))


def detect_ci(root: Path):
    names = []
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        names.extend(sorted(p.name for p in workflows.glob("*.yml")))
        names.extend(sorted(p.name for p in workflows.glob("*.yaml")))
    if (root / ".gitlab-ci.yml").is_file():
        names.append(".gitlab-ci.yml")
    for name in ("Makefile", "justfile"):
        if (root / name).is_file():
            names.append(name)
    return names


def detect_languages(root: Path):
    counts = {}
    scanned = 0
    for path in walk_files(root):
        if not path.is_file():
            continue
        scanned += 1
        ext = path.suffix.lower()
        lang = LANG_EXTENSIONS.get(ext)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    primary = None
    if counts:
        primary = max(counts.items(), key=lambda item: item[1])[0]
    return primary, counts, scanned


def detect_nested_manifests(root: Path):
    found = []
    for path in sorted(root.rglob("pyproject.toml")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel != "pyproject.toml":
            found.append(rel)
    return found


def detect_pattern_signals(root: Path):
    signals = set()
    liveops_docs = []
    automation_scripts = []
    for path in walk_files(root):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        name = path.name
        for pattern in LIVEOPS_DOC_PATTERNS:
            if pattern.search(rel):
                liveops_docs.append(rel)
                signals.add("liveops_docs")
                break
        for pattern in AUTOMATION_SCRIPT_PATTERNS:
            if pattern.search(name):
                automation_scripts.append(rel)
                signals.add("automation_scripts")
                break
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for signal_name, pattern in PATTERN_TOKEN_RULES:
            if pattern.search(text):
                signals.add(signal_name)
    return sorted(signals), sorted(set(liveops_docs)), sorted(set(automation_scripts))


def detect_execution_evidence(root: Path):
    evidence = []
    for name in ("CHANGELOG.md", "CHANGELOG", "RUN.md"):
        if (root / name).is_file():
            evidence.append(name)
    specs = root / "specs"
    if specs.is_dir():
        for path in sorted(specs.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            if re.search(r"/(spec|plan|tasks|research)\.md$", rel):
                evidence.append(rel)
                if len(evidence) >= 12:
                    break
    return evidence


def git_remote(root: Path):
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def recent_commits(root: Path, limit=10):
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "log", "--oneline", f"-{limit}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def fingerprint(root: Path, slug: str, focus_lenses: Optional[list] = None, strict_focus: bool = False):
    manifests = detect_manifests(root)
    nested_manifests = detect_nested_manifests(root)
    ci = detect_ci(root)
    primary, lang_counts, files_scanned = detect_languages(root)
    evidence = detect_execution_evidence(root)
    pattern_signals, liveops_docs, automation_scripts = detect_pattern_signals(root)
    remote = git_remote(root)
    commits = recent_commits(root)
    entry_points = []
    for candidate in ("bin", "src", "cmd", "app"):
        if (root / candidate).is_dir():
            entry_points.append(candidate + "/")

    base = {
        "schema_version": "stack-fingerprint-v1.2",
        "slug": slug,
        "repository_path": str(root),
        "repository_url": remote,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifests": manifests,
        "nested_manifests": nested_manifests,
        "ci_workflows": ci,
        "primary_language": primary,
        "language_counts": lang_counts,
        "execution_evidence": evidence,
        "entry_points": entry_points,
        "pattern_signals_all": pattern_signals,
        "liveops_docs": liveops_docs,
        "automation_scripts": automation_scripts,
        "recent_commits": commits,
    }

    focus = apply_focus(
        {
            "pattern_signals": pattern_signals,
            "ci_workflows": ci,
        },
        focus_lenses or [],
        strict_focus,
    )
    base.update(focus)
    base["pattern_signals"] = focus["pattern_signals"]

    signal_count = (
        len(manifests)
        + len(nested_manifests)
        + len(ci)
        + len(evidence)
        + len(pattern_signals)
        + (1 if primary else 0)
    )
    base["audit"] = {
        "files_scanned": files_scanned,
        "signals_found": signal_count,
        "warnings": [],
    }
    return base


def main():
    parser = argparse.ArgumentParser(description="Stack fingerprint for repo-stack-inspect")
    parser.add_argument("--path", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--json-out", default="-")
    parser.add_argument(
        "--focus",
        action="append",
        default=[],
        help="Focus lens(es): playwright, cdp, persistent-profile, ci, all-patterns (comma-separated, repeatable)",
    )
    parser.add_argument(
        "--strict-focus",
        action="store_true",
        help="Exit with error when explicit focus lenses match no signals",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    focus_lenses = parse_focus_lenses(args.focus)
    try:
        data = fingerprint(root, args.slug, focus_lenses=focus_lenses, strict_focus=args.strict_focus)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if args.json_out == "-":
        sys.stdout.write(payload)
    else:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
