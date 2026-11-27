# Implementation plan

- [x] Verify source, target, GitHub identity and Herdr participants.
- [x] Obtain user approval for task creation and implementation.
- [x] Audit branches, ignored durable files, generated output and credentials.
- [x] Preserve Trellis progress and establish cloud-only agent rules.
- [x] Make core dependency paths portable and pin cloud inputs.
- [x] Implement six-platform CI and bounded artifact retention.
- [x] Review changes without local builds or tests.
- [x] Merge reviewed branches into main and commit source changes.
- [x] Push GitHub and run remote validation.
- [x] Resolve cloud failures or record exact external blockers.
  Round 4 input: run 45864418468 at `874f195`. Verify passed. Windows and iOS packages passed.
  Round 4 fixes are implemented and independently reviewed. `w5X:p1` retains unified commit and GitHub dispatch authority.
  - [x] OHOS job 140064304581: app-setup exit 65. Owner `w5X:p3` supplied a cloud-resolved OHOS mode lock and provenance. Strict revalidation is pending.
  - [x] Linux job 140064304814: step 14 failed on `libflutter_linux_gtk.so`. Owner `w5X:p4` constrained `ldd` to the packaged library directory and preserved fatal closure checks. Cloud revalidation is pending.
  - [x] Android job 140064304819: step 7 could not locate `sdkmanager`. Owner `w5X:p2` resolved it from the pinned runner SDK root. Cloud revalidation is pending.
  - [x] macOS job 140064304834: step 11 had duplicate `QFLIJson.bundle` outputs. Owner `w5X:p5` removed only the global Xcode product-name override. Cloud revalidation is pending.
  - [x] Integrated read-only review by `w5X:p2` found no concrete blocker. `w5X:p4` inspected Windows/iOS native metadata without downloading packages. `w5X:p5` recorded run/job/artifact evidence.
- [x] Round 5 cloud revalidation at `d01803693d5f4c05299b3d8c748677c0f5aa91f1`: push run `45888643244` and publish-request run `45888770210` completed. Verify, Windows, Linux, macOS and iOS passed. Android and OHOS failed. All-six failed; release was skipped.
- [x] Round 6 fixes and same-commit cloud acceptance. Main `w5X:p1` reviews, commits, pushes and dispatches; Pi owners implement. No local executable validation.
  - [x] Android owner `w5X:p2`: align Gradle/AGP/KGP and compiler options with the fixed Flutter minima and official compatibility tables. Four Android Gradle files are frozen for review. No bypass flags, SDK/core repin or signing/ABI changes.
  - [x] OHOS producer owner `w5X:p3`: configured the documented entry-module x86_64 packaging exclusion and cloud-only emitted metadata/ABI evidence. Full native input archive and profile hashes must remain unchanged. Source is frozen; actual cloud acceptance is pending.
  - [x] Native reviewer `w5X:p4`: reviewed the exact frozen producer hashes and full diff without a concrete blocker. Output remains arm64-only. Full upstream input coverage and the unchanged native fingerprint gate remain separate requirements.
  - [x] Evidence owner `w5X:p5`: recorded both Round 5 runs, the Android toolchain evidence and the Round 6 prepared-source inventory. Inferred HAP paths and unverified compiled target API remain clearly labelled.
  - [x] Integrate reviewed changes and run GitHub verification and all six package/native gates. Run `45912056448` and `45912230227` both passed all six platform jobs and job `140224823513` / `140227496043`. Dispatch release job `140227655812` published immutable Release `460010784` after the all-six gate.
  - [x] Verify exact-head artifacts and release metadata. Both runs use `1e144e2423d6bd8b4d68a0b04983f6b97de8f996`; the immutable tag resolves to that commit. The release API manifest and checksum indices matched all 73 asset records. See `research/cloud-evidence.md` for exact evidence and signing limits.
- [x] Pull the target with `pull --ff-only`; verify the target HEAD and committed tree against GitHub main.
- [ ] Finish source/target tracked-file comparison and confirm both worktrees clean with GitHub-only target remotes.
- [ ] Record the cleanup inventory and obtain the target Codex handoff acknowledgement through Herdr.

## Validation location

Git, metadata, file hashing and static inspection may run locally.
Builds, tests, analyze, lint, package resolution and SDK installation run only in GitHub.
Run scripts/ste-lint-zh.py in GitHub for edited Chinese documentation.

## Rollback

Keep existing refs until audit decisions are recorded.
Never reset a dirty worktree or overwrite a target change.
Do not delete source or shared build infrastructure during incomplete validation.
