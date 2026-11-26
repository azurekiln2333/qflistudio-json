# 703 原生探针 nativePlugins 误拒修复

范围：只读复核与副本补丁。未运行 SDK、Flutter、hdc 或设备。
未改冻结文件。未 commit，未 push。

## 现象

- 703 先编译 harness HAP，再运行原生探针。
- HAP 编译成功，退出码 0。
- 探针输出 `BLOCKED`，退出码 1。
- 错误原文见 `harness-artifact.json`。

```
BlockedInspection: Depfile references original/live project source:
D:\MyNewProjects\qfli_json\build\o6e60792d\native_plugins\path_provider_ohos\LICENSE
```

## 根因

- HAP 聚合 depfile 与编译 depfile 合计 3090 个输入。
- 其中 5 个输入位于 `build/o6e60792d/native_plugins/`。
- 该目录是 `build/o6e60792d/` 下的隔离副本。
- 该目录同时位于 live 仓库 `D:\MyNewProjects\qfli_json` 下。
- 旧探针只允许隔离 app 与隔离 core 两个根。
- 旧探针对其余 live 路径一律判为原始源码。
- 旧探针因此误拒隔离 nativePlugins。
- 实测该隔离目录是普通目录，不是链接。

分类统计如下。

| 类别 | 输入数 |
| --- | --- |
| 隔离 app | 29 |
| 隔离 core | 387 |
| 隔离 nativePlugins | 5 |
| 外部工具链 | 2669 |
| 其他 live 路径 | 0 |

## 证据

- `prepared.json` 声明 52 个 `nativePlugins/` 文件。
- depfile 引用的 native 文件去重后为 3 个。
- 三者字节与 SHA-256 与声明逐一一致。

| 声明键 | 字节 | SHA-256 |
| --- | --- | --- |
| `nativePlugins/path_provider_ohos/LICENSE` | 1519 | `89519eca6f7b9529b35bdddd623a58c3af06a88c458dbd6531ddb4675acf75a9` |
| `nativePlugins/path_provider_ohos/lib/messages.g.dart` | 6593 | `b359e796d158f3a2ac3a7e1b3dc7edeb85449577ab732ed744756357352ca69b` |
| `nativePlugins/path_provider_ohos/lib/path_provider_ohos.dart` | 3019 | `2bcc351cf5c09078f9da4f6300bd55bc1c9600a0d88dc6308210433ed0d062ea` |

## 修复

- 只改副本 `inspect_json_release_hap_candidate.py`。
- 副本从 `inspect_json_release_hap.py` 逐字复制。
- 新增函数 `isolated_native_root(app)`。
- 该函数从 app 根推导同级 `native_plugins` 根。
- 该函数要求父目录位于 live 仓库 `build/` 下。
- 该函数要求父目录名匹配安全标识。
- 该函数要求父目录与推导根都不是链接。
- 该函数要求推导根是真实目录。
- 任一条件不满足，该函数返回 `None`。
- 分类顺序为先允许推导根内输入，再拒绝其余 live 路径。
- 推导根内输入必须是文件。
- 旧探针仍拒绝其余 live 路径。
- 外部工具链路径保持原样。

## 冻结核对

- 新增可选参数 `--prepared`。
- 传入时逐一比对 native 输入的字节与 SHA-256。
- 比对对象取自清单的 `nativePlugins/` 表。
- 缺声明或哈希不符时抛出 `BlockedInspection`。
- 不传时只按隔离根允许。
- 结果新增 `isolatedNativePlugins` 字段。
- 该字段记录根、数量、文件与核对标志。

## 复现与验证

全部命令只读。输出写入 `.trellis/.runtime/_native703_test/`。

| 用例 | 结果 |
| --- | --- |
| 旧探针 703 | `BLOCKED`，复现原错误 |
| 副本 703 | `PASS` |
| 副本加 `--prepared` 703 | `PASS`，核对标志 true |
| 副本加篡改清单 | `BLOCKED`，哈希不符 |
| 注入 live 源码路径 | `BLOCKED` |
| 注入任意 build 路径 | `BLOCKED` |
| 注入外部工具链路径 | `PASS` |
| 推导函数 live app 根 | `None` |
| 推导函数缺 staging 目录 | `None` |

703 关键值。

| 项 | 值 |
| --- | --- |
| HAP 字节 | 124516943 |
| HAP SHA-256 | `df170f250a1cecc84ba0abb73f42ddfbc5f6362a6980a64c29962bc52ad02a88` |
| kernel SHA-256 | `b77ef1778689b76995d9cbbafd12e81adf1950c937fc8effa92d2e82a44954b5` |
| 隔离 nativePlugins 根 | `build/o6e60792d/native_plugins` |
| 允许的 native 输入数 | 3 |

## 边界

- 探针只证明 depfile 归因与文件身份。
- 探针不证明设备安装。
- 探针不证明 HAP 来源真实。
- `--prepared` 为选入项，runner 默认不传。
- 不传时允许范围是隔离根，不是清单文件集。
- 副本未替换 live 探针。
- 703 结果仍属隔离编译证据，不是设备通过证据。

## 文件

| 文件 | 字节 | SHA-256 |
| --- | --- | --- |
| `inspect_json_release_hap.py`（未改） | 14684 | `9417170308902ab48c1669a6178ba66ff80b0e74ca1e5924f763a33592705b98` |
| `inspect_json_release_hap_candidate.py` | 18302 | `55eeac5ce8d23b93cbaa3c36fa8b75f0616f3c9fc224272de4c786872561b2ba` |