# Published history and branch disposition

Audit date: 2026-11-26. Repository: `azurekiln2333/qflistudio-json`.

The original local main and feature histories contained historical OHOS signing configuration. Before first publication, all 25 original commits were rewritten only at `ohos/build-profile.json5`. Author/committer identities, timestamps, messages and parent relationships were retained. Every rewritten tree was compared with its source tree. `history-map.json` records the mapping.

The original history and worktree patch remain in private local `.git/migration-backup/20261126/` and `refs/backup/pre-sanitize-20261126/`. These contain sensitive historical configuration. Never push those refs or backups. Never use `git push --all` or `git push --mirror` for this repository.

| Ref | Disposition |
| --- | --- |
| Original local `main` | Preserved in sanitized ancestry of published `main`; original retained privately. |
| `feat/offline-json-workbench` at `df93c17c38782644021b32eda62608c4f69110f8` | Verified ancestor of `main` with `git merge-base --is-ancestor`, then removed with `git branch -d`. No work was discarded. |
| GitHub `main` | Only remote head returned by live `git ls-remote --heads origin` at this audit. |
| Private backup refs | Intentionally excluded from publication; not development branches to merge. |

At `9113f2ec0380a999b05fe27fd10de33e549fb061`, the publication scan covered 33 reachable commits and 893 Git objects. It found zero exact matches for the historical signing passwords, zero recognized private-key/GitHub-token patterns and zero forbidden compiled/signing artifact paths. This bounded scan is not a universal secret certification.

Source and target each have only canonical GitHub `origin`. The target was still an unborn main with only `.git` during the pre-pull inspection. Final equality belongs in the handoff report.
