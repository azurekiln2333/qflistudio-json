# Android toolchain diagnosis and prepared correction

Evidence date: 2026-11-26 (UTC). Owner: Pi `w5X:p2`.

This record explains the frozen four-file Android correction and the separately authorized one-line workflow NDK preinstall alignment. It is source and log review, not a successful Android build. Codex `w5X:p1` retains unified review, commit, push and cloud-dispatch authority. Other owners' workflow, OHOS producer and evidence changes are outside this file's ownership.

## Actual cloud failures

Both runs use app commit `d01803693d5f4c05299b3d8c748677c0f5aa91f1`, official Flutter `3.50.0` at `ab2912035e160d9cad6306df307576da6128ebdb`, and core `476a30acee21dc486ee2849dd8064a7be665e4d5`.

| Run and Android job | Event | Observed failure time UTC |
| --- | --- | --- |
| [45888643244 / 140146185432](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45888643244/job/140146185432) | `push` | `2026-11-26T20:11:27.6832617Z` |
| [45888770210 / 140149745207](https://github.com/azurekiln2333/qflistudio-json/actions/runs/45888770210/job/140149745207) | `workflow_dispatch` | `2026-11-26T20:20:01.3185934Z` |

Each Android log reports project Gradle `8.14.0` below Flutter's minimum `9.3.1` while applying `dev.flutter.flutter-gradle-plugin` in `android/app/build.gradle.kts`. Each `assembleRelease` invocation exits 1. Both SDK-preparation steps and native-input preparation passed first. The native helper reported `status=prepared` at `20:10:08.2210217Z` and `20:18:32.4212327Z`, respectively. Both Java version commands reported Temurin `17.0.21.1`.

These observations establish that the earlier sdkmanager lookup fix reached its next gate. Native preparation validates the prebuilt native inputs. It does not establish Gradle compatibility, app compilation or APK/AAB package acceptance. The second run is the coordinator's `publish=true` dispatch; an intended publication does not override failed packaging gates. See [cloud-evidence.md](cloud-evidence.md) for the unified run and publication outcomes.

## Fixed Flutter source identities

The following paths were retrieved from `flutter/flutter` with GitHub's read-only contents API, using the complete commit above. Line numbers below refer to the original file bytes decoded from the API, not a reformatted web rendering. The content hashes were computed on those decoded source bytes without executing them.

| Label and path below Flutter root | Git blob | SHA256 |
| --- | --- | --- |
| F1: `packages/flutter_tools/gradle/src/main/kotlin/DependencyVersionChecker.kt` | `1b491847a7e6f0abfd2078f9d57f79ac6f92a2df` | `c5c93a43f7ae5bc21226d782267cabeb20eb60bc921d8c9da5de45e13fce0226` |
| F2: `packages/flutter_tools/lib/src/android/gradle_utils.dart` | `b00ce8b12128d9eea3848dff65511c96b53dcbfd` | `135aa8be414be334ca5d4d4438c697773fd176f70b50bd85a24ace85c59eaabd` |
| F3: `packages/flutter_tools/gradle/src/main/kotlin/FlutterExtension.kt` | `dfce6d1deb8ff53f0fa5e12292fd2735bea6a54d` | `a8ca02d55798c200d766e245dae9df20565cb9d638d4887b51bf617abac938a1` |
| F4: `packages/flutter_tools/templates/app/android.tmpl/gradle.properties.tmpl` | `e96108cfe4c4d200adab58b532e95774c88e485b` | `0f82b18017fba6bb5ce3aa4b2d1a00c9382fc8aae7b1d9326e44b18abd66d80b` |
| F5: `packages/flutter_tools/templates/app/android-kotlin.tmpl/app/build.gradle.kts.tmpl` | `0225bd08985c2ed865a76fcdcfcdf89eb1abe876` | `53c8326bb7569b252bcc94d345ef3282c7aa6bf0f8f7347dd6302d557aac2bb6` |

Fixed primary-source links:

- [F1: dependency validation](https://github.com/flutter/flutter/blob/ab2912035e160d9cad6306df307576da6128ebdb/packages/flutter_tools/gradle/src/main/kotlin/DependencyVersionChecker.kt).
- [F2: template versions and compatibility tables](https://github.com/flutter/flutter/blob/ab2912035e160d9cad6306df307576da6128ebdb/packages/flutter_tools/lib/src/android/gradle_utils.dart).
- [F3: app extension defaults](https://github.com/flutter/flutter/blob/ab2912035e160d9cad6306df307576da6128ebdb/packages/flutter_tools/gradle/src/main/kotlin/FlutterExtension.kt).
- [F4: Gradle property template](https://github.com/flutter/flutter/blob/ab2912035e160d9cad6306df307576da6128ebdb/packages/flutter_tools/templates/app/android.tmpl/gradle.properties.tmpl).
- [F5: Kotlin app build template](https://github.com/flutter/flutter/blob/ab2912035e160d9cad6306df307576da6128ebdb/packages/flutter_tools/templates/app/android-kotlin.tmpl/app/build.gradle.kts.tmpl).

## Exact minima and selected versions

F1 defines distinct fatal minima and warning thresholds:

| Dependency | Fatal minimum | Warning threshold | Original project | Prepared correction |
| --- | --- | --- | --- | --- |
| Gradle | `9.3.1` (line 96) | `9.5.0` (line 94) | `8.14` wrapper | `9.3.1` |
| Java | `17` (line 101) | `17` (line 99) | JDK/JVM target `17` | Unchanged |
| Android Gradle plugin | `9.1.1` (line 105) | `9.3.1` (line 103) | `8.11.1` | `9.1.1` |
| External Kotlin Gradle plugin | `2.4.10` (line 111) | `2.4.20` (line 109) | `2.2.20` | `2.4.20` |

F1 lines 129-148 check Gradle, Java, AGP and then external KGP when built-in Kotlin is not enabled. The Gradle error prevents the observed run from reaching all subsequent checks. The original AGP and KGP are also below their fatal minima. A wrapper-only patch would therefore be incomplete. The prepared Gradle and AGP versions meet the fatal minima but remain below their warning thresholds. Warnings may remain; no warning or failure gate was disabled.

F2 lines 34, 40 and 47 define template defaults `9.5.0`, `9.3.1` and `2.4.20`. This patch does not claim to copy that entire tuple. It selects the lower supported Gradle/AGP pair and the template KGP. F2 lines 825-826 map AGP `9.1.x` to Gradle `9.3.1` or later. Lines 592-593 and 710-712 cover KGP `2.4.20` with this Gradle/AGP pair. Lines 601-603 instead cap the old KGP `2.2.20` Gradle range below `8.14.99`.

Two upstream compatibility documents independently support the chosen tuple:

- [Android AGP 9.1.1 compatibility](https://developer.android.com/build/releases/agp-9-1-0-release-notes): Gradle minimum/default `9.3.1`, JDK minimum/default `17`, SDK Build Tools minimum/default `36.0.0`. Its NDK default is `28.2.13676358`, not a mandatory minimum.
- [Kotlin Gradle compatibility table](https://kotlinlang.org/docs/gradle-configure-project.html): KGP `2.4.20-2.4.21` fully supports Gradle `7.6.3-9.7.0` and AGP `8.5.2-9.3.1`. KGP `2.4.0-2.4.10` lists an AGP upper bound of `9.1.0`. Selecting `2.4.20` avoids depending on support outside that narrower published range. The old `2.2.20-2.2.21` range ends at Gradle `8.14` and AGP `8.11.1`.

These live official documents were checked during this review. The complete Flutter commit and source hashes above preserve the fixed source basis if those documentation pages later change.

## Legacy DSL and Kotlin configuration

The app already applies `kotlin-android`. The patch retains it rather than expanding scope to a full built-in-Kotlin migration.

F4 lines 4 and 6 set `android.newDsl=false` and `android.builtInKotlin=false`. The prepared `android/gradle.properties` adopts those exact values. Android's [built-in Kotlin opt-out documentation](https://developer.android.com/build/migrate-to-built-in-kotlin#opt-out-of-built-in-kotlin) also requires the old DSL when retaining the external Kotlin Android plugin. These compatibility settings do not disable Flutter's dependency-version validation. They are not a permanent AGP 10 migration strategy.

F5 lines 41-45 configure typed top-level `kotlin.compilerOptions` with `JvmTarget.JVM_17`. The patch replaces `android.kotlinOptions` with this configuration while preserving Java source/target `17`. Kotlin's [compiler-options migration guide](https://kotlinlang.org/docs/gradle-compiler-options.html#migrate-from-kotlinoptions-to-compileroptions) recommends typed compiler options and migration away from `android.kotlinOptions`. No Kotlin source file or application behavior was rewritten.

## Frozen four-file source correction

All four files were re-read immediately before editing, then read back in full. Only the following changes are in the Android patch:

| File and current lines | Change | Frozen SHA256 |
| --- | --- | --- |
| `android/gradle/wrapper/gradle-wrapper.properties:5` | Official wrapper distribution URL changes from `gradle-8.14-all.zip` to `gradle-9.3.1-all.zip` | `b690d26223576fe4e63889fad9a00df81945cb870b9476cc5a563152a1a88a74` |
| `android/settings.gradle.kts:22-23` | AGP `8.11.1` to `9.1.1`; KGP `2.2.20` to `2.4.20` | `f1df33c48dc80dd7a8c5f47d772f3ddef2d6c07869d9acba62e1cf04b47d1e87` |
| `android/gradle.properties:3-5` | Adds a rationale comment and the two pinned-template compatibility flags | `a2c1bfc0f8368940c2eef40cdd320988d1ce2d2265b8250b7cae85f5429d5ef7` |
| `android/app/build.gradle.kts:38-42` | Replaces legacy Kotlin options with typed JVM 17 options | `3b47faf3aa85812bf2f3932ae9ef5fbdf0f3e7c3ef2052ceb36f0dbbd508b1b3` |

Namespace, application ID, SDK declarations, the app's NDK declaration, requested ABIs, debug-key signing classification and all publication/native gates remain unchanged. Flutter, core, dependency locks and native plugin inputs remain unchanged. No validation-skip option was added. The four-file patch is frozen pending main's review and cloud execution.

## Separate authorized NDK preinstall alignment

The initial read-only review found this mismatch before requesting authorization:

- `.github/workflows/app-installers.yml:31` declared `ANDROID_NDK_VERSION: 27.0.12077973` in both failed runs.
- That workflow's Android preparation step passes the value to sdkmanager as the exact `ndk;...` preinstall package.
- `android/app/build.gradle.kts:11` independently sets `ndkVersion = flutter.ndkVersion`. It does not read `ANDROID_NDK_VERSION`.
- F3 line 42 sets the effective requested revision to `28.2.13676358`. F2 line 64 agrees. The immutable Flutter commit therefore transitively pins that request.

The failed runs' `27.0.12077973` preinstall value is not proof that the app compiled with NDK 27. The observed failure occurred during plugin configuration before Android compilation could establish an executed compiler identity. It is also not proof that NDK 28.2 was downloaded or used. No successful APK, AAB or native compiler invocation was inspected in these failed runs.

The mismatch weakened the clarity of the documented pin contract in `.trellis/spec/cloud-only.md`: the explicitly preinstalled revision differed from the pinned app request. It did not make the app's NDK request inherently unpinned. Existing `tool/ci/stage_artifact.py` records the immutable Flutter identity but does not emit a separate installed Android NDK revision field. That transitive source identity must not be described as direct evidence of an executed NDK installation.

### Implemented one-line correction, cloud validation pending

Main `w5X:p1` authorized this exact additional scope after receiving the read-only recommendation. Only `.github/workflows/app-installers.yml:31` changed from `ANDROID_NDK_VERSION: 27.0.12077973` to `ANDROID_NDK_VERSION: 28.2.13676358`. The workflow was re-read before the edit. Its diff contains only that environment value change.

This aligns the declared cloud preinstall with the app's existing request and the AGP 9.1.1 default. The app still uses `ndkVersion = flutter.ndkVersion`. No app NDK override was added. Overriding the app to NDK 27 would instead change the effective compiler baseline without evidence that the downgrade is appropriate. Flutter/core pins, CMake, signing, ABIs and all verification/publication gates remain unchanged.

The alignment is separate from the frozen four-file Gradle correction above. It is implemented source configuration, not evidence that sdkmanager installed NDK 28.2 or that any compiler used it. A future cloud run must establish installation and actual build use. Broader installed-toolchain provenance instrumentation remains outside this edit. P5 owns the corresponding update to `cloud-evidence.md`.

## Validation and ownership boundary

Local work used read-only Git metadata/diffs, file reads, source hashes and GitHub API/job-log requests. Primary documentation was read online. No local Gradle/Flutter/Java build command, test, analyzer, lint, Pub resolution, SDK/dependency installation or CI-helper execution ran. No SDK, distribution archive, package cache, installer or native binary was downloaded. No Git ref, index, commit or remote was mutated.

This follow-up writes this research file and the separately authorized single workflow environment value. The previously reported four Android source hashes remain frozen. Fresh GitHub execution must validate dependency configuration, compilation, all three APK ABIs, the universal AAB, native package membership and lock stability. Runtime, device, production signing, installer acceptance and durable publication remain separate gates. No part of this diagnosis converts either failed historical run into a pass.
