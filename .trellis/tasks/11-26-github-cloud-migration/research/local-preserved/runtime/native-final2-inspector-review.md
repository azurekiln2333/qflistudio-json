# native inspector 最终只读审查

## 受检文件

| 文件 | 字节 | 行数 | SHA-256 |
| --- | --- | --- | --- |
| `.trellis/.runtime/inspect_json_release_hap.py` | 25745 | 484 | `7be9dc50d9e5841939750a097fb9351c33fc4c21ee4f32477a4021d7a1119772` |
| `.trellis/.runtime/test_json_native_source_attribution.py` | 9229 | — | `02945e00f099463b4b36376c36031ea7c6396bc854a0d04f7907fff6db586a5d` |

对照规范：`.trellis/spec/json-offline.md` 第 7 节（离线设备证据与宿主窗口边界）。

## 结论

**无阻断问题。** Dart 侧归因链完整，HAP 证据校验与规范第 7 节一致。以下 6 项是证据边界与健壮性缺口，不阻断运行。

## 发现

### F1 插件文件集未绑定（中）

`inspect_json_release_hap.py:199` 的 `native_declarations` 产出 `declared`。该字典只有两处用途：`:331` 按 depfile 输入查表，`:376` 记 `nativeFileCount`。

没有任何一处把 `declared` 与磁盘插件树双向比对。

后果：`native_plugins/**/ohos/**` 下的 C++ 与 `.so` 由 Hvigor 编译，不进 Dart depfile，永远不参与比对。`preparedManifestVerified` 实际含义是「全部 Dart 插件输入已比对」，不是「插件树已比对」。

建议：把插件树文件集与 `declared` 的 `nativePlugins/` 键集双向比对。

### F2 跨根迁移绕过守卫（中）

`:323` 定义 `isolated_roots = (app, core, native)`。`:324` 仅在「拼写落在某个隔离根内」且「解析落在全部隔离根之外」时拒绝。

拼写落在 `native` 内、解析落在 `app` 内时，`any(inside(dependency, root))` 因 `app` 命中为真，守卫不触发。随后 `:326` 的 `not inside(dependency, app)` 为假，插件分支被跳过。该输入既不绑定 `declared`，也不拒绝。

实测存在同类 junction：`build/o6e60792d/native_plugins/path_provider_ohos/ohos/oh_modules/@ohos/flutter_ohos` 指向 `<iso>/qfli_json/ohos/oh_modules/`。

建议：判「拼写根」与「解析根」是否同一个隔离根，不同即拒绝。

### F3 PASS 可携带未校验标记（低）

`:370` 写 `"preparedManifestVerified": bool(recorded) and prepared is not None`。

当隔离插件根存在、而 `.flutter-plugins-dependencies` 的 `plugins.ohos` 为空列表时，`:356` 的循环空转，`native_inputs` 保持为空。记录为 `inputCount: 0`、`preparedManifestVerified: false`，函数仍返回 `status: "PASS"`。

只读 `status` 与 `passed` 的消费方会当成通过。

建议：`native is not None` 时要求 `recorded` 非空。

### F4 异常基类与规范不符（低）

`:32` 声明 `class BlockedInspection(Exception)`。

规范第 7 节要求「Malformed/encrypted archive input must raise a ValueError subclass at the offline helper API and fail its CLI」。`inspect()` 直接抛出 `zipfile.BadZipFile` 与加密条目的 `RuntimeError`，二者都不是 `ValueError` 子类。

CLI 要求已满足：`:474` 捕获 `Exception`，退出码 1。API 层不满足：按 `ValueError` 捕获的调用方接不住。

该条位于设备证据小节，是否适用于本 helper 可再判。

### F5 `zip` 截断隐患（低）

`:322` 用 `zip(depfile["inputs"], depfile["inputPaths"])`。真实解析在 `:155` 至 `:159` 保证两表等长，但代码未断言。

若将来某生产者返回不等长，尾部输入会被静默丢弃，守卫与分类同时失效。

建议：加一条长度断言。

### F6 `LIVE_APP` 推导无兜底（低）

`:21` 用 `next(...)` 且无默认值。若模块被放到任何祖先都不含 `lib/json/json_verification_page.dart` 的位置，导入即抛 `StopIteration`，早于 `main` 的异常处理。

当前冻结副本仍能上溯到仓库根，不受影响。行为 fail-closed，但异常形态不友好。

建议：改为 `next(..., None)` 并在缺失时抛 `BlockedInspection`。

## 已校验正确

- `parse_depfile` 保留原始拼写：`:155` 走 `resolve=False`，`:159` 另存 `inputPaths`。相对路径、未知转义、带引号 token 一律拒绝。
- 词法守卫覆盖三个隔离根，能挡住逃到隔离集之外。
- `:281` 在插件根存在时强制要求 `--prepared`。
- `native_declarations` 把 `appRoot`、`coreRoot` 绑定到受检根，并校验路径形状、字节数、SHA-256 格式。
- `ohos_plugin_mappings` 对插件根做 `.flutter-plugins-dependencies` 与 `package_config.json` 双向对齐。
- 逐输入比对 `bytes` 与 `sha256`。
- `:356` 起要求每个插件至少有一个 `.dart` 编译输入，且必须同时出现在聚合 depfile。这堵住了「插件存在但零输入」的旧洞。
- HAP 侧：重复条目、module 身份、仅剪贴板权限、x64 引擎、单一 kernel 位于标准路径、条目哈希。
- HAP 侧另三项：内容与隔离源逐字节相等、检后重算哈希、`xb` 独占复制。

## 测试覆盖

当前测试文件含 19 个 `test_` 方法。覆盖范围：prepared 缺失与根不符、未声明输入、哈希与字节数变更、原始 app/core、其他 staging、编译源未进聚合。
另有：package_config 与插件元数据不一致、拼写保留、链接逃逸、插件必须进入编译器证据、缺编译器 depfile。

三处缺口与上述发现对应：

- 无 F2 的 native→app 迁移用例。
- 无 F3 的空插件列表用例。
- 无「磁盘插件文件不在 `declared` 中」的用例（F1）。

另 `test_depfile_keeps_spelled_input_paths` 用 `p.absolute()` 作期望值，不做归一化，抓不到引入 `..` 归一化的回归。

## 计数说明

本次只读未运行测试。先前「17 项全通过」对应旧修订。当前文件为 19 项，SHA-256 已变。若以 19 项为准，建议重跑一次确认。
