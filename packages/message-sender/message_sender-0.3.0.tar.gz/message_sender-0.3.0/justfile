@_default:
  just --list

@lint:
  echo mypy
  just --justfile {{justfile()}} mypy
  echo ruff-check
  just --justfile {{justfile()}} ruff-check
  echo ruff-format
  just --justfile {{justfile()}} ruff-format

@mypy:
  uv run mypy message_sender tests

@ruff-check:
  uv run ruff check message_sender tests

@ruff-format:
  uv run ruff format message_sender tests

@lock:
  uv lock

@lock-upgrade:
  uv lock --upgrade

@install:
  uv sync --frozen --all-extras

@test *args="":
  uv run pytest {{args}}
