#!/usr/bin/env bash
# Extractor driver for the Codex CLI. Adjust the invocation to your installed
# Codex CLI version if its non-interactive flag differs. Driver contract:
# prompt in on stdin, one finding per line out on stdout.
set -euo pipefail
prompt=$(cat)
codex exec "$prompt"
