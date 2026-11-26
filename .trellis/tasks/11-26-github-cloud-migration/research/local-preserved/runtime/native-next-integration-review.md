# 探针集成窄审查（只读）

结论：集成未破坏加固条件。差异三处，均为收紧或等价替换。

- `LIVE_APP` 改为祖先 repo 标志发现。实测解到 `D:\MyNewProjects\qfli_json`，与 candidate 的 `parents[2]` 相同。`LIVE_CORE` 与 `build/` 固定点不变。
- 新增 `lexical_inside` 与 `inputPaths`：拼写路径在隔离根内、解析后出根时拒绝。相对 candidate 属加强。
- runner 改传 `--prepared source-before.json`。该文件 `appRoot`/`coreRoot` 等于隔离根，52 项 native 声明字节与 SHA-256 全对。

对集成版实跑 13 项。
R1 真清单 PASS（native 3，OHOS 1）。R2 无清单拒绝。R3 live 源码拒绝。R4 任意 build 拒绝。
R5 未声明 native 拒绝。R6 外部工具链放行。R7 词法逃逸拒绝。R8/R9 清单根不符拒绝。
R10 缺声明拒绝。R11 哈希不符拒绝。R12 键含 `..` 拒绝。R13 OHOS 映射不符拒绝。

残余一项：冻结副本在 repo 外时，`next()` 在导入抛 `StopIteration`，属崩溃失败，不写结果。
副本置入 staging 时 `LIVE_APP` 等于隔离 app，实测触发 `BlockedInspection`，不放行。

未改 candidate 与冻结文件。未运行 SDK、Flutter、hdc。未 commit。
