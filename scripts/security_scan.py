#!/usr/bin/env python3
"""
Dependency security scanner for the Judgement project.
Checks Python (pip-audit) and Node (npm audit) dependencies for known vulnerabilities.
Exit code 0 = clean, 1 = vulnerabilities found, 2 = scanner error.
"""

import subprocess
import sys
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=120
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out: {' '.join(cmd)}"


def check_pip_audit():
    print("=" * 60)
    print("PYTHON DEPENDENCY SCAN (pip-audit)")
    print("=" * 60)

    requirements = BACKEND_DIR / "requirements.txt"
    if not requirements.exists():
        print("  [SKIP] No requirements.txt found")
        return 0

    # Check if pip-audit is available
    code, _, _ = run_cmd([sys.executable, "-m", "pip_audit", "--version"])
    if code != 0:
        print("  Installing pip-audit...")
        run_cmd([sys.executable, "-m", "pip", "install", "pip-audit"])

    code, stdout, stderr = run_cmd(
        [sys.executable, "-m", "pip_audit", "-r", str(requirements), "--format", "json"]
    )

    if code == -1:
        print(f"  [ERROR] {stderr}")
        return 2

    if code == 0:
        print("  [PASS] No known vulnerabilities found")
        return 0

    # Parse and display vulnerabilities
    try:
        vulns = json.loads(stdout)
        if isinstance(vulns, dict):
            vulns = vulns.get("dependencies", [])
        found = 0
        for dep in vulns:
            for vuln in dep.get("vulns", []):
                found += 1
                print(f"  [VULN] {dep['name']} {dep.get('version', '?')}: {vuln.get('id', '?')} - {vuln.get('description', 'No description')[:100]}")
                fix = vuln.get('fix_versions', [])
                if fix:
                    print(f"         Fix: upgrade to {', '.join(fix)}")
        if found:
            print(f"\n  [FAIL] {found} vulnerability(ies) found")
            return 1
    except (json.JSONDecodeError, KeyError):
        # Fallback: show raw output
        print(f"  [WARN] Could not parse output:\n{stdout}\n{stderr}")
        return 1

    return 0


def check_npm_audit():
    print("\n" + "=" * 60)
    print("NODE DEPENDENCY SCAN (npm audit)")
    print("=" * 60)

    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        print("  [SKIP] No frontend/package.json found (frontend not yet set up)")
        return 0

    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("  [SKIP] node_modules not installed, run npm install first")
        return 0

    code, stdout, stderr = run_cmd(
        ["npm", "audit", "--json"], cwd=str(FRONTEND_DIR)
    )

    if code == -1:
        print(f"  [ERROR] {stderr}")
        return 2

    try:
        audit = json.loads(stdout)
        total = audit.get("metadata", {}).get("vulnerabilities", {})
        critical = total.get("critical", 0)
        high = total.get("high", 0)
        moderate = total.get("moderate", 0)
        low = total.get("low", 0)

        if critical + high + moderate + low == 0:
            print("  [PASS] No known vulnerabilities found")
            return 0

        print(f"  Critical: {critical}, High: {high}, Moderate: {moderate}, Low: {low}")

        # Show details for critical and high
        for name, advisory in audit.get("vulnerabilities", {}).items():
            severity = advisory.get("severity", "")
            if severity in ("critical", "high"):
                print(f"  [VULN] {name} ({severity}): {advisory.get('title', 'No title')}")
                fix = advisory.get("fixAvailable")
                if fix and isinstance(fix, dict):
                    print(f"         Fix: {fix.get('name', '?')}@{fix.get('version', '?')}")

        if critical > 0 or high > 0:
            print(f"\n  [FAIL] {critical + high} critical/high vulnerability(ies)")
            return 1
        else:
            print(f"\n  [WARN] {moderate + low} moderate/low vulnerability(ies)")
            return 0

    except (json.JSONDecodeError, KeyError):
        print(f"  [WARN] Could not parse npm audit output:\n{stderr}")
        return 1


def check_lockfile_integrity():
    print("\n" + "=" * 60)
    print("LOCKFILE INTEGRITY CHECK")
    print("=" * 60)

    package_lock = FRONTEND_DIR / "package-lock.json"
    if package_lock.exists():
        code, _, stderr = run_cmd(
            ["npm", "ci", "--dry-run"], cwd=str(FRONTEND_DIR)
        )
        if code == 0:
            print("  [PASS] package-lock.json is consistent")
        elif code == -1:
            print(f"  [SKIP] {stderr}")
        else:
            print("  [WARN] package-lock.json may be out of sync with package.json")
    else:
        print("  [SKIP] No package-lock.json found")

    return 0


def main():
    print(f"Security Scan — {PROJECT_ROOT.name}")
    print(f"Python: {sys.version.split()[0]}")
    print()

    results = []
    results.append(("Python deps", check_pip_audit()))
    results.append(("Node deps", check_npm_audit()))
    results.append(("Lockfile integrity", check_lockfile_integrity()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    exit_code = 0
    for name, code in results:
        status = "PASS" if code == 0 else ("FAIL" if code == 1 else "ERROR")
        print(f"  {name}: {status}")
        if code > exit_code:
            exit_code = code

    print()
    if exit_code == 0:
        print("All checks passed.")
    else:
        print("Issues found — review output above.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
