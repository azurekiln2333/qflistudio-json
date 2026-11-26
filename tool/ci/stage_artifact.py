"""Stage already-packaged cloud outputs without re-zipping Apple bundles."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target")
    parser.add_argument("--source", action="append", required=True)
    parser.add_argument("--signing", required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("cloud-only: artifact staging is restricted to GitHub Actions")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.target):
        parser.error("invalid target")
    output = Path("build/ci-artifacts") / args.target
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("refusing to overwrite an existing staged artifact")
    for item in args.source:
        source = Path(item)
        if not source.is_file() or source.is_symlink():
            raise SystemExit(f"source must be an existing packaged file, not a raw bundle: {source}")
        destination = output / source.name
        if destination.exists():
            raise SystemExit(f"duplicate asset name: {source.name}")
        shutil.copy2(source, destination)
    lock = Path("pubspec.lock")
    facts = {
        "schema": 1,
        "target": args.target,
        "app_commit": os.environ.get("GITHUB_SHA", "unknown"),
        "core_commit": os.environ.get("QFLI_CORE_COMMIT", "unknown"),
        "native_plugin_commit": "697291a27818612ae9dc53d83d4f99fa5887908e",
        "pubspec_lock_sha256": sha256(lock) if lock.is_file() else None,
        "flutter_version": os.environ.get("QFLI_FLUTTER_VERSION", "unknown"),
        "flutter_commit": os.environ.get("QFLI_FLUTTER_COMMIT", "unknown"),
        "flutter_mode": os.environ.get("QFLI_FLUTTER_MODE", "upstream"),
        "host": {"system": platform.system(), "machine": platform.machine(),
                 "image_os": os.environ.get("ImageOS"), "image_version": os.environ.get("ImageVersion")},
        "build_mode": "release",
        "signing": args.signing,
        "device_validation": "none; packaging is not runtime or installed-device acceptance",
        "distribution_warning": "Unsigned, ad-hoc and debug-signed packages are not production-signed releases.",
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "run": f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
    }
    (output / "BUILD_INFO.json").write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    with (output / "SHA256SUMS").open("w", encoding="utf-8", newline="\n") as sums:
        for path in sorted(output.iterdir()):
            if path.name != "SHA256SUMS":
                sums.write(f"{sha256(path)}  {path.name}\n")
    print(f"Staged {args.target} packaged files and provenance; no bundle was flattened")


if __name__ == "__main__":
    main()
