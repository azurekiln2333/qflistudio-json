# 家族产品编辑器接入审查（2026-10-23）

## 范围与证据边界

本记录整理已经完成的只读源码审查，覆盖 11 个独立产品的 `main/profile`、代码检查器，以及共享编辑器的文档工具、运行入口和语法高亮接入。工作区基目录为 `D:/MyNewProjects`；下文相对路径以 `qfli_json` 仓库根目录为基准，例如 `../qfli_java/lib/main.dart:35` 对应 `D:/MyNewProjects/qfli_java/lib/main.dart:35`。

**本次为 source-only 审查，未运行 build、test 或设备验证，未修改产品或共享内核源码。** 结论来自源码控制流，不能替代目标平台安装包或真机结果。各仓库处于并行开发中，行号记录审查时的位置；本记录不构成冻结提交快照的验收证明。

## 11/11 产品已接入代码检查器

没有发现独立产品遗漏 `codeAnalyzer` 配置。各产品的运行或文档入口如下；存在 provider 配置不等同于所有平台后端均可用。

| 产品 | Profile 中的检查器证据 | 运行或文档工具接入证据 |
| --- | --- | --- |
| C/C++ | `../qfli_c/lib/main.dart:34`：`ForgeCodeAnalyzer` | 同文件 33 行 `ForgeProgramRunner`；46 行明确标记运行状态 `unavailable` |
| Dart | `../qfli_dart/lib/main.dart:35`：`DartCodeAnalyzer` | 同文件 32 行 `DartProgramRunner`；运行状态依目标平台设置 |
| Go | `../qfli_go/lib/main.dart:39`：`GoCodeAnalyzer` | 同文件 38 行 `GoProgramRunner` |
| Java | `../qfli_java/lib/main.dart:35`：`JavaDiagnosticAnalyzer` | 同文件 34 行 `JavaProgramRunner`；45 行从实际 runner 可用性设置状态 |
| JSON | `lib/main.dart:37`：`JsonCodeAnalyzer` | 同文件 36 行 `JsonRunner`、39 行 `buildJsonDocument` |
| Script/Lua | `../qfli_lua/lib/main.dart:46`：`ProductCodeAnalyzer` | 同文件 45 行 `LuaProgramRunner`；检查器分派 Lua、JS/TS、Shell |
| Note/Markdown | `../qfli_note/lib/main.dart:38`：`NoteCodeAnalyzer` | 同文件 45 行 `MarkdownWorkspace.forRequest` 文档工作台 |
| Python | `../qfli_python/lib/main.dart:29`：`PythonCodeAnalyzer` | 同文件 28 行 `PythonProgramRunner` |
| Rust | `../qfli_rust/lib/main.dart:37`：`RustCodeAnalyzer` | 同文件 36 行 `RustProgramRunner`；39–42 行为移动平台选择原生分析 transport |
| SQL | `../qfli_sql/lib/main.dart:42`：`SqlCodeAnalyzer` | 同文件 31 行 `SqlProgramRunner`；35 行明确标记运行状态 `unavailable` |
| Web | `../qfli_web/lib/main.dart:38`：`WebCodeAnalyzer` | 同文件 37 行 `webPreviewFactory: WebRuntime.start` |

共享 `StudioProfile` 明确区分各能力：`../qfli_studio_core/lib/services/studio_profile.dart:133` 的空 runner 沿用默认运行逻辑；137 行的空 `codeAnalyzer` 表示未安装检查器，不会退回执行用户代码；141 行的空 debugger 表示不可用。

源码确认这些检查器有实际解析、编译检查或文档诊断实现，而非统一返回空列表：Dart 使用 analyzer 的 `parseString`（`../qfli_dart/lib/dart_tools.dart:81`）；Go 使用 `go/parser.ParseFile`（`../qfli_go/native/go_runtime/code_analysis.go:106`）；Java 调用 javac；Python 使用原生 compile-only 检查；Script 使用 QuickJS/TypeScript 语法路径；C/C++ 使用 Clang；Rust 使用 rustc metadata 分析或原生分析 ABI；SQL 使用词法分析及隔离 SQLite prepare-only 检查；Web 使用 HTML/CSS 解析器及 QuickJS；JSON 和 Markdown 使用各自文档诊断实现。语法检查成功并不证明类型、依赖或运行行为正确。

## 发现 1：Java 对不支持的活动文档可能显示“未发现问题”

**高置信度，建议由 Java 原 owner 修复。** 这是活动文档不受支持时误报 clean 的路径，不是认定 javac 对 Java 源码返回了模拟结果。

可触发场景是 Java 产品中打开项目内 README.md 或其他非 Java 文档，且项目没有 Java 源文件。共享文件树的普通打开路径没有按 profile 扩展名过滤（`../qfli_studio_core/lib/editor/file_explorer.dart:773`、775 行）。随后存在以下静态代码链：

1. 共享控制器按活动文件构造请求，将实际语言与活动路径传给 provider：`../qfli_studio_core/lib/editor/editor_analysis_controller.dart:177`。
2. `JavaDiagnosticAnalyzer.analyze` 未校验 `request.language`、`activeFilePath` 或活动快照是否属于 Java，只将所有文档文本交给项目检查：`../qfli_java/lib/java_diagnostics.dart:107`。
3. `analyzeProject` 只保留 `.java` 缓冲区（同文件 188 行），收集不到 Java 源时直接返回 `JavaAnalysisStatus.complete`（201–202 行）。因此该场景返回空诊断且没有 `unavailableReason`，实际并未检查活动 Markdown 等文档。
4. 共享控制器据此设置 `checked = true`：`../qfli_studio_core/lib/editor/editor_analysis_controller.dart:225`。
5. 状态栏在空诊断且已检查时显示“本地检查未发现问题”：`../qfli_studio_core/lib/editor/editor_problems_bar.dart:9`、11 行。

关键绝对路径定位：

- `D:/MyNewProjects/qfli_java/lib/java_diagnostics.dart:107`
- `D:/MyNewProjects/qfli_java/lib/java_diagnostics.dart:201`
- `D:/MyNewProjects/qfli_studio_core/lib/editor/editor_analysis_controller.dart:225`
- `D:/MyNewProjects/qfli_studio_core/lib/editor/editor_problems_bar.dart:11`

建议 Java owner 在 adapter 入口明确拒绝非 Java 活动文档，并校验项目归属及活动快照/版本；对不支持输入返回可见的 `unavailableReason`。后续可由该 owner 增加“只有 README.md”“活动非 Java、项目含 Java 源”等回归用例。本次未实施修复或运行这些用例。

## 发现 2：C++ owner 内 `.h` 的诊断语言与高亮语言不一致

**高置信度，建议由 C/C++ 原 owner 协调共享内核修复。** `.h` 不是没有 grammar，而是当前固定选择 C grammar。

- `../qfli_studio_core/lib/editor/highlight_themes.dart:59` 将 `.h` 固定映射为 `'c'`，而 `.hpp`、`.hh`、`.hxx` 等映射为 C++。
- 同文件 200 行的 `themeFor` 只接收文件名、内容及设置；230 行据自定义 grammar 或扩展名选择语言，没有 owner 项目类型。
- 实际编辑器调用同样只传 `open.name`：`../qfli_studio_core/lib/editor/editor_page.dart:2988`。
- 与此相对，分析语言映射已经在 `../qfli_studio_core/lib/editor/editor_analysis_controller.dart:303` 对 `.h` 使用 owner type：`cpp`/`c++` owner 选择 C++，其他 owner 选择 C。

因此 C++ 项目的 `.h` 标签会按 C++ 检查、按 C 高亮，`namespace`、`template` 等 C++ 结构的着色可能与 `.hpp` 等同内容文件不一致。

关键绝对路径定位：

- `D:/MyNewProjects/qfli_studio_core/lib/editor/highlight_themes.dart:59`
- `D:/MyNewProjects/qfli_studio_core/lib/editor/highlight_themes.dart:200`
- `D:/MyNewProjects/qfli_studio_core/lib/editor/editor_page.dart:2988`
- `D:/MyNewProjects/qfli_studio_core/lib/editor/editor_analysis_controller.dart:303`

建议 C/C++ owner 与共享内核 owner 统一 owner-aware 的语言选择，并保留用户自定义 TextMate grammar 的优先级。后续可核对 C 与 C++ owner 下同名 `.h` 的选择结果。本次未修改高亮实现或运行回归。

## 未认定为缺陷的路径

- 已注册所有独立产品主语言所需的内置 grammar（`../qfli_studio_core/lib/editor/highlight_themes.dart:34`、54 行），未找到主语言完全缺失的接入。`.luac`、`.mpy`、`.dill` 等编译输入没有源码高亮，不据此认定为 bug。
- Note 的文档工作台与 JSON 的文档工具是真实入口。共享工具栏在存在适用文档工具时显示“编辑与预览”，不进入普通 Run（`../qfli_studio_core/lib/editor/editor_page.dart:1902`）。普通 JSON 数据没有调试器不是本次缺陷。
- Web 的 HTML 运行会调用产品 `webPreviewFactory`，缺省才使用共享本地服务器（`../qfli_studio_core/lib/editor/editor_page.dart:1435`）。因此不能仅因 profile 没有 `ProgramRunner` 认定 Web 缺失运行能力。
- 已读 provider 的后端缺失、超时及损坏结果分支大多显式报告 unavailable，例如 C/C++ `../qfli_c/lib/forge_code_analyzer.dart:149`、168 行，Python `../qfli_python/lib/python_runner.dart:171`，Rust `../qfli_rust/lib/rust_code_analyzer.dart:112`，Web `../qfli_web/lib/services/web_code_analyzer.dart:205`。这些状态与“检查完成且未发现问题”需要保持区分。
- SQL 的 MySQL 方言和资源限制等不完整检查路径会保留说明（`../qfli_sql/lib/sql_code_analyzer.dart`）；本次没有把词法检查等同于服务端完整语义验证，也没有新增 SQL 缺陷结论。

后续修复归属建议为 Java 与 C/C++ 原 owner；本记录仅提供静态证据和建议，不替代各 owner 的实现、测试及目标平台验收。
