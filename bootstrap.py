#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


BEGIN_MARKER = "<!-- BEGIN dev-ofa spec-bootstrap -->"
END_MARKER = "<!-- END dev-ofa spec-bootstrap -->"


def content_prefers_chinese(content: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in content)


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


def build_agents_block(spec_relative_path: str, *, language: str) -> str:
    if language == "zh":
        return (
            f"{BEGIN_MARKER}\n"
            "## dev-ofa 规范\n\n"
            "- 本仓库接入 dev-ofa spec。\n"
            "- 本区块是供 Agent 使用的仓库本地索引。\n"
            f"- 先阅读 `{spec_relative_path}/README.md`。\n"
            f"- 编码前阅读 `{spec_relative_path}/AGENTS.md`。\n"
            "- 开始修改前，以编辑目标为起点向上查找最近的 `AGENTS.md`，按目录层级叠加适用规则；若规则冲突，以更接近编辑目标的文件为准。\n"
            f"- 遵循 `{spec_relative_path}/` 下适用的领域规范和语言指南。\n"
            "- 将 `spec` 作为兼容性事实来源；将语言指南作为实现指导。\n"
            f"{END_MARKER}\n"
        )

    return (
        f"{BEGIN_MARKER}\n"
        "## dev-ofa spec\n\n"
        "- This repository follows dev-ofa spec.\n"
        "- This block is a repo-local index for coding agents.\n"
        f"- Read `{spec_relative_path}/README.md` first.\n"
        f"- Read `{spec_relative_path}/AGENTS.md` before coding.\n"
        "- Before editing, start from the target path and look upward for the nearest `AGENTS.md`; apply rules layer by layer, and let the closer file win on conflicts.\n"
        f"- Follow the applicable domain specs and language guides under `{spec_relative_path}/`.\n"
        "- Treat `spec` as the compatibility source of truth; treat language guides as implementation guidance.\n"
        f"{END_MARKER}\n"
    )


def build_initial_agents_content(spec_relative_path: str, *, language: str) -> str:
    if language == "en":
        template = (
            "# AGENTS.md\n\n"
            "## Project Rules\n\n"
            "- This file is the repository-level entry point for coding agents.\n"
            "- Before starting a task, read this file and the relevant README, docs, and code.\n"
            "- State assumptions and ambiguities explicitly; if requirements are unclear, ask maintainers before implementing.\n"
            "- Prefer the simplest solution that fully satisfies the request; avoid speculative abstractions, options, or configurability.\n"
            "- Follow the existing repository structure, naming, testing, and commit conventions.\n"
            "- Confirm the impact scope before editing and avoid unrelated changes.\n"
            "- Make surgical changes only; do not refactor adjacent code or remove unrelated dead code unless asked.\n"
            "- Turn the task into verifiable checks and confirm them before handoff.\n\n"
        )
        return template + build_agents_block(spec_relative_path, language="en")

    template = (
        "# AGENTS.md\n\n"
        "## 项目规则\n\n"
        "- 本文件是仓库级 Agent 工作入口。\n"
        "- 开始任务前，先阅读本文件以及与任务相关的 README、docs 和代码。\n"
        "- 先显式说明假设和歧义；如果需求不清楚，先提出问题并向维护者确认。\n"
        "- 优先选择刚好满足需求的最简单方案，不预埋额外抽象、配置或扩展点。\n"
        "- 遵循仓库已有目录结构、命名、测试和提交风格。\n"
        "- 修改前先确认影响范围，不改动与任务无关的文件。\n"
        "- 只做与当前任务直接相关的最小修改，不顺手重构周边代码，也不删除既有但无关的死代码。\n"
        "- 先把任务转成可验证的完成条件，交付前确认这些检查已经满足。\n\n"
    )
    return template + build_agents_block(spec_relative_path, language="zh")


def ensure_agents_block(
    repo_root: Path, spec_relative_path: str, *, init_language: str
) -> bool:
    agents_path = repo_root / "AGENTS.md"

    if not agents_path.exists():
        agents_path.write_text(
            build_initial_agents_content(
                spec_relative_path, language=init_language
            ),
            encoding="utf-8",
        )
        return True

    original = agents_path.read_text(encoding="utf-8")
    language = "zh" if content_prefers_chinese(original) else "en"
    managed_block = build_agents_block(spec_relative_path, language=language)
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--init-language",
        choices=("zh", "en"),
        default="zh",
        help="Language used only when bootstrap creates a new root AGENTS.md.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        repo_root, spec_dir = infer_repo_paths(Path(__file__))
        spec_relative_path = spec_dir.relative_to(repo_root).as_posix()
        agents_changed = ensure_agents_block(
            repo_root, spec_relative_path, init_language=args.init_language
        )
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
