#!/usr/bin/env bash
set -euo pipefail

uv run alembic upgrade head
uv run python scripts/seed_sources.py
