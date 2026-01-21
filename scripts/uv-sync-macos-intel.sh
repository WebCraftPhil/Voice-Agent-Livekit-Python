#!/usr/bin/env bash
set -euo pipefail

uv sync --python-platform x86_64-apple-darwin

cat <<'EOF'

Done. If you run agent commands, prefer:
  uv run --no-sync python src/agent.py download-files
EOF
