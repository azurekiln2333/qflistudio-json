#!/usr/bin/env bash
# Official Flutter only. Run on the disposable GitHub runner copy, never OHOS.
set -euo pipefail
if [[ "${GITHUB_ACTIONS:-}" != true ]]; then
  echo '::error::This compatibility patch may run only in GitHub Actions.' >&2
  exit 1
fi
if [[ $# != 2 ]]; then
  echo 'usage: bash tool/ci/patch_upstream_core.sh APP_DIR CORE_DIR' >&2
  exit 2
fi
python_bin=${PYTHON:-python3}
if ! command -v "$python_bin" >/dev/null 2>&1; then python_bin=python; fi
"$python_bin" - "$1" "$2" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

app, core = (Path(arg).resolve() for arg in sys.argv[1:])
expected_commit = '8e031313ffc8d531c5a6b4d131f721f35da04c86'
expected_blob = '0ed4033647630449f73bd9b51faee35bbd8cde64'
relative = 'lib/pages/auth/huawei_quick_login_view.dart'
actual_commit = subprocess.check_output(
    ['git', '-C', str(core), 'rev-parse', 'HEAD'], text=True
).strip()
if actual_commit != expected_commit:
    raise SystemExit(f'::error::Core revision {actual_commit} is not reviewed {expected_commit}')

# A path dependency's dependency_overrides are not inherited by the app.
# The caller owns its root overrides and lockfile. This patch changes neither.
manifests = [app / 'pubspec.yaml', core / 'pubspec.yaml']
manifest_before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in manifests}
path = core / relative
before = path.read_bytes()
canonical = before.replace(b'\r\n', b'\n')
blob = hashlib.sha1(b'blob ' + str(len(canonical)).encode() + b'\0' + canonical).hexdigest()
replacement = b"""import 'package:flutter/material.dart';

// Official-Flutter CI substitute. The offline JSON profile never registers
// Huawei login. The OHOS build keeps the pinned native view unchanged.
class HuaweiQuickLoginView extends StatelessWidget {
  const HuaweiQuickLoginView({
    super.key,
    required this.agreementAccepted,
    required this.onAuthorizationCode,
    required this.onError,
  });

  final bool agreementAccepted;
  final ValueChanged<String> onAuthorizationCode;
  final ValueChanged<String> onError;

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
"""
if canonical != replacement:
    if blob != expected_blob:
        raise SystemExit(f'::error::Unreviewed source blob for {relative}: {blob}')

roots = [app / 'lib', core / 'lib', core / 'vendor/re_editor/lib']
for root in roots:
    if not root.is_dir():
        raise SystemExit(f'::error::Missing source root: {root}')
offenders = []
for root in roots:
    for source in sorted(root.rglob('*.dart')):
        # Inspect the proposed source before writing any file.
        text = replacement.decode() if source == path else source.read_text(encoding='utf-8-sig')
        for number, line in enumerate(text.splitlines(), 1):
            for token in ('TargetPlatform.ohos', 'OhosView'):
                if token in line:
                    offenders.append(f'{source}:{number}: {token}')
if offenders:
    raise SystemExit('::error::Unreviewed fork-only Dart API remains:\n' + '\n'.join(offenders))
if canonical != replacement:
    path.write_bytes(replacement)
manifest_after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in manifests}
if manifest_after != manifest_before:
    raise SystemExit('::error::Dependency manifests unexpectedly changed')
report = {
    'coreCommit': actual_commit,
    'reviewedSourceGitBlob': expected_blob,
    'changedFile': relative,
    'patchedSha256': hashlib.sha256(replacement).hexdigest(),
    'dependencyManifestsChanged': False,
    'mode': 'official-flutter-only',
    'validation': 'static compatibility preparation; not a build or test result',
}
output = Path(os.environ['RUNNER_TEMP']) / 'qfli-upstream-core-patch.json'
output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
print(f'Compatibility facts: {output}')
PY
