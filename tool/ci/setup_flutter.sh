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
# Flutter derives its framework version from LOCAL Git tags. Checking a remote
# tag alone leaves a SHA-only checkout at 0.0.0-unknown during Pub resolution.
# Fetch only the reviewed tag, then peel it and recheck against the source pin.
# Do not create a synthetic tag or trust the mutable remote tag instead of SHA.
git -C "$target" fetch --no-tags --depth=1 origin "refs/tags/$version:refs/tags/$version"
tag_commit="$(git -C "$target" rev-parse "refs/tags/$version^{commit}")"
if [ "$tag_commit" != "$expected" ] || [ "$(git -C "$target" rev-parse HEAD)" != "$expected" ]; then
  echo 'Flutter version tag does not identify the locked source commit' >&2
  exit 1
fi
test "$(git -C "$target" describe --tags --exact-match --match "$version" HEAD)" = "$version"
printf 'Flutter source and local version tag verified: %s (%s)\n' "$version" "$actual"
