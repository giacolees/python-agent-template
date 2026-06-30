#!/usr/bin/env bash
# Extractor driver for the Gemini CLI. Adjust the invocation to your installed
# Gemini CLI version if its prompt flag differs. Driver contract: prompt in on
# stdin, one finding per line out on stdout.
set -euo pipefail
prompt=$(cat)
gemini -p "$prompt"
