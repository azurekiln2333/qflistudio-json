"""Inspect one isolated debug HAP without invoking a build or device tool."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urljoin, urlparse
import zipfile


LIVE_APP = Path(__file__).resolve().parents[2]
LIVE_CORE = LIVE_APP.parent / "qfli_studio_core"
KERNEL_ENTRY = "resources/rawfile/flutter_assets/kernel_blob.bin"
CONTENT_NAMES = ("tutorials.json", "examples.json", "catalog_audit.json")


class BlockedInspection(Exception):
    """The available evidence cannot safely identify the compiled sources."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_key(path):
    return os.path.normcase(str(Path(path).resolve()))


def inside(path, directory):
    try:
        return os.path.commonpath((path_key(path), path_key(directory))) == path_key(directory)
    except ValueError:
        return False


def parse_depfile(path):
    """Parse Flutter's escaped Make depfile grammar, including Windows paths.

    Flutter doubles Windows backslashes and escapes spaces. A drive colon is
    not followed by whitespace; the sole unescaped ': ' separates the lists.
    Reject unknown escapes/relative paths instead of guessing their meaning.
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    if not text.strip() or "\x00" in text:
        raise BlockedInspection(f"Empty or binary depfile: {path}")
    text = re.sub(r"\\\r?\n", "", text)
    separators = []
    index = 0
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == ":" and index + 1 < len(text) and text[index + 1].isspace():
            separators.append(index)
        index += 1
    if len(separators) != 1:
        raise BlockedInspection(f"Ambiguous depfile separator: {path}")

    def tokens(raw):
        result, current = [], []
        index = 0
        while index < len(raw):
            character = raw[index]
            if character == "\\":
                index += 1
                if index >= len(raw) or raw[index] not in "\\ :#\t":
                    raise BlockedInspection(f"Unsupported depfile escape in {path}")
                current.append(raw[index])
            elif character.isspace():
                if current:
                    result.append("".join(current))
                    current = []
            elif character in "\"'":
                raise BlockedInspection(f"Unsupported quoted depfile token in {path}")
            else:
                current.append(character)
            index += 1
        if current:
            result.append("".join(current))
        paths = []
        for value in result:
            candidate = Path(value)
            if not candidate.is_absolute():
                raise BlockedInspection(f"Relative depfile path is not attributable: {value}")
            paths.append(candidate.resolve())
        return paths

    separator = separators[0]
    outputs, inputs = tokens(text[:separator]), tokens(text[separator + 1 :])
    if not outputs or not inputs:
        raise BlockedInspection(f"Incomplete depfile: {path}")
    return {"path": Path(path).resolve(), "outputs": outputs, "inputs": inputs}


def package_roots(app, core):
    config_path = app / ".dart_tool/package_config.json"
    if not config_path.is_file():
        raise BlockedInspection("Isolated app package_config.json is missing")
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    expected = {"qfli_json": app, "qfli_studio_core": core, "re_editor": core / "vendor/re_editor"}
    observed = {}
    for package in config.get("packages", []):
        name = package.get("name")
        if name not in expected:
            continue
        if name in observed:
            raise BlockedInspection(f"Duplicate package mapping: {name}")
        uri = urlparse(urljoin(config_path.as_uri(), package["rootUri"]))
        if uri.scheme != "file" or uri.netloc not in ("", "localhost"):
            raise BlockedInspection(f"Nonlocal package mapping: {name}")
        raw_path = unquote(uri.path)
        if os.name == "nt" and re.match(r"^/[A-Za-z]:/", raw_path):
            raw_path = raw_path[1:]
        root = Path(raw_path).resolve()
        if path_key(root) != path_key(expected[name]):
            raise BlockedInspection(f"Package {name} resolves outside its exact snapshot: {root}")
        observed[name] = str(root)
    if set(observed) != set(expected):
        raise BlockedInspection("Required app/core/re_editor package mappings are incomplete")
    return {"path": str(config_path), "sha256": sha256_file(config_path), "roots": observed}


def source_dependencies(app, core, kernel_hash):
    if path_key(app) == path_key(LIVE_APP) or path_key(core) == path_key(LIVE_CORE):
        raise BlockedInspection("The native gate requires isolated app and frozen core roots")
    config = package_roots(app, core)
    build = app / ".dart_tool/flutter_build"
    # This installed SDK writes its aggregate depfile under build/ohos, while
    # its compiler depfile is .dart_tool/flutter_build/<id>/kernel_snapshot_program.d.
    aggregate_paths = set(build.rglob("flutter_build.d")) if build.is_dir() else set()
    intermediate = app / "build/ohos/intermediates/flutter"
    if intermediate.is_dir():
        aggregate_paths.update(intermediate.rglob("flutter_build.d"))
    if not aggregate_paths:
        raise BlockedInspection("No actual Flutter aggregate flutter_build.d exists")

    def matching(paths, output_name):
        matches = []
        for path in sorted(paths):
            depfile = parse_depfile(path)
            outputs = [output for output in depfile["outputs"] if output.name == output_name]
            if len(outputs) > 1:
                raise BlockedInspection(f"Multiple {output_name} outputs in {path}")
            if outputs and outputs[0].is_file() and sha256_file(outputs[0]) == kernel_hash:
                if not inside(outputs[0], app):
                    raise BlockedInspection(f"Compiled kernel output is outside the isolated app: {outputs[0]}")
                depfile["kernelOutput"] = outputs[0]
                matches.append(depfile)
        if len(matches) != 1:
            raise BlockedInspection(f"Expected one attributable {output_name} depfile, found {len(matches)}")
        return matches[0]

    aggregate = matching(aggregate_paths, "kernel_blob.bin")
    compiler_paths = set(build.rglob("kernel_snapshot_program.d")) if build.is_dir() else set()
    if not compiler_paths:
        raise BlockedInspection("No actual kernel_snapshot_program.d exists")
    compiler = matching(compiler_paths, "app.dill")
    roots = {"app": app / "lib", "core": core / "lib", "re_editor": core / "vendor/re_editor/lib"}
    groups = {name: {} for name in roots}
    aggregate_keys = {path_key(path) for path in aggregate["inputs"]}
    compiler_keys = {path_key(path) for path in compiler["inputs"]}
    for depfile in (aggregate, compiler):
        for dependency in depfile["inputs"]:
            if not inside(dependency, app) and not inside(dependency, core):
                if inside(dependency, LIVE_APP) or inside(dependency, LIVE_CORE):
                    raise BlockedInspection(f"Depfile references original/live project source: {dependency}")
            for name, root in roots.items():
                if dependency.suffix != ".dart" or not inside(dependency, root):
                    continue
                if not dependency.is_file():
                    raise BlockedInspection(f"Compiled source dependency no longer exists: {dependency}")
                if depfile is compiler and path_key(dependency) not in aggregate_keys:
                    raise BlockedInspection(f"Compiler source is absent from aggregate dependency evidence: {dependency}")
                groups[name][path_key(dependency)] = {
                    "path": str(dependency), "sha256": sha256_file(dependency),
                }
    required = {"app": app / "lib/main.dart", "core": core / "lib/services/studio_profile.dart", "re_editor": core / "vendor/re_editor/lib/re_editor.dart"}
    for name, path in required.items():
        if path_key(path) not in groups[name] or path_key(path) not in compiler_keys:
            raise BlockedInspection(f"Kernel depfiles do not establish required {name} source: {path}")
    return {
        "status": "PASS", "packageConfig": config,
        "aggregateDepfile": {"path": str(aggregate["path"]), "sha256": sha256_file(aggregate["path"]), "inputs": len(aggregate["inputs"]), "kernelOutput": str(aggregate["kernelOutput"])},
        "compilerDepfile": {"path": str(compiler["path"]), "sha256": sha256_file(compiler["path"]), "inputs": len(compiler["inputs"]), "kernelOutput": str(compiler["kernelOutput"])},
        "sourceCounts": {name: len(group) for name, group in groups.items()},
        "sources": {name: [group[key] for key in sorted(group)] for name, group in groups.items()},
        "originalAppRootRejected": str(LIVE_APP), "liveCoreRootRejected": str(LIVE_CORE),
    }


def inspect(args):
    hap, app, core = args.hap.resolve(), args.app_root.resolve(), args.core_root.resolve()
    require(hap.is_file(), f"HAP does not exist: {hap}")
    require(app.is_dir() and core.is_dir(), "Both isolated source roots must exist")
    original_hash = sha256_file(hap)
    result = {
        "passed": False, "mode": args.mode, "hap": str(hap), "appRoot": str(app),
        "coreRoot": str(core), "hapSha256": original_hash, "copiedHap": None,
    }
    with zipfile.ZipFile(hap) as bundle:
        names = bundle.namelist()
        require(not [name for name, count in Counter(names).items() if count > 1], "HAP contains duplicate/ambiguous archive entries")
        require("module.json" in names, "Compiled module.json is missing")
        module = json.loads(bundle.read("module.json"))
        require(module.get("app", {}).get("bundleName") == "com.azurekiln.qfli.json", "Unexpected compiled bundle identity")
        permissions = module.get("module", {}).get("requestPermissions")
        require(isinstance(permissions, list) and len(permissions) == 1 and isinstance(permissions[0], dict) and permissions[0].get("name") == "ohos.permission.READ_PASTEBOARD", "Compiled permissions must be exactly READ_PASTEBOARD")
        require("libs/x86_64/libflutter.so" in names, "x86_64 libflutter.so is missing")
        require([name for name in names if Path(name).name == "kernel_blob.bin"] == [KERNEL_ENTRY], "Expected exactly one debug kernel at the standard asset path")
        entries = {}
        for information in bundle.infolist():
            if information.is_dir():
                continue
            digest = hashlib.sha256()
            with bundle.open(information) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            entries[information.filename] = {"bytes": information.file_size, "sha256": digest.hexdigest()}
        require(entries["libs/x86_64/libflutter.so"]["bytes"] > 0 and entries[KERNEL_ENTRY]["bytes"] > 0, "Runtime/kernel entry is empty")
        assets = {}
        for name in CONTENT_NAMES:
            entry = "resources/rawfile/flutter_assets/assets/content/" + name
            source = app / "assets/content" / name
            require(entry in entries and source.is_file(), f"Required content source/archive entry is missing: {name}")
            require(bundle.read(entry) == source.read_bytes(), f"Packaged content differs from isolated source: {name}")
            assets[name] = {"entry": entry, "source": str(source), **entries[entry]}
        result.update({
            "bundleName": module["app"]["bundleName"], "permissions": [permissions[0]["name"]],
            "kernelSha256": entries[KERNEL_ENTRY]["sha256"], "entries": entries, "contentAssets": assets,
        })
    result["sourceDependencies"] = source_dependencies(app, core, result["kernelSha256"])
    require(sha256_file(hap) == original_hash, "HAP changed during inspection")
    if args.copy_to:
        destination = args.copy_to.resolve()
        require(path_key(destination) != path_key(hap), "Per-mode archive must differ from the mutable build output")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            require(destination.is_file() and sha256_file(destination) == original_hash, "Refusing to overwrite a different preserved HAP")
        else:
            # Exclusive creation prevents a concurrent build from replacing a
            # previously preserved mode artifact between existence and copy.
            with hap.open("rb") as source, destination.open("xb") as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
        require(sha256_file(destination) == original_hash, "Preserved HAP hash differs from inspected HAP")
        result["copiedHap"] = str(destination)
    result["passed"] = True
    result["status"] = "PASS"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hap", required=True, type=Path)
    parser.add_argument("--app-root", required=True, type=Path)
    parser.add_argument("--core-root", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("harness", "normal"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--copy-to", type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args)
    except Exception as error:
        result = {"passed": False, "status": "BLOCKED" if isinstance(error, BlockedInspection) else "FAIL", "mode": args.mode, "hap": str(args.hap.resolve()), "copiedHap": None, "error": f"{type(error).__name__}: {error}"}
    result["inspectedUtc"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in ("entries", "contentAssets", "sourceDependencies")}, separators=(",", ":")))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
