# Cloud-only validation rules

## Local boundary

Local work may inspect Git, text, hashes, file lists and ignored paths.
Local work must not build, test, analyze, lint, resolve packages or install SDKs.

## GitHub boundary

GitHub Actions must pin Flutter, OHOS Flutter, Node, Android and native inputs.
Each job records source, core, toolchain and native identities.
Each platform uploads intermediate logs and native outputs with short retention.
Workflow packages use fourteen-day retention and include checksums and build facts.
Durable native/package publication uses immutable GitHub release assets and SHA-256 manifests.
Do not confuse short-lived workflow artifacts with durable native storage.

## Signing boundary

Signing material comes from protected GitHub secrets.
The tracked OHOS profile contains no credential or machine path.
Unsigned output remains evidence. It cannot satisfy an installable release gate.

## Dependency boundary

The app checks out `azurekiln2333/qflistudio-core` beside itself.
The checkout path is `../qflistudio-core`.
The Dart package name remains `qfli_studio_core`.
The app-owned `re_editor` override uses the core vendor tree.
The app-owned `xterm` override also uses the core vendor tree.
Enforce the cloud-resolved lock and reject silent lock or manifest drift.
Use the reviewed Git plugin commit and its native lock blob as explicit inputs.

## Evidence boundary

Historical Trellis evidence keeps its original status and outcome.
A cloud run cannot convert a historical failed or pending gate into a pass.
Cloud validation records the exact commit and GitHub run URL.
A package archive does not prove device installation or FFI runtime behavior.
Preserve native identities separately from signing and device acceptance.
