#!/usr/bin/env python3
"""Update every git repository beneath a root directory.

For each repo found, switch to its primary branch (main/master/develop/...) and
fast-forward pull. Repos that can't be safely updated -- uncommitted changes, no
remote, no detectable primary branch, or a pull that won't fast-forward -- are
skipped and reported. The run never aborts on a single repo and exits 0 even when
some repos are skipped (skips are expected, not failures).

All git calls run non-interactively (GIT_TERMINAL_PROMPT=0, ssh BatchMode) so the
script never blocks waiting for a password or host-key prompt.

Usage:
    python update_repos.py [--root DIR] [--dry-run]

    --root DIR   Base directory to search (default: current working directory).
    --dry-run    Report what would happen; perform no checkout or pull.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Fallback order when origin/HEAD can't tell us the default branch.
FALLBACK_BRANCHES = ("main", "master", "develop")

# Per-command timeout (seconds). Pull may hit the network, so give it room.
TIMEOUT_LOCAL = 30
TIMEOUT_NETWORK = 120

# Non-interactive git environment: fail fast instead of prompting.
GIT_ENV = {
    **os.environ,
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_SSH_COMMAND": "ssh -oBatchMode=yes",
}


def git(repo: Path, *args: str, timeout: int = TIMEOUT_LOCAL) -> subprocess.CompletedProcess:
    """Run a git command in `repo`, capturing output. Never raises on non-zero exit."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=GIT_ENV,
        timeout=timeout,
    )


def first_line(text: str) -> str:
    """First non-empty line of `text`, for compact error reporting."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def discover_repos(root: Path) -> list[Path]:
    """Return git repos under `root`, without descending into a repo's own subdirs."""
    repos: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        if ".git" in dirnames:
            repos.append(Path(dirpath))
            dirnames[:] = []  # prune: don't recurse inside a repo
            continue
        # Skip dotdirs we never care about (perf; avoids huge node_modules-style trees).
        dirnames[:] = [d for d in dirnames if d != ".git"]
    return sorted(repos)


def current_branch(repo: Path) -> str | None:
    """Current branch name, or None if detached HEAD."""
    cp = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if cp.returncode == 0:
        return cp.stdout.strip()
    return None


def detect_primary_branch(repo: Path, has_remote: bool) -> str | None:
    """Detect the repo's primary branch.

    Order: origin/HEAD -> `git remote set-head --auto` then retry -> first existing
    of main/master/develop. Returns the bare branch name (e.g. "main") or None.
    """
    if has_remote:
        primary = _read_origin_head(repo)
        if primary:
            return primary
        # origin/HEAD unset locally; ask the remote, then retry.
        git(repo, "remote", "set-head", "origin", "--auto", timeout=TIMEOUT_NETWORK)
        primary = _read_origin_head(repo)
        if primary:
            return primary

    # Fallback: first known branch name that exists locally or on origin.
    for name in FALLBACK_BRANCHES:
        if _branch_exists(repo, name):
            return name
    return None


def _read_origin_head(repo: Path) -> str | None:
    """Read origin/HEAD -> branch name, or None if unset."""
    cp = git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if cp.returncode == 0:
        ref = cp.stdout.strip()  # e.g. refs/remotes/origin/main
        prefix = "refs/remotes/origin/"
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return None


def _branch_exists(repo: Path, name: str) -> bool:
    """True if `name` exists as a local branch or under origin/."""
    local = git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}")
    if local.returncode == 0:
        return True
    remote = git(repo, "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{name}")
    return remote.returncode == 0


class Result:
    """Outcome for a single repo."""

    def __init__(self, repo: Path, root: Path):
        try:
            self.rel = str(repo.relative_to(root))
        except ValueError:
            self.rel = str(repo)
        self.status = ""   # updated | up-to-date | skipped | would-update
        self.reason = ""   # populated when skipped
        self.branch = ""   # branch acted on, when known


def process_repo(repo: Path, root: Path, dry_run: bool) -> Result:
    """Update one repo; return its Result. Never raises."""
    res = Result(repo, root)

    # a. Dirty working tree -> skip.
    status = git(repo, "status", "--porcelain")
    if status.returncode != 0:
        res.status = "skipped"
        res.reason = f"git status failed: {first_line(status.stderr)}"
        return res
    if status.stdout.strip():
        res.status = "skipped"
        res.reason = "uncommitted changes"
        res.branch = current_branch(repo) or "(detached)"
        return res

    # b. Remote presence.
    remotes = git(repo, "remote")
    has_remote = "origin" in remotes.stdout.split()

    # c. Primary branch.
    primary = detect_primary_branch(repo, has_remote)
    if not primary:
        res.status = "skipped"
        res.reason = "no primary branch found"
        return res
    res.branch = primary

    if not has_remote:
        res.status = "skipped"
        res.reason = "no remote"
        return res

    if dry_run:
        res.status = "would-update"
        return res

    # d. Checkout primary if not already there.
    if current_branch(repo) != primary:
        checkout = git(repo, "checkout", primary)
        if checkout.returncode != 0:
            res.status = "skipped"
            res.reason = f"checkout failed: {first_line(checkout.stderr)}"
            return res

    # e. Fast-forward pull.
    pull = git(repo, "pull", "--ff-only", timeout=TIMEOUT_NETWORK)
    if pull.returncode != 0:
        res.status = "skipped"
        res.reason = f"pull failed: {first_line(pull.stderr) or first_line(pull.stdout)}"
        return res

    if "Already up to date" in pull.stdout:
        res.status = "up-to-date"
    else:
        res.status = "updated"
    return res


def render(results: list[Result], dry_run: bool) -> None:
    """Print an aligned summary table and a counts line."""
    if not results:
        print("No git repositories found.")
        return

    def label(r: Result) -> str:
        if r.status == "skipped":
            return f"skipped ({r.reason})"
        return r.status

    rows = [(label(r), r.branch or "-", r.rel) for r in results]
    w_status = max(len(s) for s, _, _ in rows)
    w_branch = max(len(b) for _, b, _ in rows)

    for status, branch, rel in rows:
        print(f"{status:<{w_status}}  {branch:<{w_branch}}  {rel}")

    updated = sum(1 for r in results if r.status == "updated")
    uptodate = sum(1 for r in results if r.status == "up-to-date")
    would = sum(1 for r in results if r.status == "would-update")
    skipped = sum(1 for r in results if r.status == "skipped")

    print()
    if dry_run:
        print(f"{would} would update, {skipped} skipped (dry run, no changes made)")
    else:
        print(f"{updated} updated, {uptodate} up-to-date, {skipped} skipped")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update all git repos beneath a directory.")
    parser.add_argument("--root", default=".", help="Base directory to search (default: cwd).")
    parser.add_argument("--dry-run", action="store_true", help="Report only; make no changes.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    print(f"Scanning for git repos under {root} ...")
    repos = discover_repos(root)
    print(f"Found {len(repos)} repo(s).\n")

    results: list[Result] = []
    for repo in repos:
        try:
            results.append(process_repo(repo, root, args.dry_run))
        except subprocess.TimeoutExpired:
            r = Result(repo, root)
            r.status = "skipped"
            r.reason = "timed out"
            results.append(r)

    render(results, args.dry_run)
    return 0  # skips are expected; only hard arg errors return non-zero


if __name__ == "__main__":
    sys.exit(main())
