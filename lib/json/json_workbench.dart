import 'dart:convert';

class JsonProblem {
  const JsonProblem(this.message, this.offset, this.line, this.column);
  final String message;
  final int offset;
  final int line;
  final int column;
  @override
  String toString() => '第 $line 行，第 $column 列：$message';
}

class JsonNode {
  const JsonNode(this.pointer, this.value, this.offset, this.end, this.depth);
  final String pointer;
  final Object? value;
  final int offset;
  final int end;
  final int depth;
  String get type => JsonWorkbench.typeOf(value);
}

class JsonInspection {
  const JsonInspection(this.value, this.nodes, this.problems);
  final Object? value;
  final List<JsonNode> nodes;
  final List<JsonProblem> problems;
  bool get valid => problems.isEmpty;
  String get formatted => JsonWorkbench.pretty(value);
}

/// All JSON product operations run locally and share this parser/contract.
abstract final class JsonWorkbench {
  static const maximumLength = 2 * 1024 * 1024;
  static const maximumDepth = 128;
  static const maximumNodes = 50000;
  static const maximumOutputLength = 4 * 1024 * 1024;
  static const maximumCsvCells = 200000;
  static const maximumPatchWorkNodes = 250000;
  static String pretty(Object? value) {
    _guardValue(value, operation: '格式化');
    return const JsonEncoder.withIndent('  ').convert(value);
  }

  /// Count before encoding or copying. The character estimate includes the
  /// pretty printer's indentation, so a shallow source limit cannot hide a
  /// much larger deeply indented output. Returns visited value nodes.
  static int _guardValue(Object? value, {required String operation}) {
    var nodes = 0, characters = 0;
    void add(int amount) {
      characters += amount;
      if (characters > maximumOutputLength) {
        throw FormatException('$operation 结果超过 4 Mi UTF-16 字符上限');
      }
    }

    void visit(Object? node, int depth) {
      if (++nodes > maximumNodes) {
        throw FormatException('$operation 结果节点超过 50000 个');
      }
      if (depth > maximumDepth) {
        throw FormatException('$operation 结果嵌套超过 128 层');
      }
      if (node is Map) {
        add(2);
        if (node.isNotEmpty) {
          add(2 + depth * 2 + (node.length - 1) * 2);
          for (final entry in node.entries) {
            if (entry.key is! String) {
              throw const FormatException('JSON 对象键必须为字符串');
            }
            add((depth + 1) * 2 + _quotedLength(entry.key as String) + 2);
            visit(entry.value, depth + 1);
          }
        }
      } else if (node is List) {
        add(2);
        if (node.isNotEmpty) {
          add(2 + depth * 2 + (node.length - 1) * 2);
          for (final child in node) {
            add((depth + 1) * 2);
            visit(child, depth + 1);
          }
        }
      } else if (node is String) {
        add(_quotedLength(node));
      } else if (node == null ||
          node is bool ||
          (node is num && node.isFinite)) {
        add(jsonEncode(node).length);
      } else {
        throw const FormatException('需要有限数值、字符串、布尔值、null 或 JSON 容器');
      }
    }

    visit(value, 0);
    return nodes;
  }

  static int _quotedLength(String text) {
    var length = text.length + 2;
    for (final unit in text.codeUnits) {
      if (unit == 34 || unit == 92 || const [8, 9, 10, 12, 13].contains(unit)) {
        length++;
      } else if (unit < 32) {
        length += 5;
      }
    }
    return length;
  }

  static String typeOf(Object? value) => switch (value) {
    null => 'null',
    Map() => 'object',
    List() => 'array',
    String() => 'string',
    bool() => 'boolean',
    int() => 'integer',
    num() => 'number',
    _ => throw const FormatException('不是 JSON 值'),
  };

  static JsonInspection inspect(String source) {
    final parser = _JsonParser(source);
    try {
      if (source.length > maximumLength) {
        throw const FormatException('文件超过 2 MiB 编辑校验上限', null, 0);
      }
      final value = parser.parse();
      parser.nodes.sort((a, b) => a.offset.compareTo(b.offset));
      return JsonInspection(value, List.unmodifiable(parser.nodes), const []);
    } on FormatException catch (error) {
      final offset = (error.offset ?? parser.offset).clamp(0, source.length);
      final before = source.substring(0, offset);
      final breaks = RegExp(r'\r\n|\r|\n').allMatches(before).toList();
      final line = breaks.length + 1;
      final column = offset - (breaks.isEmpty ? 0 : breaks.last.end) + 1;
      return JsonInspection(null, const [], [
        JsonProblem(error.message, offset, line, column),
      ]);
    }
  }

  static Object? decode(String source) {
    final result = inspect(source);
    if (!result.valid) throw FormatException(result.problems.first.toString());
    return result.value;
  }

  static String escapeToken(String token) =>
      token.replaceAll('~', '~0').replaceAll('/', '~1');

  static List<String> pointerTokens(String pointer) {
    if (pointer.isEmpty) return const [];
    if (!pointer.startsWith('/')) {
      throw const FormatException('JSON Pointer 必须为空或以 / 开头');
    }
    return pointer.substring(1).split('/').map((token) {
      if (RegExp(r'~(?![01])').hasMatch(token)) {
        throw const FormatException('Pointer 仅允许 ~0 和 ~1 转义');
      }
      return token.replaceAll('~1', '/').replaceAll('~0', '~');
    }).toList();
  }

  static int _index(String token, int length, {bool inserting = false}) {
    if (inserting && token == '-') return length;
    if (!RegExp(r'^(0|[1-9][0-9]*)$').hasMatch(token)) {
      throw FormatException('无效数组下标：$token');
    }
    final index = int.tryParse(token);
    if (index == null || index >= length + (inserting ? 1 : 0)) {
      throw FormatException('数组下标越界：$token');
    }
    return index;
  }

  static Object? select(Object? value, String pointer) {
    for (final token in pointerTokens(pointer)) {
      if (value is Map<String, Object?> && value.containsKey(token)) {
        value = value[token];
      } else if (value is List) {
        value = value[_index(token, value.length)];
      } else {
        throw FormatException('路径不存在：$pointer');
      }
    }
    return value;
  }

  static Object? sortKeys(Object? value) => switch (value) {
    Map<String, Object?>() => {
      for (final key in value.keys.toList()..sort()) key: sortKeys(value[key]),
    },
    List() => value.map(sortKeys).toList(),
    _ => value,
  };

  static bool equal(Object? left, Object? right) {
    if (left is num && right is num) return left == right;
    if (left is List && right is List) {
      return left.length == right.length &&
          List.generate(
            left.length,
            (i) => i,
          ).every((i) => equal(left[i], right[i]));
    }
    if (left is Map && right is Map) {
      return left.length == right.length &&
          left.keys.every(
            (k) => right.containsKey(k) && equal(left[k], right[k]),
          );
    }
    return left == right;
  }

  /// RFC 7396: null members delete; arrays/scalars replace in full.
  static Object? mergePatch(Object? target, Object? patch) {
    if (patch is! Map<String, Object?>) return _copy(patch);
    final result = target is Map<String, Object?>
        ? Map<String, Object?>.from(target)
        : <String, Object?>{};
    for (final entry in patch.entries) {
      if (entry.value == null) {
        result.remove(entry.key);
      } else {
        result[entry.key] = mergePatch(result[entry.key], entry.value);
      }
    }
    return result;
  }

  static Object? _copy(Object? value) => jsonDecode(jsonEncode(value));

  /// RFC 6902. The input remains unchanged, including on a failed test.
  static Object? applyPatch(Object? value, Object? operations) {
    if (operations is! List) throw const FormatException('补丁必须是操作数组');
    var work =
        _guardValue(value, operation: '补丁输入') +
        _guardValue(operations, operation: '补丁操作');
    void charge(Object? current) {
      work += _guardValue(current, operation: '补丁');
      if (work > maximumPatchWorkNodes) {
        throw const FormatException('补丁累计处理节点超过 250000 个，请分批处理');
      }
    }

    Object? result = _copy(value);
    for (final operation in operations) {
      charge(result);
      if (operation is! Map ||
          operation['op'] is! String ||
          operation['path'] is! String) {
        throw const FormatException('每项补丁需要字符串 op 和 path');
      }
      final op = operation['op'] as String;
      final path = operation['path'] as String;
      final tokens = pointerTokens(path);
      if (op == 'test') {
        if (!operation.containsKey('value') ||
            !equal(select(result, path), operation['value'])) {
          throw FormatException('test 失败：$path');
        }
        continue;
      }
      Object? replacement;
      if (op == 'copy' || op == 'move') {
        final from = operation['from'];
        if (from is! String) throw const FormatException('copy/move 需要 from');
        final fromTokens = pointerTokens(from);
        if (op == 'move' &&
            tokens.length > fromTokens.length &&
            List.generate(
              fromTokens.length,
              (i) => i,
            ).every((i) => fromTokens[i] == tokens[i])) {
          throw const FormatException('不能把父节点移动到其子节点');
        }
        replacement = _copy(select(result, from));
        if (op == 'move' &&
            tokens.length == fromTokens.length &&
            List.generate(
              tokens.length,
              (i) => i,
            ).every((i) => tokens[i] == fromTokens[i])) {
          continue;
        }
        if (op == 'move') result = _mutate(result, fromTokens, 'remove', null);
      } else if (op == 'add' || op == 'replace') {
        if (!operation.containsKey('value')) {
          throw const FormatException('add/replace 需要 value（可以为 null）');
        }
        replacement = _copy(operation['value']);
      } else if (op != 'remove') {
        throw FormatException('不支持的补丁操作：$op');
      }
      result = _mutate(
        result,
        tokens,
        op == 'copy' || op == 'move' ? 'add' : op,
        replacement,
      );
      charge(result);
    }
    return result;
  }

  static Object? _mutate(
    Object? root,
    List<String> tokens,
    String op,
    Object? v,
  ) {
    if (tokens.isEmpty) {
      if (op == 'remove') throw const FormatException('不能删除整个文档');
      return v;
    }
    final parentPointer = tokens
        .take(tokens.length - 1)
        .map((t) => '/${escapeToken(t)}')
        .join();
    final parent = select(root, parentPointer);
    final key = tokens.last;
    if (parent is Map<String, Object?>) {
      if (op != 'add' && !parent.containsKey(key)) {
        throw FormatException('路径不存在：$key');
      }
      if (op == 'remove') {
        parent.remove(key);
      } else {
        parent[key] = v;
      }
    } else if (parent is List) {
      final index = _index(key, parent.length, inserting: op == 'add');
      if (op == 'add') {
        parent.insert(index, v);
      } else if (op == 'remove') {
        parent.removeAt(index);
      } else {
        parent[index] = v;
      }
    } else {
      throw const FormatException('目标父节点必须是对象或数组');
    }
    return root;
  }

  static List<Map<String, Object?>> diff(
    Object? before,
    Object? after, [
    String path = '',
  ]) {
    if (equal(before, after)) return [];
    if (before is Map<String, Object?> && after is Map<String, Object?>) {
      return [
        for (final key in before.keys)
          if (!after.containsKey(key))
            {'op': 'remove', 'path': '$path/${escapeToken(key)}'},
        for (final key in after.keys)
          if (!before.containsKey(key))
            {
              'op': 'add',
              'path': '$path/${escapeToken(key)}',
              'value': after[key],
            }
          else
            ...diff(before[key], after[key], '$path/${escapeToken(key)}'),
      ];
    }
    return [
      {'op': 'replace', 'path': path, 'value': after},
    ];
  }

  /// A lossless path manifest: container types preserve arrays vs numeric keys.
  static Map<String, Object?> flatten(Object? value) {
    _guardValue(value, operation: '路径展开输入');
    final containers = <String, String>{};
    final values = <String, Object?>{};
    var pathCharacters = 0;
    void visit(Object? node, String path) {
      pathCharacters += _quotedLength(path);
      if (pathCharacters > maximumOutputLength) {
        throw const FormatException('路径展开结果超过 4 Mi UTF-16 字符上限');
      }
      if (node is Map<String, Object?>) {
        containers[path] = 'object';
        for (final e in node.entries) {
          visit(e.value, '$path/${escapeToken(e.key)}');
        }
      } else if (node is List) {
        containers[path] = 'array';
        for (var i = 0; i < node.length; i++) {
          visit(node[i], '$path/$i');
        }
      } else {
        values[path] = node;
      }
    }

    visit(_copy(value), '');
    final result = {'containers': containers, 'values': values};
    _guardValue(result, operation: '路径展开');
    return result;
  }

  static Object? unflatten(Object? manifest) {
    if (manifest is! Map ||
        manifest['containers'] is! Map ||
        manifest['values'] is! Map) {
      throw const FormatException('需要 containers 和 values 路径清单');
    }
    final entries = <String, Object?>{};
    for (final e in (manifest['containers'] as Map).entries) {
      if (e.key is! String || (e.value != 'object' && e.value != 'array')) {
        throw const FormatException('容器类型必须为 object 或 array');
      }
      entries[e.key as String] = e.value == 'object'
          ? <String, Object?>{}
          : <Object?>[];
    }
    for (final e in (manifest['values'] as Map).entries) {
      if (e.key is! String ||
          entries.containsKey(e.key) ||
          e.value is Map ||
          e.value is List) {
        throw const FormatException('叶子路径冲突或值不是标量');
      }
      entries[e.key as String] = e.value;
    }
    if (!entries.containsKey('')) throw const FormatException('缺少根路径');
    final paths = entries.keys.where((p) => p.isNotEmpty).toList()
      ..sort((a, b) {
        final depth = pointerTokens(
          a,
        ).length.compareTo(pointerTokens(b).length);
        if (depth != 0) return depth;
        final aa = pointerTokens(a), bb = pointerTokens(b);
        final ai = int.tryParse(aa.last), bi = int.tryParse(bb.last);
        final ap = aa.take(aa.length - 1).join('/'),
            bp = bb.take(bb.length - 1).join('/');
        return ap == bp && ai != null && bi != null
            ? ai.compareTo(bi)
            : a.compareTo(b);
      });
    final root = entries[''];
    for (final path in paths) {
      _mutate(root, pointerTokens(path), 'add', entries[path]);
    }
    return root;
  }

  static List<Object?> fromJsonLines(String source) {
    if (source.length > maximumLength) {
      throw const FormatException('JSON Lines 整体输入超过 2 Mi 字符上限');
    }
    final lines = const LineSplitter().convert(source);
    final values = <Object?>[];
    var nodes = 1; // The converted root array is a node too.
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim().isEmpty) continue;
      final result = inspect(lines[i]);
      if (!result.valid) {
        throw FormatException(
          'JSON Lines 第 ${i + 1} 行：${result.problems.first}',
        );
      }
      nodes += result.nodes.length;
      if (nodes > maximumNodes) {
        throw FormatException('JSON Lines 第 ${i + 1} 行：整体节点超过 50000 个');
      }
      values.add(result.value);
    }
    _guardValue(values, operation: 'JSON Lines 转换');
    return values;
  }

  static String toJsonLines(Object? value) {
    if (value is! List) throw const FormatException('转换 JSON Lines 需要根数组');
    return value.map(jsonEncode).join('\n');
  }

  static String toCsv(Object? value) {
    if (value is! List || value.any((row) => row is! Map<String, Object?>)) {
      throw const FormatException('CSV 转换需要对象数组');
    }
    if (value.isEmpty) return '';
    _guardValue(value, operation: 'CSV 输入');
    final keys = <String>{
      for (final row in value) ...(row as Map<String, Object?>).keys,
    };
    if ((value.length + 1) * keys.length > maximumCsvCells) {
      throw const FormatException('CSV 行列组合超过 200000 个单元格，请减少行数或列数');
    }
    String cell(Object? v) {
      final text = v == null
          ? ''
          : v is String
          ? v
          : jsonEncode(v);
      return RegExp('[",\r\n]').hasMatch(text)
          ? '"${text.replaceAll('"', '""')}"'
          : text;
    }

    final output = StringBuffer();
    var outputLength = 0;
    void write(String text) {
      outputLength += text.length;
      if (outputLength > maximumOutputLength) {
        throw const FormatException('CSV 输出超过 4 Mi UTF-16 字符上限');
      }
      output.write(text);
    }

    var first = true;
    for (final key in keys) {
      if (!first) write(',');
      first = false;
      write(cell(key));
    }
    for (final row in value) {
      write('\r\n');
      first = true;
      for (final key in keys) {
        if (!first) write(',');
        first = false;
        write(cell((row as Map)[key]));
      }
    }
    return output.toString();
  }
}

class _JsonParser {
  _JsonParser(this.source);
  final String source;
  int offset = 0;
  int count = 0;
  int pointerCharacters = 0;
  final nodes = <JsonNode>[];
  void fail(String message, [int? at]) =>
      throw FormatException(message, source, at ?? offset);
  void whitespace() {
    while (offset < source.length &&
        const [32, 9, 10, 13].contains(source.codeUnitAt(offset))) {
      offset++;
    }
  }

  bool consume(String c) {
    whitespace();
    if (source.startsWith(c, offset)) {
      offset += c.length;
      return true;
    }
    return false;
  }

  Object? parse() {
    final value = read('', 0);
    whitespace();
    if (offset != source.length) fail('根值之后存在多余内容');
    return value;
  }

  Object? read(String pointer, int depth) {
    whitespace();
    if (depth > JsonWorkbench.maximumDepth) fail('嵌套超过 128 层');
    if (++count > JsonWorkbench.maximumNodes) fail('节点超过 50000 个');
    // A long ancestor key repeats in every child's full path. Bound their
    // combined size before retaining paths for an otherwise small document.
    pointerCharacters += pointer.length;
    if (pointerCharacters > JsonWorkbench.maximumOutputLength) {
      fail('结构路径累计超过 4 Mi UTF-16 字符上限');
    }
    final start = offset;
    Object? value;
    if (consume('{')) {
      final map = <String, Object?>{};
      if (!consume('}')) {
        do {
          whitespace();
          final keyOffset = offset;
          if (offset >= source.length || source[offset] != '"') {
            fail('对象键必须用双引号包围');
          }
          final key = string();
          if (map.containsKey(key)) fail('重复的对象键：$key', keyOffset);
          if (!consume(':')) fail('对象键后缺少冒号 :');
          map[key] = read(
            '$pointer/${JsonWorkbench.escapeToken(key)}',
            depth + 1,
          );
          if (consume('}')) break;
          if (!consume(',')) fail('对象成员之间缺少逗号 , 或结束符 }');
        } while (true);
      }
      value = map;
    } else if (consume('[')) {
      final list = <Object?>[];
      if (!consume(']')) {
        do {
          list.add(read('$pointer/${list.length}', depth + 1));
          if (consume(']')) break;
          if (!consume(',')) fail('数组元素之间缺少逗号 , 或结束符 ]');
        } while (true);
      }
      value = list;
    } else if (offset < source.length && source[offset] == '"') {
      value = string();
    } else if (consume('true')) {
      value = true;
    } else if (consume('false')) {
      value = false;
    } else if (consume('null')) {
      value = null;
    } else {
      final match = RegExp(
        r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?',
      ).matchAsPrefix(source, offset);
      if (match == null) fail('需要 JSON 值：对象、数组、双引号字符串、数字、true、false 或 null');
      final text = match!.group(0)!;
      if (!text.contains(RegExp('[.eE]'))) {
        value = int.tryParse(text);
        if (value == null) {
          fail('整数超出当前工具链 64 位范围；请用字符串保存精确的大整数', start);
        }
      } else {
        value = double.tryParse(text);
      }
      if (value == null || !(value as num).isFinite) fail('数字超出当前工具链有限数值范围');
      offset = match.end;
    }
    nodes.add(JsonNode(pointer, value, start, offset, depth));
    return value;
  }

  String string() {
    final start = offset++;
    while (offset < source.length) {
      final char = source.codeUnitAt(offset++);
      if (char == 34) {
        try {
          return jsonDecode(source.substring(start, offset)) as String;
        } on FormatException catch (e) {
          fail(e.message, start + (e.offset ?? 0));
        }
      }
      if (char == 92 && offset < source.length) {
        offset++;
      }
    }
    fail('字符串缺少结束双引号', start);
    return ''; // Unreachable: fail always throws.
  }
}
