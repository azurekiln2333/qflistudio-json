"""Publish verified staged artifacts to a new immutable GitHub release.

Only the release job has write permission. Existing releases/assets are never
reused, edited or clobbered. Transport artifacts are not durable distribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.parse

TARGETS = ("windows-x64", "linux-x64", "macos-universal", "ios-arm64", "android-multiabi", "ohos-arm64")
CORE_COMMIT = "8e031313ffc8d531c5a6b4d131f721f35da04c86"


def fail(message: str) -> None:
    raise SystemExit(f"release-blocked: {message}")


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def api(endpoint: str, *, method: str = "GET", data: dict | None = None, upload: Path | None = None) -> dict:
    command = ["gh", "api", "--method", method, "-H", "X-GitHub-Api-Version: 2022-11-28", endpoint]
    if upload:
        command += ["-H", "Content-Type: application/octet-stream", "--input", str(upload)]
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    elif data is not None:
        command += ["-H", "Content-Type: application/json", "--input", "-"]
        result = subprocess.run(command, input=json.dumps(data).encode(), check=True, stdout=subprocess.PIPE)
    else:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def staged_files(root: Path, label: str, commit: str, run_id: str, attempt: str) -> list[dict]:
    directory = root / label
    if not directory.is_dir() or directory.is_symlink():
        fail(f"missing staged artifact {label}")
    info_path = directory / "BUILD_INFO.json"
    sums = directory / "SHA256SUMS"
    if not info_path.is_file() or not sums.is_file():
        fail(f"missing staged provenance/checksums for {label}")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    if (info.get("app_commit"), info.get("core_commit"), info.get("run_id"), info.get("run_attempt")) != (
            commit, CORE_COMMIT, run_id, attempt):
        fail(f"source/run identity mismatch for {label}")
    expected = {}
    for line in sums.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._+-]*)", line)
        if not match or match.group(2) in expected:
            fail(f"invalid checksum member for {label}")
        expected[match.group(2)] = match.group(1)
    actual = {path.name for path in directory.iterdir() if path.name != "SHA256SUMS"}
    if actual != expected.keys():
        fail(f"unexpected/missing files in {label}")
    rows = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.is_symlink():
            fail(f"unsafe asset in {label}")
        value = sha256(path)
        if path.name != "SHA256SUMS" and expected[path.name] != value:
            fail(f"checksum mismatch in {label}")
        rows.append({"path": str(path), "asset_name": f"{label}--{path.name}", "sha256": value,
                     "bytes": path.stat().st_size, "target": label})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="release-inputs")
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        fail("publication is restricted to GitHub Actions")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    commit = os.environ.get("GITHUB_SHA", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        fail("invalid repository or commit identity")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        fail("only the reviewed main branch can publish")
    # Repository immutability must be enabled by an administrator in advance.
    # The setting endpoint requires administration:read, which GITHUB_TOKEN must
    # not receive. We require immutable=true on the actual published release below.
    root = Path(args.root)
    files = []
    for target in TARGETS:
        files += staged_files(root, f"installer-{target}", commit, run_id, attempt)
        files += staged_files(root, f"native-{target}", commit, run_id, attempt)
    if len({row["asset_name"] for row in files}) != len(files):
        fail("duplicate release asset name")
    tag = f"cloud-{commit[:12]}-{run_id}-{attempt}"
    # Reject an existing release before creating anything; do not use latest/name fallbacks.
    releases = api(f"repos/{repository}/releases?per_page=100")
    if any(release.get("tag_name") == tag for release in releases):
        fail("release tag already exists; no overwrite is permitted")
    body = (
        f"Cloud packaging evidence for `{commit}`. Core `{CORE_COMMIT}`.\n\n"
        "Six platform packaging/native gates passed in this exact run; no installed-device acceptance is implied.\n\n"
        "Windows installer/ZIP, Linux tar/deb and macOS tar/DMG are unsigned or ad-hoc. "
        "Android APK/AAB use a debug key. iOS IPA and OHOS HAP are unsigned. "
        "These are not production-signed or app-store releases.\n\n"
        "Native input archives are durable source-input evidence, distinct from 3-day diagnostics. "
        "SHA256SUMS and RELEASE_MANIFEST.json bind all published assets.\n"
    )
    release = api(f"repos/{repository}/releases", method="POST", data={
        "tag_name": tag, "target_commitish": commit, "name": f"QFLIJson cloud packages {commit[:12]}",
        "body": body, "draft": True, "prerelease": True, "generate_release_notes": False,
    })
    release_id = release["id"]
    endpoint = release["upload_url"].split("{", 1)[0]
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https" or parsed.hostname != "uploads.github.com":
        fail("unexpected release asset upload host")
    uploaded = []
    with tempfile.TemporaryDirectory(prefix="qfli-release-") as directory:
        scratch = Path(directory)
        manifest = scratch / "RELEASE_MANIFEST.json"
        manifest.write_text(json.dumps({"schema": 1, "app_commit": commit, "core_commit": CORE_COMMIT,
            "run_id": run_id, "run_attempt": attempt, "release_id": release_id,
            "assets": [{k: v for k, v in row.items() if k != "path"} for row in files]}, indent=2) + "\n", encoding="utf-8")
        checksums = scratch / "SHA256SUMS"
        checksums.write_text("".join(f"{row['sha256']}  {row['asset_name']}\n" for row in files)
                             + f"{sha256(manifest)}  RELEASE_MANIFEST.json\n", encoding="utf-8")
        files += [{"path": str(path), "asset_name": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
                  for path in (manifest, checksums)]
        for row in files:
            asset = api(endpoint + "?name=" + urllib.parse.quote(row["asset_name"], safe=""),
                        method="POST", upload=Path(row["path"]))
            if asset.get("state") != "uploaded" or asset.get("size") != row["bytes"]:
                fail("release asset upload was not confirmed; draft retained for investigation")
            if asset.get("digest") != "sha256:" + row["sha256"]:
                fail("GitHub release asset digest mismatch or missing; draft retained")
            uploaded.append(asset["id"])
    # Publish only after complete upload and server-side asset identity confirmation.
    api(f"repos/{repository}/releases/{release_id}", method="PATCH", data={"draft": False})
    final = api(f"repos/{repository}/releases/{release_id}")
    if final.get("draft") or final.get("immutable") is not True:
        fail("published release immutability was not confirmed; do not claim durable immutable success")
    if {asset["id"] for asset in final.get("assets", [])} != set(uploaded):
        fail("published immutable asset inventory differs from this run")
    tag_object = api(f"repos/{repository}/git/ref/tags/{tag}")["object"]
    for _ in range(4):
        if tag_object["type"] != "tag":
            break
        tag_object = api(f"repos/{repository}/git/tags/{tag_object['sha']}")["object"]
    if tag_object.get("type") != "commit" or tag_object.get("sha") != commit:
        fail("immutable release tag does not identify the verified app commit")
    summary = Path(os.environ["GITHUB_STEP_SUMMARY"])
    with summary.open("a", encoding="utf-8") as stream:
        stream.write(f"## Immutable cloud package release\n\n{final['html_url']}\n\n"
                     f"App `{commit}`; release ID `{release_id}`; {len(uploaded)} confirmed assets.\n"
                     "Unsigned/debug-signed limitations remain; no device acceptance is claimed.\n")


if __name__ == "__main__":
    main()
