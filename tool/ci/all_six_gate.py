"""Require six exact-run installers and six verified native input archives."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from publish_release import TARGETS, staged_files

REQUIRED = {
    "windows-x64": ("-windows-x64.zip", "-windows-x64-setup.exe"),
    "linux-x64": ("-linux-x64.tar.gz", "-linux-amd64.deb"),
    "macos-universal": ("-macos-universal.tar.gz", "-macos-universal.dmg"),
    "ios-arm64": ("-ios-arm64-unsigned.ipa",),
    "android-multiabi": ("-android-armeabi-v7a-debug-signed.apk", "-android-arm64-v8a-debug-signed.apk",
                         "-android-x86_64-debug-signed.apk", "-android-universal-debug-signed.aab"),
    "ohos-arm64": ("-ohos-arm64-unsigned.hap",),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="release-inputs")
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("cloud-only: all-six gate must run on GitHub Actions")
    root = Path(args.root)
    identity = (os.environ["GITHUB_SHA"], os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"])
    for target in TARGETS:
        files = staged_files(root, f"installer-{target}", *identity)
        names = [Path(row["path"]).name for row in files]
        for ending in REQUIRED[target]:
            if sum(name.endswith(ending) for name in names) != 1:
                raise SystemExit(f"all-six-blocked: missing/duplicate {target} package ending {ending}")
        staged_files(root, f"native-{target}", *identity)
        evidence_path = root / f"native-{target}" / "verify.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if (evidence.get("status"), evidence.get("appCommit"), evidence.get("runId"), evidence.get("runAttempt")) != (
                "verified-packaging", *identity):
            raise SystemExit(f"all-six-blocked: missing exact-run native package verification for {target}")
        if not (root / f"native-{target}" / "native-inputs.tar.gz").is_file():
            raise SystemExit(f"all-six-blocked: missing durable native input payload for {target}")
    print("All six exact-run package/native gates passed; no runtime/device or production-signing claim")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## All-six packaging gate\n\nAll six platforms supplied exact-run packages, checksums "
                         "and native verification evidence. Unsigned/debug-signed limitations remain. "
                         "Native input archives become durable only after immutable release publication.\n")


if __name__ == "__main__":
    main()
