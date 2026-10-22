# JSON implementation and acceptance evidence

Updated 2026-10-22. The authoritative current device/build details are in `research/ohos.md` and its adjacent artifact/result JSON files. The full family request remains open in the C coordinator's umbrella task; this report covers the JSON app and attributable shared changes.

## Delivered behavior

- 340 examples and 340 tutorial lessons: preserve the original 100, add 240 with distinct structures across 24 categories. Validate 440 exercise answers, 340 fixtures and 10 promised patch/merge operations. Asset generator check passes.
- Sixteen direct tool cards: format/check, minify, key sort, Pointer, diff, Merge Patch, JSON Patch, flatten/unflatten, JSON Lines in both directions, string escape/unescape, CSV, local Schema and statistics.
- Real JSON Run route prints actual formatted data, fails invalid JSON with source position, and does not fall through to a web server. Read-only sandbox terminal commands support quoted file paths and Pointer queries.
- Normal shared EditorPage uses jsonProfile.codeAnalyzer. Actual widget regression covers CodeEditor wavy decoration, Problems-panel click selection, unsaved corrections and unchanged disk. Separate document workspace adds navigable scalar/array structure, formatting, output and explicit saves.
- Background tool workers have cancellation and a killable five-second timeout. Limits bound source size/depth/nodes, accumulated Pointer paths, output size, CSV cells and repeated patch work. Large integer tokens fail explicitly instead of silently changing values.
- Offline profile, manifest and EntryAbility reject online entry points. Local schema/URL-data checks create zero HTTP clients under HttpOverrides.

## Local verification

| Check | Result / evidence |
| --- | --- |
| Complete JSON suite | 116/116 passed; `%TEMP%/qfli-json-final-review-tests.log` |
| Static analysis | `dart analyze lib test`: no issues; `%TEMP%/qfli-json-final-analyze.log` |
| Reproducible content | `python tool/build_json_content.py --check`: all three assets match |
| Trellis contexts | `python ../qfli_studio_core/.trellis/scripts/task.py validate 10-22-offline-json-ide`: both manifests valid |
| Diff whitespace | `git diff --check`: passed |
| Real cross-root workspace restoration | 27/27 passed; `%TEMP%/qfli-workspace-acceptance.log` |
| Backup owner regression plus compatibility | 83/83 passed; `%TEMP%/qfli-workspace-backup-after.log` |

The 83 core tests cover editor_workspace_backup, file_explorer_state, project_history_concurrency, workspace_editor_session, ai, widget, editor_run and retained_editor test files. The backup regression failed before the fix. JSON regressions likewise reproduced excessive accumulated Pointer allocation and A→B→A stale diagnostics before their fixes; before logs are `qfli-json-pointer-before.log` and `qfli-json-validation-race-before.log` under TEMP.

## Requirement audit

| Requirement | Status in this product |
| --- | --- |
| R1 Trellis and parallel ownership | Planning, spec, contexts, implementation, independent review and evidence present |
| R2 every example on OHOS | Initial installed harness: 340/340 runner passes; final package results are a separate gate in the OHOS report |
| R3 more than 100 new examples | 240 new, 340 total; all content fields audited |
| R4 language filters/badges | Shared ef34591 integration; JSON profile remains scoped to JSON |
| R5 useful direct tools | Sixteen independent cards with working defaults |
| R6 diagnostics/squiggles | Main EditorPage and document-workspace regressions pass |
| R7 tree restoration | Shared daddce2 plus focused explorer/history regressions |
| R8 multi-project workspace | Shared daddce2 preserves roots and owner-aware ordered tabs, active state and cursors; backup correction 96e6833 |
| R9 feasible debug/logs/panels | Actual Problems, validation output and local terminal; JSON has no executable breakpoint debugger |
| R10 offline | Host routing/permissions and no-HTTP local validation tests pass |
| R11 highlighting/C headers | JSON highlighting verified; C/C++ header runtime remains independently owned |
| R12 Python modules/pip | Separate Python product requirement, not proven by JSON evidence |
| R13 official tool research | Recorded in research/contracts.md |
| R14 standard commits/push | Core backup fix 96e6833 pushed to configured github/main; JSON has no remote |

## Source control ownership

Shared filter/diagnostics integration is ef34591; workspace integration is daddce2. This session's narrowly owned core backup correction was committed as `96e6833 fix(editor): preserve workspace file owner in backups` and pushed successfully to `github/main`. Concurrent Python/Go/shared-source changes were excluded.

JSON task files are committed separately. Preserve original `ohos/build-profile.json5`, `main_pages.json`, `AgreementReader.ets`, LICENSE and generated desktop registrants outside task commits. EntryAbility is intentionally part of the offline boundary change; its pre-change user snapshot is retained in ignored `.trellis/.runtime/entryability-before-offline.txt`. No product push destination is configured.

## Remaining independent gates

- Final harness installation and normal-app device UI acceptance must match the source/artifact evidence; initial-device success cannot stand in for the final package.
- Release signing, physical ARM devices and sibling language runtimes are not proven by the x86_64 emulator.
- Whole-family completion requires each runtime's own examples, modules/header behavior and device evidence. Keep the umbrella goal open.
