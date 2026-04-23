#!/usr/bin/env bash
# Install git hooks for the judgement repo.
# Usage: ./scripts/install-hooks.sh

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_DIR="$REPO_ROOT/.git/hooks"

cat > "$HOOK_DIR/pre-push" << 'HOOK'
#!/usr/bin/env bash
# Pre-push hook: run full test suite before allowing push to main.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SUITE_DIR="${JUDGEMENT_TESTS:-$REPO_ROOT/../judgement-tests}"

# Only gate pushes to main
while read local_ref local_sha remote_ref remote_sha; do
    if echo "$remote_ref" | grep -q "refs/heads/main"; then
        echo ""
        echo "=== Pre-push: running full test suite ==="
        echo ""

        # Clone test suite repo if not present
        if [ ! -d "$SUITE_DIR/backend" ]; then
            echo "Cloning judgement-tests..."
            git clone https://github.com/jvalin17/judgement-tests.git "$SUITE_DIR"
        else
            echo "Pulling latest test suite..."
            git -C "$SUITE_DIR" pull --ff-only 2>/dev/null || true
        fi

        # Pydantic check
        python3 -c "from pydantic import BaseModel" || {
            echo "ERROR: pydantic import failed. Run: python3 -m pip install --force-reinstall pydantic pydantic-core"
            exit 1
        }

        # Backend smoke tests
        echo ""
        echo "--- Backend smoke tests ---"
        python3 -m pytest "$REPO_ROOT/backend/tests/" -v || { echo "BLOCKED: backend smoke tests failed"; exit 1; }

        # Frontend smoke tests
        echo ""
        echo "--- Frontend smoke tests ---"
        cd "$REPO_ROOT/frontend" && npx vitest run || { echo "BLOCKED: frontend smoke tests failed"; exit 1; }
        cd "$REPO_ROOT"

        # TypeScript
        echo ""
        echo "--- TypeScript check ---"
        cd "$REPO_ROOT/frontend" && npx tsc -b || { echo "BLOCKED: TypeScript errors"; exit 1; }
        cd "$REPO_ROOT"

        # Backend suite tests
        echo ""
        echo "--- Backend suite tests ---"
        JUDGEMENT_REPO="$REPO_ROOT" python3 -m pytest "$SUITE_DIR/backend/" -v --rootdir="$SUITE_DIR" || { echo "BLOCKED: backend suite tests failed"; exit 1; }

        # Frontend suite tests (copy in, run, clean up)
        echo ""
        echo "--- Frontend suite tests ---"
        MARKER="$REPO_ROOT/frontend/src/.suite-tests-copied"
        cleanup() {
            if [ -f "$MARKER" ]; then
                while IFS= read -r file; do
                    rm -f "$REPO_ROOT/frontend/src/$file"
                done < "$MARKER"
                rm -f "$MARKER"
            fi
        }
        trap cleanup EXIT

        find "$SUITE_DIR/frontend/src" -name "*.test.*" -type f | while IFS= read -r src_file; do
            rel="${src_file#$SUITE_DIR/frontend/src/}"
            dest="$REPO_ROOT/frontend/src/$rel"
            mkdir -p "$(dirname "$dest")"
            cp "$src_file" "$dest"
            echo "$rel" >> "$MARKER"
        done

        cd "$REPO_ROOT/frontend" && npx vitest run || { echo "BLOCKED: frontend suite tests failed"; exit 1; }
        cd "$REPO_ROOT"

        echo ""
        echo "=== All tests passed — push allowed ==="
        echo ""
    fi
done
HOOK

chmod +x "$HOOK_DIR/pre-push"
echo "Pre-push hook installed. Full test suite will run before every push to main."
