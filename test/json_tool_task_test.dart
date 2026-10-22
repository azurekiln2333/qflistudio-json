import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_json/json/json_tools.dart';
import 'package:qfli_json/json/json_workbench.dart';

void main() {
  test(
    'all tool defaults complete in a worker with identical results',
    () async {
      for (final operation in JsonOperation.values) {
        expect(
          await JsonOperationTask(
            operation,
            operation.initialSource,
            operation.initialSecond,
          ).result,
          operation.execute(operation.initialSource, operation.initialSecond),
          reason: operation.name,
        );
      }
    },
  );

  test('worker returns a precise validation error', () async {
    await expectLater(
      JsonOperationTask(JsonOperation.format, '{"a" true}').result,
      throwsA(
        isA<FormatException>().having(
          (e) => e.message,
          'message',
          contains('缺少冒号'),
        ),
      ),
    );
  });

  test(
    'a pathological pattern times out without blocking the caller',
    () async {
      final task = JsonOperationTask(
        JsonOperation.schema,
        jsonEncode('${'a' * 100}!'),
        r'{"pattern":"^(a+)+$"}',
        const Duration(milliseconds: 200),
      );
      await expectLater(
        task.result,
        throwsA(
          isA<FormatException>().having(
            (e) => e.message,
            'message',
            contains('超时'),
          ),
        ),
      );
      expect(
        await JsonOperationTask(JsonOperation.minify, '{ "ok": true }').result,
        '{"ok":true}',
      );
    },
  );

  test('cancellation also works before worker creation completes', () async {
    final task = JsonOperationTask(JsonOperation.format, '{}');
    final result = expectLater(
      task.result,
      throwsA(
        isA<FormatException>().having(
          (e) => e.message,
          'message',
          contains('取消'),
        ),
      ),
    );
    task.cancel();
    task.cancel();
    await result;
  });

  test('raw text escaping follows the same input limit as JSON tools', () {
    expect(
      () =>
          JsonOperation.quote.execute('a' * (JsonWorkbench.maximumLength + 1)),
      throwsFormatException,
    );
  });
}
