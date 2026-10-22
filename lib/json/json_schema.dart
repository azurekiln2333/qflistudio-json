import 'json_workbench.dart';

/// Explicit local subset. Unsupported validation keywords are errors, never a
/// silent pass. No URI resolver, HTTP client, or package installation is used.
abstract final class LocalJsonSchema {
  static const supported = {
    r'$schema',
    r'$id',
    r'$ref',
    r'$defs',
    'definitions',
    'title',
    'description',
    'default',
    'examples',
    r'$comment',
    'type',
    'enum',
    'const',
    'properties',
    'required',
    'additionalProperties',
    'items',
    'prefixItems',
    'minItems',
    'maxItems',
    'uniqueItems',
    'minLength',
    'maxLength',
    'pattern',
    'minimum',
    'maximum',
    'exclusiveMinimum',
    'exclusiveMaximum',
    'multipleOf',
    'minProperties',
    'maxProperties',
    'allOf',
    'anyOf',
    'oneOf',
    'not',
  };

  static List<String> validate(Object? value, Object? schema) {
    final errors = <String>[];
    final checked = <Object>{};
    var evaluationCount = 0;
    void check(Object? s, String path, int depth) {
      if (depth > 128) throw const FormatException('Schema 嵌套过深');
      if (s is bool) return;
      if (s is! Map<String, Object?>) {
        throw FormatException('$path 必须是对象或布尔值 Schema');
      }
      if (!checked.add(s)) return;
      for (final key in s.keys) {
        if (!supported.contains(key)) {
          throw FormatException('$path：暂不支持关键字 $key');
        }
      }
      for (final key in const [
        r'$schema',
        r'$id',
        r'$comment',
        'title',
        'description',
      ]) {
        if (s.containsKey(key) && s[key] is! String) {
          throw FormatException('$key 必须为字符串');
        }
      }
      if (s.containsKey('examples') && s['examples'] is! List) {
        throw const FormatException('examples 必须为数组');
      }
      if (s.containsKey(r'$schema') &&
          s[r'$schema'] != 'https://json-schema.org/draft/2020-12/schema' &&
          s[r'$schema'] != 'https://json-schema.org/draft/2020-12/schema#') {
        throw const FormatException(
          '本地子集仅采用 JSON Schema 2020-12 语义；不支持声明的其他方言',
        );
      }
      if (path != '#' && (s.containsKey(r'$id') || s.containsKey(r'$schema'))) {
        throw const FormatException('本地子集不支持嵌套 Schema 资源或方言声明');
      }
      for (final key in const ['properties', r'$defs', 'definitions']) {
        if (s.containsKey(key)) {
          final map = s[key];
          if (map is! Map<String, Object?>) throw FormatException('$key 必须为对象');
          for (final e in map.entries) {
            check(e.value, '$path/$key/${e.key}', depth + 1);
          }
        }
      }
      for (final key in const ['items', 'additionalProperties', 'not']) {
        if (s.containsKey(key)) check(s[key], '$path/$key', depth + 1);
      }
      for (final key in const ['allOf', 'anyOf', 'oneOf', 'prefixItems']) {
        if (s.containsKey(key)) {
          if (s[key] is! List ||
              (key != 'prefixItems' && (s[key] as List).isEmpty)) {
            throw FormatException(
              '$key 必须是${key == 'prefixItems' ? '' : '非空'}数组',
            );
          }
          for (final item in s[key] as List) {
            check(item, '$path/$key', depth + 1);
          }
        }
      }
      if (s.containsKey('required') &&
          (s['required'] is! List ||
              (s['required'] as List).any((x) => x is! String) ||
              (s['required'] as List).toSet().length !=
                  (s['required'] as List).length)) {
        throw const FormatException('required 必须是无重复的字符串数组');
      }
      const types = {
        'null',
        'boolean',
        'object',
        'array',
        'number',
        'integer',
        'string',
      };
      if (s.containsKey('type')) {
        final ts = s['type'] is List ? s['type'] as List : [s['type']];
        if (ts.isEmpty ||
            ts.any((t) => !types.contains(t)) ||
            ts.toSet().length != ts.length) {
          throw const FormatException('type 必须使用标准 JSON 类型名称且不能重复');
        }
      }
      for (final key in const [
        'minItems',
        'maxItems',
        'minLength',
        'maxLength',
        'minProperties',
        'maxProperties',
      ]) {
        if (s.containsKey(key) &&
            (s[key] is! num ||
                (s[key] as num) < 0 ||
                (s[key] as num) % 1 != 0)) {
          throw FormatException('$key 必须是非负整数');
        }
      }
      for (final key in const [
        'minimum',
        'maximum',
        'exclusiveMinimum',
        'exclusiveMaximum',
        'multipleOf',
      ]) {
        if (s.containsKey(key) &&
            (s[key] is! num ||
                !(s[key] as num).isFinite ||
                (key == 'multipleOf' && (s[key] as num) <= 0))) {
          throw FormatException('$key 必须是${key == 'multipleOf' ? '正' : ''}数值');
        }
      }
      if (s.containsKey('enum') &&
          (s['enum'] is! List || (s['enum'] as List).isEmpty)) {
        throw const FormatException('enum 必须是非空数组');
      }
      if (s.containsKey('uniqueItems') && s['uniqueItems'] is! bool) {
        throw const FormatException('uniqueItems 必须是布尔值');
      }
      if (s.containsKey('pattern')) {
        if (s['pattern'] is! String) {
          throw const FormatException('pattern 必须是字符串');
        }
        RegExp(s['pattern'] as String, unicode: true);
      }
      if (s.containsKey(r'$ref')) {
        final ref = s[r'$ref'];
        if (ref is! String || !(ref == '#' || ref.startsWith('#/'))) {
          throw const FormatException('离线 Schema 仅支持 # 或 #/ 开头的本地引用');
        }
        final target = JsonWorkbench.select(
          schema,
          ref == '#' ? '' : ref.substring(1),
        );
        check(target, ref, depth + 1);
      }
    }

    List<String> evaluate(Object? v, Object? s, String path, int depth) {
      if (depth > 128 || ++evaluationCount > 20000) {
        throw const FormatException('Schema 引用循环、过深或校验复杂度超过上限');
      }
      if (s == true) return [];
      if (s == false) return ['$path：该 Schema 禁止此值'];
      final map = s as Map<String, Object?>;
      final issues = <String>[];
      void issue(String text) =>
          issues.add('${path.isEmpty ? '/' : path}：$text');
      if (map.containsKey(r'$ref')) {
        final ref = map[r'$ref'] as String;
        issues.addAll(
          evaluate(
            v,
            JsonWorkbench.select(schema, ref == '#' ? '' : ref.substring(1)),
            path,
            depth + 1,
          ),
        );
      }
      if (map.containsKey('type')) {
        final types = map['type'] is List ? map['type'] as List : [map['type']];
        final type = JsonWorkbench.typeOf(v);
        final integer = v is num && v % 1 == 0;
        if (!types.contains(type) &&
            !(types.contains('number') && v is num) &&
            !(types.contains('integer') && integer)) {
          issue('需要类型 ${types.join(' / ')}，实际 $type');
        }
      }
      if (map.containsKey('enum') &&
          !(map['enum'] as List).any((x) => JsonWorkbench.equal(v, x))) {
        issue('不在 enum 中');
      }
      if (map.containsKey('const') && !JsonWorkbench.equal(v, map['const'])) {
        issue('不等于 const');
      }
      if (v is Map<String, Object?>) {
        for (final key in (map['required'] as List? ?? const [])) {
          if (!v.containsKey(key)) issue('缺少必填字段 $key');
        }
        final props = map['properties'] as Map<String, Object?>? ?? const {};
        for (final e in v.entries) {
          final child = '$path/${JsonWorkbench.escapeToken(e.key)}';
          if (props.containsKey(e.key)) {
            issues.addAll(evaluate(e.value, props[e.key], child, depth + 1));
          } else if (map.containsKey('additionalProperties')) {
            issues.addAll(
              evaluate(e.value, map['additionalProperties'], child, depth + 1),
            );
          }
        }
        if (map['minProperties'] is num &&
            v.length < (map['minProperties'] as num)) {
          issue('属性数量不足');
        }
        if (map['maxProperties'] is num &&
            v.length > (map['maxProperties'] as num)) {
          issue('属性数量过多');
        }
      }
      if (v is List) {
        final prefix = map['prefixItems'] as List? ?? const [];
        for (var i = 0; i < v.length; i++) {
          if (i < prefix.length) {
            issues.addAll(evaluate(v[i], prefix[i], '$path/$i', depth + 1));
          } else if (map.containsKey('items')) {
            issues.addAll(evaluate(v[i], map['items'], '$path/$i', depth + 1));
          }
        }
        if (map['minItems'] is num && v.length < (map['minItems'] as num)) {
          issue('数组长度不足');
        }
        if (map['maxItems'] is num && v.length > (map['maxItems'] as num)) {
          issue('数组长度过大');
        }
        if (map['uniqueItems'] == true) {
          final seen = <String>{};
          for (final item in v) {
            // Object key order is irrelevant; normalize integral doubles as well.
            if (!seen.add(_canonical(item))) {
              issue('数组含有重复项');
              break;
            }
          }
        }
      }
      if (v is String) {
        final length = v.runes.length;
        if (map['minLength'] is num && length < (map['minLength'] as num)) {
          issue('字符串过短');
        }
        if (map['maxLength'] is num && length > (map['maxLength'] as num)) {
          issue('字符串过长');
        }
        if (map['pattern'] is String &&
            !RegExp(map['pattern'] as String, unicode: true).hasMatch(v)) {
          issue('不匹配 pattern');
        }
      }
      if (v is num) {
        for (final key in const [
          'minimum',
          'maximum',
          'exclusiveMinimum',
          'exclusiveMaximum',
        ]) {
          final bound = map[key];
          if (bound is! num) continue;
          final valid = switch (key) {
            'minimum' => v >= bound,
            'maximum' => v <= bound,
            'exclusiveMinimum' => v > bound,
            _ => v < bound,
          };
          if (!valid) issue('不满足 $key = $bound');
        }
        if (map['multipleOf'] is num) {
          if (!_multipleOf(v, map['multipleOf'] as num)) {
            issue('不满足 multipleOf');
          }
        }
      }
      for (final key in const ['allOf', 'anyOf', 'oneOf']) {
        if (map[key] is! List) continue;
        final options = map[key] as List;
        final matches = options
            .where((s) => evaluate(v, s, path, depth + 1).isEmpty)
            .length;
        if ((key == 'allOf' && matches != options.length) ||
            (key == 'anyOf' && matches == 0) ||
            (key == 'oneOf' && matches != 1)) {
          issue('不满足 $key');
        }
      }
      if (map.containsKey('not') &&
          evaluate(v, map['not'], path, depth + 1).isEmpty) {
        issue('命中 not 禁止的规则');
      }
      return issues;
    }

    try {
      check(schema, '#', 0);
      errors.addAll(evaluate(value, schema, '', 0));
    } on FormatException catch (e) {
      errors.add('Schema 错误：${e.message}');
    }
    return errors;
  }

  static String _canonical(Object? value) {
    if (value is num && value.isFinite && value % 1 == 0) {
      // BigInt preserves the represented integer even outside int64. toInt()
      // saturates there and would make unrelated large doubles look equal.
      return 'number:${BigInt.from(value)}';
    }
    if (value is num) return 'number:${JsonWorkbench.pretty(value)}';
    if (value is Map<String, Object?>) {
      final keys = value.keys.toList()..sort();
      return 'object:{${keys.map((k) => '${JsonWorkbench.pretty(k)}:${_canonical(value[k])}').join(',')}}';
    }
    if (value is List) return 'array:[${value.map(_canonical).join(',')}]';
    return 'value:${JsonWorkbench.pretty(value)}';
  }

  static bool _multipleOf(num value, num divisor) {
    if (value is int && divisor is int) return value.remainder(divisor) == 0;
    // Compare decimal values without a double quotient or an epsilon that
    // would silently permit nonmultiples. This also handles exponent notation.
    (BigInt coefficient, int scale) decimal(num number) {
      final parts = number.toString().toLowerCase().split('e');
      final fraction = parts.first.split('.');
      final digits = fraction.first + (fraction.length == 2 ? fraction[1] : '');
      final scale =
          (fraction.length == 2 ? fraction[1].length : 0) -
          (parts.length == 2 ? int.parse(parts[1]) : 0);
      return (BigInt.parse(digits), scale);
    }

    final (left, leftScale) = decimal(value);
    final (right, rightScale) = decimal(divisor);
    final difference = rightScale - leftScale;
    final ten = BigInt.from(10);
    return difference >= 0
        ? (left * ten.pow(difference)).remainder(right) == BigInt.zero
        : left.remainder(right * ten.pow(-difference)) == BigInt.zero;
  }
}
