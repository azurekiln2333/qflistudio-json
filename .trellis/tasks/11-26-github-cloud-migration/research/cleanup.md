# JSON migration cleanup audit

Date: 2026-11-26

Repository: `D:/MyNewProjects/qfli_json`

Active task: `.trellis/tasks/11-26-github-cloud-migration`

## Decision and scope

**All deletions remain PENDING. No path is approved for deletion.**

The user approved migration, not immediate cleanup. The pre-migration `main` must be published before any deletion is reconsidered. This audit does not establish that publication has happened.

The inventory was read-only. At the user's stop request, this report became the only permitted file write. No build, test, dependency installation, deletion, network request, WSL lifecycle operation, or inspection of another project's contents was performed. All future builds and tests belong on GitHub.

The report uses only observations already collected before the stop request. Directory sizes were not calculated. A missing size means **not measured**, not zero. File sizes below are observed logical byte lengths, not allocated disk space or guaranteed recoverable space. No total reclaimable-space estimate is available.

All paths below are relative to the repository unless written as absolute paths.

## Conditionally regenerable candidates

These exact paths were observed. Their location and ignore rules suggest generated state. Regeneration was not tested. Every candidate remains on hold until publication, evidence review, and ownership checks are complete.

| Exact path | Observed size | Assessment |
| --- | ---: | --- |
| `.dart_tool/` | Not measured | Flutter/Dart state. Review package configuration and historical input references before cleanup. |
| `.flutter-plugins-dependencies` | 3,580 bytes | Ignored Flutter dependency metadata. Conditional cleanup candidate. |
| `build/test_cache/` | Not measured | Test cache candidate. Do not execute local tests to regenerate it. |
| `build/unit_test_assets/` | Not measured | Generated test assets candidate. |
| `build/native_assets/` | Not measured | Generated native-assets candidate, not a native source directory. |
| `ios/Flutter/ephemeral/` | Not measured | Generated platform state candidate. |
| `ios/Flutter/Generated.xcconfig` | 545 bytes | Generated local configuration candidate. Preserve adjacent tracked configuration. |
| `ios/Flutter/flutter_export_environment.sh` | 575 bytes | Generated local environment candidate. |
| `linux/flutter/ephemeral/` | Not measured | Generated platform state candidate. |
| `macos/Flutter/ephemeral/` | Not measured | Generated platform state candidate. |
| `windows/flutter/ephemeral/` | Not measured | Generated platform state candidate. |
| `tool/__pycache__/` | Not measured | Python bytecode-cache candidate. Preserve `tool/build_json_content.py`. |
| `.trellis/.runtime/__pycache__/` | Not measured | Bytecode-cache candidate only. Do not generalize this to the rest of `.trellis/.runtime/`. |
| `ohos/.hvigor/` | Not measured | OHOS build state. May be represented in historical prepared-input maps. Evidence review required. |
| `ohos/node_modules/` | Not measured | Installed build dependencies. Keep manifests and lockfiles. Evidence review required. |
| `ohos/oh_modules/` | Not measured | Installed OHOS dependencies. Preserve any retained input/provenance requirement. |

Nested contents and reparse points were not exhaustively inspected. No link target outside this repository was followed for this audit. Directory-level cleanup must not follow links into shared caches, SDKs, or other repositories.

### Root diagnostic logs

These files were observed and match the repository's general `*.log` ignore rule. They are only conditional candidates: first establish that they are not the sole record of a failure or a retained acceptance run.

| Exact path | Observed size |
| --- | ---: |
| `flutter_01.log` | 4,627 bytes |
| `flutter_02.log` | 6,118 bytes |
| `hs_err_pid19132.log` | 15,493 bytes |
| `hs_err_pid69244.log` | 14,791 bytes |
| `hs_err_pid74676.log` | 15,527 bytes |

Their contents and evidence links were not reviewed. They are not cleared for deletion.

## Build/native/OHOS artifacts requiring retention review

**Do not remove `build/` wholesale.** It contains more than disposable compiler output. The following observed directories appear to hold isolated snapshots, readiness checks, release artifacts, or validation-window material. Their role was inferred from names and nearby evidence contracts; their complete contents were not inspected.

- `build/device-evidence-final-check/`
- `build/native-final-readiness-26555365/`
- `build/native-final-source-check-45ae6cbf/`
- `build/native-final-source-check-bc1001e0/`
- `build/native-initialized-preflight-16d92558/`
- `build/native-release-artifacts/`
- `build/native-window-artifacts/`
- `build/native-window-controls-074820a3/`
- `build/native-window-controls-ea6d5be3/`
- `build/native-window-source-check-42bde7f5/`
- `build/native-wrapper-fault-693ce079/`
- `build/native-wrapper-source-check-e2f242c4/`
- `build/native703-diagnostic-hap/`
- `build/o3d73f516/`
- `build/o6e60792d/`
- `build/o97a6ef75/`
- `build/ohos/`
- `build/ohos-json-20261024T042537960102Z/`
- `build/ohos-json-20261024T042828027750Z/`
- `build/published-json-2f9039a3ba95-20261024T031516Z/`
- `build/published-json-2f9039a3ba95-20261024T034925Z/`

All directory sizes above are **not measured**.

Retain these observed build-root provenance and inspection files until their dependencies are reconciled:

| Exact path | Observed size |
| --- | ---: |
| `build/json-initialization-provenance.json` | 1,349 bytes |
| `build/ohos-final-preparation-20261024.json` | 241,833 bytes |
| `build/ohos-initialized-preparation-20261026.json` | 253,516 bytes |
| `build/native-final-offline-inspection.json` | 59,363 bytes |
| `build/native703-offline-reinspection.json` | 59,146 bytes |
| `build/json703-terminal-receipt.txt` | 907 bytes |
| `build/json-retention-controls-prepared-20261026.json` | 1,503 bytes |

The observed `build/channel-*.json`, monitor JSON/JSONL files, readiness records, and retention messages also remain pending evidence review. An ignored path is not proof that its contents are disposable.

No top-level `native/` directory was present in the observed root listing. Patterns for other applications' native directories in `.gitignore` do not prove that those directories exist here. Do not apply them to other repositories.

## Trellis evidence to preserve

Keep the complete task evidence tree:

`.trellis/tasks/10-22-offline-json-ide/`

This includes `task.json`, `prd.md`, `design.md`, `implement.md`, `implement.jsonl`, `check.jsonl`, `evidence.md`, and the complete `research/` tree. The initial tracked-file inventory contained 206 files under `.trellis`; this was not a claim that every local Trellis file is tracked.

Observed research subdirectories requiring preservation:

- `research/device-evidence-20261026/`
- `research/named-20261023T230801Z/`
- `research/named-20261023T233005Z/`
- `research/native-703-20261026/`
- `research/native-preflight-20261026/`
- `research/native-retention-20261026/`
- `research/native-retry-20261026/`
- `research/native-window-20261026/`
- `research/pi-monitor-20261026/`
- `research/release-20261024T034923Z/`

These paths are relative to `.trellis/tasks/10-22-offline-json-ide/`, not the root-level `research/` directory.

Also preserve the adjacent raw logs, source-before/source-after manifests, artifact hashes, harness results, screenshots, UI observations, publication records, and final handoff. In particular, retain:

- `research/.gitattributes`, which protects byte-exact evidence handling.
- `research/ohos.md`, `research/ohos-final-harness-artifact.json`, and `research/ohos-final-source-snapshot.json`.
- `research/ohos-harness-final-result.json` and `research/ohos-harness-final.log`.
- `research/ohos-normal-artifact.json`, `research/ohos-normal-source-snapshot.json`, and `research/ohos-ui-acceptance.json`.
- `research/host-20261023-serial-source-before.json` and `research/host-20261023-serial-source-after.json`.
- `research/host-20261023-concurrent-failure.log`, `research/host-20261023-parallel-oom.log`, and `research/host-20261023-serial-tests.log`.
- `research/host-20261024-published-core.md`, `research/published-core-artifacts-20261024.json`, and `research/final-handoff.md`.

Keep `.trellis/tasks/archive/`, the current migration task, `.trellis/spec/json-offline.md`, `.trellis/workflow.md`, and `.trellis/workspace/codex/`. Do not treat `.trellis/.runtime/` as a disposable cache: it contains untracked review records, scripts, ownership/retention material, and the original host snapshot `.trellis/.runtime/entryability-before-offline.txt` explicitly referenced by `evidence.md`.

The spec requires exact prepared-input identity, before/after maps, package and kernel hashes, fresh device run identity, raw result matching, and terminal/empty-Job ownership evidence. Prior failed intermediates can be part of disclosed provenance. A diagnostic reinspection cannot turn a failed historical window into acceptance. Retain HOLD and cleanup-error records until ownership is reconciled.

Published evidence should include the actual referenced packages and snapshots where required, not only reports naming them. Their availability and complete dependency closure were not established by this limited inventory.

## Source and configuration exclusions

Do not classify the platform trees `android/`, `ios/`, `linux/`, `macos/`, `ohos/`, `web/`, or `windows/` as wholly generated. They contain tracked source and configuration.

The initial Git status showed a pre-existing modification to `ohos/build-profile.json5`. The diff concerned signing material. Preserve that modification and do not reproduce its sensitive values in this report. Status was not rerun after the user updated the migration task.

Preserve dependency manifests and lockfiles, platform source, generated registrants that are tracked, `ohos/hvigor/`, local SDK/signing configuration, `lib/`, `assets/`, `test/`, `scripts/`, `tool/`, README files, LICENSE, and Git history. Do not reset or regenerate them as part of cleanup.

The existing `evidence.md` explicitly distinguishes historical OHOS emulator acceptance, later host compatibility, and still-independent release/device gates. Preserve those boundaries during migration. This audit supplies no new passing build, test, or device claim.

## WSL inventory and ownership

**WSL inventory was not collected.** No distribution names, versions, running states, VHD paths, or sizes were verified. No `wsl` command was executed. This means unknown, not absent or stopped.

The only authorized optional WSL query was `wsl --list --verbose`. It was not run because the user requested an immediate stop and final report.

Do not start a distribution, unregister one, delete a VHD, terminate a distribution, or run `wsl --shutdown`. Shared WSL has no overall coordinator. The app coordinator `w65:p1` owns only its own repository and cannot authorize shared-WSL disposal. Individual repositories must not run `unregister` on their own.

## Release conditions for any later cleanup

This report performs no cleanup and grants no cleanup authority. Reconsider candidates only after:

1. The pre-migration `main` and required source history are confirmed published.
2. Trellis evidence, ignored local-only records, and required referenced artifacts are preserved and verified.
3. Each candidate's exact contents, links, and evidence dependencies are reviewed within this repository.
4. Any retained native-window ownership or HOLD state is reconciled with its custodian.
5. The user authorizes the exact deletion set separately.

Any validation build or test must run on GitHub. Shared WSL remains outside repository-local cleanup authority.
