# QFLIJson

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

QFLIJson 是离线 JSON 编辑器。产品在本机处理文档。

## 功能

- 编辑器提供 JSON 语法高亮。
- 编辑器用波浪线标记语法错误。
- 问题面板显示错误的行号与列号。
- 结构视图显示 JSON Pointer 路径。
- 运行入口输出格式化的 JSON。
- 工作区容纳多个本地项目根目录。
- 命名工作区保存打开文件与光标位置。
- 文件树保留各根目录的展开状态。

产品内置 340 条示例与 340 条教程。新增内容各有 240 条。

新增内容分为 24 类。每类包含 10 条。
校验入口校验 440 条练习答案。
校验入口校验 340 个输入样本。
10 条示例包含补丁或合并结果。

工具页直接提供 16 张卡片。

| 工具 | 用途 |
| --- | --- |
| 格式化与校验 | 整理缩进。校验语法与重复键。 |
| JSON 压缩 | 删除字符串外的无意义空白。 |
| 递归键排序 | 排序对象键。保留数组顺序。 |
| JSON Pointer 查询 | 提取路径对应的值。 |
| 结构差异 | 生成 JSON Patch。 |
| Merge Patch | 合并对象。用 null 删除字段。 |
| JSON Patch | 应用 add、remove、replace、move、copy、test。 |
| 展开路径 | 生成保留容器类型的路径清单。 |
| 还原路径 | 从路径清单恢复文档。 |
| JSON Lines 转数组 | 将逐行 JSON 转换为数组。 |
| 数组转 JSON Lines | 将每个元素输出为一行 JSON。 |
| 字符串转义 | 将文本编码为 JSON 字符串。 |
| 字符串反转义 | 还原 JSON 字符串。 |
| 对象数组转 CSV | 将对象数组转换为表格文本。 |
| 本地 Schema 校验 | 校验类型、字段与约束。 |
| 结构统计 | 统计节点、类型、深度与字节数。 |

## 使用

1. 打开本地项目。
2. 打开 `.json` 文件。
3. 编辑 JSON。
4. 查看问题面板。
5. 点击问题条目定位错误。
6. 点击运行按钮。
7. 查看输出。

运行入口优先读取 `data.json`。其次读取 `src/data.json`。

使用独立工具时，请按以下步骤操作。

1. 打开工具页。
2. 选择工具卡片。
3. 输入 JSON。
4. 按需填写第二份输入。
5. 点击运行按钮。

终端提供以下只读命令。命令输出不会覆盖源文件。

```text
json check <file>
json format <file>
json minify <file>
json sort <file>
json stats <file>
json get <file> <JSON Pointer>
```

`json help` 列出终端命令。

| 输入 | 退出码 |
| --- | --- |
| 有效 JSON | 0 |
| 无效 JSON | 1 |
| 文件缺失或路径越界 | 127 |

项目配置可指定入口文件。
命名工作区保存项目标识与最后路径。

## 开发

本仓库是独立 Flutter 应用。它依赖兄弟仓库 `qflistudio-core`。

两个仓库必须位于同一父目录。

```text
checkout-parent/
  qflistudio-core/
  qflistudio-json/
```

`pubspec.yaml` 声明 Dart 约束 `^3.11.5`。
编辑器依赖指向 `../qflistudio-core/vendor/re_editor`。

仅在本机检出源码。
构建、测试与依赖安装全部在 GitHub 运行。
本机禁止构建、测试、分析和依赖安装。

```text
git clone https://github.com/azurekiln2333/qflistudio-core.git
git -C qflistudio-core checkout 476a30acee21dc486ee2849dd8064a7be665e4d5
git clone https://github.com/azurekiln2333/qflistudio-json.git
```

从 GitHub Actions 发起验证。
工作流说明见 [cloud-ci.md](docs/cloud-ci.md)。

OHOS 构建需要匹配的 Flutter OHOS 工具链。标准 Flutter SDK 不包含该工具链。
其他 Flutter 通道也许可用。此仓库尚无对应记录。

应用运行时不需要网络。
云端首次配置可能需要下载依赖。
本机不安装 SDK 或依赖缓存。

OHOS 与 Android 发行版不请求网络权限。
Android 调试与分析版保留开发网络权限。
主机测试以 `HttpOverrides` 记录 HTTP 客户端。
本地 Schema 与 URL 数据测试均记录零个。

## 校验

以下命令只允许在 GitHub 运行。
不要在本机运行这些命令。

测试套件包含 12 个测试文件。

运行测试。

```text
flutter test
```

运行静态分析。

```text
dart analyze lib test
```

校验格式。

```text
dart format --output=none --set-exit-if-changed lib test
```

校验内置内容。

```text
python tool/build_json_content.py --check
```

该命令校验三份资源。它不会改写资源。

启动课程校验入口。

```text
flutter run --dart-define=QFLI_VERIFY_CATALOG=true
```

入口校验示例、练习答案、输入样本与工具。
每次校验生成新的 `runId`。
报告写入失败会使本次校验失败。

现有校验记录如下。

| 范围 | 结果 |
| --- | --- |
| 2026-10-24 主机完整测试 | 124 项通过，并发数为 1。 |
| 同次静态分析 | `lib` 与 `test` 无问题。 |
| 同次资源校验 | 三份资源一致。 |
| 2026-10-22 OHOS 模拟器 | API 26 x86_64 通过 340 条示例。 |

历史设备结果可能不覆盖后续共享核心修改。
当前版本的全量设备通过也许尚未证实。
签名发行与实体 ARM64 设备仍缺少验收证据。

主机证据见[校验记录](.trellis/tasks/10-22-offline-json-ide/research/host-20261024-published-core.md)。
主机测试不能证明设备通过。

JSON 证据不覆盖兄弟产品。

## Schema 边界

本地 Schema 校验支持 JSON Schema 2020-12 的子集。

- 类型规则包括 `type`、`enum`、`const`。
- 对象规则包括 `properties`、`required`、`additionalProperties`。
- 数组规则包括 `items`、`prefixItems`、`uniqueItems`。
- 组合规则包括 `allOf`、`anyOf`、`oneOf`、`not`。
- 校验器支持长度、数量与数值约束。
- `$ref` 仅接受 `#` 或 `#/` 开头的文档内引用。
- `pattern` 使用 Dart Unicode 正则。

校验器拒绝不支持的关键字。校验器不获取远程 Schema。
`format`、条件规则与 `patternProperties` 暂不受支持。
嵌套资源声明暂不受支持。

完整关键字列表见 [Schema 实现](lib/json/json_schema.dart)。
子集校验通过不代表完整规范校验通过。

## 限制

| 项目 | 上限或行为 |
| --- | --- |
| 输入 | 2 Mi UTF-16 代码单元。 |
| 输出 | 4 Mi UTF-16 代码单元。 |
| 文档深度 | 128 层。 |
| 值节点 | 50000 个。 |
| CSV 单元格 | 200000 个。 |
| 补丁累计工作量 | 250000 个节点。 |
| 工具任务 | 5 秒后超时。用户可取消任务。 |
| 运行入口读取 | 2 MiB UTF-8 字节。 |

超出有符号 64 位范围的整数必须写成字符串。
小数与指数使用有限 Dart 双精度数。

编辑器诊断只覆盖 `.json` 文档。产品不提供断点调试器。
文档中的 URL 仅作为数据。应用不打开该 URL。

产品约定见 [JSON 离线规范](.trellis/spec/json-offline.md)。
