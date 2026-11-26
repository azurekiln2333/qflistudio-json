# Expanded source preservation review

## Scope and result

This follow-up reviewed only the 52 files already classified as local quarantine in the initial 101-file runtime inventory. No other repository, build tree, native package, cache root, or WSL distribution was inspected. No historical program was executed.

- Added 21 safe unique sources: 15 Python scripts, two PowerShell scripts, and four Dart snapshots, totaling **207,202 bytes**.
- Added 23 unique JSON fixture/result/sample payloads, totaling **455,587 bytes**, representing 25 original paths.
- Added payload total: **44 unique files / 662,789 bytes**.
- Cumulative payload total: **72 unique files / 883,702 bytes**.
- Two byte-identical device-sample originals map to the one preserved sample. Existing 20 tracked duplicates remain reused.
- Six files remain local quarantine; one bytecode file stays excluded. Nothing was deleted.

All added destinations append `.txt` to the full original filename. Example: `.trellis/.runtime/named-workspace-core-before/lib/pages/home_page.dart` maps to `runtime-sources/named-workspace-core-before/lib/pages/home_page.dart.txt`. Only the filename changes; original bytes, encoding, line endings, imports, and historical outcomes do not. Main will add `.gitattributes` with `* -text`. This agent did not create or modify that file.

## Content safety review

The full source/fixture text was read for credential screening. Checks covered private-key markers, recognizable long-lived tokens, nonempty credential literals, credential-bearing connection strings, and long encoded payloads. JSON objects were recursively inspected for nonempty password/token/secret/key/authentication/session fields. No embedded credential value was identified in copied source/fixture payloads. These checks are content review, not local analyze/lint/test execution.

Manual distinctions:

- Monitor `token` variables hold Herdr lifecycle sequence identifiers. They are not authentication credentials.
- The old Home source reads `widget.auth.token`; it contains code, not a captured credential.
- `ui_probe.py` is program source. Its UI output, `full-005.json`, and the PNG captures remain quarantined.
- The historical review already retained two visibly truncated credential-documentation placeholders. No complete signing password was copied from a build profile.
- Historical machine paths remain because the user required unchanged evidence bytes. They are not rewritten into current portable configuration.

Screening is not an absolute safety guarantee. Previously tracked duplicates were not re-certified for publication. Scripts remain archival text and may contain historical mutating/build/device commands; preserving their bytes does not authorize executing them.

## Historical identity and JSON roles

The four Dart snapshots match every corresponding `beforeBytes` and `beforeSha256` in `.trellis/tasks/10-22-offline-json-ide/research/standalone-workspace-capability-handoff.json`. This establishes the exact historical pre-change identities without reading another checkout.

The probe directory is explicitly named by the preserved `runtime/native703-inspector-fix.md` and `runtime/native703-inspector-fix-v2.md` reviews. They describe the original/candidate, prepared/no-prepared, missing entry, bad hash, wrong root, and unsafe-key cases. This is directory/case-level historical linkage, not a claim that each exact filename was enumerated in those reviews.

| Role | Original paths | Logical bytes | Treatment |
| --- | ---: | ---: | --- |
| Reproducible adversarial manifest inputs | 8 | 216,592 | Preserve unchanged; synthetic path/hash mutations |
| Historical probe inspection results | 13 | 238,859 | Preserve unchanged; retain PASS/BLOCKED/FAIL and timestamps |
| Task-owned device JSON fixtures/samples | 4 | 382 | Preserve two unique payloads; alias three identical valid originals |
| Transient staging-path lists | 2 | 5,785 | Keep local; not source or durable acceptance evidence |

`device-original.json`, `device-final.json`, and `device-restored.json` match the exact 123-byte SHA256 recorded by `ohos-ui-acceptance.json` under `observations.sampleRestored`. All three map to `runtime-fixtures/device-original.json.txt`. The 13-byte `device-invalid.json` is deliberately invalid JSON and remains unchanged; its missing-colon shape matches the historical diagnostic case, but its bytes are not claimed identical to the inline illustrative fixture.

Historical inspection result timestamps do not make them agent-session state. The actual `sessions/` control record remains excluded. A preserved local probe PASS is not a new execution, installed-device result, grant, or migration acceptance.

## Added source mapping

All paths below are repository-relative. SHA256 identifies the unchanged original bytes.

| Original path | Preserved path | Bytes | Original SHA256 |
| --- | --- | ---: | --- |
| `.trellis/.runtime/_native703_test/probe_archive.py` | `runtime-sources/_native703_test/probe_archive.py.txt` | 5705 | `6f81c1cc22a9a139ccdbc6c74132dcbbb5bdff09f4ef8f51be6a3e8ce3759b45` |
| `.trellis/.runtime/_native703_test/probe_committed.py` | `runtime-sources/_native703_test/probe_committed.py.txt` | 3446 | `8742cf07da329e489b9341f1dc49e61042abb29ea6adc1db8bb3869c0209d5cc` |
| `.trellis/.runtime/_native703_test/probe_inject.py` | `runtime-sources/_native703_test/probe_inject.py.txt` | 1891 | `68d14dc4567741345d5853728e6db18f45bb542553d3013a290df21346f37e88` |
| `.trellis/.runtime/_native703_test/probe_integrated.py` | `runtime-sources/_native703_test/probe_integrated.py.txt` | 3669 | `e6aa45112c23be943505b1d5b98854fbcc3e684dc5f763bed100f1b8582452c4` |
| `.trellis/.runtime/_native703_test/probe_manifest.py` | `runtime-sources/_native703_test/probe_manifest.py.txt` | 3433 | `4a2ce0c1db515b4cd607844ec4f1475e31d1c1b7452f3d8daaa4625ba7c64b5d` |
| `.trellis/.runtime/_native703_test/probe_prov.py` | `runtime-sources/_native703_test/probe_prov.py.txt` | 2799 | `5b7a7ab065d176dc149e5229d637ee62d1436d4a39fc88e90858fc19f8a32a23` |
| `.trellis/.runtime/capture_integration.py` | `runtime-sources/capture_integration.py.txt` | 1647 | `5c3badc9177f2e82d5bc1461602f9e513357f8feaebbe86a76314347f116ce00` |
| `.trellis/.runtime/inspect_json_release_hap_candidate.py` | `runtime-sources/inspect_json_release_hap_candidate.py.txt` | 23296 | `fc3ac0da4693a3e7140fc531423cfa0ad26e720fa3391c79fb82dd86dc2425c0` |
| `.trellis/.runtime/monitor_json_pi_native_final2.py` | `runtime-sources/monitor_json_pi_native_final2.py.txt` | 5438 | `100e6a6613668ef759147e2289cbb0e891fc4744e46008596c23a81376d86081` |
| `.trellis/.runtime/monitor_json_pi_native_final3.py` | `runtime-sources/monitor_json_pi_native_final3.py.txt` | 5284 | `95a9e9583b4494a8ae32606455638df6f239afeaa268f8494f0f2e92c6c02e9f` |
| `.trellis/.runtime/monitor_json_pi_native_next.py` | `runtime-sources/monitor_json_pi_native_next.py.txt` | 5432 | `07ed99254a1f6aca46ab8b2059bcb6a8d913850e3d8dad714dd82735298c8430` |
| `.trellis/.runtime/monitor_json_pi_native703_v2.py` | `runtime-sources/monitor_json_pi_native703_v2.py.txt` | 5416 | `2d174b7dda5bb4f1d32a6b4142a14e203564d6a165a627f0278ba2228b1a44e3` |
| `.trellis/.runtime/monitor_json_pi_native703.py` | `runtime-sources/monitor_json_pi_native703.py.txt` | 5407 | `8629dbdc564814ddb0a305320738ed450f82248444895dbba8ca006f403d2fb8` |
| `.trellis/.runtime/monitor_json_pi_requests.py` | `runtime-sources/monitor_json_pi_requests.py.txt` | 2810 | `dcb7acd29220229e922518f5a5c365f4d51da94905752cfeb52e4419e2830609` |
| `.trellis/.runtime/named-workspace-core-before/lib/editor/file_explorer.dart` | `runtime-sources/named-workspace-core-before/lib/editor/file_explorer.dart.txt` | 51318 | `dc3130632d2b1371421e68b46804c4ecb7382828521a26539c396493da759a36` |
| `.trellis/.runtime/named-workspace-core-before/lib/pages/home_page.dart` | `runtime-sources/named-workspace-core-before/lib/pages/home_page.dart.txt` | 50065 | `a170901b4280701089856c2988c2ba64570980dc0c1e871e4d33b76fa70f52b4` |
| `.trellis/.runtime/named-workspace-core-before/lib/services/studio_profile.dart` | `runtime-sources/named-workspace-core-before/lib/services/studio_profile.dart.txt` | 13128 | `4bfc3fac6d6ab25dc0b54ed4dd98aac80fc67a43d4580ddbd7c17f0fb754123a` |
| `.trellis/.runtime/named-workspace-core-before/lib/workspace/saved_workspace.dart` | `runtime-sources/named-workspace-core-before/lib/workspace/saved_workspace.dart.txt` | 8220 | `1464673830eededa2c0eaf658fc7e2aed46c60caec372c69b066d1ae5369f4ef` |
| `.trellis/.runtime/run_json_multiroot.ps1` | `runtime-sources/run_json_multiroot.ps1.txt` | 2441 | `a70b1316412bed5e4d152c103b2a156fcaada21b8be940de089b1074920fdb0c` |
| `.trellis/.runtime/run_json_named.ps1` | `runtime-sources/run_json_named.ps1.txt` | 5062 | `4f31824d26e56f923714c752b6de4b80676bd785e6260bbef5ddf97e587b4712` |
| `.trellis/.runtime/ui_probe.py` | `runtime-sources/ui_probe.py.txt` | 1295 | `ddac655f8b491828afbfb1c0db98e1d645958fd7669648654d9aed556ea054ee` |

## Added fixture and result mapping

Each fixture/result was reviewed as task-owned input or historical inspection evidence. The original status is not promoted or rewritten.

| Original path | Preserved path | Role | Bytes |
| --- | --- | --- | ---: |
| `.trellis/.runtime/_native703_test/candidate-prepared.json` | `runtime-fixtures/_native703_test/candidate-prepared.json.txt` | `historical_probe_inspection_result` | 58362 |
| `.trellis/.runtime/_native703_test/candidate-tampered.json` | `runtime-fixtures/_native703_test/candidate-tampered.json.txt` | `historical_probe_inspection_result` | 425 |
| `.trellis/.runtime/_native703_test/candidate.json` | `runtime-fixtures/_native703_test/candidate.json.txt` | `historical_probe_inspection_result` | 58363 |
| `.trellis/.runtime/_native703_test/live.json` | `runtime-fixtures/_native703_test/live.json.txt` | `historical_probe_inspection_result` | 469 |
| `.trellis/.runtime/_native703_test/prepared-tampered.json` | `runtime-fixtures/_native703_test/prepared-tampered.json.txt` | `reproducible_adversarial_fixture` | 212403 |
| `.trellis/.runtime/_native703_test/probe-badsha.json` | `runtime-fixtures/_native703_test/probe-badsha.json.txt` | `reproducible_adversarial_fixture` | 558 |
| `.trellis/.runtime/_native703_test/probe-min.json` | `runtime-fixtures/_native703_test/probe-min.json.txt` | `reproducible_adversarial_fixture` | 612 |
| `.trellis/.runtime/_native703_test/probe-missing.json` | `runtime-fixtures/_native703_test/probe-missing.json.txt` | `reproducible_adversarial_fixture` | 473 |
| `.trellis/.runtime/_native703_test/probe-unsafekey.json` | `runtime-fixtures/_native703_test/probe-unsafekey.json.txt` | `reproducible_adversarial_fixture` | 733 |
| `.trellis/.runtime/_native703_test/probe-wrongapp.json` | `runtime-fixtures/_native703_test/probe-wrongapp.json.txt` | `reproducible_adversarial_fixture` | 583 |
| `.trellis/.runtime/_native703_test/probe-wrongcore.json` | `runtime-fixtures/_native703_test/probe-wrongcore.json.txt` | `reproducible_adversarial_fixture` | 618 |
| `.trellis/.runtime/_native703_test/probe-wrongsha.json` | `runtime-fixtures/_native703_test/probe-wrongsha.json.txt` | `reproducible_adversarial_fixture` | 612 |
| `.trellis/.runtime/_native703_test/res-probe-badsha.json` | `runtime-fixtures/_native703_test/res-probe-badsha.json.txt` | `historical_probe_inspection_result` | 421 |
| `.trellis/.runtime/_native703_test/res-probe-min.json` | `runtime-fixtures/_native703_test/res-probe-min.json.txt` | `historical_probe_inspection_result` | 59145 |
| `.trellis/.runtime/_native703_test/res-probe-missing.json` | `runtime-fixtures/_native703_test/res-probe-missing.json.txt` | `historical_probe_inspection_result` | 427 |
| `.trellis/.runtime/_native703_test/res-probe-unsafekey.json` | `runtime-fixtures/_native703_test/res-probe-unsafekey.json.txt` | `historical_probe_inspection_result` | 408 |
| `.trellis/.runtime/_native703_test/res-probe-wrongapp.json` | `runtime-fixtures/_native703_test/res-probe-wrongapp.json.txt` | `historical_probe_inspection_result` | 416 |
| `.trellis/.runtime/_native703_test/res-probe-wrongcore.json` | `runtime-fixtures/_native703_test/res-probe-wrongcore.json.txt` | `historical_probe_inspection_result` | 459 |
| `.trellis/.runtime/_native703_test/res-probe-wrongsha.json` | `runtime-fixtures/_native703_test/res-probe-wrongsha.json.txt` | `historical_probe_inspection_result` | 425 |
| `.trellis/.runtime/_native703_test/v2-noprepared.json` | `runtime-fixtures/_native703_test/v2-noprepared.json.txt` | `historical_probe_inspection_result` | 393 |
| `.trellis/.runtime/_native703_test/v2-prepared.json` | `runtime-fixtures/_native703_test/v2-prepared.json.txt` | `historical_probe_inspection_result` | 59146 |
| `.trellis/.runtime/device-final.json` | `runtime-fixtures/device-original.json.txt` | `task_owned_device_sample` | 123 |
| `.trellis/.runtime/device-invalid.json` | `runtime-fixtures/device-invalid.json.txt` | `task_owned_invalid_json_fixture` | 13 |
| `.trellis/.runtime/device-original.json` | `runtime-fixtures/device-original.json.txt` | `task_owned_device_sample` | 123 |
| `.trellis/.runtime/device-restored.json` | `runtime-fixtures/device-original.json.txt` | `task_owned_device_sample` | 123 |

## Remaining local-only material

| Original path | Bytes | Reason |
| --- | ---: | --- |
| `.trellis/.runtime/__pycache__/prepare_json_ohos_inputs.cpython-313.pyc` | 43154 | Generated bytecode; excluded from evidence closure; no deletion authorized. |
| `.trellis/.runtime/full-005.json` | 40711 | Actual UI dump/screenshot explicitly excluded by user; privacy safety not established; LOCAL QUARANTINE only. |
| `.trellis/.runtime/named-staged-paths.json` | 2886 | Reviewed as transient lists of staging paths, not source, test inputs, or durable acceptance records; omitted from evidence payload and retained locally. |
| `.trellis/.runtime/release-staged-paths.json` | 2899 | Reviewed as transient lists of staging paths, not source, test inputs, or durable acceptance records; omitted from evidence payload and retained locally. |
| `.trellis/.runtime/sessions/codex-json-offline-20261022.json` | 156 | Dynamic agent-session control state explicitly excluded by user; not inspected for publication and not copied. |
| `.trellis/.runtime/state-005.png` | 2132608 | Actual UI dump/screenshot explicitly excluded by user; privacy safety not established; LOCAL QUARANTINE only. |
| `.trellis/.runtime/ui-current.png` | 279612 | Actual UI dump/screenshot explicitly excluded by user; privacy safety not established; LOCAL QUARANTINE only. |

## Integrity, scope, and closure

Every new original and destination was re-read for byte length and SHA256 equality. The manifest preserves mappings for all 101 original paths, including aliases, prior tracked counterparts, and local-only omissions. Historical evidence files and runtime originals were not edited.

Only this `local-preserved/` directory was written. No Git mutation, local build/test/analyze/lint/install, device operation, WSL lifecycle action, or network request occurred. The task stops here; no further scope expansion is needed.

No old build package or whole runtime/build snapshot was published. Large native/HAP artifacts still require a separately reviewed GitHub Release-asset index and preservation before any cleanup. Credential-bearing raw build snapshots must not be published as whole bundles. UI/session exclusions are deliberate, not permission to delete their originals.
