import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';

import 'json_tools.dart';
import 'json_workbench.dart';

/// Product-owned editor with local diagnostics, source navigation and output.
class JsonDocumentPage extends StatefulWidget {
  const JsonDocumentPage({super.key, required this.request});
  final DocumentToolRequest request;
  @override
  State<JsonDocumentPage> createState() => _JsonDocumentPageState();
}

class _JsonDocumentPageState extends State<JsonDocumentPage> {
  late final _source = JsonSourceController(text: widget.request.text);
  late String _saved = widget.request.text;
  late String _lastObservedSource = widget.request.text;
  final _focus = FocusNode();
  final _output = <String>[];
  Timer? _debounce;
  JsonInspection? _inspection;
  int _generation = 0;
  bool _saving = false;
  bool _checking = true;
  bool _discard = false;
  JsonOperationTask? _transformTask;
  String _query = '';
  bool get _dirty => _source.text != _saved;

  @override
  void initState() {
    super.initState();
    _source.addListener(_changed);
    unawaited(_validate());
  }

  void _changed() {
    if (_source.text == _lastObservedSource) {
      setState(() {});
      return;
    }
    _lastObservedSource = _source.text;
    _debounce?.cancel();
    _generation++;
    _source.problemOffset = null;
    setState(() {
      _checking = true;
      _inspection = null;
    });
    _debounce = Timer(
      const Duration(milliseconds: 250),
      () => unawaited(_validate()),
    );
  }

  Future<void> _validate({bool log = false}) async {
    _debounce?.cancel();
    final source = _source.text;
    final generation = ++_generation;
    final inspection = await compute(JsonWorkbench.inspect, source);
    if (!mounted || generation != _generation) return;
    setState(() {
      _inspection = inspection;
      _checking = false;
      _source.lastValidatedSource = source;
      _source.problemOffset = inspection.valid
          ? null
          : inspection.problems.first.offset;
      if (log) {
        _output.add(
          '${TimeOfDay.now().format(context)}  ${inspection.valid ? '校验通过：${inspection.nodes.length} 个节点' : inspection.problems.join('\n')}',
        );
        if (_output.length > 100) _output.removeAt(0);
      }
    });
  }

  Future<void> _transform(JsonOperation operation) async {
    if (widget.request.readOnly || _transformTask != null) return;
    final source = _source.text;
    final task = JsonOperationTask(operation, source);
    setState(() => _transformTask = task);
    try {
      final output = await task.result;
      if (!mounted) return;
      if (_source.text != source) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('文档已更新，请重新执行')));
        return;
      }
      _source.value = TextEditingValue(
        text: output,
        selection: const TextSelection.collapsed(offset: 0),
      );
    } on FormatException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(error.message)));
      await _validate(log: true);
    } finally {
      if (mounted) setState(() => _transformTask = null);
    }
  }

  void _jump(int offset, [int? end]) {
    final start = offset.clamp(0, _source.text.length);
    _source.selection = TextSelection(
      baseOffset: start,
      extentOffset: (end ?? start).clamp(start, _source.text.length),
    );
    _focus.requestFocus();
  }

  Future<void> _save() async {
    if (_saving || widget.request.readOnly) return;
    final source = _source.text;
    setState(() => _saving = true);
    String? error;
    try {
      error = await widget.request.save(source);
    } on Object catch (e) {
      error = '保存失败：$e';
    }
    if (!mounted) return;
    setState(() {
      _saving = false;
      if (error == null) _saved = source;
    });
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? '已保存')));
  }

  Future<void> _leave(bool didPop) async {
    if (didPop || !_dirty) return;
    final discard = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('放弃未保存的修改？'),
        content: const Text('返回后仍保留上次保存的文件内容。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('继续编辑'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('放弃修改'),
          ),
        ],
      ),
    );
    if (!mounted || discard != true) return;
    setState(() => _discard = true);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) Navigator.pop(context);
    });
  }

  @override
  void dispose() {
    _generation++;
    _transformTask?.cancel();
    _debounce?.cancel();
    _source.removeListener(_changed);
    _source.dispose();
    _focus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final inspection = _inspection;
    final position = _source.selection.baseOffset.clamp(0, _source.text.length);
    final before = _source.text.substring(0, position);
    final line = '\n'.allMatches(before).length + 1;
    final column = position - before.lastIndexOf('\n');
    return PopScope(
      canPop: !_dirty || _discard,
      onPopInvokedWithResult: (didPop, result) => unawaited(_leave(didPop)),
      child: DefaultTabController(
        length: 3,
        child: Scaffold(
          appBar: AppBar(
            title: Text('${widget.request.name}${_dirty ? ' •' : ''}'),
            actions: [
              IconButton(
                tooltip: '保存',
                onPressed: _saving || widget.request.readOnly ? null : _save,
                icon: _saving
                    ? const SizedBox.square(
                        dimension: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.save_outlined),
              ),
            ],
          ),
          body: LayoutBuilder(
            builder: (context, constraints) => Column(
              children: [
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Row(
                    children: [
                      const CircleAvatar(
                        radius: 17,
                        child: Text('JSON', style: TextStyle(fontSize: 10)),
                      ),
                      const SizedBox(width: 8),
                      TextButton.icon(
                        onPressed: () => _validate(log: true),
                        icon: const Icon(Icons.rule),
                        label: const Text('校验'),
                      ),
                      TextButton(
                        onPressed:
                            widget.request.readOnly || _transformTask != null
                            ? null
                            : () => _transform(JsonOperation.format),
                        child: const Text('格式化'),
                      ),
                      TextButton(
                        onPressed:
                            widget.request.readOnly || _transformTask != null
                            ? null
                            : () => _transform(JsonOperation.sort),
                        child: const Text('键排序'),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
                    child: TextField(
                      key: const Key('json-document-source'),
                      controller: _source,
                      focusNode: _focus,
                      expands: true,
                      maxLines: null,
                      minLines: null,
                      readOnly: widget.request.readOnly,
                      autocorrect: false,
                      enableSuggestions: false,
                      keyboardType: TextInputType.multiline,
                      textAlignVertical: TextAlignVertical.top,
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 14,
                        height: 1.5,
                      ),
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.all(12),
                      ),
                    ),
                  ),
                ),
                Container(
                  color: colors.surfaceContainer,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 4,
                  ),
                  child: Row(
                    children: [
                      Text('行 $line，列 $column'),
                      const Spacer(),
                      Text(
                        _checking
                            ? '正在检查…'
                            : inspection?.valid == true
                            ? 'JSON 有效'
                            : '${inspection?.problems.length ?? 0} 个问题',
                        style: TextStyle(
                          color: inspection?.valid == false
                              ? colors.error
                              : colors.primary,
                        ),
                      ),
                    ],
                  ),
                ),
                SizedBox(
                  height: (constraints.maxHeight * .4).clamp(80.0, 220.0),
                  child: Column(
                    children: [
                      TabBar(
                        tabs: [
                          Tab(text: '问题 ${inspection?.problems.length ?? 0}'),
                          const Tab(text: '结构'),
                          const Tab(text: '输出'),
                        ],
                      ),
                      Expanded(
                        child: TabBarView(
                          children: [
                            _problems(inspection),
                            _structure(inspection),
                            Column(
                              children: [
                                Align(
                                  alignment: Alignment.centerRight,
                                  child: TextButton(
                                    onPressed: () => setState(_output.clear),
                                    child: const Text('清空输出'),
                                  ),
                                ),
                                Expanded(
                                  child: SingleChildScrollView(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 12,
                                    ),
                                    child: SelectableText(
                                      _output.isEmpty
                                          ? '点击“校验”记录本地校验结果。'
                                          : _output.join('\n'),
                                      style: const TextStyle(
                                        fontFamily: 'monospace',
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _problems(JsonInspection? inspection) {
    if (_checking) return const Center(child: Text('正在检查当前文档…'));
    if (inspection?.valid != false) {
      return const Center(child: Text('未发现 JSON 语法问题'));
    }
    return ListView(
      children: [
        for (final problem in inspection!.problems)
          ListTile(
            dense: true,
            leading: const Icon(Icons.error_outline),
            title: Text(problem.message),
            subtitle: Text('行 ${problem.line}，列 ${problem.column} · 点击定位'),
            onTap: () => _jump(problem.offset),
          ),
      ],
    );
  }

  Widget _structure(JsonInspection? inspection) {
    if (inspection?.valid != true) {
      return const Center(child: Text('修正语法后显示结构；数组也支持展开和定位。'));
    }
    final nodes = inspection!.nodes
        .where(
          (n) =>
              _query.isEmpty ||
              n.pointer.toLowerCase().contains(_query.toLowerCase()),
        )
        .toList();
    return Column(
      children: [
        SizedBox(
          height: 42,
          child: TextField(
            onChanged: (text) => setState(() => _query = text),
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: '搜索 JSON Pointer 路径',
              isDense: true,
            ),
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: nodes.length,
            itemBuilder: (context, index) {
              final node = nodes[index];
              final scalar = node.value is Map || node.value is List
                  ? node.type
                  : JsonWorkbench.pretty(node.value);
              final label = scalar.length > 90
                  ? '${scalar.substring(0, 90)}…'
                  : scalar;
              return ListTile(
                dense: true,
                visualDensity: VisualDensity.compact,
                title: Text(
                  node.pointer.isEmpty ? '(根)' : node.pointer,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(
                  '$label · ${node.type}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: const Icon(Icons.my_location, size: 16),
                onTap: () => _jump(node.offset, node.end),
              );
            },
          ),
        ),
      ],
    );
  }
}

/// JSON token colors plus an exact source error span. Flutter handles selection,
/// scrolling and IME; composing decoration is preserved for text input methods.
class JsonSourceController extends TextEditingController {
  JsonSourceController({super.text});
  int? problemOffset;
  String? lastValidatedSource;
  static final _tokens = RegExp(
    r'"(?:\\.|[^"\\])*"|-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b|\b(?:true|false|null)\b',
  );
  @override
  TextSpan buildTextSpan({
    required BuildContext context,
    TextStyle? style,
    required bool withComposing,
  }) {
    final spans = <TextSpan>[];
    final boundaries = <int>{0, text.length};
    final matches = _tokens.allMatches(text).toList();
    for (final m in matches) {
      boundaries.add(m.start);
      boundaries.add(m.end);
    }
    final error = problemOffset == null || text.isEmpty
        ? null
        : problemOffset!.clamp(0, text.length - 1);
    if (error != null) {
      boundaries.add(error);
      boundaries.add(error + 1);
    }
    final composing = value.composing;
    if (withComposing && composing.isValid && composing.end <= text.length) {
      boundaries.add(composing.start);
      boundaries.add(composing.end);
    }
    final positions = boundaries.toList()..sort();
    var matchIndex = 0;
    final dark = Theme.of(context).brightness == Brightness.dark;
    for (var i = 0; i < positions.length - 1; i++) {
      final start = positions[i], end = positions[i + 1];
      while (matchIndex < matches.length && matches[matchIndex].end <= start) {
        matchIndex++;
      }
      final m = matchIndex < matches.length ? matches[matchIndex] : null;
      TextStyle part = const TextStyle();
      if (m != null && m.start <= start && m.end >= end) {
        final token = m.group(0)!;
        var after = m.end;
        while (after < text.length &&
            const [32, 9, 10, 13].contains(text.codeUnitAt(after))) {
          after++;
        }
        final key =
            token.startsWith('"') && after < text.length && text[after] == ':';
        part = TextStyle(
          color: token.startsWith('"')
              ? key
                    ? (dark ? const Color(0xff9cdcfe) : const Color(0xff0451a5))
                    : (dark ? const Color(0xffce9178) : const Color(0xffa31515))
              : (dark ? const Color(0xffb5cea8) : const Color(0xff098658)),
        );
      }
      if (error != null && start == error) {
        part = part.copyWith(
          decoration: TextDecoration.underline,
          decorationStyle: TextDecorationStyle.wavy,
          decorationColor: Theme.of(context).colorScheme.error,
          decorationThickness: 2,
        );
      } else if (withComposing &&
          composing.isValid &&
          start >= composing.start &&
          end <= composing.end) {
        part = part.copyWith(decoration: TextDecoration.underline);
      }
      spans.add(TextSpan(text: text.substring(start, end), style: part));
    }
    return TextSpan(style: style, children: spans);
  }
}
