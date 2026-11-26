"""Build distribution containers in GitHub, preserving native payload metadata.

This helper does not compile applications. Native dependency verification runs
separately against every entry in runtime_packages before anything is published.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile

PREFIX = "qflistudio-json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(*command: str, capture: bool = False) -> str:
    result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.STDOUT if capture else None)
    return result.stdout or ""


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inventory(root: Path) -> list[dict]:
    result = []
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        row = {"path": path.relative_to(root).as_posix(), "mode": oct(stat.S_IMODE(info.st_mode))}
        if path.is_symlink():
            link = os.readlink(path)
            require(not os.path.isabs(link), "absolute payload symlink rejected")
            require(path.resolve().is_relative_to(root.resolve()), "escaping payload symlink rejected")
            row.update(type="symlink", target=link)
        elif path.is_file():
            row.update(type="file", bytes=info.st_size, sha256=sha256(path))
        elif path.is_dir():
            row.update(type="directory")
        else:
            raise SystemExit("special payload file rejected")
        result.append(row)
    return result


def make_tar(source: Path, destination: Path) -> None:
    # Python's tar writer stores Unix modes and link entries, not dereferenced files.
    inventory(source)
    with tarfile.open(destination, "w:gz", format=tarfile.PAX_FORMAT, dereference=False) as archive:
        archive.add(source, arcname=source.name, recursive=True)


def version() -> str:
    text = Path("pubspec.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^version:\s*([0-9]+\.[0-9]+\.[0-9]+)(?:\+([0-9]+))?\s*$", text)
    require(match is not None, "unsupported app version for packaging")
    assert match is not None
    return match.group(1) + ("+" + match.group(2) if match.group(2) else "")


def package_windows(output: Path, manifest: dict) -> None:
    source = Path("build/windows/x64/runner/Release")
    require((source / "qfli_json.exe").is_file(), "Windows release executable missing")
    redist = Path(os.environ.get("QFLI_MSVC_REDIST", ""))
    require(bool(os.environ.get("QFLI_MSVC_REDIST")) and redist.is_dir(), "reviewed Windows VC runtime prerequisite is missing")
    runtime_dlls = sorted(redist.glob("*.dll"))
    require(bool(runtime_dlls), "VC143 runtime redistributable DLLs are missing")
    for library in runtime_dlls:
        require(not library.is_symlink(), "linked VC runtime input rejected")
        shutil.copy2(library, source / library.name)
    manifest["payload_inventory"] = inventory(source)
    archive = output / f"{PREFIX}-windows-x64.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(source.rglob("*")):
            require(not path.is_symlink(), "Windows payload symlink requires an explicit packaging policy")
            if path.is_file():
                bundle.write(path, Path("QFLIJson") / path.relative_to(source))
    manifest["runtime_packages"].append(str(archive))
    compiler = shutil.which("ISCC.exe")
    if not compiler:
        candidate = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6/ISCC.exe"
        if candidate.is_file():
            compiler = str(candidate)
    require(bool(compiler), "dependency-blocked: Inno Setup is required; a ZIP-only build cannot satisfy the Windows installer gate")
    require('"' not in str(source.resolve()) and '"' not in str(output.resolve()), "unsafe installer path")
    script = output / "windows-installer.iss"
    script.write_text(f'''[Setup]
AppId=QFLIJson-JSON-Workbench
AppName=QFLIJson
AppVersion={version().split('+')[0]}
DefaultDirName={{localappdata}}\\Programs\\QFLIJson
DefaultGroupName=QFLIJson
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={output.resolve()}
OutputBaseFilename={PREFIX}-windows-x64-setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={{app}}\\qfli_json.exe
[Files]
Source: "{source.resolve()}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{{group}}\\QFLIJson"; Filename: "{{app}}\\qfli_json.exe"
[Run]
Filename: "{{app}}\\qfli_json.exe"; Description: "Launch QFLIJson"; Flags: nowait postinstall skipifsilent
''', encoding="utf-8")
    run(compiler, str(script))
    script.unlink()
    installer = output / f"{PREFIX}-windows-x64-setup.exe"
    require(installer.is_file(), "Windows installer was not produced")
    manifest["opaque_packages"].append({
        "path": str(installer), "sha256": sha256(installer),
        "inspectable_payload": archive.name, "payload_sha256": sha256(archive),
        "payload_relation": "Inno Setup [Files] embeds exactly this inventoried release tree",
        "inspection": "installer container is opaque; payload ZIP is verified separately",
    })


def package_linux(output: Path, manifest: dict) -> None:
    source = Path("build/linux/x64/release/bundle")
    binary = source / "qfli_json"
    require(binary.is_file() and os.access(binary, os.X_OK), "Linux executable missing or not executable")
    dependency_lines = []
    packages = {"git", "libgtk-3-0t64", "libsecret-1-0", "libstdc++6", "libc6"}
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open("rb") as stream:
            is_elf = stream.read(4) == b"\x7fELF"
        if not is_elf:
            continue
        # Plugin build paths must not override the packaged Flutter libraries.
        text = run("env", "-u", "LD_PRELOAD", "-u", "LD_AUDIT",
                   f"LD_LIBRARY_PATH={(source / 'lib').resolve()}",
                   "ldd", str(path.resolve()), capture=True)
        require("not found" not in text, f"unresolved Linux runtime library in {path.name}")
        dependency_lines.append({"member": path.relative_to(source).as_posix(), "ldd": text})
        for resolved in re.findall(r"=>\s+(/[^\s]+)", text):
            p = Path(resolved).resolve()
            if p.is_relative_to(source.resolve()):
                continue
            result = subprocess.run(["dpkg-query", "-S", str(p)], text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if result.returncode != 0 and str(p).startswith("/usr/"):
                # Ubuntu's merged-/usr links can differ from dpkg's recorded spelling.
                result = subprocess.run(["dpkg-query", "-S", str(p)[4:]], text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            require(result.returncode == 0, f"unmapped Linux system runtime dependency: {p.name}")
            for line in result.stdout.splitlines():
                owner = line.split(": ", 1)[0].split(":", 1)[0]
                require(re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", owner) is not None, "invalid Debian dependency owner")
                packages.add(owner)
    runtime = {"distribution": "Ubuntu 24.04", "architecture": "amd64",
               "minimum_distribution": "Ubuntu 24.04 or compatible ABI", "system_packages": sorted(packages),
               "elf_dependency_closure": dependency_lines}
    (source / "RUNTIME_DEPENDENCIES.json").write_text(json.dumps(runtime, indent=2) + "\n", encoding="utf-8")
    manifest["payload_inventory"] = inventory(source)
    archive = output / f"{PREFIX}-linux-x64.tar.gz"
    make_tar(source, archive)
    manifest["runtime_packages"].append(str(archive))
    with tempfile.TemporaryDirectory(prefix="qfli-deb-", dir=Path("build")) as directory:
        root = Path(directory)
        destination = root / "opt/qflistudio-json"
        shutil.copytree(source, destination, symlinks=True)
        (root / "usr/bin").mkdir(parents=True)
        os.symlink("/opt/qflistudio-json/qfli_json", root / "usr/bin/qflistudio-json")
        applications = root / "usr/share/applications"
        applications.mkdir(parents=True)
        (applications / "qflistudio-json.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=QFLIJson\nExec=/opt/qflistudio-json/qfli_json\n"
            "Icon=qflistudio-json\nCategories=Development;Utility;\nTerminal=false\n", encoding="utf-8")
        icons = root / "usr/share/icons/hicolor/256x256/apps"
        icons.mkdir(parents=True)
        shutil.copy2("assets/app_icon.png", icons / "qflistudio-json.png")
        control = root / "DEBIAN"
        control.mkdir()
        (control / "control").write_text(
            f"Package: qflistudio-json\nVersion: {version()}\nArchitecture: amd64\n"
            "Maintainer: QFLI JSON maintainers\nSection: devel\nPriority: optional\n"
            f"Depends: {', '.join(sorted(packages))}\n"
            "Description: QFLIJson offline JSON workbench\n", encoding="utf-8")
        deb = output / f"{PREFIX}-linux-amd64.deb"
        run("dpkg-deb", "--root-owner-group", "--build", str(root), str(deb))
        manifest["opaque_packages"].append({"path": str(deb), "sha256": sha256(deb),
            "inspectable_payload": archive.name, "payload_sha256": sha256(archive),
            "payload_relation": "Debian /opt/qflistudio-json is a symlink-preserving copy of the inventoried tar payload",
            "inspection": "Debian container is paired with its independently inspected runtime tar"})


def package_macos(output: Path, manifest: dict) -> None:
    source = Path("build/macos/Build/Products/Release/QFLIJson.app")
    require(source.is_dir(), "macOS PRODUCT_NAME=QFLIJson bundle missing")
    with (source / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    executable = source / "Contents/MacOS" / info["CFBundleExecutable"]
    architectures = set(run("lipo", "-archs", str(executable), capture=True).split())
    require(architectures == {"arm64", "x86_64"}, "macOS universal name requires both arm64 and x86_64")
    manifest["architectures"] = sorted(architectures)
    manifest["payload_inventory"] = inventory(source)
    archive = output / f"{PREFIX}-macos-universal.tar.gz"
    make_tar(source, archive)
    manifest["runtime_packages"].append(str(archive))
    with tempfile.TemporaryDirectory(prefix="qfli-dmg-", dir=Path("build")) as directory:
        root = Path(directory)
        run("ditto", "--rsrc", "--extattr", str(source), str(root / source.name))
        os.symlink("/Applications", root / "Applications")
        dmg = output / f"{PREFIX}-macos-universal.dmg"
        run("hdiutil", "create", "-volname", "QFLIJson", "-srcfolder", str(root),
            "-format", "UDZO", "-ov", str(dmg))
        manifest["opaque_packages"].append({"path": str(dmg), "sha256": sha256(dmg),
            "inspectable_payload": archive.name, "payload_sha256": sha256(archive),
            "payload_relation": "ditto --rsrc --extattr preserves the same inventoried QFLIJson.app in the DMG",
            "inspection": "DMG is not treated as inspected native payload; tar is inspected independently"})
    manifest["limitations"].append("macOS app/DMG is not Developer-ID signed or notarized")


def package_ios(output: Path, manifest: dict) -> None:
    source = Path("build/ios/iphoneos/Runner.app")
    require(source.is_dir(), "unsigned iOS Runner.app missing")
    manifest["payload_inventory"] = inventory(source)
    with tempfile.TemporaryDirectory(prefix="qfli-ipa-", dir=Path("build")) as directory:
        root = Path(directory)
        payload = root / "Payload"
        payload.mkdir()
        run("ditto", "--rsrc", "--extattr", str(source), str(payload / source.name))
        archive = output / f"{PREFIX}-ios-arm64-unsigned.ipa"
        # ditto stores Unix modes and symlinks; upload only this container, never raw .app.
        run("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(payload), str(archive))
    with zipfile.ZipFile(archive) as ipa:
        require("Payload/Runner.app/Info.plist" in ipa.namelist(), "invalid IPA payload layout")
    manifest["runtime_packages"].append(str(archive))
    manifest["limitations"].append("Unsigned IPA cannot be installed on a stock iOS device without valid signing/provisioning")


def android_abis(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return {m.group(1) for name in archive.namelist()
                if (m := re.match(r"(?:base/)?lib/([^/]+)/[^/]+\.so$", name))}


def package_android(output: Path, manifest: dict) -> None:
    for abi in ("armeabi-v7a", "arm64-v8a", "x86_64"):
        source = Path(f"build/app/outputs/flutter-apk/app-{abi}-release.apk")
        require(source.is_file(), f"split APK missing for {abi}")
        require(android_abis(source) == {abi}, f"APK ABI inventory disagrees with {abi} filename")
        destination = output / f"{PREFIX}-android-{abi}-debug-signed.apk"
        shutil.copy2(source, destination)
        manifest["runtime_packages"].append(str(destination))
    source = Path("build/app/outputs/bundle/release/app-release.aab")
    require(source.is_file(), "Android App Bundle missing")
    require(android_abis(source) == {"armeabi-v7a", "arm64-v8a", "x86_64"}, "AAB native ABI inventory incomplete")
    destination = output / f"{PREFIX}-android-universal-debug-signed.aab"
    shutil.copy2(source, destination)
    manifest["runtime_packages"].append(str(destination))
    manifest["architectures"] = ["armeabi-v7a", "arm64-v8a", "x86_64"]
    manifest["limitations"].append("Android release-mode packages use the project debug key, not a production/store signing key")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("windows", "linux", "macos", "ios", "android"))
    parser.add_argument("--output", default="build/ci-packages")
    args = parser.parse_args()
    require(os.environ.get("GITHUB_ACTIONS") == "true", "cloud-only: packaging may run only in GitHub Actions")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    require(not any(output.iterdir()), "refusing to replace existing package outputs")
    manifest = {"schema": 1, "platform": args.platform, "app_version": version(),
                "runtime_packages": [], "opaque_packages": [], "limitations": []}
    if args.platform in ("windows", "linux", "macos"):
        manifest["runtime_prerequisites"] = {"git": "external Git CLI must be installed and on PATH; not bundled"}
        manifest["limitations"].append("Packaging/native checks do not prove external desktop Git is present on an end-user machine")
    globals()[f"package_{args.platform}"](output, manifest)
    manifest["asset_sha256"] = {path.name: sha256(path) for path in sorted(output.iterdir()) if path.is_file()}
    (output / "package-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Packaged {args.platform}; native package verification is still required")


if __name__ == "__main__":
    main()
