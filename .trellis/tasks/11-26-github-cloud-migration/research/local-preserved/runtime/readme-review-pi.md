# README 三语独立事实与规则审查（pi）

审查时间：2026-10-26
审查范围：`README.md`、`README.zh-TW.md`、`README.en.md`
审查方式：只读。未修改任何 README，未 commit，未 push，未跑重型测试与设备操作。

结论：**三语 README 事实基本准确，机械 lint 全绿。需改动 3 项**（1 项中文一词一义，2 项英文事实精度）。无阻断项。

---

## 1. 机械检查结果

命令：

```text
python scripts/ste-lint-zh.py README.md README.zh-TW.md
python scripts/ste-lint-zh.py --max-chars 25 README.md README.zh-TW.md
```

| 文件 | 默认 40 字上限 | 收紧 25 字上限 |
| --- | --- | --- |
| `README.md` | 硬违规 0，发现 0 | 硬违规 0，发现 0 |
| `README.zh-TW.md` | 硬违规 0，发现 0 | 硬违规 0，发现 0 |

合计 2703 字，每 100 字 0.0 处。25 字上限下仍为 0，说明每条句子都满足「指令 ≤ 25 字」与「说明 ≤ 40 字」。

`python scripts/ste-lint-zh.py --selftest` 自检通过。

英文 README 不受该 lint 约束，未做机械检查。

## 2. 需改动项

### 2.1 `README.md`：`校验` / `验证` 混用（一词一义，建议改）

同一概念「validation」在同一篇出现两个词，机械 lint 的 `synonym-rotation` 组不含这一对，故未报。

- L145 `现有验证记录如下。`
- L158 `主机证据见[验证记录](...)。`

全文计数：`校验` 19 次，`验证` 2 次。

建议：把 2 处改为 `校验`，即「现有校验记录如下。」「主机证据见[校验记录]」。

对照：`README.zh-TW.md` 用 `驗證` 21 次，`校驗` 0 次，全篇统一，无需改。

### 2.2 `README.en.md` L26：标签名加了反引号但 UI 实际是中文（事实精度，建议改）

原文：

```text
The document editor has three tabs. `Problems` lists diagnostics. `Structure` lists every node by JSON Pointer and jumps to the source on tap. `Output` records local check results.
```

源码 `lib/json/json_document_page.dart:299-301` 的实际标签：

```dart
Tab(text: '问题 ${inspection?.problems.length ?? 0}'),
const Tab(text: '结构'),
const Tab(text: '输出'),
```

反引号表示字面标签，但界面显示的是 `问题` / `结构` / `输出`，不是 `Problems` / `Structure` / `Output`。

建议：去掉反引号，改为普通名词描述（Problems / Structure / Output 作为英文译名而非字面 UI 文本），或直接写中文标签。

同类对照：同文件 L28 用 `` `校验` ``、`` `格式化` ``、`` `键排序` `` 引用编辑器动作，这三个与源码一致（`json_document_page.dart` 中 `Text('校验')`、`Text('格式化')`、`Text('键排序')`），写法正确。L23 与 L22 的 `Problems entry` 未加反引号，写法也正确。只有 L26 三处加了反引号。

### 2.3 `README.en.md` L245：清单权限表述过宽（事实精度，建议改）

原文：

```text
- The OHOS and Android manifests request no internet permission.
```

实际：

- `ohos/entry/src/main/module.json5` 只申请 `ohos.permission.READ_PASTEBOARD`，无 INTERNET。属实的部分。
- `android/app/src/main/AndroidManifest.xml`（release/main）无 `uses-permission`，属实。
- 但 `android/app/src/debug/AndroidManifest.xml:6` 与 `android/app/src/profile/AndroidManifest.xml:6` 保留了 Flutter 默认的 `android.permission.INTERNET`。

测试 `test/json_offline_host_test.dart` 也只断言 `android/app/src/main/AndroidManifest.xml`，即 release 清单，未覆盖 debug/profile。

建议：改为 `The OHOS module and the Android release manifest request no internet permission.`，并可选加一句说明 debug/profile 清单保留 Flutter 开发期 INTERNET 权限。

## 3. 已核实为准确的事实

逐条与源码/证据比对，均成立。

### 计数

| 声明 | 验证方式 | 结果 |
| --- | --- | --- |
| 340 条示例 | `assets/content/examples.json` → `entries` 长度 340 | 属实 |
| 340 条教程 | `assets/content/tutorials.json` → `entries` 长度 340 | 属实 |
| 新增 240 条 | `catalog_audit.json` → `newExampleCount: 240`、`newTutorialCount: 240` | 属实 |
| 24 类、每类 10 条 | `catalog_audit.json` → `categories` 24 个键，各 10 | 属实，且明确限定为「新增内容」 |
| 440 条练习答案 | 设备报告 `exerciseAnswers: 440` | 属实 |
| 340 个输入样本 | 设备报告 `fixtures: 340` | 属实 |
| 10 条补丁/合并承诺 | 设备报告 `semanticOperations: 10` | 属实 |
| 16 张工具卡片 | `lib/json/json_tools.dart` → `enum JsonOperation` 共 16 项 | 属实 |
| 12 个测试文件 | `test/*_test.dart` 计数 12 | 属实 |

### 工具与命令

- 16 张卡片名称与用途，与 `JsonOperation` 的 `title` / `description` 逐一对应，三语一致。
- 终端 6 条只读命令 `check` / `format` / `minify` / `sort` / `stats` / `get`，与 `json_runner.dart` 允许集合一致。
- `json help` 打印列表：`args.first == 'help' || '--help'` 分支存在，属实。
- 退出码 127：`kProgramNotRunExitCode = 127`，且 `JsonRunner` 对「文件不在项目内」「文件读不到」均返回它，属实。

### 语义与边界

- Merge Patch 按 RFC 7396：注释 `/// RFC 7396: null members delete; arrays/scalars replace in full.`，属实。
- JSON Patch 按 RFC 6902：`/// RFC 6902.` 与 `add/remove/replace/move/copy/test` 分支存在，属实。
- 结构差异生成可应用 JSON Patch：`diff()` 返回 `{'op': 'remove'|'add', 'path': ...}` 列表，属实。
- JSON Lines 报原始行号：`'JSON Lines 第 ${i + 1} 行：...'`，属实。
- Schema 支持关键字集合与「拒绝不支持关键字、不取远程 Schema、`$ref` 仅本地、pattern 用 Dart Unicode 正则、嵌套资源与其它方言拒绝」均与 `LocalJsonSchema.supported` 及校验逻辑一致，属实。
- 上限：2 Mi（`maximumLength`）、4 Mi（`maximumOutputLength`）、128 层（`maximumDepth`）、50000 节点（`maximumNodes`）、200000 CSV 单元格（`maximumCsvCells`）、250000 补丁节点（`maximumPatchWorkNodes`）、5 秒超时（`Duration(seconds: 5)`），全部属实。运行入口另限 2 MiB UTF-8 字节，`json_runner.dart` 中 `file.length() > maximumLength` 属实。
- int64 越界报错：属实。
- `isOffline` 与 `offlineOnly` 存在，`jsonProfile` 中 `isOffline: true`，`offlineOnly` 默认取 `isOffline`，测试断言两者为 true，属实。
- 只接受 `.json`：`supportedFileExtensions: ['.json']`，属实。
- 入口优先 `data.json`、其次 `src/data.json`：`entryFileNames: ['data.json', 'src/data.json']`，属实。
- JSON 模板内容 `{"name": "QFLI project", "version": 1}` 写入 `src/data.json`：与 `project_templates.dart` 的 `_jsonData` 逐字一致，属实。
- 审计报告文件名 `json_verification_result.json`、新 `runId`、写入失败即判失败：与 `json_verification_report.dart` 一致，属实。
- OHOS 宿主拒绝 `openAgreement` / `openUrl`：`EntryAbility.ets` 返回 `OFFLINE_ONLY` 错误，属实。

### 验证记录与情态

- 主机 124 项通过、`lib` 与 `test` 无问题、三份资源一致，对应 `research/host-20261024-published-core.md`，属实。
- `2026-10-22` OHOS API 26 x86_64 通过 340 条示例：对应 `ohos-harness-final-result.json` 的 `platform: ohos`、`runnerPasses: 340`、`failures: []`，属实。
- 历史证据未被写成当前全量设备通过。三语均保留「可能不覆盖后续共享核心修改」「也许尚未证实」「may still depend on the platform and the package」等情态，符合「不得改动情态」要求。
- 未把桌面测试当作设备通过：`README.en.md` 明确列出「Desktop-only tests as device proof. The two are separate evidence.」，`README.md` 写「主机测试不能证明设备通过。」，两者一致。
- 签名、实体 ARM64、兄弟产品运行时均列为未验收，属实。

### 链接与语言切换

- 三语切换链接统一为 `README.md`（简体）、`README.zh-TW.md`（繁体）、`README.en.md`（英文），三文件写法一致。
- 三个 README 文件均存在，切换链接无死链。
- 正文链接全部可达：`.trellis/tasks/10-22-offline-json-ide/research/host-20261024-published-core.md`、`.trellis/spec/json-offline.md`、`lib/json/json_schema.dart`、`LICENSE`，`Test-Path` 全部为 True。

## 4. 远程地址与推送能力

```text
git remote -v   → 无输出
git config --get-regexp '^remote\.'  → 无输出
```

当前 checkout **没有配置任何远程地址**，因此**不能 push**。这与 PRD 记录一致（「Product repository has no remote, so a push cannot be performed without an authoritative destination.」）。本审查未执行 push。

分支：`feat/offline-json-workbench`。工作区另有非本任务改动（`ohos/build-profile.json5`、`ohos/.../main_pages.json`、`AgreementReader.ets`、`LICENSE`、`AGENTS.md`、`scripts/`、桌面 registrant 等），由根代理统一整合提交。

## 5. 写作 skill 说明

仓库内未找到独立写作 skill 文件。受控中文规则定义在 `AGENTS.md`（TRELLIS 区块之外），机械检查工具为 `scripts/ste-lint-zh.py`。本次审查以这两者为准，未引用外部写作 skill。

## 6. 建议改动清单（交给写作者）

1. `README.md` L145、L158：`验证` → `校验`。
2. `README.en.md` L26：去掉 `Problems` / `Structure` / `Output` 三处反引号，或改为中文标签。
3. `README.en.md` L245：`The OHOS and Android manifests` → 限定为 OMOS module 与 Android release manifest，并说明 debug/profile 保留开发期 INTERNET。

改动后重跑：

```text
python scripts/ste-lint-zh.py README.md README.zh-TW.md
```
