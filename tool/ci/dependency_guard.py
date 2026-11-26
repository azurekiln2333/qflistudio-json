"""Select cloud-only, mode-specific locks and reject dependency drift."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

GIT_COMMIT = "697291a27818612ae9dc53d83d4f99fa5887908e"
STATE = Path("build/ci-state/dependencies.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"dependency-blocked: {message}")


def check_lock(path: Path) -> None:
    if not path.is_file():
        fail(f"missing {path}; run the separate cloud resolve-lock workflow")
    text = path.read_text(encoding="utf-8")
    # Match top-level Pub package blocks, not occurrences in comments or URLs.
    blocks = dict(re.findall(r"(?ms)^  ([a-zA-Z0-9_]+):\n(.*?)(?=^  [a-zA-Z0-9_]+:|\Z)", text))
    for package in ("qfli_git", "flutter_secure_storage", "xterm"):
        if package not in blocks:
            fail(f"stale {path}: missing {package}; resolve and commit the cloud lock first")
    if not re.search(rf"(?m)^      resolved-ref: [\"']?{GIT_COMMIT}[\"']?\s*$", blocks["qfli_git"]):
        fail("qfli_git lock does not bind the reviewed exact native source commit")
    if not re.search(r"(?m)^    source: path\s*$", blocks["xterm"]):
        fail("xterm must resolve to the reviewed sibling core vendor override")


def select(mode: str) -> None:
    root = Path("pubspec.lock")
    official = Path("tool/ci/locks/pubspec-upstream.lock")
    selected = Path(f"tool/ci/locks/pubspec-{mode}.lock")
    if official.exists() and (not root.exists() or digest(root) != digest(official)):
        fail("root pubspec.lock must match the committed upstream lock")
    if not selected.exists():
        # A shared root lock is allowed while both pinned SDKs resolve the same graph.
        # If enforce-lockfile fails on OHOS, generate its mode lock in GitHub only.
        selected = root
    check_lock(selected)
    if selected != root:
        shutil.copyfile(selected, root)
    paths = [root, Path("pubspec.yaml"), Path("../qflistudio-core/pubspec.yaml")]
    for optional in (Path("pubspec_overrides.yaml"), selected):
        if optional.exists() and optional not in paths:
            paths.append(optional)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({
        "mode": mode,
        "selected_lock": str(selected),
        "qfli_git_commit": GIT_COMMIT,
        "files": {str(path): digest(path) for path in paths},
        "absent": [str(path) for path in (Path("pubspec_overrides.yaml"),) if not path.exists()],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Selected {mode} dependency lock; strict resolution required")


def verify() -> None:
    if not STATE.is_file():
        fail("dependency snapshot missing; app-setup must complete before verification")
    state = json.loads(STATE.read_text(encoding="utf-8"))
    for filename, expected in state["files"].items():
        path = Path(filename)
        if not path.is_file() or digest(path) != expected:
            fail(f"silent dependency drift rejected: {filename}")
    for filename in state["absent"]:
        if Path(filename).exists():
            fail(f"unexpected dependency override appeared: {filename}")
    check_lock(Path("pubspec.lock"))
    print("Dependency manifests and selected lock are byte-for-byte unchanged")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("select", "verify"))
    parser.add_argument("--mode", choices=("upstream", "ohos"), default="upstream")
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        fail("this helper may run only in GitHub Actions")
    if args.action == "select":
        select(args.mode)
    else:
        verify()


if __name__ == "__main__":
    main()
