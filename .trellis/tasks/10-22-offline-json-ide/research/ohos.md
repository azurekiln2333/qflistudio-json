# OHOS toolchain, offline host and verification evidence

## Current verified result — 2026-10-23

Both final x64 debug builds succeeded with the installed Hvigor's native `-c properties.enableSignTask=false` option, without editing the user's signing profile. The final harness was updated, started and executed on the API 26 HarmonyOS emulator at `127.0.0.1:5555`. Its actual process `5271` emitted `QFLI_JSON_VERIFY_RESULT` at device log time `20:48:02.595` with `passed: true`, all 340 examples and Runner executions, 340 tutorials, 340 lessons, 440 exercise answers, 340 fixtures, 10 semantic operations, all 16 background-isolate tools, and no failures. The JSON report was exported from the app sandbox and the passed screen was visually checked.

The ordinary app was then rebuilt with an explicitly empty `DART_DEFINES`, successfully updated using `hdc install -r`, and started with `aa start`. It is the current installed app. Its unsigned HAP is `ohos/entry/build/default/outputs/default/entry-default-unsigned.hap`, `123864987` bytes, SHA-256 `a7b17b33ca7a97ccdbc62ca5addbf31bf8f960ff716146298f9ac2fc48aebfa7`, modified at `2026-10-22T21:07:21.062148+08:00`. Ordinary UI acceptance ran on October 22–23; results follow below.

Both compiled archives request only `ohos.permission.READ_PASTEBOARD`, with no INTERNET permission. The three bundled content JSON assets match the source bytes. Both builds used the same 160 app/core `lib` Dart and product content JSON files; fingerprint comparisons found no changed, added or removed files during the builds or between the two snapshots. This is an offline app build and target execution result; it does not claim that the toolchain built without network access, that an archive was signed, or that physical hardware was tested.

Final evidence owned by this worker:

- `ohos-harness-final-result.json`, `ohos-harness-final.log`, and `ohos-harness-final.png`: exported report, filtered process log, and visibly passed harness screen.
- `ohos-final-harness-artifact.json` and `ohos-final-source-snapshot.json`: harness archive/asset/permission/kernel hashes and source fingerprints. Harness HAP SHA-256: `e2a945a8687ffa73e8552a5874610ef0d44420320dec5b3297f805e3f3f71268`; kernel SHA-256: `5b6a52a26e6130fc9c34735613558aabef9b84f70b09117bdc125a4f119bc71a`.
- `ohos-normal-artifact.json` and `ohos-normal-source-snapshot.json`: ordinary archive metadata and its separately captured source/repository state. Normal kernel SHA-256: `51d40fff1d792540983f00c8c8ec80db456187eceaf7265b12191315f4ba3933`.

The ordinary source snapshot records app HEAD `6df694e3e695fdb69d7b59232cfc4b833139f3f6` and shared-core HEAD `96e6833f46a791949cfa58d36e7ba7a25720d18d`. The shared working tree also contained another session's Go snippet/import changes in `code_import_service.dart`, `code_snippet.dart` and the new `go_source_file_name.dart`; those actual bytes are fingerprinted in both builds. They are not attributed to this JSON task. Snapshot metadata records the exact working-tree file list, including unrelated content-generator work, without incorporating those changes into the task's ownership.

Shared-core development continued after these builds. Device acceptance binds the 160 captured source files and their artifact hashes; it does not establish that later core edits were installed or run. The October 23 serial host compatibility run passed all 116 tests while five shared files changed during its observation window. That run is useful integration evidence, not a frozen-source device result.

Build logs remain in TEMP: `qfli-json-ohos-x64-final-harness-build.log` (exit `0`, 16.085 seconds, 42 tasks) and `qfli-json-ohos-x64-normal-build.log` (exit `0`, 18.355 seconds, 42 tasks). During handoff the emulator had stopped: `hdc` reported TCP Offline, port 5555 had no listener, and the official emulator list reported the existing `Mate 90 Pro` API 26 instance as not running. Authorized recovery used `Emulator.exe -start "Mate 90 Pro" -bootMode snapshot -noWindow`, preserving data. The same target reconnected and both update installs then succeeded. No data reset, uninstall, log clearing, device recreation or signing-profile mutation was performed.

## Ordinary UI acceptance — October 22–23

`ohos-ui-acceptance.json` records the observed checks, screenshot hashes and limits. These checks used the normal installed app, independently of the verification-only entry point:

| Action | Observed result / screenshot |
| --- | --- |
| Open Tools | Direct JSON cards appear in the existing tab; `ohos-ui-tools.png` |
| Open Pointer card and execute its default | `/items/0/id` returns `1`, copy-result action enabled; `ohos-ui-pointer.png` |
| Open examples and import example 001 | JSON badge/filter visible; normal import dialog creates a task-owned project and opens `src/data.json` |
| Open main editor | JSON syntax colors and clean local inspection; `ohos-ui-editor.png` |
| Inspect malformed source and click its Problems entry | Red wavy underline, `对象键后缺少冒号 :`, `src/data.json:1:6 · JSON json.syntax`; `ohos-ui-problems.png` captures the error state before navigation. Clicking was separately observed to select the offending character. |
| Replace all source with `{}` through editor selection/input | Unsaved marker remains, wave and Problems entry clear; disk still contains the malformed fixture; `ohos-ui-unsaved-correction.png` |
| Open 编辑与预览 and validate | Output records `校验通过：1 个节点`; `ohos-ui-output.png` |
| Search the original sample's structure for `/values/1` | Shows integer `3`; clicking navigates to line 4, column 17; `ohos-ui-structure.png`, `ohos-ui-structure-navigation.png` |
| Expand `src`, close and reopen the sidebar | Child `data.json` remains visible; `ohos-ui-tree-reopened.png` |
| Force-stop/start this task's app, reopen project and sidebar | `src` remains expanded; `ohos-ui-tree-restarted.png` |

The malformed fixture `{"a" true}\n` was seeded through `hdc` in the newly imported task-owned project; this is not claimed as UI typing. The unsaved correction was entered through the actual editor UI. After the correction check, the original sample was restored exactly: 123 bytes, SHA-256 `70739cda8c82069b2d496ac68ecff4f2c40ee67705e5c9e6a69aeba4e9a6b0ac`. It was reopened with no diagnostics, and a final download after the process-restart check matched the saved original byte for byte. No unrelated project data was discarded.

The main editor deliberately uses the document-tool action for JSON. UI validation/output was exercised through 编辑与预览; the harness separately exercised real `RunnerService` files. Multi-root restoration has the 27 host regression checks; this UI pass covers one root and does not imply multi-root device gestures. All sixteen worker defaults passed in the harness, while the ordinary UI tool interaction here covers Pointer. Release signing and physical ARM64 remain independent gates.

On October 23 the emulator was again confirmed stopped and recovered from the same snapshot with `-noWindow`; no data reset was used. A separately connected physical-device address was not targeted. UI probes were changed to use unique remote/local layout paths and reject HDC failure text, preventing an offline target from being mistaken for a cached layout. A swipe reached the OS recent-apps screen; the existing app was brought back with `aa start`, and this was not attributed to an application failure.

## Historical investigation and earlier gates

The sections below preserve the sequence of initial source inspection, failed signing invocation and initial harness. Earlier statements that no device/build/install was available describe those earlier points in time; the current verified results above supersede those gates.

## Current tools and configuration

- `flutter --version` succeeds using `D:/ProgramFiles/flutter_ohos/bin/flutter.bat`: Flutter `3.27.5-ohos-1.0.1`, framework `12587c79e8`, engine `42d3d75a56`, Dart `3.11.5`, DevTools `2.54.1`.
- `flutter build hap --help` succeeds. This installed command supports `--debug`, `--no-pub`, `--no-codesign`, and target platforms `ohos-arm64`, `ohos-arm`, `ohos-x64`.
- `hdc` resolves to `D:/ProgramFiles/Huawei/OpenHarmony/Sdk/23/toolchains/hdc.exe`. Initial `hdc list targets` returned `[Empty]`; a later recheck returned `127.0.0.1:5555`. Read-only target queries confirmed API `26`, `x86_64`, and software `emulator 7.0.0.107(SP8DEVC00E999R4P11)`. An authorized initial harness was subsequently installed and executed; see its separate evidence below.
- `ohos/local.properties` points to the same Flutter checkout and `D:/ProgramFiles/Huawei/DevEco Studio/sdk`.
- `sdk/default/sdk-pkg.json` and `default/openharmony/ets/oh-uni-package.json` report HarmonyOS API `26`, version `26.0.0.105`. Separately installed OpenHarmony SDK directories include `20` and `23`.
- Current product configuration requests compatible SDK `5.1.0(18)`, target SDK `6.1.1(24)`, `runtimeOS: HarmonyOS`. Compatibility with the installed SDK remains a build question; matching files alone is not proof of a successful build.
- `JAVA_HOME` currently points to JDK 25. The inspected configuration contains no task-owned Java override. Record the Java selected by Hvigor in the eventual build log instead of guessing.
- All three configured signing-material paths (`.cer`, `.p7b`, `.p12` under the user's `.ohos/config`) returned `False` from `Test-Path -LiteralPath`. A signed installable HAP is blocked by missing signing material. Do not copy secrets into research or change the user's signing configuration to conceal this gate.
- The current app bundle name is `com.azurekiln.qfli.json`. No existing `.hap` artifact was found by `rg --files build ohos -g '*.hap'` at inspection time.

## Native and offline boundaries

The generated OHOS plugin registrant installs only `path_provider_ohos`. JSON parsing and preview need no native executable compiler or interpreter. The native entry also provides local clipboard/file-picker/share integration. File selection goes through the explicit `PickerBridge`, since the dependency graph has no OHOS file-selector plugin.

At the initial snapshot, the release manifest requested `ohos.permission.INTERNET`. `EntryAbility.ets` also registered Huawei account authentication, navigated to an online agreement WebView, and launched arbitrary external URI abilities. These are inconsistent with the JSON product's offline boundary even though shared Flutter UI is profile-gated. The task removes INTERNET from the previously clean `ohos/entry/src/main/module.json5` and adds a host-policy regression test.

`EntryAbility.ets`, `main_pages.json`, signing configuration and the new `AgreementReader.ets` were already user-modified before this task. The research worker must not overwrite them. Safe root integration is narrowly scoped: remove the Huawei account import/channel/handler; deny `openAgreement` and `openUrl` with an offline error; remove their now-unused router/Want imports; preserve local sharing, picker calls, background handling and the user's agreement-reader source. Keeping an unreachable agreement source is not evidence that it is offered as an offline feature.

`test/json_offline_host_test.dart` checks the product's offline profile, Android/OHOS release permission boundary and active OHOS entry registration/routing. The permission test passed. A second test wraps JSON inspection and schema validation in `HttpOverrides.runZoned`, denies creation of an HTTP client, exercises inert URL data and local schema references, and rejects HTTPS/HTTP/protocol-relative/file/relative external references. It passed with zero HTTP clients created. The native source check is a source-level policy regression check. These tests do not inspect packets, prove zero network behavior throughout all shared code, or replace target-device execution.

## Existing JSON path and gaps

- `lib/main.dart` initially set `runtimeKind: json-preview`, `runtimeStatus: available`, and a null runner. The initial test explicitly expected `RunnerService.runProject` on `.json` to return the generic unrecognized-file hint. Therefore a runtime availability flag was not evidence of working Run validation.
- Shared `lib/editor/editor_page.dart` already had a separate content-tool action: it passes the current JSON editing buffer to `JsonToolPage` and applies changes back to the editor. It did not route the editor Run action through JSON parsing.
- `JsonDocumentService.analyze` calls Dart `jsonDecode`/`JsonEncoder` locally. The old structure widget displays types rather than scalar values, and its array branch does not recurse into array elements. The product-owned document-tool hook can supply the requested richer preview without changing every sibling's UI.
- The old `structured_content_test.dart` covers only one valid and one invalid document. Core retained-editor/tools tests prove routes and formatting in a desktop Flutter test host. They do not enumerate every shipped example or execute them on OHOS.

## Verification sequence

1. Run product `flutter --suppress-analytics analyze --no-pub` and `flutter --suppress-analytics test --no-pub`. Run the focused shared-core tests required by actual core changes. Every example, tutorial snippet and exercise answer must be checked through the shipped JSON service.
2. Inspect `git diff` before a build. The Flutter OHOS builder regenerates/copies Flutter assets and build metadata, so generated changes must be reviewed and excluded from the user's original edits where appropriate.
3. Build the normal offline app using the installed command: `flutter --suppress-analytics build hap --debug --no-pub --no-codesign`. Keep the full log. No signed-build claim is justified by an unsigned result.
4. Inspect the actual HAP archive path printed by the command, bundled product assets and compiled permissions. If required package caches or SDK components are absent, record the exact compiler/package error; do not initiate network installation to make an offline product test pass.
5. Re-run `hdc list targets` before attempting execution. A live target is required; release or physical-device signing must be verified separately. This emulator accepted the unsigned HAP. With a target available, execute the product's offline catalog-validation entry and capture catalog counts, failures and exit status. Test JSON document editing/diagnostic navigation on that target.
6. A compile pass proves that the current OHOS build accepts the code/assets. It does not prove sample execution, UI behavior, performance, or any C/C++, Python, Java, Dart, Rust, Go, Lua, Web, Markdown or SQL sibling runtime. Those remain independently required family gates.

## Historical pending gates, superseded by the final results above

- An x64 API 26 emulator is attached and the initial harness ran successfully. Final execution still requires rebuilding after the later numeric/resource-boundary fixes; initial success does not cover those later sources.
- Missing signing material: no signed artifact or physical-device installation is proven. This emulator accepted the unsigned HAP.
- The root integrated the active native offline boundary while preserving user-owned agreement code. Its full host-policy tests still need to be included in the final app test run.

## Authorized x64 build attempt and archive inspection

The root subsequently authorized a single x64 debug build. Executed:

```text
flutter --suppress-analytics build hap --debug --no-pub --no-codesign --target-platform ohos-x64
```

The command ended with exit `1`: `:entry:default@SignHap`, Hvigor error `00303107`, invalid `storeFile` because the configured `.p12` is absent. This Flutter branch's `--no-codesign` did not skip Hvigor's configured signing task. The user's `ohos/build-profile.json5` was not changed. Full log: `D:/AppData/Local/Temp/qfli-json-ohos-x64-build.log`; Flutter also generated `flutter_02.log` (ignored build output). The build completed Dart/ArkTS/package stages sufficiently to emit the unsigned archive, but the overall command must be reported as failed at signing.

An unsigned archive was emitted at `ohos/entry/build/default/outputs/default/entry-default-unsigned.hap`, size `123782731` bytes, SHA-256 `4f735c022328454ce5a7b4ef3da68a2aa6c98ff6f4769a17ab3a459538343d42`. Python `zipfile` inspection found 39 entries and proved:

- Compiled `module.json` identifies `com.azurekiln.qfli.json` and requests only `ohos.permission.READ_PASTEBOARD`; it does not request INTERNET.
- `libs/x86_64/libflutter.so` and the debug kernel are present.
- Product `catalog_audit.json`, `examples.json` and `tutorials.json` are bundled and byte-for-byte equal to the current source assets at inspection time. Source/package SHA-256 respectively: `6442c06e699d130ee7eec32d2fb80d1226d6810b3537ade9a1ba3972ad92bb4f`, `20a555e3f0671dfc0cafd09adb4895ba57ace25babdca332dd6bc59e33f33675`, `8cb0b9e82ba0185d6cf0c988458f7e16ac0ea3c45fea1c541ce22c50c7869ca2`.

The build tool automatically ran `ohpm install` and fetched `@ohos/hypium` `1.0.6` from its registry despite Flutter `--no-pub`. Thus this is a build of an offline app, not evidence of an entirely disconnected build process. No separate package-install command or network feature was added to the app. Future builds that require disconnected tooling must account for Hvigor/ohpm caches separately.

No install was attempted. A read-only `bm dump -n com.azurekiln.qfli.json` returned a bundle-information error; this is insufficient to prove whether an earlier product install exists. Root will arrange the separate validation harness before installation. If a clean overall unsigned command is required, prefer a temporary isolated build configuration or build copy with signing removed only in that copy. Do not rewrite or temporarily replace the user's active signing profile.

Huawei's AppGallery Connect release FAQ search result states that signing is not required when an emulator is used to install a HAP. Primary source: `https://developer.huawei.com/consumer/fr/doc/app/agc-help-releasefaq-0000001110342644`. This is a possible path for the isolated unsigned harness; it is not proof that this particular API 26 emulator accepts it. The FAQ page itself is dynamically rendered and the text was available in the official search excerpt. Wait for root authorization and verify the actual install response instead of treating the documentation as an install result.

## Native unsigned control and first installed harness

The installed Flutter source explains the earlier behavior: `packages/flutter_tools/lib/src/ohos/hvigor.dart` invokes `assembleHap` before consulting `shouldCodesign`; `_appendCommands` does not propagate it to Hvigor. The flag only gates the later signed-info check and output-file selection. It cannot disable the existing native signing task in this version.

The installed Hvigor `res/hvigor-config-schema.json` declares `properties.enableSignTask` as boolean. `src/common/util/hvigor-config-loader.js` accepts the CLI override `-c properties.enableSignTask=false`; a standalone in-memory parser check returned `enableSignTask=false`, `type=boolean`. OHOS plugin `src/tasks/sign-hap.js` exits its signing action when that property is false. `PackageHap` is a separate registered task and the dependency direction is SignHap -> PackageHap, but direct internal-task CLI invocation was not needed or claimed as tested. The supported aggregate task plus the documented property sufficed without touching the user's signing configuration.

After the root's explicit build/install authorization, executed from the product's `ohos` directory:

```powershell
& 'D:\ProgramFiles\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat' --mode module -p module=entry@default -p product=default -p buildMode=debug -p FLUTTER_TARGET=lib/main.dart -p TARGET_PLATFORM=ohos-x64 -p DART_DEFINES=UUZMSV9WRVJJRllfQ0FUQUxPRz10cnVl -p TRACK_WIDGET_CREATION=true -p TREE_SHAKE_ICONS=false -p PACKAGE_CONFIG=D:/MyNewProjects/qfli_json/.dart_tool/package_config.json -c properties.enableSignTask=false --no-daemon --no-parallel assembleHap
```

`DART_DEFINES` is base64 for `QFLI_VERIFY_CATALOG=true`. Result: exit `0`, `BUILD SUCCESSFUL in 20 s 615 ms`, 42 tasks (28 executed, 14 up-to-date). The configured SignHap task returned in 1 ms with signing disabled. Log: `D:/AppData/Local/Temp/qfli-json-ohos-x64-harness-build.log`. The existing signing profile was not edited.

This initial harness HAP was `123817355` bytes, SHA-256 `f6a862ac2cb9ff6123c94b4834d6999ec8f11bbde7abefc26c5d619ec8e36c20`. Its kernel timestamp was `2026-10-22T19:30:46.1342621+08:00`; HAP timestamp was `2026-10-22T19:30:54.6589259+08:00`. Kernel SHA-256 was `1dbd803616b2a0c85289233473e9cc97168d5edb176ef1a974a9d32540a3d01f`. Archive inspection again found only READ_PASTEBOARD in compiled permissions.

Installed with `hdc -t 127.0.0.1:5555 install <unsigned-hap>`: `install bundle successfully`. Started with `hdc -t 127.0.0.1:5555 shell aa start -a EntryAbility -b com.azurekiln.qfli.json`: `start ability successfully`. The first actual target result at `2026-10-22 19:37:33` was:

```json
{"passed":true,"examples":340,"runnerPasses":340,"tutorials":340,"lessons":340,"exerciseAnswers":440,"fixtures":340,"semanticOperations":10,"tools":16,"platform":"ohos","failures":[]}
```

Committed-evidence candidates in this task directory:

- `research/ohos-harness-initial.log`: raw filtered hilog progress and result marker from the actual app process.
- `research/ohos-harness-initial-result.json`: the 183-byte report exported from the app sandbox, containing only counts/platform/result.

These are initial harness evidence, not final-source acceptance. `json_workbench.dart` changed at `19:35:40` and `json_schema.dart` at `19:37:39`, after the built kernel. The root is also changing tool execution/resource limits. A new build and device run must include those corrections before any final package claim.

## UI verification readiness and switching modes

`uitest help` confirms support for `screenCap`, `dumpLayout -b <bundleName>`, and `uiInput` click/swipe/keyEvent/inputText/text. Both `screenCap` and bundle-filtered `dumpLayout` were exercised successfully on the installed harness. The screenshot visibly showed the passed result; the layout exposed the Flutter header and result TextInput with screen bounds. Initial screenshot/layout are in TEMP, not the source tree.

The harness flag is a compile-time Dart boolean. An `aa start` argument cannot switch the already-built harness into the ordinary app. To test ordinary UI, build without `QFLI_VERIFY_CATALOG=true`, force-stop this task's installed bundle, update it using `hdc install -r <normal-unsigned-hap>`, and start EntryAbility. Export the verification report before switching. No earlier ordinary product installation existed according to the root's bundle-manager check, so the current installed bundle/data belong to this task's harness. Do not uninstall or reset data as part of the normal-mode switch.
