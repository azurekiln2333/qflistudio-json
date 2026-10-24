# JSON offline product contracts

## 1. Scope / trigger

These contracts cover the product repository, editor/runner injection, local data tools, content assets and OHOS host. Shared core is a separate repository with concurrent owners. JSON evidence does not prove other executable-language runtimes.

## 2. Signatures

- `JsonWorkbench.inspect(String) -> JsonInspection`: source value, node spans and one-based diagnostics.
- `JsonWorkbench.applyPatch(Object?, Object?) -> Object?`: RFC 6902 subset; input is unchanged on success or failure. Removing the entire document is explicitly unsupported.
- `LocalJsonSchema.validate(Object?, Object?) -> List<String>`: local 2020-12 subset; unsupported keywords/resources are errors.
- `JsonOperationTask(operation, source, [secondary, timeout]).result -> Future<String>`; `cancel()` terminates its isolate.
- `JsonCodeAnalyzer.analyze(CodeAnalysisRequest) -> Future<CodeAnalysisResult>`: exact unsaved snapshots; UTF-16 offsets through the shared core contract.
- `JsonRunner.run(projectPath:, entryFile:)`: actual parsing/formatting through the normal Run route.
- Terminal: `json check|format|minify|sort|stats <file>` and `json get <file> <pointer>`.
- Build-time `QFLI_VERIFY_CATALOG=true` selects the installed-device audit entry; normal distributions omit it.

## 3. Contracts

- Product-specific content/services/UI stay here. Use StudioProfile hooks; do not add a second diagnostics registry.
- JSON Pointer follows RFC 6901 escaping and distinguishes absent fields from JSON null.
- Parser input: at most 2 Mi UTF-16 units, 50,000 value nodes and depth 128. Cumulative source paths and converted output are bounded; tools use 4 Mi output, 200,000 CSV cells and 250,000 cumulative patch-work nodes. Runner file reads additionally limit UTF-8 bytes to 2 MiB.
- Integers outside signed 64-bit range report an error and suggest strings. Decimal/exponent numbers use finite Dart doubles. Schema multipleOf avoids division-induced integer precision loss; uniqueness never saturates doubles through toInt.
- Tool work runs off the UI isolate with a five-second deadline. Kill the worker; timing out its Future alone is insufficient. Closing a page cancels its worker. Async document transforms never overwrite newer edits.
- Document saves use DocumentToolRequest.save. Core backups use `open.ownerProjectName`, regardless of the active tab. Diagnostic navigation never writes the file.
- No HTTP resolver, remote schema fetch, online login, web agreement or browser launch belongs to this product. URL values are inert data. OHOS requests only the existing clipboard permission.
- Catalog generation preserves the original 100 example identities and adds 240 structurally distinct examples. Run `python tool/build_json_content.py --check` before claiming reproducibility.
- The installed audit invalidates any previous success before verification and persists exceptions as failed reports. Every invocation has a fresh `runId`, start and finish UTC timestamps. The final result is flushed to a sibling temporary file before replacing the running/false marker, so a flush failure cannot expose a successful final report. A report write failure forces the returned/logged result to fail; device evidence must compare the fresh process result marker with the exported report, including its identity and contents.

## 4. Validation and error matrix

| Condition | Required behavior |
| --- | --- |
| Syntax error / duplicate key / unsupported number | Location-bearing diagnostic, Run exit 1, no fabricated output |
| Missing file or project escape | Run exit 127 (not run) |
| Invalid UTF-8 | Explicit encoding error; resource errors must not be mislabeled UTF-8 |
| Unknown schema keyword, nonlocal ref, nested resource | Explicit unsupported/schema error; no network request |
| Expanding patch/CSV/path manifest or excessive output | Stop with resource-limit error; source remains unchanged |
| Worker timeout/cancel/page disposal | Terminate isolate and close ports/timer; no stale UI update |
| Valid empty/null JSON | Valid value; absence is not inferred from null |

## 5. Good / base / bad cases

- Good: an unsaved syntax error in the normal EditorPage shows a wavy span and Problems entry; clicking selects its exact position without saving.
- Base: formatting `{"a":true}` produces indented JSON; `json get` can select a null value with exit 0.
- Bad: `{"id":9223372036854775809}` must not silently become a rounded double; a self-copying patch must not exhaust memory; a pathological schema pattern must not freeze the UI.

## 6. Tests required

- Service RFC examples, invalid inputs, precision, limits and generated diff/patch/flatten round trips.
- Every example, lesson, exercise answer, expected output and fixture; semantic patch/merge promises executed, not merely parsed.
- Real shared EditorPage with the product profile: wavy spans, Problems navigation, stale-error clearing, dirty state and unchanged disk.
- Same-name JSON files in two project roots: diagnostics use the secondary unsaved snapshot; a real document-tool save retains its captured owner after the active tab changes; primary contents remain unchanged; reconstructing the editor restores tab order, active owner and cursors. Collapse the Problems selection before looking for AppBar document actions, because a selected range shows the selection toolbar.
- Named workspaces use the actual JSON profile and Home/FileExplorer entries. Save a named document with two local roots, preserve standalone history and source bytes, destroy QfliApp, then reopen the Home workspace card and verify owners, tab order, active file, cursors and both expanded trees. Never substitute a main-product key. Pump once to start a sidebar animation before advancing its duration; seeing a root's center does not prove its right-hand toolbar is interactive.
- Tool workers: all defaults, errors, timeout, cancellation before spawn completes; document transform/save races.
- Host profile/permissions/routing plus HttpOverrides proving URL data and local schema operations create no HTTP client.
- Audit report regressions cover an old success followed by a throwing verifier, in-progress invalidation, repeated run identities, unavailable storage and initial/final export failures. A report from an earlier invocation is never accepted as current evidence.
- OHOS: installed x86_64 harness must log `QFLI_JSON_VERIFY_RESULT` with platform=ohos and 340 runner passes, then ordinary UI is checked separately. Record source/package hashes and versions. Desktop tests and HAP compilation are separate evidence.

## 7. Wrong vs correct

- Wrong: Future.timeout around synchronous schema validation on the main isolate. Correct: a dedicated worker killed on timeout and disposal.
- Wrong: runner status says available while Run falls through to a web server. Correct: return real parse output, diagnostics and exit codes via the injected runner.
- Wrong: claim all standalone runtimes pass because JSON parses on OHOS. Correct: retain independent family/runtime gates and link their evidence.
- Wrong: change active signing paths to hide missing credentials. Correct: use Hvigor's unsigned configuration for emulator testing and preserve the user's profile.
