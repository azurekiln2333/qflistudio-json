"""Collect bounded cloud diagnostics; never upload entire build/cache trees."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

PATTERNS = {
    "flutter": (
        "build/ci-logs/*.log", "build/ci-state/*.json", "build/ci-packages/package-manifest.json",
        ".dart_tool/package_config.json", ".dart_tool/package_graph.json",
        "build/**/CMakeCache.txt", "build/**/CMakeConfigureLog.yaml",
        "build/**/flutter_build.d", "build/**/flutter_assemble.d",
        "build/**/outputs/logs/manifest-merger-release-report.txt",
    ),
    "native": (
        "build/ci-native/*.json", "build/ci-native/*.log", "build/ci-native/**/*.json",
        "build/ci-native/**/*.log", "build/ci-native-evidence/*.json",
        "build/ci-state/native*.json", "build/ci-logs/native*.log",
        "build/ci-ohos/*.json", "build/ci-ohos/*.log",
    ),
}


def main() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("cloud-only: diagnostic collection requires GitHub Actions")
    root = Path.cwd().resolve()
    output = Path("build/ci-diagnostics")
    for kind, patterns in PATTERNS.items():
        destination = output / kind
        destination.mkdir(parents=True, exist_ok=True)
        count = size = 0
        omitted = []
        seen = set()
        for pattern in patterns:
            for path in sorted(Path.cwd().glob(pattern)):
                if path in seen:
                    continue
                seen.add(path)
                if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
                    continue
                relative = path.relative_to(Path.cwd())
                if path.stat().st_size > 1024 * 1024 or count >= 64 or size + path.stat().st_size > 16 * 1024 * 1024:
                    omitted.append(relative.as_posix())
                    continue
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                count += 1
                size += path.stat().st_size
        (destination / "COLLECTION.json").write_text(json.dumps({
            "files": count, "bytes": size, "max_files": 64, "max_total_bytes": 16 * 1024 * 1024,
            "max_file_bytes": 1024 * 1024, "omitted_paths": omitted,
            "coverage": "selected diagnostics only; no build output or secret/signing directories",
        }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
