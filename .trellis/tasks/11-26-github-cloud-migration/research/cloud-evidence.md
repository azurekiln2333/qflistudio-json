# JSON cloud validation evidence

All commands below ran in GitHub Actions. No local build, test, analyzer, lint, dependency resolution or SDK installation was used. Times are UTC. This report separates executed checks from skipped jobs.

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

## Confirmed fixes

`80c3cda` fetches only the reviewed Flutter tag and verifies both the peeled tag and HEAD against the immutable source commit. It does not change SDK versions, constraints or dependency locks.

`9113f2e` makes two README terms consistent. No lint baseline or gate was relaxed.

## Native preparation boundary

Run `45848522721`, verify job `140008423402`, executed the early Linux prepare command at `2026-11-26T15:23:55.8811691Z`. It returned `status=prepared` and `build/ci-native/linux/prepare.json`. This exercises the locked native input parser and archive preparation. It does not prove package membership, mobile FFI loading, device installation, signing or durable release publication.

The native helper at this run has Git blob `acdc4793e4e691ccb37899e5cf3dddb7db920a00` and SHA256 `26cd74056e9d9e83b6d944b2786ed01442141a90b77fb7570b78ba54cb44d5fc`. Native package verification did not run.

## Open test failure

Run `45848522721`, job `140008423402`, failed at `test/json_named_workspace_test.dart:78`, reported by `_until` at line 439. The assertion was: `Opening the JSON Home project did not restore its primary document.` The report appeared at `2026-11-26T15:24:19.575Z`; the suite exited 1 at `15:24:26Z`.

The fixture observed `EditorProblemsBar`, which the fixed core's large-screen editor path does not render. It now passes the core-supported `AppFormFactor.phone` override to the real `QfliApp`. The Home/editor flow and all recovery assertions remain unchanged. GitHub must verify this correction.

## Acceptance still pending

- Successful full product verification on the final JSON commit.
- Actual successful Windows, Linux, macOS, iOS, Android and OHOS package jobs.
- Native post-package validation and artifact/digest inspection for all six platforms.
- Immutable JSON release publication. Repository immutability being enabled alone is not publication evidence.
- Target pull, tracked-byte comparison and formal Herdr handoff.

Unsigned or debug-signed outputs cannot prove production signing, store readiness or installed-device behavior. Core and sibling-app runs are not JSON acceptance evidence.
