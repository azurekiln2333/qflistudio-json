# 三语 README 三版一致性校验报告

日期：2026-10-26。只读。

## 1 范围与方法

- 对照 `README.md`、`README.zh-TW.md`、`README.en.md`。
- 逐条对照源码、内容资产、发布记录。
- 未运行 SDK、Flutter、hdc 与重型测试。
- 未改项目文件。未 commit。
- 中文两版已跑 `scripts/ste-lint-zh.py`。
- 结果：两版硬违规 0 项。

## 2 结论

- 未发现错误陈述。三版数字与源码一致。
- 发现 7 项高优先缺项。多为一方有、他方无。
- 发现 6 项一般缺项。
- 发现 5 处精度问题。严重度低。
- 语言切换链接三版一致。目标文件均存在。

## 3 已核实事实

| 事实 | 值 | 依据 |
| --- | --- | --- |
| 示例数 | 340 | `assets/content/examples.json` |
| 教程数 | 340 | `assets/content/tutorials.json` |
| 课节数 | 340 | 同上 |
| 新增条目 | 240 | `assets/content/catalog_audit.json` |
| 新增分类 | 24 类、每类 10 | 同上 |
| 练习答案 | 440 | 资产实算 |
| 输入样本 | 340 | 资产实算 |
| 语义操作 | 10（7 补丁 + 3 合并） | 资产实算 |
| 工具卡片 | 16 | `lib/json/json_tools.dart` |
| 终端命令 | 6 条只读 | `lib/json/json_runner.dart` |
| 退出码 | 0 / 1 / 127 | `json_runner.dart`、core 常量 |
| 入口顺序 | 先 `data.json`、后 `src/data.json` | `lib/main.dart` |
| 测试文件 | 12 个 | `test/` 实算 |
| 记录主机测试 | 124 项通过 | `research/host-20261024-published-core.md` |
| 记录设备 | API 26 x86_64、340 条 | `research/ohos.md` |
| 剪贴板权限 | 仅 `READ_PASTEBOARD` | `ohos/.../module.json5` |
| Android 清单 | 仅 debug 与 profile 有 INTERNET | `android/app/src/*/AndroidManifest.xml` |

## 4 命令覆盖

| 命令 | `README.md` | `README.zh-TW.md` | `README.en.md` |
| --- | --- | --- | --- |
| `flutter pub get` | 有 | 有 | 有 |
| `flutter run` | 有 | 有 | 有 |
| `flutter test` | 有 | 有 | 有 |
| `dart analyze lib test` | 有 | 有 | 缺 |
| `dart format --output=none --set-exit-if-changed lib test` | 有 | 有 | 缺 |
| `python tool/build_json_content.py --check` | 有 | 有 | 有 |
| `flutter run --dart-define=QFLI_VERIFY_CATALOG=true` | 有 | 有 | 有 |
| `json check|format|minify|sort|stats|get` | 有 | 有 | 有 |
| `json help` | 缺 | 缺 | 有 |

## 5 事实覆盖

| 事实项 | `README.md` | `README.zh-TW.md` | `README.en.md` |
| --- | --- | --- | --- |
| 340 示例、340 教程、240 新增 | 有 | 有 | 有 |
| 24 类、每类 10 | 缺 | 缺 | 有 |
| 440 练习答案 | 缺 | 缺 | 有 |
| 340 输入样本 | 缺 | 缺 | 有 |
| 10 条语义操作 | 缺 | 缺 | 有 |
| 16 工具卡片 | 有 | 有 | 有 |
| 6 条终端命令 | 有 | 有 | 有 |
| 退出码 0 / 1 / 127 | 缺 | 缺 | 有 |
| 8 项资源上限 | 有 | 有 | 有 |
| Schema 子集与边界 | 有 | 有 | 有 |
| 不提供断点调试器 | 有 | 有 | 缺 |
| 124 项主机记录 | 有 | 有 | 有 |
| API 26 标注 | 有 | 有 | 缺 |
| x86_64 标注 | 有 | 有 | 有 |
| 签名材料缺失 | 有 | 有 | 有 |
| 实体 ARM64 未验收 | 有 | 有 | 有 |
| 兄弟产品未验收 | 缺 | 缺 | 有 |
| 桌面测试不等于设备证据 | 缺 | 缺 | 有 |
| Android 清单明细 | 缺 | 缺 | 有 |
| HttpOverrides 断言 | 缺 | 缺 | 有 |
| 工作区项目身份与路径 | 缺 | 缺 | 有 |
| RFC 6901 / RFC 7396 | 缺 | 缺 | 有 |
| 12 个测试文件 | 缺 | 缺 | 有 |
| 其他 Flutter 通道 | 缺 | 有 | 有 |
| 结果依赖平台与套件 | 缺 | 有 | 有 |
| 项目结构表 | 缺 | 缺 | 有 |
| 编号使用步骤 | 有 | 有 | 缺 |

## 6 高优先缺项

### 6.1 en 缺两条校验命令

- 现状：`README.en.md` 的 `## Verification` 只有 `flutter test`。
- 缺失：`dart analyze lib test`。
- 缺失：`dart format --output=none --set-exit-if-changed lib test`。
- 依据：`.trellis/.runtime/run_json_release_gate.ps1` 第 56 行与第 59 行。
- 影响：英文读者漏掉两条真实门槛命令。
- 建议：补入 `## Verification`，位置对齐中文版。

### 6.2 中文两版缺内容度量明细

- 现状：`README.md` 第 18 行只写 340、340、240。
- 缺失：24 类、每类 10 条。
- 缺失：440 条练习答案、340 个输入样本。
- 缺失：10 条语义操作承诺。
- 依据：`assets/content/catalog_audit.json`，资产实算。
- 影响：读者无法判断校验深度。
- 建议：加入三行到五行明细，或加入小表。

### 6.3 中文两版缺退出码表

- 现状：只写“运行入口输出格式化的 JSON”。
- 缺失：合法输入 0、非法输入 1、缺失或越界 127。
- 依据：`lib/json/json_runner.dart` 与 `kProgramNotRunExitCode`。
- 影响：脚本化调用缺少判据。
- 建议：把 `README.en.md` 第 59 行附近的三行表译入中文版。

### 6.4 en 缺“不提供断点调试器”

- 现状：`README.en.md` 全文无 debugger 与 breakpoint。
- 依据：`README.md` 第 196 行、`README.zh-TW.md` 第 197 行。
- 依据：`research/evidence.md` 的 R9 行。
- 影响：英文版把能力边界写窄了。
- 建议：补一句到 `## Run and terminal` 或 `## Limits`。

### 6.5 中文两版缺两条验收门槛

- 现状：只写签名发行与实体 ARM64。
- 缺失：兄弟产品与本仓库证据互不覆盖。
- 缺失：桌面测试不等于设备证据。
- 依据：`README.en.md` 第 192、193 行。
- 依据：`research/evidence.md` 的“设备范围”段。
- 建议：补齐四行门槛，保持与英文版一致。

### 6.6 `README.md` 缺“其他 Flutter 通道”一句

- 现状：`README.md` 只写 OHOS 工具链要求。
- 缺失：其他 Flutter 通道也许可用，但无记录结果。
- 依据：`README.zh-TW.md` 第 103 行、`README.en.md` 第 123 行。
- 影响：简体版与另两版结论不同。
- 建议：按繁中版句式补入 `## 开发`。

### 6.7 中文两版缺 `json help` 与测试文件数

- 缺失：`json help` 可打印命令清单。
- 依据：`lib/json/json_runner.dart`，`help` 与 `--help` 均受支持。
- 缺失：测试文件 12 个。
- 依据：`test/` 实算 12 个 `.dart` 文件。
- 建议：各补一句。

## 7 一般缺项

| 缺项 | 缺在哪版 | 依据 | 建议 |
| --- | --- | --- | --- |
| Android 清单明细 | 中文两版 | `README.en.md` 第 245 行 | 补入离线段 |
| HttpOverrides 断言 | 中文两版 | `README.en.md` 第 248 行 | 补一句 |
| 工作区项目身份与最后路径 | 中文两版 | `README.en.md` 工作区段 | 补两行 |
| RFC 6901 与 RFC 7396 | 中文两版 | `README.en.md` 第 39、41 行 | 表格补注 |
| API 26 标注 | 英文版 | `README.md` 第 152 行 | 表格补注 |
| 项目结构表 | 中文两版 | `README.en.md` 项目结构段 | 可选 |

## 8 精度问题

1. 入口顺序未提项目配置覆盖。
   - 现状：三版均写“先 `data.json`、后 `src/data.json`”。
   - 依据：core `runner_service.dart` 先读 `ProjectConfig` 的 `entryFile`。
   - 建议：加一句“项目配置可覆盖该顺序”。

2. 简体版“其次读取”暗示到此为止。
   - 现状：`README.md` 第 51 行。
   - 依据：候选名之后还有一批默认入口名回落。
   - 建议：改为“其次 `src/data.json`”，不写“仅此两个”。

3. 问题面板标签含计数。
   - 现状：三版称标签为“问题”。
   - 依据：`json_document_page.dart` 第 299 行，标签为“问题 N”。
   - 建议：英文版括注带计数。

4. 124 项记录用串行并发。
   - 现状：三版只写 `flutter test`。
   - 依据：`run_json_release_gate.ps1` 第 58 行使用 `--concurrency=1`。
   - 建议：记录行注明串行运行。

5. 英文版高亮描述偏窄。
   - 现状：`README.en.md` 第 17 行写 keys、strings、numbers。
   - 依据：`JsonSourceController` 同时着色布尔与 null。
   - 建议：补“布尔与 null”。

## 9 未校验项

- 真实设备安装、签名发行、实体 ARM64。
- 后续共享核心修改对设备结果的影响。
- 三版对上游文档的引用是否最新。

本报告不改动这三处结论。它们沿用既有记录。

## 10 依据文件

- `lib/main.dart`
- `lib/json/json_tools.dart`
- `lib/json/json_runner.dart`
- `lib/json/json_document_page.dart`
- `lib/json/json_schema.dart`
- `lib/json/json_workbench.dart`
- `lib/content/json_content_repository.dart`
- `assets/content/examples.json`
- `assets/content/tutorials.json`
- `assets/content/catalog_audit.json`
- `ohos/entry/src/main/module.json5`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/src/debug/AndroidManifest.xml`
- `android/app/src/profile/AndroidManifest.xml`
- `../qfli_studio_core/lib/services/runner_service.dart`
- `.trellis/.runtime/run_json_release_gate.ps1`
- `.trellis/tasks/10-22-offline-json-ide/research/host-20261024-published-core.md`
- `.trellis/tasks/10-22-offline-json-ide/research/ohos.md`
- `.trellis/tasks/10-22-offline-json-ide/evidence.md`
