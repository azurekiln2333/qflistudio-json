import 'dart:convert';
import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_json/json/json_schema.dart';
import 'package:qfli_json/json/json_tools.dart';
import 'package:qfli_json/json/json_workbench.dart';

void main() {
  group('strict JSON diagnostics', () {
    for (final source in [
      'null',
      'false',
      'true',
      '0',
      '-0',
      '1.25e-4',
      r'"\"\\\/\b\f\n\r\t\u4f60"',
      '{"a":[1,true,null,{"b":"你好"}]}',
      ' \r\n\t {"":"","😀":[]} \r\n',
    ]) {
      test('accepts $source and agrees with Dart JSON decoder', () {
        final result = JsonWorkbench.inspect(source);
        expect(result.problems, isEmpty);
        expect(result.value, jsonDecode(source));
        expect(jsonDecode(result.formatted), jsonDecode(source));
        expect(result.nodes.first.pointer, '');
        for (final node in result.nodes) {
          expect(
            jsonDecode(source.substring(node.offset, node.end)),
            node.value,
          );
          expect(JsonWorkbench.select(result.value, node.pointer), node.value);
        }
      });
    }
    for (final source in [
      '',
      ' ',
      '[1,]',
      '{"a":1,}',
      '{a:1}',
      "{'a':1}",
      '[01]',
      '+1',
      '.1',
      '1.',
      '1e',
      '[NaN]',
      '[Infinity]',
      '1e999',
      'true false',
      'nullx',
      '{"a" 1}',
      '[1 2]',
      '[',
      '{',
      '"unterminated',
      '"line\nbreak"',
      r'"\q"',
      r'"\uGGGG"',
      '{"a":1,"a":2}',
      '{"a":1,"\\u0061":2}',
    ]) {
      test('rejects $source', () {
        final result = JsonWorkbench.inspect(source);
        expect(result.valid, isFalse);
        expect(
          result.problems.single.offset,
          inInclusiveRange(0, source.length),
        );
        expect(result.problems.single.line, greaterThanOrEqualTo(1));
        expect(result.problems.single.column, greaterThanOrEqualTo(1));
      });
    }
    test('diagnostic is at exact second-line colon omission', () {
      final problem = JsonWorkbench.inspect(
        '{\r\n  "name" true\r\n}',
      ).problems.single;
      expect(problem.line, 2);
      expect(problem.column, 10);
      expect(problem.offset, 12);
    });
    test('integer formatting preserves int64 and rejects lossy overflow', () {
      for (final literal in [
        '9007199254740993',
        '9223372036854775807',
        '-9223372036854775808',
      ]) {
        final result = JsonWorkbench.inspect('{"id":$literal}');
        expect(result.problems, isEmpty, reason: literal);
        expect((result.value as Map)['id'], int.parse(literal));
        expect(result.formatted, contains('"id": $literal'));
      }
      for (final literal in [
        '9223372036854775808',
        '9223372036854775809',
        '-9223372036854775809',
        '123456789012345678901234567890',
      ]) {
        final result = JsonWorkbench.inspect('{"id":$literal}');
        expect(result.valid, isFalse, reason: literal);
        expect(result.problems.single.message, contains('64 位'));
        expect(result.problems.single.offset, 6);
      }
    });
    test('depth, source size and node limits are actionable', () {
      expect(
        JsonWorkbench.inspect(
          '${'[' * 130}0${']' * 130}',
        ).problems.single.message,
        contains('128'),
      );
      expect(
        JsonWorkbench.inspect(
          ' ' * (JsonWorkbench.maximumLength + 1),
        ).problems.single.message,
        contains('2 MiB'),
      );
      expect(
        JsonWorkbench.inspect(
          '[${List.filled(50001, '0').join(',')}]',
        ).problems.single.message,
        contains('50000'),
      );
    });
  });

  group('RFC 6901 JSON Pointer', () {
    final source = {
      'foo': ['bar', 'baz'],
      '': 0,
      'a/b': 1,
      'c%d': 2,
      'e^f': 3,
      'g|h': 4,
      'i\\j': 5,
      'k"l': 6,
      ' ': 7,
      'm~n': 8,
      'nil': null,
    };
    final pointers = {
      '/foo/0': 'bar',
      '/': 0,
      '/a~1b': 1,
      '/c%d': 2,
      '/e^f': 3,
      '/g|h': 4,
      '/i\\j': 5,
      '/k"l': 6,
      '/ ': 7,
      '/m~0n': 8,
      '/nil': null,
    };
    for (final e in pointers.entries) {
      test(e.key, () => expect(JsonWorkbench.select(source, e.key), e.value));
    }
    test('root and null are real values; missing and invalid indexes fail', () {
      expect(JsonWorkbench.select(source, ''), source);
      for (final path in [
        '/absent',
        '/foo/01',
        '/foo/-',
        '/foo/-1',
        '/foo/2',
        '/foo/999999999999999999999',
        '/~2',
        '#/foo',
        'foo',
      ]) {
        expect(
          () => JsonWorkbench.select(source, path),
          throwsFormatException,
          reason: path,
        );
      }
    });
  });

  group('patch, diff, lossless paths', () {
    test('RFC 7396 published example', () {
      expect(
        JsonWorkbench.mergePatch(
          {
            'title': 'Goodbye!',
            'author': {'givenName': 'John', 'familyName': 'Doe'},
            'tags': ['example', 'sample'],
            'content': 'This will be unchanged',
          },
          {
            'title': 'Hello!',
            'phoneNumber': '+01-123-456-7890',
            'author': {'familyName': null},
            'tags': ['example'],
          },
        ),
        {
          'title': 'Hello!',
          'author': {'givenName': 'John'},
          'tags': ['example'],
          'content': 'This will be unchanged',
          'phoneNumber': '+01-123-456-7890',
        },
      );
      expect(JsonWorkbench.mergePatch({'a': 1}, null), null);
      expect(JsonWorkbench.mergePatch([1], {'b': 2}), {'b': 2});
    });
    test('all six RFC 6902 operations and array order after move', () {
      final original = JsonWorkbench.decode(
        '{"foo":["all","grass","cows","eat"],"a/b":null}',
      );
      final result = JsonWorkbench.applyPatch(original, [
        {'op': 'test', 'path': '/a~1b', 'value': null},
        {'op': 'move', 'from': '/foo/1', 'path': '/foo/3'},
        {'op': 'copy', 'from': '/foo/0', 'path': '/copied'},
        {'op': 'add', 'path': '/foo/-', 'value': '!'},
        {'op': 'replace', 'path': '/copied', 'value': true},
        {'op': 'remove', 'path': '/a~1b'},
      ]);
      expect(result, {
        'foo': ['all', 'cows', 'eat', 'grass', '!'],
        'copied': true,
      });
      expect((original as Map)['foo'], ['all', 'grass', 'cows', 'eat']);
    });
    test('failed patch cannot mutate input; parents must exist', () {
      final original = JsonWorkbench.decode('{"a":[1,2]}');
      expect(
        () => JsonWorkbench.applyPatch(original, [
          {'op': 'replace', 'path': '/a/0', 'value': 5},
          {'op': 'test', 'path': '/a/1', 'value': 3},
        ]),
        throwsFormatException,
      );
      expect(original, {
        'a': [1, 2],
      });
      for (final operation in [
        {'op': 'add', 'path': '/missing/x', 'value': 1},
        {'op': 'replace', 'path': '/missing', 'value': 1},
        {'op': 'move', 'from': '/a', 'path': '/a/0/child'},
        {'op': 'add', 'path': '/a/00', 'value': 1},
        {'op': 'remove', 'path': '/missing'},
        {'op': 'add', 'path': '/x'},
        {'op': 'unknown', 'path': ''},
      ]) {
        expect(
          () => JsonWorkbench.applyPatch(original, [operation]),
          throwsFormatException,
        );
      }
    });
    test('randomized round trips cover all scalar/container shapes', () {
      final random = Random(17);
      Object? value(int depth) {
        if (depth > 3) {
          return [null, true, 'x/~/😀', random.nextInt(100), 1.5][random
              .nextInt(5)];
        }
        return switch (random.nextInt(4)) {
          0 => {'0': value(depth + 1), 'a/b': value(depth + 1), '~': []},
          1 => List.generate(random.nextInt(5), (_) => value(depth + 1)),
          2 => <String, Object?>{},
          _ => value(4),
        };
      }

      for (var i = 0; i < 100; i++) {
        final a = value(0), b = value(0);
        expect(JsonWorkbench.inspect(jsonEncode(a)).value, a);
        expect(JsonWorkbench.unflatten(JsonWorkbench.flatten(a)), a);
        expect(JsonWorkbench.applyPatch(a, JsonWorkbench.diff(a, b)), b);
      }
    });
    test('paths preserve empty roots, nulls and numeric object keys', () {
      for (final v in [
        null,
        [],
        {},
        {
          '0': {},
          'x': [
            null,
            [],
            {'~a/b': 3},
          ],
        },
      ]) {
        expect(JsonWorkbench.unflatten(JsonWorkbench.flatten(v)), v);
      }
      expect(
        () => JsonWorkbench.unflatten({
          'containers': {'': 'array'},
          'values': {'/2': 1},
        }),
        throwsFormatException,
      );
    });
  });

  group('local Schema subset', () {
    test('nested constraints and local refs report pointer paths', () {
      final schema = JsonWorkbench.decode(
        r'{"type":"object","required":["name","items"],"additionalProperties":false,"properties":{"name":{"type":"string","minLength":2},"items":{"type":"array","items":{"$ref":"#/$defs/item"}}},"$defs":{"item":{"type":"integer","minimum":1}}}',
      );
      expect(
        LocalJsonSchema.validate({
          'name': 'Ada',
          'items': [1, 2],
        }, schema),
        isEmpty,
      );
      final errors = LocalJsonSchema.validate({
        'name': 'A',
        'items': [0, 'a'],
        'extra': null,
      }, schema);
      expect(errors.join('\n'), contains('/items/0'));
      expect(errors.join('\n'), contains('/items/1'));
      expect(errors.join('\n'), contains('/extra'));
      expect(errors.join('\n'), contains('/name'));
    });
    test(
      'integer accepts 1.0, Unicode length and unordered duplicate objects',
      () {
        expect(LocalJsonSchema.validate(1.0, {'type': 'integer'}), isEmpty);
        expect(LocalJsonSchema.validate('😀', {'maxLength': 1}), isEmpty);
        expect(
          LocalJsonSchema.validate(
            [
              {'a': 1, 'b': 2},
              {'b': 2.0, 'a': 1.0},
            ],
            {'uniqueItems': true},
          ),
          isNotEmpty,
        );
        expect(LocalJsonSchema.validate(0.3, {'multipleOf': 0.1}), isEmpty);
        expect(LocalJsonSchema.validate(0.31, {'multipleOf': 0.1}), isNotEmpty);
      },
    );
    test('combinators and prefixItems use declared semantics', () {
      expect(
        LocalJsonSchema.validate(
          [1, 'x'],
          {
            'prefixItems': [
              {'type': 'integer'},
            ],
            'items': {'type': 'string'},
          },
        ),
        isEmpty,
      );
      expect(
        LocalJsonSchema.validate(1, {
          'oneOf': [
            {'type': 'integer'},
            {'type': 'number'},
          ],
        }),
        isNotEmpty,
      );
      expect(
        LocalJsonSchema.validate(null, {
          'not': {'type': 'string'},
          'anyOf': [
            {'type': 'null'},
            false,
          ],
        }),
        isEmpty,
      );
      expect(
        LocalJsonSchema.validate(3, {
          'allOf': [
            {'minimum': 2},
            {'maximum': 5},
          ],
        }),
        isEmpty,
      );
    });
    test(
      'multipleOf does not round large odd integers or permit near misses',
      () {
        for (final divisor in [2, 2.0]) {
          expect(
            LocalJsonSchema.validate(9007199254740993, {'multipleOf': divisor}),
            isNotEmpty,
          );
          expect(
            LocalJsonSchema.validate(9007199254740992, {'multipleOf': divisor}),
            isEmpty,
          );
        }
        for (final value in [1.00000000001, 0.30000000000000004]) {
          expect(
            LocalJsonSchema.validate(value, {'multipleOf': 0.1}),
            isNotEmpty,
          );
        }
        expect(LocalJsonSchema.validate(0.3, {'multipleOf': 0.1}), isEmpty);
        expect(LocalJsonSchema.validate(-0.3, {'multipleOf': 0.1}), isEmpty);
        expect(LocalJsonSchema.validate(3e-9, {'multipleOf': 1e-9}), isEmpty);
        expect(
          LocalJsonSchema.validate(9007199254740993, {'multipleOf': 0.5}),
          isEmpty,
        );
        expect(
          LocalJsonSchema.validate(9007199254740993, {'multipleOf': 0.2}),
          isEmpty,
        );
        expect(
          LocalJsonSchema.validate(9007199254740993, {'multipleOf': 0.3}),
          isEmpty,
        );
      },
    );
    test('uniqueItems does not saturate large integral doubles into int64', () {
      expect(
        LocalJsonSchema.validate(
          [9223372036854775808.0, 10000000000000000000.0],
          {'uniqueItems': true},
        ),
        isEmpty,
      );
      expect(
        LocalJsonSchema.validate(
          [-9223372036854775808.0, -10000000000000000000.0],
          {'uniqueItems': true},
        ),
        isEmpty,
      );
      expect(
        LocalJsonSchema.validate(
          [9223372036854775808.0, 9223372036854775808.0],
          {'uniqueItems': true},
        ),
        isNotEmpty,
      );
      expect(
        LocalJsonSchema.validate([1, 1.0], {'uniqueItems': true}),
        isNotEmpty,
      );
      expect(
        LocalJsonSchema.validate([1, '1'], {'uniqueItems': true}),
        isEmpty,
      );
      expect(
        LocalJsonSchema.validate(
          [
            {'x': 1},
            {'x': 1.0},
          ],
          {'uniqueItems': true},
        ),
        isNotEmpty,
      );
    });
    test(
      'metadata types and unsupported dialect/scoping are explicit errors',
      () {
        for (final schema in [
          {r'$schema': 123},
          {r'$id': true},
          {r'$comment': null},
          {'title': <Object?>[]},
          {'description': <String, Object?>{}},
          {'examples': 'not-an-array'},
          {r'$schema': 'http://json-schema.org/draft-07/schema#'},
          {
            'properties': {
              'x': {r'$id': 'nested-resource', r'$ref': '#'},
            },
          },
          {'multipleOf': double.infinity},
          {'minimum': double.nan},
        ]) {
          expect(
            LocalJsonSchema.validate(1, schema),
            isNotEmpty,
            reason: '$schema',
          );
        }
        expect(
          LocalJsonSchema.validate('note', {
            r'$schema': 'https://json-schema.org/draft/2020-12/schema',
            r'$id': 'urn:qfli:local-example',
            r'$comment': 'Never fetched',
            'title': 'Local title',
            'description': 'Local subset',
            'examples': ['note'],
            'type': 'string',
          }),
          isEmpty,
        );
      },
    );
    test('unsupported/remote/malformed schemas never silently pass', () {
      for (final schema in [
        {r'$ref': 'https://example.invalid/schema.json'},
        {'format': 'email'},
        {'if': true},
        {'required': 'name'},
        {'type': 'Date'},
        {'type': []},
        {'minimum': '0'},
        {'pattern': '['},
        {'items': []},
        {'enum': []},
        {'minLength': -1},
        {
          'required': ['a', 'a'],
        },
        {r'$ref': '#/missing'},
        {r'$ref': '#'},
      ]) {
        expect(
          LocalJsonSchema.validate(1, schema),
          isNotEmpty,
          reason: '$schema',
        );
      }
    });
  });
  test('line-oriented and CSV conversions preserve embedded escapes', () {
    final rows = [
      {'name': 'Ada, "A"', 'text': 'a\nb'},
      {'name': '林', 'ok': true},
    ];
    expect(JsonWorkbench.fromJsonLines(JsonWorkbench.toJsonLines(rows)), rows);
    expect(
      JsonWorkbench.toCsv(rows),
      'name,text,ok\r\n"Ada, ""A""","a\nb",\r\n林,,true',
    );
    expect(
      () => JsonWorkbench.fromJsonLines('{"a":1}\n\nno'),
      throwsA(
        isA<FormatException>().having(
          (e) => e.message,
          'line',
          contains('第 3 行'),
        ),
      ),
    );
  });
  group('transformation resource limits', () {
    test('inspection bounds repeated long JSON Pointer paths', () {
      final source = jsonEncode({'k' * 20000: List.filled(300, 0)});
      expect(source.length, lessThan(JsonWorkbench.maximumLength));
      final inspection = JsonWorkbench.inspect(source);
      expect(inspection.valid, isFalse);
      expect(inspection.nodes, isEmpty);
      expect(inspection.problems.single.message, contains('结构路径累计超过 4 Mi'));
      expect(() => JsonWorkbench.decode(source), throwsFormatException);

      final ordinary = JsonWorkbench.inspect('{"a/b":{"~key":[0,1]}}');
      expect(ordinary.valid, isTrue);
      expect(ordinary.nodes.map((node) => node.pointer), [
        '',
        '/a~1b',
        '/a~1b/~0key',
        '/a~1b/~0key/0',
        '/a~1b/~0key/1',
      ]);
    });
    test('CSV bounds the row-column product before expanding sparse rows', () {
      final sparseRows = List.generate(
        500,
        (i) => <String, Object?>{'field$i': i},
      );
      expect(
        () => JsonWorkbench.toCsv(sparseRows),
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'limit',
            contains('200000'),
          ),
        ),
      );
      expect(
        JsonWorkbench.toCsv([
          {'name': 'local', 'value': 1},
        ]),
        'name,value\r\nlocal,1',
      );
    });
    test('CSV bounds its escaped output while streaming cells', () {
      final quotes = '"' * (JsonWorkbench.maximumOutputLength ~/ 3 + 1000);
      expect(
        () => JsonWorkbench.toCsv([
          {
            'cell': {'value': quotes},
          },
        ]),
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'limit',
            contains('CSV 输出'),
          ),
        ),
      );
    });
    test('copy growth and excess depth fail without changing the original', () {
      final original = <String, Object?>{'text': 'x' * 1024};
      expect(
        () => JsonWorkbench.applyPatch(
          original,
          List.generate(
            12,
            (i) => {'op': 'copy', 'from': '', 'path': '/clone$i'},
          ),
        ),
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'limit',
            contains('4 Mi'),
          ),
        ),
      );
      expect(original, {'text': 'x' * 1024});
      expect(
        () => JsonWorkbench.applyPatch(
          original,
          List.generate(
            130,
            (_) => {'op': 'copy', 'from': '', 'path': '/clone'},
          ),
        ),
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'limit',
            contains('128'),
          ),
        ),
      );
      expect(original, {'text': 'x' * 1024});
      expect(
        JsonWorkbench.applyPatch(original, [
          {'op': 'move', 'from': '', 'path': ''},
        ]),
        original,
      );
    });
    test(
      'patch charges cumulative work even for successful read-only tests',
      () {
        final original = List.filled(200, 0);
        expect(
          () => JsonWorkbench.applyPatch(
            original,
            List.generate(
              2000,
              (_) => {'op': 'test', 'path': '/0', 'value': 0},
            ),
          ),
          throwsA(
            isA<FormatException>().having(
              (e) => e.message,
              'limit',
              contains('累计处理'),
            ),
          ),
        );
        expect(original, everyElement(0));
      },
    );
    test('JSON Lines caps the entire input and converted node count', () {
      expect(
        () => JsonWorkbench.fromJsonLines(
          ' ' * (JsonWorkbench.maximumLength + 1),
        ),
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'limit',
            contains('整体输入'),
          ),
        ),
      );
      expect(
        () => JsonWorkbench.fromJsonLines(List.filled(50000, '0').join('\n')),
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'limit',
            contains('整体节点'),
          ),
        ),
      );
      expect(JsonWorkbench.fromJsonLines('0\nfalse\nnull'), [0, false, null]);
    });
    test(
      'flatten rejects repeated long paths before allocating the full manifest',
      () {
        expect(
          () => JsonWorkbench.flatten({'k' * 200000: List.filled(25, 0)}),
          throwsA(
            isA<FormatException>().having(
              (e) => e.message,
              'limit',
              contains('路径展开结果'),
            ),
          ),
        );
        final ordinary = <String, Object?>{
          'a/b': [null, 1],
        };
        expect(
          JsonWorkbench.unflatten(JsonWorkbench.flatten(ordinary)),
          ordinary,
        );
      },
    );
    test('pretty output bounds direct callers as well as parsed sources', () {
      expect(
        () => JsonWorkbench.pretty('x' * JsonWorkbench.maximumOutputLength),
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'limit',
            contains('4 Mi'),
          ),
        ),
      );
    });
  });
  test('every direct tool has a working initial example', () {
    for (final operation in JsonOperation.values) {
      expect(
        operation.execute(operation.initialSource, operation.initialSecond),
        isNotEmpty,
        reason: operation.title,
      );
    }
  });
}
