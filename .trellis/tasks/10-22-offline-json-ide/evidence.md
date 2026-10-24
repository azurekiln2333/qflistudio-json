# JSON implementation and acceptance evidence

Updated 2026-10-24. The authoritative device/build details are in `research/ohos.md` and its adjacent artifact/result JSON files. The full family request remains open in the C coordinator's umbrella task; this report covers the JSON app and attributable shared changes.

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
| JSON same-name multi-root integration | New real-profile case 1/1 passed and scoped analysis clean at October 23 11:31 +08:00; 291 captured inputs identical before/after; `research/host-20261023-multiroot.md` |
| JSON named Home workspace | Real jsonProfile/QfliApp save and whole-app reconstruction/reopen 1/1 passed; scoped analysis clean; 294 inputs identical; October 24 07:30 +08:00; `research/host-20261024-named-workspace.md` |
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

The later targeted source review `research/family-offline-followup-20261023.md` records 25 selected file hashes. Native refusals are now source-confirmed for Go, SQL, Note, Java, Dart, Python and Rust; Web restricts its browser entry to literal loopback previews. C's native remote handlers remained open at that capture. Java's active-document guard, owner-aware C++ `.h` highlighting and the shared API offline guard are source-fixed, with owner test/build/device gates kept separate. Owner-reported handler tests are attributed to their coordination messages; JSON did not rerun them.

`test/json_multi_root_editor_test.dart` adds a real-profile integration case for same-name files in two roots, secondary unsaved diagnostics, captured-owner document-tool saving and reconstruction. Independent source review corrected the selection-toolbar interaction and added stale-error/wave clearing assertions. The case passed in the explicitly handed-off JSON306 window; scoped analysis found no issues and all 291 captured inputs matched before/after. Wrapper307 immediately released the host slot to Lua212. This is one new focused case alongside the earlier 116-test suite result, not a new full 117-test suite run. The composed core remains unpublished and dirty; no new target build or device action was performed.

Go312 and JSON317 identified a separate workspace scope gap, acknowledged open by C320: named saved-workspace UI currently admits only the main release. The passing JSON case proves legacy child multi-root history, not that named-workspace entry. Shared owners will coordinate the standalone capability and migration; this remains an explicit family follow-up.

October 24 update: C407/411 explicitly delegated four narrow capability hunks. They now enable local named saving and the Home workspace scope for the actual JSON profile while preserving identity/offline policy, legacy history and main v4 selector behavior. The new actual-profile named Home regression passed 1/1 under Web431/JSON434; analysis is clean and all 294 captured inputs match. The original clipped-toolbar fixture failure is retained separately. C owns coherent publication with the main Home/saved-tab dependencies and the generic cloud-primary creation edge. No new target package or complete suite run is claimed; see `research/host-20261024-named-workspace.md`.
