# Branch, remote-head, worktree, and Trellis disposition

Audit snapshot: 2026-11-27 09:20:28 +08:00. Repository: `azurekiln2333/qflistudio-json`.

Source: `D:/MyNewProjects/qfli_json`. Target: `E:/MyNewProjects/QFLIProjects/qflistudio-json`.

Authority: `D:/MyNewProjects/_orchestra/qfli-unified-migration.md`, read in full. Its text is not reproduced here. Coordinator `w5X:p1` owns integration and final acceptance. This research refresh owns only this file.

## Audit boundary

- Read local refs, branch tracking, worktrees, remotes, status, trees, and hashes.
- Queried live GitHub heads with `git ls-remote`.
- Read the target checkout metadata without changing it.
- Checked tracked and ignored Trellis paths and the preserved-runtime manifest.
- Did not fetch, push, create, delete, reset, merge, rebase, or change a ref.
- Did not stage, commit, change Git configuration, or perform worktree-management operations. This report is the sole file written.
- Did not build, test, analyze, lint, install dependencies, install SDKs, or generate packages.

A fetch was intentionally not run. The live remote-head query is the refresh evidence that does not write remote-tracking refs.

## Current canonical revision

| Location | Branch or ref | Commit | Tree | Disposition |
| --- | --- | --- | --- | --- |
| Source | `main` | `1e144e2423d6bd8b4d68a0b04983f6b97de8f996` | `4eec9d31a3efabc72a66f9d9ed56f76003d185c3` | Retain as the active source branch. |
| Source tracking ref | `origin/main` | `1e144e2423d6bd8b4d68a0b04983f6b97de8f996` | same as source | Equal to local `main`. |
| Target | `main` | `1e144e2423d6bd8b4d68a0b04983f6b97de8f996` | `4eec9d31a3efabc72a66f9d9ed56f76003d185c3` | Retain as the target checkout branch. |
| Live GitHub | `refs/heads/main` | `1e144e2423d6bd8b4d68a0b04983f6b97de8f996` | not queried by `ls-remote` | Canonical live remote head. |

Source `main`, source `origin/main`, target `main`, and live GitHub `main` all identify the same commit. Source and target also identify the same tree. Local `main...origin/main` has zero commits on either side.

## Local branch dispositions

| Local branch or historical branch | Observed state | Disposition |
| --- | --- | --- |
| `main` | Exists at `1e144e2423d6bd8b4d68a0b04983f6b97de8f996` and tracks `origin/main`. | **KEEP / canonical.** No merge is required. |
| `feat/offline-json-workbench` | No current feature branch exists in either checkout. Its original sanitized tip `5081d54af71bb74f28cf0ed6125e15f24b5e140d` and recorded final pre-deletion tip `df93c17c38782644021b32eda62608c4f69110f8` are both ancestors of current `main`. | **INTEGRATED / historical local branch removed.** The prior audit records deletion with `git branch -d` after an ancestry check. This refresh verifies reachability and absence, not a new deletion. |
| Original publication `main` | Original tip `aeff00f590c50b31c7d657f3749b204973d17935` exists only under the private backup ref below. | **PRIVATE RETENTION.** Its sanitized ancestry is represented in published `main`. Do not publish the original ref. |
| Original publication feature | Original tip `d3234e148913af58dacd8040ebed48e46a8336fc` exists only under the private backup ref below. | **PRIVATE RETENTION.** Do not publish the original ref. |

`history-map.json` records the original-to-sanitized mapping. Fresh `git merge-base --is-ancestor` checks returned exit 0 for sanitized original `main` at `2029bcd5b4943c79652625073fa400ab5bf195af`, sanitized feature tip `5081d54af71bb74f28cf0ed6125e15f24b5e140d`, and final feature tip `df93c17c38782644021b32eda62608c4f69110f8`, all against current `main`. These checks close the surviving and historically removed development branches. No branch deletion or history rewrite occurred in this refresh.

## Live remote-head dispositions

The live query at audit time returned exactly one GitHub branch head:

```text
1e144e2423d6bd8b4d68a0b04983f6b97de8f996 refs/heads/main
```

The live symbolic `HEAD` points to `refs/heads/main`. No live `feat/offline-json-workbench` head or other GitHub branch head was returned.

| Remote ref | Disposition |
| --- | --- |
| `origin/main` / live `refs/heads/main` | **KEEP / canonical publication.** Equal to source and target `main`. |
| Target `origin/HEAD` | **KEEP / symbolic pointer.** Points to `origin/main`, not an additional branch. No source `origin/HEAD` ref exists. |
| Any other live GitHub branch | **NONE OBSERVED.** No disposition or deletion action is needed. |

Both source and target have only the GitHub `origin` remote. The fetch and push URLs are both:

```text
https://github.com/azurekiln2333/qflistudio-json.git
```

No non-GitHub remote was observed.

## Private backup refs

The source repository retains these local backup refs:

```text
refs/backup/pre-sanitize-20261126/main
  aeff00f590c50b31c7d657f3749b204973d17935
refs/backup/pre-sanitize-20261126/feat/offline-json-workbench
  d3234e148913af58dacd8040ebed48e46a8336fc
```

Disposition: **KEEP PRIVATE / EXCLUDE FROM PUBLICATION.** These refs preserve pre-sanitization history. They are not development branches, live remote heads, or merge candidates. Fresh ancestry checks returned exit 1 for both original tips against current `main`, as expected for sanitized history. Use the mapped sanitized tips for integration decisions, not the sensitive originals. Never push backup refs. Never use `git push --all` or `git push --mirror`.

Private backup metadata was observed at `.git/migration-backup/20261126/`: `original-history.bundle`, `working-tree.patch`, `mapping.json`, and `refs.json`. Contents were not opened. Keep these outside publication. No backup was moved or deleted, and no new backup or secure-retention verification was performed. Any relocation or secure-retention decision remains with the coordinator.

The prior 2026-11-26 audit records that all 25 original commits were sanitized only at `ohos/build-profile.json5`. It records preservation of identities, timestamps, messages, parents, and other tree entries. At `9113f2ec0380a999b05fe27fd10de33e549fb061`, its bounded scan covered 33 reachable commits and 893 Git objects with zero exact historical-password matches, recognized private-key/GitHub-token patterns, or forbidden compiled/signing paths. Those are historical findings, not a fresh scan of current `main` or a universal secret certification.

Source refs consist of the two backup refs, `refs/heads/main`, and `refs/remotes/origin/main`. Target refs consist of `refs/heads/main`, `refs/remotes/origin/main`, and symbolic `refs/remotes/origin/HEAD`. No tags or stash refs were observed.

## Worktree dispositions

| Worktree | Branch | Observed HEAD | Status at observation | Disposition |
| --- | --- | --- | --- | --- |
| `D:/MyNewProjects/qfli_json` | `main` | `1e144e2423d6bd8b4d68a0b04983f6b97de8f996` | `M AGENTS.md` | **KEEP.** Do not reset or overwrite the unowned change. This source worktree is not clean. |
| `E:/MyNewProjects/QFLIProjects/qflistudio-json` | `main` | `1e144e2423d6bd8b4d68a0b04983f6b97de8f996` | clean at observation | **KEEP.** Target worktree is clean and matches source HEAD and tree. |

Each checkout reports one worktree. No additional worktree was observed. Before this report, source `git status --porcelain=v1 --untracked-files=all` reported only `AGENTS.md` modified. There were no staged changes or non-ignored untracked files. That change belongs to another owner and was left untouched. This report also becomes modified until the coordinator integrates it. The source cannot pass a clean-worktree or push-gate check in this state. Committed-tree equality does not establish equality of dirty working files or final migration acceptance.

Final metadata recheck at 2026-11-27 09:27:37 +08:00: source and target HEAD/tree and live GitHub `main` remain as recorded above. Target status remains empty. Source now also reports a concurrent `research/cloud-evidence.md` modification alongside this report and `AGENTS.md`. That evidence change is another owner's work and was not edited here. Do not treat this shared-worktree snapshot as atomic or final acceptance.

## Trellis preservation disposition

The current `main` tree and index each contain 303 tracked `.trellis` paths. Before this report, no durable Trellis modification or non-ignored untracked Trellis path was reported.

| Tracked class | Paths | Disposition |
| --- | ---: | --- |
| `.trellis/tasks/10-22-offline-json-ide/` | 205 | Preserve historical task, research, outcomes, and source evidence. |
| `.trellis/tasks/11-26-github-cloud-migration/` | 93 | Preserve migration artifacts, including 76 `research/local-preserved/` paths. |
| `.trellis/spec/` | 2 | Preserve product and cloud-only contracts. |
| `.trellis/workspace/` | 2 | Preserve index and journal. |
| `.trellis/workflow.md` | 1 | Preserve workflow. |

The 76 preserved-directory paths are a subset of the 93 migration paths, not an additional count. Both spec files, all task PRDs/designs/plans/context manifests, research, historical outcomes, and the workspace index/journal remain durable progress.

The ignored Trellis state remains local and is not a publication candidate:

- `.trellis/.developer` is local developer identity.
- `.trellis/.runtime/` contains 101 ignored runtime paths, including session state, screenshots, ownership records, and quarantine material.
- Three additional ignored bytecode files under historical research are generated state. One more bytecode file is already included in the 101 runtime paths. All remain untouched.

There are 105 ignored Trellis paths in total: 101 runtime paths, one developer-identity file, and three additional bytecode files. The index contains no `.trellis/.developer` or `.trellis/.runtime/` paths. Do not blanket-add or remove these ignored boundaries.

The preserved-runtime manifest was checked read-only. It reports 101 original runtime entries:

| Manifest status | Entries | Bytes | Local identity check |
| --- | ---: | ---: | --- |
| `already_tracked` | 20 | 280,945 | 20 of 20 present with matching size and SHA-256. |
| `preserved` | 72 | 883,702 | 72 of 72 present with matching size and SHA-256. |
| `preserved_alias` | 2 | 246 | 2 of 2 present with matching size and SHA-256. |
| `local_quarantine` | 6 | 2,458,872 | 6 of 6 remain local with matching size and SHA-256. |
| `regenerable_cache` | 1 | 43,154 | 1 of 1 remains local with matching size and SHA-256. |

All 94 mapped entries resolve to 91 distinct tracked counterpart paths. Each counterpart exists in the current `main` tree, and each current local counterpart matches its manifest size and SHA-256. All 101 original local runtime files also match their recorded sizes and SHA-256 values. No runtime entry is unmapped. The six quarantine files and the runtime bytecode remain intentionally unpublished, not missing preservation work.

The `local-preserved/.gitattributes` rule still reports `text: unset` for the manifest and representative preserved source/reference files. The 72 unique copied payloads total 883,702 bytes. Aliases and existing tracked duplicates do not represent extra payload copies. Manifest SHA-256: `f3b33993976315a1d03018c5c40b225092e9d34f271017cb9a7cba9261061d87`.

This is bounded byte-identity and tracked-tree evidence, not a new privacy audit, device pass, or verification of large historical packages, Release assets, and their dependency closure. Prior failed, pending, and HOLD outcomes remain unchanged. No ignored Trellis path was deleted, moved, staged, or published.

## Readiness and blockers

- **Research disposition: READY.** Branch, live-head, worktree, backup-ref, and Trellis dispositions are recorded.
- **Source publication: NOT READY.** The source worktree has unowned `AGENTS.md` and `research/cloud-evidence.md` modifications. This report is also an authorized research change until integrated by the coordinator.
- **Target metadata comparison: MATCH at this observation.** Target HEAD and committed tree equal the source, both use canonical GitHub URLs, and only the target is clean. Final handoff and working-file comparison belong to the coordinator.
- **Cleanup: NOT AUTHORIZED.** Private backups, ignored runtime state, generated state, build output, native output, caches, and shared WSL data remain outside any deletion set.
- **Cloud/release acceptance: NOT ASSESSED.** No Actions, artifact, Release, signing, or device claim is made by this branch-only refresh.

No Git write, build, test, package operation, push, or target write occurred during this refresh.
