# Current JSON cleanup inventory

Task: `.trellis/tasks/11-26-github-cloud-migration`

Repository: `D:/MyNewProjects/qfli_json`

Inventory date: 2026-11-26, beginning at 23:24:34 +08:00.

## Decision and acceptance boundary

**HOLD: this is an inventory, not approval to delete. Nothing was deleted.**

The user reports that preservation is accepted and published. The local checkout and locally resolvable publication commit both identify:

`9113f2ec0380a999b05fe27fd10de33e549fb061`

CI is ongoing and final migration acceptance is **not complete**, as stated by the user. No remote or CI query was performed. Local publication-tree inspection is not independent verification of the remote or its current workflows.

The initial tracked worktree check was clean. A later read-back still showed HEAD at the same commit but detected concurrent changes to `.github/workflows/app-installers.yml`, the migration task's `implement.md` and `task.json`, `.trellis/workspace/codex/index.md`, `.trellis/workspace/codex/journal-1.md`, and `AGENTS.md`. Those files were not written or inspected for content by this inventory. Do not infer a clean final worktree or acceptance of those later edits. Counts and sizes below remain the pre-report metadata snapshot, not a refreshed measurement of concurrent changes.

Only this report was written. The original `research/cleanup.md` must remain unchanged. Its pre-write identity is 11,768 bytes, SHA256:

`3a15b916b64eb2974e84931bca5eeb6027292eec1e7c9d5bccc6908683515ce9`

The report's ready SHA256 is supplied separately after writing and read-back; it is not embedded into the file it identifies.

## Method and limitations

- Enumerated regular-file names, lengths, directory boundaries, and reparse attributes inside this checkout only.
- Skipped every `.git` directory and all 29 encountered reparse points. Did not inspect link targets, follow junctions, or traverse external project/cache/SDK roots.
- Used read-only Git tracked-path metadata and `check-ignore --stdin` on the already enumerated regular files. Reparse paths were not submitted for traversal. Git optional locks and filesystem monitor were disabled for these reads. Long-path handling was enabled per command, not written to Git configuration.
- Read no source, log, package, private-backup, or credential contents in this inventory. Prior accepted preservation classifications are explicitly distinguished from current metadata observations.
- Ran no build, test, analyzer, linter, dependency resolution/installation, SDK action, device operation, or WSL command. No network request, Git mutation, deletion, or backup upload occurred.
- All sizes are sums of logical regular-file lengths. They exclude directory allocation, link targets, and Git storage. They are not allocated disk usage or guaranteed recoverable space. Nested rows are not additive unless explicitly described as disjoint.
- Enumeration reported no directory errors. Totals describe the observed checkout before creation of this report, not an atomic filesystem snapshot. A later cleanup must re-inventory its exact scope.

## Repository overview

| Boundary | Regular files | Logical bytes | Disposition |
| --- | ---: | ---: | --- |
| Enumerated checkout, excluding `.git` and reparse targets | 7,110 | 1,735,641,800 | Inventory boundary, never a deletion set |
| Tracked regular files present | 518 | 9,104,882 | Preserve |
| Ignored regular files present | 6,592 | 1,726,536,918 | Mixed generated state, historical evidence, and local/private material |
| Untracked, not ignored, before this report | 0 | 0 | This report becomes a new untracked deliverable |
| `build/` | 5,700 | 1,119,611,265 | Mixed; do not remove wholesale |
| `ohos/` | 755 | 427,277,706 | Mixed source/configuration and output; do not remove wholesale |
| `.dart_tool/` | 50 | 175,781,110 | Conditional generated-state candidate |
| `.trellis/` | 402 | 10,235,160 | Durable evidence plus local runtime/quarantine; preserve selectively as below |

## A. Lower-risk generated candidates, still conditional

Every regular file in this table is currently ignored and none is tracked. These are exact candidate boundaries, not commands or deletion approval. A path may contain historical input identities even when its payload is regenerable. All prerequisites below still apply.

| Exact repository-relative path | Regular files | Logical bytes | Notes |
| --- | ---: | ---: | --- |
| `.dart_tool/` | 50 | 175,781,110 | Dart/Flutter state, including historical compiler/configuration state; preserve required input identities first |
| `.flutter-plugins-dependencies` | 1 | 3,580 | Generated plugin mapping; retain any required historical attribution first |
| `build/test_cache/` | 1 | 62,341,520 | Generated test cache |
| `build/unit_test_assets/` | 26 | 12,631,493 | Generated test assets; source assets remain tracked elsewhere |
| `build/native_assets/` | 1 | 45 | Generated native-assets state, not native source |
| `android/app/src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java` | 1 | 1,078 | Ignored generated registrant only |
| `ios/Flutter/ephemeral/` | 2 | 1,384 | Generated platform state |
| `ios/Flutter/Generated.xcconfig` | 1 | 545 | Generated local configuration |
| `ios/Flutter/flutter_export_environment.sh` | 1 | 575 | Generated environment file; no contents inspected |
| `ios/Runner/GeneratedPluginRegistrant.h` | 1 | 378 | Ignored generated registrant |
| `ios/Runner/GeneratedPluginRegistrant.m` | 1 | 742 | Ignored generated registrant |
| `macos/Flutter/ephemeral/` | 2 | 975 | Generated platform state |
| `ohos/entry/src/main/ets/plugins/GeneratedPluginRegistrant.ets` | 1 | 693 | Ignored generated registrant only |
| `tool/__pycache__/` | 1 | 88,231 | Generated bytecode, not Python source |
| `tool/ci/__pycache__/` | 1 | 5,158 | Generated bytecode, not CI source |
| `.trellis/.runtime/__pycache__/` | 1 | 43,154 | Bytecode only; does not authorize removal of runtime evidence |
| `.trellis/tasks/10-22-offline-json-ide/research/device-evidence-20261026/__pycache__/` | 1 | 41,589 | Bytecode only; preserve surrounding research |
| `.trellis/tasks/10-22-offline-json-ide/research/native-retry-20261026/runners/__pycache__/` | 2 | 79,976 | Bytecode only; preserve runner source and evidence |
| **Disjoint regular-file subtotal** | **95** | **251,022,226** | Candidate inventory only; not approved reclaimable space |

The six bytecode files above account for 258,108 bytes within that subtotal.

`linux/flutter/ephemeral/` and `windows/flutter/ephemeral/` each contain zero enumerated regular-file bytes, but each has two skipped plugin reparse points. They are **not empty** and their target sizes are unknown. Do not treat their linked dependencies as local disposable bytes.

## B. Evidence-bound OHOS output and dependencies

The following disjoint regular-file sets are all ignored. Keep them on hold until historical evidence closure, package preservation, and ownership checks are satisfied. Their generated nature alone does not settle whether they are the last copy of required evidence.

| Exact path | Regular files | Logical bytes | Boundary |
| --- | ---: | ---: | --- |
| `ohos/.hvigor/` | 20 | 3,874,501 | Historical native build state |
| `ohos/node_modules/` | 1 | 496 | Local regular file only; one plugin reparse point skipped |
| `ohos/oh_modules/` | 203 | 41,644,133 | Local dependency payload; two reparse points skipped |
| `ohos/entry/build/` | 461 | 300,139,556 | Includes package/intermediate/cache evidence; not ordinary source |
| `ohos/entry/src/main/resources/rawfile/flutter_assets/` | 28 | 81,533,630 | Generated copied Flutter assets under a source-looking path |
| **Disjoint subtotal** | **713** | **427,192,316** | Held, not approved for deletion |

`ohos/entry/oh_modules/` contains three skipped plugin reparse points and contributes no enumerated regular-file bytes. The links may point to shared or otherwise independently retained material. No target was inspected.

Preserve tracked OHOS source, manifests, build profiles, `AppScope/`, `hvigor/`, and native host code. Do not delete `ohos/entry/src/` as a whole merely because one nested asset directory is generated.

### Ignored OHOS manifests are not cache approval

These four ignored files need an explicit migration/provenance disposition, not automatic cleanup:

| Exact path | Files | Bytes | Ignore source |
| --- | ---: | ---: | --- |
| `ohos/package.json` | 1 | 127 | `ohos/.gitignore`, `/package.json` |
| `ohos/package-lock.json` | 1 | 649 | `ohos/.gitignore`, `/package-lock.json` |
| `ohos/oh-package-lock.json5` | 1 | 678 | `ohos/.gitignore`, `**/oh-package-lock.json5` |
| `ohos/entry/oh-package-lock.json5` | 1 | 2,114 | Same nested lockfile rule |
| **Subtotal** | **4** | **3,568** | Preserve until reconciled |

No content safety or portability finding was made for these files in this metadata-only pass. A published replacement does not silently change their historical role.

## C. Old build evidence: separate retention hold

Only the three `build/` rows listed in section A are in the lower-risk subtotal. The remainder is **5,672 files / 1,044,638,207 bytes** on evidence hold.

The following directory rows are disjoint children of `build/`. No package, archive, embedded source, or signing configuration was opened.

| Exact path | Regular files | Logical bytes |
| --- | ---: | ---: |
| `build/o6e60792d/` | 1,362 | 469,866,778 |
| `build/published-json-2f9039a3ba95-20261024T034925Z/` | 584 | 125,546,041 |
| `build/native703-diagnostic-hap/` | 1 | 124,516,943 |
| `build/ohos/` | 30 | 81,683,945 |
| `build/o97a6ef75/` | 808 | 66,864,433 |
| `build/o3d73f516/` | 808 | 66,864,420 |
| `build/published-json-2f9039a3ba95-20261024T031516Z/` | 555 | 50,778,065 |
| `build/ohos-json-20261024T042828027750Z/` | 634 | 25,434,491 |
| `build/ohos-json-20261024T042537960102Z/` | 634 | 25,434,491 |
| `build/native-final-readiness-26555365/` | 15 | 2,159,330 |
| `build/native-release-artifacts/` | 26 | 853,950 |
| `build/native-window-source-check-42bde7f5/` | 6 | 750,168 |
| `build/native-initialized-preflight-16d92558/` | 6 | 746,071 |
| `build/native-final-source-check-bc1001e0/` | 6 | 740,988 |
| `build/native-final-source-check-45ae6cbf/` | 6 | 737,490 |
| `build/native-wrapper-source-check-e2f242c4/` | 3 | 734,251 |
| `build/native-window-controls-074820a3/` | 35 | 59,784 |
| `build/native-window-controls-ea6d5be3/` | 35 | 59,782 |
| `build/native-window-artifacts/` | 71 | 38,260 |
| `build/device-evidence-final-check/` | 1 | 9,364 |
| `build/native-wrapper-fault-693ce079/` | 4 | 933 |
| Direct regular files immediately under `build/` | 42 | 758,229 |

The direct-file subtotal includes preparation/source maps, inspections, monitor records, ownership/retention messages, and terminal receipts observed in the earlier audit. Exact examples remain:

- `build/ohos-final-preparation-20261024.json`
- `build/ohos-initialized-preparation-20261026.json`
- `build/json-initialization-provenance.json`
- `build/native-final-offline-inspection.json`
- `build/native703-offline-reinspection.json`
- `build/json703-terminal-receipt.txt`

Embedded `qfli_studio_core` directories in this table are snapshots physically under this JSON checkout, not independently inspected sibling checkouts. No external repository was traversed. Twenty-nine total reparse points, including nested snapshot links, were excluded from every size.

### Individually observed large artifact metadata

These rows overlap parent-directory totals and must not be added to them:

| Exact path | Logical bytes | Retention rule |
| --- | ---: | --- |
| `build/native703-diagnostic-hap/harness-unsigned.hap` | 124,516,943 | Preserve reviewed historical package and its identity before cleanup |
| `ohos/entry/build/default/outputs/default/entry-default-unsigned.hap` | 123,864,987 | Mutable build output; requires exact historical-role/hash reconciliation |
| `build/published-json-2f9039a3ba95-20261024T034925Z/qfli_studio_core.tar` | 23,582,720 | Historical core archive, not a verified public-safe Release asset |
| `build/published-json-2f9039a3ba95-20261024T031516Z/qfli_studio_core.tar` | 23,582,720 | Same size does not establish identical bytes |

These four observed files total 295,547,370 bytes, but are neither a complete artifact closure nor an approved cleanup set. No new package hash or archive safety claim was produced by this metadata-only report.

Large required native/HAP artifacts must be preserved as individually reviewed GitHub Release assets with a durable index before cleanup. **Do not publish an entire old `build/` or runtime bundle.** Prior accepted reviews identified signing-configuration risk in isolated snapshots. Preserve unsafe originals privately when required; a sanitized derivative cannot silently replace the raw identity claimed by a historical hash. Release assets, their actual availability, and complete dependency closure were not verified in this pass.

## D. Private/local quarantine and backup boundary

These are not public Release assets, source-cleanup candidates, or disposable caches:

| Exact path | Files | Bytes | Retention disposition |
| --- | ---: | ---: | --- |
| `.trellis/.runtime/full-005.json` | 1 | 40,711 | Actual UI dump; privacy safety unconfirmed |
| `.trellis/.runtime/state-005.png` | 1 | 2,132,608 | UI screenshot, local quarantine |
| `.trellis/.runtime/ui-current.png` | 1 | 279,612 | UI screenshot, local quarantine |
| `.trellis/.runtime/sessions/codex-json-offline-20261022.json` | 1 | 156 | Dynamic session control state; excluded from publication |
| `.trellis/.runtime/named-staged-paths.json` | 1 | 2,886 | Transient staging-path list; preserve locally until separately authorized |
| `.trellis/.runtime/release-staged-paths.json` | 1 | 2,899 | Transient staging-path list; preserve locally until separately authorized |
| **Known runtime quarantine subtotal** | **6** | **2,458,872** | No deletion or publication approval |
| `.trellis/.developer` | 1 | 55 | Local developer identity; not read |
| `android/local.properties` | 1 | 80 | Machine-local configuration; not read |
| `ohos/local.properties` | 1 | 145 | Machine-local configuration; not read |

The complete `.trellis/.runtime/` remains 101 ignored files / 3,666,919 bytes. The prior accepted preservation map accounts for 94 original paths / 1,164,893 bytes through preserved or already tracked counterparts, six quarantine paths above, and one 43,154-byte bytecode file. This mapping is carried forward from the accepted preservation work; it is not a fresh content/hash proof in this metadata-only inventory. Do not delete runtime wholesale, including ownership/HOLD records, based solely on matching totals.

No separate private-backup/quarantine-named directory, standalone signing-key/certificate file, or `.bak`/`.orig` file was encountered among regular files in the enumerated non-Git checkout. This does **not** establish that private backups do not exist. `.git` storage, external backup locations, other checkouts, shared caches, and reparse targets were deliberately excluded. Their sizes, safety, retention state, and recoverability remain unknown and out of scope. Ordinary source filenames containing `backup` are not private backup archives.

Any previously created private backup, signing backup, unsanitized source archive, or credential-bearing Git backup remains private quarantine until its owner separately verifies secure retention. Do not upload it publicly, infer its size from an unrelated source snapshot, or include it in a repository-local deletion set. This report grants no authority over such backups.

## E. Durable published material to keep

Current regular-file tracking was checked locally:

| Exact boundary | Files | Bytes | Git state |
| --- | ---: | ---: | --- |
| `.trellis/tasks/11-26-github-cloud-migration/research/local-preserved/` | 76 | 1,019,518 | All tracked; all 76 paths present in local `9113f2e` tree |
| `.trellis/tasks/11-26-github-cloud-migration/` before this report | 87 | 1,090,340 | All tracked |
| `.trellis/tasks/10-22-offline-json-ide/` | 208 | 5,414,269 | 205 tracked; only three generated bytecode files ignored |
| `.trellis/workspace/` | 2 | 11,405 | Both tracked; journal ignore issue no longer present |
| `.trellis/spec/` | 2 | 12,856 | Both tracked |
| `.trellis/workflow.md` | 1 | 39,316 | Tracked |

The local publication tree contains 81 paths across `local-preserved/`, workspace, specs, and workflow. These are overlapping selections, not an additional copy or size.

Keep all preserved source text, original-path/hash mappings, `.gitattributes`, review reports, task PRDs/design/plans/contexts, historical result and source maps, raw evidence logs, screenshots already classified as durable evidence, journal entries, and failed/pending/HOLD dispositions. Migration publication is not a new historical device pass.

Also preserve `.git`, `.github`, `docs`, `lib`, `assets`, `test`, `scripts`, `tool`, dependency manifests/locks, platform source/configuration, README files, LICENSE, and tracked generated registrants. Only the exact ignored generated registrants in section A are candidates. The prior artifact/private-backup limits still apply even after source publication.

## F. Root diagnostic logs: review before removal

| Exact path | Files | Bytes |
| --- | ---: | ---: |
| `flutter_01.log` | 1 | 4,627 |
| `flutter_02.log` | 1 | 6,118 |
| `hs_err_pid19132.log` | 1 | 15,493 |
| `hs_err_pid69244.log` | 1 | 14,791 |
| `hs_err_pid74676.log` | 1 | 15,527 |
| **Subtotal** | **5** | **56,556** |

All are ignored. Their contents were not read here. Confirm they are not the only failure evidence, and review privacy before any public upload. They are excluded from the lower-risk subtotal.

## G. WSL: previously observed inventory only

No WSL command was run for this report. The following is the earlier read-only `wsl --list --verbose` observation on 2026-11-26, not a refreshed state:

| Distribution | Earlier state | Version | JSON ownership |
| --- | --- | --- | --- |
| `Ubuntu` (default) | Stopped | 2 | Not established |
| `qfli-terminal-test` | Stopped | 2 | Not established |
| `qfli-terminal-al3-clean` | Stopped | 2 | Not established |
| `qfli-terminal-al3-test` | Stopped | 2 | Not established |
| `qfli-java-build` | Stopped | 2 | Not established |

No distribution is established as JSON-only. VHD paths, sizes, content, and current running state are unknown. Shared WSL has no overall cleanup coordinator. The app coordinator `w65:p1` owns its repository only and cannot authorize shared-WSL disposal. No start, terminate, shutdown, unregister, VHD deletion, or global-cache cleanup is authorized.

## Exact prerequisites for any later safe cleanup

**All applicable conditions must be met for each exact path; source publication alone is insufficient.**

1. **Publication and target identity:** preserve the pre-migration main/history and accepted source/evidence on the canonical remote. Confirm the intended target checkout, branch integration dispositions, app/core identities, and clean reviewed tree. The current local identity is `9113f2ec0380a999b05fe27fd10de33e549fb061`; do not substitute an unreviewed later tree.
2. **CI and acceptance:** wait for the required GitHub-only jobs on that exact accepted source/core revision to finish. Record run URLs, conclusions, checksums, and explicit blockers/waivers. Obtain the coordinator's final migration acceptance. CI is ongoing and acceptance is not complete at this inventory, so this prerequisite is not met. Never run local builds/tests/analyze/lint/install to satisfy it.
3. **Published-byte verification:** verify remote/target copies of durable Trellis evidence and preserved source against `local-preserved/manifest.json`, including aliases and existing tracked counterparts. Confirm `.gitattributes` preserves original bytes. Do not erase original-path mappings or rewrite historical failures/PENDING/HOLD statuses.
4. **Historical artifact closure:** before touching evidence-bound `build/`, OHOS package/intermediate state, prepared-input maps, or runtime originals, identify every required package/kernel/input/dependency and preserve it through a reviewed durable index. Necessary large packages must have verified GitHub Release-asset identities, byte lengths, SHA256 values, source/evidence links, availability, and retained original outcomes. Do not equate short-lived CI artifacts or a report naming an absent package with preservation.
5. **Private safety and backup retention:** keep UI/session material and all private or credential-bearing backups separate. Review contents only under appropriate authorization. Unsafe raw historical artifacts require secure private retention and an explicit disposition; do not upload whole snapshot bundles or replace raw claimed hashes with a sanitized version without recording both identities.
6. **Ownership and idleness:** confirm no active process, retained native-window custodian, pending ownership handoff, or unresolved HOLD requires the exact path. Reconcile terminal/empty-Job evidence with the owner; metadata existence and a historical stopped WSL listing do not prove current idleness.
7. **Exact scope and link protection:** immediately before any approved deletion, re-enumerate only the requested JSON paths without following reparse points. Confirm no tracked, newly untracked durable, source, manifest, signing, private-backup, or unmapped evidence file is included. Treat links as distinct objects; never recursively follow their targets. Reconcile ignored OHOS manifests before including them anywhere.
8. **Separate deletion authorization:** present a precise path-level deletion list with current file counts, logical sizes, evidence/private exclusions, and rollback/retention references. Obtain explicit authorization for that exact list. This report supplies no such authorization. Do not use unrestricted `git clean`, whole-checkout deletion, whole-`build/` deletion, WSL lifecycle actions, or global-cache removal.

Until these conditions are satisfied, every candidate remains **PENDING / HOLD**. The old `cleanup.md` and all historical evidence remain unchanged. No deletion has occurred.
