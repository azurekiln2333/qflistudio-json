# JSON multi-root host integration — 2026-10-23

Actual run: 03:30:59–03:31:15 UTC (11:30:59–11:31:15 +08:00).

## Result

- New widget integration case: **1/1 passed**, exit 0, test body about four seconds.
- Scoped static analysis: **No issues found**, exit 0, about 3.3 seconds.
- Dart formatting: exit 0.
- Both snapshots contain **291** app/core input files; path sets and every byte hash match. App HEAD stayed `62fbeb108ee9f0e58206833a51a781abeb03ec89`; core HEAD stayed `e025805b60435fdedafd33e60082dc660afebe5a`. Both repository dirty states are captured; these hashes describe the composed working source, not a new published core commit.

## Real behavior exercised

`test/json_multi_root_editor_test.dart` mounts the actual `jsonProfile`, shared `EditorPage`, real JSON compute analyzer and `JsonDocumentPage`. No fake document-save hook or analyzer substitutes for those product paths.

1. Restore two registered roots with the same `data.json` filename, ordered tabs, secondary active owner and independent cursors.
2. Change only the secondary in-memory buffer to invalid JSON. Assert its exact diagnostic path/UTF-16 range, real wavy span and Problems navigation; both disk files remain unchanged.
3. Collapse the Problems selection so the real AppBar document action is available, then open the product document tool and check its captured file/root/text.
4. Switch the underlying active editor to the primary tab while the tool route remains open. Save the secondary edit through the actual page. Assert primary buffer/disk stay unchanged and the secondary disk/dirty state are correct.
5. Return to the secondary document, assert the old diagnostic message and wave clear, then destroy/reconstruct the editor and verify tab order, owner, saved contents, active state and both cursors.

Independent source review found and corrected the selection-toolbar fixture interaction before execution, and added explicit stale-wave clearing assertions. No shared or sibling source was edited for this regression.

## Commands and handoff

Executable: `D:/ProgramFiles/flutter_ohos/bin/flutter.bat` (format uses the adjacent Dart shim).

```powershell
dart format test/json_multi_root_editor_test.dart
flutter --suppress-analytics test --no-pub --concurrency=1 --timeout 45s test/json_multi_root_editor_test.dart
flutter --suppress-analytics analyze --no-pub test/json_multi_root_editor_test.dart
```

The snapshots hash all app/core `lib` and `test` Dart files, pubspec manifests/locks and content/tutorial JSON assets, with Git HEAD and status. Formatting completed before the first snapshot. The second snapshot follows test and analysis completion.

Global `qfli-core-release-sync` coordination 286 named this bounded window, Web304 explicitly released it, JSON306 accepted, and wrapper307 emitted the actual terminal exits and immediately released to Lua212. Tool session `48278` then reported terminal exit 0. No host handle is retained.

This is one new focused regression alongside the historical complete 116-test run. A full 117-test suite was **not** run in this window. There was no native build, HAP packaging or device operation. Final shared-core publication and a new source-bound OHOS acceptance remain open under the family goal.

Go312/JSON317 additionally identified the named-workspace entry scope. `saved_workspace.dart:14` admits only null/qflistudio as the main release; Home `_buildScopes` includes the workspace tab only for that release, and FileExplorer routes child profiles to legacy management. C320 acknowledged this as an open standalone capability gap. This regression proves legacy child ProjectHistory restoration; it does not prove the main-only named save/reopen UI. C/main own the shared capability and migration integration.

## Evidence bytes

- `host-20261023-multiroot-format.log`: 96 bytes, SHA256 `57b21f73d59a9a468f69d77355d12df45b3004f5bde06d6246898e09b1863fd4`
- `host-20261023-multiroot-test.log`: 224 bytes, SHA256 `0b0a31a4376a28249c9cd91d2c5c522712e7eee25180410bc84296cd95a782d7`
- `host-20261023-multiroot-analyze.log`: 98 bytes, SHA256 `92d3473517a3e3dbdf402db58a08ef0625191601c03ddcf5feb685f2f013f9be`
- `host-20261023-multiroot-result.json`: 329 bytes, SHA256 `5785c7f8f3737b47df44534a541bc33eae62d1453fcc4d0ae7633b99ca328e52`
- `host-20261023-multiroot-source-before.json`: 52325 bytes, SHA256 `b1ccf96bb173605c2f9bd47d3cf724f14368a01bf39b1feee944438d4c50ae2c`
- `host-20261023-multiroot-source-after.json`: 52430 bytes, SHA256 `d3e9b7541ca984b5fb41d58ab086e75a464f0a3d2713a3d3d8dae75be2cb544a`

- Test source SHA256: `99006e7ae6c0ff9637b858fa26715fa9bd06327de0c03a40ee778a7a8c152cc3`
