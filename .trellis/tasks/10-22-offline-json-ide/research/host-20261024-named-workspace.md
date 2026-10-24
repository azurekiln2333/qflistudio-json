# JSON named-workspace acceptance — October 24, 2026

The actual `jsonProfile` passed one new host widget regression through the real
`QfliApp`, Home, retained editor, FileExplorer and named-workspace dialog. Scoped
analysis reports **No issues found**. This is current-worktree host evidence;
shared publication and a new OHOS package remain separate gates.

## Observed behavior

1. Open the registered primary JSON project from Home; its existing standalone
   history restores `data.json`.
2. Use the actual workspace toolbar/dialog to name a workspace and add a second
   local JSON project. The workspace document records both roots and the live
   editor is attached to its identity.
3. Open the second root's same-name `data.json` through its tree, set distinct
   cursors, expand both nested folders and hide/show the sidebar.
4. Destroy the whole QfliApp and its retained editor controller. The persisted
   workspace preserves ordered document owners, active secondary tab, cursors
   and both expansions. Standalone history and four source files remain byte
   identical to their captured values.
5. Reload workspace metadata from disk, reconstruct the project/auth/settings
   stores and QfliApp, select Home's actual **工作区** scope and open its card.
   A new real EditorPage restores both owners, JSON types, document text, clean
   buffers, tab order, active tab, cursor positions and expanded trees.

The profile retains its JSON product key, offline-only policy and hidden
language chips. No replacement main-product profile is used. Desktop sidebar
hide/show retains its widget; whole-app destruction proves reconstruction.

## Commands, source and terminal identities

- Current test: `test/json_named_workspace_test.dart`, SHA256
  `b7c5b0b454bc1b23b901ca7337144fc6bd6bfdfa3d89b272a964f84ae43ab4b2`.
- Direct cached Flutter tool: `test --no-pub --concurrency=1 --reporter=expanded
  --timeout 45s test/json_named_workspace_test.dart`.
- SDK commands: `dart format test/json_named_workspace_test.dart` and
  `dart analyze test/json_named_workspace_test.dart`.
- Grant Web431/432, acceptance JSON434; automatic terminal release JSON435 to C.
- Successful invocation: `named-20261023T233005Z/`, October 24 **07:30:05–07:30:18
  +08:00** (October 23 23:30:05–23:30:18 UTC), elapsed 13.481 seconds.
- Format PID79956 exit0; test PID83400 exit0 (**1/1 PASS**); analysis PID62432
  exit0. Every owned Windows Job tree is confirmed empty; no timeout or launcher
  error. The test and analysis roots required recorded residual-descendant
  cleanup after their terminal result. Publication exit0 appended event435.
- All **294** captured app/core input hashes are identical before/after. App
  HEAD is `567513f46ad99a70281428eec0dd788af44a54d0`; core HEAD is
  `43d145d1ae649cfa2c8db576cf7a42729cfdcde8`, with dirty composed source explicitly
  listed in both captures. These source bytes, not HEAD alone, bind the result.

`result.json`, raw stdout/stderr logs, source captures and the exact automatic
release acknowledgement are retained in the successful invocation directory.

## Earlier failure and correction

The initial C416 invocation (`named-20261023T230801Z/`) failed **0/1** before
saving at the first workspace toolbar click; scoped analysis passed and its 294
inputs were stable. The test advanced fake time before AnimatedAlign had
started. A root's center became interactive while the right settings button
remained clipped. The fixture now pumps once to start the animation, advances
its duration, waits for the actual IconButton and finishes the dialog transition.
The original failure is retained; it is not reported as a capability pass.

## Integration ownership and limits

C407/411 explicitly delegated four narrow capability paths. JSON added the
default-true profile capability, independent saved-workspace helper, Home scope
gate and FileExplorer save gate. Other Home work, main/cloud policies, legacy
history, v4 project selector, page/controller/terminal and both core indexes
were preserved. The raw before/after SHA256 and Git blobs are in
`standalone-workspace-capability-handoff.json`; the exact narrow patch is
`standalone-workspace-capability-implemented.patch`.

C owns shared publication, legacy opt-out fixture updates and the separately
reported generic cloud-primary creation edge. Main's existing Home/saved-tab
dependencies are required in a published candidate; passing this dirty
worktree does not establish that candidate. This focused case is not a new full
118-test-suite result, native build, HAP or installed-device acceptance. The
family goal remains active.
