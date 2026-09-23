#!/usr/bin/env python3
"""Create the public GitHub repos for the ports, push them, and tag v0.1.0.

  python3 publish.py            # dry run: show what would happen
  python3 publish.py --yes      # actually create/push/tag
  python3 publish.py --yes --repos acorn-go espree-go

Order matters: a repo is published before anything that depends on it, so the
module versions its dependents require already exist.
"""
import argparse
import json
import pathlib
import subprocess
import sys

PROJECTS = pathlib.Path.home() / "Projects" / "jclyons52"
OWNER = "jclyons52"
TAG = "v0.1.0"

# Publish order (dependencies first).
ORDER = [
    # no intra-project dependencies
    "acorn-go",
    "estraverse-go",
    "eslint-scope-go",
    "esutils-go",
    "color-name-go",
    "debug-go",
    "flatted-go",
    "ignore-go",
    "isexe-go",
    "json-schema-traverse-go",
    "lodash-merge-go",
    "nodelib-fs-stat-go",
    "prelude-ls-go",
    "ungap-structured-clone-go",
    "uri-js-go",
    "argparse-go",
    "eslint-community-regexpp",
    "eslint-visitor-keys-go",
    "humanwhocodes-object-schema-go",
    # depend on the above
    "espree-go",
    "esquery-go",
    # the composition target, depends on several of the above
    "eslint-go",
    # tooling
    "uplift",
    "ts-go-morph",
    "go-gqlcodegen",
    "go-typewryter",
    # the showcase site
    "go-ports",
]

DESCRIPTIONS = {
    "eslint-go": "ESLint's Linter pipeline in Go: parses with a Go parser, runs real ESLint rules, byte-identical CLI output to eslint 8.57",
    "go-ports": "Go ports of JavaScript tooling, verified against the npm originals — project index and methodology",
    "acorn-go": "Go port of acorn (JavaScript parser), verified against the npm original",
    "espree-go": "Go port of espree (the ESLint parser), verified against the npm original",
    "eslint-scope-go": "Go port of eslint-scope (scope analysis), verified against the npm original",
    "estraverse-go": "Go port of estraverse (ESTree traversal), verified against the npm original",
    "esquery-go": "Go port of esquery (the ESLint selector engine), verified against the npm original",
    "esutils-go": "Go port of esutils (AST/code/keyword helpers), verified against the npm original",
    "uplift": "JS→Go uplift toolchain: measure, registry, scaffold, spec, transpile — the pipeline behind these ports",
    "ts-go-morph": "Go port of ts-morph (TypeScript AST manipulation)",
    "go-gqlcodegen": "Native Go port of GraphQL Code Generator — byte-identical TypeScript output, ~90x faster cold start",
    "go-typewryter": "Go port of the typewryter CLI",
}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def remote_url(repo):
    res = git(repo, "remote", "get-url", "origin")
    return res.stdout.strip() if res.returncode == 0 else ""


def plan(repo_name):
    repo = PROJECTS / repo_name
    if not repo.is_dir():
        return f"  ! {repo_name}: directory missing"
    names = [l for l in git(repo, "ls-files").stdout.splitlines() if "node_modules/" in l]
    dirty = git(repo, "status", "--porcelain").stdout.strip()
    notes = []
    if names:
        notes.append(f"{len(names)} node_modules files still tracked")
    if dirty:
        notes.append("uncommitted changes")
    remote = remote_url(repo)
    if not remote:
        action = f"create {OWNER}/{repo_name} (public), push, tag {TAG}"
    else:
        action = f"push to {remote}"
        if not gh("repo", "view", f"{OWNER}/{repo_name}", "--json", "visibility").stdout.strip():
            action += " (repo not visible to gh?)"
    suffix = f" [{'; '.join(notes)}]" if notes else ""
    return f"  {repo_name}: {action}{suffix}"


def publish(repo_name):
    repo = PROJECTS / repo_name
    if not repo.is_dir():
        print(f"  ! {repo_name}: missing")
        return False
    remote = remote_url(repo)
    desc = DESCRIPTIONS.get(repo_name, f"Go port of the npm package {repo_name}")
    if not remote:
        res = gh(
            "repo", "create", f"{OWNER}/{repo_name}",
            "--public", f"--source={repo}", "--remote=origin", "--push",
            "--description", desc,
        )
        if res.returncode != 0:
            print(f"  ! create failed: {res.stderr.strip()}")
            return False
        print(f"  ✓ created and pushed {OWNER}/{repo_name}")
    else:
        res = git(repo, "push", "origin", "HEAD:main")
        if res.returncode != 0 and "up-to-date" not in (res.stderr + res.stdout):
            res2 = git(repo, "push", "-u", "origin", "main")
            if res2.returncode != 0:
                print(f"  ! push failed: {res.stderr.strip()}{res2.stderr.strip()}")
                return False
        # make sure the repo is public if it exists in another visibility
        view = gh("repo", "view", f"{OWNER}/{repo_name}", "--json", "visibility")
        if '"visibility":"PRIVATE"' in view.stdout.replace(" ", ""):
            res = gh("repo", "edit", f"{OWNER}/{repo_name}", "--visibility", "public",
                     "--accept-visibility-change-consequences")
            if res.returncode != 0:
                print(f"  ! visibility change failed: {res.stderr.strip()}")
                return False
            print(f"  ✓ made public {OWNER}/{repo_name}")
        res = gh("repo", "edit", f"{OWNER}/{repo_name}", "--description", desc)
        print(f"  ✓ pushed {OWNER}/{repo_name}")

    # tag
    git(repo, "tag", "-f", TAG)
    res = git(repo, "push", "-f", "origin", TAG)
    if res.returncode != 0:
        print(f"  ! tag push failed: {res.stderr.strip()}")
    else:
        print(f"  ✓ tagged {TAG}")
    return True


def enable_pages(repo_name):
    repo = PROJECTS / repo_name
    res = gh("api", f"repos/{OWNER}/{repo_name}/pages", "-X", "POST",
             "-f", "source[branch]=main", "-f", "source[path]=/")
    if res.returncode == 0:
        print(f"  ✓ Pages enabled for {repo_name} -> https://{OWNER}.github.io/{repo_name}/")
    elif "already" in (res.stderr + res.stdout).lower() or "409" in (res.stderr + res.stdout):
        res = gh("api", f"repos/{OWNER}/{repo_name}/pages", "-X", "PUT",
                 "-f", "source[branch]=main", "-f", "source[path]=/")
        print(f"  ✓ Pages updated for {repo_name}")
    else:
        print(f"  ! Pages failed: {res.stderr.strip() or res.stdout.strip()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="do it (default is a dry run)")
    ap.add_argument("--repos", nargs="*")
    args = ap.parse_args()

    names = args.repos or ORDER
    if not args.yes:
        print(f"DRY RUN — would publish {len(names)} repos in this order:")
        for n in names:
            print(plan(n))
        print("\n(re-run with --yes to create/push/tag)")
        return 0

    failures = []
    for n in names:
        print(f"{n}:")
        if not publish(n):
            failures.append(n)
    if "go-ports" in names and "go-ports" not in failures:
        enable_pages("go-ports")

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print(f"published {len(names)} repos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
