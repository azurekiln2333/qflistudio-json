import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_json/json/json_verification_report.dart';

void main() {
  late Directory root;
  late File report;
  setUp(() async {
    root = await Directory.systemTemp.createTemp('json_verification_report_');
    report = File(p.join(root.path, 'json_verification_result.json'));
    await report.writeAsString('{"passed":true,"runId":"old-success"}');
  });
  tearDown(() async {
    await root.delete(recursive: true);
  });

  test(
    'a throwing audit replaces old success with its current failure',
    () async {
      String? pendingRun;
      final result = await runJsonVerificationReport(
        storageDirectory: () async => root.path,
        verify: (path) async {
          expect(path, root.path);
          final pending = jsonDecode(await report.readAsString()) as Map;
          expect(pending['passed'], isFalse);
          expect(pending['status'], 'running');
          expect(pending['runId'], isNot('old-success'));
          pendingRun = pending['runId'] as String;
          throw StateError('catalog load failed');
        },
      );
      expect(result['passed'], isFalse);
      expect(result['status'], 'failed');
      expect(result['error'], contains('catalog load failed'));
      expect(result['runId'], pendingRun);
      expect(result['startedUtc'], isA<String>());
      expect(result['finishedUtc'], isA<String>());
      expect(jsonDecode(await report.readAsString()), result);
    },
  );

  test('success is persisted with a distinct identity for each run', () async {
    Future<Map<String, Object?>> run() => runJsonVerificationReport(
      storageDirectory: () async => root.path,
      verify: (_) async => {'passed': true, 'runnerPasses': 340},
    );
    final first = await run();
    final second = await run();
    expect(first['passed'], isTrue);
    expect(second['passed'], isTrue);
    expect(second['status'], 'passed');
    expect(second['runnerPasses'], 340);
    expect(second['runId'], isNot(first['runId']));
    expect(jsonDecode(await report.readAsString()), second);
  });

  test(
    'an unwritable report prevents audit execution and returns failure',
    () async {
      await report.delete();
      await Directory(report.path).create();
      var ran = false;
      final result = await runJsonVerificationReport(
        storageDirectory: () async => root.path,
        verify: (_) async {
          ran = true;
          return {'passed': true};
        },
      );
      expect(ran, isFalse);
      expect(result['passed'], isFalse);
      expect(result['status'], 'failed');
      expect(result['error'], contains('无法写入本次验证报告'));
      expect(result['runId'], isNot('old-success'));
    },
  );

  test('a failed final export cannot return a successful audit', () async {
    final result = await runJsonVerificationReport(
      storageDirectory: () async => root.path,
      verify: (_) async {
        await report.delete();
        await Directory(report.path).create();
        return {'passed': true};
      },
    );
    expect(result['passed'], isFalse);
    expect(result['status'], 'failed');
    expect(result['error'], contains('无法写入本次验证报告'));
  });

  test(
    'a failed staged write leaves the current running marker failed',
    () async {
      String? currentRun;
      final result = await runJsonVerificationReport(
        storageDirectory: () async => root.path,
        verify: (_) async {
          final pending = jsonDecode(await report.readAsString()) as Map;
          currentRun = pending['runId'] as String;
          await Directory('${report.path}.$currentRun.tmp').create();
          return {'passed': true};
        },
      );
      expect(result['passed'], isFalse);
      expect(result['runId'], currentRun);
      final persisted = jsonDecode(await report.readAsString()) as Map;
      expect(persisted['runId'], currentRun);
      expect(persisted['passed'], isFalse);
      expect(persisted['status'], 'running');
    },
  );

  test('missing storage still produces a fresh failure identity', () async {
    var ran = false;
    final result = await runJsonVerificationReport(
      storageDirectory: () async => null,
      verify: (_) async {
        ran = true;
        return {'passed': true};
      },
    );
    expect(ran, isFalse);
    expect(result['passed'], isFalse);
    expect(result['error'], contains('找不到应用可写沙盒'));
    expect(result['runId'], isNot('old-success'));
  });
}
