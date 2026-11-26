# 归档审查：native-retry-20261026（提交后复核）

只读审查。未运行 SDK、Flutter、hdc 或设备。未改共享核心文件。未改冻结脚本。
审查对象：`.trellis/tasks/10-22-offline-json-ide/research/native-retry-20261026/`。
提交：HEAD `d0f3c50`。工作区对该目录干净。
基准：`4ded5d7` 的 `native-703-20261026/`。

## 结论

未发现阻断 provenance 问题。提交字节与清单声明全部相符。
F1、F2、F3 已解决。明确记录一项 NOT READY 留存问题。
该留存问题阻断运行，不损害 provenance。
703 仍是失败且已释放的窗口。

## 提交字节核对

- 提交树含 29 个文件。`validation.json` 声明 28 个。
- 两者差 1 个，即 `validation.json` 自身。清单无法声明自身哈希，属固有限制。
- 28 项声明逐一对提交 blob 计算 SHA-256。字节与哈希 0 处不符。
- 28 项工作区字节等于提交 blob。0 处漂移。
- 提交树无 `__pycache__`。`.gitignore` 的 `*.pyc` 已排除。
- 无未声明的已提交文件。

## 明确 NOT READY 留存项

`validation.json` 记录如下。

- `executionReady` 为 false。
- `retentionIssue` = `unchanged bounded helper closes uncertain handles; source-only repair required before new READY`。
- `boundedJobHelperUnchanged` 为 true。
- `parentObserverUnchanged` 为 true。
- `newNativeGrantReceived` 为 false。`deviceExecuted` 为 false。
- `coordinatorNoticeEvent` 为 767。
- `diagnosticOfflineInspectionPassed` 为 true。
- `diagnosticDoesNotPassGrant703` 为 true。

`README.md` 含章节 `Retention issue found before READY`。
该节写明：未变的 bounded Job helper 在清理未确认时关闭句柄，违反保留 HOLD 要求。
该节写明：本轮为 source-only 修复证据，NOT READY for execution。
该节写明：新原生授权前必须先做单独保留修复与验证。
引用：`README.md` 第 44 至 49 行，以及 `validation.json` 的 `retentionIssue` 与 `executionReady`。

## 前次发现状态

- F1 已解决。`diagnostic-inspection.json` 59363 字节已入清单。
- F2 已解决。`README.md` 3235 字节、`documentation-lint.json` 402 字节已入清单。
- F3 已解决。字节码未提交。
- F4 仍为低。负向控制源未归档。
  `capture-checks.json` 引用 `build/native-final-readiness-26555365/` 下 3 个源文件与哈希。
  归档只保留 `tool-changed.log`、`readiness-tool-changed.log`、`readiness-source-changed.log`。
  源文件当前仍在本地，可复核。归档自身不能重放这 3 个用例。
- F5 仍为低。`namedToolAndPluginFiles` 为 13，只等于 `prepared-manifest.json` 的 `tools` 表项数。插件文件为 53。
- F6 仍为提示。`originFileMapsMatchCommittedBefore` 实际比对 `originalAppInputs` 与 `originalCacheReferences`。两者在 703 前后不变。

## 前次成立项仍成立

- 提交 `4ded5d7` 的 703 前后捕获哈希相符。
- `prepared-manifest.json` 的 provenance 与 `validation.json` 一致。
- 805 文件、7 缓存引用、6 用例、19 归因控制、16 就绪控制全部相符。
- 新增 1、变更 4、缓存引用新增 1、删除 0 的差额相符。
- `runners/` 9 个脚本与 live `.trellis/.runtime/` 逐字节相同。
- 诊断内部绑定成立：`preparedManifestSha256`、`diagnosticHap.sha256` 与 `hapSha256` 互等。

## 边界

- 诊断只覆盖 harness HAP。它不证明普通包通过，也不证明设备通过。
- 本留存问题属于运行门禁，不是归档造假或哈希不符。
- 未复核 `.trellis/spec/json-offline.md` 之外的产品契约。