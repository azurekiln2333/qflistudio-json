# JSON complete host gate on the published workspace core

October 24, 2026: **124/124 tests passed**, `dart analyze lib test` found no
issues, all 23 Dart files passed the format check without changes, and the
three generated curriculum assets matched. This full run includes the previous
116 cases, both real-profile editor/workspace integration cases and six new
verification-report regressions.

## Exact source and commands

- Published core commit: `2f9039a3ba95449679b17257b0313c1ee3644a2c`.
- Exact core tree: `d21ffcdc7ac9c834e0b788b21178e9f80768a519`, independently
  resolved from the local Git object. C493 records its four remote identities.
- JSON baseline: `9bd21f6841583815829c94e7898e5a692ee07a10`, plus exactly three
  captured owned overlays: `json_verification_page.dart`, the new
  `json_verification_report.dart` and `json_verification_report_test.dart`.
- Fresh sibling snapshots isolate both repositories. Package mappings for
  `qfli_json`, `qfli_studio_core` and `re_editor` point to these snapshots;
  external cached dependencies retain absolute package locations.
- The **513** captured inputs include app/core code and assets, tests, tools,
  core vendor source, dependency manifests/locks/configuration, effective
  analysis options and all three native source fixtures used by host tests.
  Before/after path sets and all hashes are identical.

The snapshot ran these commands from its JSON root:

```text
dart format --output=none --set-exit-if-changed lib test
python tool/build_json_content.py --check
dart <cached Flutter tools snapshot> --suppress-analytics test --no-pub --concurrency=1 --reporter=expanded --timeout 30s
dart analyze lib test
```

Original formatting was limited to the three owned overlay files before the
snapshot. It changed only the new test's layout. Both source captures bind the
post-format bytes. The manifest also records their canonical Git blob IDs so
the subsequent commit can be compared with the tested source.

## Report reliability correction

Previously, an exception while loading or verifying the catalog displayed a
failure but left an earlier successful disk report intact. The page now uses
one report coordinator which writes a fresh `running/false` marker before work,
persists thrown failures, and attaches a unique invocation ID plus UTC start
and finish times. Final results are written and flushed to a sibling temporary
file before replacing the marker. Storage/export failure returns failure.

Six tests cover stale-success replacement, pending invalidation, distinct
identities, missing storage and initial/staged/final write failures.
Independent review caught and corrected the write-before-flush edge, then
confirmed the revised source. A future device result must match the fresh
process marker and exported document, including run ID and contents.

## Process and queue evidence

- Java516 terminal handoff; JSON519 acceptance; automatic JSON522 terminal
  release to C. C523 accepted it. No old reservation was reused.
- UTC **03:49:23.685–03:50:02.275**, local **11:49:23–11:50:02 +08:00**;
  validation/capture elapsed **38.591 seconds** before the bounded publisher.
- Root PIDs: format19056, prepare80492, format-check60112, content83000,
  test84500, analysis66448, final capture72924, publisher82176. All exit0;
  every owned Windows Job tree is confirmed empty, with no timeout/errors.
- The containment helper records and performs post-root residual Job cleanup
  for the six work phases and source capture. The publisher needs none. This
  is recorded cleanup, not a claim that all descendants exited naturally.
  Test and analyzer acceptance also require their final success markers.
- The raw result binds the runner, preparation helper, containment helper,
  Dart executable and Flutter tool snapshot hashes. Exact helper copies and
  raw logs are retained with this run.

Raw evidence: `release-20261024T034923Z/`. This is complete host evidence for
the published core and recorded JSON correction. No native build, HAP or
installed-device action occurred in this window. Later source-bound OHOS
packages and target acceptance remain separate gates; the family goal stays
active.
