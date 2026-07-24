#!/usr/bin/env python3
"""Diff this parser against a reference YAML implementation.

Every file in tests/conformance is parsed twice — once by tests/dump.milo, once
by ruamel.yaml in YAML 1.2 mode — and the two results are compared as data, not
as text, so float spelling and key order never produce false failures.

    pip install ruamel.yaml
    python3 scripts/oracle.py [--milo /path/to/milo]
"""

import argparse
import io
import json
import math
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = sorted((ROOT / "tests" / "conformance").glob("*.yaml"))


def reference(path):
    from ruamel.yaml import YAML

    yaml = YAML(typ="safe", pure=True)
    return yaml.load(io.StringIO(path.read_text()))


def ours(milo, path):
    out = subprocess.run(
        [milo, "run", str(ROOT / "tests" / "dump.milo"), str(path)],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout)
    return json.loads(out.stdout.strip().splitlines()[-1])


def equal(a, b):
    """Compare parsed documents. Numbers compare by value: JSON has no way to
    say 1.5e3 and 1500.0 are the same number, but YAML does."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0) or a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--milo", default="milo")
    args = ap.parse_args()

    failures = 0
    for case in CASES:
        try:
            mine = ours(args.milo, case)
        except Exception as e:  # noqa: BLE001 — the message is the report
            print(f"FAIL {case.name}: {e}")
            failures += 1
            continue
        want = reference(case)
        if equal(mine, want):
            print(f"ok   {case.name}")
        else:
            failures += 1
            print(f"FAIL {case.name}")
            print(f"  ours: {json.dumps(mine, sort_keys=True)}")
            print(f"  ref : {json.dumps(want, sort_keys=True, default=str)}")

    print(f"\n{len(CASES) - failures}/{len(CASES)} cases match the reference parser")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
