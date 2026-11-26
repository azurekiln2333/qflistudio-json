# native 第二轮窗口 —— 只读终审

审查对象（冻结版本，未改动）：

| 文件 | 实际字节 SHA-256（本次实测） | 字节 / 行 | 状态 |
| --- | --- | --- | --- |
| `.trellis/.runtime/run_json_ohos_window.ps1` | `aa0af8de601453cb089fc6dcc8cca2a160dac667f08dfafe8221833310fe3df3` | 10107 / 106 | 未变 |
| `.trellis/.runtime/run_json_ohos_release.ps1` | `0db96b75a97d58b2e7ad11eed7243246a402ea74eac3482859b3fdd15fb77e65` | 14683 / 176 | 已变（见更正记录） |
| `.trellis/.runtime/json-bounded-process.cs` | `6657cffb8a9e4ac741f7143d1d771ae8631c649f9227aa0679a5e0e6e0aa5919` | 13034 / 213 | 未变 |
| `.trellis/.runtime/prepare_json_ohos_inputs.py` | `890f10ac5820420445fe663f8ca7c317f875962498155dcc285f85935d2695d1` | 29175 / 587 | 已变（见更正记录） |
| `.trellis/.runtime/json_hvigor_phase.ps1` | `85477722f652ae60203f69aa1842c3aa2bb718c6a73a94a8c1060f722a02c3c0` | 294 / 7 | 未变 |
| `.trellis/.runtime/inspect_json_release_hap.py` | `7be9dc50d9e5841939750a097fb9351c33fc4c21ee4f32477a4021d7a1119772` | 25745 / 484 | 已变（本次未审内容） |

依据：`.trellis/spec/json-offline.md` 第 3 节与第 7 节「Offline device-evidence and host-window boundaries」。

方式：只读。读取脚本与规格，比对文件哈希，用小型 Python 读取两份 manifest。未执行 SDK、Hvigor、Flutter、hdc、设备、构建。未 commit。未改任何冻结脚本。

---

## 结论

**无阻断问题。**

四条轴线均符合规格。其中第 4 条须按更正后的口径理解：240 是参数上限，不是运行期硬上限。发现 4 项低严重度与 2 项信息级问题。这些都 fail-closed，不会产生假通过。

第二轮窗口有两处实质改进，正好对应 703 的失败模式：

1. `run_json_ohos_window.ps1:75` 要求 `artifacts` 恰为 2 项。这排除了「只跑 harness 就通过」。
2. `run_json_ohos_release.ps1:123` 要求 `sourceDrift` 为 0。这排除了带着漂移收尾。

---

## 更正记录（本次按实际字节重核）

上一版使用了陈旧身份，并有一处表述过强。本次逐条重核。

| 文件 | 上一版写法 | 实际字节现在 | 处理 |
| --- | --- | --- | --- |
| `run_json_ohos_release.ps1` | `FC245197...` | `0db96b75...` | 全部引用行号按新字节重核，结果一致 |
| `prepare_json_ohos_inputs.py` | `8EF4F2F4...`，写作「未变」 | `890f10ac...` | 「未变」判断错误。行号已改为 443-478、558、572、579 |
| `inspect_json_release_hap.py` | 未列 | `7be9dc50...` | 本报告未审其内容，仅记录身份 |

三次测量均一致的文件：`run_json_ohos_window.ps1`（`aa0af8de...`）、`json-bounded-process.cs`（`6657cffb...`）、`json_hvigor_phase.ps1`（`85477722...`）。

archive 校验：`.trellis/tasks/10-22-offline-json-ide/research/native-retry-20261026/runners/` 下三个脚本与当前字节逐一相符。

| 副本 | 归档 SHA-256 | 当前 SHA-256 | 相符 |
| --- | --- | --- | --- |
| `run_json_ohos_release.ps1` | `0db96b75...` | `0db96b75...` | 是 |
| `run_json_ohos_window.ps1` | `aa0af8de...` | `aa0af8de...` | 是 |
| `prepare_json_ohos_inputs.py` | `890f10ac...` | `890f10ac...` | 是 |

归档副本可用于复核。已变的两个脚本由他人编辑，非本次审查所为。本报告全部结论基于本表所列的实际字节。

另一处更正：「240 秒上限无法被突破」过强。详见第四节。

---

## 一、四条轴线符合性

### 1. SDK 前守卫 —— 符合

守卫全部位于首次 hvigor 调用之前。首次 hvigor 调用在第 93 行。

| 顺序 | 行号 | 守卫内容 |
| --- | --- | --- |
| 1 | `release:53` | `$jsonPrepared.prepared -ne $true` 即抛 `Native snapshot was not prepared.` |
| 2 | `release:86` | `capture-before` 阶段。带 `--expected-prepared` 与 `--runner`/`--tool` 身份参数 |
| 3 | `release:89` | 输出 HAP 已存在即抛 `Isolated output HAP already exists. Preserve it before a new validation window.` |
| 4 | `release:93` | 首次 hvigor 调用 |

第 2 步是真正的身份闸门。`prepare_json_ohos_inputs.py:443-478` 的 `readiness_mismatches()` 对 18 个键做全等比较，其中包含 `files`、`cacheReferences`、`tools`、`helperIdentity`、`exclusionPolicy`。任一不符即置 `readiness_failed`（第 558 行）。同文件第 572 行把它并入 `changed`，第 579 行 `return 1 if changed else 0`。

该脚本以退出码 1 结束。`release:37` 见非零退出码即抛 `Native capture-before phase failed; later build phases unrun.`。故凭据或源码在 SDK 启动前已被拦截。

`:89` 的 HAP 守卫依赖第 88 行定义的路径，即 `$jsonPrepared.appRoot` 下的 `entry-default-unsigned.hap`。该守卫在第 90 行的构建循环之外，也在循环之前。

### 2. terminal 与 Job 保留 —— 符合

观察器不依赖子进程的自我声明。它用作业对象跟踪整棵树。

| 行号 | 内容 |
| --- | --- |
| `window:31` | `BoundedProcess::Run` 记录根进程与全部后代 `ObservedProcessIds` |
| `window:62` | `validation` 行即子发布运行器，仍走同一 `Run` |
| `window:65` | `$validation.treeEmpty -ne $true` 即抛 `... remains unconfirmed; HOLD.` |
| `window:75` | `childGatePassed` 要求该行 exit 0、treeEmpty、未超时、无错误 |
| `window:91` | 交接文本声明「wrapper/root 及全部后代 Job（含 pending publisher）已 terminal+active0」 |

该声明有据。子树的空状态由第 65 行实测确认，不是自述。

发布运行器自身也在收尾处坚持同一标准：`release:130` 检查 `capture.treeEmpty`，`release:151` 检查 publication 树，`release:152` 两者任一不满足即抛 `Automatic release publisher unconfirmed.`。

规格要求「观察器必须保留真实 validation 根/Job，并等待 terminal 加空」已满足。

### 3. 同一次调用内交接 —— 符合

验收、等待、清理、交接都在同一个 `try`/`finally` 内，共用 `$jsonWindowClock` 与 `$MaxSeconds`。

| 阶段 | 行号 | 预算 |
| --- | --- | --- |
| acceptance 消息 | `window:54` | 5000 ms |
| validation 子进程 | `window:57-62` | `mainWait = (MaxSeconds-30)*1000 - elapsed` |
| final-relay 消息 | `window:89-94` | `min(5000, MaxSeconds*1000 - elapsed - 11000)` |

`:59` 在预算不足 90 秒时直接抛 `Too little budget remains to start validation.`。`:89` 在交接预算不为正时抛 `No bounded final-relay budget remains; manual handoff required.`

规格要求「A message sent during publication cannot prove its own final exit」已满足。`:91` 的交接文本明确写「This relay is coordination only」与「Final window budget/pass verdict is ONLY in the completed result.json」。每条消息的退出码由 `Test-JsonWindowRow` 实测确认，不靠文本自证。

所有权与验收已分离。`:15` 定义 `handoffReady` 与 `handoffMeaning='ownership only; not runtime acceptance'`。`:94` 仅在交接实测成功后置 `handoffReady=$true`。`:100` 的 `finalGatePassed` 另需 `exit -eq 0`、`childGatePassed`、非超预算三项。`:87` 在 `terminal` 为假时整段跳过交接，符合「未知或存活的归属须 HOLD」。

失败时释放空树也成立。`release:140` 的 disposition 为 `RELEASE_PENDING_PUBLISHER; NO_SUCCESSOR_GRANT`。

### 4. max240 —— 参数上限符合，运行时上限须由完成记录确立

| 行号 | 内容 |
| --- | --- |
| `release:6` | `[ValidateRange(90,240)][int]$MaxSeconds=240` |
| `window:6` | 同上 |
| `window:58` | `$childMax = floor($mainWait/1000) - 10`，最大值 200，落在子脚本合法区间 |
| `window:98` | `budgetExceeded` 实测超出即置位 |
| `window:100` | `budgetExceeded` 参与 `finalGatePassed` |
| `release:164` | 子级同样实测并置位 |

父级传给子级的 `MaxSeconds` 不超过 200。子级再按 `workCutoffSeconds=$MaxSeconds-50` 与 `cleanupReserveSeconds=50` 分配。

更正（原表述过强）：**240 秒不是运行期硬上限。实际耗时是否越界，只能由完成记录确立。** 依据如下：

- `MaxSeconds` 只受 `[ValidateRange(90,240)]` 约束。那是参数校验，不是运行期计时器。
- 第 32 行按 `min(阶段上限, 截止余量)` 计算等待。它只约束「阶段开始时」的余量。
- 收尾阶段用固定上限，与剩余预算无关。`release:111` 的 capture-after 为 7000 毫秒，`release:149` 的 publication 为 5000 毫秒。
- 阶段超时后，`BoundedProcess` 还需杀树与回收。这段耗时计入实际时间，但不计入阶段上限。
- `budgetExceeded` 在 `release:164` 与 `window:98` 于工作完成后才测量。它是事后判定，不是事前阻断。

因此可能发生的情况是「实际耗时越界」。脚本对此的处理是置 `exit=1` 并令 `finalGatePassed=false`。越界不可能以通过结束。

权威边界只有一条：完成记录里的 `elapsedSeconds` 与 `budgetExceeded`。验收时须以该记录为准。不得用「上限 240」推定未超时。

---

## 二、发现（按严重度）

### F1 —— 低 —— 阶段上限之和大于工作截止

文件：`run_json_ohos_release.ps1`
行号：`14`（`workCutoffSeconds=($MaxSeconds-50)`）、`33`、`86`、`90-99`

两个 mode 的阶段申请上限合计为 12 + 100 + 10 + 100 + 10 = 232 秒。工作截止为 `MaxSeconds-50`，在 240 秒下即 190 秒。

`Invoke-JsonNativePhase` 第 32 行按 `min(cap, 截止余量)` 取用，故不会越界。但上限之和大于截止，意味着 harness 构建若用满 100 秒，normal 两个阶段只能分到约 68 秒。

后果是第二 mode 可能饿死，抛 `Native shared host work deadline exhausted.`（第 33 行）。该文案读起来像预算耗尽，实际可能是单阶段耗时过长。

不产生假通过。记录仍为 `exit=1`。建议把各阶段上限之和压到工作截止以内，或在错误文案中区分「预算不足」与「单阶段超限」。

### F2 —— 低 —— 参数下限允许必定失败的授权

文件：`run_json_ohos_window.ps1`
行号：`6`、`54`、`57-59`

第 6 行允许 `MaxSeconds` 取 90 至 240。第 57 至 58 行推得 `childMax = MaxSeconds - 40`。第 59 行要求 `childMax >= 90`。

故 `MaxSeconds` 落在 90 至 129 时必然抛出 `Too little budget remains to start validation.`。

关键点：第 54 行的 acceptance 消息在此之前已经发出。于是该区间的授权会先公布 `JSON ACCEPT fresh grant...`，再中止，不执行任何验证。

不产生假通过（`exit=1`、`handoffReady=false`），但会在频道留下「已接受」却「未验证」的记录。建议把第 6 行下限提到 130，或在第 54 行之前先做预算校验。

### F3 —— 低 —— 结果落盘失败时预算结论缺省为假

文件：`run_json_ohos_release.ps1`
行号：`14`、`131-137`、`164`

`budgetExceeded` 初始值为 `$false`（第 14 行）。唯一的赋值在第 164 行，位于 `if($jsonReady -and $jsonPublicationAllowed)` 之内。

若发布前的保存失败，第 131 行置 `$jsonPublicationAllowed=$false`，第 165 行起的整块被跳过。第 164 行永不执行，`budgetExceeded` 停在其初始 `$false`。

规格第 7 节要求「Check the completed record for the final budget verdict」。在该路径下，完成记录会低估耗时越界。

不产生假通过，因为第 135 行已强制 `exit=1` 并要求 HOLD。建议在 `finally` 顶层无条件计算 `budgetExceeded`，与 `window:98` 的做法保持一致。

### F4 —— 信息 —— 跨 mode 的旧 HAP 复用只被间接拦截

文件：`run_json_ohos_release.ps1`
行号：`88-89`、`90`、`94`、`102`

`$jsonHap` 在两种 mode 下是同一个路径（第 88 行）。第 89 行的守卫只在构建循环之前生效。循环内 normal 构建直接覆盖该路径。

证明 normal 产物新鲜的只有两条间接证据：第 94 行要求日志含 `BUILD SUCCESSFUL`，第 102 行要求两次 `kernelSha256` 不同。

若某次 repackage 静默无操作，只有 kernel 相同才会被发现。这足以 fail-closed，但依赖单一信号。

建议在第 99 行之后显式断言两次 `--copy-to` 的 HAP 文件哈希不同。这样「新鲜」成为直接事实，不再靠推得。

### F5 —— 信息 —— 观察器身份集合只覆盖五个路径

文件：`run_json_ohos_window.ps1`
行号：`50`、`71`

第 50 行的 `$jsonWindowIdentityPaths` 含 window 脚本、child 脚本、`json-bounded-process.cs`、prepared manifest、`pwsh.exe`。不含 `inspect_json_release_hap.py`、`prepare_json_ohos_inputs.py`、`json_hvigor_phase.ps1`。

这三者由子级在第 58 至 60 行记录进 `runnerHashes`，并经 `capture-before`/`capture-after` 的 `--runner` 参数比对。其漂移会以 `child.sourceDrift` 的 `runners` 分类出现，而非 `identityDrift`。

防护是完整的，但分散在两份记录里。第 75 行同时要求两者为空，故不影响判定。记录此点便于日后核对时知道去哪一份找证据。

### F6 —— 低 —— 漂移判定的声明边界

文件：`run_json_ohos_release.ps1`（第 123 行门禁）与 `build/ohos-initialized-preparation-20261026.json`

第 123 行要求 `sourceDrift` 为 0。该门禁在第二轮可以满足，因为基线等于 703 构建后的状态。

实测依据：

| 项 | 新 manifest 基线值 | 703 `source-after.json` 值 |
| --- | --- | --- |
| `nativePlugins/.../ohos/BuildProfile.ets` | `89c1631c...1754ec` | `89c1631c...1754ec` |
| `app/ohos/entry/oh-package-lock.json5` | `cbcad7e0...` | `cbcad7e0...` |
| `app/ohos/oh-package-lock.json5` | `afefb3b8...` | `afefb3b8...` |
| `nativeCache/oh_modules/.ohpm/lock.json5` | `272716d0...` | `272716d0...` |
| `nativePlugins/.../ohos/oh-package-lock.json5` | `62a44e1d...` | `62a44e1d...` |
| `cacheReferences` 条数 | 7 | 7 |

`files` 共 805 项，与 703 构建后一致。`exclusionPolicy` 排除 `build`、`.hvigor`、`entry/libs`、`flutter_assets`、`BuildProfile.ets`、`rawfile/buildinfo.json5` 与凭据。

由此得出口径结论：`sourceDrift == 0` 的含义是「相对 703 构建后快照无变化」，不是「干净树构建」。

这一点已在 manifest 中披露：`snapshotState='initialized isolated snapshot; failed grant703 not acceptance'`、`snapshotContainsPriorBuildIntermediates=true`、`initializationGatePassed=false`、`buildExecutedDuringThisCapture=false`。`diagnosticHap` 记录旧 HAP 归档哈希 `df170f25...` 与大小 124516943。

故不构成虚假声称，但任何「干净构建」「全新快照」的措辞都无据。建议验收结论固定使用「相对初始化基线无漂移」。

补充：`snapshotContainsPriorBuildIntermediates`、`initializationGatePassed`、`initializedByGrant`、`snapshotState`、`diagnosticHap`、`preparedOrigin` 六个字段未被任何运行期脚本产生或消费。它们是写入 manifest 的外部信息。故它们只能作文档，既不强制也不弱化。

补充：manifest 的 `beforeIdentity` 为 `ec94cdc3...`（248643 字节），不是 703 的 `6814b767...`（248184 字节）。manifest 未记录 `expectedPreparedIdentity` 与 `readinessMismatches`，说明它自身生成时未做就绪比对。它是基线，不是被校验对象，逻辑上成立。

---

## 三、本次未审查

- `json-bounded-process.cs` 的内部语义。`TreeEmpty`、`ResidualTreeTerminated`、`Error` 的精确判定条件未展开。两份脚本的全部终态判定都依赖它。该文件哈希未变。
- `inspect_json_release_hap.py` 的检查内容。仅确认第 95 行向它传入 `--prepared`，以及第 98 行要求 `passed -eq $true`。
- 实际执行。未做任何一次真实运行，故所有结论来自静态阅读与既有证据比对。

---

## 四、未改动与未执行

未修改两份脚本或任何冻结文件。未改动 `lib/`、`test/`、`tool/`、core 或签名配置。未执行 SDK、Hvigor、Flutter、hdc 与设备操作。未构建。未 commit，未 push。
