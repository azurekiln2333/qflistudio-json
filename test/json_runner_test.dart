import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_json/json/json_runner.dart';
import 'package:qfli_studio_core/terminal/shell/sandbox_shell_backend.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory project;
  setUp(() {
    project = Directory.systemTemp.createTempSync('json_runner_');
  });
  tearDown(() async {
    await project.delete(recursive: true);
  });
  Future<File> write(String name, String source) =>
      File(p.join(project.path, name)).writeAsString(source);
  test(
    'valid JSON runs through the product runner and prints real formatted output',
    () async {
      final file = await write('data.json', '{"a":[true,null]}');
      final result = (await const JsonRunner().run(
        projectPath: project.path,
        entryFile: file.path,
      ))!;
      expect(await result.exitCode, 0);
      expect(
        await result.stdout.join('\n'),
        '{\n  "a": [\n    true,\n    null\n  ]\n}',
      );
      expect(await result.stderr.toList(), isEmpty);
    },
  );
  test(
    'invalid data fails with exact diagnostic; missing file is not-run status',
    () async {
      final file = await write('data.json', '{\n"a" true}');
      final result = (await const JsonRunner().run(
        projectPath: project.path,
        entryFile: file.path,
      ))!;
      expect(await result.exitCode, 1);
      expect(await result.stdout.toList(), isEmpty);
      expect(await result.stderr.join(), contains('第 2 行'));
      final missing = (await const JsonRunner().run(
        projectPath: project.path,
        entryFile: p.join(project.path, 'absent.json'),
      ))!;
      expect(await missing.exitCode, 127);
      expect(
        await const JsonRunner().run(
          projectPath: project.path,
          entryFile: 'other.py',
        ),
        isNull,
      );
    },
  );
  test('terminal parses quoted paths and never overwrites the input', () async {
    final file = await write('my data.json', '{"a/b":[null,2]}');
    final backend = SandboxShellBackend(
      sandboxRoot: project.path,
      delegate: jsonTerminalCommand,
    );
    final chunks = <String>[];
    final subscription = backend.output.listen((c) => chunks.add(c.text));
    await backend.execute('json get "my data.json" /a~1b/0');
    expect(backend.lastExitCode, 0);
    expect(chunks.join(), contains('null'));
    chunks.clear();
    await backend.execute('json get "my data.json" /missing');
    expect(backend.lastExitCode, 1);
    expect(chunks.join(), contains('路径不存在'));
    await backend.execute('json format "my data.json"');
    expect(await file.readAsString(), '{"a/b":[null,2]}');
    chunks.clear();
    await backend.execute('json check ../outside.json');
    expect(backend.lastExitCode, 1);
    expect(chunks.join(), contains('不能越出沙盒'));
    await subscription.cancel();
    await backend.shutdown();
  });
  test(
    'valid UTF-8 with excessive formatted output reports the output limit',
    () async {
      final source =
          '${'[' * 100}[${List.filled(15000, '"${'x' * 100}"').join(',')}]${']' * 100}';
      final file = await write('data.json', source);
      final result = (await const JsonRunner().run(
        projectPath: project.path,
        entryFile: file.path,
      ))!;
      expect(await result.exitCode, 1);
      final error = await result.stderr.join();
      expect(error, contains('结果超过'));
      expect(error, isNot(contains('有效 UTF-8')));
      expect(await result.stdout.toList(), isEmpty);
      expect(await file.readAsString(), source);
    },
  );
  test(
    'oversized and non-UTF8 inputs fail without successful output',
    () async {
      final file = await write('data.json', ' ' * (2 * 1024 * 1024 + 1));
      expect(
        await (await const JsonRunner().run(
          projectPath: project.path,
          entryFile: file.path,
        ))!.exitCode,
        1,
      );
      await file.writeAsBytes([0xff, 0xfe]);
      expect(
        await (await const JsonRunner().run(
          projectPath: project.path,
          entryFile: file.path,
        ))!.exitCode,
        1,
      );
    },
  );
}
