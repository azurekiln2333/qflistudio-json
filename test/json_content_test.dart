import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_json/content/json_content_repository.dart';
import 'package:qfli_json/json/json_workbench.dart';
import 'package:qfli_studio_core/content/content_repository.dart';
import 'package:qfli_studio_core/content/content_validator.dart';

class _FileBundle extends CachingAssetBundle {
  final requested = <String>[];

  @override
  Future<String> loadString(String key, {bool cache = true}) async {
    requested.add(key);
    return File(key).readAsString();
  }

  @override
  Future<ByteData> load(String key) =>
      throw UnsupportedError('Text assets only');
}

String _shape(Object? value) {
  if (value is Map<String, Object?>) {
    final keys = value.keys.toList()..sort();
    return '{${keys.map((key) => '${jsonEncode(key)}:${_shape(value[key])}').join(',')}}';
  }
  if (value is List) {
    final children = value.map(_shape).toSet().toList()..sort();
    return '[${children.join(',')}]';
  }
  return JsonWorkbench.typeOf(value);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late ContentCatalog catalog;
  late Map<String, Object?> audit;

  setUpAll(() async {
    catalog = await JsonContentRepository(bundle: _FileBundle()).load();
    audit =
        (jsonDecode(await File(JsonContentRepository.auditAsset).readAsString())
                as Map)
            .cast<String, Object?>();
  });

  test('catalog meets the core release contract for the JSON product', () {
    final result = ContentCatalogValidator.validate(
      catalog,
      enforceReleaseMinimum: true,
      requiredTypes: {'json'},
      minimumEntriesPerType: 320,
    );
    expect(result.issues, isEmpty, reason: result.issues.join('\n'));
    expect(catalog.examples, hasLength(340));
    expect(catalog.tutorials, hasLength(340));
    expect(audit['newExampleCount'], 240);
    expect(audit['newTutorialCount'], 240);
    expect((audit['categories'] as Map).length, 24);
    expect((audit['categories'] as Map).values, everyElement(10));
    expect(
      [...catalog.tutorials, ...catalog.examples].map((e) => e.type),
      everyElement('json'),
    );
  });

  test(
    'every old example and lesson retains its exact original ID and code',
    () {
      final baseline = ContentCatalog.fromJson(
        tutorialsSource: File(
          '../qflistudio-core/assets/content/tutorials.json',
        ).readAsStringSync(),
        examplesSource: File(
          '../qflistudio-core/assets/content/examples.json',
        ).readAsStringSync(),
      );
      final originalExamples = baseline.examples.where((e) => e.type == 'json');
      final originalTutorials = baseline.tutorials.where(
        (e) => e.type == 'json',
      );
      expect(originalExamples, hasLength(100));
      expect(originalTutorials, hasLength(100));
      final examplesById = {for (final e in catalog.examples) e.id: e};
      final tutorialsById = {for (final e in catalog.tutorials) e.id: e};
      for (final original in originalExamples) {
        final current = examplesById[original.id];
        expect(current, isNotNull, reason: original.id);
        expect(current!.code, original.code, reason: original.id);
        expect(current.title, original.title);
        expect(current.summary, original.summary);
      }
      for (final original in originalTutorials) {
        final current = tutorialsById[original.id];
        expect(current, isNotNull, reason: original.id);
        final lessons = {for (final e in current!.lessons) e.id: e};
        for (final oldLesson in original.lessons) {
          final lesson = lessons[oldLesson.id];
          expect(lesson, isNotNull, reason: oldLesson.id);
          expect(lesson!.code, oldLesson.code, reason: oldLesson.id);
          expect(lesson.explain, startsWith(oldLesson.explain));
          expect(lesson.exercises, hasLength(oldLesson.exercises.length));
          for (var i = 0; i < oldLesson.exercises.length; i++) {
            expect(lesson.exercises[i].prompt, oldLesson.exercises[i].prompt);
            expect(JsonWorkbench.decode(lesson.exercises[i].answer), {
              'explanation': oldLesson.exercises[i].answer,
            });
          }
        }
      }
      expect(audit['inheritedExampleCount'], 100);
      expect(audit['inheritedTutorialCount'], 100);
      expect(audit['corrections'], {
        'exampleOutputs': 100,
        'lessonOutputs': 100,
        'proseExerciseAnswers': 200,
        'exampleFixtures': 100,
      });
      expect(audit['correctionDetails'], hasLength(500));
    },
  );

  test(
    'new scenarios have 240 distinct structural models and explanations',
    () {
      final practical = catalog.examples
          .where((e) => e.id.startsWith('json-practical-'))
          .toList();
      expect(practical, hasLength(240));
      expect(
        practical.map((e) => _shape(JsonWorkbench.decode(e.code))).toSet(),
        hasLength(240),
      );
      expect(practical.map((e) => e.summary).toSet(), hasLength(240));
      expect(practical.every((e) => e.summary.length >= 40), isTrue);
    },
  );

  test('all 340 examples and every fixture pass the shipped JSON parser', () {
    final semanticDocuments = <String>{};
    final lessonIds = {
      for (final tutorial in catalog.tutorials)
        for (final lesson in tutorial.lessons) lesson.id,
    };
    for (final example in catalog.examples) {
      final inspected = JsonWorkbench.inspect(example.code);
      expect(inspected.problems, isEmpty, reason: example.id);
      expect(
        example.expectedOutput,
        JsonWorkbench.pretty(inspected.value),
        reason: '${example.id} must show the actual formatter result',
      );
      expect(example.sourceLessonId, isIn(lessonIds), reason: example.id);
      expect(example.inputFixtures, isNotEmpty, reason: example.id);
      for (final fixture in example.inputFixtures.entries) {
        final result = JsonWorkbench.inspect(fixture.value);
        expect(
          result.problems,
          isEmpty,
          reason: '${example.id}/${fixture.key}',
        );
        expect(
          JsonWorkbench.equal(result.value, inspected.value),
          isTrue,
          reason: '${example.id} fixture must be the actual imported document',
        );
      }
      final canonical = JsonWorkbench.pretty(
        JsonWorkbench.sortKeys(inspected.value),
      );
      expect(
        semanticDocuments.add(canonical),
        isTrue,
        reason: 'Duplicate document: ${example.id}',
      );
    }
  });

  test('every lesson output and exercise answer is real, valid JSON', () {
    final ids = <String>{};
    var exercises = 0;
    for (final tutorial in catalog.tutorials) {
      for (final lesson in tutorial.lessons) {
        expect(ids.add(lesson.id), isTrue, reason: lesson.id);
        final parsed = JsonWorkbench.inspect(lesson.code);
        expect(parsed.problems, isEmpty, reason: lesson.id);
        expect(
          lesson.output,
          JsonWorkbench.pretty(parsed.value),
          reason: lesson.id,
        );
        expect(lesson.exercises, isNotEmpty, reason: lesson.id);
        for (final exercise in lesson.exercises) {
          exercises++;
          final answer = JsonWorkbench.inspect(exercise.answer);
          expect(
            answer.problems,
            isEmpty,
            reason: '${lesson.id}: ${exercise.prompt}',
          );
          if (lesson.id.startsWith('json-practical-')) {
            const prefix = '使用 JSON Pointer ';
            const suffix = ' 选择当前值，以合法 JSON 写出答案。';
            expect(exercise.prompt, startsWith(prefix));
            expect(exercise.prompt, endsWith(suffix));
            final pointer =
                jsonDecode(
                      exercise.prompt.substring(
                        prefix.length,
                        exercise.prompt.length - suffix.length,
                      ),
                    )
                    as String;
            expect(
              JsonWorkbench.equal(
                JsonWorkbench.select(parsed.value, pointer),
                answer.value,
              ),
              isTrue,
              reason: '${lesson.id}: exercise must match the document',
            );
            expect(lesson.objective, isNotEmpty);
            expect(lesson.pitfalls, isNotEmpty);
          }
        }
      }
    }
    expect(exercises, 440);
  });

  test(
    'practical patch and merge examples also pass their promised operation',
    () {
      for (final example in catalog.examples.where(
        (e) => e.id.startsWith('json-practical-'),
      )) {
        final value = JsonWorkbench.decode(example.code);
        if (value is! Map<String, Object?>) continue;
        if (value.containsKey('operations') && value.containsKey('expected')) {
          expect(
            JsonWorkbench.equal(
              JsonWorkbench.applyPatch(value['document'], value['operations']),
              value['expected'],
            ),
            isTrue,
            reason: example.id,
          );
        }
        if (value.containsKey('target') &&
            value.containsKey('patch') &&
            value.containsKey('expected')) {
          expect(
            JsonWorkbench.equal(
              JsonWorkbench.mergePatch(value['target'], value['patch']),
              value['expected'],
            ),
            isTrue,
            reason: example.id,
          );
        }
      }
    },
  );

  test(
    'repository caches local reads and applies language/product filters',
    () async {
      final bundle = _FileBundle();
      final repository = JsonContentRepository(bundle: bundle);
      final first = await repository.load();
      expect(await repository.load(), same(first));
      expect(bundle.requested, [
        JsonContentRepository.tutorialAsset,
        JsonContentRepository.exampleAsset,
      ]);
      expect(
        await repository.examples(filter: ContentFilter.forProduct('json')),
        hasLength(340),
      );
      expect(
        await repository.examples(
          filter: const ContentFilter(language: 'JSON'),
        ),
        hasLength(340),
      );
      expect(
        await repository.examples(filter: const ContentFilter(type: 'python')),
        isEmpty,
      );
      expect(
        await repository.tutorials(filter: ContentFilter.forProduct('forge')),
        isEmpty,
      );
    },
  );

  test('product bundle contains the actual shipped JSON curriculum', () async {
    final bundled = await JsonContentRepository().load();
    expect(bundled.examples, hasLength(catalog.examples.length));
    expect(bundled.tutorials, hasLength(catalog.tutorials.length));
    expect(
      await rootBundle.loadString(JsonContentRepository.auditAsset),
      isNotEmpty,
    );
  });
}
