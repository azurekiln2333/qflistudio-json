# 交接说明与证据一致性校验（只读）

范围：`.trellis/tasks/10-22-offline-json-ide/research/native-window-20261026/`。
对象：`README.md`、`command-template.json`、`identities.json`、`preflight.json`、`controls/*.json`、`runners/*`。
方法：静态阅读加只读取哈希。未执行 SDK、Flutter、hdc 或任何构建，未改脚本，未 commit。

结论：7 个 runner 的哈希与证据全等，源快照 804 个文件前后全等，5 个控制用例的观察者副本只差 10 行。有 6 处可证实的偏差，其中 2 处影响后继方判断。

---

## 1. 可证实的偏差

### 1.1 「same process identity is gone」无实现支撑

README 原文：

> The descendant test records explicit residual cleanup and checks that the same process identity is gone before relay.

实际实现只数 Job 的活跃进程数。
`json-bounded-process.cs:186`：

```csharp
while (ActiveCount(job) != 0 && cleanup.ElapsedMilliseconds < 5000) Thread.Sleep(20);
result.TreeEmpty = ActiveCount(job) == 0;
```

`ActiveCount` 取自 `JobObjectBasicAccountingInformation.ActiveProcesses`（第 105 行）。
没有逐 PID 比对进程创建时间，也没有 `UniqueProcessId` 复用检测。

同一文件第 178 行的注释写明该设计放弃 PID 复用判定：

> no name scans, global Dart kills, guessed ancestry or reused PIDs

`controls/orphan.json` 也没有任何字段断言某个 PID 已消失。
`observedProcessIds` 是 4 个 PID 的记录，`residualCleanup: true` 与 `treeEmpty: true` 只证明 Job 归零。

建议：README 改成「确认 Job 活跃进程归零且根进程已退出，清理限 5 秒」。删掉 identity 一词。

### 1.2 README 未提 `embeddedSigningConfigurationCopied`

`prepare_json_ohos_inputs.py:507` 硬编码：

```python
"embeddedSigningConfigurationCopied": True,
```

`preflight.json` 同名字段可查：`embeddedSigningConfigurationCopied: True`，`credentialPathsExcluded: []`。
`exclusionPolicy` 只写 `standalone credential files`。

`files` 集合里有 `app/ohos/build-profile.json5`，sha256 为 `9361a0f9…2c1eb6`。
该文件含明文 `storePassword` 与 `keyPassword`，以及 `.cer`、`.p7b`、`.p12` 绝对路径。

风险边界要说清：`files` 每个条目的值只有 `bytes` 与 `sha256`，research 目录的 JSON 不含密码明文。
但隔离副本确实带上明文签名配置，README 一字未提。

建议：README 增加一句。写清隔离副本含明文签名配置，且不据此宣称可签名构建。

### 1.3 两处 `runners` 键式不同，机械比对必然不等

`identities.json` 用文件名加 `{sha256, bytes}`：

```json
"run_json_ohos_window.ps1": {"sha256": "aa0af8de…3df3", "bytes": 10107}
```

`preflight.json` 来源的 `after.json` 用无扩展名键加 `{path, bytes, sha256}`：

```json
"run_json_ohos_window": {"path": "D:\\…\\.runtime\\run_json_ohos_window.ps1", "bytes": 10107, "sha256": "aa0af8de…3df3"}
```

按内容逐项比对，7 个哈希全部相等。
按结构直接相等，结果为 `False`。

后果：任何脚本化的交叉校验都会报不一致，掩盖真实不一致。

建议：两份证据统一键名与字段集。

### 1.4 `identities.json` 要求设备授权，与 scope 冲突

`identities.json:remaining`：

> Fresh named SDK grant and separate assigned device grant required

同文件 `scope` 写 `no SDK/device acceptance`。
README 写 `A NEW named serial grant and explicit successor are still required`，未提设备。
`command-template.json:scope` 写 `no device`。

四处口径不一。按 scope 的表述，本批不需要设备授权。

建议：删掉 `remaining` 里的设备授权一句，或改 scope。二者不可并存。

### 1.5 `command-template.json` 的 `-GrantEvent` 无法绑定

模板取值：

```json
"-GrantEvent", "<NEW-named-grant-event>"
```

`run_json_ohos_window.ps1:4` 声明 `[Parameter(Mandatory=$true)][int]$GrantEvent`。
占位串无法转换成 `Int32`，参数绑定阶段即失败。
5 个控制用例全部用 `grant: 777`。

同时 `identities.json` 称其为 `named` grant，与 `[int]` 类型冲突。

建议：占位改成 `0`，并在模板里注明必须替换为真实整数事件号。删掉 `named` 一词。

### 1.6 README 的 `defer` 与实际记录不符

README：

> A short window may defer validation before launch.

`controls/insufficient-budget.json`（`maxSeconds: 90`）实际记录：

- `exit: 1`
- `finalGatePassed: false`
- `error` 含 `Too little budget remains to start validation.`
- `rows` 只有 `acceptance` 与 `final-relay`，无 `validation`

`defer` 读起来是中性的延期，记录写的是失败。
另外该用例反证：`MaxSeconds` 取 90 至 134 时永远起不了校验，可用下界是 135。

建议：README 改成「预算不足时在校验启动前即判失败」，并补可用下界 135。

---

## 2. 已校验为一致的部分

**7 个 runner 哈希全等。** `runners/` 与 `.runtime/` 两处副本逐字节相同，且与 `identities.json` 全等：

| 文件 | 字节 | sha256 前缀 |
| --- | --- | --- |
| `run_json_ohos_window.ps1` | 10107 | `aa0af8de` |
| `run_json_ohos_release.ps1` | 14578 | `8ee89a44` |
| `json_hvigor_phase.ps1` | 294 | `85477722` |
| `prepare_json_ohos_inputs.py` | 26442 | `8ef4f2f4` |
| `inspect_json_release_hap.py` | 14684 | `94171703` |
| `json-bounded-process.cs` | 13034 | `6657cffb` |
| `run_json_window_controls.py` | 5597 | `6f93671a` |

**源快照前后全等。** `before.json` 与 `after.json` 的 `files` 映射逐项相等，均为 804 条。
`after.json.differences` 九个类别均为空，`repositoriesChanged` 为空。
两者文件摘要不同（`5fd170a3…` 对 `9615c229…`），原因是 `after.json` 多出 `beforeIdentity`、`differences`、`repositoriesChanged` 三个键。不是源变更。

**负向控制生效。** `changed-tool.json` 摘要 `56a4d62a…`，差异为 `tools/changed` 类别新增一条：`added: ["negative-control"]`，退出码 1。说明比对器能发现改动。

**观察者副本只差 10 行。** 5 个 `observer-copy.ps1` 与冻结脚本的 `difflib` 差异都是 10 行，且只落在两处：`$jsonWindowChildScript` 赋值，以及 `Invoke-JsonWindowMessage` 整个函数体。README 的「Only the SDK child and transport bindings change」成立。

**控制记录的身份路径与代码一致。** `identities` 恰为 5 条：观察者副本、`fake-child.ps1`、`.runtime/json-bounded-process.cs`、`ohos-final-preparation-20261024.json`、`pwsh.exe`。与脚本的 `$jsonWindowIdentityPaths` 同集合。

**预算公式与记录一致。** `normal.json` 的 `waitMilliseconds: 207718` 对应 `-MaxSeconds 197`。`orphan.json` 的 `209293` 对应 `199`。均符合 `floor(mainWait/1000)-10`。

**失败仍归还资源。** `failed-child`、`insufficient-budget`、`failed-acceptance` 三条均为 `handoffReady: true` 加 `finalGatePassed: false`，`handoffMeaning` 为 `ownership only; not runtime acceptance`。与 root 决策一致。

---

## 3. 次要问题

**`childBudget` 字符串缺空格。** `command-template.json` 写作 `reserve is30s; child has its own50s cleanup reserve`。另漏了子进程多扣的 10 秒。

**多个证据指向未跟踪目录。** `identities.json:controlsSource` 与 `preflight.json:captureDirectory` 都指向 `build/` 下路径。`**/build/` 在 `.gitignore:36`，`git ls-files` 确认未跟踪。新克隆无法复核这两处。

**`controls/summary.json` 与 `preflight.json` 的 `processControls` 完全重复。** 同一份 5 条记录存两份，改动易失同步。

---

## 4. 未核实的部分

以下只在合成控制下成立，真实构建未验证：

- 真实 Hvigor 构建 240 秒总预算是否够用。
- `trellis channel send` 的真实时延。5 个控制用例把整个传输函数替换成 `-File fake-relay.ps1`，`-EncodedCommand` 的 base64 编码路径一次也未执行。
- Job 清理 5 秒上限在真实构建树下的余量。
- `4MB` 子结果上限对真实 HAP 的余量。

第 2 项建议单独补一个不联网的编码往返测试。
