# JSON cloud validation evidence

All validation commands reported below ran in GitHub Actions. No local build, test, analyzer, lint, dependency resolution, SDK installation or CI-helper execution was used. Evidence retrieval used read-only GitHub API and job-log requests. Times are UTC. This report separates executed checks from skipped jobs.

## Fixed inputs

- Repository: `azurekiln2333/qflistudio-json`.
- Core: `476a30acee21dc486ee2849dd8064a7be665e4d5`. The core owner reaffirmed this baseline on 2026-11-26 and has not supplied a final migration commit.
- Official Flutter: `3.50.0`, commit `ab2912035e160d9cad6306df307576da6128ebdb`.
- OHOS Flutter: `3.41.10-ohos-1.0.1`, commit `adaf911c35c9136a7d18fc424d714c9ec7724e60`.
- Git plugin: `697291a27818612ae9dc53d83d4f99fa5887908e`. Native source: `194a6c9dd70873a472e441b67875766541572372`.

## Runs

| Run | Exact JSON commit | Observed result |
| --- | --- | --- |
| [45825769686](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45825769686) | `df93c17c38782644021b32eda62608c4f69110f8` | Dependency resolution succeeded. Reviewed lock committed in `d4f9713`. |
| [45840615362](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45840615362) | `1e2af3dde41f9f03cea32ccb5ce75559e39f84a3` | Setup failed before native checks. Flutter reported `0.0.0-unknown` because the pinned checkout lacked its local version tag. |
| [45844909967](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45844909967) | `80c3cda93138dc812ddf70fe71a551952b078e52` | Setup and Python compilation succeeded. Chinese README lint found one terminology violation. Native checks and all platform jobs were skipped. |
| [45848522721](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45848522721) | `9113f2ec0380a999b05fe27fd10de33e549fb061` | Setup, Python compilation, Chinese docs and early native preparation succeeded. Analyzer had eight nonfatal informational deprecations. Product suite had 123 passes and one failure. All platform packages were skipped. |
| [45850250184](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45850250184) | `9113f2ec0380a999b05fe27fd10de33e549fb061` | OHOS dependency resolution succeeded with the pinned OHOS SDK, Flutter and core inputs. This was a resolve-lock run, not installer acceptance. |
| [45864418468](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468) | `874f1959ad2f4b75a521952017c3f49591e9b771` | Completed with failure. Verification, Windows and iOS succeeded. OHOS app setup, Linux distribution packaging, Android SDK preparation and macOS Xcode build failed. All-six failed. Release was skipped. |
| [45888643244](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45888643244) | `d01803693d5f4c05299b3d8c748677c0f5aa91f1` | Push, attempt 1, completed with failure. Verification and four platform jobs (Windows, Linux, macOS and iOS) passed. Android and OHOS failed. All-six failed. Release was skipped. |
| [45888770210](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45888770210) | `d01803693d5f4c05299b3d8c748677c0f5aa91f1` | Workflow dispatch with main-reported `publish=true`, attempt 1, completed with failure. Verification and the same four platform jobs passed. Android and OHOS failed. All-six failed. Release was skipped. |

## Confirmed fixes

`80c3cda` fetches only the reviewed Flutter tag and verifies both the peeled tag and HEAD against the immutable source commit. It does not change SDK versions, constraints or dependency locks.

`9113f2e` makes two README terms consistent. No lint baseline or gate was relaxed.

## Native preparation boundary

Run `45848522721`, verify job `140008423402`, executed the early Linux prepare command at `2026-11-26T15:23:55.8811691Z`. It returned `status=prepared` and `build/ci-native/linux/prepare.json`. This exercises the locked native input parser and archive preparation. It does not prove package membership, mobile FFI loading, device installation, signing or durable release publication.

The native helper at this run has Git blob `acdc4793e4e691ccb37899e5cf3dddb7db920a00` and SHA256 `26cd74056e9d9e83b6d944b2786ed01442141a90b77fb7570b78ba54cb44d5fc`. Native package verification did not run.

## Historical test failure

Run `45848522721`, job `140008423402`, failed at `test/json_named_workspace_test.dart:78`, reported by `_until` at line 439. The assertion was: `Opening the JSON Home project did not restore its primary document.` The report appeared at `2026-11-26T15:24:19.575Z`; the suite exited 1 at `15:24:26Z`.

The fixture observed `EditorProblemsBar`, which the fixed core's large-screen editor path does not render. It now passes the core-supported `AppFormFactor.phone` override to the real `QfliApp`. The Home/editor flow and all recovery assertions remain unchanged. Later run `45864418468` reports `+124: All tests passed!` at `2026-11-26T17:05:20.8701859Z`. This later success does not change the failed historical run.

## Run 45864418468: exact-run evidence

The run API identifies `main` commit `874f1959ad2f4b75a521952017c3f49591e9b771`, event `push`, attempt `1`, status `completed` and conclusion `failure`. The run started at `2026-11-26T17:03:46Z`. Its final API update was `2026-11-26T17:12:07Z`.

Evidence was read from these GitHub REST resources on `2026-11-26`:

- `GET /repos/azurekiln2333/qflistudio-json/actions/runs/45864418468`
- `GET /repos/azurekiln2333/qflistudio-json/actions/runs/45864418468/jobs?per_page=100`
- `GET /repos/azurekiln2333/qflistudio-json/actions/runs/45864418468/artifacts?per_page=100`
- Job logs retrieved with `gh run view 45864418468 --repo azurekiln2333/qflistudio-json --job <job-id> --log` or `--log-failed`.

### Verification and per-platform outcomes

| Job | API conclusion | Executed evidence and boundary |
| --- | --- | --- |
| [140063440620: verify](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140063440620) | `success` | Setup, Python syntax, Chinese README lint, early Linux native preparation, analyzer, product tests, content verification and final dependency guard passed. Analyzer retained eight informational deprecations. The suite reported 124 passes. The content check verified three offline JSON curriculum assets. The final guard reported byte-for-byte unchanged manifests and selected lock. |
| [140064304839: Windows](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140064304839) | `success` | Windows prerequisites, native preparation, release build, distribution packaging, runtime/native package verification, lock guard and both transport uploads passed. The native helper reported `verified-packaging` at `2026-11-26T17:09:04.6983373Z`. Signing classification was `unsigned`. No installation or launch was observed. |
| [140064304822: iOS](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140064304822) | `success` | Native preparation, unsigned device build, distribution packaging, runtime/native package verification, lock guard and both transport uploads passed. Flutter reported `build/ios/iphoneos/Runner.app (40.4MB)`. The native helper reported `verified-packaging` at `2026-11-26T17:11:15.7793860Z`. Signing classification was `unsigned-not-installable-without-provisioning`. No device deployment was observed. |
| [140064304581: OHOS](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140064304581) | `failure` | SDK setup succeeded. Step 4, `app-setup`, failed at `2026-11-26T17:08:29.6827038Z` with exit 65. Strict dependency resolution reported that `pubspec.lock` could not satisfy `pubspec.yaml`. The log proposed `clock 1.1.2 (was 1.1.3)`. Native preparation, HAP build, package verification and installer/native uploads were skipped. |
| [140064304814: Linux](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140064304814) | `failure` | Prerequisites, app setup, native preparation and Flutter release build passed. Step 14, distribution containers, failed at `2026-11-26T17:08:20.1062599Z` with `unmapped Linux system runtime dependency: libflutter_linux_gtk.so`, then exit 1. Post-package verification and installer/native uploads were skipped. A successful Flutter build is not a successful Linux package job. |
| [140064304819: Android](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140064304819) | `failure` | App setup succeeded. Step 7, hosted Android SDK preparation, failed at `2026-11-26T17:06:32.2841771Z` with `sdkmanager: command not found`, then exit 127. Native preparation, APK/AAB builds, distribution packaging, verification and installer/native uploads were skipped. |
| [140064304834: macOS](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140064304834) | `failure` | App setup and native preparation passed. Step 11 reached Xcode after Flutter configuration. Xcode reported duplicate `QFLIJson.bundle` outputs at `2026-11-26T17:08:24.6386340Z`, then exited 65. Distribution packaging, post-package verification and installer/native uploads were skipped. |
| [140067648985: all-six](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140067648985) | `failure` | Step 2 received `VERIFY_RESULT=success`, `MATRIX_RESULT=failure` and `OHOS_RESULT=failure`. It exited 1 at `2026-11-26T17:12:04.3694870Z`. Artifact downloads and the twelve-input/checksum gate were skipped. |
| [140067731843: release](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140067731843) | `skipped` | No release steps ran. This push run did not publish an immutable release. |

### macOS failure and prepared correction

The Xcode log's command-line settings include `PRODUCT_NAME = QFLIJson` at `2026-11-26T17:07:53.9976900Z`. That global override also reaches dependency targets. The log identifies these three resource-bundle targets as producers of the same `QFLIJson.bundle` directories, `PrivacyInfo.xcprivacy` and `Info.plist`:

- `file_selector_macos_file_selector_macos`
- `flutter_secure_storage_darwin_flutter_secure_storage_darwin`
- `path_provider_foundation_path_provider_foundation`

`macos/Runner/Configs/AppInfo.xcconfig` already sets `PRODUCT_NAME = QFLIJson` for the app. The prepared workflow correction removes only `PRODUCT_NAME=QFLIJson` from the `xcodebuild` command. It keeps `ARCHS='arm64 x86_64'`, `ONLY_ACTIVE_ARCH=NO`, `CODE_SIGNING_ALLOWED=NO`, `CODE_SIGNING_REQUIRED=NO`, the workspace/scheme/configuration, all pins and every gate unchanged. It preserves the concurrent Android SDK-step correction. This is a source correction, not evidence of a successful macOS rebuild. Only a subsequent GitHub run can verify it.

### Artifact API ledger: transport only

The API returned 17 artifacts bound to run `45864418468` and exact head `874f1959ad2f4b75a521952017c3f49591e9b771`. All had `expired=false` when queried. Sizes and digests below are API-reported transport metadata. The SHA-256 values identify uploaded outer archives. They are not independently rehashed payloads, package-member checksums, native-library identities or signatures. No complete archive, installer or `native-inputs.tar.gz` was downloaded for this report. The separate metadata-only range audit is recorded below.

Only Windows and iOS produced `installer-*` and `native-*` transport sets. These have fourteen-day retention. The other thirteen entries are three-day diagnostics/intermediates, including entries from failed jobs. An intermediate artifact does not prove that its platform package built or passed verification.

| Artifact | ID | Bytes | API digest | Expires UTC |
| --- | --- | ---: | --- | --- |
| `diagnostics-verify` | `15139791839` | 13017 | `sha256:150bbe01755f981fc6a8c3c66f62954d944cfb6cef93164d535e07982242006d` | `2026-11-29T17:05:21Z` |
| `installer-ios-arm64` | `15140077117` | 14423922 | `sha256:5499cb026c30ad4abf4e949daad398e9192e39848cb77d45d6f8ec5cfc65b293` | `2026-12-10T17:11:16Z` |
| `installer-windows-x64` | `15140576315` | 34283709 | `sha256:fe02f82b849685706117c4b3f8079687faba2bcdf7e809f5216ad4762ffe2ae3` | `2026-12-10T17:09:05Z` |
| `intermediate-flutter-android-multiabi` | `15140835475` | 3535 | `sha256:2db0e6f64852b2179f11145d8c7fee643e92b4904ce4275b3665e45b6d198406` | `2026-11-29T17:06:32Z` |
| `intermediate-flutter-ios-arm64` | `15139967309` | 26995087 | `sha256:75d9911198cf9b961513eb17626fd0375ff7e479a4b2cf4cd6beeba039647a01` | `2026-11-29T17:11:43Z` |
| `intermediate-flutter-linux-x64` | `15139906730` | 25073863 | `sha256:b38a9ca6dc8f0408124d50bbf8019ed8a07d1bbeb31c508544a91ca3d9f26ee8` | `2026-11-29T17:08:36Z` |
| `intermediate-flutter-macos-universal` | `15140750843` | 27026 | `sha256:b5d9621fa4ea6e8614e5eff3ce45e740179156ff836c450ab59995765cbc2b63` | `2026-11-29T17:08:26Z` |
| `intermediate-flutter-ohos-arm64` | `15139976804` | 3204 | `sha256:69df92c1e3a633ec8aa2bce6b1fdf6ecb6cf01cfad1927981e63cc826a7b1a36` | `2026-11-29T17:08:29Z` |
| `intermediate-flutter-windows-x64` | `15139029871` | 25498378 | `sha256:e44b21e4e3cdb20e94d37cd3b838885545bd63ad8baddf6c5c51ce577aed4209` | `2026-11-29T17:09:31Z` |
| `intermediate-native-android-multiabi` | `15140760660` | 1046 | `sha256:0d0cea4600a0672acc58bed5f23f92e74c96ea22841e58a099b92e893bffcce0` | `2026-11-29T17:06:34Z` |
| `intermediate-native-ios-arm64` | `15140521857` | 3932095 | `sha256:c54005dced6082d57d24d008d26bf7c9935577a95c8ee766d0bb37d7043374d7` | `2026-11-29T17:11:46Z` |
| `intermediate-native-linux-x64` | `15139822158` | 19547538 | `sha256:480dec7aede92b8eab9528f83bbbca5ec69919dfae68e3aebab756f991f8f8ab` | `2026-11-29T17:08:39Z` |
| `intermediate-native-macos-universal` | `15140995482` | 4878 | `sha256:5df4f88fc601246507887eb42956cec74e0b20d12d6bf559d2828f4f6eaa3fcb` | `2026-11-29T17:08:27Z` |
| `intermediate-native-ohos-arm64` | `15139956759` | 2170 | `sha256:a8f75d5cb75236bfdc9953ba8cfd5abcdcf15cafae581d9d51c807cef0066aad` | `2026-11-29T17:08:30Z` |
| `intermediate-native-windows-x64` | `15139049925` | 22997129 | `sha256:ee1609fce0fc4d8a7f113ca76137092b1ebab7a682047e6df354fa9561844f83` | `2026-11-29T17:09:34Z` |
| `native-ios-arm64` | `15140866148` | 6684139 | `sha256:2b40ea250ca75dc26001ffa85dfbbb896344ad623c7b5a9db4a33364ec9c1a7f` | `2026-12-10T17:11:19Z` |
| `native-windows-x64` | `15140586263` | 6686133 | `sha256:4ea6c3aa45114cf5080af4d95bd5bf1bcc33033198be10c2e488a9a6b6aa1fca` | `2026-12-10T17:09:08Z` |

These records establish short-lived artifact transport availability only. The names `installer-*` and `native-*` do not establish a signed release, device installation, mobile FFI runtime success or durable native storage. The skipped release job supplies no publication evidence.

### Windows/iOS metadata-only native audit

Pi `w5X:p4` inspected HTTPS byte ranges from the two native artifact ZIPs. The audit retrieved the ZIP directory and only `BUILD_INFO.json`, `prepare.json`, `verify.json` and `SHA256SUMS`. It did not fetch installers, `native-inputs.tar.gz` or complete artifact ZIPs. Pi `w5X:p5` read the preserved metadata and independently hashed the six JSON files. All six hashes match their artifact `SHA256SUMS`. This is text/hash inspection, not local helper execution or independent package verification.

Both metadata sets bind attempt `1`, run `45864418468`, app `874f1959ad2f4b75a521952017c3f49591e9b771`, core `476a30acee21dc486ee2849dd8064a7be665e4d5`, plugin `697291a27818612ae9dc53d83d4f99fa5887908e` and native source `194a6c9dd70873a472e441b67875766541572372`. `BUILD_INFO.json` records Flutter `3.50.0` at `ab2912035e160d9cad6306df307576da6128ebdb` and lock SHA256 `ef4832862e8c547b490b7d5b4a0b1209dc15aaeb4063a857e8fdb5d59bf6c254`. Both verification records bind contract SHA256 `5980ba82a5ab98012d8013a9139ce73d1b5bb5b730e9cf88e7d3260fe369617b` and retain historical native producer run `44863517943` as provenance.

| Metadata | Windows SHA256 | iOS SHA256 |
| --- | --- | --- |
| `BUILD_INFO.json` | `4ed972d43e5cca4088ec9fbea0fcebca852644300e1e04888e7862652adecd65` | `304d9c6c889a4e2448a8ca3f415984a06b43815b3d13bcf30ae4c21395d17a46` |
| `prepare.json` | `c21271127298fc771c1ede6aa9aac235430b7402010bbc169b5871e6445374d5` | `54f72707eb07edead6818f749f11005eccee56d90347932dde1dca0b2b28f302` |
| `verify.json` | `e9ab236ed3be8c4fb2b75e8355f7a90dbf4adce05a9644d153f6692d7f1cb647` | `2e6f252f649dc0d63ba16aa3644eeedc2a34748b4fff5122d52ba7c58a8132e1` |

- Windows `verify.json` reports `status=verified-packaging`, `target=windows`, backend `external-git-cli` and an x86_64 package with a CA member. It records `qflistudio-json-windows-x64.zip`, 19,048,330 bytes, SHA256 `7713eca0077f7a5c123b0683e644f3d8aec0c527c01051de22f2d41ef9d9e70e`. Its 14-entry native inventory includes Flutter, plugins and VC runtimes. Empty `qfliGit` matches the external Git backend. It does not prove that external Git is installed or usable.
- iOS `verify.json` reports `status=verified-packaging`, `target=ios`, backend `qfli-git-ffi` and an arm64 package with a CA member. It records `qflistudio-json-ios-arm64-unsigned.ipa`, 14,380,229 bytes, SHA256 `89393244ce74fbbff6dacbb9ed846264487628c4183046cb75555d4577319eb9`. The packaged `qfli_git.framework/qfli_git` is 1,587,768 bytes with SHA256 `d702e53b166d357f93009e33add37a99b0d0569b085f167a64fa5ca73addc9b8`. The cloud verifier records it as `byte-identical` to the reviewed `ios-arm64` input. The inventory also records Flutter and App frameworks.

Both `SHA256SUMS` files declare native-input archive SHA256 `6bd854073673d1207d84d9ae6fa771d79c6f5106fc3dcfdc3ec896a94d5dbbc1`. That archive was not independently fetched or hashed. Package and native-member hashes above are cloud-verifier metadata, not a local reinspection of those binaries. Both records explicitly retain `runtimeValidation=not-run`, `deviceValidation=not-run`, `signingValidation=not-performed`, `installerValidation=not-performed` and `durablePublication=required-separate-release-or-immutable-store`. Metadata consistency does not satisfy any of those gates. The unsigned iOS output is not an installable release.

## d018036: push and publish-requested dispatch results

Read-only run and jobs API requests confirm that both runs used exact app commit `d01803693d5f4c05299b3d8c748677c0f5aa91f1` on `main`, attempt `1`. Both finished with `status=completed` and `conclusion=failure`. Run `45888643244` has event `push`, created at `2026-11-26T20:07:01Z` and last updated at `2026-11-26T20:15:40Z`. Run `45888770210` has event `workflow_dispatch`, created at `2026-11-26T20:08:00Z` and last updated at `2026-11-26T20:22:48Z`. Main supplied the latter's dispatch input `publish=true`; the run API identifies the event, not the input value.

| Gate/job | Push 45888643244: job ID / API conclusion | Dispatch 45888770210: job ID / API conclusion |
| --- | --- | --- |
| Verification | `140145541002` / `success` | `140149130942` / `success` |
| Windows | `140146185306` / `success` | `140149745156` / `success` |
| Linux | `140146185335` / `success` | `140149745184` / `success` |
| macOS | `140146185337` / `success` | `140149745161` / `success` |
| iOS | `140146185537` / `success` | `140149745188` / `success` |
| Android | `140146185432` / `failure` | `140149745207` / `failure` |
| OHOS | `140146185215` / `failure` | `140149745141` / `failure` |
| All-six | `140149059754` / `failure` | `140151989392` / `failure` |
| Immutable release | `140149129056` / `skipped` | `140152038743` / `skipped` |

This is verification plus **four successful platform jobs**, not five platform jobs. Neither run satisfies the all-six gate. The publish-requested dispatch did not publish a release. These are exact-run API conclusions, not device, signing or independent payload acceptance. Later prepared Android/OHOS source corrections are not validated by either run.

### Android fatal wrapper mismatch and prepared correction

Both Android jobs failed at step 13, `Build ABI-explicit Android APKs and universal AAB`, while applying `dev.flutter.flutter-gradle-plugin` from `android/app/build.gradle.kts` line 1. The actual push log at `2026-11-26T20:11:27.6832617Z` reports project Gradle **8.14.0**, below Flutter's minimum **9.3.1**. The dispatch log repeats those exact fatal versions at `2026-11-26T20:20:01.3185934Z`. The first `assembleRelease` failed with exit 1 in both jobs. These are wrapper-version failures after SDK preparation, not the earlier run's missing `sdkmanager` failure. They do not establish any subsequent APK/AAB build or verification result.

Pi `w5X:p2` owns the prepared four-file Android correction:

- `android/gradle/wrapper/gradle-wrapper.properties`: pin the distribution to `gradle-9.3.1-all.zip`, replacing `gradle-8.14-all.zip`.
- `android/settings.gradle.kts`: change AGP `8.11.1` to `9.1.1` and Kotlin Gradle plugin `2.2.20` to `2.4.20`.
- `android/gradle.properties`: add `android.newDsl=false` and `android.builtInKotlin=false` while retaining the Kotlin Gradle plugin.
- `android/app/build.gradle.kts`: replace the legacy `android.kotlinOptions` JVM target block with typed `kotlin.compilerOptions` and retain JVM 17.

This is a prepared source correction, not a GitHub-verified Android result. The log's suggested `--android-skip-build-dependency-validation` bypass is not used. Flutter/core/native pins, SDK/NDK/CMake inputs, ABI targets, signing classifications, strict lock enforcement and native/all-six/release gates are not relaxed by these four files. P2 owns its source and research review. P3 separately owns the OHOS producer correction. Only fresh GitHub execution can validate the integrated changes.

P2's [Android toolchain research](android-toolchain.md) is READY/FROZEN at SHA256 `b33c156c7277229185d1bc129a8f098feb5e07297b24ad58c88944a5f84c8635`. It records both fatal logs, the pinned Flutter source paths/blobs/hashes, fatal minima versus warning thresholds, the selected versions and the four source-file hashes. The prepared Gradle/AGP pair may retain warnings. No warning threshold was turned into a demonstrated fatal failure, and no prepared correction is treated as tested.

The same research records the separate NDK preinstall alignment that main authorized and p2 implemented. The failed runs declared workflow `ANDROID_NDK_VERSION=27.0.12077973`, while the app's `flutter.ndkVersion` requests `28.2.13676358` from pinned Flutter. The current workflow diff changes only that environment value to `28.2.13676358`; its frozen SHA256 is `e868d531ef41790b49ceb71d60fe7e5780b1ac929abe0d521fa122e3930682b5`. The app still uses `ndkVersion = flutter.ndkVersion`. No app override, CMake, signing, ABI or gate change is included. This implemented alignment is separate from the frozen four-file correction and remains cloud-unvalidated. The observed failures precede compiler invocation. Neither those failures nor the source edit proves that sdkmanager installed NDK 28.2 or that any compiler used it. Direct installed/executed-NDK provenance remains unestablished.

## Run 45888643244: blocked OHOS architecture gate

The run API confirms attempt `1` at app commit `d01803693d5f4c05299b3d8c748677c0f5aa91f1`, status `completed`, conclusion `failure`. [OHOS job 140146185215](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45888643244/job/140146185215) passed SDK setup, strict app setup, native preparation and unsigned HAP creation. Step 7, `Verify HAP native members, lock and provenance before staging`, emitted `native-dependency-blocked: unrequested-packaged-native-architecture` at `2026-11-26T20:13:24.8085975Z`. The native verifier exited 2. The enclosing step exited 1. Installer and native publication-input uploads were skipped. In dispatch run `45888770210`, OHOS job `140149745141` also built the unsigned HAP successfully, then failed the same step 7 with `unrequested-packaged-native-architecture` at `2026-11-26T20:21:24.4354258Z`. Its installer/native uploads were likewise skipped. The detailed intermediate-metadata audit below belongs to push run `45888643244`; it is not a payload audit of the dispatch run.

### Directly observed metadata

Pi's metadata-only diagnosis read artifact directories and allowlisted JSON/log ranges. This report reused the preserved text and independently checked its hashes. It fetched no HAP, binary, SDK, installer or complete payload archive. It ran no local CI helper, build, test, analyzer or lint.

| Preserved text | SHA256 |
| --- | --- |
| OHOS `build-facts.json` | `9339f42e794f0df5979556ef21544fd73c1f583be92e508b8a37f0769287fff1` |
| `ohos-toolchain.json` | `d1fd5e965153f144971bd92290ade7f3e9059f88d0f9cffcd094aa226d22045f` |
| Native `INTERMEDIATE_MANIFEST.json` | `adbe908582b5bc1aaa0e7402ff84fbf5dd19bdb520286bcd7430e1ba0c13718f` |
| Blocked OHOS `verify.json` | `398a77333a0cc9f33973b2c3149002638b42517ba8c04ab86c4a5dc7f0862f3c` |

Build facts bind this app commit, core `476a30acee21dc486ee2849dd8064a7be665e4d5` and OHOS Flutter `3.41.10-ohos-1.0.1` at `adaf911c35c9136a7d18fc424d714c9ec7724e60`. They record mode-lock SHA256 `bbb6311daad0206abd04b88984b5511bf1f46327250f4691dc09fd37b3e5b958`, `buildExitCode=0` and `packageBuilt=true`. The cloud-recorded unsigned HAP SHA256 is `b84c1d55978ed1cee824ca2aafc47f0b3d85d3ebc29e23562bf01e6a93a63cbd`. This is a metadata value, not an independent HAP rehash.

The build command requests `ohos-arm64`. The native intermediate manifest lists `libs/default/arm64-v8a/{libapp.so,libflutter.so,libqfli_git.so}` and an additional `libs/default/x86_64/libqfli_git.so`, beneath `ohos/entry/build/default/intermediates/`. It also lists the extra x86_64 library under `stripped_native_libs/default/`. The merged x86_64 input is 1,944,568 bytes with SHA256 `e70e3c72aab2f317da84bfbff4b5fabfed332391a4121225ecfe7c7dc338f6ba`, matching the reviewed upstream OHOS x86_64 input in `prepare.json`. The stripped x86_64 intermediate is 1,944,384 bytes with SHA256 `6f3537a191ba66a610d11054b2a4613d7218f1e16fed01a5ca6f6277af465f5a`.

Build facts record `targetSdkVersion=26.0.0`, `sdkApiVersion=26`, `sdkVersion=26.0.0.105` and Node `24.14.1`. Toolchain facts distinguish tools `26.0.0.821` from installed SDK `26.0.0.105` at API `26`. These identifiers do not indicate toolchain drift. The tool source is a third-party redistribution with `releaseImmutable=false`; committed asset byte counts and SHA256 values are its trust anchor. Pre-build/profile/facts and the helper's ZIP/arm64-engine check do not establish emitted `targetAPIVersion`. No compiled `module.json` or `pack.info` was read.

### Inference and correction boundary

The unchanged native verifier checks each qfli_git member's exact path/ABI and reviewed payload fingerprint before checking the requested output architecture set. The observed `unrequested-packaged-native-architecture` error therefore implies that an extra qfli_git member passed those earlier guards. Together with the intermediate manifest, this supports the diagnosis that the arm64 HAP retained upstream x86_64 qfli_git. The HAP member path `libs/x86_64/libqfli_git.so` is inferred from the executed guards and error. It was not read from a fetched HAP directory.

`tool/ci/native-contract.json` and the verifier's `expected_archs` require exactly `arm64-v8a` for the OHOS output. `EXPECTED_ABIS` also includes x86_64 to check the complete immutable upstream input inventory. That input-coverage requirement grants no permission to emit x86_64 in this HAP. No diagnostic ABI exception or legitimate verifier correction was identified. Keep the guard closed. The producer/HAR merge must exclude unrequested ABIs before HAP creation while preserving the immutable native input archive and arm64 payload fingerprint. That correction requires a fresh GitHub run.

This evidence update changes neither `tool/ci/native_dependencies.py` (SHA256 `26cd74056e9d9e83b6d944b2786ed01442141a90b77fb7570b78ba54cb44d5fc`) nor `tool/ci/native-contract.json` (SHA256 `5980ba82a5ab98012d8013a9139ce73d1b5bb5b730e9cf88e7d3260fe369617b`). The blocked result remains failed package verification. It supplies no runtime, device, signing, installation or release acceptance.

### Diagnostic transport metadata

The artifact API binds both entries below to this run and exact app commit. API digests describe outer transport ZIPs. They were not independently rehashed and do not validate payload binaries or durable publication.

| Artifact | ID | Bytes | API digest | Expires UTC |
| --- | --- | ---: | --- | --- |
| `intermediate-native-ohos-arm64` | `15151275736` | 35979809 | `sha256:eff06a039af08ec09c51f444179b7a3d25b07db13c7f1cd236ac69f99ff65e19` | `2026-11-29T20:13:46Z` |
| `intermediate-flutter-ohos-arm64` | `15151101048` | 31295290 | `sha256:a3b2a88f4bfdfe1918e2179c62ed4734584be54167ebc0c9d91148fec95afbc4` | `2026-11-29T20:13:43Z` |

## Acceptance still pending

- Successful full product verification on the final JSON commit. Recorded successes apply only to their exact run heads, not to later corrections.
- Successful Android and OHOS package jobs. Both `d01803693d5f4c05299b3d8c748677c0f5aa91f1` runs passed verification plus the four Windows/Linux/macOS/iOS jobs. Neither run validates later prepared corrections. This report did not inspect those four platform jobs' new artifact payloads.
- Successful all-six package/native gates on the same final JSON commit.
- Native post-package verification and payload/checksum inspection for all six platforms. The API transport ledger is not payload inspection.
- Immutable JSON release publication. Repository immutability being enabled alone is not publication evidence.
- Target pull, tracked-byte comparison and formal Herdr handoff.

Unsigned or debug-signed outputs cannot prove production signing, store readiness or installed-device behavior. Core and sibling-app runs are not JSON acceptance evidence.

## Round 6 prepared-source inventory

Main completed integrated read-only review and reported p4's review pass. The frozen identities below describe implemented source/configuration, **not cloud-tested corrections or acceptance**. Both baseline runs `45888643244` (push) and `45888770210` (main-reported `publish=true`) remain historical failures at exact app commit `d01803693d5f4c05299b3d8c748677c0f5aa91f1`: verification plus four platform jobs passed, Android/OHOS failed, all-six failed and release was skipped.

| Owner / frozen file | Prepared change | SHA256 |
| --- | --- | --- |
| p2: `android/gradle/wrapper/gradle-wrapper.properties` | Gradle `9.3.1` | `b690d26223576fe4e63889fad9a00df81945cb870b9476cc5a563152a1a88a74` |
| p2: `android/settings.gradle.kts` | AGP `9.1.1`, Kotlin Gradle plugin `2.4.20` | `f1df33c48dc80dd7a8c5f47d772f3ddef2d6c07869d9acba62e1cf04b47d1e87` |
| p2: `android/gradle.properties` | Legacy DSL/external Kotlin compatibility flags | `a2c1bfc0f8368940c2eef40cdd320988d1ce2d2265b8250b7cae85f5429d5ef7` |
| p2: `android/app/build.gradle.kts` | Typed Kotlin compiler options, JVM 17 retained | `3b47faf3aa85812bf2f3932ae9ef5fbdf0f3e7c3ef2052ceb36f0dbbd508b1b3` |
| p2: `.github/workflows/app-installers.yml` | Separately authorized one-line NDK preinstall alignment to `28.2.13676358` | `e868d531ef41790b49ceb71d60fe7e5780b1ac929abe0d521fa122e3930682b5` |
| p3: `ohos/entry/build-profile.json5` | Entry native packaging filter excludes `**/x86_64/*.so` | `05e2d503451f884d19f2f2886c55c4ca92bf279614405546e1551c5fae026e2b` |
| p3: `tool/ci/build_ohos.py` | Guard exact filter/input/profile identities and inspect emitted HAP metadata | `59813ae96cca58fffc39cb283505e332e53c0a472bc26c039ac3cbff09307fa3` |

Separate frozen research:

- P2's [Android toolchain rationale](android-toolchain.md), SHA256 `b33c156c7277229185d1bc129a8f098feb5e07297b24ad58c88944a5f84c8635`, explains the actual fatal wrapper error, pinned-source version requirements, four-file correction and separately authorized NDK alignment. It does not prove installed NDK identity, compiler use or an Android package result.
- P3's [OHOS ABI-filter and emitted-metadata design](ohos-abi-filter.md), SHA256 `5a3926220ac60e1e88476f092f9b48a589e3a86dc8e67375654732fcc179f809`, documents pre-HAP native filtering, unchanged input/profile guards, and planned cloud-recorded emitted member names, `.so` hashes, raw `module.json`/optional `pack.info` and exact compiled target-API fields. The implementation is not evidence that new metadata has been emitted. Compiled target API remains recorded-only, not guessed or verified against an invented encoding.

Fresh GitHub execution must validate the integrated commit. The unchanged native verifier and contract still govern package identity and the arm64-only OHOS output. No local executable validation ran for this appendix. No source/workflow edit, payload retrieval, Git mutation, signing/device/runtime acceptance or durable-release claim is included.
