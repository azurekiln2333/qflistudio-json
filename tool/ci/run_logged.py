"""Run one cloud command with a bounded diagnostic tail and exact exit status."""
from __future__ import annotations

import argparse
from collections import deque
import os
from pathlib import Path
import re
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("cloud-only: command execution is restricted to GitHub Actions")
    if not re.fullmatch(r"[a-z0-9-]+", args.name):
        parser.error("invalid log name")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("missing command")
    # Windows Flutter and Dart entry points are .bat wrappers; resolve explicitly.
    if os.name == "nt" and command[0] in ("flutter", "dart"):
        command = ["cmd.exe", "/d", "/s", "/c", subprocess.list2cmdline(command)]
    log = Path("build/ci-logs") / f"{args.name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    tail: deque[bytes] = deque()
    size = 0
    limit = 2 * 1024 * 1024
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert process.stdout is not None
        while chunk := process.stdout.read1(8192):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            tail.append(chunk)
            size += len(chunk)
            while size > limit and tail:
                size -= len(tail.popleft())
        result = process.wait()
    except OSError as error:
        tail.append(f"Could not start command: {type(error).__name__}\n".encode())
        result = 127
    log.write_bytes(b"Bounded command-output tail; this is not the complete log.\n" + b"".join(tail))
    raise SystemExit(result)


if __name__ == "__main__":
    main()
