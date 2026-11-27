# JSON cloud execution

Local agents may edit source and inspect Git, text, hashes and filesystem metadata.
All builds, tests, analysis, lint, package resolution and SDK installation run on GitHub.
Do not run CI helpers locally or fake GITHUB_ACTIONS to bypass their guards.

## Fixed migration inputs

| Input | Reviewed value |
| --- | --- |
| App repository | azurekiln2333/qflistudio-json |
| Sibling core | 1ae4674a4b153701b0c3b3ff04b1a1b77a318611 |
| Git plugin | 697291a27818612ae9dc53d83d4f99fa5887908e |
| Historical native producer | 194a6c9dd70873a472e441b67875766541572372, run 44863517943 |
| Official Flutter | 3.50.0 at ab2912035e160d9cad6306df307576da6128ebdb |
| OHOS Flutter | 3.41.10-ohos-1.0.1 at adaf911c35c9136a7d18fc424d714c9ec7724e60 |
| OHOS tools / API / Node | 26.0.0.821 / 26 / 24.14.1 |
| Android NDK / CMake | 27.0.12077973 / 3.22.1 |

These are fixed inputs, not claims about the newest available versions.
The coordinator approved this core revision for the 2026-11-28 pin wave.
Change that pin only after a new coordinator decision and contract review.
The workflows check out qflistudio and qflistudio-core as siblings.
The package/import name remains qfli_studio_core.
The app owns re_editor and xterm overrides under ../qflistudio-core/vendor/.
Core's explicit prepare_flutter_core.py invocation checks the pinned SDK and
changes only the disposable CI Huawei login widget for official Flutter.
It does not change dependency manifests. OHOS retains the original widget.

## Dependency lock

Resolve pinned JSON dependency lock runs manually on GitHub.
Review and commit its output before installer validation.
Initial successful resolution: run 45825769686 on app df93c17c38782644021b32eda62608c4f69110f8.
The tracked lock provenance and dependency graph are in migration research.
Installer jobs enforce the committed lock and reject silent drift.
Mode-specific locks must come from corresponding cloud resolution runs.

## Deliverables and limitations

The app-installers workflow owns verification and six platform jobs.
The all-platform gate must examine every result. A declared job is not successful build evidence.
Release assets must come from the same app commit and run attempt.

| Platform | Intended package | Signing/device limit |
| --- | --- | --- |
| Windows x64 | Portable ZIP and setup EXE | No Authenticode signature claimed |
| Linux x64 | Runtime tar and Debian package | Declared runtime system dependencies |
| macOS universal | App tar and DMG | No Developer ID signature or notarization |
| iOS arm64 | Unsigned IPA | Needs signing/provisioning for stock devices |
| Android | ABI-specific APKs and universal AAB | Debug certificate, not store signing |
| OHOS arm64 | Unsigned HAP | Needs appropriate signing for ordinary devices |

There are no production signing jobs yet. Missing signing secrets do not currently fail a job.
Add protected signing workflows before claiming store-ready releases.
No migration run alone proves device installation, mobile FFI execution or historical product acceptance.

## Native and intermediate outputs

The transition contract consumes the exact Git plugin tree selected by core.
It verifies the native lock blob, source identity, file sizes/digests, ABIs and required exports.
The old plugin tree contains native payloads. JSON does not commit those binaries.
This is a pinned historical Git source, not an upstream immutable release claim.
GitHub creates native archives recording app/core/plugin/native identities.
Package inspection verifies native membership and architectures.
Opaque installers are paired with inspected runtime archives and hashes.
Desktop Git uses an external Git CLI. Desktop builds do not prove mobile FFI execution.

Diagnostics and Flutter/native intermediates use short-lived GitHub artifacts.
Durable native and package assets require separate publication with SHA-256 manifests.
Immutable releases are enabled and must be checked after publication.
Never overwrite published assets. Use a new commit/run-specific identity.
Never upload entire Pub caches, signing directories, SDKs or unreviewed historical build snapshots.

## Evidence

Current progress and handoff: .trellis/tasks/11-26-github-cloud-migration/.
Use research/history-map.json to resolve original commits after signing-config removal.
Use research/local-preserved/INDEX.md and manifest.json for recovered runtime records.
Historical reports retain original results and machine paths as provenance.
Quarantined UI/session material and credential-bearing backups stay local.
Read the final cloud report before calling any platform accepted.
