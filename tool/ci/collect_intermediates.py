"""Archive explicitly allowed cloud-generated intermediates with strict size caps.

Never walks a Pub cache, home directory or linked plugin checkout. Collection
is diagnostic only: omitted files are recorded and never imply complete inputs.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tarfile

MAX_FILE = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_FILES = 256
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".cer", ".crt", ".p7b", ".mobileprovision"}
FLUTTER_SUFFIXES = {".dill", ".d", ".json", ".stamp", ".snapshot", ".cache", ".bin", ".so", ".a", ".o", ".obj"}
NATIVE_SUFFIXES = {".o", ".obj", ".so", ".dylib", ".dll", ".a", ".lib", ".pdb", ".d", ".ninja", ".map"}


def candidates(kind: str):
    roots = [Path(".dart_tool/flutter_build")] if kind == "flutter" else [Path("build"), Path("ohos/entry/build"), Path("ohos/.cxx")]
    if kind == "flutter":
        roots.append(Path("build/ohos/intermediates/flutter"))
    for root in roots:
        if not root.is_dir() or root.is_symlink():
            continue
        for directory, directories, files in os.walk(root, followlinks=False):
            parent = Path(directory)
            directories[:] = [name for name in directories if not (parent / name).is_symlink()
                              and not (parent / name).is_junction()
                              and name not in {"ci-artifacts", "ci-packages", "ci-intermediates", "ci-diagnostics", "ci-native", ".git", "node_modules", "oh_modules"}]
            for name in sorted(files):
                path = parent / name
                if path.is_symlink() or path.suffix.lower() in SECRET_SUFFIXES or name.startswith(".env"):
                    continue
                if kind == "flutter" and (path.suffix.lower() in FLUTTER_SUFFIXES or name in {"kernel_blob.bin", "isolate_snapshot_data"}):
                    yield path
                if kind == "native" and (path.suffix.lower() in NATIVE_SUFFIXES or any(part.endswith(".dSYM") for part in path.parts)
                                         or ".cxx" in path.parts and path.suffix in {".txt", ".json"}):
                    yield path


def main() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("cloud-only: intermediate collection requires GitHub Actions")
    root = Path.cwd().resolve()
    for kind in ("flutter", "native"):
        output = Path("build/ci-intermediates") / kind
        output.mkdir(parents=True, exist_ok=True)
        selected, omitted = [], []
        total = 0
        seen = set()
        archive = output / f"{kind}-intermediates.tar.gz"
        with tarfile.open(archive, "w:gz", dereference=False) as bundle:
            for path in candidates(kind):
                if path in seen:
                    continue
                seen.add(path)
                if not path.is_file() or not path.resolve().is_relative_to(root):
                    continue
                size = path.stat().st_size
                relative = path.as_posix()
                if size > MAX_FILE or total + size > MAX_TOTAL or len(selected) >= MAX_FILES:
                    omitted.append({"path": relative, "bytes": size, "reason": "bounded-retention-size-cap"})
                    continue
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                bundle.add(path, arcname=relative, recursive=False)
                selected.append({"path": relative, "bytes": size, "sha256": digest.hexdigest(),
                                 "mode": oct(path.stat().st_mode & 0o777)})
                total += size
        (output / "INTERMEDIATE_MANIFEST.json").write_text(json.dumps({
            "kind": kind, "files": selected, "omitted": omitted, "uncompressed_bytes": total,
            "limits": {"files": MAX_FILES, "file_bytes": MAX_FILE, "total_bytes": MAX_TOTAL},
            "retention_days": 3, "app_commit": os.environ.get("GITHUB_SHA"),
            "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "scope": "allowlisted generated intermediates only; never the entire build tree or any dependency cache",
        }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
