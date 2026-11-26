# 703 路径分类审查：隔离 native_plugins 的 LICENSE 被拒

范围：`.trellis/.runtime/inspect_json_release_hap.py`、`.trellis/.runtime/prepare_json_ohos_inputs.py`。
方法：静态阅读加只读取证。用真实 depfile 复算判定。未运行 SDK、Flutter、hdc，未改脚本，未 commit。

结论：拒绝逻辑按「是否在仓库内」划界，而不是按「是否在隔离根内」。隔离插件因此被当成原始源码拒绝。另有两处同等严重的方向性错误。

---

## 1. 实测现场

隔离快照布局（`build/o6e60792d`）：

```
build/o6e60792d/                 <- isolated root  (app.parent)
  qfli_json/                     <- app
  qfli_studio_core/              <- core
  native_plugins/                <- 插件，app 的兄弟目录
    path_provider_ohos/
      LICENSE
      lib/path_provider_ohos.dart
      lib/messages.g.dart
```

`prepare_json_ohos_inputs.py` 三处认定这个布局是合法的：

- 第 147 行：`inventory(app.parent / "native_plugins", "nativePlugins", ...)`，把插件计入冻结输入。
- 第 349 行：`clones[source] = destination / "native_plugins" / plugin["name"]`。
- 第 221 至 222 行：`if not under(packages["path_provider_ohos"], app.parent / "native_plugins")` 才拒绝。

所以 `native_plugins` 属于隔离集。`inspect_json_release_hap.py` 不认这一点。

拒绝点在 `inspect_json_release_hap.py:179`：

```python
if not inside(dependency, app) and not inside(dependency, core):
    if inside(dependency, LIVE_APP) or inside(dependency, LIVE_CORE):
        raise BlockedInspection(f"Depfile references original/live project source: {dependency}")
```

代入本机真实路径：

| 表达式 | 值 |
| --- | --- |
| `LIVE_APP` | `D:\MyNewProjects\qfli_json` |
| `inside(pluginRoot, app)` | `False` |
| `inside(pluginRoot, core)` | `False` |
| `inside(pluginRoot, LIVE_APP)` | `True` |

三个条件同时成立，于是抛 `BlockedInspection`。

用两份真实 depfile 复算：

| depfile | 输入总数 | 在 app | 在 core | 两者之外 | 会被拒 |
| --- | --- | --- | --- | --- | --- |
| `flutter_build.d` | 1587 | 17 | 201 | 1369 | 3 |
| `kernel_snapshot_program.d` | 1503 | 12 | 186 | 1305 | 2 |

被拒的全部是隔离插件，无例外：

```
<iso>/native_plugins/path_provider_ohos/LICENSE
<iso>/native_plugins/path_provider_ohos/lib/path_provider_ohos.dart
<iso>/native_plugins/path_provider_ohos/lib/messages.g.dart
```

`LICENSE` 命中的原因：Flutter 聚合 depfile 收录所有包的 LICENSE 以生成 NOTICES。它不是 Dart 源，所以不走第 183 行的 `.dart` 分支，只被第 180 行误判。

---

## 2. 三处缺陷

### 2.1 假阳性：隔离插件被当成原始源码

第 180 行用 `LIVE_APP` 划界。因为隔离根建在仓库的 `build/` 下，隔离集是 `LIVE_APP` 的子集。这条规则无法区分「仓库里的隔离副本」与「仓库里的原始源码」。

### 2.2 假阴性：1369 条外部输入静默通过

第 179 行只处理「不在 app 也不在 core」且「在 LIVE_APP」。落在两者之外的输入既不拒绝也不记录。

实测 1587 条输入里有 1369 条属于此类：Pub 缓存、Flutter SDK、`D:\ProgramFiles\...`。任意一个 `D:\other\build\...` 同样静默通过。

结果是：该拒的放行，该放的拒绝。

### 2.3 位置依赖：冻结副本的守卫失效

第 17 行：

```python
LIVE_APP = Path(__file__).resolve().parents[2]
```

守卫强度取决于脚本自身位置。实测两份副本：

| 副本 | `LIVE_APP` | `LIVE_CORE` 存在 |
| --- | --- | --- |
| `.trellis/.runtime/` | `D:\MyNewProjects\qfli_json` | 是 |
| `research/native-window-20261026/runners/` | `...\10-22-offline-json-ide\research` | 否 |

运行冻结副本时，`inside(dependency, LIVE_APP)` 对任何真实源码都为假。第 180 行的拒绝完全失效，原始源码会静默通过。

这一条与 2.1 同时存在：同一份代码，在 A 位置误拒，在 B 位置完全失守。

---

## 3. 精确条件

把「是否在仓库内」换成「是否在隔离根内」，并把分类做全。

### 3.1 先定隔离根

```python
ISOLATED = app.parent                                   # build/<id>
PLUGIN_ROOT = ISOLATED / "native_plugins"
```

新增两条前置断言，与 `prepare` 侧对齐：

- **A1** `inside(ISOLATED, ROOT / "build")` 成立。
- **A2** `ISOLATED.name` 匹配 `^o[0-9a-f]{8}$`。

不满足即 `BlockedInspection`。这两条把布局钉住，后续判定才有意义。

### 3.2 每个输入必须归入唯一一类

对每个 depfile 输入同时取**词法路径** `p` 与**解析路径** `r = p.resolve()`。

| 类 | 条件 | 动作 |
| --- | --- | --- |
| `app` | `inside(r, app)` | 放行，计入 `app` 源 |
| `core` | `inside(r, core)` | 放行，计入 `core` 源 |
| `plugin` | `inside(r, PLUGIN_ROOT)` 且名字段合法 | 放行，计入 `plugin` 输入 |
| `toolchain` | `inside(r, 白名单根之一)` | 放行，计入 `toolchain` 输入 |
| `foreign` | 其余 | 拒绝 |

`plugin` 类另加两条：

- **P1** `r.relative_to(PLUGIN_ROOT).parts[0]` 匹配 `^[A-Za-z0-9_]+$`。
- **P2** 该名字属于 `<app>/.flutter-plugins-dependencies` 的 `plugins.ohos[].path` 重映射后集合。

`prepare` 第 348 行已用同一正则校验插件名，两边保持一致。

### 3.3 拒绝条件（按顺序判，先命中先拒）

- **R1** `foreign` → 拒绝，错误里带首个路径分量。
- **R2** `inside(r, LIVE_APP) and not inside(r, ISOLATED)` → 拒绝。**这一条修掉 2.1**：插件在 `ISOLATED` 内，放行。原始 `lib/`、`ohos/`、仓库根 `native_plugins/` 在 `ISOLATED` 外，拒绝。
- **R3** `inside(r, LIVE_CORE) and not inside(r, core)` → 拒绝。
- **R4** 路径含 `build` 分量且该 `build` 目录不等于 `ISOLATED` → 拒绝。用于挡住 `<ROOT>/build/<其他id>/...`。
- **R5** 词法路径在 `PLUGIN_ROOT` 内但 `r` 在外 → 拒绝。这是 junction 逃逸。

`LIVE_APP` 不再从 `__file__` 推导。改成显式传入：

- **R6** 新增 `--live-app` 与 `--live-core` 参数，缺省即 `BlockedInspection`。

**这一条修掉 2.3**：冻结副本与运行副本行为一致。

### 3.4 junction 是实存风险，不是假设

实测存在一个 junction：

```
<iso>/native_plugins/path_provider_ohos/ohos/oh_modules/@ohos/flutter_ohos
  -> <iso>/qfli_json/ohos/oh_modules/.ohpm/.../oh_modules/@ohos/flutter_ohos
```

本次它指向隔离 app 内部，`resolve()` 后落在 `app`，无害。
但 `prepare` 的 `copy_tree(..., native=True)` 会把任何 linked 目录重建成 junction（第 294 行）。目标来自 `mapped(...)`，不保证落在隔离集内。

所以 R5 必须显式判定，不能指望 `resolve()` 天然安全。

### 3.5 非 `.dart` 输入也要分类

第 183 行只对 `.dart` 做归属校验。`LICENSE`、`.frag`、`.g.dart` 之外的附件全部绕过。

`LICENSE` 这次只被第 180 行顺带命中，恰好暴露了问题。按 3.2 分类后，非 `.dart` 输入也必须有类，也要记录。

### 3.6 结果要留痕

`sourceDependencies` 增加：

```json
"inputClasses": {"app": 17, "core": 201, "plugin": 3, "toolchain": 1366, "foreign": 0}
```

并要求 `foreign == 0` 才 PASS。当前结果只报 `sourceCounts`（只含 `.dart`），外部输入完全不可见。

---

## 4. 判定表

| 输入 | 当前 | 应为 |
| --- | --- | --- |
| `<iso>/qfli_json/lib/main.dart` | 放行 | `app`，放行 |
| `<iso>/qfli_studio_core/lib/...` | 放行 | `core`，放行 |
| `<iso>/native_plugins/path_provider_ohos/LICENSE` | **拒绝** | `plugin`，放行 |
| `<iso>/native_plugins/path_provider_ohos/lib/*.dart` | **拒绝** | `plugin`，放行 |
| `D:\AppData\Local\Pub\Cache\...\LICENSE` | 静默忽略 | `toolchain`，放行并计数 |
| `D:\ProgramFiles\flutter_ohos\...\widgets.dart` | 静默忽略 | `toolchain`，放行并计数 |
| `<ROOT>/lib/main.dart` | 拒绝 | `foreign`，拒绝 |
| `<ROOT>/ohos/build-profile.json5` | 拒绝 | 拒绝（R2） |
| `<ROOT>/native_plugins/...`（原始插件） | 拒绝 | 拒绝（R2，在 `ISOLATED` 外） |
| `<ROOT>/build/<其他id>/native_plugins/...` | 拒绝 | 拒绝（R4） |
| `<iso>/native_plugins/../../lib/x.dart` | 取决于 resolve 结果 | 拒绝（解析后越界） |
| 经 junction 指向 `ISOLATED` 外 | 取决于 resolve 结果 | 拒绝（R5） |

「原始/任意 build 路径」的边界就落在 `ISOLATED`：`ISOLATED` 内的 `native_plugins` 放行，`ISOLATED` 外的任何 `build/` 段拒绝。

---

## 5. 与 prepare 侧的一致性

| 项 | prepare | inspect（现状） | inspect（提案） |
| --- | --- | --- | --- |
| 隔离根 | `destination`，必须在 `ROOT/build` 下（第 342 行） | 不校验 | A1、A2 |
| 插件根 | `destination/native_plugins`（第 349 行） | 不知道 | `PLUGIN_ROOT` |
| 插件名 | `^[A-Za-z0-9_]+$`（第 348 行） | 不校验 | P1 |
| 插件归属 | `under(..., app.parent/native_plugins)`（第 222 行） | 不认 | P2 |
| 原始根 | 显式 `mappings` 区分 `old_app` 与 `app` | `__file__` 推导 | `--live-app` 显式 |

`prepare` 已经区分「原始根」与「隔离根」。`inspect` 缺少这一层，是本缺陷的结构性原因。

---

## 6. 未验证

- 未运行 inspector，未产出真实 HAP 证据。全部数字来自对现存 depfile 的只读复算。
- 未覆盖 harness 模式。两个模式的 depfile 可能不同，`plugin` 输入数可能变化。
- 未校验 `nativeCache` 目录（`app/ohos/oh_modules` 等）是否也出现在 depfile 里。它们位于 `app` 内，按 R1 归 `app` 类，但语义上属于缓存引用。
- `toolchain` 白名单的具体取值未定。需要确认 Pub 缓存与 Flutter SDK 的稳定根，以及是否允许 `D:\ProgramFiles\` 整体。
