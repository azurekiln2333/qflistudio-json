# 原生就绪门最终只读复核

对象：`.trellis/.runtime/prepare_json_ohos_inputs.py`（29175 B，`890f10ac`）与 `.trellis/.runtime/test_json_native_readiness.py`（5945 B，`f78d1e24`）。
依据：`.trellis/spec/json-offline.md` 第 3、7 节。

## 结论

**无阻塞问题。** 就绪门在首次构建之前运行，并拒绝锁文件字节改动与工具哈希改动。

## 已复核通过

1. 就绪门先于构建。`run_json_ohos_release.ps1:86` 先跑 `capture-before`，`:93` 才跑构建。`Invoke-JsonNativePhase` 在非零退出时抛错，构建因此不运行。
2. 原始输入按字节绑定。`signature()`（`:60-69`）对原始字节取 SHA-256。`readiness_mismatches`（`:450-455`）对 `files` 与 `cacheReferences` 做整表判等，不规范化。
3. 5 条 703 漂移路径全部在 `files` 内。`BuildProfile.ets`、4 份锁文件、1 条缓存引用均已绑定（`build/ohos-initialized-preparation-20261026.json`）。
4. 独立复算一致。以 `guarded.json` 为实际值，就绪清单复算得 `[]`。源码变体得 `['files']`。工具变体得 `['tools']`。
5. 负向对照齐备。`readiness-source-changed` 与 `readiness-tool-changed` 均为 `changed: true`。
6. 16 项测试全过。`Ran 16 tests ... OK`，退出 0。

## 发现（按严重度）

### 中

无。

### 低

- **L1 新增运行器条目不参与就绪比对。** `:456-466` 只遍历 `expected["runners"]`。`run_json_ohos_release.ps1:83` 每次另加 2 条 `*-config` 运行器，就绪清单只有 7 条。两处抵消了影响：命令内容经 `:467-477` 的 `nativeCommands` 判等仍受绑，脚本自身哈希也受绑。故仅为口径不完整。
- **L2 排除策略文本与绑定集合不一致。** `:549` 的 `exclusionPolicy` 仍列 `BuildProfile.ets`。`input_set`（`:148`）对该根只传 `cache=True`，`generated()`（`:97-105`）不生效，该文件实际进入 `files`。绑定更严，但策略串误导读者。
- **L3 `credentialPathsExcluded` 未比对。** 该键不在 `:450-453` 的键表内。新增凭据文件落入排除表而非 `files`，就绪门会放过。
- **L4 `metadataPresent` 与 `schemaVersion` 未比对。** 分别见 `:543`、`:533`。
- **L5 `prepared` 只校验清单侧。** `:448` 判 `expected["prepared"]`。`:533` 的采集侧 `prepared` 不参判。`--prepare-native` 与 `--expected-prepared` 互斥，故属设计选择，但测试名 `test_unprepared_snapshot_refuses_readiness` 会误导。
- **L6 测试覆盖缺口。** 未覆盖 `packageRoots`、`appRoot`、`coreRoot`、`hostManifestIdentity`、`hostAppOverlays`、`originalAppInputs`、`originalExecutableComparison`、`originalCacheReferences`、`exclusionPolicy`、`embeddedSigningConfigurationCopied`。也未覆盖 `:463` 的凭据运行器分支。`test:22` 依赖 `build/` 已存在。

### 信息

- **I1 绑定的是制备后的锁字节。** `write_json` 重排锁文件后再绑定。同一隔离根内可复现。构建期 ohpm 改写不在就绪门范围内。
- **I2 就绪门只证构建前状态。** 它不证构建不改字节。该项需一次真实构建才能验证。

## 未验证

未运行 SDK、Flutter、hdc、设备或构建。就绪门的“构建不改字节”结论仍待真实构建验证。
