# Native offline follow-up — 2026-10-23

Captured UTC: 2026-10-23T02:54:52.864460+00:00

This targeted follow-up supersedes the open **source dispositions** in the earlier family audit for the paths below. It is a read-only source review, not a test/build/device pass. The checker was interrupted twice by account concurrency; the root completed the targeted reads and recorded these hashes. No sibling/core source was edited. JSON/Lua retain their earlier independently scoped evidence and were not re-audited here.

## Source-confirmed changes

| Product | Current native method behavior | Remaining boundary |
| --- | --- | --- |
| Go | `EntryAbility.ets:47` refuses openAgreement/openUrl before reading arguments; no Huawei login handler | INTERNET remains for authored Go runtime capabilities. No automatic network behavior is asserted. |
| SQL | `:65`, `:76`, `:113` refuse remote agreement/browser/login before arguments; AccountKit/client_id/INTERNET removed | Local picker/share/startup and Unix-socket MySQL remain. New HAP/device proof pending. |
| Note | `:75` returns OFFLINE_ONLY before retained agreement/browser draft branches; `:136` rejects login | Retained unreachable route text and client metadata are not reachable network calls. FILE_ACCESS_PERSIST supports local documents. |
| Java | `:50` rejects remote agreement/browser and `:94` rejects login | INTERNET/client metadata remain; preserve the actual local JDWP requirement. Current handlers do not invoke Huawei authentication. |
| Web | `:61` accepts only policy-approved HTTP(S) literal loopback preview URLs | `OfflinePreviewPolicy.ets:2` requires explicit 1–65535 port and literal 127.0.0.1/[::1], rejects whitespace/control/backslash, hostnames, userinfo and external hosts. INTERNET supports local preview. |
| Dart | `:55` rejects openUrl/openAgreement; no account channel | Manifest requests only clipboard permission. New installed-package verification pending. |
| Python | Literal `OFFLINE_ONLY=true` at `:21`; `:60` rejects agreement/browser before old draft branches; `:134` rejects login before AccountKit code | INTERNET removed. Dead route/account text remains, guarded. FFI/module/debug HAP drift remains a separate open gate. |
| Rust | `:55` rejects agreement/browser; no account channel | No INTERNET request (manifest comment mentioning INTERNET is not a permission). New installed-package verification pending. |
| C/C++ | **Still open:** `:67` routes remote HTTPS agreements, `:91` launches arbitrary URI, login invokes AccountKit | Native implementation remains the C owner's repair scope. Normal offline UI gating is separate from a native boundary; automatic network activity is not established here. |

Shared core `ApiClient._requireOnline` now checks the current profile's `offlineOnly` before `_send` constructs URI/transport request, and before `terminalEvents` creates its stream transport. The source test `test/api_client_offline_test.dart` exists; this review did not execute it. A source guard is not evidence for a final composed-core package.

Adjacent editor findings are also source-fixed pending their owners' tests: Java `analyze` now calls `_requestIssue` before javac and rejects a non-Java active document; its test `java_diagnostics_test.dart:63` covers unsupported files. Core `themeFor(ownerType:)` now selects C++ for a cpp/c++ owner's `.h`, preserves custom TextMate precedence, and EditorPage passes `open.projectType`. C's focus diagnostic additionally guards disabled/unmounted/leaving state and `focusContext.mounted` before reading a widget (coordination 282/284). None is called a test pass here.

## Owner-reported execution, separately scoped

- SQL 258 reports committed/pushed `6999b0d`, SDK-transpiled actual-handler 303 assertions, seven policy mutation controls and seven inspector cases. JSON did not rerun these commands.
- Note 267 reports committed `82092c1` and three actual-source SDK-transpiled host groups. These mock platform APIs; no new installed OHOS pass.
- Web 261/269 reports actual-handler 13/13, 93 URL vectors and 116 dispatches. Actual ArkTS/HAP/device remains pending.
- Java 266 reports actual native-handler 4/4 plus baseline negative control; Flutter/JDK helper final verification remains queued.
- Python 289 reports committed/pushed `bd789c3a6feb47769b0de8b6ae077ba2bf3f256b`, staged-source actual-handler pass and failing baseline/guard-disabled controls. Current FFI/debug/content package remains open.
- Go 252 reports target audit source added; no new rebuilt HAP/device result. Dart/Rust refusals above are only source-confirmed by this review.

Historic installed artifacts remain valid only for their recorded bytes. No owner-reported host result upgrades those artifacts to current source. All-product runtime and final shared-core gates remain active.

## Repository checkpoint and selected permissions

HEAD names do not freeze dirty bytes. The exact selected source hashes follow this table; statuses describe only the reviewed entry/manifest paths at capture.

| Product | HEAD | Selected path status | Requested permissions |
| --- | --- | --- | --- |
| go | `82e17af4233e3aa2c6dd8eac2cb3f808f0f20a4f` | dirty | ohos.permission.INTERNET, ohos.permission.READ_PASTEBOARD |
| sql | `6999b0d2171318129fcd64a82ae9e493d13609e9` | dirty | ohos.permission.READ_PASTEBOARD |
| note | `82092c100977cf6e15d1c268010e2bdd6509a39e` | dirty | ohos.permission.FILE_ACCESS_PERSIST, ohos.permission.READ_PASTEBOARD |
| java | `4d5d2a308a8a25d7bf82b32610a496c6dd5e2232` | dirty | ohos.permission.INTERNET, ohos.permission.READ_PASTEBOARD |
| web | `e0f81a56230ec27890b67eb9ac0c1df71a805c71` | dirty | ohos.permission.INTERNET, ohos.permission.READ_PASTEBOARD |
| c | `2cccdbeb85ea5994898fd75a82aa756c07786324` | dirty | ohos.permission.INTERNET, ohos.permission.READ_PASTEBOARD |
| dart | `b90f4b93cc5c3f1cea3d3434ecbe61006a8d81ae` | dirty | ohos.permission.READ_PASTEBOARD |
| python | `bd789c3a6feb47769b0de8b6ae077ba2bf3f256b` | dirty | ohos.permission.READ_PASTEBOARD |
| rust | `78fb7b149c140e589177bd5d7ac4f91231011a70` | dirty | ohos.permission.READ_PASTEBOARD |

## Exact selected file SHA256

- `../qfli_go/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `2522c581738465fdcf2911f01ecda0c54661728c7b866d9ecb8853b5b1529bd4`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_go/ohos/entry/src/main/module.json5`
  - SHA256 `0e574054df7c81d1de9f24a75caf1fbb47ef93c9beb23b71ddd041b52858f89a`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_sql/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `cf6929e44a7450dd9add82f14a2f1ab8012d65fcfcb58b435d5619d92764c3a3`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_sql/ohos/entry/src/main/module.json5`
  - SHA256 `31d36189aa4fff98c1aeabc120dc1b339a7e868277002fc658c3d2cf3a8e0e63`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_note/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `6218ca67837401c314ba6e17171aa73c70d4fc84816f8523fd6dfd7fbfff63e9`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_note/ohos/entry/src/main/module.json5`
  - SHA256 `4623058d555809b170cc863caee81b836760fdc666443965bc40c95f6dfa4eb7`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_java/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `aacb08bac41de14d7c45ba02fa72282f1c1b826712e3e41ff216b28431226c3a`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_java/ohos/entry/src/main/module.json5`
  - SHA256 `923dbd876fb413a989049ffa142d80e019dbb48984dc4db279e5dc884aa58eaf`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_web/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `9fb0ed1a4353fda08b46f43d1ecaf92770d0e2661c5f6b66e2563919b27c5938`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_web/ohos/entry/src/main/module.json5`
  - SHA256 `6156a6f4a2baf3558df41b6fa8c7eb1354562e01d22304bf93659ed95fd8c356`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets`
- `../qfli_c/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `b6a341683b67f08f21f7a3e4cf58bc93bde784033cc97acc49a1160cda819645`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_c/ohos/entry/src/main/module.json5`
  - SHA256 `de2daf05eae7dc269a9c56978c8d7e5c0d6c4e1acd3c5d23ad3069d3af03bc24`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_dart/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `aff14006766b80337a741f1e62e4d3099b017bb2d7aeea7fdf6ceac9839fcb56`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_dart/ohos/entry/src/main/module.json5`
  - SHA256 `397821c4deb10dfca08e8d2f76487a567d78f34cd470c54f3a62908626b46c67`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_python/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `05357ad9ae83e1839542d10f5bcb36902ff2a47fd4c02970833e403d7751844c`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_python/ohos/entry/src/main/module.json5`
  - SHA256 `397821c4deb10dfca08e8d2f76487a567d78f34cd470c54f3a62908626b46c67`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_rust/ohos/entry/src/main/ets/entryability/EntryAbility.ets`
  - SHA256 `7c866b7844360173eca6c3f2281b12e4ab4b0295dc9e2ad164861b6b3ea62dc0`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_rust/ohos/entry/src/main/module.json5`
  - SHA256 `8341379d03db89db63fbaccd337cf377b413b76513fc21099a14b19d1e50c188`
  - `M ohos/entry/src/main/ets/entryability/EntryAbility.ets;  M ohos/entry/src/main/module.json5`
- `../qfli_web/ohos/entry/src/main/ets/entryability/OfflinePreviewPolicy.ets`
  - SHA256 `d0173a6295fdb4a87fd4333b4c60134c55072646102bf907e06b8ec2efc95369`
  - `?? ohos/entry/src/main/ets/entryability/OfflinePreviewPolicy.ets`
- `../qfli_studio_core/lib/services/api_client.dart`
  - SHA256 `14b4cfc1b7dba45b346ff3e88a7596ac52865c80a65e5e380999d58488abaa45`
  - `M lib/services/api_client.dart`
- `../qfli_studio_core/lib/editor/highlight_themes.dart`
  - SHA256 `63d1655d1218faa739dbc44776aa7e8d8e82230223b0c6822822a1cc6f04ba24`
  - `M lib/editor/highlight_themes.dart`
- `../qfli_studio_core/lib/editor/editor_page.dart`
  - SHA256 `9b265620cf1300ab1e6c5f0c14beec87edc0f70ba26b12c9cdb376fe543f2b14`
  - `M lib/editor/editor_page.dart`
- `../qfli_studio_core/test/api_client_offline_test.dart`
  - SHA256 `b999151f470d46dbfef9d910264d1f2bf1be1628ecdbf5393c6dfde09772fed1`
  - `?? test/api_client_offline_test.dart`
- `../qfli_java/lib/java_diagnostics.dart`
  - SHA256 `92f188218669370b2d4bc8e842906897a504975bf0e77728119fa43de9481875`
  - `M lib/java_diagnostics.dart`
- `../qfli_java/test/java_diagnostics_test.dart`
  - SHA256 `04792c6b2e1aec436f0835aa5f5503c7dcda5440587377b6703d7bcfe6b77879`
  - `M test/java_diagnostics_test.dart`
