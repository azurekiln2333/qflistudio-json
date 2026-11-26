# OHOS arm64 producer packaging filter

Round 6 source correction. This record does not claim a successful corrected cloud build. Main `w5X:p1` owns review, commits, pushes and GitHub dispatch. Pi `w5X:p4` reviews the producer change read-only.

## Failure and scope

Run `45888643244`, attempt `1`, app commit `d01803693d5f4c05299b3d8c748677c0f5aa91f1`, OHOS job `140146185215` built an unsigned HAP. Native verification then rejected an unrequested architecture at `2026-11-26T20:13:24.8085975Z`.

The retained native intermediate manifest directly lists merged and stripped x86_64 `libqfli_git.so` beside the arm64 app, engine and Git libraries. The x86_64 HAP member path is inferred from the executed verifier's preceding path/fingerprint checks and its architecture error. No HAP was fetched locally for this diagnosis. `cloud-evidence.md` preserves the detailed observation/inference boundary.

The OHOS output contract permits exactly `arm64-v8a`. Full upstream native input coverage includes x86_64, but does not authorize that output. The correction belongs in application packaging before HAP creation, not in the verifier or immutable input inventory.

## Authoritative packaging references

1. Huawei's versioned build-profile reference:
   https://developer.huawei.com/consumer/en/doc/harmonyos-guides-V13/ide-hvigor-build-profile-V13/
   The module-level `buildOption` supports `nativeLib.filter.excludes`. Its example filters HAR-dependent native libraries with `**/x86_64/*.so`. Module build options take precedence over project options for the same item.
2. Huawei's versioned native C++ reference:
   https://developer.huawei.com/consumer/en/doc/harmonyos-guides-V13/ide-hvigor-cpp-V13/
   The `nativeLib.filter` example uses the same x86_64 exclusion for app packaging. This is distinct from `externalNativeOptions.abiFilters`, which controls native compilation. `select` has higher priority than `excludes` and the pick options.
3. Current native C++ reference, consulted for the same precedence warning:
   https://developer.huawei.com/consumer/en/doc/harmonyos-guides/ide-hvigor-cpp/

The entry profile now configures only:

```json
"buildOption": {
  "nativeLib": {
    "filter": {
      "excludes": ["**/x86_64/*.so"]
    }
  }
}
```

There are no `select`, `pickFirsts`, `pickLasts` or target-specific native filter overrides in the entry profile. `build_ohos.py` requires the base filter object to match this exact object. Its pre/post hash comparison rejects profile mutation during the build. The `apiType` string uses double quotes so the existing bounded JSON5-subset reader can inspect this profile. Its value is unchanged.

## Fixed Flutter-OHOS source compatibility

The pinned Flutter commit remains `adaf911c35c9136a7d18fc424d714c9ec7724e60`, tag `3.41.10-ohos-1.0.1`. The canonical source repository is `openharmony-tpc/flutter_flutter` on GitCode. Exact source was read through the public GitHub mirror at the same commit; the paths and Git blob identities below make that retrieval explicit.

- `packages/flutter_tools/lib/src/ohos/hvigor.dart`, Git blob `210400fc1256af7c048b25f5c5c7ebb5573502d7`:
  https://github.com/zhongdaiqi/flutter_flutter/blob/adaf911c35c9136a7d18fc424d714c9ec7724e60/packages/flutter_tools/lib/src/ohos/hvigor.dart
  `assembleHap` selects the product/build mode and appends `TARGET_PLATFORM` from the requested architectures. The app helper still requests only `ohos-arm64`.
- `packages/flutter_tools/hvigor/src/plugin/flutter-hvigor-plugin.ts`, Git blob `e89b9bb9f1e96db0d96de9e8689a6d13404efd12`:
  https://github.com/zhongdaiqi/flutter_flutter/blob/adaf911c35c9136a7d18fc424d714c9ec7724e60/packages/flutter_tools/hvigor/src/plugin/flutter-hvigor-plugin.ts
  The plugin adjusts app overrides, module dependency options, Flutter tasks and generated assets. It does not replace the entry module's `buildOption.nativeLib` configuration or rewrite its build-profile file.
- `packages/flutter_tools/templates/app/ohos.tmpl/entry/build-profile.json5.tmpl`, Git blob `6de31ee2243926392c90c572c00a052f7c3fa9e9`:
  https://github.com/zhongdaiqi/flutter_flutter/blob/adaf911c35c9136a7d18fc424d714c9ec7724e60/packages/flutter_tools/templates/app/ohos.tmpl/entry/build-profile.json5.tmpl
  The pinned template places the entry module's `buildOption` at the location changed here.

These sources support applying the native packaging filter without modifying Flutter, Hvigor, the core checkout or plugin native inputs. GitHub must still demonstrate that the installed toolchain applies it.

## Cloud-only emitted evidence

`tool/ci/build_ohos.py` now records the exact filter, both product and entry profile hashes before/after building, and the full prepared native-input archive SHA-256 before/after building. The starting archive must match `prepare.json`. Any changed archive or profile fails the build helper. The helper does not delete or rewrite input binaries, unpack native inputs for surgery, alter HARs, strip libraries or rewrite ZIP members.

After Flutter creates the fresh unsigned HAP, the helper opens it read-only and records:

- Every emitted HAP member name and uncompressed byte count.
- Each `.so` member's exact path, size, SHA-256 and ABI directory.
- The source of the ABI label: the emitted `libs/<abi>/<name>.so` path, not a substitute ELF fingerprint check.
- Raw UTF-8 `module.json` and optional `pack.info` text, byte counts and SHA-256 values. Metadata reads are capped at 1 MiB per member. Absence of optional `pack.info` is explicit.
- The exact emitted `module.json` app fields: bundle name, versions, `targetAPIVersion`, `minAPIVersion`, `compileSdkVersion` and `compileSdkType`.
- The exact emitted module name, run URL and attempt.

Duplicate HAP member names fail. Missing or malformed required `module.json`, wrong app/entry identity, or missing/invalid numeric `app.targetAPIVersion` fail. Available raw metadata and hashes remain in build facts even when these gates fail. The expected JSON schema bounds are used without inventing a version mapping.

The native output ABI set must equal `['arm64-v8a']`, not merely omit x86_64. The package must contain exactly located arm64 `libapp.so`, `libflutter.so` and `libqfli_git.so`. Unexpected native paths or additional ABI directories fail. This checks emitted names and file hashes. The existing separate native-contract gate remains responsible for ELF identity, reviewed arm64 payload fingerprints and native-package acceptance. No verifier or output contract is weakened.

The existing diagnostic upload already retains `build-facts.json`; this correction needs no workflow edit. Facts are written in `finally`, with the error preserved on build/inspection failure. Successful source implementation is not proof that any new facts have been produced yet.

## Compiled target API: recorded, not guessed

Huawei's packing-tool mapping identifies `module.json` as generated output and maps `app.targetAPIVersion` from explicit `targetSdkVersion`:
https://developer.huawei.com/consumer/en/doc/doccenter-capabilities/packing-tool/

The app configuration reference specifies a numeric `targetAPIVersion` in the range 0 through 2147483647:
https://developer.huawei.com/consumer/en/doc/doccenter-getting-started/app-configuration-file/

Huawei's compatibility reference explicitly notes that API numbering changed at `26.0.0`:
https://developer.huawei.com/consumer/en/doc/harmonyos-releases/app-compatibility-influence-factor/

These references do not, by themselves, prove the fixed SDK's numeric encoding of emitted `26.0.0`. The helper therefore reads the exact compiled field rather than recursively matching unrelated metadata or copying the input target value. It leaves `compiledTargetApiVerified=false` and labels the numeric value `recorded-only`. No equality to a guessed `26` or `260000` is enforced or claimed. Fixed-SDK cloud evidence is required before establishing that encoding.

The existing input checks remain exact: product `targetSdkVersion=26.0.0`, SDK metadata API string `26`, command-line tools `26.0.0.821`, installed SDK metadata `26.0.0.105`, Node `24.14.1`, and the pinned Flutter/core commits. `compatibleSdkVersion=5.1.0(18)` remains unchanged and distinct from the target.

## Preserved boundaries and next acceptance

No SDK/core/plugin/native pin, dependency lock, product target, compatible version or signing setting changes. `native_dependencies.py` remains SHA-256 `26cd74056e9d9e83b6d944b2786ed01442141a90b77fb7570b78ba54cb44d5fc`. `native-contract.json` remains SHA-256 `5980ba82a5ab98012d8013a9139ce73d1b5bb5b730e9cf88e7d3260fe369617b`.

Local work was source/text/Git metadata inspection, approved source reads, exact edits and hashing only. No local build, test, analyzer, lint, helper execution, package resolution, dependency/SDK installation, Git mutation or payload-binary download occurred. Other owners' files were preserved.

Next GitHub acceptance must show the exact reviewed commit, strict OHOS setup, native preparation, effective filter, unchanged full input archive/profiles, arm64-only emitted members, recorded compiled metadata and the unchanged native fingerprint gate passing. The unsigned HAP still supplies no installation, runtime, device, production-signing or durable-release acceptance.
