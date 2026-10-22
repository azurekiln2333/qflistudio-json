# 家族交付与 artifact 来源核对 — 2026-10-23

本报告记录 2026-10-23（Asia/Shanghai）已经完成的只读核对。范围为本地 Git HEAD、remote/push URL 配置、Trellis handoff/publication 引用的提交对象及祖先关系，以及现有 source/artifact 报告和现存 HAP/JSON 的只读 hash/结构比较。它是一个时间点的 source/artifact 审查；各 owner 仍在工作，不是对所有仓库的原子冻结，也不是当前源码的运行时验收。

写入本报告时未继续开展新审查。唯一写入路径为 `qfli_json/.trellis/tasks/10-22-offline-json-ide/research/family-artifact-audit-20261023.md`。没有改动兄弟仓库或共享 core，没有联网、fetch、push、构建、测试、安装或设备操作，没有管理任何运行时进程。远端实时状态未复核；保存的 push/ls-remote 回执属于原报告执行时的证据。

以下仓库相对路径以 `D:/MyNewProjects/` 为基准；JSON 自有 `.trellis/...` 路径以 `qfli_json/` 为基准。本文只报告明确的版本边界，不把后续 owner 的正常修改称为证据造假或已证实产品故障，也不宣称整个家族完成。

**结论。** 所查 handoff/publication 引用提交均在本地存在，且是对应仓库所观察 HEAD 的祖先。没有发现明确的 owner 冲突，或把普通 HAP 直接冒充验证 HAP 的错误声明。发现 Web 当前两对课程晚于现存包、JSON 当前 16 个 core 文件晚于设备快照、Python 当前 FFI 晚于模块审计包三处明确来源漂移。现存包均仍匹配其报告 hash，原报告可继续证明归档版本，不能自动证明后来源码。

**Web：两对课程已修改，但现存普通包和验证包仍含旧目录。**

依据：

- `qfli_web/.trellis/tasks/10-22-standalone-offline-ide/research/hap-481-inspection.json:3` / `:5` 记录普通 HAP 路径及 hash，`:18` / `:23` 记录其两个目录资源；`:143` / `:145` 和 `:158` / `:163` 分别记录 ohosTest HAP 及目录。
- `qfli_web/.trellis/tasks/10-22-standalone-offline-ide/research/ohos-481-final.md:3` 记录真实 OHOS ArkWeb 全量 474/481、7 fail、4,012 assertions；`:7` 为 started `2026-10-22T16:17:14.274Z`。
- 当前来源：`qfli_web/assets/content/examples.json:4041` 为 `html-example-160`，`:9374` 为 `js-example-053`；`tutorials.json:8300` / `:8320` 为 HTML 对应教程/lesson，`:19191` / `:19210` 为 JavaScript 对应教程/lesson。

| 对象 | 报告与现存 HAP 内目录 | 审查时当前源码 |
| --- | --- | --- |
| examples.json | 798,654 bytes；`50b77850b99e0889a35163d5fb16f9ecc020970f7f0bc8c0e5ef48a77a0dddfc` | 800,054 bytes；`b40f900eaf6caa44abc2d1d9fb26d695f8571f8a7394408b99b4dd11632a57cd` |
| tutorials.json | 1,393,445 bytes；`b9fd7227ed11d13d81c0663dd51a84f0b7cfdefb5c3a48cdd64fdcd7674d7424` | 1,395,900 bytes；`fe05fd1b3164219bba9b259b1aa3564b2052dd816c857c0e076cfed15d077f89` |

只读打开现存普通 HAP ZIP 并解析 JSON 后，确认不是只有 JSON 空白变化：481 个 example ID 均保留，但 `html-example-160`、`js-example-053` 的 `code` 和 `expectedOutput` 已不同；对应 tutorial lesson 的 code/output/explain 等也已不同。没有增删课程 ID。

普通 HAP 80,688,547 bytes，实际 hash 仍为 `b3ac4a805488789565715dc91037b9859da4333accf563d18c03d0ce3b0cb6d6`；ohosTest HAP 165,793,100 bytes，实际 hash 仍为 `c18d88a5ba79abf1a93bd9aec2ac01dc753205eb6ad15a5c23f994d01a74a0f6`。两者与 `hap-481-inspection.json` 一致。由此只能认定最新两对课程修复尚未进入这两份现存包；474/481 结果不能证明新修复已经目标通过。后续最终包与目标重跑仍归 Web owner。

**JSON：普通包保持归档身份，当前共享 core 已有 16 个文件漂移。**

`research/ohos-normal-artifact.json:13` 的普通 HAP hash 为 `a7b17b33ca7a97ccdbc62ca5addbf31bf8f960ff716146298f9ac2fc48aebfa7`，现存普通 unsigned HAP 仍完全匹配。

`research/ohos-normal-source-snapshot.json:2` 的 capture 时间为 `2026-10-22T13:07:01.261343+00:00`，`:3` 明确范围为 app/core lib Dart 与 app content JSON。只读重算归档 160 个文件后，app 文件全部一致，以下 16 个 core 文件不同：

- `core/lib/content/local_content_adapter.dart`
- `core/lib/editor/editor_controller.dart`
- `core/lib/editor/editor_page.dart`
- `core/lib/editor/editor_problems_bar.dart`
- `core/lib/editor/file_explorer.dart`
- `core/lib/editor/retained_editor_host.dart`
- `core/lib/editor/terminal_pane.dart`
- `core/lib/pages/home_page.dart`
- `core/lib/pages/local_content_pages.dart`
- `core/lib/pages/points_page.dart`
- `core/lib/pages/tasks_page.dart`
- `core/lib/pages/tools_grid.dart`
- `core/lib/services/code_import_service.dart`
- `core/lib/services/process_supervisor.dart`
- `core/lib/services/studio_profile.dart`
- `core/lib/services/task_activity_service.dart`

例如快照中的 editor controller/page/Problems/explorer 分别在 `ohos-normal-source-snapshot.json:145`、`:165`、`:173`、`:181`，process supervisor/profile 在 `:501`、`:545`。这里的 `core/` 对应共享 `qfli_studio_core/` 来源。

C 的旧 JSON 审查“当时仅两个 core 文件不同”仍是正确的历史观察，不能继续用作当前差异数量。`ohos-normal-artifact.json:9` 的 `sourceChangesAfterSnapshot:[]` 是当次构建检查字段，不是对未来工作树的永久保证。`research/ohos-ui-acceptance.json:59` 已明确 “Device results bind the archived source snapshot, not later shared-core edits”，这一限制正确。普通 HAP/UI 与 340-case harness 证明继续绑定其归档 bytes，不能升级为当前 core `e025805b` 的设备验收。

**Python：模块审计包仍完好，FFI 来源已变化。**

`qfli_python/.trellis/tasks/10-22-python-offline-modules/research/ohos-audit-build-ready.json:3` 明确 target 为 `build/python_module_audit/main.dart`，不是普通 `lib/main.dart`。`:12` / `:14` 记录默认 signed HAP，`:176` 开始记录 product source digests，`:180` 记录 `lib/python_ffi.dart`；`:200` / `:202` 记录独立保存的模块审计 HAP。

八个捕获 product source hash 中，仅 `lib/python_ffi.dart` 不匹配：报告为 `ba73e80c6a1c60d7648be7318938dd8023f33468830101afd7a5f06064bcb490`，审查时当前文件为 `15ac3f0075e21ea00f5c4c6bbb15fe74af6fafe644e857e8cc923f5efdbe9648`。相对 foundation commit，该文件存在 3 行增加、28 行删除；本报告未执行或评估这份后续实现的运行行为。

默认 signed HAP 与独立 `build/artifacts/python-modules-x64-d1387df94ebe8cb7.hap` 都仍为 `d1387df94ebe8cb74513a0f71253d8723a915cc7fd64af7b5c6d2f0c0b9cdaaf`，与原报告一致。这证明保留包身份未变化，不证明当前 FFI 已打包或通过目标。模块 build-ready 与当前内容 host pass 也不能替代尚未建立的 installed module/import/debugger 门禁。

**本地提交、HEAD 与 remote 边界。** 以下为只读观察到的 HEAD；push 目的地按配置去重，统计包括多个 remote 或同一 remote 的多个 `pushurl`。

| 仓库 | 观察 HEAD | push 目的地 | 本地提交关系/交付范围 |
| --- | --- | ---: | --- |
| qfli_c | `2cccdbeb85ea5994898fd75a82aa756c07786324` | 5 | tools `343b637` 为祖先；compiler 交付 `2cccdbeb` 等于 HEAD。 |
| qfli_dart | `b90f4b93cc5c3f1cea3d3434ecbe61006a8d81ae` | 5 | 已引用 handoff 提交等于 HEAD；新课程/runtime/device 批次另有未完成门禁。 |
| qfli_go | `82e17af4233e3aa2c6dd8eac2cb3f808f0f20a4f` | 5 | 当前 HEAD 是既有 release/Android handoff；不把它称为当前 10-22 批次交付完成。 |
| qfli_java | `4d5d2a308a8a25d7bf82b32610a496c6dd5e2232` | 5 | `142a9f0`、`a377d1b`、`f461881` 均存在且为祖先；Java-only core `9a1c8b9` 亦为当前 core HEAD 祖先。 |
| qfli_json | `8f4d8e363bdb6d92e0641d5d7387b1fd6e34b358` | 0 | 实现 `6df694e3` 存在且为祖先；无配置推送目的地。 |
| qfli_lua | `327b7c54d04bc184e03171f52da942c2157083b1` | 5 | 是既有 mirror handoff；当前 `requirements-evidence.md:22` 明确新会话 code commit/push 未完成。 |
| qfli_note | `16e6a38892ae9d0a41eb5cb157d563ccadd3f9ab` | 0 | `a7509155` 存在且为祖先；当前 HEAD 为后续证据文档提交，无 remote。 |
| qfli_python | `a1a953bd5e8d7a3cc127859876de6f19b20aea1e` | 5 | module foundation 等于 HEAD；保存回执指向 `release/python-storefront-20261015` 分支。 |
| qfli_rust | `78fb7b149c140e589177bd5d7ac4f91231011a70` | 5 | 一个 remote 配五个 push URL；当前 10-22 批次没有已完成交付提交声明。 |
| qfli_sql | `3bd36f1a0c5759f568d5e9eea823064b877d8bb0` | 5 | product `9f92d49`、初始 publication `3dfb073` 均存在且为祖先；最新是六个 scoped commits。 |
| qfli_web | `e0f81a56230ec27890b67eb9ac0c1df71a805c71` | 5 | checkpoint 等于 HEAD；回执指向 `feat/offline-web-ide`，明确排除 ongoing catalog/panel 工作。 |
| qfli_studio_core | `e025805b60435fdedafd33e60082dc660afebe5a` | 4 | 所查 `ef345913`、`daddce27`、`96e6833`、`f8edb042`、`0ec321c`、`9a1c8b9` 均存在且为祖先。 |

交付依据行号：

- C/Dart：`qfli_c/.trellis/tasks/10-22-offline-standalone-ide/research/acceptance.md:19`、`:23`。
- Java：`qfli_java/.trellis/tasks/10-22-offline-ide-completeness/research/java-final-handoff.md:92`–`:99`（逐项提交和原推送范围）。
- Python：`qfli_python/.trellis/tasks/10-22-python-offline-modules/research/module-foundation-push.json:4` / `:5`，五份回执的 `verified` 为 true；本次未联网重查。
- SQL：`qfli_sql/.trellis/tasks/10-22-offline-ide-completeness/research/publication-20261023.md:3`–`:5` 为初始 `3dfb073`；最新 `research/requirements-evidence.md:17` 与 `build/offline-ide-check/publication-docs-1023.json:3` 为六提交 `3bd36f1`。旧五提交描述是早先 checkpoint，不是最新发布 tip。
- Web：`qfli_web/.trellis/tasks/10-22-standalone-offline-ide/research/web-push-checkpoint.json:2`–`:4` 明确六个 checkpoint、scope 和 feature 分支，后续代码不属于该发布声明。

只有一个 remote 名称不代表只有一个推送站点：SQL、Rust 的 origin 都有五个 push URL，Python、Web 也有多 push URL。部分本地 remote-tracking refs 仍停在旧 main；直接 URL 或 feature/release 分支发布可以不更新这些 tracking refs。不能据此否定保存的推送回执，也不能从回执推断本次审查时远端未变化。本报告没有发起网络查询。

**其余包身份与所有权核对。** 下列现存包已在本次只读审查中重算，与各自已有报告完全一致：

| 产品/包 | SHA-256 | 证据边界 |
| --- | --- | --- |
| C ordinary signed ARM64 | `1ab90015df9045bd8246ea58b24ccca53dfd6ae2b07320490897eaf9afeefb3c` | `research/code-analysis-package-evidence.json`；其八个捕获 product source hash 也均一致，`:8` / `:26` 明确 app/device execution false。 |
| Note ordinary unsigned | `ba7c21824970b177a0830030198b7e6b849864ba115da86621d7ed1d7a4632d5` | `research/note-package-evidence.json:2`–`:4` 明确只证明 package contents，不证明 signing/device。 |
| Java ordinary signed main | `71c5c823e7bc29673d0295f0272c7be7f06f73b2d091666105f92c3de8f9c387` | `research/java-main-ohos-x64-build.json` 与 `java-final-handoff.md:37` / `:48`；runtime acceptance 的 target/hash 与普通 main 分别记录，没有把两包身份合并。 |
| SQL full audit signed | `0c5007b468e3e525d687b4e52983865b4c84d6ad2a89dd006aaf83bd8df76d78` | `research/publication-20261023.md:35`–`:40` 明确 audit bundle `com.azurekiln.qfli.sqlab.audit`，normal target UI 与设备门禁仍开。 |

所有权依据一致：C `research/acceptance.md:4` 将公共 core 唯一集成权交给 C；Lua `research/requirements-evidence.md:21` 保留同一边界，并把 provider/tests 与 shared writes 区分；Note handoff 也声明未改 core/sibling。没有从 Git HEAD、旧清单或 WIP 推导无主任务，也没有发现足以认定抢改的直接证据。

这份记录可用于 owner 的下一次 source/package/device handoff。上述漂移不要求撤销历史报告，但最终交付必须继续明确所验证的源码、artifact、入口与平台，不能把历史通过自动附着到后来源码。
