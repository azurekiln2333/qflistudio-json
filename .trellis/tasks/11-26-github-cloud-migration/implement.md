# Implementation plan

- [x] Verify source, target, GitHub identity and Herdr participants.
- [x] Obtain user approval for task creation and implementation.
- [ ] Audit branches, ignored durable files, generated output and credentials.
- [ ] Preserve Trellis progress and establish cloud-only agent rules.
- [ ] Make core dependency paths portable and pin cloud inputs.
- [ ] Implement six-platform CI and bounded artifact retention.
- [ ] Review changes without local builds or tests.
- [ ] Merge reviewed branches into main and commit source changes.
- [ ] Push GitHub and run remote validation.
- [ ] Resolve cloud failures or record exact external blockers.
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
