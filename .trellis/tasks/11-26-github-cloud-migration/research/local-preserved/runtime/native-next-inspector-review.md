# native inspector 窄审查（最终）

受检文件：
- `.trellis/.runtime/inspect_json_release_hap.py`，24771 字节，SHA-256 `2281654044fbf474ed647f8b9a526f9439485b4063154813d3fff29169d025ce`
- `.trellis/.runtime/test_json_native_source_attribution.py`，8771 字节，SHA-256 `0ea11973eaa218c6c9d5bebbf4a20c2a45f3d4bdc3deb1ed780fe96165dba052`，17 项测试

**新增两项已核对属实。**
其一，`parse_depfile` 第 155 至 159 行保留原始拼写：`spelled_inputs = tokens(..., resolve=False)` 走 `candidate.absolute()`，另存 `inputPaths`，`inputs` 单独 `resolve()`。
其二，第 321 至 323 行拒绝越界：`any(lexical_inside(spelled, root))` 且 `not any(inside(dependency, root))` 即 `BlockedInspection`。`lexical_inside` 用 `abspath`，不解析链接。

**但该越界核对只挡住逃到全部隔离根之外。**
`isolated_roots = (app, core, native)` 三个根同级。拼写落在 `native` 内、解析落在 `app` 内时，`any(inside(...))` 因 `app` 命中而为真，判定通过。此后 `not inside(dependency, app)` 为假，插件分支与原始源码分支都不进入，该输入既不绑定 `declared` 也不被拒。插件内 junction 指向 app 缓存正是这种形态，实测存在。

**阻断 1 仍在**：第 360 行 `preparedManifestVerified` 只入证据。无插件输入时记录 `inputCount: 0`、`false`，`status` 仍 `PASS`。
**阻断 2 仍在**：`declared` 只作查表（第 329 行）与计数（第 366 行）。插件根以下文件集从不与 `declared` 双向比对，新增 `.so` 这类不进 depfile 的文件即可绕过。

**已核对正确**：wrapper 已传 `--prepared`。`native_declarations(None)` 返回 `{}`。`isolated_native_root` 钉住 staging 位置、名字、无链接，失败即 fail-closed。`prepared.appRoot`/`coreRoot` 必须等于受检根。插件根经 `.flutter-plugins-dependencies` 与 `package_config.json` 双向对齐。逐输入比对 `bytes` 与 `sha256`。