# JSON implementation and acceptance evidence

Updated 2026-10-23. The authoritative device/build details are in `research/ohos.md` and its adjacent artifact/result JSON files. The full family request remains open in the C coordinator's umbrella task; this report covers the JSON app and attributable shared changes.

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
| Complete JSON suite | 116/116 passed on October 22; October 23 serial compatibility run also 116/116; `research/host-20261023-serial-tests.log` |
| Static analysis | `flutter --suppress-analytics analyze --no-pub`: no issues; `research/host-20261023-analyze.log` |
| Reproducible content | `python tool/build_json_content.py --check`: all three assets match |
| Trellis contexts | `python ../qfli_studio_core/.trellis/scripts/task.py validate 10-22-offline-json-ide`: both manifests valid |
| Diff whitespace | `git diff --check`: passed |
| Real cross-root workspace restoration | 27/27 passed; `%TEMP%/qfli-workspace-acceptance.log` |
| Backup owner regression plus compatibility | 83/83 passed; `%TEMP%/qfli-workspace-backup-after.log` |

The 83 core tests cover editor_workspace_backup, file_explorer_state, project_history_concurrency, workspace_editor_session, ai, widget, editor_run and retained_editor test files. The backup regression failed before the fix. JSON regressions likewise reproduced excessive accumulated Pointer allocation and A→B→A stale diagnostics before their fixes; before logs are `qfli-json-pointer-before.log` and `qfli-json-validation-race-before.log` under TEMP.

October 23 integration checks first observed a transient shared-core `Map<String, ?>` syntax error (98 tests passed, four files failed to load). After its owner corrected the type, the default parallel run hit Dart VM out-of-memory/software-rendering backing-store errors (103 passed, incomplete tests). A controlled `flutter --suppress-analytics test --no-pub --concurrency=1` then passed all 116 with no OOM. The original failure logs are retained alongside the serial log. Core HEAD was `e025805b60435fdedafd33e60082dc660afebe5a` before and after the serial run, but five core files changed during that window; adjacent before/after fingerprints make this boundary explicit. None of those shared changes were committed by this task.

Research attributes preserve report JSON, screenshots and raw logs byte for byte across Git checkouts. Logs are marked binary for diff purposes because parser test names include deliberate whitespace; their original output remains readable from disk.

## Requirement audit

| Requirement | Status in this product |
| --- | --- |
| R1 Trellis and parallel ownership | Planning, spec, contexts, implementation, independent review and evidence present |
| R2 every example on OHOS | Final installed harness: 340/340 runner passes, platform=ohos, failures=[]; all 16 tool workers also pass |
| R3 more than 100 new examples | 240 new, 340 total; all content fields audited |
| R4 language filters/badges | Shared ef34591 integration; JSON profile remains scoped to JSON |
| R5 useful direct tools | Sixteen independent cards with working defaults |
| R6 diagnostics/squiggles | Regressions plus ordinary OHOS wave, Problems navigation, unsaved correction and document output pass |
| R7 tree restoration | Shared daddce2, focused regressions and ordinary OHOS sidebar/process-restart expansion checks |
| R8 multi-project workspace | Shared daddce2 preserves roots and owner-aware ordered tabs, active state and cursors; backup correction 96e6833 |
| R9 feasible debug/logs/panels | Actual Problems, validation output and local terminal; JSON has no executable breakpoint debugger |
| R10 offline | Host routing/permissions and no-HTTP local validation tests pass |
| R11 highlighting/C headers | JSON highlighting verified; C/C++ header runtime remains independently owned |
| R12 Python modules/pip | Separate Python product requirement, not proven by JSON evidence |
| R13 official tool research | Recorded in research/contracts.md |
| R14 standard commits/push | Core backup fix 96e6833 pushed to configured github/main; JSON has no remote |

## Source control ownership

Shared filter/diagnostics integration is ef34591; workspace integration is daddce2. This session's narrowly owned core backup correction was committed as `96e6833 fix(editor): preserve workspace file owner in backups` and pushed successfully to `github/main`. Concurrent Python/Go/shared-source changes were excluded.

JSON implementation is `6df694e feat(json): add offline workbench and 340 verified examples`. Preserve original `ohos/build-profile.json5`, `main_pages.json`, `AgreementReader.ets`, LICENSE and generated desktop registrants outside task commits. EntryAbility is intentionally part of the offline boundary change; its pre-change user snapshot is retained in ignored `.trellis/.runtime/entryability-before-offline.txt`. No product push destination is configured.

## Device scope and remaining independent gates

- Final harness installation passed on October 22 at 20:48 local time. Ordinary UI checks continued through October 23; `research/ohos-ui-acceptance.json` records exact observations and screenshot hashes. The original task-created sample was restored and byte-checked after restarting the app.
- Both device builds bind the recorded 160-file snapshots. Later shared-core edits are not covered by the installed HAP. Host compatibility passing during concurrent edits is not a frozen-source device result.
- Release signing, physical ARM devices and sibling language runtimes are not proven by the x86_64 emulator.
- Whole-family completion requires each runtime's own examples, modules/header behavior and device evidence. Keep the umbrella goal open.

## Family follow-up review

Three additional source-only reviews are recorded in `research/family-editor-audit-20261023.md`, `family-offline-host-audit-20261023.md` and `family-artifact-audit-20261023.md`. They cover all eleven product profiles/native hosts and distinguish retained native capabilities, current UI gating, loopback services, unsupported-document diagnostics and package/source identity. They do not establish new sibling runtime or device passes.

The Java unsupported-document clean result and C++ `.h` grammar mismatch were reported to the Java and shared-core owners. Native offline-entry findings were sent to the relevant product owners; Web/Python artifact drift was also reported. Coordination message 237 in the global `qfli-core-release-sync` channel records JSON's durable handoff, device release and C-owned follow-ups. A queued report is not a resolved issue; `research/family-followups-20261023.json` preserves the open dispositions. No sibling/core source changes, additional builds or device operations were made for these reviews.
