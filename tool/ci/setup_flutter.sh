#!/usr/bin/env bash
# Executed only by GitHub Actions. Never call this helper in a local workspace.
set -euo pipefail

if [ "${GITHUB_ACTIONS:-}" != true ]; then
  echo 'cloud-only: Flutter installation is restricted to GitHub Actions' >&2
  exit 2
fi
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo 'usage: setup_flutter.sh <directory> <version> <commit> [--ohos]' >&2
  exit 2
fi

target="$1"
version="$2"
expected="$3"
[[ "$expected" =~ ^[0-9a-f]{40}$ ]] || { echo 'invalid Flutter commit' >&2; exit 2; }
[[ "$version" =~ ^[0-9][0-9A-Za-z.+_-]*$ ]] || { echo 'invalid Flutter version' >&2; exit 2; }
case "${4:-}" in
  '') repository='https://github.com/flutter/flutter.git' ;;
  --ohos) repository='https://gitcode.com/openharmony-tpc/flutter_flutter.git' ;;
  *) echo 'invalid Flutter mode' >&2; exit 2 ;;
esac
# A fresh, per-job runner directory avoids trusting a mutable SDK cache.
if [ -e "$target" ]; then
  echo 'Flutter target already exists; refusing to reuse an unverified SDK' >&2
  exit 1
fi
mkdir -p "$target"
git -C "$target" init --quiet
git -C "$target" remote add origin "$repository"
git -C "$target" -c advice.detachedHead=false fetch --no-tags --depth=1 origin "$expected"
git -C "$target" -c advice.detachedHead=false checkout --detach --quiet FETCH_HEAD
actual="$(git -C "$target" rev-parse HEAD)"
if [ "$actual" != "$expected" ]; then
  echo 'Flutter source commit mismatch' >&2
  exit 1
fi
# Tags are a secondary identity check, never a substitute for the full commit.
tag_commit="$(git ls-remote --tags "$repository" "refs/tags/$version" "refs/tags/$version^{}" | awk 'END {print $1}')"
if [ -z "$tag_commit" ] || [ "$tag_commit" != "$expected" ]; then
  echo 'Flutter version tag is missing or does not identify the locked commit' >&2
  exit 1
fi
printf 'Flutter source verified: %s (%s)\n' "$version" "$actual"
