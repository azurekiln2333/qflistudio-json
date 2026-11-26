# 703 原生探针补强 v2

范围：只改副本 `inspect_json_release_hap_candidate.py`。
未运行 SDK、Flutter、hdc 或设备。未改冻结文件。未 commit，未 push。
首轮报告 `native703-inspector-fix.md` 保留作历史。本轮取代其结论。

## 首轮行为更正

- 首轮不传清单时按隔离根允许 native 输入。
- 该判断只看目录位置。
- 该判断不构成冻结通过。
- 本轮取消该判断。
- native 输入出现时，必须传 `--prepared`。
- 清单核对通过，native 输入才记为冻结通过。

## 本轮收紧

- native 输入出现时强制要求 `--prepared`。
- 清单 `appRoot` 必须等于当前 app 隔离根。
- 清单 `coreRoot` 必须等于当前 core 隔离根。
- native 输入只接受清单声明的 `nativePlugins/` 文件。
- 声明必须带精确字节数与 SHA-256。
- 清单键含 `..`、空段或反斜杠时拒绝。
- OHOS 插件映射与 `package_config.json` 双向核对。
- live 路径与其他 build 路径仍拒绝。

## 判定顺序

1. 核对 app 与 core 是隔离根。
2. 推导隔离 `native_plugins` 根。
3. 核对清单 `appRoot` 与 `coreRoot`。
4. 核对 OHOS 插件映射。
5. 分类 depfile 输入。
6. native 输入核对声明、字节与 SHA-256。
7. live 路径一律拒绝。

## 与首轮差异

| 项 | 首轮 | 本轮 |
| --- | --- | --- |
| 无 `--prepared` | 只看目录 | 拒绝 |
| 清单根字段 | 不核对 | 必须相等 |
| native 文件 | 只看目录 | 清单声明加字节与 SHA-256 |
| OHOS 插件映射 | 不核对 | 双向核对 |

## 验证

全部命令只读。输出写入 `.trellis/.runtime/_native703_test/`。

| 用例 | 结果 |
| --- | --- |
| 无清单 703 | `BLOCKED` |
| 真清单 703 | `PASS` |
| 清单只含 3 项 native | `PASS` |
| 清单缺 LICENSE | `BLOCKED` |
| 清单 SHA 清零 | `BLOCKED` |
| 清单 `appRoot` 改 live | `BLOCKED` |
| 清单 `coreRoot` 改别名 | `BLOCKED` |
| 清单键含 `..` | `BLOCKED` |
| 清单 SHA 格式错 | `BLOCKED` |
| 注入 live 源码 | `BLOCKED` |
| 注入任意 build 路径 | `BLOCKED` |
| 注入未声明 native 路径 | `BLOCKED` |
| 注入外部工具链 | `PASS` |
| OHOS 路径不符 | `BLOCKED` |
| OHOS 缺 package 映射 | `BLOCKED` |
| package 多出 native 映射 | `BLOCKED` |
| native 根缺失时含 OHOS 插件 | `BLOCKED` |

关键错误文本。

| 用例 | 错误 |
| --- | --- |
| 无清单 | `Native plugin inputs need the prepared manifest: pass --prepared` |
| 缺声明 | `Native plugin input is absent from the prepared manifest` |
| 哈希不符 | `Native plugin input differs from the prepared manifest` |
| `appRoot` 不符 | `Prepared manifest appRoot differs from the inspected root` |
| `coreRoot` 不符 | `Prepared manifest coreRoot differs from the inspected root` |
| 键不安全 | `Prepared manifest has an unusable native plugin path` |
| OHOS 路径不符 | `OHOS plugin path differs from package_config.json` |

## 关键值

| 项 | 值 |
| --- | --- |
| HAP 字节 | 124516943 |
| HAP SHA-256 | `df170f250a1cecc84ba0abb73f42ddfbc5f6362a6980a64c29962bc52ad02a88` |
| kernel SHA-256 | `b77ef1778689b76995d9cbbafd12e81adf1950c937fc8effa92d2e82a44954b5` |
| `package_config.json` SHA-256 | `0ae3acb25e587272183c2700c8646cc567ab4158824f978e4392ed9b2e4a5324` |
| `.flutter-plugins-dependencies` SHA-256 | `b8b12dbc2aa8249be8e1913954c5964b928de50cc34ba6886bd07ec4da8d845c` |
| 清单声明 native 文件数 | 52 |
| depfile 观测 native 文件数 | 3 |
| OHOS 插件数 | 1 |
| OHOS 插件名 | `path_provider_ohos` |

## 边界

- 探针只核对它观测到的 native 输入。
- 清单可以只声明 depfile 引用的文件。
- 清单完整性不在探针范围。
- 探针不证明设备安装。
- 探针不证明 HAP 来源真实。
- runner 必须传 `--prepared`，否则本轮一律拒绝。
- 副本未替换 live 探针。

## 文件

| 文件 | 字节 | SHA-256 |
| --- | --- | --- |
| `inspect_json_release_hap.py`（未改） | 14684 | `9417170308902ab48c1669a6178ba66ff80b0e74ca1e5924f763a33592705b98` |
| `inspect_json_release_hap_candidate.py` | 23296 | `fc3ac0da4693a3e7140fc531423cfa0ad26e720fa3391c79fb82dd86dc2425c0` |