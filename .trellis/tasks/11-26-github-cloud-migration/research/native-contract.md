# Exact-pin native contract for JSON cloud CI

Date: 2026-11-26. Scope: source inspection and implementation only.
No local dependency resolution, binary download, analyzer, lint, test or build ran.
No Git operation changed a ref, index or commit in this audit.
The implementation changes only the five authorized native-contract files and this report.

## Verdict

The old Git pin is not missing its native payload. It tracks the native binaries.
The approved transition uses those exact Git blobs as historical inputs.
It does not replace them with the newer native release.
It does not claim that the upstream release is immutable.

The consumer implementation is ready for its first GitHub execution.
Its parser and package checks have not yet run locally or in this audit's cloud window.
A missing or invalid contract fails closed. No fallback downloads exist.
Six complete installers, signing and installed-device acceptance remain separate gates.

## Fixed primary sources

- Core commit: `476a30acee21dc486ee2849dd8064a7be665e4d5`.
- Core Git tree: `356cc7e32077f58f7a8a0448910f0de988ba90e5`.
- Core dependency declaration:
  https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/pubspec.yaml
- Core lock:
  https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/pubspec.lock
- Runtime selection:
  https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/git/git_backend.dart
- Native initialization:
  https://github.com/azurekiln2333/qflistudio-core/blob/476a30acee21dc486ee2849dd8064a7be665e4d5/lib/git/native_git_backend.dart
- Plugin package and declared platforms:
  https://github.com/azurekiln2333/qflistudio-git/blob/697291a27818612ae9dc53d83d4f99fa5887908e/pubspec.yaml
- Native lock:
  https://github.com/azurekiln2333/qflistudio-git/blob/697291a27818612ae9dc53d83d4f99fa5887908e/native_libs.lock.json
- Native ABI contract:
  https://github.com/azurekiln2333/qflistudio-git/blob/697291a27818612ae9dc53d83d4f99fa5887908e/tool/ci/native_contract.json
- Loader:
  https://github.com/azurekiln2333/qflistudio-git/blob/697291a27818612ae9dc53d83d4f99fa5887908e/lib/src/library.dart
- iOS embedding:
  https://github.com/azurekiln2333/qflistudio-git/blob/697291a27818612ae9dc53d83d4f99fa5887908e/ios/qfli_git.podspec
- Android integration:
  https://github.com/azurekiln2333/qflistudio-git/blob/697291a27818612ae9dc53d83d4f99fa5887908e/android/build.gradle
- Native link closure:
  https://github.com/azurekiln2333/qflistudio-git/blob/697291a27818612ae9dc53d83d4f99fa5887908e/native/CMakeLists.txt

The main agent explicitly authorized reading these fixed Git plugin sources through `gh api`.
No local Git owner repository or other owner's worktree was read.

## Historical identities

| Identity | Exact value |
| --- | --- |
| Resolved plugin commit | `697291a27818612ae9dc53d83d4f99fa5887908e` |
| Native lock Git blob | `1a7428add5902ce7d4ae48106bdf24a732aae48c` |
| Native lock bytes | `11314` |
| Native lock SHA-256 | `0aaa998ab74802473ad0186b0a17f8b6d9e8302a44de6d072af6bf3d3de31a66` |
| Lock schema / API | `2` / `3` |
| ABI contract SHA-256 | `d12d803c7ec7fc6d6ccb3d3abbb705b9748452da1873de86a699e37459c4486a` |
| Native source commit | `194a6c9dd70873a472e441b67875766541572372` |
| Historical producer run | `44863517943` |
| Historical release | `null` |
| CA Git blob | `4a38c72a9e1a35c4c24459989b18fd455be1b78e` |

The historical run number is provenance from the pinned lock.
This audit does not infer its attempt number or asset identifiers.
The main agent reported that `native-v0.1.1` uses newer source `85406ecf` and is mutable.
That release must not substitute for these inputs.

## Exact native payload

The lock has ten files. All ten are checked on every cloud prepare.
All ten enter the retained native-input archive, including the simulator slice.

| Platform / ABI | Path below the pinned plugin | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Android arm64-v8a | `android/src/main/jniLibs/arm64-v8a/libqfli_git.so` | 1819248 | `5bd07ec1379fbb6b7243aaba706055a96c0069c147a35bb7a529787cde94d332` |
| Android armeabi-v7a | `android/src/main/jniLibs/armeabi-v7a/libqfli_git.so` | 1333740 | `90a47f12c14753cb82c63be8722267ef062608cf77562212c3ea5ee390620d0b` |
| Android x86_64 | `android/src/main/jniLibs/x86_64/libqfli_git.so` | 1906112 | `b745270b1c44555cad7a3c5349884a4883ea13379baa1d246878f5bbfb048bea` |
| iOS container | `ios/Frameworks/qfli_git.xcframework/Info.plist` | 1190 | `1ab0cc3f51d692287535eb8af984016cd05e36b0701b703cad887289a3ec0e33` |
| iOS device plist | `ios/Frameworks/qfli_git.xcframework/ios-arm64/qfli_git.framework/Info.plist` | 715 | `21885d61a5e496c26991275ae8b18d835e0ae457797420bee3c6dc76ad0678a8` |
| iOS device arm64 | `ios/Frameworks/qfli_git.xcframework/ios-arm64/qfli_git.framework/qfli_git` | 1587768 | `d702e53b166d357f93009e33add37a99b0d0569b085f167a64fa5ca73addc9b8` |
| iOS simulator plist | `ios/Frameworks/qfli_git.xcframework/ios-arm64_x86_64-simulator/qfli_git.framework/Info.plist` | 715 | `21885d61a5e496c26991275ae8b18d835e0ae457797420bee3c6dc76ad0678a8` |
| iOS simulator arm64+x86_64 | `ios/Frameworks/qfli_git.xcframework/ios-arm64_x86_64-simulator/qfli_git.framework/qfli_git` | 3271144 | `117a71810600054aa41ba21fadda7d8af4ffa20ee4056c0666d294fa60db4b3b` |
| OHOS arm64-v8a | `ohos/libs/arm64-v8a/libqfli_git.so` | 2166616 | `59779edca3f721eb397f62f13c681a6f6bb9edf19d3f5addc8b3f07ff19c93d2` |
| OHOS x86_64 | `ohos/libs/x86_64/libqfli_git.so` | 1944568 | `e70e3c72aab2f317da84bfbff4b5fabfed332391a4121225ecfe7c7dc338f6ba` |

The iOS framework is dynamic. The podspec explicitly embeds it.
The earlier static-framework possibility is ruled out for this pin.
The old lock reports an empty architecture list for the thin device framework.
The consumer parses its Mach-O CPU field instead of treating that empty list as proof.

The native build links libgit2 1.9.7, mbedTLS 3.6.8 and bundled zlib statically.
It disables SSH. The CA bundle version is 2026-11-05.
The consumer still checks actual runtime dependencies; source comments alone do not prove closure.
Android integration requires compileSdk 36 and minSdk 24.

## Executable cloud consumer

Files owned by this audit:

- `tool/ci/native_dependencies.py`
- `tool/ci/native-contract.json`
- `tool/ci/native-contract.schema.json`
- `tool/ci/native-contract.template.json`
- This report.

The actual contract is approved for these exact pins.
The template remains blocked and contains no invented asset identities.
No release download mode or `latest` fallback is implemented.
Cloud package resolution supplies the pinned Git checkout and native bytes.

```text
python tool/ci/native_dependencies.py --target PLATFORM --phase prepare
python tool/ci/native_dependencies.py --target PLATFORM --phase verify --package ARCHIVE [--package ARCHIVE ...]
```

Targets: `windows`, `linux`, `macos`, `macos-universal`, `ios`, `android`, `ohos`.
The universal alias uses the `macos` evidence directory.
An optional `--contract PATH` selects a reviewed contract.
A missing, blocked or mismatched contract exits nonzero.
The helper refuses local execution.

### Prepare

1. Require GitHub source, run and attempt identities.
2. Locate core and plugin through `.dart_tool/package_config.json`.
3. Compare both Git HEADs with the approved commits.
4. Require the root lock's exact plugin URL and resolved SHA.
5. Check the lock's raw length, SHA-256 and Git blob.
6. Check ABI contract bytes and all ten native file digests.
7. Parse ELF or Mach-O bytes without loading native code.
8. Check required API 3 exports and actual architecture slices.
9. Check 16 KiB ELF load alignment and runtime dependency closure.
10. Verify the pinned CA and platform integration metadata.
11. Produce a deterministic native-input archive and provenance.

Output: `build/ci-native/PLATFORM/prepare.json`, `native-inputs.tar.gz`, `SHA256SUMS`.
The archive includes the inputs, both contracts, CA, integration metadata and plugin license.
The plugin checkout itself is not modified.
Windows checkout must use LF text bytes for comparisons with Git blobs.

### Verify

Only inspectable runtime archives are accepted through `--package`.
Metadata files do not satisfy package coverage.
Supported archives: ZIP, APK, AAB, IPA, HAP, TAR, TAR.GZ and TGZ.
Opaque EXE, DMG, PKG and DEB wrappers require the packaging owner's payload relation.
The helper does not claim those opaque installers were inspected.
It never extracts untrusted package entries into the worktree.
Unsafe paths, encrypted ZIPs, duplicate paths and unsafe links fail closed.

Each package records its own SHA-256 and native member hashes.
Mobile payloads must contain the expected loader path, CA and native architectures.
Android requires all three ABIs across supplied packages; the AAB requires all three itself.
OHOS currently requires the arm64 device payload. Its x86_64 input remains retained separately.
iOS requires the dynamic device framework and arm64 Runner.
Desktop products require the requested executable architecture coverage.
macOS universal requires both arm64 and x86_64.

Stripping or signing may change non-code metadata.
The consumer then requires identical allocated code/data fingerprints, exports and dependencies.
It records the original and packaged file digests separately.
It does not equate a changed file with byte identity.
An unknown transformation fails rather than weakening the comparison.

Output: `build/ci-native/PLATFORM/verify.json`.
Its successful state is `verified-packaging`, not runtime, signing or installer acceptance.

## Six-platform coverage boundary

| Platform | Git execution backend | Required retained native coverage |
| --- | --- | --- |
| Windows x64 | External Git CLI | Flutter engine/plugin DLLs, native-assets inventory, CMake/link/PDB evidence |
| Linux x64 | External Git CLI | Bundle shared libraries, native-assets inventory, CMake/link/debug evidence |
| macOS universal | External Git CLI | Both executable slices, framework/dylib inventory, dSYM/link evidence |
| iOS arm64 | qfli_git FFI | Embedded dynamic framework, CA, engine/plugins, device dSYM/link evidence |
| Android 3 ABIs | qfli_git FFI | Per-ABI qfli_git, libapp/libflutter and plugin libraries, merged/stripped/debug JNI evidence |
| OHOS arm64 | qfli_git FFI | HAP libraries, CA, HAR/Hvigor/CMake/lock evidence; x86_64 retained as input, not device acceptance |

The plugin declares no desktop FFI platform. No desktop Git library is invented.
Core chooses external Git CLI on desktop. A complete installer must declare and enforce that dependency or bundle a reviewed Git distribution.
This native helper inventories native payloads; it does not prove delivery of an external Git executable.
Core also adds `flutter_secure_storage` and its platform-native packages.
Its Android picker plugin must register and package with the JSON app.
These outputs are additional to qfli_git, not substitutes for its provenance.

## Durable assets and remaining gates

Keep Flutter intermediates and native intermediates as separate short-lived artifacts.
Keep installers for fourteen days.
Publish native input archives to JSON's reviewed durable release or immutable store.
Record actual JSON app/core/plugin/source SHAs, run/attempt, archive and per-file hashes.
Record the actual publication asset ID and digest after creation.
Never invent these future identifiers in the contract.
A short-lived Actions artifact is not durable native storage.
The helper explicitly leaves durable publication pending for the publisher to enforce.

Signatures, notarization, SDK availability, install/start checks and fresh device results remain independent.
Unsigned IPA or HAP is diagnostic evidence, not an installable release.
Desktop tests cannot prove the mobile FFI loader or installed-device behavior.
No existing product's success is borrowed for JSON.

## Coordination

Findings and the agreed CLI were sent to JSON main `w5X:p1` and packaging owner `w5X:p2` through Herdr.
Git owner `w5T:p1` was contacted only through Herdr.
Its delayed reply states that the transition is feasible in principle, not verified acceptance.
It could not send a Herdr response itself, so its reply was read through the Herdr pane.
The main agent independently supplied and authorized the exact fixed lock source.
That fixed lock, not a mutable newer release or an owner assertion, anchors the implementation.
