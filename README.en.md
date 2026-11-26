# QFLIJson

Languages: [简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

QFLIJson edits and validates JSON files on your machine. The app parses, checks, formats and navigates JSON data. It is designed to run offline.

## What this app does

JSON is a data format. The app turns it into a readable result: parse status, error positions, formatted output and a navigable tree. The app never runs JSON as a program.

The app uses one product profile named `json`. That profile registers the JSON runner, the JSON analyzer, the tool cards, the document editor, the terminal commands and the bundled content.

## Editor and diagnostics

Open a `.json` file in the shared editor. The editor highlights keys, strings, numbers, booleans and null.

The app checks the exact text in memory, including unsaved edits. The check uses pure Dart parsing. No server or external program is involved.

| Behavior | Result |
| --- | --- |
| Valid JSON | Status shows `JSON 有效`. |
| Syntax error, duplicate key or unsupported number | The app shows a wavy underline, a line and column, and Problems entries. |
| Click a Problems entry | The editor selects the exact error span. The file stays unchanged on disk. |
| Fix the error | The next check clears the old warning. |

The document editor has three tabs. The Problems tab (`问题 N`, including the count) lists diagnostics. The Structure tab (`结构`) lists every node by JSON Pointer and jumps to the source on tap. The Output tab (`输出`) records local check results.

The editor also has `校验`, `格式化` and `键排序` actions. Saving stays an explicit user action. The app asks before it discards unsaved edits.

## Sixteen tool cards

The tools tab holds 16 independent cards. Each card runs locally and shows a working default input.

| # | Tool | What it does |
| --- | --- | --- |
| 1 | Format and check | Checks syntax, duplicate keys and error position. Indents the result. |
| 2 | Minify | Removes insignificant whitespace and keeps string content. |
| 3 | Recursive key sort | Sorts object keys. Array order stays the same. |
| 4 | JSON Pointer query | Selects a value with an RFC 6901 path. |
| 5 | Structural diff | Compares two documents and emits an applicable JSON Patch. |
| 6 | Merge Patch | Merges objects per RFC 7396. A null member deletes a field. Arrays replace in full. |
| 7 | JSON Patch | Applies `add`, `remove`, `replace`, `move`, `copy` and `test`. |
| 8 | Flatten | Writes a lossless path manifest that keeps container types. |
| 9 | Unflatten | Restores arrays, objects and empty containers from a manifest. |
| 10 | JSON Lines to array | Checks each line and reports the failing original line number. |
| 11 | Array to JSON Lines | Writes one element per line. |
| 12 | String escape | Encodes raw text as a JSON string. |
| 13 | String unescape | Restores quotes, newlines and Unicode escapes. |
| 14 | Object array to CSV | Merges column names and quotes commas, quotes and newlines. |
| 15 | Local Schema validation | Checks fields, types and constraints against a local schema. |
| 16 | Structure statistics | Reports node count, types, depth and UTF-8 byte size. |

Tool work runs in a background worker. The worker has a five-second deadline and a cancel button. Closing the page also stops the worker. A timeout or a cancel reports an error instead of a stale result.

## Run and terminal

The `Run` action reads the project entry file through the normal run route.

| Input | Exit code | Output |
| --- | --- | --- |
| Valid JSON | 0 | Formatted JSON on stdout |
| Invalid JSON | 1 | Position-bearing message on stderr and no output |
| Missing file or a path outside the project | 127 | Not-run message |

The sandbox terminal offers six read-only commands. They read local files and never overwrite the source:

```text
json check <file>
json format <file>
json minify <file>
json sort <file>
json stats <file>
json get <file> <JSON Pointer>
```

Run `json help` to print this list.

JSON is data. The app provides no breakpoint debugger.

## Workspaces

A workspace can hold several local project roots. A saved workspace stores a name, its members and the editor session. The session keeps open tab order, the active file, cursors and the expanded tree of each root.

Reopening a named workspace restores that state. A workspace belongs to its own identity, so opening a plain project does not restore another project's tabs.

A saved workspace stores the project identity and the last known path. A renamed or re-registered project can still be found. A missing folder is reported without touching it.

## Bundled content

The app bundles 340 examples and 340 tutorial lessons. It loads them as local assets and never falls back to a server or another product's catalog.

| Metric | Count |
| --- | --- |
| Examples | 340 |
| Tutorial lessons | 340 |
| New entries added on top of the original 100 | 240 |
| Categories of newly added entries | 24 |
| Newly added entries per category | 10 |
| Exercise answers checked | 440 |
| Input fixtures checked | 340 |

The original 100 example identities stay intact. Each example carries a code block, an expected output and input fixtures. Ten examples also promise a patch or merge result, and the check executes that promise.

## Requirements before you build

This repository is a Flutter app. It is an independent Git repository.

The app depends on `qfli_studio_core`. Check out `qflistudio-core` next to this one:

```text
checkout-parent/
  qflistudio-core/
  qflistudio-json/
```

| Dependency | Value |
| --- | --- |
| Dart SDK | `^3.11.5` |
| Flutter | A Flutter SDK that satisfies the Dart constraint |
| Shared core | `../qflistudio-core` by path |
| Editor | `re_editor` from `../qflistudio-core/vendor/re_editor` |
| Other packages | `path`, `cupertino_icons` |
| Test packages | `flutter_test`, `flutter_lints ^6.0.0` |

OHOS builds require a matching Flutter OHOS toolchain. The standard Flutter SDK does not include that toolchain. A different Flutter channel may also work, but this checkout does not record a result for it.

The installed app works offline. Initial cloud setup may need to download dependencies. Do not install SDKs or package caches in the local workspace.

## Build and run

Local work is limited to source editing, Git operations and read-only inspection.
All builds, tests, analyzers, lint and dependency installation run on GitHub.
Clone both repositories as siblings, keeping the reviewed core commit:

```text
git clone https://github.com/azurekiln2333/qflistudio-core.git
git -C qflistudio-core checkout 476a30acee21dc486ee2849dd8064a7be665e4d5
git clone https://github.com/azurekiln2333/qflistudio-json.git
```

Use GitHub Actions for execution. See [cloud-ci.md](docs/cloud-ci.md).

Create a project from the `JSON` template. The template writes `src/data.json` with this content:

```json
{
  "name": "QFLI project",
  "version": 1
}
```

Project configuration can specify the entry file. Otherwise the profile tries `data.json` first and `src/data.json` second before the shared fallback names.

## Verification

The commands below are cloud-only instructions. Do not execute them locally.

Run the test suite:

```text
flutter test
```

Run static analysis and the format check:

```text
dart analyze lib test
dart format --output=none --set-exit-if-changed lib test
```

The suite has 12 test files.
It covers the workbench, the tool workers, the content catalog, the run route and the terminal.
It also covers the offline host boundary, the editor diagnostics, the cross-root case and the named workspace case.

Regenerate or check the bundled content:

```text
python tool/build_json_content.py --check
```

`--check` verifies the three assets without writing. Running the script without `--check` rewrites them.

Run the on-device audit page against the installed catalog:

```text
flutter run --dart-define=QFLI_VERIFY_CATALOG=true
```

The audit holds one report at a time. It marks the previous report as incomplete before it starts. It writes each run to `json_verification_result.json` and stamps a fresh `runId`. A report write failure marks the run as failed.

### Recorded results

| Check | Recorded result |
| --- | --- |
| Host suite on the published core revision, 2026-10-24 | 124 tests passed with concurrency 1 |
| Static analysis | No issues reported for `lib` and `test` |
| Content reproducibility | All three assets match |
| Installed audit on an OHOS API 26 x86_64 emulator | 340 runner passes, platform `ohos`, no failures |

Host evidence: [published-core verification record](.trellis/tasks/10-22-offline-json-ide/research/host-20261024-published-core.md).

The device numbers come from the installed harness on 2026-10-22. They describe that package and those sources. Later shared-core edits fall outside that package, so they are not covered by that result.

The following gates stay unverified. Do not read the rows above as proof of them:

- Signed release distribution. Three configured signing files are absent, and the recorded device run used an unsigned package.
- Physical ARM devices. The recorded run used an x86_64 emulator only.
- Sibling products and their runtimes. JSON evidence does not prove them.
- Desktop-only tests as device proof. The two are separate evidence.

## Limits

The app refuses work that would exceed these bounds. It reports an error and leaves the source unchanged.

| Limit | Value |
| --- | --- |
| Source text | 2 Mi UTF-16 units |
| Value nodes | 50,000 |
| Nesting depth | 128 |
| Converted output | 4 Mi UTF-16 units |
| CSV cells | 200,000 |
| Cumulative patch work | 250,000 nodes |
| Tool worker deadline | 5 seconds |
| Run-route file read | 2 MiB of UTF-8 bytes |

Integers outside the signed 64-bit range fail with an instruction to store them as strings. The app never rounds a large integer silently. Decimal and exponent numbers use finite Dart doubles.

## JSON Schema support boundary

Tool 15 checks a document against a schema on your machine. The checker supports a local subset of JSON Schema 2020-12.

| Supported | Detail |
| --- | --- |
| Core keywords | `type`, `enum`, `const`, `required`, `properties`, `additionalProperties`, `items`, `prefixItems` |
| Size and count constraints | `minItems`, `maxItems`, `uniqueItems`, `minLength`, `maxLength`, `minProperties`, `maxProperties` |
| Numeric constraints | `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf` |
| Combination rules | `allOf`, `anyOf`, `oneOf`, `not` |
| References | `$ref` to `#` or `#/` inside the same document, plus `$defs` and `definitions` |
| Annotations | `$schema`, `$id`, `title`, `description`, `default`, `examples`, `$comment` |

`pattern` uses Dart Unicode regular expressions.

The checker reports these cases as errors. It never accepts them silently.

- `format` and any keyword outside the list above.
- A reference that is not local, such as an `http` URL.
- A conditional rule.
- `patternProperties` and other regular-expression property rules.
- A nested `$id` or `$schema` that declares another resource or dialect.
- A dialect other than 2020-12.
- A schema nested deeper than the depth limit, or a reference cycle that exceeds the evaluation cap.

A pass therefore means "valid inside this subset". It does not mean "valid under the full 2020-12 specification".

## Offline boundary

The profile declares `isOffline` and `offlineOnly`. It accepts `.json` files only.

The recorded host checks confirm these properties. They may still depend on the platform and the package:

- The OHOS module and the Android release manifest request no internet permission. The Android debug and profile manifests retain Flutter development internet permission.
- The OHOS host registers no login route, no external URL route and no ability start.
- A URL value inside a document stays inert data.
- A local schema check and a URL-data check create zero HTTP clients under `HttpOverrides`.

The OHOS host requests the clipboard permission. Tools and the editor copy results through the clipboard.

## Project layout

| Path | Content |
| --- | --- |
| `lib/main.dart` | Product profile, entry point and audit entry |
| `lib/json/json_workbench.dart` | Parser, Pointer, diff, patch, flatten, CSV and JSON Lines |
| `lib/json/json_schema.dart` | Local Schema subset |
| `lib/json/json_tools.dart` | The 16 tool cards and the worker |
| `lib/json/json_analyzer.dart` | Editor diagnostics provider |
| `lib/json/json_runner.dart` | Run route and terminal commands |
| `lib/json/json_document_page.dart` | Document editor with diagnostics and structure |
| `lib/content/` | Bundled content repository |
| `assets/content/` | Examples, tutorials and the catalog audit |
| `tool/build_json_content.py` | Content generator and checker |
| `test/` | Test suite |
| `.trellis/spec/json-offline.md` | Product contracts and the validation matrix |

Shared UI, the editor and the workspace store live in `../qflistudio-core`. Change them there, and keep their own tests and evidence with them.

Product contracts: [JSON offline specification](.trellis/spec/json-offline.md).
