# 初始化基线策略只读校验

1. 字节绑定未放宽。`exclusionPolicy` 仍为 7 条。比对仍按原始哈希判等，无规范化。
2. 绑定面反而收紧。`files` 由 804 升到 805。`cacheReferences` 由 6 升到 7。
3. 703 的 6 项差异路径已全部进入绑定集。未排除 4 份锁文件。
4. 负向对照只覆盖键新增。`tools` 加第 14 项即判 `added`。
5. 该对照未覆盖哈希改动。`differences.tools.changed` 为空表。值改动尚无对照。
6. 基线内容等同 703 失败运行的 after 状态。`files` 与 `cacheReferences` 逐键相等。
7. 基线因此继承 703 的生成物。重跑同样的失败构建仍可过源码比对。
8. 基线无法由 `preparedOrigin` 复现。该清单记的是 804/6 的干净集。
9. 两次采集相隔 3 秒，期间未运行构建。相等只证采集稳定。
10. 该相等不证构建不改字节。703 的漂移正来自构建期改写锁文件。
11. 清单未声称验收。`initializationGatePassed` 为 false。`snapshotState` 标注失败 703 不是验收。
12. HAP 已移动。旧路径不存在。新路径哈希 `df170f25` 与清单记录一致。
13. `embeddedSigningConfigurationCopied` 为 true。绑定集内无签名材料路径。该旁路未进比对。

**结论：不是字节放宽，是基线溯源放宽。**

14. 建议补负向对照：改动某个 tool 的 `sha256`，必须判 `changed`。
15. 建议给基线加溯源断言：由 `preparedOrigin` 重放，须复现 804/6 或显式记差异来源。
