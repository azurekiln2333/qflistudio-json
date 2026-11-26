# Design

## Repository boundary

Publish to azurekiln2333/qflistudio-json. Keep only GitHub remotes in the target.
Review the existing main and feat/offline-json-workbench branches before integration.
Preserve history unless the security audit requires a separately reviewed cleanup.
Do not force push or silently discard work.

## Portable dependency

Use sibling qflistudio-core with Dart package name qfli_studio_core.
Pin the cloud checkout to a complete published core commit.
Keep app-owned vendor overrides consistent with the checkout layout.

## Cloud validation

Use GitHub-hosted runners. Build official Flutter targets separately from the OHOS fork.
Resolve signing material only from protected GitHub secrets.
Treat unsigned packages and signed installers as separate deliverables.
Record app/core/toolchain identities and checksums with artifacts.
Apply short retention to intermediate outputs. Keep artifacts outside Git.

## Durable progress

Track Trellis specs, tasks, workflow and journals. Exclude developer identity and runtime state.
Keep historical failed and pending acceptance records unchanged.
Document missing workflow helpers rather than claiming they were executed.

## Cleanup boundary

Inventory only this repository. Shared WSL distributions require cross-owner coordination.
Verify GitHub publication and target identity before recommending source cleanup.
Never use an unrestricted git clean or delete an entire workspace.
