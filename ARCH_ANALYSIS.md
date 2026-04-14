# Architecture Mismatch Analysis

## System Facts

| Fact | Value |
|------|-------|
| CPU | Apple M4 Max (arm64) |
| macOS | Darwin 25.3.0 |
| Python | `/usr/bin/python3` 3.9.6 — universal binary (x86_64 + arm64e) |
| pip packages | `~/Library/Python/3.9/lib/python/site-packages/` |
| Terminal.app | Universal binary — runs as arm64 natively on Apple Silicon |
| Claude Code bash | Runs under Rosetta (x86_64/i386) |

## Root Cause

Two different contexts use the **same Python binary** and **same site-packages**, but in **different architectures**:

| Context | Python runs as | Why |
|---------|---------------|-----|
| User's Terminal.app | **arm64** | Terminal runs natively on Apple Silicon |
| Claude Code bash | **x86_64** | Claude Code runs under Rosetta |

When Claude Code runs `pip install`, pip detects x86_64 and downloads **x86_64 wheels**. When the user opens Terminal and runs `./play`, Python loads as **arm64** and fails to dlopen x86_64 .so files.

### The exact failure chain:

```
User opens Terminal (arm64) → runs ./play → bash starts python3 (arm64) →
uvicorn loads → imports fastapi → imports pydantic → imports pydantic_core →
dlopen(_pydantic_core.cpython-39-darwin.so) → FAILS: .so is x86_64, need arm64
```

## Why previous fixes didn't work

| Fix attempted | Why it failed |
|---------------|---------------|
| `pip3 install --force-reinstall pydantic` (from Claude Code) | Installs x86_64 wheels because Claude Code bash is x86_64 |
| Subprocess instead of thread in desktop/main.py | Subprocess inherits parent arch — still arm64 in user's Terminal |
| Starting server from bash in `./play` | User's bash IS arm64, so python3 also runs as arm64 |

## The fix: Architecture-aware startup

The `./play` script must detect which architecture can actually load the packages and force Python to use that arch.

```bash
# Try arm64 first (native), then x86_64, then bare python3
if arch -arm64 python3 -c "from pydantic_core import __version__" 2>/dev/null; then
    PYTHON="arch -arm64 python3"
elif arch -x86_64 python3 -c "from pydantic_core import __version__" 2>/dev/null; then
    PYTHON="arch -x86_64 python3"
else
    echo "ERROR: pydantic broken. Run: pip3 install --force-reinstall pydantic pydantic-core"
    exit 1
fi
```

This works because:
- `arch -arm64 python3` forces the universal binary to arm64 regardless of terminal
- `arch -x86_64 python3` forces x86_64 regardless of terminal
- Whichever arch matches the installed .so files wins

## Alternate permanent fix: Install native arm64 wheels

Since the machine is Apple Silicon and the user's Terminal is arm64:

```bash
arch -arm64 pip3 install --force-reinstall pydantic pydantic-core
```

This installs arm64 wheels that match the user's native Terminal. But this can break again if Claude Code reinstalls packages (x86_64).

## How to auto-test

```bash
# 1. Verify pydantic loads under BOTH architectures (or at least one)
arch -arm64 python3 -c "from pydantic_core import __version__; print('arm64 OK')" 2>&1
arch -x86_64 python3 -c "from pydantic_core import __version__; print('x86_64 OK')" 2>&1

# 2. Verify FastAPI app loads under the arch that'll be used
arch -arm64 python3 -c "from backend.app.main import app; print('app OK arm64')" 2>&1
arch -x86_64 python3 -c "from backend.app.main import app; print('app OK x86_64')" 2>&1

# 3. Full server start test
arch -arm64 python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765 &
sleep 3 && curl -s http://127.0.0.1:8765/health && kill %1

# 4. End-to-end ./play test (what the user actually runs)
./play &
sleep 12 && curl -s http://127.0.0.1:8000/health && kill %1
```

## Strategy chosen — IMPLEMENTED AND VERIFIED

**Approach: Arch-detect in ./play + install arm64 wheels + setup uses native arch**

### What was done:

1. **Installed arm64 wheels**: `arch -arm64 pip3 install --force-reinstall pydantic pydantic-core`
2. **`./play`**: Auto-detects working arch by testing `arch -arm64 python3`, `arch -x86_64 python3`, then bare `python3`. Uses whichever can load pydantic_core.
3. **`./setup`**: Detects Apple Silicon via `sysctl hw.optional.arm64`, uses `arch -arm64 pip3` for all installs so wheels match native Terminal.
4. **Verification**: Server starts, /health responds, quick-join works, 190 tests pass.

### How to test:

```bash
# Quick verification
arch -arm64 python3 -c "from backend.app.main import app; print('OK')"

# Full test
./play &
sleep 12 && curl -s http://127.0.0.1:8000/health

# Tests (use arch -arm64 if in Rosetta terminal)
arch -arm64 python3 -m pytest backend/tests/ -q
```

### Key lesson for Claude Code

Claude Code's bash runs under Rosetta (x86_64). The user's Terminal runs natively (arm64). They share the same Python binary and site-packages. Any `pip install` from Claude Code gets x86_64 wheels that won't work in the user's Terminal. **Always use `arch -arm64 pip3 install` on Apple Silicon Macs.**
