# native703 验收核对 —— 只读审查

审查对象：grant 703 的父子 result、各 phase 日志、最终交接凭证。
审查时间：2026-10-26
审查方式：只读。未执行 SDK / Hvigor / Flutter / hdc / 设备命令，未修改任何仓库文件，未 commit，未 push。仅读取文件、计算哈希、用小型 Python 解析 depfile。

---

## 0. 结论先行

**grant 703 未通过验收。`finalGatePassed = false`，`exit = 1`。**

真实执行停在 `harness-inspect`。`harness-build` 的 exit 0 只表示「HAP 编译成功」，**不表示门禁通过**——紧接着的 `harness-inspect` 以 `BLOCKED` 退出，于是 `normal` 构建阶段从未开始，设备侧从未介入。

失败的直接原因是一处**隔离路径误判**：inspector 把隔离快照内的原生插件目录判成了「原始/在线项目源码」。

`handoffReady = true` 只表示**所有权移交就绪**，结果文件自己写明 `handoffMeaning: "ownership only; not runtime acceptance"`。不得据此写「通过」。

---

## 1. 审查对象与身份

| 项 | 值 |
| --- | --- |
| 父 result | `build/native-window-artifacts/20261025T215527Z-e5c6f6b8/result.json`（5082 字节） |
| 子 result | `build/native-release-artifacts/20261025T215530Z-c940500b/evidence/result.json`（4424 字节） |
| 子 result SHA-256 | `5B4CD3D2A2B2AF5645D02522510B815B7CC23BF977212222C24D48DA4C651567` |
| 父记录的 childResult.sha256 | `5b4cd3d2a2b2af5645d02522510b815b7cc23bf977212222c24d48da4c651567` → **一致** |
| 父 startedUtc | 2026-10-25T21:55:27.9010391Z |
| 父 finishedUtc | 2026-10-25T21:56:07.5022698Z，elapsedSeconds **39.72**（上限 240） |
| 子 startedUtc | 2026-10-25T21:55:30.0719621Z |
| 子 finishedUtc | 2026-10-25T21:56:06.5556342Z，elapsedSeconds **36.485** |
| 子 coreCommit | `2f9039a3ba95449679b17257b0313c1ee3644a2c` |
| 隔离 appRoot | `build/o6e60792d/qfli_json` |
| 隔离 coreRoot | `build/o6e60792d/qfli_studio_core` |
| 后继所有者 | `c-coordinator` |

子 result 文件当前哈希与父记录值逐字节相符，说明审查时该证据未被重写。

**运行器身份全部相符**（父 `identities` / 子 `runnerHashes` 与磁盘实测 SHA-256 逐一比对）：

| 文件 | 记录值（前 16 位） | 实测 |
| --- | --- | --- |
| `run_json_ohos_window.ps1` | `aa0af8de601453cb` | 一致 |
| `run_json_ohos_release.ps1` | `8ee89a4450090b41` | 一致 |
| `json_hvigor_phase.ps1` | `85477722f652ae60` | 一致 |
| `prepare_json_ohos_inputs.py` | `8ef4f2f4e355fe97` | 一致 |
| `inspect_json_release_hap.py` | `9417170308902ab4` | 一致 |
| `json-bounded-process.cs` | `6657cffb8a9e4ac7` | 一致 |
| `build/ohos-final-preparation-20261024.json` | `af6361444e9b4a49` | 一致 |
| `pwsh.exe` | `8737aa78bdbe2941` | 一致 |

`identityDrift: []`，且上述实测确认运行器与准备清单在运行后未被改动。

---

## 2. 真实执行到哪一步

父 result 的 `rows` 有三项，子 result 的 `phases` 有三项，另有 `capture` 与 `publication`。

### 父级三行

| 行 | pid | exit | elapsed | treeEmpty | timedOut | residualCleanup |
| --- | --- | --- | --- | --- | --- | --- |
| acceptance | 42308 | 0 | 944 ms | true | false | false |
| validation | 56436 | **1** | 36735 ms（允许 207945） | true | false | false |
| final-relay | 70524 | 0 | 848 ms | true | false | false |

### 子级 phase 链（按实际时序）

| 阶段 | pid | exit | elapsed | residualCleanup | 说明 |
| --- | --- | --- | --- | --- | --- |
| capture-before | 70376 | 0 | 3486 ms | **true** | 记录 804 个源文件 / 6 条缓存引用 |
| harness-build | 57940 | **0** | 24924 ms | false | hvigor `BUILD SUCCESSFUL in 23 s 332 ms`，44 tasks 全执行 |
| harness-inspect | 25700 | **1** | 3579 ms | **true** | `BLOCKED`，门禁失败 |
| capture-after | 14816 | **1** | — | true | 记录 805 个源文件 / 7 条缓存引用，`changed: true` |
| publication | 67684 | 0 | — | false | 写出 `RELEASE_PENDING_PUBLISHER` |

时间线（UTC）：

```
21:55:27.901  父启动
21:55:29.769  acceptance 消息 seq 707
21:55:30.071  子启动；harness-command.json / normal-command.json 同时落盘
21:55:30       capture-before 开始（3486 ms）
21:55:59       harness-build 结束，产出 HAP
21:56:02.837   harness-inspect 判定 BLOCKED
21:56:05       capture-after / source-after.json / release.txt
21:56:06       publication 结束
21:56:06.555   子 result 落盘（exit 1）
21:56:07.444   final-relay 消息 seq 709
21:56:07.502   父 result 落盘（exit 1）
```

### harness-build 的实际产出

hvigor 日志尾部：

```
> hvigor Finished :entry:default@PackageHap... after 854 ms
> hvigor Finished :entry:default@SignHap... after 2 ms
> hvigor BUILD SUCCESSFUL in 23 s 332 ms
44 tasks in total: 44 executed, 0 up-to-date
```

HAP 确实生成：

| 项 | 值 |
| --- | --- |
| 路径 | `build/o6e60792d/qfli_json/ohos/entry/build/default/outputs/default/entry-default-unsigned.hap` |
| 大小 | 124516943 字节 |
| SHA-256 | `DF170F250A1CECC84BA0ABB73F42DDFBC5F6362A6980A64C29962BC52AD02A88` |
| 签名 | 未签名（`-c properties.enableSignTask=false`，文件名 `-unsigned`） |
| 目标平台 | `TARGET_PLATFORM=ohos-x64` |
| DART_DEFINES | `UUZMSV9WRVJJRllfQ0FUQUxPRz10cnVl` → 解码为 `QFLI_VERIFY_CATALOG=true` |

**但这枚 HAP 未被接受。** `harness-artifact.json`：

```json
{
  "passed": false,
  "status": "BLOCKED",
  "mode": "harness",
  "hap": ".../entry-default-unsigned.hap",
  "copiedHap": null,
  "error": "BlockedInspection: Depfile references original/live project source: D:\\MyNewProjects\\qfli_json\\build\\o6e60792d\\native_plugins\\path_provider_ohos\\LICENSE",
  "inspectedUtc": "2026-10-25T21:56:02.837082+00:00"
}
```

子 result 的 `artifacts` 为 `[]`，`copiedHap` 为 `null`。**HAP 留下的是构建中间产物，不是已接受产物。**

### 一句话概括真实进度

编译完成 → 产物落盘 → 静态检查拒绝 → 后续构建阶段未启动 → 结束。**没有任何环节证明该 HAP 的运行时行为。**

---

## 3. 隔离路径误判（失败根因）

### 现象

inspector 在 `source_dependencies()` 中抛出：

```
BlockedInspection: Depfile references original/live project source:
  D:\MyNewProjects\qfli_json\build\o6e60792d\native_plugins\path_provider_ohos\LICENSE
```

该路径**不是**在线项目源码。它是隔离快照内的原生插件副本。

### 代码位置

`.trellis/.runtime/inspect_json_release_hap.py`：

```python
17: LIVE_APP  = Path(__file__).resolve().parents[2]      # → D:\MyNewProjects\qfli_json
18: LIVE_CORE = LIVE_APP.parent / "qfli_studio_core"

176: for depfile in (aggregate, compiler):
177:     for dependency in depfile["inputs"]:
178:         if not inside(dependency, app) and not inside(dependency, core):
179:             if inside(dependency, LIVE_APP) or inside(dependency, LIVE_CORE):
180:                 raise BlockedInspection(f"Depfile references original/live project source: {dependency}")
```

### 判定链

快照布局：

```
build/o6e60792d/            ← 快照根
├── native_plugins/         ← 插件副本（app/core 的同级兄弟）
│   └── path_provider_ohos/
├── qfli_json/              ← app 快照（= app 参数）
└── qfli_studio_core/       ← core 快照（= core 参数）
```

`build/o6e60792d/` 整体位于在线仓库 `D:\MyNewProjects\qfli_json` 之下。于是对 `build/o6e60792d/native_plugins/path_provider_ohos/LICENSE`：

- `inside(dependency, app)` → 假（`native_plugins` 不是 `qfli_json` 的子目录）
- `inside(dependency, core)` → 假
- `inside(dependency, LIVE_APP)` → **真**（整个快照都在在线仓库内）

三段判定全部按代码执行，`raise` 必然触发。

**根因**：守卫的意图是拦「dep 指向在线检出而非冻结快照」。但冻结快照本身被放在在线检出内部（`<repo>/build/<id>/`）。所以「在 LIVE_APP 内」对每个快照文件都成立，该条件无法区分「快照」与「在线源码」。只有落在 `app`/`core` 之下的文件因为第 178 行先行排除才幸免；落在快照内但在 `app`/`core` 之外的文件（即 `native_plugins`）一律误伤。

### 误判范围（已量化，非单文件）

用与 inspector 相同的分隔规则解析两份 depfile：

| depfile | 输入总数 | 落在 app/core 内 | 在仓库内但在 app/core 外 → 会触发 `raise` | 仓库外（pub cache / SDK，不触发） |
| --- | --- | --- | --- | --- |
| `flutter_build.d`（aggregate，158233 字节） | 1587 | app 17 / core 201 | **3** | 1366 |
| `kernel_snapshot_program.d`（compiler，146454 字节） | 1503 | app 12 / core 186 | **2** | 1303 |

全部越界输入都指向同一个插件包根：

```
build\o6e60792d\native_plugins\path_provider_ohos\LICENSE
build\o6e60792d\native_plugins\path_provider_ohos\lib\messages.g.dart
build\o6e60792d\native_plugins\path_provider_ohos\lib\path_provider_ohos.dart
```

其中两份是 `.dart` 编译源，说明 `path_provider_ohos` **确实参与了编译**。所以即使单独豁免 `LICENSE`，另外两个 `.dart` 仍会立刻触发同样的 `raise`。**这不是一个文件的特例，而是一个包根的系统性误伤。**

### 内部冲突

- `.trellis/.runtime/prepare_json_ohos_inputs.py:221` 明确**要求**插件包根位于 `app.parent / "native_plugins"`：
  `if not under(packages["path_provider_ohos"], app.parent / "native_plugins"):`
- 同文件 `:350` 也是照此布局克隆：`clones[source] = destination / "native_plugins" / plugin["name"]`

即：准备阶段强制把插件放到 `app` 的同级目录，检查阶段却把该位置判为违规。**两边对同一布局给出相反结论。**

需要说明的是，inspector 的 `package_roots()`（第 110–137 行）只校验 `qfli_json` / `qfli_studio_core` / `re_editor` 三个映射，对插件包根既不承认也不校验，因此没有在更早的位置拦住这次误判。

### 影响面

该守卫并未「放行危险输入」，而是「错误拒绝合法输入」。它 fail-closed，所以不构成安全漏洞；但它使**任何包含原生插件包的隔离快照都无法通过 harness 门禁**，即该门禁在当前布局下不可达通过态。

---

## 4. 未执行 normal / 设备（证据）

### normal 构建从未执行

- `normal-command.json` 存在（与 `harness-command.json` 同在 21:55:30 落盘），说明命令**已准备好但未执行**。
- 子 result 的 `phases` 数组只有 `capture-before` / `harness-build` / `harness-inspect` 三项，无任何 normal 阶段。
- 子 result 的 `error` 明确写：`Native harness-inspect phase failed; later build phases unrun.`
- 磁盘上快照内**只有一个 HAP**。用 `Get-ChildItem -Recurse -Filter *.hap` 扫描 `build/o6e60792d`，唯一结果为第 2 节列出的 harness HAP。normal 构建的 HAP 不存在。

两条命令的差异仅在 `DART_DEFINES`：

| 命令 | DART_DEFINES |
| --- | --- |
| harness | `UUZMSV9WRVJJRllfQ0FUQUxPRz10cnVl`（= `QFLI_VERIFY_CATALOG=true`） |
| normal | 空 |

因此现有唯一产物是**验证模式**构建，不是发布模式构建。

### 设备从未介入

- 父 scope：`isolated unsigned x64 package validation; no device`
- 子 scope：`isolated published-core unsigned x64 harness and normal HAP builds; no device`
- 两份命令 JSON 的目标平台均为 `TARGET_PLATFORM=ohos-x64`，无 ARM64 变体。
- 两份命令 JSON 均无 `hdc`、无 install、无 start 调用；`phases` 无设备阶段。
- 子 result 的 `publication` 只写 `RELEASE_PENDING_PUBLISHER`，未描述安装或运行。
- 交接凭证 `final-relay.txt`：`No device/ARM64/signed-release claim.`

**结论：未执行设备验证，未执行 ARM64 构建，未执行签名。** 任何「设备通过」「真机验证」的表述均无据。

---

## 5. 源漂移边界

子 result 与父 result 的 `sourceDrift` 均为同样 6 项：

```json
"sourceDrift": [
  "files/added/nativePlugins/path_provider_ohos/ohos/BuildProfile.ets",
  "files/changed/app/ohos/entry/oh-package-lock.json5",
  "files/changed/app/ohos/oh-package-lock.json5",
  "files/changed/nativeCache/oh_modules/.ohpm/lock.json5",
  "files/changed/nativePlugins/path_provider_ohos/ohos/oh-package-lock.json5",
  "cacheReferences/added/nativePlugins/path_provider_ohos/ohos/oh_modules/@ohos/flutter_ohos"
]
```

### 逐项性质与实测字节

| 漂移项 | 类型 | before | after |
| --- | --- | --- | --- |
| `nativePlugins/.../ohos/BuildProfile.ets` | 新增（构建生成） | 不存在 | 519 字节 |
| `app/ohos/entry/oh-package-lock.json5` | 修改（锁文件） | 2048 字节 | 2054 字节 |
| `app/ohos/oh-package-lock.json5` | 修改（锁文件） | 680 字节 | 678 字节 |
| `nativeCache/oh_modules/.ohpm/lock.json5` | 修改（锁文件） | 4456 字节 | 4374 字节 |
| `nativePlugins/.../ohos/oh-package-lock.json5` | 修改（锁文件） | 834 字节 | 896 字节 |
| `cacheReferences/.../@ohos/flutter_ohos` | 新增（缓存引用） | 不存在 | 指向 app 快照 `oh_modules` 内的 flutter_ohos |

文件计数 `804 → 805`，缓存引用 `6 → 7`，与上述唯一新增项吻合。

### 边界（这是本次核对的关键区分）

`source-after.json` 的 `differences` 显示，其余分组**全为空**：

```json
"originalAppInputs":         {"added": [], "deleted": [], "changed": []}
"originalCacheReferences":   {"added": [], "deleted": [], "changed": []}
"originalExecutableComparison": {"added": [], "deleted": [], "changed": []}
"runners":                   {"added": [], "deleted": [], "changed": []}
"tools":                     {"added": [], "deleted": [], "changed": []}
"buildParameters":           {"added": [], "deleted": [], "changed": []}
"helperIdentity":            {"added": [], "deleted": [], "changed": []}
```

并且：

- `repositoriesChanged: []` —— 无 git 仓库内容变化。
- `files` 字典中 `app/lib/**` 各项均未出现在 `differences.files.changed` 中，即 **`lib/` 源码零漂移**。
- `beforeIdentity.sha256 = 6814b76710ccf8fece71a2d350638eeaffa417c92d742900b921d5b2c80c998b`，与磁盘 `source-before.json` 实测一致（248184 字节）。
- 父 result `identityDrift: []`；core HEAD `2f9039a3` 未变。

**边界结论**：漂移全部落在 **ohpm / hvigor 生成的锁文件、构建元数据与缓存引用**，范围限于隔离快照；**身份集合（运行器、工具、helper、构建参数、原始可执行对比）与源码身份零漂移，核心 HEAD 未变。**

因此准确表述是「有 6 项生成/锁/缓存漂移，无身份漂移」，**不能**写成「源码无漂移」（漂移确实存在并导致 `capture-after` exit 1），也**不能**写成「源码被篡改」（无 `lib/` 与仓库内容变化）。

---

## 6. 最终交接的语义边界

`final-relay` 是该轮的第三步，exit 0，`treeEmpty: true`。

`final-relay.txt` 与日志（seq 709）核心内容：

```
JSON grant703 FINAL VALIDATION TERMINAL RELEASE to c-coordinator.
Retained validation wrapper/root and all its descendant Jobs, including its pending
publisher, are now terminal+active0. SDKValidationExit=1, childGatePassed=False.
This relay is coordination only. Final window budget/pass verdict is ONLY in the
completed result.json; verify handoffReady/relay treeEmpty before next execution.
No device/ARM64/signed-release claim.
```

父 result 的三个布尔必须分开读：

| 字段 | 值 | 含义 |
| --- | --- | --- |
| `handoffReady` | **true** | 所有权可以移交 |
| `handoffMeaning` | `"ownership only; not runtime acceptance"` | 明确排除运行时验收 |
| `finalGatePassed` | **false** | 门禁未通过 |

`release.txt` 同向：`RELEASE_PENDING_PUBLISHER`、`Artifacts=0; drift=6`、`Unsigned x64 package proof only; no installed/device/ARM64/release-signing claim.`

进程清理状态：父三级 `treeEmpty` 全为 true，`timedOut` 全为 false，父 `budgetExceeded: false`。子级 `capture-before`、`harness-inspect`、`capture-after` 的 `residualCleanup` 为 true（检测并清理了残留进程），但 `treeEmpty` 仍为 true，说明无遗留进程。

---

## 7. 不得使用的表述（对照）

| ✗ 错误表述 | ✓ 有据表述 |
| --- | --- |
| 「harness build exit 0，通过」 | `harness-build` 阶段 exit 0，但 `harness-inspect` exit 1，门禁未通过 |
| 「native 门禁通过」 | `finalGatePassed = false`，`childGatePassed = false` |
| 「703 验收通过」 | 703 失败（exit 1），仅完成所有权移交 |
| 「handoffReady，所以通过」 | `handoffReady` 只表示所有权移交（`ownership only; not runtime acceptance`） |
| 「产出了 HAP 即验证通过」 | HAP 已产出但未被接受：`artifacts: []`、`copiedHap: null` |
| 「normal 构建通过」 | normal 构建从未执行（`later build phases unrun`），磁盘无 normal HAP |
| 「设备验证通过」 | 未执行任何设备操作（`no device`） |
| 「源码无漂移」 | 有 6 项生成/锁/缓存漂移；但无身份漂移，`lib/` 与核心 HEAD 未变 |
| 「隔离检查通过」 | 隔离检查**误判失败**：把快照内插件目录判成了在线源码 |

---

## 8. 附带观察（不改变结论）

1. **父级 `error` 文本过于笼统**：`Child validation failed, timed out or drifted; inspect exact retained result and logs.` 三个候选原因并列，且实际三项都不是——子级是 `harness-inspect` 静态拒绝，`timedOut` 全为 false，`budgetExceeded` 为 false。真实原因必须读子 result 与 `harness-artifact.json` 才能确定。
2. **`residualCleanup: true` 出现在三个子阶段**：说明有残留进程被清理。`treeEmpty` 仍为 true，清理生效；但该信号在三阶段同时出现，值得追查是否有进程回收时序问题。
3. **误判发生在门禁早期**：`matching()` 对两份 depfile 都成功定位到输出，说明 kernel hash、包根映射、隔离根校验等前序检查全部通过，才走到第 176 行的守卫。所以修复点单一且明确。
4. **`release.txt` 与 result 口径一致**：均声明 `Artifacts=0`、`drift=6`、无设备/ARM64/签名主张，未出现夸大。

---

## 9. 本次审查未做的事

- 未修改任何仓库文件；未改动 `inspect_json_release_hap.py` 或任何运行器。
- 未执行 SDK / Hvigor / Flutter / hdc / 设备命令；未重新构建；未重新运行 inspector。
- 未重跑 grant 703，未复用其产物。
- 未 commit，未 push。
- 只读操作：读取父/子 result 与全部 phase 日志、计算 8 个文件哈希、用小型 Python 加载 `source-before/after.json` 比对漂移项、用小型 Python 按 depfile 分隔规则统计越界输入数量。
- 未对是否修复该误判给出实现改动，仅指出根因、代码位置与影响面。
