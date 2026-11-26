#!/usr/bin/env bash
set -euo pipefail
if [[ "${GITHUB_ACTIONS:-}" != true ]]; then
  echo '::error::SDK installation is restricted to GitHub Actions.' >&2
  exit 1
fi
version='26.0.0.821'
api='26'
node_version='24.14.1'
while getopts ':v:a:n:' option; do
  case "$option" in
    v) version=$OPTARG ;;
    a) api=$OPTARG ;;
    n) node_version=$OPTARG ;;
    *) echo 'usage: setup.sh -v 26.0.0.821 -a 26 -n 24.14.1' >&2; exit 2 ;;
  esac
done
if [[ "$version" != '26.0.0.821' || "$api" != '26' || "$node_version" != '24.14.1' ]]; then
  echo '::error::Only the reviewed SDK 26.0.0.821 / API 26 / Node 24.14.1 tuple is permitted.' >&2
  exit 1
fi
python_bin=${PYTHON:-python3}
if ! command -v "$python_bin" >/dev/null 2>&1; then python_bin=python; fi
action_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
node_actual=$(node --version)
if [[ "$node_actual" != "v$node_version" ]]; then
  echo "::error::setup-node selected $node_actual, expected v$node_version" >&2
  exit 1
fi
node_bin=$(node -p 'process.execPath')
"$python_bin" "$action_dir/install_sdk.py" \
  --manifest "$action_dir/sdk-assets.json" \
  --version "$version" --api-level "$api" \
  --node-version "$node_version" --node-bin "$node_bin"
