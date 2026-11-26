# OHOS cloud-resolved dependency lock

Evidence date: 2026-11-26 (UTC). This change addresses OHOS app-setup exit 65 in installer run `45864418468`. It does not establish OHOS package or device acceptance.

## Observed failure

- App commit: `874f1959ad2f4b75a521952017c3f49591e9b771`.
- Installer run: https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468
- OHOS job: https://github.com/azurekiln2333/qflistudio-json/actions/runs/45864418468/job/140064304581
- Step 4, `Run ./qflistudio/.github/actions/app-setup`, failed at `2026-11-26T17:08:29Z`.
- At `17:08:11.4715662Z`, the dependency guard selected OHOS mode. No OHOS mode-lock file existed, so its documented fallback selected the root upstream lock.
- At `17:08:29.6318074Z`, `flutter pub get --enforce-lockfile` reported `Would change 8 dependencies.` It then reported `Unable to satisfy pubspec.yaml using pubspec.lock.` The step exited 65.

The strict gate correctly rejected a different SDK dependency graph. This change supplies the previously generated OHOS lock without relaxing that gate.

## Successful source-lock artifact

| Field | Recorded value |
| --- | --- |
| Workflow | `Resolve pinned JSON dependency lock` |
| Run | https://github.com/azurekiln2333/qflistudio-json/actions/runs/45850250184 |
| Resolve job | `140014443287` |
| App commit | `9113f2ec0380a999b05fe27fd10de33e549fb061` |
| Result | Success, completed `2026-11-26T15:36:24Z` |
| Artifact | `resolved-lock-ohos`, ID `15134191473` |
| Archive size | 7,026 bytes |
| Archive SHA-256 | `b898f5cb7eaaedbd98ebaeef9c514e72427df3a5cad12cca8791b57b92b3de9f` |
| Artifact creation | `2026-11-26T15:36:21Z` |
| Artifact expiry | `2026-12-03T15:36:20Z` |

The artifact API metadata, resolve-job upload log and downloaded archive have the same archive SHA-256. The archive contained exactly these source files:

| Source file | Bytes | SHA-256 |
| --- | ---: | --- |
| `pubspec.lock` | 18,198 | `bbb6311daad0206abd04b88984b5511bf1f46327250f4691dc09fd37b3e5b958` |
| `lock-provenance.txt` | 396 | `3afaaa834b4f52e95c97a798dd0bca33b9330c0943ef93c48c6584a0c6606491` |
| `dependency-graph.json` | 26,076 | `0ae50b714232cb8c0f9a1bc390e07f51c3e3de56e18e0d69d1e807b6f8788d09` |

Only those three source files remain in private local `.git/migration-backup/resolved-lock-45850250184/`. The transfer archive was removed after digest verification and allowlisted extraction. No SDK, package cache, native binary or installer was downloaded locally.

The original cloud provenance is:

```text
app=9113f2ec0380a999b05fe27fd10de33e549fb061
core=476a30acee21dc486ee2849dd8064a7be665e4d5
flutter=adaf911c35c9136a7d18fc424d714c9ec7724e60
mode=ohos
cf490b3952ee3a1bab0c442472fdbd5e749d9450f8f456bbbc8c73922fa24f73  pubspec.yaml
bbb6311daad0206abd04b88984b5511bf1f46327250f4691dc09fd37b3e5b958  pubspec.lock
0ae50b714232cb8c0f9a1bc390e07f51c3e3de56e18e0d69d1e807b6f8788d09  dependency-graph.json
```

## Exact input comparison

The successful resolver and failed installer use the same dependency inputs:

| Input | Exact identity |
| --- | --- |
| App manifest SHA-256 | `cf490b3952ee3a1bab0c442472fdbd5e749d9450f8f456bbbc8c73922fa24f73` |
| Core checkout | `476a30acee21dc486ee2849dd8064a7be665e4d5` |
| OHOS Flutter | `3.41.10-ohos-1.0.1` |
| OHOS Flutter source | `adaf911c35c9136a7d18fc424d714c9ec7724e60` |
| Dart in OHOS graph | `3.11.5` |
| OHOS command-line tools input | `26.0.0.821` |
| Installed SDK metadata | `26.0.0.105`, API `26` |
| Node | `24.14.1` |
| Git plugin ref and resolved-ref | `697291a27818612ae9dc53d83d4f99fa5887908e` |

The installed SDK metadata version is not the command-line tools archive version. Both job logs report SDK `26.0.0.105`, API `26`, Node `v24.14.1`. Both verify the same Flutter tag and commit.

Git tree inspection found identical blobs at `9113f2e` and `874f195` for `pubspec.yaml`, `pubspec.lock`, `.github/actions/app-setup/action.yml`, `.github/actions/setup-ohos/action.yml`, `.github/actions/setup-ohos/setup.sh`, `.github/workflows/resolve-lock.yml`, `tool/ci/setup_flutter.sh`, `tool/ci/dependency_guard.py` and `tool/ci/native-contract.json`. The intervening installer-workflow change switches only the macOS and iOS runners from `macos-14` to `macos-15`. It does not change OHOS inputs. The resolver used the explicit `dependency-mode: resolve` branch. The installer used the default strict branch.

The reviewed source pins remain unchanged. `qfli_studio_core` still resolves from `../qflistudio-core`. The `re_editor` and `xterm` overrides still resolve from that sibling core's vendor tree. Their package versions remain `0.10.0` and `4.0.0`. `qfli_git` remains `0.1.0` at the exact Git ref above. Its entire lock block is unchanged. `flutter_secure_storage` remains `11.2.0`. No local core checkout or resolution was used for this comparison.

## Dependency delta against the official root lock

The root lock contains 80 packages. The generated OHOS lock contains 79. Exactly eight package blocks differ:

| Package | Root upstream lock | Generated OHOS lock |
| --- | --- | --- |
| `clock` | `1.1.3` | `1.1.2` |
| `intl` | `0.20.3` | `0.20.2` |
| `matcher` | `0.12.20` | `0.12.19` |
| `meta` | `1.19.0` | `1.17.0` |
| `stack_trace` | `1.12.2` | `1.12.1` |
| `test_api` | `0.7.14` | `0.7.10` |
| `vector_math` | `2.4.4` | `2.2.0` |
| `listen` | `1.0.1` | Removed |

The seven retained changed packages also carry their corresponding hosted-content SHA-256 values from the generated lock. No other package block changes. The lock's Dart constraint changes from `>=3.13.0-0 <4.0.0` to `>=3.11.5 <4.0.0`. The Flutter constraint remains `>=3.27.0`.

The preserved official graph in `research/dependency-graph.json` has SHA-256 `386a72cff385c405dbda5346b84122e8fa0457acae67bb5338c097ac888686c1`. It contains 81 graph nodes including the app. The OHOS graph contains 80. Comparing package identity, version, source, kind and unordered dependency edges confirms the same seven version changes and removal of `listen`. The only additional retained-node edge difference is that OHOS `flutter` does not depend on `listen`. The fork's JSON output omits the upstream graph's `dependencyConstraints` metadata. That serialization difference is not an additional dependency change.

## Approved source edits

| Path | Source and purpose | SHA-256 |
| --- | --- | --- |
| `tool/ci/locks/pubspec-ohos.lock` | Byte-for-byte copy of artifact `15134191473`'s `pubspec.lock` | `bbb6311daad0206abd04b88984b5511bf1f46327250f4691dc09fd37b3e5b958` |
| `tool/ci/locks/pubspec-upstream.lock` | Byte-for-byte snapshot of the unchanged official root lock | `ef4832862e8c547b490b7d5b4a0b1209dc15aaeb4063a857e8fdb5d59bf6c254` |

The upstream lock was generated in cloud run `45825769686` at app commit `df93c17c38782644021b32eda62608c4f69110f8`, core `476a30acee21dc486ee2849dd8064a7be665e4d5` and official Flutter commit `ab2912035e160d9cad6306df307576da6128ebdb`. Existing `research/lock-provenance.txt` records the same upstream lock hash. The private preserved source lock from that run also matches the root lock bytes.

The existing dependency guard already supports both mode-lock paths. Adding the upstream snapshot activates its root-versus-upstream consistency check. In OHOS mode, it copies the OHOS lock to the ephemeral job root before strict resolution. It then snapshots the selected lock and manifests for the existing drift check. No helper or workflow edit is required.

The root `pubspec.lock` remains unchanged at SHA-256 `ef4832862e8c547b490b7d5b4a0b1209dc15aaeb4063a857e8fdb5d59bf6c254`. This change does not edit manifests, core, Git plugin/native inputs, toolchain pins or signing settings.

## Review and validation boundary

Local work was limited to Git/text inspection, GitHub read requests, the reviewed source artifact download, file copying and hashing. No local build, test, analyzer, lint, dependency resolution, installation or CI-helper execution ran. Other owners' concurrent edits were preserved.

The source-lock resolution succeeded in GitHub. Strict OHOS app-setup with the newly added mode lock still requires a new GitHub run on the reviewed commit. OHOS native compilation, packaging, signing and device acceptance remain unproven by this lock-only change. Codex `w5X:p1` retains exclusive review, commit, push and cloud-dispatch authority. `w5X:p2` receives the frozen paths and hashes for read-only integrated review.
