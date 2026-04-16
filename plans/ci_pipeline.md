# CI pipeline — prereq for the mascot feature (and everything after)

## Why this comes first

Today the only GitHub Actions workflow is `release.yml`, which runs **only on tag push**. There is no CI that runs tests on pull requests or on `main`. For a cross-cutting feature like the mascot system — new backend module + new WebSocket event types + frontend reducer changes — we want a green-tick gate on every PR before merging. Cost is tiny (~40 lines of YAML, one GitHub Actions minute per push); benefit is that every subsequent feature lands on a protected branch.

The CI pipeline itself is architecturally non-trivial: it enforces the "game/ and ai/ are pure logic" layering by catching any regression that accidentally imports `api/` or adds I/O to pure modules. So it has its own "solid architecture" value beyond just running tests.

## Scope

One new workflow file, `.github/workflows/test.yml`. No changes to existing `release.yml`.

Triggers:
- `push` to any branch
- `pull_request` targeting `main`

Two jobs, each matrixed across **Ubuntu + Windows** (= 4 check cells total on every PR).

### Job 1 — `backend` (matrix: ubuntu-latest, windows-latest)

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, windows-latest]
runs-on: ${{ matrix.os }}
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5 (python-version: '3.11', cache: 'pip')
  - pip install -r backend/requirements.txt
  - python -m pytest backend/tests/ -v --tb=short
```

Python 3.11 matches the release workflow. `fail-fast: false` so a Windows-only failure doesn't hide the Ubuntu result (and vice versa). pywebview is not a test dep, so the backend test job runs on hosted Windows runners without the GTK/WebKit headaches that keep Linux out of `release.yml`.

### Job 2 — `frontend` (matrix: ubuntu-latest, windows-latest)

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, windows-latest]
runs-on: ${{ matrix.os }}
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-node@v4 (node-version: '20', cache: 'npm', cache-dependency-path: frontend/package-lock.json)
  - cd frontend && npm ci
  # npm run lint intentionally NOT gated in the initial PR — see "lint deferred" below
  - cd frontend && npm run build        # tsc -b && vite build — covers typecheck + build
```

`npm run build` runs `tsc -b` first, so this catches any TypeScript errors (including `erasableSyntaxOnly` violations, which are an easy thing to break when adding new types). Matrixing on Windows catches path-separator bugs (`frontend/dist` vs `frontend\dist` come up in Vite plugin paths) before they hit the Windows release build.

**Why lint is deferred:** `npm run lint` currently reports 8 pre-existing errors on `main` (react-refresh / react-hooks rules). Adding it to CI today would immediately fail the first run and defeat the green-baseline purpose of this PR. Lint gets wired in as a gate in a follow-up PR once the baseline is clean.

### Why Windows in CI

The project already ships a Windows desktop bundle via `release.yml`. Running backend tests + frontend build on Windows on every PR catches:

- **Asyncio / websockets platform quirks** — Windows uses a different event loop (ProactorEventLoop) by default. Past releases have shipped with Windows-only regressions that weren't caught until a user ran the bundled `.exe`.
- **Path separator bugs** — PyInstaller's `--add-data` uses `:` on Unix and `;` on Windows, `Path` objects stringify differently, and `os.path.join` hides bugs that break on the wrong OS. Tests importing modules with path-manipulation catch these.
- **Line-ending and encoding mismatches** — a test that accidentally depends on `\n` vs `\r\n` can pass on Ubuntu and fail on Windows; we want to know on PR, not at release.

Cost: doubles the check count and ~doubles the minutes spent per PR, but GitHub Actions is free for public repos and Windows minutes bill at 2× so for a private repo we'd want to revisit. Currently: acceptable.

## What we explicitly DO NOT do in this PR

- **No coverage gate.** Let's measure first, set a threshold later.
- **No matrix across Python versions.** Target Python 3.9 locally (per CLAUDE.md), Python 3.11 in CI — one version each is enough. Bridging happens in the release workflow, not here.
- **No macOS in the test matrix.** The release workflow already runs PyInstaller on macOS for every tagged release, which exercises the backend under macOS. Adding macOS to test CI would triple the matrix for modest additional coverage. Revisit if we ever ship a macOS-only test regression.
- **No frontend unit tests yet.** We don't have Vitest installed. Adding Vitest is part of PR 4 of the mascot plan if we want component tests.
- **No dependency caching beyond what `setup-python` / `setup-node` provide.** pip + npm caches are good enough.
- **No branch protection rule changes.** That's a separate GitHub settings change the maintainer applies after the green-tick is proven.
- **No `pip-audit` / `npm audit`.** Security scan already exists as `scripts/security_scan.py` and is run manually before releases; turning it into a gating CI job is a separate question (noisy on transitive deps).

## Files touched

| File | Change |
|------|--------|
| `.github/workflows/test.yml` | **NEW** — the workflow described above |
| `README.md` | Tiny update: add a "CI status" badge near the top |

Nothing else.

## Validation checklist

Before merging the CI PR itself:

1. Push the branch. Confirm **all 4 check cells** (backend × {ubuntu, windows}, frontend × {ubuntu, windows}) run green.
2. Deliberately break a backend test, push, confirm **both** backend cells (Ubuntu + Windows) fail red, and both frontend cells stay green. Revert, push, confirm green.
3. Deliberately break `erasableSyntaxOnly` (e.g. add a TS `enum` somewhere), push, confirm **both** frontend cells fail red, and both backend cells stay green. Revert, push, confirm green.
4. Open a PR against `main` from the feature branch. Confirm all 4 check rows appear on the PR "Checks" tab.
5. **Branch protection is a separate maintainer action** (GitHub Settings → Branches → main): once the checks are proven stable, the maintainer marks all 4 as required. This is out of scope for the CI PR itself.

## Order of work

This is a single small PR. No sub-PRs. Estimated footprint: one YAML file, one README line.

## Future / after this lands

- **Frontend lint as a gate.** Clean up the 8 pre-existing ESLint errors on `main`, then add `npm run lint` to the frontend job.
- **Frontend unit tests.** The frontend has no test runner today. Once this pipeline is green, add Vitest + @testing-library/react in a follow-up PR so the frontend job runs `npm test` alongside `lint` + `build`. Backend already has 210+ pytest tests; the long-term goal is parity so both halves have executable test coverage wired into CI.
- **Branch protection.** After a few PRs validate the green-gate behaviour, the maintainer should mark all 4 check cells as **required** on `main` via GitHub Settings → Branches.
- **Coverage reporting.** Once both halves have tests, add coverage + a reasonable threshold (don't gate on 100%, but catch regressions below baseline).

## Open questions

- **Required vs optional checks.** After the CI lands, maintainer should mark `backend` and `frontend` as **required checks** in GitHub's branch protection settings for `main`. We can't do that from a PR; it's a setting change.
- **CI runner minutes budget.** Public repo → free GitHub Actions minutes for Ubuntu. If the repo is made private later, this costs minutes. Currently no concern.
- **Windows runner for the backend?** Tempting — it would catch asyncio/websockets quirks that only surface on Windows (we already hit a PATH issue with launchd on macOS). Default: skip for now; the release workflow's Windows build already executes enough of the backend to catch egregious Windows-only breakage. Revisit if we ship a real Windows bug.
