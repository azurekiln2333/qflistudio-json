# Design

## Ownership

Keep JSON services, curriculum, UI, terminal integration and tests in qfli_json. Use StudioProfile contentRepositoryFactory, toolsTabBuilder, documentToolBuilder, codeAnalyzer, editorFileTools and runner hooks. Shared fixes are narrowly scoped, separately committed, and verified in core. The C coordinator owns shared-core integration; this session contributes reviewed explorer/history work and the owner-aware backup correction. JSON workers own content/service review, editor regressions, and OHOS build/device evidence respectively.

## JSON data flow

Product asset documents -> typed ContentCatalog -> profile-scoped local examples/tutorial pages -> core import workflow -> editor. A single product JsonWorkbench service owns parsing, line/column diagnostics, JSON Pointer selection, deep sorting, flatten/unflatten, structural comparison, merge patch, JSON Patch, JSON Lines, tabular CSV conversion and explicitly scoped local schema validation. Tool UI, JSON runner, terminal delegate and document workspace all consume it.

The document workspace keeps editable source in memory and saves only through DocumentToolRequest.save so core backup/history/dirty-state contracts remain intact. Debounced diagnostics and navigable structure use parsed offsets; traversal/limits protect UI responsiveness. Highlight JSON keys, strings, literals and numbers; syntax error spans receive wavy underlines. Problems and output belong to the open document; no fake runtime debugging.

The normal shared EditorPage uses the shared CodeAnalyzer contract and EditorAnalysisController. JsonCodeAnalyzer validates in-memory snapshots in a background isolate and returns UTF-16 source offsets. The controller renders wavy spans and an actionable Problems panel; navigation does not save the document. No separate diagnostic registry is introduced.

Interactive transformations run in a dedicated JsonOperationTask isolate, which is killed on timeout, cancellation, or disposal. Input controls show a running state; document formatting applies only if the captured source still matches the live buffer. Parser and transformation limits bound nodes, depth, cumulative paths, output, CSV cells and repeated patch work. Integer tokens outside signed 64-bit range fail explicitly instead of being silently rounded; fractional values use the runtime's finite doubles.

## Shared editor state

Restore explorer expansion at construction and fence asynchronous restoration with captured project identity/generation. Serialize history read-modify-write per project. Shared commits ef34591/daddce2 persist selected workspace roots, independent expansion, tab order, active file, owning project type and cursor/folding state. File operations and pre-save backups use the opened file's owner, even when a different project tab is active.

## Curriculum

Own JSON content assets and use the product repository hook so other products' catalogs are unaffected. Preserve all previous JSON content, correct invalid snippets, then add more than 200 distinct practical JSON documents grouped by concepts and applications. Exercises and expected output must be machine checked. Supply an OHOS validation entry point that calls the same service/catalog; execution requires an attached device and is an explicit gate.

## Offline and compatibility

No external schema downloads, package installation, telemetry, cloud services or port forwarding. Local URL strings in example data are inert. Only local #/ references are accepted by schema/patch tools. Remove INTERNET from the JSON manifest after inspecting the host's agreement path; never overwrite the user's agreement reader/signing changes. Avoid shared profile API changes where existing injection hooks suffice.

## Review and rollback

Use product and core commits separately. No broad reformatting of shared files. Keep existing uncommitted files out of commits. Revert the respective task commit to remove product features or shared fixes independently. Do not archive or mark the full goal complete if device/family evidence is absent.
