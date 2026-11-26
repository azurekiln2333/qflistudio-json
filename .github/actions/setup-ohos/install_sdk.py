#!/usr/bin/env python3
"""Install the reviewed SDK on GitHub; never resolve a mutable latest asset."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def fail(message):
    raise SystemExit(f'::error::{message}')


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def append(name, values):
    target = os.environ.get(name)
    if not target:
        fail(f'{name} is required')
    with open(target, 'a', encoding='utf-8', newline='\n') as stream:
        for value in values:
            if '\n' in value or '\r' in value:
                fail(f'Unexpected newline for {name}')
            stream.write(value + '\n')


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        fail('SDK installation is restricted to GitHub Actions')
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--version', required=True)
    parser.add_argument('--api-level', required=True)
    parser.add_argument('--node-version', required=True)
    parser.add_argument('--node-bin', required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    platform = f'{os.environ["RUNNER_OS"]}-{os.environ["RUNNER_ARCH"]}'
    if args.version != manifest['version'] or args.api_level != manifest['apiLevel']:
        fail('Requested SDK is not the committed reviewed identity')
    if args.node_version != '24.14.1':
        fail('Node must be exactly 24.14.1')
    selected = manifest['platforms'].get(platform)
    if selected is None:
        fail(f'Unsupported SDK runner: {platform}')
    node = args.node_bin.resolve(strict=True)
    actual_node = subprocess.check_output([str(node), '--version'], text=True).strip()
    if actual_node != f'v{args.node_version}':
        fail(f'Selected Node reports {actual_node}')
    node_home = node.parent.parent if node.parent.name == 'bin' else node.parent
    expected_node = node_home / ('node.exe' if os.name == 'nt' else 'bin/node')
    if not expected_node.is_file() or expected_node.resolve() != node:
        fail('NODE_HOME does not resolve the exact selected Node interpreter')

    root = Path(os.environ['RUNNER_TEMP']) / f'ohos-sdk-{args.version}-{platform}'
    # Do not trust an SDK cache or silently reuse partial extraction.
    root.mkdir(parents=True, exist_ok=False)
    download = root / 'download'
    download.mkdir()
    repository = manifest['repository']
    release = json.loads(subprocess.check_output(
        ['gh', 'api', f'repos/{repository}/releases/{manifest["releaseId"]}'], text=True
    ))
    if release['id'] != manifest['releaseId'] or release['tag_name'] != args.version:
        fail('SDK release identity changed')
    assets = {item['id']: item for item in release['assets']}
    for part in selected['parts']:
        asset = assets.get(part['id'])
        if not asset or asset['name'] != part['name'] or asset['size'] != part['bytes']:
            fail(f'SDK asset identity changed: {part["name"]}')
        if asset.get('digest') not in (None, 'sha256:' + part['sha256']):
            fail(f'SDK advertised digest changed: {part["name"]}')
        destination = download / part['name']
        print(f'Downloading reviewed asset {repository}/{part["id"]}: {part["name"]}', flush=True)
        with destination.open('wb') as stream:
            subprocess.run(
                ['gh', 'api', f'repos/{repository}/releases/assets/{part["id"]}',
                 '-H', 'Accept: application/octet-stream'],
                stdout=stream, check=True,
            )
        if destination.stat().st_size != part['bytes'] or digest(destination) != part['sha256']:
            fail(f'Committed SHA-256/size mismatch: {part["name"]}')
    archive = download / selected['archive']
    with archive.open('wb') as stream:
        for part in selected['parts']:
            with (download / part['name']).open('rb') as source:
                shutil.copyfileobj(source, stream, 1024 * 1024)
    archive_sha = digest(archive)
    # Extraction follows verification of every byte against committed digests.
    if selected['archive'].endswith('.tar.gz'):
        subprocess.run(['tar', '-xzf', str(archive), '-C', str(root)], check=True)
    else:
        subprocess.run(['unzip', '-q', str(archive), '-d', str(root)], check=True)
    tools = root / 'command-line-tools'
    sdk = tools / 'sdk'
    metadata_path = sdk / 'default/sdk-pkg.json'
    if not metadata_path.is_file():
        fail('SDK default/sdk-pkg.json is absent; Flutter cannot detect this SDK')
    metadata = json.loads(metadata_path.read_text(encoding='utf-8-sig')).get('data', {})
    if metadata.get('apiVersion') != args.api_level:
        fail(f'Installed API metadata is {metadata.get("apiVersion")!r}, expected string {args.api_level!r}')
    sdk_version = metadata.get('version')
    if not isinstance(sdk_version, str) or not sdk_version:
        fail('SDK metadata contains no version')
    ndk = sdk / 'default/openharmony'
    required_dirs = [ndk / 'toolchains', ndk / 'native/llvm/bin']
    for directory in required_dirs:
        if not directory.is_dir():
            fail(f'Incomplete SDK: {directory}')
    tool_bin = tools / 'bin'
    suffix = '.bat' if os.name == 'nt' else ''
    for command in ('ohpm', 'hvigorw'):
        candidate = tool_bin / (command + suffix)
        if not candidate.is_file():
            fail(f'Missing SDK entry point: {candidate}')
        if os.name != 'nt' and not os.access(candidate, os.X_OK):
            fail(f'SDK entry point is not executable: {candidate}')
    shutil.rmtree(download)
    facts = {
        'toolsRepository': repository,
        'toolsReleaseId': manifest['releaseId'],
        'toolsVersion': args.version,
        'releaseImmutable': False,
        'trustAnchor': 'committed per-part SHA-256 and byte count, not downloaded checksum',
        'platform': platform,
        'assets': selected['parts'],
        'combinedArchiveSha256': archive_sha,
        'installedSdkVersion': sdk_version,
        'apiVersion': metadata['apiVersion'],
        'sdkMetadataSha256': digest(metadata_path),
        'nodeVersion': actual_node,
        'nodeSha256': digest(node),
        'nodeHome': str(node_home),
        'sdkHome': str(sdk),
        'sdkSource': 'third-party redistribution; not an official Huawei download channel',
    }
    facts_path = Path(os.environ['RUNNER_TEMP']) / 'ohos-toolchain.json'
    facts_path.write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8')
    append('GITHUB_ENV', [
        f'HOS_SDK_HOME={sdk}', f'DEVECO_SDK_HOME={sdk}',
        f'OHOS_NDK_HOME={ndk}', f'NODE_HOME={node_home}',
        f'OHOS_TOOLS_VERSION={args.version}', f'OHOS_API_LEVEL={args.api_level}',
        f'OHOS_NODE_VERSION={args.node_version}', f'OHOS_TOOLCHAIN_FACTS={facts_path}',
    ])
    # Node is last so the runner prepends it ahead of the SDK's bundled Node.
    # Hvigor also receives NODE_HOME to avoid its internal fallback interpreter.
    append('GITHUB_PATH', [str(tool_bin), str(node.parent)])
    append('GITHUB_OUTPUT', [
        f'sdk-version={sdk_version}', f'api-version={args.api_level}',
        f'sdk-home={sdk}', f'node-home={node_home}', f'facts-path={facts_path}',
    ])
    print(f'Installed reviewed SDK {sdk_version}, API {args.api_level}, Node {actual_node}')
    print(f'Toolchain facts: {facts_path}; retain with cloud logs for three days')


if __name__ == '__main__':
    main()
