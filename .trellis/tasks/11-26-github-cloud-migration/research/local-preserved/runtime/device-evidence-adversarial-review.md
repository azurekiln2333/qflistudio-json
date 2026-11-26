# 设备证据校验器 —— 独立负面审查（pi）

审查时间：2026-10-26
审查对象与固定版本（本次审查只对这两个字节内容负责）：

| 文件 | 字节 | mtime（本地） | SHA-256 |
| --- | --- | --- | --- |
| `.trellis/.runtime/verify_json_device_evidence.py` | 30310 | 2026-10-26 03:11:45 | `22A49F1516CFD70450E56BB0955178F75D14E5B14E5D062A0D7C90F37DE814C5` |
| `.trellis/.runtime/test_json_device_evidence.py` | 36832 | 2026-10-26 03:17:32 | `46A0013B0B3D0AA39C80E0946489E9E4F75AA67BFBBF5D74B6448D0ECE4436A4` |

审查方式：只读 + 纯标准库离线探针。
未改实现，未改测试，未改 `lib/`、`test/`、`tool/`、core、README、签名与共享设置；未 commit，未 push；未执行 SDK / Hvigor / Flutter / Dart / hdc / 设备 / 重型测试；未改变冻结的 native 构建输入。

说明：审查过程中实现被并发改写（02:45 版 29823 字节 → 03:11 版 30310 字节）。凡并发期间得到的结论均已用固定版本重跑确认；下文只报固定版本的结果。**02:45 版曾存在的 `semanticOperations` 每示例去重缺陷（同示例双分支只记 1）在 03:11 版已修复**，本次不再计为缺陷。

结论：**需改 2 项实质缺陷，另 5 项测试缺口，加 3 项边界必须写清。** 基线可用：固定版本下 `python -m unittest` 67/67 通过。

---

## 1. 实测攻击面矩阵（固定版本）

探针在临时目录用测试模块自身的 `Fixture` 构造自洽证据，再逐项变异，记录「接受 / 拒绝 / 由哪条检查拦下」。全部纯标准库，无设备。

| 变异 | 结果 | 拦下的检查 |
| --- | --- | --- |
| 基线（自洽合成证据） | 接受 | —— |
| `report.passed = 1`（整数冒充布尔） | 拒绝 | `report.passed must be true` |
| `report.fixtures = 340.0`（浮点冒充整数） | 拒绝 | `must be an integer (bool is rejected)` |
| `capture.schemaVersion = true` | 拒绝 | `schemaVersion must be the integer 1` |
| `capture.processId = true` | 拒绝 | `processId must be an integer` |
| `capture.grant = true` | 拒绝 | `grant must be non-empty` |
| `report.failures = ""`（空串冒充空列表） | 拒绝 | `failures must be an empty list` |
| 报告文件内重复 JSON 键 | 拒绝 | 重复键检测 |
| capture 文件内重复 JSON 键 | 拒绝 | 重复键检测 |
| 日志 marker 内重复 JSON 键 | 拒绝 | 重复键检测 |
| `report.startedUtc` 无时区（naive） | 拒绝 | `must carry an explicit UTC offset` |
| `report.startedUtc` 用 `+08:00` | 拒绝 | `must be in UTC` |
| `report.startedUtc` 早于 capture 窗口 | 拒绝 | 包围关系 |
| capture 窗口早于报告结束 | 拒绝 | 包围关系 |
| `report.finishedUtc` 早于 `startedUtc` | 拒绝 | 区间自洽 |
| 3 位小数 `startedUtc`（自洽，runId 同步） | **接受（正确）** | Dart 合法输出形态 |
| ZIP 内重复条目名（重算产物哈希） | 拒绝 | `duplicate archive entry names` |
| 大小写变体额外条目 | 拒绝 | 由 HAP 哈希一致性拦下 |
| 路径穿越式额外条目 | 拒绝 | 由 HAP 哈希一致性拦下 |
| 报告超过 16 MiB 上限 | 拒绝 | `exceeds the ... input limit` |
| 日志 marker 折行到两行 | 拒绝 | 单行 JSON 解析失败 |
| 日志独有 `cleanupError` 键 | 拒绝 | 全文结构相等 |
| **ZIP 成员载荷损坏（CRC/解压）** | **拒绝，但抛 `zlib.error`** | **非 `ValueError`（见 D1）** |
| **ZIP 成员加密** | **拒绝，但抛 `RuntimeError`** | **非 `ValueError`（见 D1）** |
| marker 字面量出现在报告某字段值内 | 拒绝（误拒，见 D4） | 裸子串计数 |
| `report.status = "PASSED"` | **接受（见 D2）** | 大小写归一 |
| `report.status = "  passed  "` | **接受（见 D2）** | 空白归一 |

真实资源复算（`derive_catalog_metrics`）：`examples=340, runnerPasses=340, tutorials=340, lessons=340, exerciseAnswers=440, fixtures=340, semanticOperations=10, tools=16`，与设备报告 `ohos-harness-final-result.json` 逐项一致。双分支示例的语义计数复算为 4，与 Dart 生产者（两个独立 `if`）一致。

---

## 2. 实质缺陷

### D1（中）损坏或加密的 ZIP 成员让 `verify_evidence` 抛出非 `ValueError`

契约：`verify_evidence(...) -> dict`，「无效输入抛 `ValueError`（可自定义子类）」。

实测：

```text
_scan_hap(损坏成员 HAP)   -> zlib.error          | ValueError=False
_scan_hap(加密成员 HAP)   -> builtins.RuntimeError | ValueError=False
verify_evidence(损坏 HAP) -> 抛 zlib.error（不是 EvidenceValidationError）
```

原因：`_scan_hap` 只在 `zipfile.ZipFile(path)` 构造处捕获 `BadZipFile/OSError`；而 `_hash_zip_member` / `_read_zip_member` 里的 `archive.open(info)` 与随后的 `read()` 没有任何异常映射。加密成员在 `open()` 抛 `RuntimeError`，损坏的 deflate 流在 `read()` 抛 `zlib.error`（CRC 不符时抛 `zipfile.BadZipFile`，同样不是 `ValueError`）。

影响面：
- **CLI 不受影响**：`main()` 的最外层 `except Exception` 会兜住，仍 exit 1、输出 `passed:false`，属 fail-closed。
- **API 契约受影响**：任何直接调用 `verify_evidence` 的调用方拿不到 `ValueError`，无法按契约 `except ValueError` 处理；测试若新增该用例会失败。
- 现测试完全没覆盖（无 `zlib` / `encrypt` / `corrupt` 关键字）。

建议（写明方向，不代改代码）：把成员读取包一层，把 `zlib.error`、`zipfile.BadZipFile`、`RuntimeError`、`OSError` 统一转成 `EvidenceValidationError`（`ValueError` 子类）。加密条目应给出「不支持加密成员」的明确信息。

### D2（低）`report.status` 用 `strip().lower()` 归一，放行非生产值

契约要求拒绝 `pending/failed`。生产者（`json_verification_report.dart`）只写小写且精确的 `running|passed|failed`。

实现：

```python
isinstance(status, str) and status.strip().lower() == "passed"
```

实测 `"PASSED"` 与 `"  passed  "` 都被接受。这与 `artifact.status == "PASS"` 的精确比较不一致，也让「未知状态值」以宽松方式通过。

建议：报告 `status` 改为精确相等 `== "passed"`。若确要容忍历史文件，应把容忍写成显式白名单，而不是大小写归一。

---

## 3. 测试缺口（六类攻击面逐项）

固定版本测试 67 项，已补齐大量负面用例（`test_rejects_log_only_cleanup_error`、`test_accepts_millisecond_precision_started_utc`、`test_rejects_duplicate_{report,capture,artifact}_key`、`test_rejects_integer_passed`、`test_rejects_missing_failure_list`、`test_rejects_matched_but_under_minimum_tutorials` 等）。以下仍缺：

### G1（高）ZIP 歧义无任何用例

无重复条目名、无大小写变体、无路径穿越、无「同名不同内容」。当前唯一防线是 `len(names)==len(set(names))`，逻辑正确且实测有效，但**没有测试锁定**，回归时无人发现。

建议用例：`test_rejects_duplicate_zip_entry_name`（用 `writestr` 同名写两次，并重算产物 `hapSha256` 与 `installedHapSha256`，否则只会被哈希一致性命中，测不到判重本身）。

### G2（高）损坏/加密 ZIP 成员无用例

这正是 D1 所在处。缺 `test_corrupt_zip_member_raises_value_error` 与 `test_encrypted_zip_member_raises_value_error`。两者都应断言异常是 `ValueError` 子类，而不是仅断言「被拒绝」——现有 `_assert_rejected` 会吞掉异常类型差异。

### G3（中）输入过大无用例

`MAX_HAP_BYTES` / `MAX_JSON_BYTES` / `MAX_LOG_BYTES` / `MAX_ZIP_*` 全无测试。缺：超限报告、超限日志、超限 capture、`MAX_ZIP_ENTRIES` 超限、压缩比超限、单成员解压超限。

数值边界须记入测试注释：真实 HAP `123864987` 字节（118.13 MiB），`MAX_HAP_BYTES = 2 GiB`，因此真实证据不会被误拒；若日后收紧上限，必须大于 118 MiB。

### G4（中）时间/时区缺 3 项

- 无 `test_rejects_naive_started_utc`（无时区串）。
- 无 `test_rejects_non_utc_offset`（`+08:00`）。
- 无 `test_rejects_report_finished_before_started`。

已实测这三项都会被正确拒绝，但缺锁定。

### G5（低）`test_rejects_stale_run_id` 名实不符

该用例只把 `runId` 的微秒段减一天、`startedUtc` 不动，实际命中的是「微秒段必须等于 `startedUtc`」规则，与 `test_rejects_run_id_time_not_matching_started_utc` 重复。**真正意义的「旧成功重放」未被测试**，原因见 §4 边界 B1：一个内部自洽但整体陈旧的证据集，本校验器无法拒绝。建议改名或补一个显式的边界用例。

### G6（低）CLI 失败路径只测字典拒绝，未测异常路径

`test_cli_exit_codes_and_output` 的失败用例是 `report.runnerPasses=1`（拒绝返回字典），未覆盖 `verify_evidence` 抛异常时 CLI 是否仍写出 `--output` 且 `passed:false`。建议加 `test_cli_invalid_input_writes_failed_output`（例如 HAP 路径不存在）。

另有两点未测且属真实行为：
- **D4 的误拒**：报告某字段值内含 `QFLI_JSON_VERIFY_RESULT` 字面量时，裸子串计数得 2 而误拒（见 §4）。
- marker 折行（当前正确拒绝，但无用例）。

---

## 4. 另外三项应记入结论的判定

### D4（低）marker 用裸子串计数，存在误拒

`_extract_log_marker` 用 `text.count(MARKER)`。若报告某个字段（如 `error` 或 `stack`）的值里含 `QFLI_JSON_VERIFY_RESULT` 字面量，计数变 2 → 误拒一次真实成功。实测确认。

影响低（当前报告字段不含该串），但属 fail-closed 的误拒。建议改为「按 marker 起始位置计数」，即匹配 `^\s*...QFLI_JSON_VERIFY_RESULT\s+\{` 形态，或只统计 marker 后紧跟 JSON 的行。

### D5（信息）HAP 被读取两次，存在 TOCTOU 窗口

`_scan_hap` 先 `_sha256_file(hap)`，再 `zipfile.ZipFile(hap_path)` 重新打开。两次之间文件若被替换，可能「哈希对得上、内容对不上」。`inspect_json_release_hap.py` 有收尾复算（`require(sha256_file(hap) == original_hash)`），本校验器没有。实际风险低（内容 SHA 还会与产物比对），但建议在读完 ZIP 后复算一次 HAP 哈希，或从同一句柄完成哈希与解包。

### D6（信息）`_deep_equal` 要求日志与报告全套键相等，含 `cleanupError` 情形

固定版本采用**严格相等**：日志独有 `cleanupError` 会被拒。实测确认。

这与协议审查 §1.3 的担忧相反，但与任务书「比较日志与导出报告全文结构」一致。真实成功路径下，`staged.rename()` 后临时文件已不存在，`staged.exists()` 为假，不会追加 `cleanupError`，因此该形态只在异常清理时出现——那时报告本身也已判失败。**判定：维持严格相等是对的**，但应把「成功路径不会产生 `cleanupError`」写入实现注释或测试，避免后人误放宽。

---

## 5. 已确认正确的判定（摘要）

- 整数/布尔分离：`type(value) is int`；`True`、`340.0`、`"340"` 全拒。
- 重复 JSON 键：报告、capture、产物、日志四处都用 `object_pairs_hook`，实测均拒。
- 时区：naive 与 `+08:00` 均拒；仅接受显式 UTC 零偏移；**3 位小数合法且被接受**（见 §6 修正）。
- 微秒换算：`_epoch_micros` 用整数运算（`days*86400+seconds)*1e6+microseconds`），**正确避开浮点截断**。
- ZIP：重复条目名判重；压缩比、单成员解压、总量、条目数均有上限；解压后再按实际长度复核，不信任中心目录。
- 指标：从 HAP 内资源复算，双分支语义计数与 Dart 一致（实测 4 == 4）。
- 日志：`QFLI_JSON_VERIFY_RESULT` 精确匹配（不会误吞 `..._PROGRESS`）；要求单行 JSON；与报告全文结构相等。
- 产物：`passed is True`、`status == "PASS"`、`mode == "harness"`、bundle/权限精确、`sourceDependencies.status == "PASS"` 且三组 `sources` 非空。
- 输出：`scope: evidence-consistency-only`、`devicePassIndependentlyProven: false` 与 disclaimer，未把合成样例写成设备通过。

---

## 6. 对协议审查 `device-evidence-protocol-review.md` 的独立复核

- **§1.4 概率方向相反（需更正）**：该文称「设备上 `DateTime.now()` 常见毫秒精度，余数为 0，因此 3 位小数是常态」。查 Dart VM 实现 `bin/cache/dart-sdk/lib/_internal/vm_shared/lib/date_patch.dart:104`：`DateTime._nowUtc() : isUtc = true, _value = _getCurrentMicros();`，取的是**微秒**，不是毫秒。因此 `microsecond == 0` 是 1/1000 的稀有情形，**6 位小数才是常态，3 位是稀有**。需求方向不变（两种都要处理），但概率判断应更正，否则会误导实现把 3 位当主路径。
- **§1.4 的位数结论本身正确**：`bin/cache/dart-sdk/lib/core/date_time.dart:681` 的 `toIso8601String()` 恒输出 3 位毫秒，仅当 `microsecond != 0` 再追加 3 位。实测校验器的 `_parse_utc` 用 `datetime.fromisoformat`，3 位与 6 位都能解析，**3 位自洽证据实测被接受**，无缺陷。
- **§1.3 的 `cleanupError` 担忧在固定版本不成立**（见 D6）：实现选择了严格相等，且成功路径不产生该键。协议审查的建议若被照抄放宽，反而会削弱「全文结构相等」。
- 其余 §1.1、§1.2、§1.5、§1.6、§2、§3、§4 的字段与词表结论与源码一致，本次复核未发现新分歧。

---

## 7. 证据边界（必须随结论一起引用）

校验器只验证**输入证据之间的一致性**：

- 不证明设备真的安装了该 HAP。
- 不证明日志与报告来自真实硬件或该进程。
- 不证明 `capture.grant` 授权的真实性。
- 不证明 `mode == "harness"` 对应的 HAP 内容确实是校验版（`mode` 来自 CLI 参数）。
- 不证明 `platform == "ohos"` 来自真实 OHOS 设备。

合成夹具即使被接受，也只是「协议自洽样例」，**不得写成设备通过**。固定版本已在返回体与 CLI 输出中带 `devicePassIndependentlyProven: false` 与 disclaimer，方向正确，应保持。

现存的真实证据（`research/ohos-harness-final-result.json`、`ohos-ui-acceptance.json`）**不能通过本校验器**：它们产生于 2026-10-22，早于报告可靠性修正（`d7fddf3`），既无 `runId`/`startedUtc`/`finishedUtc`，也无配套 capture。这是正确的 fail-closed 行为，不是缺陷；但意味着**当前仓库内没有任何一组输入能通过该校验器**，只有等到一次新设备运行产出完整证据集。

## 8. 边界与残留风险（本校验器结构上无法消除）

- **B1 内部自洽的旧证据重放**：只要把 `startedUtc`/`finishedUtc`/`runId`/capture 窗口一起改到旧时刻，包围关系与微秒一致仍然成立，校验器无法判「旧」。它没有可信时间参照。任务书的「拒绝旧时间」只能收敛为「报告窗口必须落在 capture 窗口内」。
- **B2 同一进程内的多次运行**：`runId` 的序号段只保证同进程内递增，校验器不维护跨运行状态，无法发现同一组证据被重复提交。
- **B3 `runId` 前缀 PID 与 hilog 行内 PID 未交叉校验**：真实日志行形如 `... 5271 5271 W ... QFLI_JSON_VERIFY_RESULT {...}`，行内已带进程号。当前只比对 `runId` 前缀与 `capture.processId`，未比对日志行自身 PID。这是可加强的点（不属缺陷）。

## 9. 复核建议清单（交实现者）

1. **D1**：`_hash_zip_member` / `_read_zip_member` 捕获 `zlib.error`、`zipfile.BadZipFile`、`RuntimeError`、`OSError`，转 `EvidenceValidationError`。
2. **D2**：`report.status` 改为精确 `== "passed"`。
3. **G1/G2/G3/G4/G5/G6**：按 §3 增加负面用例；`_assert_rejected` 建议允许断言期待的具体异常类型，以暴露 D1 一类问题。
4. **D4**：marker 计数改为「marker + 同行 JSON」形态匹配。
5. **D5**：读完 ZIP 后复算 HAP 哈希，或单句柄完成。
6. **D6**：把「成功路径无 `cleanupError`」写进注释或加一个正向用例。
7. 更正协议审查 §1.4 的概率表述（见 §6）。

## 10. 本次审查未做的事

- 未改 `verify_json_device_evidence.py`、`test_json_device_evidence.py` 或任何仓库文件。
- 未写文件到 `.trellis/.runtime` 以外；探针脚本写在系统 TEMP 目录。
- 未执行 SDK / Hvigor / Flutter / Dart / hdc / 设备命令；未安装、未构建、未改签名。
- 未 commit，未 push。
- 只运行了纯标准库离线探针与该测试模块的 `unittest`（无设备、无 SDK、无网络），用于确认固定版本的实测行为。