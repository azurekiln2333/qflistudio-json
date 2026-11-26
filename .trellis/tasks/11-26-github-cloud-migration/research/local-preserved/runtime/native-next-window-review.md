# native 下一窗口 —— 最终窄审查（只读）

结论：四项主张成立。未见错误声称新 root，未见重用授权，未见弱化验收。一处口径需收紧。

已验证：
- 父观察器 `run_json_ohos_window.ps1` 哈希仍 `AA0AF8DE…`，未变。
- Job helper `json-bounded-process.cs` 哈希仍 `6657CFFB…`，未变。
- 旧 HAP 已归档 `build/native703-diagnostic-hap/harness-unsigned.hap`，124516943 字节，SHA-256 `DF170F25…` 与 703 一致，mtime 未变（移动非重建）。
- 快照输出路径 `entry-default-unsigned.hap` 已不存在；`build/o6e60792d` 下 HAP 数为 0，旧产物无法冒充新构建。
- 新 manifest `prepared=true`，`preparedOrigin` 指向原 `ohos-final-preparation-20261024.json`（`af636144…`），`differences` 全空，`repositoriesChanged=[]`。
- `appRoot`/`coreRoot` 与 703 相同，未声称新 root；`snapshotState="…failed grant703 not acceptance"`、`initializedByGrant=703`、`initializationGatePassed=false`、`snapshotContainsPriorBuildIntermediates=true`、`buildExecutedDuringThisCapture=false`。
- 新窗口仍严格：release runner 第 89 行在 HAP 已存在时抛错；第 109 行 capture-after 以 `--before source-before.json` 比对；第 102 行 harness 与 normal 的 `kernelSha256` 相同即抛错。
- runner 确认新增 inspector `--prepared "$jsonOut/source-before.json"`（第 95 行）。

口径需收紧：inspector 改动不止「加参数」。新增 `native_declarations()`（187–220 行）与 311–321 行，把原生插件输入由「一律拒绝」改为「按 prepared manifest 的 bytes+sha256 逐项核对」，53 个 `nativePlugins` 条目含 `LICENSE`。这是 703 误判的实际修复，属来源锚定而非放宽；第 324 行仍拒绝在线源码。不得表述为「仅传参」。

残留风险（已披露，非隐瞒）：`snapshotContainsPriorBuildIntermediates=true`，新产物建立在 703 增量中间产物之上，不得据此声称干净构建。新字段 `initializationGatePassed`/`snapshotContainsPriorBuildIntermediates`/`diagnosticHap` 未被任何门禁消费，仅作文档。

未执行 SDK/Hvigor/hdc/设备，未改文件，未 commit。
