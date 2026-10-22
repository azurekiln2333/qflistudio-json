import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_json/json/json_analyzer.dart';
import 'package:qfli_json/main.dart' show jsonProfile;
import 'package:qfli_studio_core/editor/editor_analysis_controller.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/editor/editor_problems_bar.dart';
import 'package:qfli_studio_core/editor/project_history.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
// Inspect the actual widget owned by the shared core's re_editor dependency.
// ignore: depend_on_referenced_packages
import 'package:re_editor/re_editor.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory root;
  setUp(() {
    root = Directory.systemTemp.createTempSync('json_analyzer_');
  });
  tearDown(() {
    root.deleteSync(recursive: true);
  });
  CodeAnalysisRequest request(
    List<CodeDocumentSnapshot> documents, {
    String active = 'data.json',
  }) => CodeAnalysisRequest(
    projectPath: root.path,
    activeFilePath: p.join(root.path, active),
    language: 'json',
    revision: 1,
    documents: documents,
  );
  CodeDocumentSnapshot doc(String name, String text) => CodeDocumentSnapshot(
    path: p.join(root.path, name),
    text: text,
    revision: 1,
  );
  test(
    'analyzer checks unsaved snapshots and preserves exact UTF-16/CRLF offsets',
    () async {
      File(p.join(root.path, 'data.json')).writeAsStringSync('{}');
      final source = '{"emoji":"😀",\r\n "name" true}';
      final result = await const JsonCodeAnalyzer().analyze(
        request([
          doc('data.json', source),
          doc('second.json', '{"a":1,"a":2}'),
          doc('notes.txt', 'not JSON'),
        ]),
      );
      expect(result.unavailableReason, isNull);
      expect(result.diagnostics, hasLength(2));
      final error = result.diagnostics.first;
      expect(error.startOffset, source.indexOf('true'));
      expect(error.endOffset, error.startOffset + 1);
      expect(error.filePath, p.join(root.path, 'data.json'));
      expect(error.message, contains('缺少冒号'));
      expect(File(p.join(root.path, 'data.json')).readAsStringSync(), '{}');
    },
  );
  test(
    'unsupported extension and absent active snapshot never claim clean',
    () async {
      expect(
        (await const JsonCodeAnalyzer().analyze(
          request([doc('notes.txt', 'text')], active: 'notes.txt'),
        )).unavailableReason,
        isNotNull,
      );
      expect(
        (await const JsonCodeAnalyzer().analyze(request([]))).unavailableReason,
        isNotNull,
      );
      expect(
        (await const JsonCodeAnalyzer().analyze(
          request([doc('data.json', 'null')]),
        )).diagnostics,
        isEmpty,
      );
    },
  );
  testWidgets(
    'main editor diagnostics decorate, navigate in Problems and clear unsaved corrections',
    (tester) async {
      const original = '{\n "a" true}';
      final file = File(p.join(root.path, 'data.json'))
        ..writeAsStringSync(original);
      final project = Project.create(
        name: 'JSON',
        path: root.path,
        language: 'JSON',
        type: 'json',
      );
      final auth = AuthStore();
      final settings = SettingsStore();
      final store = ProjectStore(
        storageFile: File(p.join(root.path, '.test-projects.json')),
      );
      final previousProfile = StudioProfile.current;
      StudioProfile.current = jsonProfile;
      addTearDown(() async {
        await tester.pumpWidget(const SizedBox.shrink());
        var historyFinished = false;
        ProjectHistory.load(root.path).then((_) => historyFinished = true);
        await _pumpEditorUntil(tester, () => historyFinished);
        StudioProfile.current = previousProfile;
        auth.dispose();
        settings.dispose();
        store.dispose();
      });
      await tester.pumpWidget(
        MaterialApp(
          home: EditorPage(
            project: project,
            auth: auth,
            store: store,
            settings: settings,
            initialOpenPath: file.path,
          ),
        ),
      );
      EditorAnalysisController? mountedAnalysis;
      await _pumpEditorUntil(tester, () {
        final bars = find.byType(EditorProblemsBar);
        if (bars.evaluate().isEmpty) return false;
        mountedAnalysis = tester.widget<EditorProblemsBar>(bars.first).analysis;
        return mountedAnalysis!.checked &&
            !mountedAnalysis!.pending &&
            find.text('问题 1').evaluate().isNotEmpty;
      });
      final analysis = mountedAnalysis!;
      final editor = analysis.editor;
      expect(analysis.checked, isTrue, reason: analysis.unavailableReason);
      expect(analysis.problems, hasLength(1));
      expect(find.text('问题 1'), findsOneWidget);
      final open = editor.current!;
      final codeEditor = tester.widget<CodeEditor>(find.byType(CodeEditor));
      expect(codeEditor.controller, same(open.controller));
      final context = tester.element(find.byType(CodeEditor));
      final span = open.controller.buildTextSpan(
        context: context,
        index: 1,
        textSpan: const TextSpan(text: ' "a" true}'),
        style: const TextStyle(),
      );
      bool wavy(InlineSpan s) =>
          s is TextSpan &&
          (s.style?.decorationStyle == TextDecorationStyle.wavy ||
              (s.children?.any(wavy) ?? false));
      expect(wavy(span), isTrue);
      final problem = analysis.problems.single;
      expect(analysis.location(problem), 'data.json:2:6');
      await tester.tap(find.byKey(const ValueKey('editor-problems-status')));
      await _pumpEditorUntil(
        tester,
        () => find.byType(EditorProblemsPanel).evaluate().isNotEmpty,
      );
      final problemRow = find.descendant(
        of: find.byKey(const ValueKey('editor-problems-list')),
        matching: find.byType(ListTile),
      );
      expect(problemRow, findsOneWidget);
      expect(
        find.descendant(of: problemRow, matching: find.text(problem.message)),
        findsOneWidget,
      );
      expect(find.text('data.json:2:6 · JSON json.syntax'), findsOneWidget);
      await tester.tap(problemRow);
      await tester.pump();
      expect(open.controller.selection.baseIndex, 1);
      expect(open.controller.selection.baseOffset, 5);
      expect(open.controller.selection.extentIndex, 1);
      expect(open.controller.selection.extentOffset, 6);
      expect(open.dirty, isFalse);
      expect(file.readAsStringSync(), original);

      const corrected = '{"a":true}';
      codeEditor.controller!.text = corrected;
      expect(analysis.checked, isFalse);
      expect(open.diagnostics!.problems, isEmpty);
      await _pumpEditorUntil(
        tester,
        () =>
            analysis.checked &&
            !analysis.pending &&
            find.text('本地检查未发现问题').evaluate().isNotEmpty,
      );
      expect(analysis.problems, isEmpty);
      expect(analysis.checked, isTrue);
      expect(find.text(problem.message), findsNothing);
      expect(find.byKey(const ValueKey('editor-problems-list')), findsNothing);
      expect(find.text('本地检查未发现问题'), findsWidgets);
      expect(
        wavy(
          open.controller.buildTextSpan(
            context: tester.element(find.byType(CodeEditor)),
            index: 0,
            textSpan: const TextSpan(text: corrected),
            style: const TextStyle(),
          ),
        ),
        isFalse,
      );
      expect(open.controller.text, corrected);
      expect(open.dirty, isTrue);
      expect(file.readAsStringSync(), original);
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _pumpEditorUntil(WidgetTester tester, bool Function() done) async {
  for (var attempt = 0; attempt < 200; attempt++) {
    // Analyzer isolates and disk reads need real time; their notifications and
    // the diagnostic post-frame repaint then need widget frames to converge.
    await tester.pump(const Duration(milliseconds: 20));
    if (done()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(done(), isTrue, reason: 'The main editor operation did not finish.');
}
