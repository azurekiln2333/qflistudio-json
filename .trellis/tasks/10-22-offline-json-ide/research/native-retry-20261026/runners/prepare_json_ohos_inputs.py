"""Prepare/capture isolated OHOS inputs without invoking an SDK or build tool.

The passed host snapshot is authoritative.  Preparation writes a NEW directory,
copies executable inputs byte-for-byte, relocates package/native references, and
excludes standalone credential files and previous build outputs. Embedded signing
configuration remains in the private, ignored native snapshot and is never
exported as evidence content.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import url2pathname
import uuid


ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "lib/json/json_verification_page.dart").is_file())
LIVE_CORE = ROOT.parent / "qfli_studio_core"
GENERATED = {"build", ".hvigor", "oh_modules", "node_modules", ".git", ".dart_tool"}
CREDENTIAL_SUFFIXES = {
    ".p12", ".pfx", ".pem", ".key", ".jks", ".keystore", ".p7b",
    ".cer", ".crt", ".mobileprovision", ".csr",
}
EXECUTABLE_ROOTS = ("lib", "assets")
FROZEN_ROOTS = ("lib", "assets", "test", "tool", "vendor")
ROOT_INPUTS = (
    "pubspec.yaml", "pubspec.lock", "analysis_options.yaml", ".metadata",
    ".flutter-plugins-dependencies", ".flutter-plugins",
    ".dart_tool/package_config.json", ".dart_tool/package_graph.json",
)


def now():
    return datetime.now(timezone.utc).isoformat()


def signature(path):
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            length += len(chunk)
            digest.update(chunk)
    return {"bytes": length, "sha256": digest.hexdigest()}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(directory, *args, data=None):
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    result = subprocess.run(
        ["git", *args], cwd=directory, input=data, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True, env=environment,
    )
    return result.stdout.decode("utf-8", errors="replace").strip()


def repository(directory):
    return {
        "root": str(directory), "head": git(directory, "rev-parse", "HEAD"),
        "tree": git(directory, "rev-parse", "HEAD^{tree}"),
        "status": git(directory, "status", "--porcelain=v1", "--untracked-files=all").splitlines(),
    }


def under(path, root):
    return path.resolve().is_relative_to(root.resolve())


def credential(path):
    lowered = path.name.lower()
    return path.suffix.lower() in CREDENTIAL_SUFFIXES or lowered in {
        ".env", ".npmrc", ".netrc", "credentials", "credentials.json",
        "signing.properties", "key.properties",
    }


def linked(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def generated(relative):
    parts = relative.parts
    return (
        any(part in GENERATED for part in parts)
        or (len(parts) >= 2 and parts[:2] == ("entry", "libs"))
        or "flutter_assets" in parts
        or relative.name == "BuildProfile.ets"
        or relative.as_posix().endswith("resources/rawfile/buildinfo.json5")
    )


def inventory(directory, label, files, links, exclusions, *, native=False, cache=False):
    """Never traverse links: capture reference identities separately from files."""
    if not directory.exists():
        return
    for base, directories, names in os.walk(directory, followlinks=False):
        base = Path(base)
        for name in list(directories):
            path = base / name
            relative = path.relative_to(directory)
            if (native and generated(relative)) or (cache and name in {"build", ".hvigor", ".git"}):
                directories.remove(name)
            elif linked(path):
                links[label + "/" + relative.as_posix()] = str(path.resolve(strict=True))
                directories.remove(name)
        for name in names:
            path = base / name
            relative = path.relative_to(directory)
            key = label + "/" + relative.as_posix()
            if native and generated(relative):
                continue
            if credential(path):
                exclusions.append(key)
            elif linked(path):
                links[key] = str(path.resolve(strict=True))
            else:
                files[key] = signature(path)


def input_set(app, core):
    files, links, exclusions = {}, {}, []
    for label, directory in (("app", app), ("core", core)):
        for name in FROZEN_ROOTS:
            inventory(directory / name, label + "/" + name, files, links, exclusions)
        for name in ROOT_INPUTS:
            path = directory / name
            if path.is_file():
                files[label + "/" + name] = signature(path)
    inventory(app / "ohos", "app/ohos", files, links, exclusions, native=True)
    for name in ("oh_modules", "entry/oh_modules", "node_modules"):
        inventory(app / "ohos" / name, "nativeCache/" + name, files, links, exclusions, cache=True)
    inventory(app.parent / "native_plugins", "nativePlugins", files, links, exclusions, cache=True)
    return files, links, sorted(exclusions)


def verify_host(manifest):
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("Host manifest has no frozen file map")
    app, core = Path(manifest["appSnapshot"]).resolve(), Path(manifest["coreSnapshot"]).resolve()
    failures = []
    for key, expected in files.items():
        label, relative = key.split("/", 1)
        if label not in {"app", "core"} or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Unsafe path in host manifest")
        path = (app if label == "app" else core) / relative
        if not path.is_file() or signature(path) != expected:
            failures.append(key)
    for label, directory in (("app", app), ("core", core)):
        expected = {key for key in files if key.startswith(tuple(label + "/" + name + "/" for name in FROZEN_ROOTS))}
        actual = set()
        for name in FROZEN_ROOTS:
            if (directory / name).exists():
                actual.update(label + "/" + p.relative_to(directory).as_posix()
                              for p in (directory / name).rglob("*") if p.is_file())
        failures.extend(sorted(expected ^ actual))
    if failures:
        raise ValueError("Authoritative host snapshot changed: " + ", ".join(sorted(set(failures))[:30]))
    return app, core


def verify_original(manifest):
    """Git-clean canonical baseline, raw overlay hashes; never normalize frozen bytes."""
    expected = {key[4:]: value for key, value in manifest["files"].items()
                if key.startswith(tuple("app/" + name + "/" for name in EXECUTABLE_ROOTS))}
    actual = {path.relative_to(ROOT).as_posix()
              for name in EXECUTABLE_ROOTS for path in (ROOT / name).rglob("*") if path.is_file()}
    if set(expected) != actual:
        raise ValueError("Original executable path set differs from host snapshot")
    rows = git(ROOT, "ls-tree", "-r", manifest["appCommit"], "--", *EXECUTABLE_ROOTS).splitlines()
    blobs = {row.split("\t", 1)[1]: row.split("\t", 1)[0].split()[2] for row in rows}
    overlays = manifest.get("appOverlays", {})
    checked = {}
    for name in sorted(expected):
        source = ROOT / name
        raw = signature(source)
        if name in overlays:
            if raw["sha256"] != overlays[name]["sha256"]:
                raise ValueError("Original owned overlay changed: " + name)
            method = "raw-overlay-sha256"
        else:
            canonical = git(ROOT, "hash-object", "--path=" + name, "--stdin", data=source.read_bytes())
            if canonical != blobs.get(name):
                raise ValueError("Original baseline Git blob changed: " + name)
            method = "canonical-git-blob"
        checked[name] = {**raw, "comparison": method}
    return checked


def package_root(config_path, value):
    uri = urljoin(config_path.resolve().as_uri(), value)
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        raise ValueError("Package root is not a local file URI")
    return Path(url2pathname(unquote(parsed.path))).resolve()


def verify_packages(app, core, allow_native_plugin=False):
    path = app / ".dart_tool/package_config.json"
    packages = {p["name"]: package_root(path, p["rootUri"]) for p in read_json(path)["packages"]}
    required = {"qfli_json": app.resolve(), "qfli_studio_core": core.resolve(), "re_editor": (core / "vendor/re_editor").resolve()}
    for name, root in required.items():
        if packages.get(name) != root:
            raise ValueError("Package config does not resolve frozen " + name)
    if allow_native_plugin and "path_provider_ohos" in packages:
        if not under(packages["path_provider_ohos"], app.parent / "native_plugins"):
            raise ValueError("OHOS plugin still resolves shared Pub cache")
    return {name: str(packages[name]) for name in required}


def verify_executable_copy(manifest, app, core):
    for label, directory in (("app", app), ("core", core)):
        expected = {key.split("/", 1)[1]: value for key, value in manifest["files"].items()
                    if key.startswith(tuple(label + "/" + name + "/" for name in FROZEN_ROOTS))}
        actual = {p.relative_to(directory).as_posix() for name in FROZEN_ROOTS
                  if (directory / name).exists() for p in (directory / name).rglob("*") if p.is_file()}
        if actual != set(expected):
            raise ValueError("Prepared executable path set differs from passed host: " + label)
        for name, value in expected.items():
            if signature(directory / name) != value:
                raise ValueError("Prepared executable bytes differ from passed host: " + label + "/" + name)


def mapped(path, mappings):
    path = path.resolve()
    for source, destination in sorted(mappings, key=lambda item: len(str(item[0])), reverse=True):
        if path.is_relative_to(source):
            return destination / path.relative_to(source)
    return path


def junction(path, target):
    if path.exists() or linked(path):
        raise ValueError("Refusing to overwrite cache reference: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        quote = lambda value: "'" + str(value).replace("'", "''") + "'"
        command = "New-Item -ItemType Junction -Path " + quote(path) + " -Target " + quote(target) + " | Out-Null"
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            raise ValueError("Cannot create isolated cache junction: " + str(path))
    else:
        path.symlink_to(target, target_is_directory=True)


def copy_tree(source, destination, mappings, *, native=False, cache=False):
    destination.mkdir(parents=True, exist_ok=True)
    references = []
    for base, directories, names in os.walk(source, followlinks=False):
        base = Path(base)
        for name in list(directories):
            original = base / name
            relative = original.relative_to(source)
            target = destination / relative
            if ((native and generated(relative))
                    or (cache and name in {"build", ".hvigor", ".git", ".dart_tool"})):
                directories.remove(name)
            elif linked(original):
                references.append((target, mapped(original.resolve(strict=True), mappings)))
                directories.remove(name)
            else:
                target.mkdir(parents=True, exist_ok=True)
        for name in names:
            original = base / name
            relative = original.relative_to(source)
            if credential(original) or (native and generated(relative)):
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if linked(original):
                raise ValueError("Unexpected linked native input file: " + str(original))
            # Native frozen policy files are copied from the passed host below.
            try:
                shutil.copy2(original, target)
            except OSError as error:
                raise ValueError("Cannot copy native input (use a short destination on Windows): " + str(target)) from error
    for target, reference in references:
        junction(target, reference)


def relocate_string(value, source_dir, mappings):
    prefix, candidate = "", value
    if value.startswith("file:"):
        prefix, candidate = "file:", value[5:]
    elif "@../" in value:
        index = value.rfind("@../") + 1
        prefix, candidate = value[:index], value[index:]
    if candidate.startswith(("../", "./", "..\\", ".\\")):
        path = (source_dir / candidate).resolve()
        if not path.exists():
            # path_provider's declared HAR is intentionally masked by the
            # installed Flutter plugin's absolute engine-HAR override.
            fallback = (path.name == "flutter.har" and path.parent.name == "libs"
                        and path.parent.parent.name == "ohos"
                        and any(path.is_relative_to(source) and target.parent.name == "native_plugins"
                                for source, target in mappings))
            if not fallback:
                raise ValueError("Unresolvable native lock reference in " + str(source_dir))
        return prefix + mapped(path, mappings).as_posix()
    if Path(candidate).is_absolute():
        return prefix + mapped(Path(candidate), mappings).as_posix()
    return value


def relocate_json(value, source_dir, mappings):
    if isinstance(value, dict):
        return {relocate_string(key, source_dir, mappings): relocate_json(child, source_dir, mappings)
                for key, child in value.items()}
    if isinstance(value, list):
        return [relocate_json(child, source_dir, mappings) for child in value]
    if isinstance(value, str):
        return relocate_string(value, source_dir, mappings)
    return value


def remap_package_config(source, target, mappings):
    config = read_json(source)
    for package in config["packages"]:
        package["rootUri"] = mapped(package_root(source, package["rootUri"]), mappings).as_uri()
    write_json(target, config)


def prepare(manifest_path, manifest, old_app, old_core, destination):
    if (destination.exists() or not under(destination, ROOT / "build")
            or under(destination, old_app.parent)):
        raise ValueError("Preparation requires a NEW directory inside the app build directory")
    app, core = destination / "qfli_json", destination / "qfli_studio_core"
    plugins = read_json(old_app / ".flutter-plugins-dependencies")
    clones = {}
    for plugin in plugins.get("plugins", {}).get("ohos", []):
        source = Path(plugin["path"]).resolve()
        if not source.is_dir() or not re.fullmatch(r"[A-Za-z0-9_]+", plugin["name"]):
            raise ValueError("Invalid native plugin metadata")
        clones[source] = destination / "native_plugins" / plugin["name"]
    mappings = [(old_app, app), (old_core, core), (ROOT, app), (LIVE_CORE, core), *clones.items()]
    destination.mkdir(parents=True, exist_ok=False)
    # Copy only host-manifest files; no host test/build intermediates are reused.
    for key in manifest["files"]:
        label, name = key.split("/", 1)
        source = (old_app if label == "app" else old_core) / name
        target = (app if label == "app" else core) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for source, target in clones.items():
        copy_tree(source, target, mappings, native=True)
    copy_tree(ROOT / "ohos", app / "ohos", mappings, native=True)
    # Existing host-owned policy inputs remain the exact passed host bytes.
    for key in manifest["files"]:
        if key.startswith("app/ohos/"):
            name = key[4:]
            shutil.copy2(old_app / name, app / name)
    for name in ("oh_modules", "entry/oh_modules", "node_modules"):
        source = ROOT / "ohos" / name
        if source.is_dir():
            copy_tree(source, app / "ohos" / name, mappings, cache=True)
    # Keys and values can both contain depth-relative identities in native locks.
    lock_sources = [ROOT / "ohos"] + [source / "ohos" for source in clones]
    for native_root in lock_sources:
        for base, directories, names in os.walk(native_root, followlinks=False):
            directories[:] = [name for name in directories if name not in {"build", ".hvigor", "node_modules"}
                              and not linked(Path(base) / name)]
            for name in names:
                if name not in {"oh-package-lock.json5", "package-lock.json", ".package-lock.json", "lock.json5"}:
                    continue
                source = Path(base) / name
                target = mapped(source, mappings)
                if target == source or not target.is_file():
                    continue
                reference_base = source.parent
                if source.name == "lock.json5" and source.parent.name == ".ohpm":
                    reference_base = source.parent.parent.parent
                elif source.name == ".package-lock.json" and source.parent.name == "node_modules":
                    reference_base = source.parent.parent
                write_json(target, relocate_json(read_json(source), reference_base, mappings))
    for source, target in ((old_app, app), (old_core, core)):
        remap_package_config(source / ".dart_tool/package_config.json", target / ".dart_tool/package_config.json", mappings)
    for group in plugins.get("plugins", {}).values():
        for plugin in group:
            original = Path(plugin["path"]).resolve()
            if original in clones:
                plugin["path"] = str(clones[original]) + os.sep
    write_json(app / ".flutter-plugins-dependencies", plugins)
    if (ROOT / ".metadata").is_file():
        shutil.copy2(ROOT / ".metadata", app / ".metadata")
    verify_executable_copy(manifest, app, core)
    verify_packages(app, core, allow_native_plugin=True)
    return app, core


def changes(before, after):
    return {
        "added": sorted(set(after) - set(before)),
        "deleted": sorted(set(before) - set(after)),
        "changed": sorted(key for key in set(before) & set(after) if before[key] != after[key]),
    }


def named_files(values):
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError("Tool identities must use NAME=PATH")
        name, raw = value.split("=", 1)
        path = Path(raw).resolve(strict=True)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or not path.is_file() or credential(path):
            raise ValueError("Invalid tool identity")
        result[name] = {"path": str(path), **signature(path)}
    return result


def parameters(values):
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError("Build parameters must use NAME=VALUE")
        name, content = value.split("=", 1)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Invalid build parameter name")
        if re.search(r"password|secret|credential|token|signing|keystore", name, re.I):
            result[name] = {"redacted": True, "sha256": hashlib.sha256(content.encode()).hexdigest()}
        else:
            result[name] = content
    return result


def readiness_mismatches(expected, actual):
    """Compare a fresh pre-build capture with the reviewed readiness manifest."""
    mismatches = []
    if not isinstance(expected, dict):
        return ["expected-prepared-not-object"]
    if expected.get("prepared") is not True:
        mismatches.append("snapshot-not-prepared")
    for key in ("appRoot", "coreRoot", "hostManifest", "hostManifestIdentity", "coreCommit", "coreTree",
                "hostAppCommit", "hostAppOverlays", "packageRoots", "files", "cacheReferences",
                "originalExecutableComparison", "originalAppInputs", "originalCacheReferences", "tools",
                "helperIdentity", "exclusionPolicy", "embeddedSigningConfigurationCopied"):
        if key not in expected or expected[key] != actual.get(key):
            mismatches.append(key)
    runners = expected.get("runners")
    if not isinstance(runners, dict) or not runners:
        mismatches.append("missing-reviewed-runners")
    else:
        for name, identity in runners.items():
            try:
                path = Path(identity["path"]).resolve(strict=True)
                if credential(path) or signature(path) != {"bytes": identity["bytes"], "sha256": identity["sha256"]}:
                    mismatches.append("runner/" + name)
            except (OSError, KeyError, TypeError):
                mismatches.append("runner/" + name)
    commands = expected.get("nativeCommands")
    if not isinstance(commands, dict) or set(commands) != {"harness", "normal"}:
        mismatches.append("missing-reviewed-native-commands")
    else:
        for mode in ("harness", "normal"):
            try:
                command = json.loads(actual.get("buildParameters", {}).get(mode + ".command", ""))
                if command != commands[mode]:
                    mismatches.append("command/" + mode)
            except (ValueError, TypeError):
                mismatches.append("command/" + mode)
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--app-root", type=Path)
    parser.add_argument("--core-root", type=Path)
    parser.add_argument("--prepare-native", action="store_true")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--expected-prepared", type=Path)
    parser.add_argument("--runner", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--tool", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--build-parameter", action="append", default=[], metavar="NAME=VALUE")
    args = parser.parse_args()
    if args.prepare_native and args.expected_prepared:
        raise ValueError("A readiness comparison cannot prepare a new snapshot")
    if args.output.exists():
        raise ValueError("Refusing to overwrite capture output")
    host_path = args.host_manifest.resolve(strict=True)
    manifest = read_json(host_path)
    old_app, old_core = verify_host(manifest)
    original_match = verify_original(manifest)
    if args.prepare_native:
        if args.before or args.app_root or args.core_root:
            raise ValueError("Preparation cannot reuse an existing app/core or pre-capture")
        # OHPM store package identities are long; keep the snapshot prefix short.
        destination = (args.destination or ROOT / "build" / ("o" + uuid.uuid4().hex[:8])).resolve()
        app, core = prepare(host_path, manifest, old_app, old_core, destination)
    else:
        if not args.app_root or not args.core_root:
            raise ValueError("Capture requires explicit --app-root and --core-root")
        app, core = args.app_root.resolve(strict=True), args.core_root.resolve(strict=True)
        if app in {ROOT, old_app} or core in {LIVE_CORE, old_core} or not under(app, ROOT / "build"):
            raise ValueError("Native capture requires an isolated app/core snapshot")
        verify_executable_copy(manifest, app, core)
    roots = verify_packages(app, core, allow_native_plugin=True)
    files, links, excluded = input_set(app, core)
    for reference in links.values():
        target = Path(reference)
        if under(target, LIVE_CORE) or (under(target, ROOT) and not under(target, app.parent)):
            raise ValueError("Native cache reference resolves to a live project input")
    original_files, original_links, original_excluded = input_set(ROOT, LIVE_CORE)
    # The live core can advance independently; capture its identity but never build it.
    native_original = {key: value for key, value in original_files.items()
                       if key.startswith("app/") or key.startswith("nativeCache/")}
    tool_identities = named_files(args.tool)
    plugin_root = app / "ohos/node_modules/flutter-hvigor-plugin"
    for tool_file in sorted(plugin_root.rglob("*")):
        if tool_file.is_file() and tool_file.suffix in {".ts", ".json"}:
            name = tool_file.relative_to(plugin_root).as_posix()
            tool_identities["installed-hvigor/" + name] = {"path": str(tool_file.resolve()), **signature(tool_file)}
    data = {
        "schemaVersion": 1, "capturedUtc": now(), "prepared": bool(args.prepare_native),
        "appRoot": str(app), "coreRoot": str(core), "hostManifest": str(host_path),
        "hostManifestIdentity": signature(host_path), "coreCommit": manifest["coreCommit"],
        "coreTree": manifest["coreTree"], "hostAppCommit": manifest["appCommit"],
        "hostAppOverlays": manifest.get("appOverlays", {}), "packageRoots": roots,
        "files": files, "cacheReferences": links,
        "originalExecutableComparison": original_match,
        "originalAppInputs": native_original,
        "originalCacheReferences": original_links,
        "originalApp": repository(ROOT), "originalCore": repository(LIVE_CORE),
        "metadataPresent": (ROOT / ".metadata").is_file(),
        "credentialPathsExcluded": sorted(set(excluded + original_excluded)),
        "buildParameters": parameters(args.build_parameter),
        "runners": named_files(args.runner), "tools": tool_identities,
        "helperIdentity": signature(Path(__file__)),
        "exclusionPolicy": ["build", ".hvigor", "entry/libs", "flutter_assets", "BuildProfile.ets", "rawfile/buildinfo.json5", "standalone credential files"],
        "embeddedSigningConfigurationCopied": True,
        "buildExecuted": False,
    }
    readiness_failed = False
    if args.expected_prepared:
        expected_path = args.expected_prepared.resolve(strict=True)
        expected = read_json(expected_path)
        data["expectedPreparedIdentity"] = signature(expected_path)
        data["readinessMismatches"] = readiness_mismatches(expected, data)
        readiness_failed = bool(data["readinessMismatches"])
    if args.before:
        before = read_json(args.before.resolve(strict=True))
        stable = ("appRoot", "coreRoot", "hostManifest", "hostManifestIdentity", "coreCommit", "coreTree", "packageRoots")
        if any(before.get(key) != data.get(key) for key in stable):
            raise ValueError("Post-capture identity differs from pre-capture")
        data["beforeIdentity"] = signature(args.before)
        data["differences"] = {name: changes(before.get(name, {}), data[name])
                               for name in ("files", "cacheReferences", "originalAppInputs", "originalCacheReferences", "originalExecutableComparison",
                                            "runners", "tools", "buildParameters", "helperIdentity")}
        data["repositoriesChanged"] = [name for name in ("originalApp", "originalCore") if before.get(name) != data[name]]
        changed = any(any(value for value in delta.values()) for delta in data["differences"].values()) or bool(data["repositoriesChanged"])
    else:
        changed = False
    changed = changed or readiness_failed
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Refusing to overwrite capture output")
    write_json(output, data)
    print(json.dumps({"output": str(output), "prepared": data["prepared"], "appRoot": str(app), "coreRoot": str(core),
                      "files": len(files), "cacheReferences": len(links), "changed": changed}, indent=2))
    return 1 if changed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print("OHOS input preparation failed: " + str(error), file=sys.stderr)
        sys.exit(2)
