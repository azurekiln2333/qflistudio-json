"""Prepare read-only commit snapshots; this script never launches an SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
from urllib.parse import urljoin
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT.parent / "qfli_studio_core"


def git(directory, *args):
    return subprocess.check_output(["git", *args], cwd=directory).decode().strip()


def oid(directory, value):
    resolved = git(directory, "rev-parse", "--verify", value + "^{commit}")
    if len(resolved) != 40 or any(c not in "0123456789abcdef" for c in resolved):
        raise ValueError("Expected a full commit identity")
    return resolved


def archive(directory, commit, destination, names=()):
    destination.mkdir(parents=True, exist_ok=False)
    bundle_path = destination.parent / (destination.name + ".tar")
    subprocess.run(
        ["git", "archive", "--format=tar", "--output=" + str(bundle_path), commit, *names],
        cwd=directory, check=True,
    )
    with tarfile.open(bundle_path) as bundle:
        bundle.extractall(destination, filter="data")


def metadata(source, destination, replacements):
    for name in (
        ".dart_tool/package_config.json", ".dart_tool/package_graph.json",
        ".flutter-plugins-dependencies", ".flutter-plugins",
    ):
        if (source / name).is_file():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, target)
    target = destination / ".dart_tool/package_config.json"
    config = json.loads(target.read_text(encoding="utf-8"))
    for package in config["packages"]:
        if package["name"] in replacements:
            package["rootUri"] = replacements[package["name"]].as_uri()
        else:
            package["rootUri"] = urljoin((source / ".dart_tool/package_config.json").as_uri(), package["rootUri"])
    target.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def fingerprint(app, core):
    files = {}
    for label, directory in (("app", app), ("core", core)):
        paths = set()
        for name in (
            "lib", "assets", "test", "tool", "vendor/re_editor", "android", "ohos",
            "pubspec.yaml", "pubspec.lock", "analysis_options.yaml",
            ".dart_tool/package_config.json", ".dart_tool/package_graph.json",
            ".flutter-plugins-dependencies", ".flutter-plugins",
        ):
            path = directory / name
            if path.is_dir():
                paths.update(p for p in path.rglob("*") if p.is_file())
            elif path.is_file():
                paths.add(path)
        for path in sorted(paths):
            data = path.read_bytes()
            files[label + "/" + path.relative_to(directory).as_posix()] = {
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            }
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-commit", required=True)
    parser.add_argument("--app-commit", default="HEAD")
    parser.add_argument("--publication-event", required=True, type=int)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--owned-overlay", action="append", default=[])
    args = parser.parse_args()
    if args.capture:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        data = {"capturedUtc": datetime.now(timezone.utc).isoformat(),
                "files": fingerprint(Path(manifest["appSnapshot"]), Path(manifest["coreSnapshot"]))}
        args.capture.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("Captured", len(data["files"]), "snapshot inputs")
        return

    app_commit = oid(ROOT, args.app_commit)
    core_commit = oid(CORE, args.core_commit)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = ROOT / "build" / ("published-json-" + core_commit[:12] + "-" + stamp)
    app = folder / "qfli_json"
    core = folder / "qfli_studio_core"
    archive(CORE, core_commit, core)
    archive(ROOT, app_commit, app, (
        "lib", "assets", "test", "tool", "pubspec.yaml", "pubspec.lock", "analysis_options.yaml",
        "android/app/src/main/AndroidManifest.xml", "ohos/entry/src/main/module.json5",
        "ohos/entry/src/main/ets/entryability/EntryAbility.ets",
    ))
    overlays = {}
    for name in args.owned_overlay:
        relative = Path(name)
        source = (ROOT / relative).resolve()
        if relative.is_absolute() or not source.is_relative_to(ROOT) or relative.parts[0] not in ("lib", "test"):
            raise ValueError("Overlay must be an explicitly owned lib/test path")
        destination = app / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        overlays[relative.as_posix()] = {
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "gitBlob": git(ROOT, "hash-object", "--path=" + relative.as_posix(), str(source)),
        }
    profile = (core / "lib/services/studio_profile.dart").read_text(encoding="utf-8")
    if "supportsSavedWorkspaces" not in profile:
        raise ValueError("Core checkpoint has no standalone named-workspace capability")
    metadata(CORE, core, {"qfli_studio_core": core, "re_editor": core / "vendor/re_editor"})
    metadata(ROOT, app, {"qfli_json": app, "qfli_studio_core": core, "re_editor": core / "vendor/re_editor"})
    manifest = {
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "committed JSON baseline plus explicit owned overlays; exact published core; host only",
        "publicationEvent": args.publication_event,
        "appCommit": app_commit, "appTree": git(ROOT, "rev-parse", app_commit + "^{tree}"),
        "appOverlays": overlays,
        "coreCommit": core_commit, "coreTree": git(CORE, "rev-parse", core_commit + "^{tree}"),
        "appSnapshot": str(app), "coreSnapshot": str(core),
        "originalAppHead": git(ROOT, "rev-parse", "HEAD"),
        "originalCoreHead": git(CORE, "rev-parse", "HEAD"),
        "files": fingerprint(app, core),
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(folder / "manifest.json"), "inputs": len(manifest["files"]),
                      "app": app_commit, "core": core_commit}, indent=2))


if __name__ == "__main__":
    main()
