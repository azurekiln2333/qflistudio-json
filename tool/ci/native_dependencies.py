"""Cloud-only exact-pin native input and packaged-payload verification.

No native code is executed. This verifies historical Git blobs, binary structure
and packaged code/data, not installation, runtime API results or signing.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import posixpath
import re
import struct
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlparse

CORE = "1ae4674a4b153701b0c3b3ff04b1a1b77a318611"
PLUGIN = "697291a27818612ae9dc53d83d4f99fa5887908e"
NATIVE_SOURCE = "194a6c9dd70873a472e441b67875766541572372"
NATIVE_RUN = "44863517943"
LOCK_SHA = "0aaa998ab74802473ad0186b0a17f8b6d9e8302a44de6d072af6bf3d3de31a66"
LOCK_BLOB = "1a7428add5902ce7d4ae48106bdf24a732aae48c"
ABI_SHA = "d12d803c7ec7fc6d6ccb3d3abbb705b9748452da1873de86a699e37459c4486a"
MAX_MEMBER = 256 * 1024 * 1024
SYSTEM_ELF = {
    "android": {"libc.so", "libm.so", "libdl.so", "liblog.so", "libandroid.so", "libz.so"},
    "ohos": {"libc.so", "libm.so", "libdl.so", "libhilog_ndk.z.so", "libace_napi.z.so"},
}
EXPECTED_ABIS = {"android": {"arm64-v8a", "armeabi-v7a", "x86_64"},
                 "ohos": {"arm64-v8a", "x86_64"}}


class Blocked(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Blocked(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    require(result.returncode == 0, f"git-source-unavailable: {args[0]}")
    return result.stdout


def blob_id(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data,
                        usedforsecurity=False).hexdigest()


def safe_name(value):
    require(isinstance(value, str) and value and "\\" not in value and
            "\0" not in value and ":" not in value and not value.startswith("/"),
            "unsafe-member-path")
    while value.startswith("./"):
        value = value[2:]
    path = PurePosixPath(value)
    require(value and ".." not in path.parts, "unsafe-member-path")
    return path.as_posix()


def read_json(path):
    require(path.is_file() and not path.is_symlink(), f"missing-native-contract: {path}")
    require(path.stat().st_size <= 1024 * 1024, "oversized-json-input")
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def package_root(root, name):
    configuration = root / ".dart_tool/package_config.json"
    value = read_json(configuration)
    matches = [p for p in value.get("packages", []) if p.get("name") == name]
    require(len(matches) == 1, f"missing-resolved-package: {name}")
    uri = urlparse(urljoin(configuration.as_uri(), matches[0]["rootUri"]))
    require(uri.scheme == "file" and uri.netloc in ("", "localhost"), "nonlocal-package-root")
    decoded = unquote(uri.path)
    if os.name == "nt" and re.match(r"^/[A-Za-z]:/", decoded):
        decoded = decoded[1:]
    return Path(decoded).resolve(strict=True)


def bounded(data, offset, length):
    require(0 <= offset <= len(data) and 0 <= length <= len(data) - offset, "invalid-binary-bounds")
    return data[offset:offset + length]


def cstring(data, offset):
    require(0 <= offset < len(data), "invalid-string-offset")
    end = data.find(b"\0", offset)
    require(end >= offset, "unterminated-binary-string")
    return data[offset:end].decode("utf-8", errors="strict")


def elf_info(data):
    require(data[:4] == b"\x7fELF" and data[4] in (1, 2) and data[5] == 1, "unsupported-elf")
    bits = 64 if data[4] == 2 else 32
    header = struct.unpack_from("<HHIQQQIHHHHHH" if bits == 64 else "<HHIIIIIHHHHHH", data, 16)
    machine = header[1]
    architecture = {(64, 183): "arm64-v8a", (32, 40): "armeabi-v7a", (64, 62): "x86_64"}.get((bits, machine))
    require(architecture is not None, "unsupported-elf-architecture")
    phoff, shoff, phsize, phcount, shsize, shcount, names_index = (
        header[4], header[5], header[8], header[9], header[10], header[11], header[12])
    require(0 < shcount <= 65535 and names_index < shcount and phcount <= 4096, "invalid-elf-tables")
    section_format = "<IIQQQQIIQQ" if bits == 64 else "<IIIIIIIIII"
    require(shsize >= struct.calcsize(section_format), "invalid-elf-section-size")
    sections = [struct.unpack(section_format, bounded(data, shoff + i * shsize, struct.calcsize(section_format)))
                for i in range(shcount)]
    strings = bounded(data, sections[names_index][4], sections[names_index][5])
    exports, needed, allocated, alignments, segments = set(), set(), [], [], []
    for item in sections:
        name = cstring(strings, item[0])
        kind, flags, address, offset, length, link, stride = item[1], item[2], item[3], item[4], item[5], item[6], item[9]
        body = b"" if kind == 8 else bounded(data, offset, length)
        if flags & 2 and kind != 8 and not name.startswith((".note", ".gnu_debug")):
            allocated.append([name, kind, flags, address, length, sha(body)])
        if kind == 11:
            require(link < len(sections), "invalid-elf-symbol-strings")
            table = bounded(data, sections[link][4], sections[link][5])
            size = 24 if bits == 64 else 16
            require(stride >= size and length % stride == 0, "invalid-elf-symbol-table")
            for index in range(0, length, stride):
                entry = struct.unpack_from("<IBBHQQ" if bits == 64 else "<IIIBBH", body, index)
                symbol, info, visibility, defined = (entry[0], entry[1], entry[2], entry[3]) if bits == 64 else (entry[0], entry[3], entry[4], entry[5])
                if defined and info >> 4 in (1, 2) and visibility & 3 in (0, 3):
                    exports.add(cstring(table, symbol))
        if kind == 6:
            require(link < len(sections), "invalid-elf-dynamic-strings")
            table = bounded(data, sections[link][4], sections[link][5])
            size = 16 if bits == 64 else 8
            require(stride >= size and length % stride == 0, "invalid-elf-dynamic-table")
            for index in range(0, length, stride):
                tag, value = struct.unpack_from("<qQ" if bits == 64 else "<iI", body, index)
                if tag == 1:
                    needed.add(cstring(table, value))
    phformat = "<IIQQQQQQ" if bits == 64 else "<IIIIIIII"
    require(phsize >= struct.calcsize(phformat), "invalid-elf-program-size")
    for index in range(phcount):
        entry = struct.unpack(phformat, bounded(data, phoff + index * phsize, struct.calcsize(phformat)))
        if entry[0] == 1:
            alignments.append(entry[7])
            segments.append([entry[1], entry[3], entry[5], entry[6], entry[7]] if bits == 64
                            else [entry[6], entry[2], entry[4], entry[5], entry[7]])
    require(allocated and alignments, "empty-elf-payload")
    return {"kind": "elf", "architecture": architecture, "exports": sorted(exports),
            "needed": sorted(needed), "loadAlignments": alignments,
            "filetype": header[0],
            "payloadSha256": sha(json.dumps([sorted(allocated), segments], separators=(",", ":")).encode())}


def uleb(data, position):
    value, shift = 0, 0
    while True:
        require(position < len(data) and shift <= 63, "invalid-export-trie")
        byte = data[position]
        position += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, position
        shift += 7


def trie_exports(data):
    exports, visited = set(), set()
    pending = [(0, "")]
    while pending:
        offset, prefix = pending.pop()
        require(offset not in visited and len(visited) < 100000, "cyclic-export-trie")
        visited.add(offset)
        length, start = uleb(data, offset)
        position = start + length
        require(position < len(data) and len(prefix) <= 4096, "invalid-export-trie")
        if length:
            exports.add(prefix.removeprefix("_"))
        count = data[position]
        position += 1
        for _ in range(count):
            label = cstring(data, position)
            position += len(label.encode()) + 1
            child, position = uleb(data, position)
            pending.append((child, prefix + label))
    return exports


def macho_info(data):
    magic = data[:4]
    if magic in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf", b"\xbe\xba\xfe\xca", b"\xbf\xba\xfe\xca"):
        endian = ">" if magic[:1] == b"\xca" else "<"
        wide = magic in (b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca")
        count = struct.unpack(endian + "I", bounded(data, 4, 4))[0]
        require(0 < count <= 16, "invalid-macho-fat-count")
        slices = []
        for index in range(count):
            fmt = endian + ("IIQQII" if wide else "IIIII")
            size = struct.calcsize(fmt)
            entry = struct.unpack(fmt, bounded(data, 8 + index * size, size))
            slices.extend(macho_info(bounded(data, entry[2], entry[3]))["slices"])
        require(len({s["architecture"] for s in slices}) == len(slices), "duplicate-macho-slice")
        return {"kind": "macho", "slices": slices}
    formats = {b"\xcf\xfa\xed\xfe": ("<", True), b"\xfe\xed\xfa\xcf": (">", True),
               b"\xce\xfa\xed\xfe": ("<", False), b"\xfe\xed\xfa\xce": (">", False)}
    require(magic in formats, "unsupported-macho")
    endian, wide = formats[magic]
    header_size = 32 if wide else 28
    cpu, _, filetype, count, command_bytes, _ = struct.unpack(endian + "IIIIII", bounded(data, 4, 24))
    architecture = {0x100000C: "arm64", 0x1000007: "x86_64", 12: "arm", 7: "x86"}.get(cpu)
    require(architecture and count <= 65535, "invalid-macho-header")
    end = header_size + command_bytes
    require(end <= len(data), "invalid-macho-commands")
    position, exports, needed, sections, loader_data = header_size, set(), set(), [], []
    for _ in range(count):
        command, size = struct.unpack(endian + "II", bounded(data, position, 8))
        require(size >= 8 and position + size <= end, "invalid-macho-command")
        body = bounded(data, position, size)
        if command in (1, 0x19):
            segment_wide = command == 0x19
            section_count = struct.unpack_from(endian + "I", body, 64 if segment_wide else 48)[0]
            section_start, section_size = (72, 80) if segment_wide else (56, 68)
            require(section_start + section_count * section_size <= size, "invalid-macho-sections")
            for index in range(section_count):
                part = bounded(body, section_start + index * section_size, section_size)
                name = part[:16].split(b"\0")[0].decode()
                segment = part[16:32].split(b"\0")[0].decode()
                address, length = struct.unpack_from(endian + ("QQ" if segment_wide else "II"), part, 32)
                offset = struct.unpack_from(endian + "I", part, 48 if segment_wide else 40)[0]
                flags = struct.unpack_from(endian + "I", part, 64 if segment_wide else 56)[0]
                if flags & 255 not in (1, 12, 18) and segment not in ("__LINKEDIT", "__DWARF"):
                    sections.append([segment, name, address, length, flags, sha(bounded(data, offset, length))])
        elif command == 2:
            symbols, total, strings, string_size = struct.unpack_from(endian + "IIII", body, 8)
            table = bounded(data, strings, string_size)
            stride = 16 if wide else 12
            require(total <= len(data) // stride, "invalid-macho-symbol-count")
            for index in range(total):
                entry = bounded(data, symbols + index * stride, stride)
                string_index, symbol_type = struct.unpack_from(endian + "IB", entry)
                if symbol_type & 1 and not symbol_type & 0xE0 and symbol_type & 0x0E:
                    exports.add(cstring(table, string_index).removeprefix("_"))
        elif command in (0x22, 0x80000022, 0x80000033, 0x80000034):
            if command in (0x22, 0x80000022):
                for index in range(5):
                    offset, length = struct.unpack_from(endian + "II", body, 8 + index * 8)
                    loader_data.append([command, index, sha(bounded(data, offset, length))])
                offset, length = struct.unpack_from(endian + "II", body, 40)
            else:
                offset, length = struct.unpack_from(endian + "II", body, 8)
                loader_data.append([command, sha(bounded(data, offset, length))])
            if length and command != 0x80000034:
                exports.update(trie_exports(bounded(data, offset, length)))
        elif command in (0xC, 0x80000018, 0x8000001F, 0x80000023):
            needed.add(cstring(body, struct.unpack_from(endian + "I", body, 8)[0]))
        position += size
    require(position == end and sections, "invalid-macho-payload")
    return {"kind": "macho", "slices": [{"architecture": architecture, "filetype": filetype,
            "exports": sorted(exports), "needed": sorted(needed),
            "payloadSha256": sha(json.dumps([sorted(sections), loader_data], separators=(",", ":")).encode())}]}


def native_info(data, platform, required):
    info = elf_info(data) if data.startswith(b"\x7fELF") else macho_info(data)
    for part in info.get("slices", [info]):
        require(set(required) <= set(part["exports"]), "missing-native-exports")
        if info["kind"] == "elf":
            require(part["filetype"] == 3, "native-library-is-not-shared-elf")
            require(platform in SYSTEM_ELF and set(part["needed"]) <= SYSTEM_ELF[platform],
                    f"unlocked-native-runtime-dependency: {part['needed']}")
            require(min(part["loadAlignments"]) >= 16384, "native-page-alignment-below-16k")
        else:
            require(part["filetype"] == 6, "native-framework-is-not-dylib")
            require(all(n.startswith(("/usr/lib/", "/System/Library/")) for n in part["needed"]),
                    f"unlocked-framework-runtime-dependency: {part['needed']}")
    return info


def identities(root, contract_path):
    contract = read_json(contract_path)
    require(contract.get("schemaVersion") == 1 and contract.get("status") == "approved" and
            contract.get("mode") == "bundled-git-blob", "missing-native-contract: unapproved/unsupported contract")
    require(contract.get("core") == {"repository": "azurekiln2333/qflistudio-core", "commit": CORE} and
            contract.get("plugin") == {"package": "qfli_git", "repository": "azurekiln2333/qflistudio-git", "commit": PLUGIN},
            "native-contract-pin-mismatch")
    core, plugin = package_root(root, "qfli_studio_core"), package_root(root, "qfli_git")
    require(git(core, "rev-parse", "HEAD").decode().strip() == CORE, "resolved-core-pin-mismatch")
    require(git(plugin, "rev-parse", "HEAD").decode().strip() == PLUGIN, "resolved-native-plugin-pin-mismatch")
    core_spec = (core / "pubspec.yaml").read_bytes()
    require(core_spec == git(core, "show", f"{CORE}:pubspec.yaml") and PLUGIN.encode() in core_spec,
            "modified-core-native-dependency")
    root_lock = (root / "pubspec.lock").read_text(encoding="utf-8")
    match = re.search(r"(?m)^  qfli_git:\n(?P<body>(?: {4}[^\n]*\n|\n)*)", root_lock)
    require(match and f'resolved-ref: "{PLUGIN}"' in match["body"] and
            'url: "https://github.com/azurekiln2333/qflistudio-git.git"' in match["body"], "unlocked-root-native-dependency")
    expected = contract.get("upstreamLock", {})
    require(expected == {"path": "native_libs.lock.json", "gitBlob": LOCK_BLOB, "bytes": 11314,
                        "sha256": LOCK_SHA, "schemaVersion": 2, "apiVersion": 3, "contractSha256": ABI_SHA},
            "native-lock-anchor-mismatch")
    lock_raw = (plugin / "native_libs.lock.json").read_bytes()
    require(len(lock_raw) == 11314 and sha(lock_raw) == LOCK_SHA and blob_id(lock_raw) == LOCK_BLOB and
            lock_raw == git(plugin, "show", f"{PLUGIN}:native_libs.lock.json"), "native-lock-content-mismatch")
    lock = json.loads(lock_raw)
    abi_raw = (plugin / "tool/ci/native_contract.json").read_bytes()
    require(sha(abi_raw) == ABI_SHA, "native-abi-contract-mismatch")
    abi_contract = json.loads(abi_raw)
    require(lock.get("schemaVersion") == 2 and lock.get("apiVersion") == 3 and
            lock.get("contractSha256") == ABI_SHA and abi_contract.get("apiVersion") == 3 and
            lock.get("requiredExports") == abi_contract.get("requiredExports"), "native-api-contract-mismatch")
    source = lock.get("source", {})
    require(contract.get("nativeSource") == {"commit": NATIVE_SOURCE, "runId": NATIVE_RUN} and
            source.get("commit") == NATIVE_SOURCE and
            source.get("run") == f"https://github.com/azurekiln2333/qflistudio-git/actions/runs/{NATIVE_RUN}" and
            source.get("commits") == dict.fromkeys(("android", "ios", "ohos"), NATIVE_SOURCE), "native-source-mismatch")
    ca_contract = contract.get("caBundle")
    require(ca_contract == {"path": "assets/cacert.pem", "gitBlob": "4a38c72a9e1a35c4c24459989b18fd455be1b78e"}, "ca-anchor-mismatch")
    ca = (plugin / "assets/cacert.pem").read_bytes()
    require(blob_id(ca) == ca_contract["gitBlob"] and ca == git(plugin, "show", f"{PLUGIN}:assets/cacert.pem"), "native-ca-mismatch")
    records, material = [], {"native_libs.lock.json": lock_raw, "tool/ci/native_contract.json": abi_raw, "assets/cacert.pem": ca}
    files = lock.get("files", [])
    require(len(files) == 10 and len({f["path"] for f in files}) == 10, "native-file-inventory-mismatch")
    for record in files:
        name = safe_name(record["path"])
        path = plugin / name
        require(not path.is_symlink() and path.resolve().is_relative_to(plugin), "native-input-link-escape")
        require(path.is_file() and path.stat().st_size == record["bytes"] <= MAX_MEMBER, "native-input-size-mismatch")
        data = path.read_bytes()
        require(sha(data) == record["sha256"], f"native-input-hash-mismatch: {name}")
        item = dict(record)
        if name.endswith(".so") or name.endswith(".framework/qfli_git"):
            item["binary"] = native_info(data, record["platform"], lock["requiredExports"])
            if name.endswith(".so"):
                require(item["binary"]["architecture"] == record["abi"], "native-input-abi-mismatch")
        records.append(item)
        material[name] = data
    for platform, wanted in EXPECTED_ABIS.items():
        require({f["abi"] for f in files if f["platform"] == platform} == wanted, "native-input-platform-coverage-mismatch")
    ios = {f["path"]: f for f in records if "binary" in f and f["platform"] == "ios"}
    for suffix, wanted in (("ios-arm64", {"arm64"}), ("ios-arm64_x86_64-simulator", {"arm64", "x86_64"})):
        info = ios[f"ios/Frameworks/qfli_git.xcframework/{suffix}/qfli_git.framework/qfli_git"]["binary"]
        require({s["architecture"] for s in info["slices"]} == wanted, "native-ios-slice-mismatch")
    # The exact package tree must supply integration metadata as well as binaries.
    for name in ("pubspec.yaml", "android/build.gradle", "ios/qfli_git.podspec", "lib/src/library.dart", "lib/src/bindings.dart", "native/CMakeLists.txt", "LICENSE"):
        contents = (plugin / name).read_bytes()
        require(contents == git(plugin, "show", f"{PLUGIN}:{name}"), f"modified-native-integration: {name}")
        material[name] = contents
    return contract, records, material, ca


def package_members(path):
    require(path.is_file() and not path.is_symlink(), f"missing-inspectable-package: {path}")
    seen = set()
    def accepted(name):
        normalized = safe_name(name)
        require(normalized not in seen, "duplicate-package-member")
        seen.add(normalized)
        require(len(seen) <= 100000, "oversized-package-inventory")
        return normalized
    if path.suffix.lower() in (".zip", ".apk", ".aab", ".ipa", ".hap"):
        with zipfile.ZipFile(path) as bundle:
            require(len(bundle.infolist()) <= 100000, "oversized-package-inventory")
            for item in bundle.infolist():
                name = accepted(item.filename)
                if item.is_dir():
                    continue
                require(not item.flag_bits & 1, "encrypted-package-member")
                require((item.external_attr >> 16) & 0o170000 != 0o120000, "zip-symlink-use-tar-instead")
                yield name, item.file_size, lambda i=item: bundle.read(i)
    elif path.name.endswith((".tar", ".tar.gz", ".tgz")):
        with tarfile.open(path, "r:*") as bundle:
            for item in bundle:
                name = accepted(item.name)
                if item.isdir():
                    continue
                if item.issym() or item.islnk():
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), item.linkname) if item.issym() else item.linkname)
                    safe_name(target)
                    continue
                require(item.isfile(), "unsupported-tar-member")
                yield name, item.size, lambda i=item: bundle.extractfile(i).read(MAX_MEMBER + 1)
    else:
        raise Blocked(f"opaque-or-unsupported-package: {path.name}; supply inspectable payload archive")


def packaged_fingerprint(actual, expected):
    if actual["kind"] != expected["kind"]:
        return False
    if actual["kind"] == "elf":
        return all(actual[key] == expected[key] for key in ("architecture", "filetype", "exports", "needed", "payloadSha256", "loadAlignments"))
    wanted = {s["architecture"]: s for s in expected["slices"]}
    return len(actual["slices"]) == len(wanted) and all(wanted.get(s["architecture"]) == s for s in actual["slices"])


def inspect_package(path, target, records, ca, required, architectures):
    inputs = [f for f in records if f["platform"] == target and "binary" in f]
    native, ca_members, inventory, app_archs = [], [], [], set()
    native_arch_paths = set()
    for name, size, read in package_members(path):
        basename = PurePosixPath(name).name
        is_git = basename == "libqfli_git.so" or bool(re.search(r"/qfli_git\.framework/(?:Versions/[^/]+/)?qfli_git$", name))
        is_ca = name.endswith("/packages/qfli_git/assets/cacert.pem")
        is_main = ((target == "windows" and basename == "qfli_json.exe") or
                   (target == "linux" and basename == "qfli_json") or
                   (target == "macos" and "/QFLIJson.app/Contents/MacOS/" in "/" + name) or
                   (target == "ios" and bool(re.search(r"(?:^|/)Payload/[^/]+\.app/Runner$", name))))
        is_native = is_git or bool(re.search(r"\.(?:so(?:\.\d+)*|dll|dylib)$", basename)) or ".framework/" in name and not basename.endswith((".plist", ".h", ".modulemap"))
        if not (is_git or is_ca or is_main or is_native):
            continue
        require(0 <= size <= MAX_MEMBER, "oversized-native-member")
        data = read()
        require(len(data) == size, "truncated-native-member")
        digest = sha(data)
        if is_ca:
            require(data == ca, "packaged-native-ca-mismatch")
            ca_members.append(name)
        if is_native and data[:4] in (b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf") or is_native and data[:2] == b"MZ":
            inventory.append({"path": name, "bytes": size, "sha256": digest})
            if target in ("android", "ohos") and basename in ("libapp.so", "libflutter.so"):
                info = elf_info(data)
                native_arch_paths.add((basename, info["architecture"]))
        if is_git:
            require(target in ("android", "ohos", "ios"), "unexpected-desktop-qfli-git-library")
            actual = native_info(data, target, required)
            if target in ("android", "ohos"):
                prefix = r"(?:base/)?lib" if target == "android" else "libs"
                match = re.fullmatch(prefix + r"/([^/]+)/libqfli_git\.so", name)
                require(match and match[1] == actual["architecture"], "packaged-native-location-mismatch")
                candidates = [f for f in inputs if f["abi"] == match[1]]
            else:
                require(re.fullmatch(r"Payload/[^/]+\.app/Frameworks/qfli_git\.framework/qfli_git", name), "packaged-framework-location-mismatch")
                candidates = [f for f in inputs if "/ios-arm64/" in f["path"]]
            require(len(candidates) == 1, "unlocked-packaged-native-abi")
            expected = candidates[0]
            require(packaged_fingerprint(actual, expected["binary"]), "packaged-native-code-or-dependency-drift")
            native.append({"path": name, "bytes": size, "sha256": digest, "sourcePath": expected["path"],
                           "sourceSha256": expected["sha256"], "identity": "byte-identical" if digest == expected["sha256"] else "allocated-code-data-and-exports-identical",
                           "architectures": [s["architecture"] for s in actual["slices"]] if target == "ios" else [actual["architecture"]]})
        if is_main:
            if target == "windows":
                require(data[:2] == b"MZ", "invalid-windows-executable")
                offset = struct.unpack_from("<I", data, 0x3C)[0]
                require(bounded(data, offset, 4) == b"PE\0\0", "invalid-windows-pe")
                machine = struct.unpack("<H", bounded(data, offset + 4, 2))[0]
                require(machine == 0x8664, "windows-package-architecture-mismatch")
                app_archs.add("x86_64")
            elif target == "linux":
                app_archs.add(elf_info(data)["architecture"])
            else:
                app_archs.update(s["architecture"] for s in macho_info(data)["slices"])
    require(ca_members, "missing-packaged-native-ca")
    if target in ("android", "ohos", "ios"):
        require(native and len({a for record in native for a in record["architectures"]}) == sum(len(record["architectures"]) for record in native), "missing-or-duplicate-packaged-native-library")
        found = {a for record in native for a in record["architectures"]}
        require(found <= set(architectures), "unrequested-packaged-native-architecture")
        if target in ("ios", "ohos") or path.suffix == ".aab":
            require(found == set(architectures), "incomplete-package-native-architecture-coverage")
        if target == "ios":
            require(app_archs == set(architectures), "ios-runner-architecture-mismatch")
        else:
            require({(name, architecture) for name in ("libapp.so", "libflutter.so") for architecture in found} <= native_arch_paths,
                    "missing-or-mismatched-flutter-native-library")
    else:
        require(app_archs == set(architectures), "incomplete-desktop-package-architecture-coverage")
        found = app_archs
    return {"path": path.as_posix(), "bytes": path.stat().st_size, "sha256": file_sha(path),
            "architectures": sorted(found), "qfliGit": native, "caMembers": ca_members, "nativeInventory": inventory}


def run(args, root, output, evidence):
    contract_path = (root / args.contract).resolve()
    contract, records, material, ca = identities(root, contract_path)
    configuration = contract.get("targets", {}).get(args.target)
    expected_archs = {"windows": ["x86_64"], "linux": ["x86_64"], "macos": ["arm64", "x86_64"],
                      "ios": ["arm64"], "android": ["armeabi-v7a", "arm64-v8a", "x86_64"], "ohos": ["arm64-v8a"]}[args.target]
    backend = "external-git-cli" if args.target in ("windows", "linux", "macos") else "qfli-git-ffi"
    require(configuration == {"backend": backend, "architectures": expected_archs}, "native-target-contract-mismatch")
    evidence.update({"contractSha256": file_sha(contract_path), "coreCommit": CORE, "pluginCommit": PLUGIN,
                     "nativeSourceCommit": NATIVE_SOURCE, "historicalProducerRunId": NATIVE_RUN,
                     "upstreamRelease": None, "sourceMode": "bundled-git-blob", "backend": backend,
                     "deviceValidation": "not-run", "signingValidation": "not-performed"})
    if args.phase == "prepare":
        require(not args.package, "prepare-does-not-accept-packages")
        archive = output / "native-inputs.tar.gz"
        temporary = archive.with_suffix(".tmp")
        with temporary.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped, tarfile.open(fileobj=zipped, mode="w|") as bundle:
            material["json-consumer-contract.json"] = contract_path.read_bytes()
            for name, data in sorted(material.items()):
                item = tarfile.TarInfo("qfli_git/" + name)
                item.size, item.mode, item.mtime = len(data), 0o644, 0
                bundle.addfile(item, io.BytesIO(data))
        temporary.replace(archive)
        evidence.update({"status": "prepared", "files": records, "caSha256": sha(ca),
                         "archive": {"path": archive.as_posix(), "bytes": archive.stat().st_size, "sha256": file_sha(archive)},
                         "durablePublication": "required-separate-release-or-immutable-store"})
        (output / "SHA256SUMS").write_text(f"{evidence['archive']['sha256']}  native-inputs.tar.gz\n", encoding="utf-8")
    else:
        prepared = read_json(output / "prepare.json")
        require(prepared.get("status") == "prepared" and all(prepared.get(k) == evidence.get(k) for k in
                ("repository", "appCommit", "runId", "runAttempt", "target", "contractSha256", "pluginCommit", "coreCommit")), "stale-native-preparation")
        require(args.package, "missing-inspectable-runtime-packages")
        archive = output / "native-inputs.tar.gz"
        require(file_sha(archive) == prepared["archive"]["sha256"], "prepared-native-archive-drift")
        packages = [(root / p).resolve(strict=True) for p in args.package]
        require(len(set(packages)) == len(packages), "duplicate-runtime-package")
        results = [inspect_package(path, args.target, records, ca,
                   json.loads(material["native_libs.lock.json"])["requiredExports"], expected_archs) for path in packages]
        require({a for result in results for a in result["architectures"]} == set(expected_archs), "incomplete-target-native-coverage")
        evidence.update({"status": "verified-packaging", "packages": results,
                         "runtimeValidation": "not-run", "installerValidation": "not-performed",
                         "durablePublication": "required-separate-release-or-immutable-store"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=["windows", "linux", "macos", "macos-universal", "ios", "android", "ohos"])
    parser.add_argument("--phase", required=True, choices=["prepare", "verify"])
    parser.add_argument("--contract", default="tool/ci/native-contract.json")
    parser.add_argument("--package", action="append", default=[])
    args = parser.parse_args()
    # Refuse all local execution, including missing-contract probes.
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_SERVER_URL") != "https://github.com":
        print("::error::cloud-only-native-helper: run on GitHub Actions, not locally", file=sys.stderr)
        return 2
    args.target = "macos" if args.target == "macos-universal" else args.target
    root = Path.cwd().resolve()
    output = root / "build/ci-native" / args.target
    output.mkdir(parents=True, exist_ok=True)
    evidence = {"status": "running", "target": args.target, "phase": args.phase,
                "repository": os.environ.get("GITHUB_REPOSITORY"), "appCommit": os.environ.get("GITHUB_SHA"),
                "runId": os.environ.get("GITHUB_RUN_ID"), "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT")}
    destination = output / f"{args.phase}.json"
    atomic_json(destination, evidence)
    try:
        require(evidence["repository"] == "azurekiln2333/qflistudio-json" and
                re.fullmatch(r"[0-9a-f]{40}", evidence["appCommit"] or "") and
                all(re.fullmatch(r"[1-9][0-9]*", evidence[k] or "") for k in ("runId", "runAttempt")), "missing-trusted-cloud-identity")
        require(git(root, "rev-parse", "HEAD").decode().strip() == evidence["appCommit"], "app-source-identity-mismatch")
        run(args, root, output, evidence)
    except (Blocked, OSError, ValueError, KeyError, IndexError, TypeError, struct.error, tarfile.TarError, zipfile.BadZipFile) as error:
        evidence.update({"status": "blocked", "error": str(error)[:2000]})
        atomic_json(destination, evidence)
        print(f"::error::native-dependency-blocked: {str(error)[:2000]}", file=sys.stderr)
        return 2
    atomic_json(destination, evidence)
    print(json.dumps({"status": evidence["status"], "evidence": destination.relative_to(root).as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
