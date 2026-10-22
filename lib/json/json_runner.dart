import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/terminal/shell/command_parser.dart';
import 'package:qfli_studio_core/terminal/shell/sandbox_shell_backend.dart';

import 'json_workbench.dart';

class JsonRunner implements ProgramRunner {
  const JsonRunner();
  @override
  Future<ProgramRunResult?> run({
    required String projectPath,
    required String entryFile,
  }) async {
    if (p.extension(entryFile).toLowerCase() != '.json') return null;
    try {
      final root = await Directory(projectPath).resolveSymbolicLinks();
      final file = File(entryFile);
      final resolved = await file.resolveSymbolicLinks();
      if (!p.isWithin(root, resolved)) {
        return _result('JSON 校验', '', '文件不在当前项目内', kProgramNotRunExitCode);
      }
      if (await file.length() > JsonWorkbench.maximumLength) {
        return _result('JSON 校验', '', '文件超过 2 MiB 校验上限', 1);
      }
      final String source;
      try {
        source = utf8.decode(await file.readAsBytes());
      } on FormatException catch (e) {
        return _result('JSON 校验', '', '文件不是有效 UTF-8：${e.message}', 1);
      }
      final inspection = await compute(JsonWorkbench.inspect, source);
      return inspection.valid
          ? _result('JSON 校验与预览', inspection.formatted, '', 0)
          : _result('JSON 校验', '', inspection.problems.join('\n'), 1);
    } on FileSystemException catch (e) {
      return _result(
        'JSON 校验',
        '',
        '无法读取文件：${e.message}',
        kProgramNotRunExitCode,
      );
    } on FormatException catch (e) {
      return _result('JSON 校验', '', e.message, 1);
    }
  }
}

ProgramRunResult _result(String title, String output, String error, int code) =>
    ProgramRunResult(
      title: title,
      stdout: Stream.fromIterable(
        output.isEmpty
            ? const <String>[]
            : const LineSplitter().convert(output),
      ),
      stderr: Stream.fromIterable(
        error.isEmpty ? const <String>[] : const LineSplitter().convert(error),
      ),
      exitCode: Future.value(code),
    );

/// Read-only commands: mutations remain explicit through the editor Save action.
Future<bool> jsonTerminalCommand(
  SandboxShellBackend backend,
  String command,
) async {
  final parsed = CommandParser.tokenize(
    command,
    escapePolicy: EscapePolicy.backslashLiteral,
  );
  if (!parsed.ok ||
      parsed.tokens.isEmpty ||
      parsed.tokens.first.text != 'json') {
    return false;
  }
  final args = parsed.tokens.skip(1).map((t) => t.text).toList();
  const usage =
      'json check|format|minify|sort|stats <文件>\njson get <文件> <JSON Pointer>\n仅在本机读取文件；输出不会覆盖源文件。';
  var output = '', error = '';
  var code = 0;
  try {
    if (args.isEmpty || args.first == '--help' || args.first == 'help') {
      output = usage;
    } else {
      final operation = args.first;
      if (!const {
            'check',
            'format',
            'minify',
            'sort',
            'stats',
            'get',
          }.contains(operation) ||
          args.length != (operation == 'get' ? 3 : 2)) {
        throw const FormatException(usage);
      }
      final path = backend.resolveSandboxPath(args[1]);
      final resolved = await File(path).resolveSymbolicLinks();
      final realRoot = await Directory(
        backend.sandboxRoot,
      ).resolveSymbolicLinks();
      if (!p.isWithin(realRoot, resolved)) {
        throw const FormatException('文件链接不能越出沙盒');
      }
      final file = File(resolved);
      if (await file.length() > JsonWorkbench.maximumLength) {
        throw const FormatException('文件超过 2 MiB 上限');
      }
      final source = await file.readAsString();
      final inspection = await compute(JsonWorkbench.inspect, source);
      if (!inspection.valid) {
        throw FormatException(inspection.problems.join('\n'));
      }
      output = switch (operation) {
        'check' => 'JSON 有效：${inspection.nodes.length} 个节点',
        'format' => inspection.formatted,
        'minify' => jsonEncode(inspection.value),
        'sort' => JsonWorkbench.pretty(
          JsonWorkbench.sortKeys(inspection.value),
        ),
        'get' => JsonWorkbench.pretty(
          JsonWorkbench.select(inspection.value, args[2]),
        ),
        _ => JsonWorkbench.pretty({
          'nodes': inspection.nodes.length,
          'characters': source.length,
          'rootType': JsonWorkbench.typeOf(inspection.value),
        }),
      };
    }
  } on FormatException catch (e) {
    error = e.message;
    code = 1;
  } on FileSystemException catch (e) {
    error = '无法读取文件：${e.message}';
    code = 1;
  } on SandboxEscapeException {
    error = '不能越出沙盒目录';
    code = 1;
  }
  await backend.runStreams(
    title: 'JSON',
    stdout: _result('', output, '', 0).stdout,
    stderr: _result('', '', error, 0).stderr,
    exitCode: Future.value(code),
  );
  return true;
}
