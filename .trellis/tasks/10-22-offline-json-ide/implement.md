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
- [ ] Recheck affected JSON behavior after the final shared editor/debug/workspace checkpoint. Any new OHOS build and installed-device acceptance must name its own source/artifact hashes; the archived 160-file result remains historical evidence.
- [ ] Track the standalone named-workspace capability acknowledged open by C320. The passing JSON case covers legacy multi-root ProjectHistory; verify a supported named save/reopen entry once the shared owner publishes it, preserving child migration and offline behavior.

Coordination 286 named JSON after C211/Web219; Web304 explicitly released the slot and JSON306 accepted. Wrapper307 recorded format/test/analyze exits 0 and immediately released to Lua212. This proves the focused host case on the captured composed source; final shared publication and a new OHOS package remain separate gates.
