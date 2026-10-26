# Implementation and verification

1. [x] Read the entire attachment, inspect product/core/Trellis, record original dirty files and environment.
2. [x] Create planning artifacts and contexts before implementation; user already explicitly authorized immediate continuation.
3. [x] Research official JSON/editor contracts and record references.
4. [x] Add JSON workbench service with rigorous edge-case tests and honest local-schema boundaries.
5. [x] Preserve/check all old JSON content and add 200+ useful tested examples plus richer tutorials in product assets; wire repository factory.
6. [x] Add direct tools-tab cards, document diagnostics/highlighting/tree/problems/output, JSON runner and sandbox terminal commands.
7. [x] Fix shared explorer state and history concurrency; verify multi-project workspace and tutorial/example filters/badges with focused regression tests.
8. [x] Inspect and tighten JSON OHOS offline boundary without overwriting original host changes.
9. [x] Run product flutter analyze/test; core focused tests and analyze; use current OHOS Flutter build and inspect bundled assets/permissions. October 23 serial compatibility rerun also passed 116 tests; device scope remains the recorded build snapshots.
10. [x] Execute target-device catalog validation if hdc exposes a device. Final installed OHOS harness passed all 340 runners and 16 background tool defaults; see research/ohos-harness-final-result.json.
11. [x] Conduct requirement-by-requirement completion review, update specs/journal, make conventional commits for owned files; push only to configured authoritative destination. Implementation 6df694e; core backup 96e6833 pushed; final evidence accompanies this checklist. Product has no remote, and the family task remains in progress.

## Commands

- `flutter --version`, `flutter analyze --no-pub`, `flutter test --no-pub`
- Core focused editor/history/content/offline tests after changes, followed by broader checks only where justified.
- `flutter build hap --help`, then supported unsigned debug build; retain complete build logs.
- `hdc list targets` before device validation; inspect HAP with the available archive tools.
- `git diff --check`, staged diff review, `git status --short`, `git remote -v` before commits/push.

## Gates

Do not claim all product-family runtimes passed from JSON tests. Do not claim OHOS execution from a compiled bundle. Keep missing family/device verification explicit in evidence.md and leave parent in progress.

## Final shared-core integration follow-up

- [x] Author a product-owned regression using the real JSON profile, shared EditorPage and JsonDocumentPage with two roots containing the same filename. Cover unsaved diagnostics, captured-owner saves, unchanged primary contents and restored tabs/active state/cursors.
- [x] Independently review and execute the new regression against an explicitly coordinated shared-source checkpoint; run scoped analysis and record exact source fingerprints. October 23 11:31 +08:00: 1/1 passed, scoped analysis clean, all 291 captured inputs identical before/after; see research/host-20261023-multiroot.md.
- [x] Recheck affected JSON host behavior after the published shared editor/debug/workspace checkpoint: full124/124 on core2f9039a with stable513-input capture. Any new OHOS build and installed-device acceptance must name its own source/artifact hashes; the archived 160-file result remains historical evidence.
- [x] Track and verify the standalone named-workspace capability acknowledged open by C320. Coherent publication2f9039a and actual JSON named save/reopen now participate in the full124-test run, preserving child migration and offline behavior.

October 24 follow-up: C407/411 explicitly delegated four narrow shared capability hunks. Implemented default-true `StudioProfile.supportsSavedWorkspaces`, its independent helper, the Home scope gate and FileExplorer named-save entry; no core staging/commit and no history/selector/page edits. Exact raw before/after hashes and Git blobs are in `research/standalone-workspace-capability-handoff.json`; C owns coherent publication with the main Home/saved-tab dependencies. Product regression `test/json_named_workspace_test.dart` uses real QfliApp/jsonProfile and actual Home save/reopen. First C416 window failed before saving at a clipped toolbar finder (0/1); its failure and clean analysis are retained. Corrected fixture passed 1/1 under Web431/JSON434, scoped analysis clean, all 294 captured inputs identical; automatic release435 to C. See `research/host-20261024-named-workspace.md`. Actual-worktree named Home behavior is verified; the checklist stays open for coherent shared publication and source-bound target acceptance.

## Final published-core host gate and report reliability

C published capability commit `2f9039a3ba95449679b17257b0313c1ee3644a2c`, exact tested tree `d21ffcdc7ac9c834e0b788b21178e9f80768a519`. C reports 69/69 core tests, actual JSON named workspace 1/1 and 12-file analysis clean; event493 confirms four remote branch identities. This resolves coherent capability publication but does not replace the final JSON suite or device gates.

- [x] Source review found that an audit exception could leave the previous successful disk report. Route the page through a report coordinator that invalidates old success, persists failures, records fresh run identity/UTC times and refuses success after export failure.
- [x] Add six focused report regressions, including pending invalidation, failed staging and failed final export. Independent review caught the write-before-flush edge; final results now finish flushing in a separate file before replacement.
- [x] Run the complete JSON suite, analysis, format and reproducible-content checks against the exact published core with all package mappings and native source fixtures captured:124/124 PASS, analysis/format/content clean,513 inputs stable; see research/host-20261024-published-core.md. Record owned overlays and compare their canonical blobs during commit review.
- [ ] Build and inspect new source-bound normal/harness HAPs, then perform separately authorized target acceptance with fresh process marker/export identity matching. Historical x64 evidence is retained separately.

Coordination 286 named JSON after C211/Web219; Web304 explicitly released the slot and JSON306 accepted. Wrapper307 recorded format/test/analyze exits 0 and immediately released to Lua212. This proves the focused host case on the captured composed source; final shared publication and a new OHOS package remain separate gates.


### 2026-10-26: source-only native retry readiness

Archived `research/native-retry-20261026`: exact prepared initialized805/7 snapshot, raw
captures, nine runner/test files, 35 passing pure controls, six source-only CLI cases and zero
PowerShell syntax errors. The child now compares reviewed prepared identity before SDK
execution. The inspector binds declared isolated plugins and compiler evidence. Final offline
reinspection of the preserved703 harness passes diagnostically only. Grant703 remains failed. No
new native grant or device execution occurred. Parent observer and bounded Job helper remain
unchanged. Frozen core remains published2f9039a, not current C work-in-progress equivalence. A
new serial grant, then separate assigned-target device authorization, remain required. Task
remains in progress for current-source OHOS and family acceptance.

Root found uncertain Job handles close during failed cleanup in the unchanged helper6657cffb.
This source-only archive is NOT READY. Coordinator notice767 records the issue.
A separate retention repair must precede a fresh grant request. No native window was started.


### 2026-10-26: retained-HOLD source repair

The helper now retains original handles on uncertain cleanup. Parent validation uses a
non-terminating custodian deadline. Payloads and publishers retain exact ownership until
terminal and Jobactive0. Seven host controls are authored, not executed. Two independent
source reviews accepted this hierarchy. Four PowerShell AST checks passed. Old native
manifest9d is retired for execution. Protocol question776 and a new controls grant remain
pending. No compiler, SDK, native or device execution occurred.
