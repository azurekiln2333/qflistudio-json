# OHOS 原生发布包装器独立审查（pi）

审查时间：2026-10-26
审查范围：`.trellis/.runtime/run_json_ohos_release.ps1` 及其 helper
- `.trellis/.runtime/json_hvigor_phase.ps1`
- `.trellis/.runtime/json-bounded-process.cs`
- `.trellis/.runtime/prepare_json_ohos_inputs.py`
- `.trellis/.runtime/inspect_json_release_hap.py`

审查方式：只读。脚本保持原样，未执行 SDK / Hvigor / build / test / 设备操作，未 commit。

结论：**结构成立，未发现阻断真实构建的缺陷**。有 9 项需收紧。其中 3 项关乎真实构建，4 项是身份或隔离缺口，2 项是记录语义。无阻断项。

---

## 0. 已确认的外部前提（只读核对，未启动构建）

| 前提 | 核对方式 | 结果 |
| --- | --- | --- |
| `hvigorw.bat` 存在 | `Test-Path` | True |
| `hvigorw.js` 存在（`$(Split-Path $jsonHvigor)` 同级） | `Test-Path` | True |
| `$PSHOME/pwsh.exe` 存在 | `Test-Path` | True |
| 当前 shell 为 PS7 Core | `$PSVersionTable` | 7.6.3 / Core |
| `python`、`node` 可解析 | `Get-Command` | Python313 / nodejs |
| `DEVECO_SDK_HOME`、`HOS_SDK_HOME` 已设 | 环境变量 | 均指向 DevEco sdk |
| `ohos/node_modules`、`ohos/oh_modules`、`ohos/entry/oh_modules` 存在 | `Test-Path` | 均 True |
| `ohos/local.properties` 存在 | 读取 | `flutter.sdk`、`hwsdk.dir` 为绝对路径 |
| `build/` 被 Git 忽略 | `git check-ignore -v build` | `.gitignore:36 **/build/` |
| `.trellis/.runtime/` 被 Git 忽略 | `git check-ignore -v` | `.gitignore:96` |
| harness 的 `DART_DEFINES` 解码值 | Base64 解码 | `QFLI_VERIFY_CATALOG=true` |

`build/` 与 `.trellis/.runtime/` 都被忽略。包装器把证据写进这两处，不会污染 `repository(ROOT).status`。这一条是「前后身份比较」不自伤的必要条件，成立。

---

## 1. PowerShell 7 约束

### 1.1 双层守卫，成立

- 文件头 `#requires -Version 7.0`。
- try 内二次断言。任一条件命中即抛错：`$PSVersionTable.PSVersion.Major -lt 7`、`PSEdition -ne 'Core'`、`$PSHOME/pwsh.exe` 不存在。

`$jsonPowerShell=Join-Path $PSHOME 'pwsh.exe'` 取当前 PS7 安装目录下的 pwsh，与 `PSEdition -eq 'Core'` 一致。不会拿 Windows PowerShell 5.1 的 `powershell.exe` 混用。成立。

### 1.2 需收紧：try 之前的失败不落盘（记录缺口）

以下语句在 `try {` 之前执行，且 `$ErrorActionPreference='Stop'` 已生效：

```powershell
$jsonPython=(Get-Command python).Source
[IO.Directory]::CreateDirectory($jsonOut) | Out-Null
[IO.Directory]::CreateDirectory($jsonPackages) | Out-Null
```

若 `python` 不在 PATH，`Get-Command python` 变为终止性异常。脚本在进入 try 之前退出。此时 `result.json` 从未写出，`$jsonRecord` 也不存在。目录创建失败同理。

建议：把 `$jsonPython=(Get-Command python -ErrorAction SilentlyContinue).Source` 与两次目录创建移入 try。或在 try 之前包一层最小 catch，只写一条最小 `result.json`（含 `error`、`exit=1`）。

对照：`node` 的解析在 try 内（`(Get-Command node -CommandType Application).Source`），已被覆盖。只有 `python` 和目录创建留在外面。

### 1.3 观察：`Add-Type` 依赖的 C# 编译

`Add-Type -Path json-bounded-process.cs` 在 try 内。失败时 `$jsonReady` 保持 `$false`，final 里跳过前后捕获与 publication，但仍写 `result.json` 且 `exit=1`。成立。

---

## 2. 前后完整身份比较

### 2.1 成立的部分

`source-before.json` 与 `source-after.json` 由同一组参数产出。`$jsonCaptureIdentityArgs` 在两次调用间未变。`prepare_json_ohos_inputs.py` 的 `stable` 键强制相等：

```python
stable = ("appRoot","coreRoot","hostManifest","hostManifestIdentity",
          "coreCommit","coreTree","packageRoots")
```

`differences` 覆盖 9 类：

```text
files, cacheReferences, originalAppInputs, originalCacheReferences,
originalExecutableComparison, runners, tools, buildParameters, helperIdentity
```

加 `repositoriesChanged`（`originalApp`、`originalCore` 的 head、tree、status）。

关键点核对：

| 输入 | 是否被比较 | 说明 |
| --- | --- | --- |
| `app/lib`、`app/assets` 等冻结根 | 是（`files`） | `FROZEN_ROOTS` + `signature` |
| `app/ohos` 原生输入 | 是（`files`） | `native=True`，`generated()` 排除构建产物 |
| `ohos/oh_modules`、`entry/oh_modules`、`node_modules` | 是（`files`，`nativeCache/*`） | `cache=True` 只剪 build/.hvigor/.git |
| `native_plugins` | 是（`files`） | |
| 工作树 owned overlay | 是（`originalExecutableComparison`） | `verify_original` 对 `appCommit` 做 Git blob 比对，或对 overlay 做原始 sha256 |
| 包装器自身与 5 个 helper | 是（`runners`） | `wrapper`、`hvigorPhase`、`prepare`、`inspector`、`boundedProcess` |
| python / pwsh / hvigor / hvigorw.js / node | 是（`tools`） | |
| 两种模式的 command JSON | 是（`runners` 的 `<mode>-config` + `buildParameters`） | |
| prepare 脚本自身 | 是（`helperIdentity`） | |

`changes()` 在 Python 里做结构比较（`before[key] != after[key]`）。`buildParameters` 的嵌套 dict 不会因语言语义产生假漂移。成立。

`hostAppCommit`、`hostAppOverlays` 未进入 `stable` 或 `differences`。两者都由 `hostManifest` 派生，而 `hostManifestIdentity` 已强制相等，因此间接覆盖。可接受。

### 2.2 需收紧：Flutter hvigor 插件身份覆盖不全

`ohos/node_modules/flutter-hvigor-plugin` 是**链接**（`Mode l----`），指向 Flutter SDK。`ohos/package.json` 声明 `file:D:\ProgramFiles\flutter_ohos\packages\flutter_tools\hvigor`。

后果：

- `input_set` 走到 `nativeCache/node_modules` 时，`linked()` 为真。它只把**链接路径**写进 `cacheReferences`，不哈希其内容。
- 内容只由 `tools` 里的 4 个文件覆盖：`src/plugin/flutter-hvigor-plugin.ts`、`src/util/file-util.ts`、`src/util/parameter-util.ts`、`package.json`。
- 未覆盖：`src/util/properties-util.ts`（解析 `local.properties`）、`src/util/string-util.ts`（`toCamelCase` 决定 `intermediateDir`）、`index.ts`、`tsconfig.json`。

`properties-util.ts` 直接决定 `sdkPath` 与 engine HAR 路径。`string-util.ts` 直接决定产物目录。两者变更会改变构建结果，却不被身份比较捕获。

建议：把插件目录下全部 `.ts` 与 `.json` 纳入 `tool_identities`。或对链接目标做一次目录级清单哈希。

### 2.3 注明：身份比较的边界

比较范围是「快照输入 + 命名的 runner 与 tool + 两仓 Git 状态」。不包含 DevEco SDK、ohpm store、Java 执行环境、Flutter SDK 本体。这与脚本 `scope` 字段声明的范围一致。但报告里不要把它读成「构建可复现」。

---

## 3. publication 异常落盘

### 3.1 成立的部分

publication 块是 `try / catch / finally`：

```text
先写 publication={...started=false}，Save
置 started=true
BoundedProcess::Run
覆写 publication={...started=true}，记 pid/exit/treeEmpty/timedOut/residualCleanup/error
若 treeEmpty 非真，terminal=false
失败则 throw
catch：写 publication.error，terminal 依 started && !treeEmpty 决定，exit=1
finally：重算 finishedUtc / elapsedSeconds，Save
```

关键路径核对：

| 失败点 | publication 是否落盘 | terminal | exit |
| --- | --- | --- | --- |
| `BoundedProcess::Run` 抛异常 | 是（保留 `started=true`，补 `error`） | false（`treeEmpty` 为 null） | 1 |
| Run 返回但 `RootExitCode != 0` | 是 | 视 treeEmpty | 1 |
| Run 返回但 `TimedOut` | 是 | 视 treeEmpty | 1 |
| `Get-Command trellis` 失败 | 是（`started=false`） | 不强制 false | 1 |
| `WriteAllText(release.txt)` 失败 | 是（`started=false`） | 不强制 false | 1 |

`$jsonRecord.Contains('publication')` 分支处理成立。ordered dictionary 已含该键时只补 `error`，不重建壳子，避免丢掉已记录的 pid。

### 3.2 需收紧：`release.txt` 可能先于发送落盘

`release.txt` 的写入在 `Get-Command trellis` 之前：

```powershell
[IO.File]::WriteAllText("$jsonOut/release.txt",$jsonMessage,...)
$jsonTrellis=(Get-Command trellis -ErrorAction Stop).Source...
```

若 `trellis` 不在 PATH，或后续编码与发送失败，`release.txt` 已存在。该文件文本含 `Explicit RELEASE to <NextOwner>`。消息实际没有发出去，但磁盘上留下一个「已 RELEASE」的文件。

建议：把 `release.txt` 的写入挪到 `BoundedProcess::Run` 之前紧邻处（此时已确认 trellis 可解析）。或在 catch 里改名，追加 `UNSENT` 标记。

### 3.3 需收紧：catch 内 `Save-JsonNative` 自身失败会吞掉终局

publication 的 `finally` 调用 `Save-JsonNative`。若该写入抛异常（磁盘满、目录被删），异常从 `finally` 抛出。外层 `finally` 中断，`exit $jsonRecord.exit` 不再执行。结果：脚本以未捕获异常退出，`result.json` 停留在旧版本。

建议：`Save-JsonNative` 内部加一次 `try/catch`。失败时退到 `Write-Host` 输出关键字段（exit、terminal、error）。保证至少有一个可读的终局记录。

### 3.4 注明：`release.txt` 的 RELEASE 语义

消息文本是 `terminal exit=<n>; Explicit RELEASE to <NextOwner>`。`terminal` 只表示「本进程拥有的进程树已确认清空」，不表示构建成功。`exit` 在同一句里给出，读者可区分。这个设计成立。但报告或下游不应把 `RELEASE` 读成通过。

---

## 4. deadline

### 4.1 结构

```powershell
$jsonRemaining=[int][Math]::Min($Seconds*1000,($MaxSeconds-50)*1000-$jsonWatch.ElapsedMilliseconds)
if($jsonRemaining -le 0){throw 'Native shared host work deadline exhausted.'}
```

- 每阶段有独立上限（8 / 100 / 10 秒）。
- 全局预算为 `MaxSeconds-50`，预留 50 秒给尾部清理。
- 预算耗尽时在 `Run` 之前抛错，后续阶段不启动。

尾部开销：final capture 固定 7000 ms，publication 固定 5000 ms，合计 12 秒。50 秒预留覆盖 12 秒，并留 38 秒给凭据清理与异常路径。成立。

### 4.2 需收紧：C# 的截止时间只约束等待循环，不约束清理

`json-bounded-process.cs` 的 `Run` 把 `maxMilliseconds` 用于三处：

- 启动前的 `remaining` 核对。
- `Timer` 的到期回调。
- 等待循环里的 `elapsed.ElapsedMilliseconds >= maxMilliseconds`。

但 `finally` 里的清理不受 `maxMilliseconds` 约束：

```text
job 清理循环        ：最多 5000 ms
root 退出等待       ：最多 5000 ms
```

合计每阶段最多超出传入值约 10 秒。超时会把 `TreeEmpty` 置 false 并触发 HOLD。后续阶段不再启动。因此最坏情况是一次阶段超跑约 10 秒。50 秒预留仍可吸收，但 `MaxSeconds` 不是硬墙。

建议：在记录里区分「阶段等待上限」与「阶段实际墙钟」。把每阶段的 `elapsedMilliseconds` 单独落盘，便于核算 `MaxSeconds` 是否被突破。

### 4.3 需收紧：`ValidateRange(90,240)` 的下界偏紧

阶段上限之和是 228 秒。两次 100 秒 build，两次 10 秒 inspect，一次 8 秒 capture-before。`MaxSeconds=240` 时全局预算为 190 秒。

按实际耗时推算。若第一次 build 用掉 100 秒，第二次 build 只剩 `190-118=72` 秒。第二次 inspect 只剩 `190-190=0` 秒，直接触发 deadline 耗尽。默认 240 秒对「两次完整 Hvigor build」是紧的。

建议：

- 下界抬到 150 以上。
- 或把两次 build 的独立上限改为按剩余预算动态分配。并在 `result.json` 里记录每阶段实得预算。

### 4.4 成立：超时记失败

`Invoke-JsonNativePhase` 的判定：

```powershell
if(!$jsonRun.TreeEmpty -or $jsonRun.TimedOut -or $jsonRun.Error -or $jsonRun.RootExitCode -ne 0){throw ...}
```

`TimedOut` 单列进失败条件，不依赖退出码。`json_hvigor_phase.ps1` 用 `exit $LASTEXITCODE` 透传。超时被杀时 `RootExitCode` 为 124、125 或 259（STILL_ACTIVE），均为非零，双重捕获。成立。

---

## 5. 进程树 empty 判断

### 5.1 成立的部分

判据是 job 对象自身的 `ActiveProcesses`。不是 PID 扫描，不是名字匹配，不是祖先推断。

```csharp
job = CreateJobObject(...)
limit.Basic.Flags = 0x2000;              // KILL_ON_JOB_CLOSE，无 BREAKAWAY_OK
CreateProcess(..., 0x08000004, ...)      // CREATE_NO_WINDOW | CREATE_SUSPENDED
AssignProcessToJobObject(job, process.Process)   // 挂起态先入 job，再 ResumeThread
```

- 子进程在 Resume 之前入 job，不存在「跑了才抓到」的窗口。
- 没有 `BREAKAWAY_OK`，子孙默认继承同一个 job。`cmd.exe`、`node.exe`、`flutter.bat` 都在内。
- `TreeEmpty` 取自 `QueryInformationJobObject(kind=1).ActiveProcesses == 0`，是内核计数。
- `Observe` 只用于记录 PID 列表，不参与 empty 判定。

结构体核对：

| 项 | 代码 | 结论 |
| --- | --- | --- |
| `JOBOBJECT_BASIC_PROCESS_ID_LIST` 计数偏移 | `Marshal.ReadInt32(buffer, 4)` | 正确（第 2 个 DWORD） |
| PID 数组起始 | `8 + IntPtr.Size*i` | 正确（x64 有 4 字节对齐填充） |
| job 信息类 | `SetInformationJobObject(job, 9, ...)` | 正确（ExtendedLimit） |
| 记账类 | `QueryInformationJobObject(job, 1, ...)` | 正确（BasicAccounting） |
| 缓冲上限 | `8 + IntPtr.Size*4096` | 4096 个 PID，超出则记录异常而非误判 |

`process.Process == IntPtr.Zero` 时 `TreeEmpty=true`，与「没起过进程」一致。root 句柄非零但 5 秒内未退出时强制 `TreeEmpty=false` 并写 `Error`，是保守方向。成立。

### 5.2 需收紧：Timer 回调与 finally 的句柄竞争

```csharp
deadline.Dispose();        // 不等待正在执行的回调
lock (gate) {
    ...
    TerminateJobObject(job, ...);
    CloseHandle(job); job = IntPtr.Zero;
}
```

`Timer.Dispose()` 不阻塞已在执行的回调。回调可能在 `Dispose` 之前已进入 `lock(gate)`，并通过 `job != IntPtr.Zero` 判断。随后 finally 取得锁、关闭句柄并置零。回调仍可能对一个已关闭的句柄调用 `TerminateJobObject`。Windows 句柄值会复用，理论上可能命中无关对象。

建议：改用 `Timer.Dispose(WaitHandle)` 或 `ManualResetEvent`，确认「回调已退出」再关闭句柄。或在回调里只置标志，由主线程统一执行终止。

### 5.3 注明：breakaway 逃逸不可见

job 未开 `BREAKAWAY_OK`，普通子进程无法脱离。显式 `CREATE_BREAKAWAY_FROM_JOB` 只在 job 允许时才会成功。当前配置下不会成功。因此没有已知逃逸路径，这一点成立。无需变更，只在报告里不要声称「绝对无逃逸」。

---

## 6. harness / normal 隔离

### 6.1 成立的部分

| 机制 | 位置 | 说明 |
| --- | --- | --- |
| 产物分文件保留 | `--copy-to $jsonPackages/json-<mode>-unsigned.hap` | 两模式各有独立 HAP |
| 独占创建 | `destination.open("xb")` | 防止并发构建换掉已保留的产物 |
| 拒绝覆盖不同内容 | `inspect` 中 sha256 比对 | 同内容可重入，不同内容记录异常 |
| 内核必须不同 | `artifacts[0].kernelSha256 -ne artifacts[1].kernelSha256` | 防止两模式产出同一份 |
| 模式顺序固定 | harness → inspect → normal → inspect | harness 核对时 normal 尚未构建 |
| 每次核对只归因一份 depfile | `matching()` 按 kernel 哈希过滤并要求恰好 1 份 | 旧 depfile 不会误配 |
| 构建前拒绝已有 HAP | `if(Test-Path $jsonHap){throw ...}` | 防止复用陈旧产物 |

模式顺序是关键。harness 的 `inspect` 在 normal 构建之前完成。因此 harness 的 kernel 与 depfile 归因不会被 normal 覆盖。成立。

`DART_DEFINES` 的取值与 Flutter 侧契约一致：

- `flutter-hvigor-plugin` 用 `getParameter('DART_DEFINES')`，非空时加 `--DartDefines=<值>`。
- 插件对 `TARGET_PLATFORM` 做 `split(',')`。`-p TARGET_PLATFORM=ohos-x64` 得到单平台，正好只出 `x86_64`，与 `inspect` 要求的 `libs/x86_64/libflutter.so` 对齐。
- `FLUTTER_TARGET`、`TRACK_WIDGET_CREATION`、`TREE_SHAKE_ICONS` 均为插件认识的键名。
- normal 模式 `DART_DEFINES` 为空，插件走 falsy 分支，不加该参数。

### 6.2 需收紧：两模式共享中间产物目录，无 clean

插件里的产物目录是固定的：

```ts
const intermediateDir = `build/ohos/intermediates/flutter/${toCamelCase([productName, buildMode])}`
```

`productName=default`、`buildMode=debug`，两模式都是 `defaultDebug`。因此 harness 与 normal 共用：

- `appRoot/ohos/build/ohos/intermediates/flutter/defaultDebug`
- `appRoot/.dart_tool/flutter_build/`

包装器在两次 build 之间不做 clean。当前能工作，因为三条上游行为：

1. `FlutterTask` 未声明 `inputs` 或 `outputs`，Hvigor 每次都执行。
2. 插件每次 `rmSync(destFlutterAssetsDir)` 后重新 `copyDirectory`。
3. Flutter assemble 按 `--DartDefines` 变更重建 kernel。

但这三条都是**上游插件的隐式行为**，不是包装器保证的。若插件将来加了 up-to-date 核对，或 assemble 缓存键不含 defines，normal 的 HAP 可能拿到 harness 的 assets。`kernelSha256` 断言只能发现「两份相同」，发现不了「错配但不同」。

建议：两种模式之间清理 `ohos/build`、`ohos/entry/build`、`.dart_tool/flutter_build`。或分别用独立 `appRoot`。并在 `result.json` 里记录每模式核对时的 depfile 路径，作为配对证据。

### 6.3 注明：`kernelSha256` 不同只是代理证据

断言证明两模式编出的 kernel 不同。它不证明 harness 的 kernel 里真的烘进了 `QFLI_VERIFY_CATALOG=true`。`main.dart` 用的是 `const bool.fromEnvironment('QFLI_VERIFY_CATALOG')`。defines 变更必然改变 kernel 字节，所以作为代理是合理的。但报告里应写成「两模式 kernel 不同」，不要写成「已证明核对页被编入」。

---

## 7. helper 细节核对

### 7.1 `json_hvigor_phase.ps1`

```powershell
Set-Location -LiteralPath $jsonBuild.cwd
$jsonArguments=[string[]]$jsonBuild.arguments
& $jsonBuild.executable @jsonArguments
exit $LASTEXITCODE
```

- `$jsonBuild.executable` 是 `hvigorw.bat`，由 pwsh 经 `cmd.exe` 执行，`$LASTEXITCODE` 正常透传。
- `.bat` 从未直接交给 `CreateProcess`。`BoundedProcess::Run` 的程序参数始终是 `python.exe` 或 `pwsh.exe`。因此不会触发 `CreateProcess` 不支持 `.bat` 的问题。这一点很关键，成立。
- `-NoProfile -NonInteractive -File` 调用。`$Config` 为 `Mandatory`，参数传递成立。

### 7.2 凭据进入快照（安全项）

`ohos/build-profile.json5` 含明文签名材料：

```text
storePassword = 0000001B...
keyPassword   = 0000001B...
certpath / profile / storeFile = C:\Users\lichengyu\.ohos\config\*.cer|.p7b|.p12
```

`prepare_json_ohos_inputs.py` 的 `credential()` 只按后缀（`.p12`、`.pem`、`.p7b` 等）和固定文件名（`.env`、`signing.properties` 等）判定。`build-profile.json5` 命中不了。因此：

1. 它被 `copy_tree` 与 `shutil.copy2` 复制进 `appRoot/ohos/`。
2. 它也进入 `manifest["files"]` 与 `files` 身份比较。

结果是明文口令被复制到 `build/native-release-artifacts/<id>/qfli_json/ohos/build-profile.json5`。`build/` 被 Git 忽略，所以不会进版本库。但 `exclusionPolicy` 里写的 `credential contents` 与实际不符。

另外，`-c properties.enableSignTask=false` 只是跳过签名任务。它不改变明文材料仍被复制的事实。

建议：

- 在 `credential()` 里补一条内容检测。文件名是 `build-profile.json5` 且含 `storePassword` 或 `keyPassword` 时，复制前先脱敏。或在 `exclusionPolicy` 里明确写出「`build-profile.json5` 含签名材料，按需保留」。
- 报告里不要声称「凭据内容已排除」。

### 7.3 `local.properties` 保留绝对路径

`local.properties` 含 `flutter.sdk=D:\\ProgramFiles\\flutter_ohos` 与 `hwsdk.dir=D:\\ProgramFiles\\Huawei\\DevEco Studio\\sdk`。

- 这是**期望行为**。插件靠 `flutter.sdk` 找 engine HAR，DevEco 靠 `hwsdk.dir` 找 SDK。
- `relocate_string` 只重写 lock 文件，不动 `local.properties`。因此快照仍指向真实 SDK。成立。
- `properties-util.ts` 的 `loadProperties` 不处理反斜线转义，值会是字面 `D:\\ProgramFiles\\flutter_ohos`。Windows 会折叠重复分隔符，历史上构建通过，因此可用。但这是依赖平台宽容度，不是明确契约。可接受，注明。

### 7.4 `ohos/package.json` 的 `file:` 绝对路径

```json
"flutter-hvigor-plugin": "file:D:\\ProgramFiles\\flutter_ohos\\packages\\flutter_tools\\hvigor"
```

该文件在 `app/ohos` 下，不在 `node_modules` 内。因此被 `files` 身份比较覆盖。成立。

### 7.5 `inspect_json_release_hap.py`

- `package_roots` 要求 `qfli_json`、`qfli_studio_core`、`re_editor` 精确指向快照根，拒绝非本地 URI 与重复映射。成立。
- `source_dependencies` 先断言 app 与 core 不等于 `LIVE_APP` 或 `LIVE_CORE`，再用 aggregate 与 compiler 两份 depfile 交叉核对，要求 compiler 的源必须出现在 aggregate 里。成立。
- 要求 `main.dart`、`studio_profile.dart`、`re_editor.dart` 三者在两侧 depfile 中都出现。成立。
- 核对 `bundleName`、权限恰为 `READ_PASTEBOARD`、单一 `kernel_blob.bin`、`libs/x86_64/libflutter.so` 非空、三份内容资源与快照字节相等。与 `json_offline_host_test.dart` 的离线断言一致。成立。
- 失败分类为 `BLOCKED`（`BlockedInspection`）与 `FAIL`。两类均写 `output` 且 `exit=1`。包装器读到 `passed != true` 即抛错。落盘成立。

---

## 8. 阻碍真实构建的问题

未发现代码级阻断项。以下 3 项是真实构建可能失败的外部条件，需在开跑前确认。它们不属于脚本缺陷。

1. **Hvigor 需要 node 与 SDK 环境**。`hvigorw.bat` 在 `NODE_HOME` 未设时回退到 PATH 里的 `node`。`DEVECO_SDK_HOME` 与 `HOS_SDK_HOME` 决定 SDK 解析。当前进程环境两者均已具备：node 在 PATH，两个 SDK 变量已设。若在干净 shell 里跑，需先设这三个变量。

2. **空值参数 `-p DART_DEFINES=`**。normal 模式传空字符串。插件走 falsy 分支不加参数。但 Hvigor 的 `-p` 解析是否接受空值未在源码层确认。历史上 normal 构建通过，因此实际可用。若某次 Hvigor 升级后报参数异常，这是第一处要查的地方。

3. **`-c properties.enableSignTask=false` 的 CLI 契约**。`-c` 的语义与 `properties.` 前缀写法来自 PRD 记录。`evidence.md` 记有 `properties.enableSignTask=false` 成功产出未签名 HAP。本次未在 Hvigor 源码中定位到该选项定义。属证据驱动，不属源码确认。

---

## 9. 结果记录完整性

`$jsonRecord` 顶层键：

```text
grant, nextOwner, scope, startedUtc, phases, artifacts, sourceDrift, error,
exit, terminal, powerShell, coreCommit, appRoot, coreRoot, runnerHashes,
capture, publication, finishedUtc, elapsedSeconds
```

核对：

- `powerShell` 有 version、path、sha256，成立。
- `runnerHashes` 覆盖 5 个 helper，成立。`$jsonRunners` 先被用作 `--runner` 参数，又被用作 `runnerHashes` 的键。两者同源，成立。
- `capture` 只在 `$jsonPrepared`、`$jsonReady`、`$jsonCaptureReady` 都真时写入，成立。
- `$jsonRecord.terminal` 只统计**已记录**的阶段。deadline 耗尽时 `Invoke-JsonNativePhase` 在追加行之前抛错。该阶段不会出现在 `phases` 里，因此 `terminal` 仍可能为真。这与 §3.4 的语义一致（terminal 只表示进程树清空）。`exit=1` 会同时出现在消息里。可接受，但建议在 `phases` 里补一行 `{name=..., skipped=$true}`，让「没跑」与「跑过且干净」在记录里可区分。

---

## 10. 建议清单（交给脚本所有者）

按优先级：

1. **§7.2**：`build-profile.json5` 含明文签名口令。`credential()` 未覆盖，`exclusionPolicy` 表述不准。补脱敏或补声明。
2. **§6.2**：两模式共用 `defaultDebug` 中间目录且不 clean。隔离依赖上游插件的隐式重跑。加 clean 或独立 `appRoot`。
3. **§2.2**：`flutter-hvigor-plugin` 是链接。仅 4 个文件进 `tools`。`properties-util.ts` 与 `string-util.ts` 未覆盖。
4. **§4.3**：`ValidateRange(90,240)` 下界偏紧。默认 240 秒容纳两次完整 Hvigor build 余量小。
5. **§3.2**：`release.txt` 在 `trellis` 解析前落盘。失败时留下「已 RELEASE」残件。
6. **§3.3**：`Save-JsonNative` 自身失败会吞掉终局记录。
7. **§1.2**：`python` 解析与目录创建在 try 之外，失败不落盘。
8. **§5.2**：`Timer.Dispose()` 不等待回调，句柄存在理论竞争。
9. **§4.2 与 §9**：记录每阶段实际墙钟。`phases` 补 `skipped` 行。

---

## 11. 本次审查的边界

- 未执行 `hvigorw`、`flutter`、`dart`、`ohpm`，未触发任何 build。
- 未执行 `flutter test` 或 `python tool/build_json_content.py`。
- 未连接设备，未安装 HAP。
- 脚本保持原样，未 commit 或 push。
- 只读操作：`Get-Content`、`Test-Path`、`Get-Command`、`git check-ignore`、Base64 解码、目录列举。
- 当前 checkout 无 Git remote（`git remote -v` 无输出）。因此本审查不涉及推送。
- 上游已说明：`MaxSeconds-20` 已改为 `MaxSeconds-50`，实际超时记为失败，AST 与 804 文件 source-only 前后比较已通过。本审查按 §4.1 的 50 秒预留口径核对，尾部 12 秒开销被覆盖。