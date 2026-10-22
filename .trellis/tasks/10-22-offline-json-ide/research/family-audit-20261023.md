# 独立应用家族证据核对 — 2026-10-23

审查日期：2026-10-23，Asia/Shanghai。报告拥有者为 JSON 会话；本文件汇总本会话已经完成的家族只读审查，并在写入前补查引用路径及关键报告摘要。文中的“最新”均指本次实际检查到的最新证据，不表示对持续变化的全部工作树重新验收。

本次唯一写入路径为 `qfli_json/.trellis/tasks/10-22-offline-json-ide/research/family-audit-20261023.md`。未修改兄弟产品或共享 core，未运行构建、测试、全量课程验证、安装、设备命令或运行时进程。已保存报告的通过计数属于其原始作者的执行证据，本次没有重新执行这些检查。

以下路径均以 `D:/MyNewProjects/` 为基准，除原始需求附件另列绝对路径。原始需求已读：`C:/Users/lichengyu/.codex/attachments/a5c5fc51-abae-40c5-a792-7d88695907ce/pasted-text-1.txt`。需求覆盖所有独立应用、当前 OHOS 既有内容先验收、实质性新增超过 100、语言筛选/圆形标识、直接工具、真实编辑器诊断、持久树及多项目、可行离线调试/日志面板、高亮、C/C++ 本地头文件及 Python 离线模块。不能用单产品、host 或打包通过替代整个家族的目标设备验收。

**家族状态仍未完成。** C 总任务仍为 `in_progress`；多个产品的原始 OHOS 全量门禁、扩充、调试消费或最终交付仍未关闭。没有发现可以由 JSON 会话直接接管的无主产品实现任务。

**所有权与协调依据。** 已检查 C 总任务的 `prd.md`、`design.md`、`implement.md` 及 `research/acceptance.md`，根目录为 `qfli_c/.trellis/tasks/10-22-offline-standalone-ide/`。其中明确 C 是共享 core 唯一集成者，语言协调者拥有各自运行时、课程和 provider；各产品记录引用协调频道 `qfli-core-release-sync`。语言方获得的特定授权（如 Python 的 `core/tool/python_content/**` 与串行聚合生成窗口）不能推广为 JSON 的共享文件写入权限。

- C、Dart、Java、Lua、Note、Python 主任务及四个子任务、Rust、SQL、Web、JSON 的对应 10-22 `task.json` 均为 `in_progress`。
- Go 的 `10-22-go-curriculum-ohos`、`10-22-go-offline-ide` 为 `in_progress`；`10-22-standalone-ide-completeness`、`10-22-standalone-integration` 仍标 `planning`，但已有活跃子任务，不能据此视作无主。
- 多数 `task.json` 的 assignee 为通用 `lichengyu`，JSON 为 `codex`；这些字段不能单独识别当前会话。产品交付、协调记录与现有任务必须一起判断。旧清单中的未勾选项也不授予抢改权限。
- 历史设备队列或某次 Web 独占窗口不是当前设备所有权。本报告未查询或使用设备；后续设备动作应继续由当前协调者安排。

**共享功能的证据边界。** C 的 `research/acceptance.md` 记录共享筛选/圆形标识、高亮、Problems、owner-aware 多根工作区和树状态实现；core `daddce27` 的历史检查为 712 pass / 2 skip，工作区聚焦回归 27 pass。该记录同时保留真实设备交互门禁。`f8edb04` 发布可选 debugger provider/snapshot/cleanup API，不等于公共 Debug 控件已经交付；公共 Debug 控件、独立 Output/Debug Console/Ports UI、POSIX 后代进程取消仍是 C 所有的后续事项。Lua 最新记录还将 secondary-root Run、import rollback 与 supervisor 修复归给 C，JSON 不接管这些文件。

| 产品 | 最新已检查证据路径与计数 | 尚未通过或尚未证明的门禁 |
| --- | --- | --- |
| C/C++ | `qfli_c/.trellis/tasks/10-22-offline-standalone-ide/research/acceptance.md`、`research/code-analysis-20261022.md`：既有 native 200/200、重建 LLVM/WASI portable 200/200（host-only）；实际 Clang/WasmEdge/NAPI 桥 31 项及真实 unsaved-buffer 分析；当前 ARM64 包/签名材料已有证据。 | 当前所属应用安装包上的完整执行，尤其用户创建的本地/嵌套头文件；计划新增 160 对尚未完成；公共调试/面板与整个家族门禁仍开。可用模拟器是 x64，现有 C 包为 ARM64，不能把架构不匹配当目标通过。 |
| Dart | `qfli_dart/.trellis/tasks/10-22-offline-ide-completeness/research/portable-production-baseline.json`：`tom_d4rt 1.229.0+qfli.1; product offline policy and supervisor`，checked 240、failures 0；报告明确是 host portable engine。 | 安装后的 OHOS 原始全集门禁；其后才能晋升 +180 草稿对（121–300）并执行扩充后的目标验证。不能沿用旧“43/120”表示当前 host 状态。 |
| Go | `qfli_go/.trellis/tasks/10-22-go-curriculum-ohos/research/catalog-official-import-baseline.json`：364/364；同目录 `catalog-native-import-baseline.json`：357/364、7 fail。两者 `deviceExecution:false`。 | 剩余 7 个 native/runtime/import 情况、native 重建、包内 FFI/目标全集验证，以及计划 +160 扩充。两份报告 inventory SHA 不同（official `e23e008b…`，native `acb733b6…`），须在同一最终输入上重跑，不能直接宣称后端对等。 |
| Java | `qfli_java/.trellis/tasks/10-22-offline-ide-completeness/research/java-final-handoff.md`：280 对主题（+180）、1,120 镜像断言；host 280/280；真实 OHOS x64 280/280、1,120 assertions；dirty-buffer 诊断及 16 个真实 JDI 生命周期检查；235/235 app tests。handoff 记录提交/推送。 | 物理 ARM64；公共 core/UI 消费及整个家族门禁仍独立。保留 Windows 包名等已知限制，不能把 x64 等同 ARM64。 |
| Lua/Script | `qfli_lua/.trellis/tasks/10-22-offline-ide-completeness/research/requirements-evidence.md`（记录 latest local verification 为 2026-10-23）：240 Lua 对、480 exact host executions，41 个教学修复；完整 1,282 个位置首次 host 执行均匹配终端行/状态，482 匹配 exact bytes。debugger 首轮 13/13、真实 shared adapter 23/23、runtime lifecycle 22/22；真实四语言 EditorPage 诊断已检查。 | 总 host 门禁仍因 3 个混合 Windows 分隔符的 probe 路径比较失败；须修 harness 后重跑。当前安装包的全量课程、工具、dirty-buffer、调试与窄屏验证仍开；shared adapter 包探针、公共编辑器 UI 与 shell 后代清理归既有 owner；本会话尚无产品 commit/push 完成证据。 |
| Python 内容 | 最新直接报告为 `qfli_python/.trellis/tasks/10-22-python-content-ohos/research/python-content-originals-host.json`：2026-10-23 00:49–00:52 +08:00，原始 120 主题/186 答案及所有 aggregate/legacy 表示共 planned/completed/passed 1,158，failed 0，embedded-host，`deviceGatePassed:false`。同目录 `generation-originals-preservation.json`：1,158 representations、assetMismatches 空，非 Python tutorial/example 各 1,700 记录保留。 | 当前 OHOS 原始 main/answer/fixture 全集，以及普通 import/run；通过后才开始 +180 主题。旧 `qfli_python/.trellis/tasks/10-22-offline-language-apps/research/python-content-audit.json` 中 116/120 example、115/120 tutorial、176/186 answer compile 是历史失败基线，不能再当当前未修复计数。 |
| Python 模块 | `qfli_python/.trellis/tasks/10-22-python-offline-modules/research/ohos-audit-build-ready.json`：x64 HAP build exit 0、签名/资源/native strip-binding 就绪的现有报告；十个内置模块为 base64、bisect、contextlib、copy、csv、functools、itertools、statistics、string、textwrap。SQL/Lua 协调记录报告 foundation `a1a953bd` 已提交/推送。 | 已安装应用中的 module/package/import、完整原始课程、工具及真实调试器验收；包构建就绪不是 device execution。专职 Python 内容/模块/工具/debugger owner 仍活跃，不重复实现模块管理，也不引入在线 pip。 |
| Rust | `qfli_rust/build/offline-ide-audit/host-baseline.json`：正常 host rustc 166 对、332/332 程序；`qfli_rust/build/offline-ide-audit/native-host-catalog.json`：HOST embedded-Miri source preflight，332 attempted、316 passed，executionComplete true、status failed，OHOS acceptance not established。 | 16 个嵌入运行时失败；当前包 OHOS baseline；其后 +180 主题。provider/tools/native owner 已存在，旧 ledger 缺新实现进度不代表无主。 |
| SQL | `qfli_sql/.trellis/tasks/10-22-offline-ide-completeness/research/requirements-evidence.md`：生产 126 主题、372 scripts（SQLite 120/360，MySQL 6/12）；host SQLite 通过。最新隔离 checkpoint 为 272 PASS/2 Oracle desktop SKIP、analysis 0 issues；+180 草稿/540 scripts host pass，尚未晋升。`research/publication-20261023.md`：5 个 reviewed commits 已正常推送 5 个镜像，均为 `3dfb07362015ea378a9526efc64e0423eff7714f`。 | 当前 OHOS 全 372（含 6 个 MySQL 情况）、安装信任及生产签名、真实编辑器/UI/工作区。其后才晋升为 306 主题/912 scripts 并验收。SDK public test identity 签名通过不能称为生产签名。 |
| Note | `qfli_note/.trellis/tasks/10-22-offline-note-completeness/research/final-handoff.md`：264 tests；220 个新例子、4 tutorials/22 lessons；直接离线工具/诊断；双 ABI unsigned HAP；本地 commit `a7509155e6c68d5a7e372506536a4dc2888858df`，无 remote。 | 三个匹配签名文件缺失；实际安装后的 renderer、native URI open/save/persistence 与物理 ARM64。内容是在 host baseline 后创作，OHOS baseline-first 要求仍未闭合；不能把 fenced language 展示/高亮称为执行。 |
| Web | `qfli_web/.trellis/tasks/10-22-standalone-offline-ide/research/browser-481-final-desktop.json` / `browser-481-final-mobile.json` 及同名 `.md`：host 各 481/481，4,016/4,015 assertions。`research/ohos-481-final.md` / `.json`：真实 OHOS ArkWeb 全量 474/481、7 fail、4,012 assertions，started 2026-10-22T16:17:14.274Z，catalog SHA/bytes verified。另 `research/ohos-runtime.json` / `web-ohos-runtime-acceptance.md`：实际 QuickJS/Nginx 服务生命周期 15/15。 | 7 个剩余 ArkWeb 全量失败及修复后的完整目标重跑；最终 ordinary artifact/source 一致性、UI/工作区/诊断手势。15 个 native service 情况不能证明 481 课程通过，host Chromium 通过也不能替代 ArkWeb。 |
| JSON | `.trellis/tasks/10-22-offline-json-ide/research/host-20261023-serial-tests.log`：116/116；`host-20261023-analyze.log`：No issues。`ohos-harness-final-result.json`：实际 OHOS，340 examples/runnerPasses/tutorials/lessons、440 answers、340 fixtures、10 semantic operations、16 tools、0 failures。`ohos-ui-acceptance.json` 记录 10-22/10-23 普通 UI 的直接卡片、Pointer、主编辑器高亮/波浪线/Problems 定位、未保存修复不写盘、结构定位、树重开/进程重启恢复。 | 仅 unsigned x64 emulator；无 release signing/物理 ARM64。多根恢复有 host 回归，未做目标手势；普通 UI 仅覆盖所记录路径。设备结果绑定归档 source snapshot，不能自动扩展到之后的共享 core 改动。JSON 最终任务文档/提交归现有 JSON owner，不能据此关闭兄弟产品。 |

**需要纠正的过时 ledger 项。** 以下只记录修正依据，不在本次改动兄弟 ledger：

| 过时说法或混用 | 本次采用的依据与修正 |
| --- | --- |
| Dart “43/120”或仍只有失败的 production baseline | 新 `portable-production-baseline.json` 为 240 checked / 0 failures；仍是 host-only。 |
| Go “300/364” | 最新 official 364/364、native 357/364；保留不同输入 hash 与 7 个失败，不把 host 报告写成设备通过。 |
| Lua 尚未执行完整 1,282 host 位置 | 最新全部 1,282 已执行，行/状态匹配；总门禁因 3 个路径 probe 失败，不能误写完全通过。 |
| Python 仍有原始 117–120 main/十个 answer 未修复 | 旧审计仅保留为失败历史；最新 1,158/1,158 shipped representations embedded-host pass，OHOS 门禁仍为 false。 |
| Rust 只有“无实现/待实现”，或普通 rustc 332/332 等同嵌入引擎 | 新 Miri preflight 为 316/332、16 fail；设备未建立。 |
| SQL denominator 378 | 实际生产为 372，旧 378 已由产品明确纠正；草稿 540 不加入生产门禁分母。 |
| SQL 当前 full suite 273/2，或尚未提交推送 | 273/2 是历史 dirty-tree；最终隔离 272/2，5 reviewed commits 推送 5 镜像已记录；OHOS/生产签名仍开。 |
| Web 只有 443/481、38 fail，或只看 34-case subset | 新完整 ArkWeb 报告为 474/481、7 fail；仍未全过。另有 15/15 service suite，须单列。 |
| JSON “unknown owner/no handoff”，或普通 UI 尚未有修复/树恢复证据 | 现有 JSON task/session 及 C `research/json-owner-audit-20261022.md` 已证明实现存在；本地 `ohos-ui-acceptance.json` 又增加 10-23 明确交互。应交付 durable handoff，而不是重新接管开发。 |
| core debugger contract 已发布，所以共享 Debug/Console/Ports 已完成 | C `research/acceptance.md` 与 Lua 当前要求记录仍将公共 UI、supervisor descendant cleanup 等列为 C-owned follow-up。 |
| 历史队列即当前设备窗口；打包/签名/host pass 即手机通过 | 只引用原报告明确的平台、ABI、bundle/source snapshot 与设备执行范围；本次不授予设备窗口，也不关闭未跑门禁。 |

**JSON 证据与 source snapshot 的交接。** C 的 `qfli_c/.trellis/tasks/10-22-offline-standalone-ide/research/json-owner-audit-20261022.md` 已记录 340 例子/教程、+240 实质新增、440 answers、340 fixtures、16 direct tools、真实 `JsonCodeAnalyzer` 与 bounded/killable 工具 worker。该审查当时发现只有 `core/lib/services/process_supervisor.dart`、`core/lib/services/studio_profile.dart` 与设备快照不同；这是当时观察，不是本次重新 hash 的结果。JSON 自有 `ohos-final-source-snapshot.json`、`ohos-normal-source-snapshot.json` 和 artifact 元数据保留归档来源。Pointer 为 RFC 6901，不称 JSONPath；Schema 为明确的本地 2020-12 子集，不称完整 Schema 实现；数据变换通过不推导可执行语言调试器或 C/Python runtime 能力。

**可继续承担的工作。** JSON 可以在自己的任务范围维护该家族证据索引、交付 durable JSON handoff，或进行不触碰设备/进程的只读 package/source/hash/offline-permission/extension coverage 核对，再把发现交给现有 owner。运行时修复、内容扩充、共享 debugger/panel、共享 core 与设备验收均已有归属；需要接手时应先取得明确所有权移交，不能从旧清单推断无人维护。家族仍在推进，本报告不宣称家族完成。
