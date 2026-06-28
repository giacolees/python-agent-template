#!/usr/bin/env bash
# Extractor driver (default): relay the prompt on stdin to the Claude Code
# CLI and print its insight lines on stdout. Driver contract: prompt in on
# stdin, one finding per line out on stdout, empty output == no insights.
set -euo pipefail
prompt=$(cat)
claude -p "$prompt"
