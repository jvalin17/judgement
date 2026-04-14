# TODO / Known Issues

## pydantic_core Architecture Mismatch (macOS with Rosetta)

**Problem:** System Python 3.9 is a universal binary. pywebview installs pyobjc which pulls arm64 wheels, flipping the process architecture. pydantic_core .so then has the wrong arch.

**Symptoms:**
- `ImportError: dlopen ... incompatible architecture (have 'x86_64', need 'arm64')` or vice versa
- Happens after `pip install pywebview`, `pip install pyobjc`, or any install that touches compiled .so files

**Immediate fix:**
```bash
pip3 install --force-reinstall pydantic pydantic-core
python3 -c "from pydantic_core import __version__; print(__version__)"
```

**Permanent fix applied:**
- `desktop/main.py` runs uvicorn as a **subprocess** (not a thread) so pywebview (arm64) and pydantic_core (x86_64) never share a process
- `./setup` script verifies pydantic_core after every pip install and auto-fixes if broken

**When stuck on import errors:**
1. Check the exact error — note which arch it "has" vs "needs"
2. Run `file $(python3 -c "import pydantic_core._pydantic_core as m; print(m.__file__)")` to see .so arch
3. Run `python3 -c "import platform; print(platform.machine())"` to see Python's current arch
4. If they don't match: `pip3 install --force-reinstall pydantic pydantic-core`
5. If the issue is pywebview in same process: use subprocess instead of threading

## Future Work

- [ ] Persistence — save SessionLog to disk (see CLAUDE.md "Add persistence")
- [ ] Online multiplayer — lobby/join codes over internet (not just local network)
- [ ] Table design — user wanted an Indian-inspired design (revisit)
- [ ] PyInstaller packaging — single .app/.exe for distribution
