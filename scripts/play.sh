#!/bin/bash
# One command to build and play Judgement.
# Wrapper that calls the top-level ./play script.
set -e
cd "$(dirname "$0")/.."
exec ./play "$@"
