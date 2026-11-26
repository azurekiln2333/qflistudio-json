# Cloud-only validation rules

## Local boundary

Local work may inspect Git, text, hashes, file lists and ignored paths.
Local work must not build, test, analyze, lint, resolve packages or install SDKs.

## GitHub boundary

GitHub Actions must pin Flutter, OHOS Flutter, Node, Android and native inputs.
Each job records source, core, toolchain and native identities.
Each platform uploads intermediate logs and native outputs with short retention.
Release packages use fourteen-day retention and include checksums and build facts.

## Signing boundary

Signing material comes from protected GitHub secrets.
The tracked OHOS profile contains no credential or machine path.
Unsigned output remains evidence. It cannot satisfy an installable release gate.

## Dependency boundary

The app checks out `azurekiln2333/qflistudio-core` beside itself.
The checkout path is `../qflistudio-core`.
The Dart package name remains `qfli_studio_core`.
The app-owned `re_editor` override uses the core vendor tree.

## Evidence boundary

Historical Trellis evidence keeps its original status and outcome.
A cloud run cannot convert a historical failed or pending gate into a pass.
Cloud validation records the exact commit and GitHub run URL.
