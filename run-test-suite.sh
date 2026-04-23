#!/usr/bin/env bash
# Run the full test suite from jvalin17/judgement-tests against this repo.
# Usage: ./run-test-suite.sh
#
# Expects judgement-tests repo cloned as a sibling directory:
#   parent/
#     judgement/        <-- this repo (run from here)
#     judgement-tests/  <-- test suite repo

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SUITE_DIR="${JUDGEMENT_TESTS:-$SCRIPT_DIR/../judgement-tests}"

if [ ! -d "$SUITE_DIR/backend" ]; then
    echo "Error: Cannot find judgement-tests repo at $SUITE_DIR"
    echo "Clone it: git clone https://github.com/jvalin17/judgement-tests.git $SUITE_DIR"
    exit 1
fi

echo "=== Running smoke tests (main repo) ==="
python3 -m pytest backend/tests/ -v
cd frontend && npx vitest run && cd ..

echo ""
echo "=== Running full test suite ==="

# Backend: run suite tests with main repo on sys.path
JUDGEMENT_REPO="$SCRIPT_DIR" python3 -m pytest "$SUITE_DIR/backend/" -v --rootdir="$SUITE_DIR"

# Frontend: copy suite test files in, run, clean up
TEMP_MARKER="$SCRIPT_DIR/frontend/src/.suite-tests-copied"
cleanup() {
    if [ -f "$TEMP_MARKER" ]; then
        # Remove only the files we copied
        while IFS= read -r file; do
            rm -f "$SCRIPT_DIR/frontend/src/$file"
        done < "$TEMP_MARKER"
        rm -f "$TEMP_MARKER"
    fi
}
trap cleanup EXIT

# Copy suite frontend tests into main repo's frontend/src
find "$SUITE_DIR/frontend/src" -name "*.test.*" -type f | while IFS= read -r src_file; do
    rel="${src_file#$SUITE_DIR/frontend/src/}"
    dest="$SCRIPT_DIR/frontend/src/$rel"
    mkdir -p "$(dirname "$dest")"
    cp "$src_file" "$dest"
    echo "$rel" >> "$TEMP_MARKER"
done

cd frontend && npx vitest run && cd ..

echo ""
echo "=== All tests passed ==="
