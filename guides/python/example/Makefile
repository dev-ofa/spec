.PHONY: install fmt lint type test lock sync

install:
	command -v uv >/dev/null || (echo "请先安装 uv：https://docs.astral.sh/uv/"; exit 1)
	uv pip install -e ".[dev]"

fmt:
	ruff format .

lint:
	ruff check .

type:
	pyright

test:
	pytest

lock:
	uv lock

sync:
	uv sync
