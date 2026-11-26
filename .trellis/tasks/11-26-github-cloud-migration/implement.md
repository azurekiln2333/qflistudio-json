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
- [ ] Resolve cloud failures or record exact external blockers.
  Round 4 input: run 45864418468 at `874f195`. Verify passed. Windows and iOS packages passed.
  Round 4 fixes are implemented and independently reviewed. `w5X:p1` retains unified commit and GitHub dispatch authority.
  - [x] OHOS job 140064304581: app-setup exit 65. Owner `w5X:p3` supplied a cloud-resolved OHOS mode lock and provenance. Strict revalidation is pending.
  - [x] Linux job 140064304814: step 14 failed on `libflutter_linux_gtk.so`. Owner `w5X:p4` constrained `ldd` to the packaged library directory and preserved fatal closure checks. Cloud revalidation is pending.
  - [x] Android job 140064304819: step 7 could not locate `sdkmanager`. Owner `w5X:p2` resolved it from the pinned runner SDK root. Cloud revalidation is pending.
  - [x] macOS job 140064304834: step 11 had duplicate `QFLIJson.bundle` outputs. Owner `w5X:p5` removed only the global Xcode product-name override. Cloud revalidation is pending.
  - [x] Integrated read-only review by `w5X:p2` found no concrete blocker. `w5X:p4` inspected Windows/iOS native metadata without downloading packages. `w5X:p5` recorded run/job/artifact evidence.
- [ ] Round 5 cloud revalidation on the unified commit: strict OHOS mode lock, Linux package closure, Android SDK setup, macOS universal build, all-six gate and immutable release readback. Trigger `workflow_dispatch` with `publish=true`; publication remains gated by all-six success.
- [ ] Pull the target and compare commits, trees and tracked file contents.
- [ ] Confirm clean source and target worktrees and GitHub-only target remotes.
- [ ] Record cleanup inventory and final handoff through Herdr.

## Validation location

Git, metadata, file hashing and static inspection may run locally.
Builds, tests, analyze, lint, package resolution and SDK installation run only in GitHub.
Run scripts/ste-lint-zh.py in GitHub for edited Chinese documentation.

## Rollback

Keep existing refs until audit decisions are recorded.
Never reset a dirty worktree or overwrite a target change.
Do not delete source or shared build infrastructure during incomplete validation.
