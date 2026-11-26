# native 窗口终审（更正版）—— 含保留式 HOLD 阻断

文件：`.trellis/.runtime/native-final3-window-review.md`
取代：`.trellis/.runtime/native-final2-window-review.md`

---

## 0. 边界声明（先读这一节）

**脚本层源码审查：无阻断问题。**
`run_json_ohos_window.ps1`、`run_json_ohos_release.ps1`、`prepare_json_ohos_inputs.py` 三个文件的四条轴线均符合规格。

**native 执行：未就绪（NOT READY）。**
阻断点在 `.trellis/.runtime/json-bounded-process.cs`。该 helper 的 `finally` 无条件 `CloseHandle(job)`，即使 `ActiveCount(job) != 0`、即使根进程退出未确认。作业对象以 `KILL_ON_JOB_CLOSE` 创建，故关句柄本身就会杀掉全部残留进程。

后果：`TreeEmpty=false` 时调用方声明的「保留树 + HOLD + 人工核对」无法成立。树已被销毁，没有可核对的对象。

这不是「假通过」通道。它不会产出被接受的产物。它破坏的是**证据保留**，不是门禁结论。

**修复前不得启动 native 窗口。** 修复范围仅限 helper 的保留语义。不得改动现有脚本的运行期行为来绕开。

---

## 1. 身份（本次实测字节）

| 文件 | SHA-256（实测） | 字节 | 行 | mtime | 变化 |
| --- | --- | --- | --- | --- | --- |
| `.trellis/.runtime/json-bounded-process.cs` | `6657cffb8a9e4ac741f7143d1d771ae8631c649f9227aa0679a5e0e6e0aa5919` | 13034 | 213 | 2026-10-24 07:07:14 | 未变（含阻断缺陷） |
| `.trellis/.runtime/run_json_ohos_window.ps1` | `aa0af8de601453cb089fc6dcc8cca2a160dac667f08dfafe8221833310fe3df3` | 10107 | 106 | 2026-10-26 03:39:23 | 未变 |
| `.trellis/.runtime/run_json_ohos_release.ps1` | `0db96b75a97d58b2e7ad11eed7243246a402ea74eac3482859b3fdd15fb77e65` | 14683 | 176 | 2026-10-26 07:37:18 | 已变 |
| `.trellis/.runtime/prepare_json_ohos_inputs.py` | `890f10ac5820420445fe663f8ca7c317f875962498155dcc285f85935d2695d1` | 29175 | 587 | 2026-10-26 07:39:25 | 已变 |
| `.trellis/.runtime/json_hvigor_phase.ps1` | `85477722f652ae60203f69aa1842c3aa2bb718c6a73a94a8c1060f722a02c3c0` | 294 | 7 | 2026-10-24 12:18:24 | 未变 |
| `.trellis/.runtime/inspect_json_release_hap.py` | `7be9dc50d9e5841939750a097fb9351c33fc4c21ee4f32477a4021d7a1119772` | 25745 | 484 | 2026-10-26 07:29:29 | 已变（本次未审内容） |

archive 校验：`research/native-retry-20261026/runners/` 下的 `run_json_ohos_release.ps1`、`run_json_ohos_window.ps1`、`prepare_json_ohos_inputs.py` 与当前字节逐一相符（`0db96b75...`、`aa0af8de...`、`890f10ac...`）。

方式：只读。读取脚本、helper 与规格，比对哈希，用小型 Python 读取 manifest。未执行 SDK、Hvigor、Flutter、hdc、设备、构建、编译。未 commit。未改任何脚本或 core。

---

## 2. B1 —— 阻断 —— helper 保留式 HOLD 未实现

文件：`.trellis/.runtime/json-bounded-process.cs`（`6657cffb...`）

### 声明

`json-bounded-process.cs:159-161` 的注释声明：

> `// A termination request is not proof of exit. Stop the`
> `// observation loop at the same deadline even if Windows`
> `// cannot terminate/signal the root; finally performs only`
> `// bounded cleanup and leaves TreeEmpty false if unconfirmed.`

「leaves TreeEmpty false」意为把未确认的树留在原地。规格第 7 节要求一致：观察器必须保留真实 validation 根/Job，并等待 terminal 加空。未知或存活的归属须 HOLD 并核对。

### 实际行为

`json-bounded-process.cs:127`：

```csharp
ExtendedLimit limit = new ExtendedLimit(); limit.Basic.Flags = 0x2000; // KILL_ON_JOB_CLOSE; no BREAKAWAY_OK
```

`0x2000` 即 `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`。关掉作业句柄时，内核终止作业内所有剩余进程。

`json-bounded-process.cs:177-191`：

```csharp
} finally {
  ...
  if (job != IntPtr.Zero) {
    TerminateJobObject(job, result.TimedOut ? 124u : 125u);
    Stopwatch cleanup = Stopwatch.StartNew();
    try {
      while (ActiveCount(job) != 0 && cleanup.ElapsedMilliseconds < 5000) Thread.Sleep(20);
      result.TreeEmpty = ActiveCount(job) == 0;
    } catch (Exception exception) { result.Error = exception.Message; }
    CloseHandle(job); job = IntPtr.Zero;      // 第 191 行：无条件
  }
```

第 188 行最多等 5000 毫秒。第 189 行记录 `TreeEmpty`。第 191 行无条件关闭句柄，没有 `if (!result.TreeEmpty)` 保护，也没有 `if (ActiveCount(job) == 0)` 保护。

### 三条推导

1. `ActiveCount(job) != 0` 时，第 189 行记 `TreeEmpty=false`。紧接着第 191 行关闭句柄。因 `KILL_ON_JOB_CLOSE`，残留进程在此刻被内核终止。树没有留在原地。
2. 因此调用方的 HOLD 分支没有核对对象。`release:37` 见 `!$jsonRun.TreeEmpty` 即抛 `Native $Name phase failed; later build phases unrun.`。`window:65` 见 `!$validation.treeEmpty` 即抛 `... remains unconfirmed; HOLD.`。两处都要求人工核对一棵已经被杀掉的树。
3. `window:91` 的交接文本声明「Retained validation wrapper/root and all its descendant Jobs, including its pending publisher, are now terminal+active0」。该声明只在 terminal 为真时发出，故文本本身不假。但「retained」这一前提由 helper 负责，而 helper 做不到。全部阶段（含 publication 发布器）都经 `BoundedProcess::Run`，故发布器同样不可能被保留。

### 附带损失

- **PID 证据失效。** `ObservedProcessIds` 最后刷新在第 170 行与第 163 行。第 191 行之后作业消失，PID 被系统回收。第 183-184 行注释声称「no ... reused PIDs」，但返回后的 PID 恰已可被复用。任何按 PID 的事后核对都不可靠。
- **错误路径同样强杀。** 第 188 行 `ActiveCount` 若抛异常，第 190 行只置 `result.Error`。`result.TreeEmpty` 停在默认 `false`。第 191 行仍执行。故错误路径也不保留。
- **注释与代码矛盾。** 第 161 行说「leaves」，第 191 行做的是销毁。这是意图与实现的直接背离。

### 不构成假通过

`TreeEmpty != true` 会让所有调用方置 `exit=1`。`window:100` 的 `finalGatePassed` 也因此为假。故不会有未确认的树换来一个通过结论。

危害限于：规格要求的「保留 + HOLD + 核对」能力不存在，以及 PID 类证据不可信。

### 修复方向（仅列方向，未改代码）

1. 第 191 行的 `CloseHandle` 改为有条件。仅在 `ActiveCount(job) == 0` 时执行。
2. 未确认时不要关闭句柄。把作业句柄的所有权交给调用方，或提供显式释放步骤。`KILL_ON_JOB_CLOSE` 只在确认空之后生效。
3. 为 `ProcessResult` 增加区分状态。至少区分「确认空」、「已终止但未确认空」、「已保留待核对」。调用方据此决定 HOLD 还是继续。
4. 在 `TreeEmpty=false` 的返回中保留 `ObservedProcessIds` 的最后刷新时刻，或保留作业句柄以防 PID 复用。

---

## 3. 身份更正记录

上一版（`native-final2-window-review.md`）使用了陈旧身份，并有一处表述过强。本次按实际字节重核。

| 项 | 上一版 | 实际字节 | 处理 |
| --- | --- | --- | --- |
| `run_json_ohos_release.ps1` | `FC245197...` | `0db96b75...` | 全部引用行号按新字节重核，结果一致 |
| `prepare_json_ohos_inputs.py` | `8EF4F2F4...`，写作「未变」 | `890f10ac...` | 「未变」判断错误。行号改为 `443-478`、`558`、`572`、`579` |
| `inspect_json_release_hap.py` | 未列 | `7be9dc50...` | 本报告未审其内容，仅记录身份 |

三次测量均一致：`json-bounded-process.cs`（`6657cffb...`）、`run_json_ohos_window.ps1`（`aa0af8de...`）、`json_hvigor_phase.ps1`（`85477722...`）。

上一版还有一处范围失误需记录。当时把 `json-bounded-process.cs` 的内部语义列为「本次未审查」。阻断缺陷 B1 正落在该文件。故上一版「无阻断问题」的结论只在三个脚本范围内成立，未覆盖 helper。脚本断言「保留」时并未验证 helper 能否兑现。

---

## 4. 四条轴线符合性（脚本层）

### 1. SDK 前守卫 —— 符合

守卫全部位于首次 hvigor 调用之前。首次 hvigor 调用在 `release:93`。

| 顺序 | 行号 | 内容 |
| --- | --- | --- |
| 1 | `release:53` | `$jsonPrepared.prepared -ne $true` 即抛 `Native snapshot was not prepared.` |
| 2 | `release:86` | `capture-before` 阶段。带 `--expected-prepared` 与 `--runner`/`--tool` 身份参数 |
| 3 | `release:89` | 输出 HAP 已存在即抛 `Isolated output HAP already exists.` |
| 4 | `release:93` | 首次 hvigor 调用 |

第 2 步是身份闸门。`prepare_json_ohos_inputs.py:443-478` 的 `readiness_mismatches()` 对 18 个键做全等比较，含 `files`、`cacheReferences`、`tools`、`helperIdentity`、`exclusionPolicy`。任一不符即置 `readiness_failed`（第 558 行）。第 572 行并入 `changed`，第 579 行 `return 1 if changed else 0`。

该脚本以退出码 1 结束。`release:37` 见非零退出码即抛。故身份或源码不符在 SDK 启动前已被拦截。

### 2. terminal 与 Job 保留 —— 脚本层符合，集成层不符合

| 行号 | 内容 |
| --- | --- |
| `window:31` | 经 `BoundedProcess::Run` 记录根与全部后代 |
| `window:62` | `validation` 行即子发布运行器，走同一入口 |
| `window:65` | `!$validation.treeEmpty` 即抛 HOLD |
| `window:75` | `childGatePassed` 要求 `treeEmpty` 等四项 |
| `window:91` | 交接文本声明保留，依据是实测空树 |
| `release:130` | 子级检查 `capture.treeEmpty` |
| `release:151` | 子级检查 publication 树 |
| `release:152` | 任一不满足即抛 `Automatic release publisher unconfirmed.` |

脚本层判定标准正确。它要求实测空，不采信自述。但它假定了 helper 会保留未确认的树。B1 说明该假定不成立。故本条在集成层不达。

### 3. 同一次调用内交接 —— 符合

验收、等待、清理、交接都在同一 `try`/`finally`，共用 `$jsonWindowClock` 与 `$MaxSeconds`。

| 阶段 | 行号 | 预算 |
| --- | --- | --- |
| acceptance | `window:54` | 5000 毫秒 |
| validation | `window:57-62` | `mainWait = (MaxSeconds-30)*1000 - elapsed` |
| final-relay | `window:89-94` | `min(5000, MaxSeconds*1000 - elapsed - 11000)` |

`:59` 预算不足 90 秒即抛 `Too little budget remains to start validation.`。`:89` 交接预算不为正即抛 `No bounded final-relay budget remains; manual handoff required.`

每条消息的退出码由 `Test-JsonWindowRow` 实测确认。`:91` 明确写「This relay is coordination only」与「Final window budget/pass verdict is ONLY in the completed result.json」。所有权与验收分离，见 `:15`、`:94`、`:100`。`:87` 在 terminal 为假时整段跳过交接。

### 4. max240 —— 参数上限符合，运行时上限须由完成记录确立

更正（原表述过强）：**240 秒不是运行期硬上限。实际耗时是否越界，只能由完成记录确立。**

- `MaxSeconds` 只受 `[ValidateRange(90,240)]` 约束（`release:6`、`window:6`）。那是参数校验，不是运行期计时器。
- `release:32` 按 `min(阶段上限, 截止余量)` 计算等待。它只约束「阶段开始时」的余量。
- 收尾阶段用固定上限，与剩余预算无关。`release:111` 的 capture-after 为 7000 毫秒，`release:149` 的 publication 为 5000 毫秒。
- 阶段超时后，helper 还需杀树与回收。这段耗时计入实际时间，不计入阶段上限。
- `budgetExceeded` 在 `release:164` 与 `window:98` 于工作完成后才测量。它是事后判定，不是事前阻断。

故可能发生「实际耗时越界」。脚本对此置 `exit=1` 并令 `finalGatePassed=false`。越界不可能以通过结束。

权威边界只有一条：完成记录里的 `elapsedSeconds` 与 `budgetExceeded`。验收须以该记录为准。

---

## 5. 低严重度与信息级发现

### F1 —— 低 —— 阶段上限之和大于工作截止

文件：`run_json_ohos_release.ps1`
行号：`14`、`33`、`86`、`90-99`

两个 mode 的阶段申请上限合计 12 + 100 + 10 + 100 + 10 = 232 秒。工作截止为 `MaxSeconds-50`，在 240 秒下即 190 秒。

`release:32` 按 `min(cap, 截止余量)` 取用，故不会越界。但上限之和大于截止，意味着 harness 构建若用满 100 秒，normal 两个阶段只剩约 68 秒。

后果是第二 mode 可能饿死，抛 `Native shared host work deadline exhausted.`（第 33 行）。该文案读起来像预算耗尽，实际可能是单阶段耗时过长。

不产生假通过。记录仍为 `exit=1`。

### F2 —— 低 —— 参数下限允许必定失败的授权

文件：`run_json_ohos_window.ps1`
行号：`6`、`54`、`57-59`

第 6 行允许 `MaxSeconds` 取 90 至 240。第 57 至 58 行推得 `childMax = MaxSeconds - 40`。第 59 行要求 `childMax >= 90`。

故 `MaxSeconds` 落在 90 至 129 时必然抛出 `Too little budget remains to start validation.`

关键点：第 54 行的 acceptance 消息在此之前已发出。该区间会先公布 `JSON ACCEPT fresh grant...`，再中止，不执行验证。

不产生假通过，但会在频道留下「已接受」却「未验证」的记录。建议把下限提到 130，或先做预算校验再发 acceptance。

### F3 —— 低 —— 结果落盘失败时预算结论缺省为假

文件：`run_json_ohos_release.ps1`
行号：`14`、`131-137`、`164`

`budgetExceeded` 初始为 `$false`（第 14 行）。唯一赋值在第 164 行，位于 `if($jsonReady -and $jsonPublicationAllowed)` 之内。

若发布前的保存失败，第 131 行置 `$jsonPublicationAllowed=$false`，其后整块被跳过。第 164 行永不执行，`budgetExceeded` 停在 `$false`。

规格第 7 节要求以完成记录确认最终预算结论。该路径下完成记录会低估越界。

不产生假通过，因为第 135 行已强制 `exit=1` 并要求 HOLD。建议在 `finally` 顶层无条件计算 `budgetExceeded`，与 `window:98` 一致。

### F4 —— 信息 —— 跨 mode 的旧 HAP 复用只被间接拦截

文件：`run_json_ohos_release.ps1`
行号：`88-89`、`90`、`94`、`102`

`$jsonHap` 在两种 mode 下是同一路径（第 88 行）。第 89 行守卫只在构建循环之前生效。normal 构建直接覆盖该路径。

证明 normal 产物新鲜的只有两条间接证据：第 94 行要求日志含 `BUILD SUCCESSFUL`，第 102 行要求两次 `kernelSha256` 不同。

若某次 repackage 静默无操作，只有 kernel 相同才会被发现。建议在第 99 行之后显式断言两个 `--copy-to` HAP 的哈希不同。

### F5 —— 信息 —— 观察器身份集合只覆盖五个路径

文件：`run_json_ohos_window.ps1`
行号：`50`、`75`

第 50 行的身份集合含 window 脚本、child 脚本、`json-bounded-process.cs`、prepared manifest、`pwsh.exe`。不含 inspect、prepare、hvigor-phase 三个脚本。

这三者由子级记入 `runnerHashes`，并经 capture 的 `--runner` 参数比对。其漂移以 `child.sourceDrift` 的 `runners` 分类出现，而非 `identityDrift`。第 75 行要求两者均为空，故判定不受影响。

### F6 —— 低 —— 漂移判定的声明边界

文件：`run_json_ohos_release.ps1`（第 123 行门禁）与 `build/ohos-initialized-preparation-20261026.json`

第 123 行要求 `sourceDrift` 为 0。该门禁可以满足，因为基线等于 703 构建后的状态。

| 项 | 新 manifest 基线 | 703 `source-after.json` |
| --- | --- | --- |
| `nativePlugins/.../ohos/BuildProfile.ets` | `89c1631c...1754ec` | `89c1631c...1754ec` |
| `app/ohos/entry/oh-package-lock.json5` | `cbcad7e0...` | `cbcad7e0...` |
| `app/ohos/oh-package-lock.json5` | `afefb3b8...` | `afefb3b8...` |
| `nativeCache/oh_modules/.ohpm/lock.json5` | `272716d0...` | `272716d0...` |
| `nativePlugins/.../ohos/oh-package-lock.json5` | `62a44e1d...` | `62a44e1d...` |
| `cacheReferences` 条数 | 7 | 7 |

`files` 共 805 项，与 703 构建后一致。`exclusionPolicy` 在第 548 行，排除 `build`、`.hvigor`、`entry/libs`、`flutter_assets`、`BuildProfile.ets`、`rawfile/buildinfo.json5` 与凭据。

口径结论：`sourceDrift == 0` 的含义是「相对 703 构建后快照无变化」，不是「干净树构建」。

已在 manifest 披露：`snapshotState='initialized isolated snapshot; failed grant703 not acceptance'`、`snapshotContainsPriorBuildIntermediates=true`、`initializationGatePassed=false`、`buildExecutedDuringThisCapture=false`。`diagnosticHap` 记录旧 HAP 归档哈希 `df170f25...` 与大小 124516943。

故不构成虚假声称。但「干净构建」「全新快照」的措辞无据。建议结论固定用「相对初始化基线无漂移」。

补充：`snapshotContainsPriorBuildIntermediates`、`initializationGatePassed`、`initializedByGrant`、`snapshotState`、`diagnosticHap`、`preparedOrigin` 六个字段未被任何运行期脚本产生或消费。它们只作文档，既不强制也不弱化。

---

## 6. 本次未审查

- `inspect_json_release_hap.py`（`7be9dc50...`）的检查内容。仅确认 `release:95` 传入 `--prepared`，`release:98` 要求 `passed -eq $true`。
- helper 的 P/Invoke 结构体布局与 `ExtendedLimit` 长度是否与 Windows 期望一致。
- 实际执行。未做任何一次真实运行。全部结论来自静态阅读与既有证据比对。

---

## 7. 未改动与未执行

未修改 `json-bounded-process.cs`、两份窗口脚本、prepare、inspect 或任何冻结文件。未改动 `lib/`、`test/`、`tool/`、core 或签名配置。未执行 SDK、Hvigor、Flutter、hdc 与设备操作。未构建，未编译。未 commit，未 push。

**修复 B1 之前，native 窗口不得启动。**