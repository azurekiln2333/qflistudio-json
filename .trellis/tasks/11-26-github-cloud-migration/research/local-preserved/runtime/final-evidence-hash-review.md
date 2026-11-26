# 设备证据哈希只读复核

复核对象：`.trellis/tasks/10-22-offline-json-ide/research/device-evidence-20261026/validation.json`。
复核时间：2026-10-26。
复核方式：只读。仅用小型 Python 脚本读取文件并计算 SHA-256。
未运行 SDK、Flutter 或设备。未改冻结文件。未 commit，未 push。

## 结论

- 三项声明哈希全部一致。
- 测试日志与计数一致。
- 目录指标与资源复算一致。
- 未发现哈希不符或内容冲突。
- 证据只证明文件身份与内部一致性。
- 证据不证明真实设备通过。

## 哈希对照

| 文件 | 声明字节 | 实测字节 | 声明 SHA-256 | 实测 SHA-256 | 结论 |
| --- | --- | --- | --- | --- | --- |
| `verify_json_device_evidence.py` | 31909 | 31909 | `b6a39af51155e529d193ba4fe27306cab6aa7a9c00cbca151c1a988066663014` | `b6a39af51155e529d193ba4fe27306cab6aa7a9c00cbca151c1a988066663014` | 一致 |
| `test_json_device_evidence.py` | 42031 | 42031 | `8699d794be166e99168cb5d78806676823b7455ff3b8bde42906c83bae7be412` | `8699d794be166e99168cb5d78806676823b7455ff3b8bde42906c83bae7be412` | 一致 |
| `unittest.log` | 9364 | 9364 | `582de54a2ec885c8ca1ddbbd8f3ce7c83364a1e3ac242913d6bc0da0f0d28652` | `582de54a2ec885c8ca1ddbbd8f3ce7c83364a1e3ac242913d6bc0da0f0d28652` | 一致 |

补充记录。

| 文件 | 字节 | SHA-256 | 说明 |
| --- | --- | --- | --- |
| `validation.json` | 1525 | `4a9359d3abb620c70d2367594d284dcae61f04c703df7d20a80f6b67229c45f5` | 未自声明 |
| `README.md` | 3036 | `59a009c5dd4e6a069976ae6dbfed389f4b36fd13db93fe6b11b9c6ac7f2ca801` | 未纳入清单 |

## 冻结副本与工作副本

- 冻结 `verify_json_device_evidence.py` 与 `.trellis/.runtime/verify_json_device_evidence.py` 同哈希。
- 冻结 `test_json_device_evidence.py` 与 `.trellis/.runtime/test_json_device_evidence.py` 同哈希。
- 冻结 `unittest.log` 与 `build/device-evidence-final-check/unittest.log` 同哈希。
- 复核时未发现工作副本偏离冻结副本。

## 日志与测试计数

- `unittest.log` 记录 `Ran 79 tests in 1.912s`。
- `unittest.log` 末尾记录 `OK`。
- 冻结测试文件含 79 个 `def test_`。
- `validation.json` 记录 `tests: 79` 与 `passed: true`。
- 四项一致。

## 指标对照

| 指标 | 资源复算 | validation | 结论 |
| --- | --- | --- | --- |
| examples | 340 | 340 | 一致 |
| runnerPasses | 340 | 340 | 一致 |
| tutorials | 340 | 340 | 一致 |
| lessons | 340 | 340 | 一致 |
| exerciseAnswers | 440 | 440 | 一致 |
| fixtures | 340 | 340 | 一致 |
| semanticOperations | 10 | 10 | 一致 |
| tools | 16 | 16 | 一致 |

资源复算读取 `assets/content/examples.json` 与 `assets/content/tutorials.json`。
`runnerPasses` 等于包内示例数。
这是通过态的必然推论。它不是静态证明实际运行。

## 冻结实现声明核对

| 声明 | 源码证据 | 结论 |
| --- | --- | --- |
| `historicalReportRejected` | 源码含 `report.status must be passed` | 一致 |
| 编译产物身份 | 源码读 `module.json` 与 `libflutter.so` | 一致 |
| 读取后重算 HAP | 源码两次调用 `_sha256_file`，并有 `HAP changed during verification` | 一致 |
| 输入错误映射 `ValueError` | 源码含 `ValueError` 子类 | 一致 |
| `cleanupError` 仍拒绝 | 源码无 `cleanupError` 特判，测试含 `test_rejects_log_only_cleanup_error` | 一致 |
| 限制值 | `MAX_HAP_BYTES` 512 MiB，日志 16 MiB，JSON 16 MiB，成员 256 MiB，总计 768 MiB | 一致 |

## 观察与缺口

1. `validation.json` 只哈希两个 Python 文件。
2. `README.md` 与 `.gitattributes` 未纳入哈希清单。
3. `unittest.log` 由 `unittestLogSha256` 单独覆盖。
4. `unittestLog` 记录本机绝对路径 `D:\MyNewProjects\qfli_json\build\device-evidence-final-check\unittest.log`。
5. 冻结目录含 `__pycache__`。它不在声明范围。
6. `validation.json` 未记录自身哈希。
7. 上述缺口不改变现有哈希结论。
8. 上述缺口可能影响日后冻结集的完整性判断。

## 边界

- 本复核只读文件。
- 本复核不重跑测试。
- 本复核不运行设备。
- 本复核不证明实际安装。
- 本复核不证明硬件来源。
- 本复核不证明 grant 真实。
- 79 项为离线合成用例。
- 合成用例不能写成设备通过。

## 复核命令摘要

只读脚本完成下列动作。

- 读取 `validation.json`。
- 计算冻结文件 SHA-256 与字节数。
- 计算工作副本 SHA-256。
- 计算 `unittest.log` 两处副本 SHA-256。
- 从 `assets/content` 复算指标。
- 读取源码常量与声明字符串。

脚本未写入冻结目录。
脚本未写入工作副本。
脚本只输出到标准输出。
