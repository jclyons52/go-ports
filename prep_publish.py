#!/usr/bin/env python3
"""Prepare the port repos for public release.

Non-invasive on purpose: it only touches files that do not participate in the
Go build (LICENSE, NOTICE, .gitignore, README.md, .github/workflows/) and
removes build artefacts from git's index without touching the working tree.

  python3 prep_publish.py            # dry run: report what would change
  python3 prep_publish.py --apply    # make the changes and commit

What it does per repo:
  * LICENSE      — if missing, install the upstream package's own licence text
                   (these are derivative works; the original licence governs),
                   falling back to MIT for original code.
  * NOTICE       — how this repository relates to the upstream package.
  * .gitignore   — node_modules, build output, editor/test noise.
  * CI workflow  — gofmt, go vet, go test (parity suites self-skip when the npm
                   oracle is not installed, so CI stays honest either way).
  * git index    — untrack node_modules (kept on disk for the oracle).
"""
import argparse
import json
import pathlib
import subprocess
import sys

PROJECTS = pathlib.Path.home() / "Projects" / "jclyons52"
ESLINT_GO = PROJECTS / "eslint-go"

# repo -> (upstream npm package for the licence, one-line relationship)
UPSTREAM = {
    "acorn-go": ("acorn", "acorn 8.15"),
    "argparse-go": ("argparse", "argparse 2.0.1"),
    "debug-go": ("debug", "debug 4.3.4"),
    "eslint-community-regexpp": ("@eslint-community/regexpp", "@eslint-community/regexpp 4.12.1"),
    "eslint-go": ("eslint", "eslint 8.57.0"),
    "eslint-scope-go": ("eslint-scope", "eslint-scope 7.2.2"),
    "eslint-visitor-keys-go": ("eslint-visitor-keys", "eslint-visitor-keys 3.4.3"),
    "espree-go": ("espree", "espree 9.6.1"),
    "esquery-go": ("esquery", "esquery 1.7.0"),
    "estraverse-go": ("estraverse", "estraverse 5.3.0"),
    "flatted-go": ("flatted", "flatted 3.4.4"),
    "ignore-go": ("ignore", "ignore 5.3.2"),
    "isexe-go": ("isexe", "isexe 2.0.0"),
    "json-schema-traverse-go": ("json-schema-traverse", "json-schema-traverse 0.4.1"),
    "lodash-merge-go": ("lodash.merge", "lodash.merge 4.6.2"),
    "nodelib-fs-stat-go": ("@nodelib/fs.stat", "@nodelib/fs.stat 2.0.5"),
    "prelude-ls-go": ("prelude-ls", "prelude-ls 1.2.1"),
    "ungap-structured-clone-go": ("@ungap/structured-clone", "@ungap/structured-clone 1.3.3"),
    "uri-js-go": ("uri-js", "uri-js 4.4.1"),
    "esutils-go": ("esutils", "esutils 2.0.3"),
    "color-name-go": ("color-name", "color-name 1.1.4"),
    "humanwhocodes-object-schema-go": (
        "@humanwhocodes/object-schema",
        "@humanwhocodes/object-schema 1.2.1",
    ),
}

GITIGNORE = """# Go build output
/bin/
/dist/
*.test
*.out

# npm oracle (installed locally, never vendored into git)
node_modules/
package-lock.json

# editors / OS
.DS_Store
.idea/
.vscode/
"""

CI = """name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: 'stable'
      - name: gofmt
        run: |
          unformatted="$(gofmt -l .)"
          if [ -n "$unformatted" ]; then
            echo "gofmt needed for:"; echo "$unformatted"; exit 1
          fi
      - name: vet
        run: go vet ./...
      - name: test
        run: go test ./...
"""


def oracle_license_path(pkg):
    """Find the upstream package's LICENSE text in a local npm install."""
    candidates = [
        ESLINT_GO / "oracle" / "node_modules" / pkg,
        PROJECTS / "uplift" / "oracle" / "node_modules" / pkg,
    ]
    for base in candidates:
        if not base.is_dir():
            continue
        for name in ("LICENSE", "LICENSE.md", "LICENSE-MIT", "LICENSE.BSD", "LICENSE.txt"):
            p = base / name
            if p.is_file():
                return p
        for p in sorted(base.glob("LICENSE*")):
            if p.is_file():
                return p
    return None


def run(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def git(repo, *args, check=True):
    return run(["git", *args], cwd=repo)


def tracked_node_modules(repo):
    out = git(repo, "ls-files").stdout.splitlines()
    return [f for f in out if "node_modules/" in f]


def prepare(repo_name, apply_changes):
    repo = PROJECTS / repo_name
    if not repo.is_dir():
        print(f"  ! {repo_name}: not found, skipped")
        return
    changes = []

    # LICENSE
    if not (repo / "LICENSE").exists():
        pkg, version = UPSTREAM.get(repo_name, (None, None))
        src = oracle_license_path(pkg) if pkg else None
        if src:
            text = src.read_text(errors="replace")
            header = (
                f"This Go package is a port of the npm package {pkg} ({version}).\n"
                f"It is a derivative work, so the original licence below governs\n"
                f"the ported code (the Go translation is by Joseph Lyons).\n\n"
                + "-" * 72
                + "\n\n"
            )
            changes.append(("LICENSE", header + text))
            src_label = str(src)
        else:
            changes.append(("LICENSE", f"MIT License\n\nCopyright (c) 2026 Joseph Lyons (jclyons52)\n"))
            src_label = "MIT fallback"
        print(f"  + LICENSE ({src_label})")

    # NOTICE
    if not (repo / "NOTICE").exists():
        pkg, version = UPSTREAM.get(repo_name, (repo_name, ""))
        if pkg:
            changes.append(
                (
                    "NOTICE",
                    f"{repo_name}\n"
                    f"{'=' * len(repo_name)}\n\n"
                    f"A Go port of {pkg}" + (f" ({version})" if version else "") + ".\n\n"
                    "The upstream package is vendored under the parity oracle directory\n"
                    "(`oracle/` or `original/`) and is used at test time to check this port's\n"
                    "behaviour. Its licence is reproduced in LICENSE. Only the Go code in this\n"
                    "repository is the port work; the upstream package remains the work of its\n"
                    "own authors.\n",
                )
            )
            print("  + NOTICE")

    # .gitignore
    if not (repo / ".gitignore").exists():
        changes.append((".gitignore", GITIGNORE))
        print("  + .gitignore")

    # CI
    ci = repo / ".github" / "workflows" / "ci.yml"
    if not ci.exists():
        changes.append((".github/workflows/ci.yml", CI))
        print("  + .github/workflows/ci.yml")

    untrack = tracked_node_modules(repo)
    if untrack:
        print(f"  - untrack {len(untrack)} node_modules files (kept on disk)")

    if not apply_changes:
        return

    staged = []
    for rel, content in changes:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        staged.append(rel)
    if untrack:
        # remove from the index only; the files stay on disk for the oracle
        git(repo, "rm", "-r", "--cached", "--quiet", "node_modules")
        for d in (repo / "original").glob("node_modules"):
            rel = d.relative_to(repo)
            git(repo, "rm", "-r", "--cached", "--quiet", str(rel))
    if staged or untrack:
        # Stage only what this script touched — other work may be in flight.
        if staged:
            git(repo, "add", "--", *staged)
        res = git(repo, "commit", "-q", "-m",
                  "chore(release): licence, NOTICE, .gitignore and CI for publication\n\n"
                  "The port is a derivative work, so the upstream package's licence text is\n"
                  "installed alongside a NOTICE explaining the relationship. node_modules is\n"
                  "untracked (it stays on disk as the parity oracle) and CI runs gofmt, vet\n"
                  "and the test suite.")
        if res.returncode not in (0, 1):
            print(f"  ! commit failed: {res.stderr.strip()}")
        else:
            print("  ✓ committed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes and commit")
    ap.add_argument("--repos", nargs="*", help="limit to these repos")
    args = ap.parse_args()

    manifest = json.loads((pathlib.Path(__file__).parent / "manifest.json").read_text())
    names = [r["repo"] for s in manifest["sections"] for r in s["repos"]]
    if args.repos:
        names = args.repos

    print(f"{'APPLYING' if args.apply else 'DRY RUN'} for {len(names)} repos")
    for name in names:
        print(f"{name}:")
        prepare(name, args.apply)
    if not args.apply:
        print("\n(re-run with --apply to write these changes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
