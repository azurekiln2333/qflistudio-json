# 窗口观察器审查（只读）

范围：`.trellis/.runtime/run_json_ohos_window.ps1` 与子脚本 `run_json_ohos_release.ps1`。
方法：静态阅读。未执行脚本，未跑构建，未接设备。

结论：等待顺序与预算分配成立。有 1 项阻断缺陷：失败路径仍广播 RELEASE。另有 3 项精密度缺陷与 2 项隐式不变量。

---

## 1. 阻断项：失败仍广播 RELEASE

`run_json_ohos_window.ps1:86`：

```powershell
if($saved -and $jsonWindowRecord.terminal){
```

该条件只看「进程已收尾」，不看「校验是否通过」。`$jsonWindowRecord.exit` 与 `childGatePassed` 都不参与判定。

后果一：子进程判失败但仍收尾干净时，窗口照发 `TERMINAL RELEASE`。
触发路径举例：

- `child.exit=1`，原因是 `sourceDrift` 非空。
- `childGatePassed=false`，第 74 行。
- 第 75 行抛出异常，`catch` 置 `exit=1`。
- `finally` 第 80 行算出 `terminal=true`。
- 第 86 行条件成立，第 90 行发出 `FINAL VALIDATION TERMINAL RELEASE`。

同一段文本里写着 `GateExit=1, childGatePassed=False`，开头却是 `TERMINAL RELEASE`。后继方若只读关键词，会当成放行。

后果二：验收消息发送失败时，校验根本没启动，窗口仍发 RELEASE。
第 55 行抛出后，`validation` 行不存在，`rows` 只有 `acceptance` 行且 `treeEmpty=true`，`terminal` 仍为 `true`。

后果三：第 93 行无条件置 `handoffReady=$true`。失败执行也会留下 `handoffReady=true` 与 `exit=1` 并存的记录。

建议：按结果选词，不要按结果决定是否发送。
`$jsonWindowRecord.exit -eq 0 -and $jsonWindowRecord.childGatePassed` 成立时发 `TERMINAL RELEASE`。
不成立时改发 `TERMINAL HOLD`，并在同一条消息里写明 `GateExit` 与失败原因。
`handoffReady` 只在放行分支置真。失败分支另记 `holdReady`。

---

## 2. 精密度缺陷

### 2.1 预算判定排在 relay 之后

第 86 至 94 行先发消息，第 97 行才算 `budgetExceeded`。
第 98 行把 `exit` 改成 1 时，RELEASE 消息已经出网，收不回来。

建议：把第 97 行的判定上移到第 86 行之前。
超预算时跳过 relay，直接写 `HOLD`。

### 2.2 `MaxSeconds` 下界 90 不可达

第 6 行声明 `ValidateRange(90,240)`。
第 59 行要求 `childMax -ge 90`。
`childMax = floor(mainWait/1000) - 10`，`mainWait = (MaxSeconds-30)*1000 - elapsed`。
代入 `elapsed≈5`：需要 `MaxSeconds >= 135`。

即 `MaxSeconds` 取 90 至 134 时，窗口必然抛 `Too little budget remains to start validation.`。
声明下界与实际可用下界差 45 秒。

建议：把 `ValidateRange` 下界改成 135，或把第 59 行的门槛改成随 `MaxSeconds` 推导。

### 2.3 超时子进程异常文本错标

子进程超时时不会执行到 `Write-Host "JSON OHOS result=..."`（第 174 行）。
于是 `validation.log` 里没有 marker，第 66 行抛 `Missing or ambiguous child result path.`

真实原因是超时，文本说的是「缺路径」。
第 64 行只校验 `treeEmpty`，未先校验 `$validation.timedOut`。

建议：第 64 行之前加一次 `timedOut` 判定，抛 `Child validation timed out`。

---

## 3. 隐式不变量

### 3.1 窗口不直接校验 publication

第 74 行的门槛不读 `$child.publication`。
放行依赖一条推理：`child.exit=0` 意味着发布成功。
该推理成立，因为发布失败在子脚本第 158 至 170 行一律置 `exit=1`。
但推理藏在两个文件之间，窗口一侧没有断言。

建议：门槛里补 `$child.publication.treeEmpty -eq $true`，把推理写成显式断言。

### 3.2 子进程结果上限 4MB

第 72 行拒绝超过 4MB 的子结果。
子结果含两份 artifact 的 `entries` 与 `sourceDependencies`。
调试 HAP 约 100 个文件时远低于上限。资源变多后可能触顶，届时会报「超限」而非「证据不全」。

建议：把上限写进常量并注明推导依据。

---

## 4. 已校验为正确的

**等待顺序。** 第 62 行 `Invoke-JsonWindowOwned 'validation'` 返回时，C# `BoundedProcess::Run` 已完成根进程等待与 Job 清理。第 64 行再查 `treeEmpty`。第 80 行用全部行重算 `terminal`。第 86 行才发 relay。顺序符合「先等根与全部 Job 退出，再 relay」。

**嵌套 Job 覆盖发布进程。** 子进程的发布器由子进程内的 `BoundedProcess::Run` 创建，属窗口 Job 的子 Job。窗口 Job 的 `ActiveProcesses` 归零即覆盖该发布器。第 90 行「including its pending publisher, are now terminal+active0」这句话成立。

**预算分配。** 取 `MaxSeconds=240`、验收耗时 5 秒：

| 项 | 值 |
| --- | --- |
| `mainWait` | 约 205000 毫秒 |
| `childMax` | 195 秒 |
| 子进程工作截止 | 145 秒（`MaxSeconds-50`） |
| 子进程尾部 | 上限 42 秒（10+17+15） |
| 窗口 relay 等待 | 5000 毫秒 |
| 合计 | 约 215 秒 |

窗口留 30 秒，子进程留 50 秒，两处预留都在实际耗时之前扣除。cleanup 与 publication 都落在预留段内，未侵占工作段。

**返回值与输出。** 三个函数都只返回行对象，赋值语句不产生额外管道输出。`Test-JsonWindowRow` 的 `-and` 与 `-eq` 优先级正确。第 66 行正则锚定首尾，`LIVE` 行不匹配，`Count -ne 1` 拒绝零条与多条。`$childPath` 与 `$allowedPrefix` 都经 `GetFullPath` 归一为反斜杠，`StartsWith` 前缀比较有效。

**身份漂移。** 第 73 行在放行前重算 5 个路径的 SHA256，第 74 行要求 `identityDrift.Count -eq 0`。

**失败不误报（除 §1）。** 子脚本第 158 行要求发布器 `RootExitCode -eq 0` 且 `TreeEmpty`。第 168 行失败时改写 `release.txt` 为 `PUBLICATION UNCONFIRMED`，并把 `exit` 置 1。窗口第 74 行要求 `artifacts` 恰好 2 份、`sourceDrift` 为空。任一不满足都不会把 `exit` 置 0。

---

## 5. 边界

本节只覆盖静态逻辑。以下未验证：

- `BoundedProcess` 在真实超时下的清理耗时是否真能落在 10 秒内。
- `trellis channel send` 的真实网络延迟。
- `4MB` 上限对真实 HAP 的余量。
- 反斜杠归一在非 Windows 主机上的行为。

阻断项只有 §1 一项。§2 三项建议同批修正。

---

## 6. root 审查决策（本节取代 §1 与 §2.1、§2.3）

### 6.1 决策一：RELEASE 语义

RELEASE 只表示「所有 owned Job 已清空」。
失败测试也必须归还资源。
RELEASE 不表示验收通过。
不得对已清空的失败测试使用 HOLD。
C 侧已按此接受 SQL590 与 SQL625。

我 §1 的「按结果选词发 HOLD」建议已撑回。RELEASE 与失败可以共存。

### 6.2 决策二：新增两个窗口字段

第 15 行新增 `handoffMeaning='ownership only; not runtime acceptance'`。
第 100 行新增 `finalGatePassed = exit==0 && childGatePassed && handoffReady && !budgetExceeded`。
最终放行判决只读 `result.json` 的 `finalGatePassed`。
第 103 行在持久化失败时把 `handoffReady` 与 `finalGatePassed` 同时置假。

### 6.3 决策三：SDK 校验退出码与窗口预算判决分开

relay 文本改称 `SDKValidationExit`。
同段加注「This relay is coordination only. Final window budget/pass verdict is ONLY in the completed result.json」。
消息超前的风险由声明消解，不再靠发送前拦截。

### 6.4 决策四：timedOut 优先诊断

第 64 行改为 `if($validation.timedOut){throw 'Child validation timed out; owned cleanup status is recorded separately.'}`。
子进程超时不再报「缺路径」。

### 6.5 对齐结果

| 本审查条目 | 状态 |
| --- | --- |
| §1 失败仍广播 RELEASE | 由 6.1 与 6.2 消解 |
| §2.1 预算判决排在 relay 之后 | 由 6.3 消解 |
| §2.3 超时文本错标 | 由 6.4 消解 |
| §2.2 `MaxSeconds` 下界不可达 | 不在本批范围，状态不变 |
| §3.1 窗口不直接校验 publication | 不在本批范围，状态不变 |
| §3.2 子结果 4MB 上限 | 不在本批范围，状态不变 |

本任务到此结束。不再扩展本报告。
