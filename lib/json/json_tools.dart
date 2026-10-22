import 'dart:async';
import 'dart:convert';
import 'dart:isolate';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qfli_studio_core/pages/tools_grid.dart';
import 'package:qfli_studio_core/store/project_store.dart';

import 'json_schema.dart';
import 'json_workbench.dart';

enum JsonOperation {
  format('格式化与校验', '检查语法、重复键与错误位置，整理缩进'),
  minify('JSON 压缩', '删除无意义空白，保留字符串内容'),
  sort('递归键排序', '按对象键排序，数组顺序保持不变'),
  pointer('JSON Pointer 查询', '用 RFC 6901 路径提取对象和数组中的值'),
  diff('结构差异', '比较两份数据，生成可应用的 JSON Patch'),
  merge('Merge Patch', '合并对象；null 删除字段，数组整体替换'),
  patch('JSON Patch', '应用 add / remove / replace / move / copy / test'),
  flatten('展开路径', '生成保留容器类型的无损路径清单'),
  unflatten('还原路径', '从路径清单恢复数组、对象和空容器'),
  fromLines('JSON Lines 转数组', '逐行校验 JSON，显示出错的原始行号'),
  toLines('数组转 JSON Lines', '每个元素输出为独立一行 JSON'),
  quote('字符串转义', '将原始文本编码为 JSON 字符串'),
  unquote('字符串反转义', '还原双引号、换行、Unicode 等转义'),
  csv('对象数组转 CSV', '合并列名，正确处理逗号、双引号与换行'),
  schema('本地 Schema 校验', '检查字段、类型与约束，仅解析文档内引用'),
  stats('结构统计', '查看节点、类型、深度与 UTF-8 字节数');

  const JsonOperation(this.title, this.description);
  final String title;
  final String description;
  bool get secondary =>
      const {pointer, diff, merge, patch, schema}.contains(this);
  String get secondLabel => switch (this) {
    pointer => 'JSON Pointer（空路径代表根值）',
    schema => '本地 JSON Schema',
    patch => 'JSON Patch 操作数组',
    merge => 'Merge Patch 文档',
    _ => '比较目标 JSON',
  };
  String get initialSource => switch (this) {
    quote => '你好，JSON！\n第二行',
    unquote => r'"你好\nJSON"',
    fromLines => '{"id":1}\n{"id":2}',
    toLines || csv => '[{"id":1,"name":"Ada"},{"id":2,"name":"林"}]',
    unflatten =>
      '{"containers":{"":"object","/items":"array"},"values":{"/items/0":true}}',
    _ => '{"name":"QFLIJson","items":[{"id":1,"ready":true}],"version":1}',
  };
  String get initialSecond => switch (this) {
    pointer => '/items/0/id',
    schema =>
      '{"type":"object","required":["name"],"properties":{"name":{"type":"string","minLength":1}}}',
    patch =>
      '[{"op":"test","path":"/version","value":1},{"op":"replace","path":"/version","value":2}]',
    merge => '{"version":2,"name":null}',
    _ => '{"name":"QFLIJson","items":[],"version":2}',
  };

  String execute(String source, [String second = '']) {
    if (source.length > JsonWorkbench.maximumLength ||
        second.length > JsonWorkbench.maximumLength) {
      throw const FormatException('输入超过 2 Mi 字符上限');
    }
    if (this == quote) return jsonEncode(source);
    if (this == fromLines) {
      return JsonWorkbench.pretty(JsonWorkbench.fromJsonLines(source));
    }
    final value = JsonWorkbench.decode(source);
    return switch (this) {
      format => JsonWorkbench.pretty(value),
      minify => jsonEncode(value),
      sort => JsonWorkbench.pretty(JsonWorkbench.sortKeys(value)),
      pointer => JsonWorkbench.pretty(JsonWorkbench.select(value, second)),
      diff => JsonWorkbench.pretty(
        JsonWorkbench.diff(value, JsonWorkbench.decode(second)),
      ),
      merge => JsonWorkbench.pretty(
        JsonWorkbench.mergePatch(value, JsonWorkbench.decode(second)),
      ),
      patch => JsonWorkbench.pretty(
        JsonWorkbench.applyPatch(value, JsonWorkbench.decode(second)),
      ),
      flatten => JsonWorkbench.pretty(JsonWorkbench.flatten(value)),
      unflatten => JsonWorkbench.pretty(JsonWorkbench.unflatten(value)),
      toLines => JsonWorkbench.toJsonLines(value),
      csv => JsonWorkbench.toCsv(value),
      unquote =>
        value is String
            ? value
            : throw const FormatException('请输入带双引号的 JSON 字符串'),
      schema => _schema(value, second),
      stats => _statistics(source),
      _ => throw const FormatException('未知操作'),
    };
  }

  static String _schema(Object? value, String source) {
    final errors = LocalJsonSchema.validate(
      value,
      JsonWorkbench.decode(source),
    );
    return errors.isEmpty
        ? '校验通过（本地 Schema 支持范围内）'
        : '校验未通过：\n${errors.join('\n')}';
  }

  static String _statistics(String source) {
    final inspection = JsonWorkbench.inspect(source);
    final types = <String, int>{};
    var depth = 0;
    for (final node in inspection.nodes) {
      types.update(node.type, (n) => n + 1, ifAbsent: () => 1);
      if (node.depth > depth) depth = node.depth;
    }
    return JsonWorkbench.pretty({
      'nodes': inspection.nodes.length,
      'maximumDepth': depth,
      'utf8Bytes': utf8.encode(source).length,
      'types': types,
    });
  }
}

/// Each task owns a worker so expensive patterns can be stopped, including when
/// the page closes. Timing out a Future alone would leave its isolate running.
class JsonOperationTask {
  JsonOperationTask(
    JsonOperation operation,
    String source, [
    String second = '',
    Duration timeout = const Duration(seconds: 5),
  ]) {
    _subscription = _port.listen((message) {
      if (message is (bool, String)) {
        if (message.$1) {
          _complete(message.$2);
        } else {
          _fail(message.$2);
        }
      } else {
        _fail('操作未能完成，请缩小输入后重试');
      }
    });
    _timer = Timer(timeout, () => _fail('处理超时，请缩小输入或简化 Schema 规则'));
    unawaited(_start(operation, source, second));
  }

  final _completion = Completer<String>();
  final _port = ReceivePort();
  late final StreamSubscription<Object?> _subscription;
  late final Timer _timer;
  Isolate? _worker;
  Future<String> get result => _completion.future;

  Future<void> _start(
    JsonOperation operation,
    String source,
    String second,
  ) async {
    try {
      _worker = await Isolate.spawn(
        _executeJsonOperation,
        (_port.sendPort, operation, source, second),
        onError: _port.sendPort,
        onExit: _port.sendPort,
      );
      if (_completion.isCompleted) _worker!.kill(priority: Isolate.immediate);
    } on Object {
      _fail('无法启动本地处理，请重试');
    }
  }

  void _complete(String output) {
    if (_completion.isCompleted) return;
    _completion.complete(output);
    _close();
  }

  void _fail(String error) {
    if (_completion.isCompleted) return;
    _completion.completeError(FormatException(error));
    _close();
  }

  void cancel() => _fail('操作已取消');

  void _close() {
    _timer.cancel();
    _worker?.kill(priority: Isolate.immediate);
    unawaited(_subscription.cancel());
    _port.close();
  }
}

void _executeJsonOperation((SendPort, JsonOperation, String, String) request) {
  try {
    final output = request.$2.execute(request.$3, request.$4);
    if (output.length > JsonWorkbench.maximumOutputLength) {
      throw const FormatException('结果超过 4 Mi 字符上限，请缩小输入');
    }
    request.$1.send((true, output));
  } on FormatException catch (error) {
    request.$1.send((false, error.message));
  } on Object {
    request.$1.send((false, '操作未能完成，请检查输入数据'));
  }
}

Widget jsonToolsTab(ProjectStore store, VoidCallback onOpenTerminal) =>
    ToolsGrid(
      onOpenTerminal: onOpenTerminal,
      sections: [
        ToolSection(
          title: 'JSON 数据工具',
          icon: Icons.data_object,
          tools: [
            for (final operation in JsonOperation.values)
              ToolDefinition(
                icon: switch (operation) {
                  JsonOperation.schema || JsonOperation.format => Icons.rule,
                  JsonOperation.pointer => Icons.search,
                  JsonOperation.diff => Icons.difference_outlined,
                  JsonOperation.stats => Icons.bar_chart,
                  _ => Icons.data_object,
                },
                title: operation.title,
                description: operation.description,
                builder: (_) => JsonOperationPage(operation: operation),
              ),
          ],
        ),
      ],
    );

class JsonOperationPage extends StatefulWidget {
  const JsonOperationPage({super.key, required this.operation});
  final JsonOperation operation;
  @override
  State<JsonOperationPage> createState() => _JsonOperationPageState();
}

class _JsonOperationPageState extends State<JsonOperationPage> {
  late final _source = TextEditingController(
    text: widget.operation.initialSource,
  );
  late final _second = TextEditingController(
    text: widget.operation.initialSecond,
  );
  final _result = TextEditingController();
  String? _error;
  JsonOperationTask? _task;
  bool get _running => _task != null;
  @override
  void dispose() {
    _task?.cancel();
    _source.dispose();
    _second.dispose();
    _result.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    if (_running) return;
    FocusScope.of(context).unfocus();
    final task = JsonOperationTask(
      widget.operation,
      _source.text,
      _second.text,
    );
    setState(() {
      _task = task;
      _error = null;
      _result.clear();
    });
    try {
      final output = await task.result;
      if (!mounted) return;
      setState(() {
        _result.text = output;
      });
    } on FormatException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
      });
    } finally {
      if (mounted) setState(() => _task = null);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.operation.title)),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(widget.operation.description),
        if (widget.operation == JsonOperation.schema)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text(
              '支持 JSON Schema 2020-12 的本地子集：类型、字段、枚举、数值/长度约束、组合规则和 #/ 本地引用。'
              '暂不支持 format、远程引用、条件规则、正则属性与嵌套资源；遇到未支持关键字会明确报错。'
              'pattern 使用 Dart Unicode 正则。',
            ),
          ),
        const SizedBox(height: 16),
        TextField(
          key: const Key('json-tool-source'),
          controller: _source,
          readOnly: _running,
          minLines: 6,
          maxLines: 16,
          autocorrect: false,
          enableSuggestions: false,
          style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
          decoration: InputDecoration(
            labelText: widget.operation == JsonOperation.quote
                ? '原始文本'
                : '输入 JSON',
            border: const OutlineInputBorder(),
          ),
        ),
        if (widget.operation.secondary) ...[
          const SizedBox(height: 16),
          TextField(
            key: const Key('json-tool-secondary'),
            controller: _second,
            readOnly: _running,
            minLines: 1,
            maxLines: 10,
            autocorrect: false,
            enableSuggestions: false,
            decoration: InputDecoration(
              labelText: widget.operation.secondLabel,
              border: const OutlineInputBorder(),
            ),
          ),
        ],
        const SizedBox(height: 16),
        Wrap(
          spacing: 12,
          children: [
            FilledButton.icon(
              onPressed: _running ? null : _run,
              icon: _running
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.play_arrow),
              label: Text(_running ? '处理中…' : '执行'),
            ),
            if (_running)
              TextButton(
                onPressed: () => _task?.cancel(),
                child: const Text('取消'),
              ),
            OutlinedButton.icon(
              onPressed: _running || _result.text.isEmpty
                  ? null
                  : () async {
                      await Clipboard.setData(
                        ClipboardData(text: _result.text),
                      );
                      if (context.mounted) {
                        ScaffoldMessenger.of(
                          context,
                        ).showSnackBar(const SnackBar(content: Text('结果已复制')));
                      }
                    },
              icon: const Icon(Icons.copy),
              label: const Text('复制结果'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        if (_error != null)
          SelectableText(
            _error!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        TextField(
          key: const Key('json-tool-result'),
          controller: _result,
          readOnly: true,
          minLines: 6,
          maxLines: 20,
          style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
          decoration: const InputDecoration(
            labelText: '结果',
            border: OutlineInputBorder(),
          ),
        ),
      ],
    ),
  );
}
