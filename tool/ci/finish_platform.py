"""Verify native packages, lock drift and stage platform deliverables in GitHub."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def call(*args: str) -> None:
    subprocess.run([sys.executable, *args], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=("windows", "linux", "macos", "ios", "android", "ohos"))
    parser.add_argument("--target", required=True)
    parser.add_argument("--signing", required=True)
    parser.add_argument("--package", action="append", default=[])
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("cloud-only: package finalization requires GitHub Actions")
    manifest = Path("build/ci-packages/package-manifest.json")
    if args.package:
        runtime_packages = args.package
        assets = [Path(path) for path in args.package]
    else:
        if not manifest.is_file():
            raise SystemExit("missing package-manifest.json")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("platform") != args.platform or not data.get("runtime_packages"):
            raise SystemExit("package manifest platform or runtime payload list is invalid")
        runtime_packages = data["runtime_packages"]
        assets = sorted(manifest.parent.iterdir())
    if not Path("tool/ci/native_dependencies.py").is_file():
        raise SystemExit("missing-native-contract: native verifier helper is absent")
    # The native consumer normalizes macos-universal to its macos evidence directory.
    target = args.platform
    command = ["tool/ci/native_dependencies.py", "--target", target, "--phase", "verify"]
    for package in runtime_packages:
        if not isinstance(package, str) or not Path(package).exists():
            raise SystemExit("runtime payload archive is missing")
        command += ["--package", package]
    call("tool/ci/run_logged.py", "native-verify", "--", sys.executable, *command)
    call("tool/ci/dependency_guard.py", "verify")
    # Only an already-verified package can reach the installer artifact directory.
    stage = ["tool/ci/stage_artifact.py", args.target, "--signing", args.signing]
    for path in assets:
        if not path.is_file() or path.is_symlink():
            raise SystemExit("non-file package asset rejected")
        stage += ["--source", str(path)]
    for name in ("prepare.json", "verify.json"):
        evidence = Path("build/ci-native") / target / name
        if evidence.is_file():
            # Unique provenance names avoid confusing native package coverage with metadata.
            destination = Path("build/ci-packages") / f"native-{name}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(evidence.read_bytes())
            stage += ["--source", str(destination)]
    call(*stage)
    native = Path("build/ci-native") / target / "native-inputs.tar.gz"
    if not native.is_file():
        raise SystemExit("missing-native-contract: durable native input archive was not produced")
    call("tool/ci/stage_artifact.py", f"native-{args.target}", "--signing", "source-input-evidence",
         "--source", str(native),
         "--source", str(native.parent / "prepare.json"),
         "--source", str(native.parent / "verify.json"))


if __name__ == "__main__":
    main()
