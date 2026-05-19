#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


BEGIN_MARKER = "<!-- BEGIN dev-ofa spec-bootstrap -->"
END_MARKER = "<!-- END dev-ofa spec-bootstrap -->"


def infer_repo_paths(script_file: Path) -> tuple[Path, Path]:
    spec_dir = script_file.resolve().parent

    if spec_dir.name != "spec" or spec_dir.parent.name != "docs":
        raise RuntimeError(
            "bootstrap.py currently supports only the `docs/spec` layout inside "
            "the target project. If you use another distribution path, update "
            "the repo-local index manually or extend this script first."
        )

    repo_root = spec_dir.parent.parent
    return repo_root, spec_dir


def build_agents_block(spec_relative_path: str) -> str:
    return (
        f"{BEGIN_MARKER}\n"
        "## dev-ofa spec\n\n"
        "- This repository follows dev-ofa spec.\n"
        "- This block is a repo-local index for coding agents.\n"
        f"- Read `{spec_relative_path}/README.md` first.\n"
        f"- Read `{spec_relative_path}/AGENTS.md` before coding.\n"
        f"- Follow the applicable domain specs and language guides under `{spec_relative_path}/`.\n"
        "- Treat `spec` as the compatibility source of truth; treat language guides as implementation guidance.\n"
        f"{END_MARKER}\n"
    )


def ensure_agents_block(repo_root: Path, spec_relative_path: str) -> bool:
    agents_path = repo_root / "AGENTS.md"
    managed_block = build_agents_block(spec_relative_path)

    if not agents_path.exists():
        agents_path.write_text(managed_block, encoding="utf-8")
        return True

    original = agents_path.read_text(encoding="utf-8")
    updated = upsert_managed_block(original, managed_block)
    if updated == original:
        return False

    agents_path.write_text(updated, encoding="utf-8")
    return True


def upsert_managed_block(content: str, managed_block: str) -> str:
    if BEGIN_MARKER in content and END_MARKER in content:
        start = content.index(BEGIN_MARKER)
        end = content.index(END_MARKER) + len(END_MARKER)
        replaced = content[:start] + managed_block.rstrip("\n") + content[end:]
        return normalize_trailing_newline(replaced)

    trimmed = content.rstrip()
    if not trimmed:
        return managed_block

    return normalize_trailing_newline(f"{trimmed}\n\n{managed_block}")


def normalize_trailing_newline(content: str) -> str:
    return content.rstrip() + "\n"


def main() -> int:
    try:
        repo_root, spec_dir = infer_repo_paths(Path(__file__))
        spec_relative_path = spec_dir.relative_to(repo_root).as_posix()
        agents_changed = ensure_agents_block(repo_root, spec_relative_path)
    except Exception as exc:  # pragma: no cover - top-level error reporting
        print(f"[spec-bootstrap] error: {exc}", file=sys.stderr)
        return 1

    print("[spec-bootstrap] bootstrap finished")
    print(f"  - repo root: {repo_root}")
    print(f"  - spec path: {spec_relative_path}")
    print(f"  - AGENTS.md block: {'updated' if agents_changed else 'unchanged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
