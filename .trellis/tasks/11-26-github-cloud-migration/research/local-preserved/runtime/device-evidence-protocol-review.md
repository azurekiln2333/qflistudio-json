# 设备证据协议审查（pi）

审查时间：2026-10-26
审查范围：任务书给出的 `verify_evidence` 契约，对照真实产出方
- `lib/json/json_verification_report.dart`（报告与 runId）
- `lib/json/json_verification_page.dart`（日志 marker）
- `lib/json/json_catalog_verification.dart`（指标计数）
- `.trellis/.runtime/inspect_json_release_hap.py`（HAP 产物字段）
- `assets/content/examples.json`、`assets/content/tutorials.json`（静态计数）

审查方式：只读。未写实现，未改测试，未运行 SDK / Hvigor / Flutter / Dart / hdc / 设备 / 重型测试，未 commit。

结论：**契约与真实输出有 6 处会直接造成误判。** 现有实现已覆盖 5 处。仅剩 `cleanupError` 容忍与 `semanticOperations` 分支累加两项未覆盖，且两项都与其自测冲突。计数推导仅 `runnerPasses` 不能静态成立。

---

## 1. 会直接造成误判的 6 处

### 1.1 `status` 词表大小写与取值不同（最高风险）

真实报告（`json_verification_report.dart`）的 `status` 只有三个值，全小写：

```text
running   （初始占位，写入 passed:false）
passed
failed
```

真实 HAP 产物（`inspect_json_release_hap.py`）的 `status` 全大写：

```text
PASS / FAIL / BLOCKED
```

任务书写的「拒绝 pending/failed」与真实产出不符。真实报告里**没有 `pending`**，占位值是 `status:'running'`。

实现要求：报告按 `running|passed|failed` 判定，产物按 `PASS|FAIL|BLOCKED` 判定。两套词表分开写常量，不要共用。

### 1.2 报告存在 `passed:false` 且 `status:'running'` 且缺 `finishedUtc` 的落盘形态

`json_verification_report.dart` 的 staged 写入失败分支：

```dart
} on Object catch (error, stack) {
  result = { ...identity, 'finishedUtc': ..., 'passed': false, 'status': 'failed', 'error': ... };
}
```

此时磁盘上的报告仍是先前的 `running` 占位，**没有 `finishedUtc`**。函数返回的 `result` 与磁盘报告不同。

实现要求：不得假设 `finishedUtc` 一定存在。缺 `finishedUtc` 时按失败处理，不要抛未捕获异常。

### 1.3 日志 JSON 可能比报告多 `cleanupError`

同一文件的 `finally`：

```dart
} finally {
  try { if (await staged.exists()) await staged.delete(); } on Object catch (error) {
    result = {...result, 'cleanupError': '$error'};
  }
}
```

`cleanupError` 追加在 rename 成功之后。报告已经写完，不会带上该键。日志里的 `jsonEncode(result)` 会带上。

实现要求：全文结构比较要对齐「报告应有键集」。把 `cleanupError` 视为日志独有，不参与相等判定。否则会误杀一次真实成功的运行。

### 1.4 runId 的微秒字段与 `startedUtc` 小数位不总相等长

runId 形态（`json_verification_report.dart`）：

```dart
'runId': '$pid-${started.microsecondsSinceEpoch}-${_runSequence++}'
```

`startedUtc` 用 `started.toIso8601String()`。Dart 在微秒余数为 0 时只输出 3 位小数（毫秒），余数非 0 时才输出 6 位。

设备上 `DateTime.now()` 常见毫秒精度，余数为 0，因此 **3 位小数是常态**，不是特例。

实现要求：解析小数位时按位数补零到 6 位，再换算成微秒。假设固定 6 位会让约千分之一到近乎全部运行失败。

### 1.5 `runnerPasses` 不能从 HAP 资源静态推导

任务书把它列入「从 HAP 内 examples/tutorials 资源推导」。实际它是运行结果，`json_catalog_verification.dart` 里逐示例跑 runner 后才累加。

HAP 里没有 Dart 源码，也没有运行记录。静态侧唯一可靠的规则是 `runnerPasses == examples`。

实现要求：把 `runnerPasses` 写成「等于 `examples`」的断言，并注明这是通过态的必然推论，不是静态推导。

### 1.6 日志里同时有两种 marker，前缀匹配会误命中

`json_verification_page.dart` 同时输出：

```text
QFLI_JSON_VERIFY_PROGRESS <status>
QFLI_JSON_VERIFY_RESULT {单行 JSON}
```

两者共享前缀 `QFLI_JSON_VERIFY_`。

实现要求：只认 `QFLI_JSON_VERIFY_RESULT ` 加一个空格后的单行 JSON。不要按 `QFLI_JSON_VERIFY_` 前缀匹配，否则会把每条进度行当成结果。

---

## 2. 计数推导（静态已校验）

从 HAP 内的 `assets/content/examples.json` 与 `assets/content/tutorials.json` 可以直接算出下表。`entries` 与 `catalog.examples.length` 是 1 对 1，`ContentCatalog.fromJson` 不做去重或过滤，因此静态值与报告值应相等。

| 指标 | 静态推导式 | 当前值 |
| --- | --- | --- |
| `examples` | `len(examples.entries)` | 340 |
| `tutorials` | `len(tutorials.entries)` | 340 |
| `lessons` | `sum(len(t.lessons))` | 340 |
| `exerciseAnswers` | `sum(len(l.exercises))` | 440 |
| `fixtures` | `sum(len(e.inputFixtures))` | 340 |
| `semanticOperations` | 见 2.2 | 10 |
| `runnerPasses` | 见 1.5，等于 `examples` | 340 |
| `tools` | 见 2.3，硬编码 16 | 16 |

### 2.1 三项数值相同是巧合

`examples`、`tutorials`、`lessons`、`fixtures` 当前都是 340。四条各自独立计数，不能互相替代。教程当前恰好一课一条，`lessons` 才等于 `tutorials`。

### 2.2 `semanticOperations` 按每示例两处独立累加

`json_catalog_verification.dart` 对同一示例可能命中两个分支，各加 1：

- 含 `operations` 与 `expected` → 加 1（当前 7 例）。
- 含 `target`、`patch` 与 `expected` → 加 1（当前 3 例）。

合计 10。实现要按「每示例每分支一次」累加，不能按「每示例一次」去重。

### 2.3 `tools` 固定 16 不是 HAP 推导

`tools` 来自 `JsonOperation.values.length`。HAP 内没有该枚举的源码。只能断言报告 `tools == 16`，并把它标为「当前契约常量」。

### 2.4 320 是每类下限，不是总数

`ContentCatalogValidator.validate` 用 `minimumEntriesPerType=320`，且对 `tutorials` 与 `examples` 分别按 `type=='json'` 计数。当前各 340。

实现要求：断言 `tutorials >= 320` 与 `examples >= 320`。写成「恰好 340」会超出契约，任何一次内容追加都会误拒。

---

## 3. HAP 产物字段对接

真实键名与任务书措辞不同，实现要按真实键名写。

| 任务书措辞 | 真实键 | 位置 |
| --- | --- | --- |
| HAP SHA | `hapSha256` | 顶层 |
| 内核 SHA | `kernelSha256` | 顶层 |
| 三资源 SHA | `contentAssets[<name>].sha256` | 仅三个键：`tutorials.json`、`examples.json`、`catalog_audit.json` |
| bundle | `bundleName` | 顶层，值 `com.azurekiln.qfli.json` |
| 权限 | `permissions` | 列表，当前恰一项 `ohos.permission.READ_PASTEBOARD` |
| mode | `mode` | 顶层，取值 `harness` 或 `normal` |
| sourceDependencies | `sourceDependencies.status` | 仅 `PASS` 时存在 |

### 3.1 `sourceDependencies` 只在 PASS 时存在

`source_dependencies()` 抛 `BlockedInspection` 时整个 `inspect()` 失败。产物变成 `status:'BLOCKED'`，**没有** `sourceDependencies` 键。因此「`sourceDependencies.status == 'PASS'`」与「顶层 `status == 'PASS'`」等价，不必重复判定。

`sources` 与 `sourceCounts` 的键都是 `app`、`core`、`re_editor`。三组都要非空。

### 3.2 `copiedHap` 可能为 null

未传 `--copy-to` 时该键为 `null`。当前包装器总传 `--copy-to`，但契约不应强制非空。若要强制，需在任务书里写明。

### 3.3 `mode` 只证明参数，不证明内容

`mode` 来自 CLI 参数。产物不会校验 HAP 里真的烘进了 `QFLI_VERIFY_CATALOG`。`kernelSha256` 不同只是间接证据。

实现与报告都不要把 `mode:'harness'` 读成「已证明是校验版」。

---

## 4. capture 字段

任务书的 12 个字段在仓库里没有任何产出方。它们由设备侧编排脚本写入。

| 字段 | 可校验内容 | 不可校验内容 |
| --- | --- | --- |
| `installedHapSha256` | 与 `artifact.hapSha256` 相等 | 设备是否真装了该 HAP |
| `processLogSha256` | 与 `sha256(process_log)` 相等 | 日志是否由该进程产出 |
| `reportSha256` | 与 `sha256(report)` 相等 | 报告是否由该设备导出 |
| `deviceId` | 非空字符串 | 设备身份真实性 |
| `grant` | 非空 | 授权真实性 |
| `processId` | 正整数，等于 runId 首段 | 进程归属 |
| `platform` | 等于 `ohos` | 实际运行平台 |

### 4.1 `startedUtc` 与 `finishedUtc` 命名冲突

capture 与报告都用这两个键名。解析时必须区分文档，不要共用变量名。

包含关系应为 `capture.startedUtc <= report.startedUtc` 且 `capture.finishedUtc >= report.finishedUtc`。

### 4.2 拒绝「旧时间」缺参照

任务书说拒绝旧时间，但没给上界。建议固定为「`report.startedUtc` 不得早于 `capture.startedUtc`」。否则无从判定。

### 4.3 布尔当整数

Python 里 `isinstance(True, int)` 为真。`processId` 与全部计数都要用 `type(x) is int`，不要用 `isinstance(x, int)`。

### 4.4 重复 JSON 键

标准 `json.load` 静默保留最后一个键。日志单行 JSON、报告、产物、capture 四处都要用 `object_pairs_hook` 检测重复键，命中即判失败。

---

## 5. 日志解析细节

- marker 可能在行中，不在行首。设备经 hilog 输出时常带时间戳与进程前缀。按「行内含 marker」提取其后文本。
- marker 之后必须是单行 JSON。提取后要断言其中不含换行。
- `wrapWidth: 100000` 防换行。若单行 JSON 超过 100000 字符会被折行，假设失效。当前结果在 1 KB 量级，风险低，但要记入实现注释。
- 报告与日志的 `stack` 含换行。`jsonEncode` 会转义成 `\n`，所以仍是单行。解析后不要对 `stack` 做行级处理。
- `passed` 必须 `is True`。Dart 侧用 `== true` 归一化，`1` 与 `"true"` 都应拒绝。
- `failures` 在异常分支缺失。`runJsonVerificationReport` 的 catch 只产出 `error` 与 `stack`。缺 `failures` 要判失败，不能跳过。

---

## 6. 校验器不能证明的内容

任务书已声明，实现与文档都要照此写，不得放宽。

- 不证明设备真的安装了该 HAP。
- 不证明日志与报告来自真实硬件。
- 不证明 `grant` 授权的真实性。
- 不证明 `mode:'harness'` 对应的 HAP 内容。
- 不证明 `platform:'ohos'` 来自真实 OHOS 设备。

因此 synthetic fixture 只能写成「协议自洽样例」，不能写成设备通过。

---

## 7. 建议的判定顺序（给实现者）

1. 路径存在与可读。缺失抛 `ValueError`。
2. 四个 JSON 输入用 `object_pairs_hook` 解析，拒绝重复键。
3. 产物：`passed is True`、`status == 'PASS'`、`mode == 'harness'`。
4. 产物：`bundleName` 与 `permissions` 精确匹配。
5. 产物：`hapSha256` 与 `sha256(hap)` 相等。
6. 产物：三资源 SHA 与 HAP 内解出的三文件 SHA 相等。
7. 产物：`sourceDependencies.status == 'PASS'`，三组 `sources` 非空。
8. capture：12 字段齐全，类型正确，`processId` 用 `type() is int`。
9. capture：两个文件 hash 与实测相等，`installedHapSha256 == artifact.hapSha256`。
10. 日志：唯一 `QFLI_JSON_VERIFY_RESULT`，其后单行 JSON。
11. 报告与日志：按报告键集做全文结构比较，容忍日志独有 `cleanupError`。
12. 报告：`status == 'passed'`、`passed is True`、`failures` 为空、`platform == 'ohos'`。
13. runId：首段等于 `capture.processId`。第二段等于 `startedUtc` 的微秒值（补零到 6 位）。
14. 时间：capture 区间包住报告区间。
15. 从 HAP 解出两个资源文件，按 §2 算 7 个指标。
16. 报告指标与静态指标逐项相等。`tutorials >= 320`、`examples >= 320`、`tools == 16`、`runnerPasses == examples`。
17. 任一项不满足即 `passed:false`。CLI 输出 `passed:false` 并 `exit 1`。

---

## 8. 优先修正清单

按风险排序，交给实现者。

1. §1.1 `status` 两套词表，`pending` 实际是 `running`。
2. §1.4 `startedUtc` 小数位可能是 3 位，微秒换算要补零。
3. §1.3 日志独有 `cleanupError` 会破坏全文相等。
4. §1.2 缺 `finishedUtc` 的 `running` 形态要能判失败而不崩。
5. §1.5 `runnerPasses` 只能等于 `examples`，不能声称静态推导。
6. §1.6 两种 marker 前缀相同，必须精确匹配。
7. §2.2 `semanticOperations` 按每示例两处累加。
8. §2.4 320 是每类下限，按 `type=='json'` 分别计。
9. §4.3 布尔当整数，用 `type() is int`。
10. §3.1 `sourceDependencies` 仅 PASS 时存在。

本清单是协议层优先级。实现侧实际状态见 §9。现有实现已覆盖第 1、2、4、5、6、7、9、10 项。仅 §9.2 的两项待修。

---

## 9. 实现对接核对（只读）

本地已存在 `.trellis/.runtime/verify_json_device_evidence.py`，并有 `test_json_device_evidence.py` 配套。本节按静态阅读核对，未运行测试。

### 9.1 已覆盖的发现

| 本审查条目 | 实现位置 | 结论 |
| --- | --- | --- |
| §1.1 两套 status 词表 | `_validate_artifact` 用 `== "PASS"`，`_validate_report` 用 `status.lower() == "passed"` | 已分开 |
| §1.2 缺 `finishedUtc` | `_parse_utc` 抛 `EvidenceValidationError`，CLI 走 `passed:false` 与 `exit 1` | 已覆盖 |
| §1.4 微秒小数位 | `_parse_utc` 用 `datetime.fromisoformat`，3 位与 6 位均可解析 | 已覆盖 |
| §1.5 `runnerPasses` | `derive_catalog_metrics` 直接写 `len(examples)` | 已覆盖 |
| §1.6 marker 前缀 | `MARKER` 常量不含 `PROGRESS`，并要求 `count == 1` | 已覆盖 |
| §2.4 320 下限 | `MIN_EXAMPLES` 与 `MIN_TUTORIALS` 各 320，分别断言 | 已覆盖 |
| §3 产物键名 | `hapSha256`、`kernelSha256`、`contentAssets[*].sha256`，并对 `assets` 做回退 | 已覆盖 |
| §4 capture 与布尔整数 | `_as_int` 用 `type(value) is int` | 已覆盖 |
| §4.4 重复 JSON 键 | `_no_duplicate_pairs` 作为 `object_pairs_hook` | 已覆盖 |

### 9.2 未覆盖：两项会与自测冲突

#### 9.2.1 日志独有的 `cleanupError` 会被误判

`verify_evidence` 末尾：

```python
_require(
    _deep_equal(log_marker, report_doc),
    "process log marker JSON and exported report differ in structure",
)
```

`_deep_equal` 对键集合做严格相等（`left.keys() != right.keys()`）。报告没有 `cleanupError`，日志有。键集合不等，直接判失败。

与 `test_accepts_log_only_cleanup_error` 冲突。该用例经 `set_log_field` 只改日志载荷，报告与 capture 不变。

建议：比较前从日志侧移除 `cleanupError`。或按「报告应有键集」做子集比较，并把日志独有键记入结果。

#### 9.2.2 `semanticOperations` 被按示例去重

```python
def _semantic_operation(example: dict) -> bool:
    ...
    if "operations" in value and "expected" in value:
        return True
    return "target" in value and "patch" in value and "expected" in value
```

`semantic = sum(1 for example in examples if _semantic_operation(example))` 每个示例最多计 1。

`verifyJsonCatalog` 对同一示例的两个分支各加 1。夹具 `n_patch=7, n_merge=3, n_both=1` 期望 12。当前实现推导 11。

与 `test_accepts_per_branch_semantic_accumulation` 冲突。`report.semanticOperations == 12` 与推导 11 不等，被判失败。

建议：把 `_semantic_operation` 改成返回 0 到 2 的整数，再求和。

### 9.3 潜在偏差（当前资源不触发）

- `_lessons` 支持 `chapters` 回退，`_exercises` 支持 `tasks` 回退。`verifyJsonCatalog` 只读 `lessons` 与 `exercises`。若某教程改用 `chapters`，两边计数会不等。
- `derive_catalog_metrics` 统计全部 `entries`。`ContentCatalogValidator` 只统计 `type == 'json'` 的条目。当前全为 `json`。
- `_semantic_operation` 用 `json.loads` 解析 `code`，不查重复键。`JsonWorkbench.inspect` 会拒绝重复键。若某示例含重复键，两边语义计数会不等。
- `_fixture_count` 允许 `inputFixtures` 为字符串并计 1。Dart 侧只按 Map 计数。

四条都不影响当前资源。若要对齐 Dart，优先补 `type == 'json'` 过滤。

---

## 10. 本次审查的边界

- 未写 `verify_json_device_evidence.py`。
- 未改 `lib/`、`test/`、`tool/`、core、README、签名与共享设置。
- 未运行 SDK、Hvigor、Flutter、Dart、hdc、设备与重型测试。
- 未 commit，未 push。
- 只读操作：读取 Dart 源码与 core 内容解析器，读取两个资源文件做静态计数，读取既有 HAP 校验器字段。
- 静态计数结论可由两个资源文件复算。报告指标为运行时产物，未在本机运行。
