import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/content/content_repository.dart';
import 'package:qfli_studio_core/content/content_validator.dart';
import 'package:qfli_studio_core/services/runner_service.dart';

import 'json_tools.dart';
import 'json_workbench.dart';

/// The same audit is callable from desktop tests and an installed OHOS app.
/// Runner checks use real sandbox files and the profile's normal Run route.
Future<Map<String, Object?>> verifyJsonCatalog(
  ContentCatalog catalog,
  String writableRoot, {
  void Function(String)? progress,
}) async {
  final failures = <String>[];
  var runnerPasses = 0,
      lessonCount = 0,
      exercises = 0,
      fixtures = 0,
      semanticOperations = 0;
  void require(bool condition, String label) {
    if (!condition) failures.add(label);
  }

  final validation = ContentCatalogValidator.validate(
    catalog,
    enforceReleaseMinimum: true,
    requiredTypes: {'json'},
    minimumEntriesPerType: 320,
  );
  failures.addAll(validation.issues.map((e) => e.toString()));
  final scratch = await Directory(
    p.join(writableRoot, 'json_verification'),
  ).create(recursive: true);
  final run = await scratch.createTemp('run_');
  try {
    final entry = File(p.join(run.path, 'data.json'));
    for (final example in catalog.examples) {
      final inspection = JsonWorkbench.inspect(example.code);
      require(inspection.valid, '${example.id}: ${inspection.problems}');
      if (inspection.valid) {
        require(
          inspection.formatted == example.expectedOutput,
          '${example.id}: expected output mismatch',
        );
        final value = inspection.value;
        if (value is Map<String, Object?>) {
          if (value.containsKey('operations') &&
              value.containsKey('expected')) {
            require(
              JsonWorkbench.equal(
                JsonWorkbench.applyPatch(
                  value['document'],
                  value['operations'],
                ),
                value['expected'],
              ),
              '${example.id}: patch result',
            );
            semanticOperations++;
          }
          if (value.containsKey('target') &&
              value.containsKey('patch') &&
              value.containsKey('expected')) {
            require(
              JsonWorkbench.equal(
                JsonWorkbench.mergePatch(value['target'], value['patch']),
                value['expected'],
              ),
              '${example.id}: merge result',
            );
            semanticOperations++;
          }
        }
      }
      for (final fixture in example.inputFixtures.entries) {
        fixtures++;
        final parsed = JsonWorkbench.inspect(fixture.value);
        require(
          parsed.valid && JsonWorkbench.equal(parsed.value, inspection.value),
          '${example.id}/${fixture.key}: fixture',
        );
      }
      await entry.writeAsString(example.code, flush: true);
      final result = await RunnerService.runProject(
        projectPath: run.path,
        entryFile: entry.path,
      );
      if (result == null ||
          result.stdout == null ||
          result.stderr == null ||
          result.exitCode == null) {
        failures.add('${example.id}: runner did not start');
      } else {
        final output = await result.stdout!.join('\n');
        final error = await result.stderr!.join('\n');
        final code = await result.exitCode!;
        if (code == 0 && error.isEmpty && output == example.expectedOutput) {
          runnerPasses++;
        } else {
          failures.add(
            '${example.id}: runner exit=$code outputMatch=${output == example.expectedOutput} error=$error',
          );
        }
      }
      if (runnerPasses % 40 == 0) {
        progress?.call('运行校验 $runnerPasses / ${catalog.examples.length}');
      }
    }
    for (final tutorial in catalog.tutorials) {
      for (final lesson in tutorial.lessons) {
        lessonCount++;
        final parsed = JsonWorkbench.inspect(lesson.code);
        require(
          parsed.valid && parsed.formatted == lesson.output,
          '${lesson.id}: lesson/output',
        );
        for (final exercise in lesson.exercises) {
          exercises++;
          final answer = JsonWorkbench.inspect(exercise.answer);
          require(answer.valid, '${lesson.id}: exercise answer');
          const prefix = '使用 JSON Pointer ', suffix = ' 选择当前值，以合法 JSON 写出答案。';
          if (exercise.prompt.startsWith(prefix) &&
              exercise.prompt.endsWith(suffix)) {
            final pointer =
                jsonDecode(
                      exercise.prompt.substring(
                        prefix.length,
                        exercise.prompt.length - suffix.length,
                      ),
                    )
                    as String;
            require(
              JsonWorkbench.equal(
                JsonWorkbench.select(parsed.value, pointer),
                answer.value,
              ),
              '${lesson.id}: exercise result',
            );
          }
        }
      }
    }
    for (final operation in JsonOperation.values) {
      final output = await JsonOperationTask(
        operation,
        operation.initialSource,
        operation.initialSecond,
      ).result;
      require(output.isNotEmpty, 'tool ${operation.name}');
    }
    await entry.writeAsString('{\n"a" true}');
    final invalid = await RunnerService.runProject(
      projectPath: run.path,
      entryFile: entry.path,
    );
    final invalidOutput = await invalid?.stdout?.join('\n');
    final invalidError = await invalid?.stderr?.join('\n');
    final invalidCode = await invalid?.exitCode;
    require(
      invalidCode == 1 &&
          invalidOutput == '' &&
          (invalidError?.contains('第 2 行') ?? false),
      'invalid source runner diagnostic',
    );
  } finally {
    await run.delete(recursive: true);
  }
  return {
    'passed': failures.isEmpty,
    'examples': catalog.examples.length,
    'runnerPasses': runnerPasses,
    'tutorials': catalog.tutorials.length,
    'lessons': lessonCount,
    'exerciseAnswers': exercises,
    'fixtures': fixtures,
    'semanticOperations': semanticOperations,
    'tools': JsonOperation.values.length,
    'platform': Platform.operatingSystem,
    'failures': failures,
  };
}
