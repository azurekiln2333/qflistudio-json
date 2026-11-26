#!/usr/bin/env python3
"""Build a source-bound unsigned JSON HAP, exclusively on a GitHub runner."""
import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import zipfile

PINNED_FLUTTER = 'adaf911c35c9136a7d18fc424d714c9ec7724e60'
PACKAGING_FILTER = {'excludes': ['**/x86_64/*.so']}


def fail(message):
    raise SystemExit(f'::error::{message}')


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def git(directory, *arguments):
    return subprocess.check_output(['git', '-C', str(directory), *arguments], text=True).strip()


def load_profile(path):
    text = path.read_text(encoding='utf-8-sig')
    # Preserve quoted strings while removing JSON5 comments. This profile uses
    # quoted JSON keys/strings; reject other syntax instead of guessing it.
    tokens = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    text = re.sub(tokens, lambda m: m[0] if m[0].startswith('"') else '', text)
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return json.loads(text)


def inspect_hap(path, facts):
    """Read emitted metadata and native members; never modify the HAP."""
    with zipfile.ZipFile(path) as package:
        entries = package.infolist()
        names = [entry.filename for entry in entries]
        facts['hapSha256'] = sha256(path)
        facts['hapMemberInventory'] = [
            {'path': entry.filename, 'bytes': entry.file_size} for entry in entries
        ]
        facts['compiledMetadata'] = {}
        parsed = {}
        for name in ('module.json', 'pack.info'):
            matches = [entry for entry in entries if entry.filename == name]
            evidence = {'present': bool(matches)}
            facts['compiledMetadata'][name] = evidence
            if not matches:
                continue
            if len(matches) != 1 or matches[0].file_size > 1024 * 1024:
                fail(f'Emitted {name} is ambiguous or exceeds the metadata limit')
            raw = package.read(matches[0])
            evidence.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            try:
                evidence['text'] = raw.decode('utf-8-sig')
                parsed[name] = json.loads(evidence['text'])
            except (UnicodeError, ValueError) as error:
                evidence['parseError'] = str(error)
                fail(f'Emitted {name} is not UTF-8 JSON')

        native = []
        for entry in entries:
            if entry.is_dir() or not entry.filename.endswith('.so'):
                continue
            result = hashlib.sha256()
            with package.open(entry) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    result.update(chunk)
            match = re.fullmatch(r'libs/([^/]+)/[^/]+\.so', entry.filename)
            native.append({'path': entry.filename, 'bytes': entry.file_size,
                           'sha256': result.hexdigest(),
                           'abi': match.group(1) if match else None})
        facts['hapNativeMembers'] = native
        facts['hapNativeAbiSource'] = 'emitted libs/<abi>/<name>.so paths; ELF fingerprints use the separate native gate'
        facts['hapNativeAbis'] = sorted({item['abi'] for item in native if item['abi']})
        if len(names) != len(set(names)):
            fail('Unsigned HAP contains duplicate member names')
        if 'module.json' not in parsed or not isinstance(parsed['module.json'], dict):
            fail('Unsigned HAP must contain an emitted module.json object')
        compiled_app = parsed['module.json'].get('app')
        compiled_module = parsed['module.json'].get('module')
        if not isinstance(compiled_app, dict) or not isinstance(compiled_module, dict):
            fail('Emitted module.json must contain app and module objects')
        facts['compiledAppMetadata'] = {
            key: compiled_app.get(key) for key in
            ('bundleName', 'versionCode', 'versionName', 'targetAPIVersion',
             'minAPIVersion', 'compileSdkVersion', 'compileSdkType')
        }
        facts['compiledModuleName'] = compiled_module.get('name')
        if compiled_app.get('bundleName') != 'com.azurekiln.qfli.json' or compiled_module.get('name') != 'entry':
            fail('Emitted module.json does not identify the JSON entry application')
        target_api = compiled_app.get('targetAPIVersion')
        if type(target_api) is not int or not 0 <= target_api <= 2147483647:
            fail('Emitted module.json app.targetAPIVersion must be a valid integer')
        facts['compiledTargetApiValidation'] = (
            'recorded-only; API 26.0.0 numeric encoding is not inferred from the input profile'
        )
        if any(item['abi'] is None for item in native) or facts['hapNativeAbis'] != ['arm64-v8a']:
            fail('Unsigned HAP must package exactly the arm64-v8a native ABI')
        required = {f'libs/arm64-v8a/{name}' for name in
                    ('libapp.so', 'libflutter.so', 'libqfli_git.so')}
        if not required.issubset({item['path'] for item in native}):
            fail('Unsigned HAP lacks the arm64 app, Flutter engine or qfli_git library')
        facts['hapNativeAbiVerified'] = True


def append(name, lines):
    with open(os.environ[name], 'a', encoding='utf-8', newline='\n') as stream:
        for line in lines:
            if '\n' in line or '\r' in line:
                fail(f'Unexpected newline in {name}')
            stream.write(line + '\n')


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        fail('OHOS builds are restricted to GitHub Actions')
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--api-level', default='26')
    parser.add_argument('--flutter-commit', default=PINNED_FLUTTER)
    args = parser.parse_args()
    app = args.app_dir.resolve(strict=True)
    output = args.output_dir.resolve()
    if args.api_level != '26' or args.flutter_commit != PINNED_FLUTTER:
        fail('Only the reviewed API 26 / Flutter OHOS commit is supported')
    if os.environ.get('RUNNER_OS') != 'Linux':
        fail('The OHOS release build is supported on a Linux GitHub runner')
    runner_temp = Path(os.environ['RUNNER_TEMP']).resolve(strict=True)
    if output == app or app in output.parents or runner_temp not in output.parents:
        fail('Stage the OHOS package outside the source tree, under RUNNER_TEMP')
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        fail('Output directory is not empty; refusing to mix build windows')

    profile_path = app / 'ohos/build-profile.json5'
    profile = load_profile(profile_path)['app']
    if profile.get('signingConfigs', []) or any('signingConfig' in p for p in profile['products']):
        fail('The cloud OHOS profile must contain no signing material or signingConfig selection')
    product = [p for p in profile['products'] if p['name'] == 'default']
    if len(product) != 1 or product[0].get('targetSdkVersion') != '26.0.0':
        fail('The default OHOS product must target numeric SDK version 26.0.0 (API 26)')
    module_profile_path = app / 'ohos/entry/build-profile.json5'
    module_profile = load_profile(module_profile_path)
    native_filter = module_profile.get('buildOption', {}).get('nativeLib', {}).get('filter')
    if native_filter != PACKAGING_FILTER:
        fail('The entry module must use only the reviewed x86_64 nativeLib packaging exclusion')
    profile_hashes = {str(path.relative_to(app)): sha256(path)
                      for path in (profile_path, module_profile_path)}
    native_archive = app / 'build/ci-native/ohos/native-inputs.tar.gz'
    prepared = json.loads((native_archive.parent / 'prepare.json').read_text(encoding='utf-8'))
    archive_before = sha256(native_archive)
    if (prepared.get('status') != 'prepared' or prepared.get('target') != 'ohos' or
            prepared.get('archive', {}).get('sha256') != archive_before):
        fail('Full native input archive must match the prepared OHOS evidence before building')
    sdk = Path(os.environ['HOS_SDK_HOME']).resolve(strict=True)
    metadata_path = sdk / 'default/sdk-pkg.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8-sig'))['data']
    if metadata.get('apiVersion') != '26':
        fail('Installed SDK metadata does not report API string 26')
    node = Path(os.environ['NODE_HOME']) / 'bin/node'
    if subprocess.check_output([str(node), '--version'], text=True).strip() != 'v24.14.1':
        fail('Hvigor NODE_HOME does not select Node 24.14.1')
    flutter_command = shutil.which('flutter')
    if not flutter_command:
        fail('Flutter is not on PATH')
    flutter = Path(flutter_command).resolve(strict=True)
    flutter_root = flutter.parent.parent
    actual_flutter = git(flutter_root, 'rev-parse', 'HEAD')
    if actual_flutter != PINNED_FLUTTER:
        fail(f'Flutter is {actual_flutter}, expected {PINNED_FLUTTER}')
    core = app.parent / 'qflistudio-core'
    core_commit = git(core, 'rev-parse', 'HEAD')
    if core_commit != '476a30acee21dc486ee2849dd8064a7be665e4d5':
        fail(f'Unreviewed shared-core revision: {core_commit}')
    huawei = (core / 'lib/pages/auth/huawei_quick_login_view.dart').read_bytes().replace(b'\r\n', b'\n')
    huawei_blob = hashlib.sha1(b'blob ' + str(len(huawei)).encode() + b'\0' + huawei).hexdigest()
    if huawei_blob != '0ed4033647630449f73bd9b51faee35bbd8cde64':
        fail('OHOS must retain the real pinned native view, not the official-Flutter stub')
    lock = app / 'pubspec.lock'
    lock_before = sha256(lock)
    roots = [app / 'build/ohos', app / 'ohos/entry/build', app / 'ohos/build']
    if any(root.is_dir() and any(root.rglob('*.hap')) for root in roots):
        fail('Pre-existing HAP found; this job requires a fresh package window')
    command = [str(flutter), 'build', 'hap', '--release', '--target-platform',
               'ohos-arm64', '--no-pub', '--no-codesign']
    log = output / 'flutter-build.log'
    facts = {
        'appCommit': git(app, 'rev-parse', 'HEAD'),
        'coreCommit': core_commit,
        'huaweiViewGitBlob': huawei_blob,
        'flutterCommit': actual_flutter,
        'flutterVersion': '3.41.10-ohos-1.0.1',
        'sdkApiVersion': metadata['apiVersion'],
        'sdkVersion': metadata['version'],
        'nodeVersion': '24.14.1',
        'targetSdkVersion': '26.0.0',
        'pubspecLockSha256': lock_before,
        'profileSha256': profile_hashes['ohos/build-profile.json5'],
        'profileSha256Before': profile_hashes,
        'nativePackagingFilter': native_filter,
        'expectedNativeAbis': ['arm64-v8a'],
        'nativeInputArchiveSha256Before': archive_before,
        'compiledTargetApiVerified': False,
        'compiledTargetApiValidation': 'not-inspected',
        'hapNativeAbiVerified': False,
        'command': command,
        'signing': 'unsigned; signing is required before distribution/installation',
        'deviceValidation': 'none',
        'run': f'{os.environ["GITHUB_SERVER_URL"]}/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}',
        'runAttempt': os.environ['GITHUB_RUN_ATTEMPT'],
        'packageBuilt': False,
    }
    facts_path = output / 'build-facts.json'
    try:
        print('Running on the GitHub runner: ' + ' '.join(command), flush=True)
        with log.open('wb') as stream:
            process = subprocess.Popen(command, cwd=app, stdout=stream, stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL, start_new_session=True)
            try:
                code = process.wait(timeout=2700)
            except subprocess.TimeoutExpired:
                facts['timedOut'] = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                fail('OHOS build exceeded its 45-minute process deadline')
        facts['buildExitCode'] = code
        with log.open(encoding='utf-8', errors='replace') as stream:
            print(''.join(deque(stream, maxlen=120)))
        facts['profileSha256After'] = {
            str(path.relative_to(app)): sha256(path)
            for path in (profile_path, module_profile_path)
        }
        facts['nativeInputArchiveSha256After'] = sha256(native_archive)
        if facts['profileSha256After'] != profile_hashes:
            fail('Build changed the reviewed OHOS product or entry-module profile')
        if facts['nativeInputArchiveSha256After'] != archive_before:
            fail('Build changed the full immutable native input archive')
        if code != 0:
            fail(f'Flutter HAP build exited {code}; see {log}')
        if sha256(lock) != lock_before:
            fail('Build changed the enforced pubspec.lock')
        candidates = sorted({p.resolve() for root in roots if root.is_dir()
                             for p in root.rglob('*-unsigned.hap') if p.is_file()})
        if not candidates:
            fail('Flutter produced no unsigned HAP')
        identities = {sha256(path) for path in candidates}
        if len(identities) != 1:
            fail('Several different unsigned HAPs were produced; refusing an ambiguous package')
        if any(root.is_dir() and any(root.rglob('*-signed.hap')) for root in roots):
            fail('Unexpected signed HAP in an unsigned build window')
        source = candidates[0]
        inspect_hap(source, facts)
        print('Emitted HAP native ABIs: ' + ', '.join(facts['hapNativeAbis']), flush=True)
        print('Emitted module.json app.targetAPIVersion: ' +
              str(facts['compiledAppMetadata']['targetAPIVersion']), flush=True)
        destination = output / 'qflistudio-json-ohos-arm64-unsigned.hap'
        shutil.copyfile(source, destination)
        hap_hash = sha256(destination)
        facts.update(packageBuilt=True, hapPath=str(destination), hapSha256=hap_hash,
                     packageVerification='Exact native ABI and metadata identity only; compiled target API encoding is unverified; native-contract fingerprint verification remains a separate required gate')
        (output / 'SHA256SUMS').write_text(f'{hap_hash}  {destination.name}\n', encoding='utf-8')
        append('GITHUB_ENV', [f'HAP_PATH={destination}', f'OHOS_PACKAGE_DIR={output}'])
        append('GITHUB_OUTPUT', [f'hap-path={destination}', f'package-dir={output}'])
        print(f'Unsigned HAP ready for the separate native-contract gate: {destination}')
    except (Exception, SystemExit) as error:
        facts['error'] = str(error)
        raise
    finally:
        facts_path.write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
