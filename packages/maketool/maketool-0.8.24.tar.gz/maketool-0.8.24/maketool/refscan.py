#!/usr/bin/env python3
"""
maketool-refscan

Usage:
  maketool-refscan <entry_file>

Reports:
  1) UNUSED files: filename/path tokens not found in scanned text sources
     - Grouped by extension, with .py printed last and a blank line before the .py group
  2) MISSING imports: imports used by entry (and local-resolved siblings) but not installed
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set

try:
    from importlib.metadata import packages_distributions  # py 3.8+
except Exception:
    packages_distributions = None  # type: ignore


# ----------------------------
# Refscan settings
# ----------------------------

DEFAULT_IGNORE_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".pytest_cache",
    ".venv", "venv", "env",
    "build", "dist", ".tox",
}

DEFAULT_SCAN_EXTS = {
    ".py", ".ui", ".qrc", ".qss",
    ".bat", ".cmd", ".ps1",
    ".txt", ".md", ".rst",
    ".ini", ".cfg", ".toml",
    ".json", ".yaml", ".yml",
    ".xml", ".html", ".htm", ".css",
}

DEFAULT_SKIP_CONTENT_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg",
    ".ico", ".icns",
    ".pdf", ".zip", ".7z", ".rar",
    ".db", ".sqlite", ".dll", ".exe", ".pyd",
}


@dataclass(frozen=True)
class Candidate:
    path: Path
    rel: str
    tokens: tuple[str, ...]


def usage_exit(msg: str = "") -> None:
    if msg:
        print(msg, file=sys.stderr)
    print("Usage: maketool-refscan <entry_file>", file=sys.stderr)
    raise SystemExit(2)


def iter_files(root: Path, ignore_dirs: set[str]) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in ignore_dirs for part in p.parts):
            continue
        yield p


def safe_read_text(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def norm(s: str) -> str:
    return s.replace("\\", "/").lower()


def build_candidates(root: Path, files: list[Path]) -> list[Candidate]:
    out: list[Candidate] = []
    for p in files:
        rel = str(p.relative_to(root))
        rel_norm = norm(rel)
        base = p.name.lower()
        stem = p.stem.lower()

        tokens = {
            base,                          # rat.ico
            stem,                          # common
            rel_norm,                      # icons/rat.ico
            rel_norm.replace("/", "\\"),   # icons\rat.ico
        }
        out.append(Candidate(p, rel, tuple(t for t in tokens if t)))
    return out


def is_text_source(p: Path) -> bool:
    ext = p.suffix.lower()
    if ext in DEFAULT_SKIP_CONTENT_EXTS:
        return False
    return ext in DEFAULT_SCAN_EXTS


def print_unused_grouped(unused_rels: list[str]) -> None:
    """
    Print unused files grouped by extension, with .py printed last and a blank
    line inserted before the .py group.
    """
    def sort_key(rel: str):
        ext = Path(rel).suffix.lower()
        is_py = (ext == ".py")
        return (is_py, ext, rel.lower())

    unused_sorted = sorted(unused_rels, key=sort_key)

    print("UNUSED files (no filename/path tokens found)")
    print("--------------------------------------------")

    printed_py_gap = False
    for rel in unused_sorted:
        if Path(rel).suffix.lower() == ".py" and not printed_py_gap:
            # print()  # blank line before first .py file
            printed_py_gap = True
        print(rel)

    print()


# ----------------------------
# Missing-import report
# ----------------------------

def stdlib_names() -> Set[str]:
    names = set(getattr(sys, "stdlib_module_names", set()) or set())
    if names:
        return names

    # Fallback (incomplete) for older Python
    return {
        "os", "sys", "re", "math", "time", "json", "pathlib", "typing", "ast",
        "subprocess", "logging", "datetime", "functools", "itertools", "collections",
        "statistics", "threading", "multiprocessing", "asyncio", "http", "urllib",
        "email", "sqlite3", "csv", "gzip", "zipfile", "hashlib", "base64",
        "ctypes", "inspect", "platform", "shutil", "glob", "fnmatch", "traceback",
        "unittest", "doctest", "xml", "html", "socket", "ssl", "queue",
        "codecs", "shlex", "winreg",
    }


def resolve_local_module(module_name: str, base_dir: Path) -> Optional[Path]:
    rel = Path(*module_name.split("."))
    for candidate in (base_dir / f"{rel}.py", base_dir / rel / "__init__.py"):
        if candidate.exists():
            return candidate
    return None


def imported_top_level_packages(entry_file: Path) -> Set[str]:
    visited: Set[Path] = set()
    found: Set[str] = set()

    def analyze_file(file_path: Path) -> None:
        if file_path in visited:
            return
        visited.add(file_path)

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return

        base_dir = file_path.parent

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    found.add(top)
                    local = resolve_local_module(alias.name, base_dir)
                    if local:
                        analyze_file(local)

            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                top = node.module.split(".")[0]
                found.add(top)
                local = resolve_local_module(node.module, base_dir)
                if local:
                    analyze_file(local)

    analyze_file(entry_file)
    return found


def _index_local_modules_under(root: Path) -> Set[str]:
    found: Set[str] = set()
    if not root.exists():
        return found

    for init_file in root.glob("*/__init__.py"):
        found.add(init_file.parent.name)

    for py in root.glob("*.py"):
        found.add(py.stem)

    return found


def index_local_modules(project_root: Path) -> Set[str]:
    roots: List[Path] = [project_root]

    for name in ["src", "lib", "app", "python", "package", "packages"]:
        p = project_root / name
        if p.exists() and p.is_dir():
            roots.append(p)

    locals_found: Set[str] = set()
    for r in roots:
        locals_found |= _index_local_modules_under(r)

    return locals_found


def try_importable_as_local(name: str, project_root: Path) -> bool:
    added: List[str] = []
    try:
        sp = str(project_root)
        if sp and sp not in sys.path:
            sys.path.insert(0, sp)
            added.append(sp)
        __import__(name)
        return True
    except Exception:
        return False
    finally:
        for sp in added:
            try:
                sys.path.remove(sp)
            except ValueError:
                pass


def compute_missing_used_imports(
    used_import_names: Set[str],
    std: Set[str],
    local_index: Set[str],
    import_to_dists: Dict[str, List[str]],
    project_root: Path,
) -> Set[str]:
    missing: Set[str] = set()
    for name in used_import_names:
        if not name or name in std:
            continue
        if name in local_index:
            continue
        if import_to_dists.get(name):
            continue
        if try_importable_as_local(name, project_root):
            continue
        try:
            __import__(name)
            continue
        except Exception:
            missing.add(name)
    return missing


def run_missing_imports_report(entry: Path, project_root: Path) -> None:
    print("MISSING (used but not installed):")
    print("------------------------------")

    if packages_distributions is None:
        print("(skipped: Python 3.8+ required for importlib.metadata.packages_distributions())\n")
        return

    std = stdlib_names()
    local_index = index_local_modules(project_root)
    used_import_names = imported_top_level_packages(entry)
    import_to_dists: Dict[str, List[str]] = packages_distributions() or {}

    missing = compute_missing_used_imports(
        used_import_names=used_import_names,
        std=std,
        local_index=local_index,
        import_to_dists=import_to_dists,
        project_root=project_root,
    )

    if not missing:
        return

    for m in sorted(missing):
        print(m)
    print()


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    if len(sys.argv) != 2:
        usage_exit()

    entry = Path(sys.argv[1]).expanduser()
    if not entry.exists():
        usage_exit(f"Entry file not found: {entry}")

    entry = entry.resolve()
    root = entry.parent

    ignore_dirs = set(DEFAULT_IGNORE_DIRS)

    files = sorted(iter_files(root, ignore_dirs))
    candidates = build_candidates(root, files)
    text_sources = [p for p in files if is_text_source(p)]

    references: Dict[str, List[str]] = {c.rel: [] for c in candidates}

    for src in text_sources:
        src_rel = str(src.relative_to(root))
        text = safe_read_text(src)
        if not text:
            continue
        hay = text.lower()

        for c in candidates:
            if src == c.path: continue
            # if src == entry: continue
            if any(tok in hay for tok in c.tokens):
                references[c.rel].append(src_rel)

    unused_rels = [c.rel for c in candidates if not references[c.rel]]
    print_unused_grouped(unused_rels)

    if entry.suffix.lower() == ".py":
        run_missing_imports_report(entry=entry, project_root=root)
    else:
        print("MISSING (used but not installed):")
        print("------------------------------")
        print("(skipped: entry is not a .py file)\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
