import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_json/json/json_document_page.dart';
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
// Exercise the actual shared editor's text and selection controllers.
// ignore: depend_on_referenced_packages
import 'package:re_editor/re_editor.dart';

const _primarySource = '{\n  "owner": "primary",\n  "value": 1\n}';
const _secondarySource = '{\n  "owner": "secondary",\n  "value": 2\n}';
const _unsavedError = '{\n  "owner" true\n}';
const _savedSecondary = '{\n  "owner": "secondary edited",\n  "value": 99\n}';
const _primaryCursor = FileCursor(
  baseIndex: 1,
  baseOffset: 3,
  extentIndex: 1,
  extentOffset: 3,
);
const _secondaryCursor = FileCursor(
  baseIndex: 2,
  baseOffset: 4,
  extentIndex: 2,
  extentOffset: 4,
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'JSON child editor restores same-name owners and saves document edits to the captured secondary root',
    (tester) async {
      late _JsonRoots fixture;
      await tester.runAsync(() async {
        fixture = await _JsonRoots.create();
      });
      final previousProfile = StudioProfile.current;
      StudioProfile.current = jsonProfile;
      addTearDown(() async {
        try {
          await tester.pumpWidget(const SizedBox.shrink());
          await fixture.readHistory(tester);
        } finally {
          StudioProfile.current = previousProfile;
          fixture.auth.dispose();
          fixture.settings.dispose();
          fixture.store.dispose();
          await tester.runAsync(
            () => fixture.directory.delete(recursive: true),
          );
        }
      });

      // Use the real JSON child profile's legacy multi-root history. A saved
      // main-release workspace must not be required for this product contract.
      var analysis = await fixture.mount(tester);
      expect(
        tester.widget<EditorPage>(find.byType(EditorPage)).workspace,
        isNull,
      );
      final editor = analysis.editor;
      final primary = editor.files[0];
      final secondary = editor.files[1];
      expect(editor.files.map((file) => file.name), ['data.json', 'data.json']);
      expect(editor.files.map((file) => file.path), [
        fixture.primaryFile.path,
        fixture.secondaryFile.path,
      ]);
      expect(primary.projectRootPath, fixture.primary.path);
      expect(primary.ownerProjectName, fixture.primary.name);
      expect(secondary.projectRootPath, fixture.secondary.path);
      expect(secondary.ownerProjectName, fixture.secondary.name);
      expect(secondary.projectType, 'json');
      expect(
        secondary.tabLabel(fixture.primary.name),
        'Secondary JSON/data.json',
      );
      expect(editor.current, same(secondary));
      _expectCursor(primary.controller.selection, _primaryCursor);
      _expectCursor(secondary.controller.selection, _secondaryCursor);
      expect(analysis.problems, isEmpty);

      // The disk contains valid JSON. Only the secondary root's in-memory
      // snapshot is invalid, so a disk reread or primary-root fallback fails.
      secondary.controller.text = _unsavedError;
      await _pumpUntil(
        tester,
        () =>
            analysis.checked &&
            !analysis.pending &&
            analysis.problems.length == 1,
        'The real JSON analyzer did not inspect the secondary unsaved buffer.',
      );
      final problem = analysis.problems.single;
      expect(problem.filePath, fixture.secondaryFile.path);
      expect(problem.source, 'JSON');
      expect(problem.message, contains('缺少冒号'));
      expect(problem.startOffset, _unsavedError.indexOf('true'));
      expect(problem.endOffset, problem.startOffset + 1);
      expect(analysis.location(problem), 'data.json:2:11');
      expect(secondary.diagnostics!.problems, hasLength(1));
      expect(primary.diagnostics!.problems, isEmpty);
      expect(secondary.dirty, isTrue);
      expect(primary.dirty, isFalse);
      expect(primary.controller.text, _primarySource);
      fixture.expectDisk(_primarySource, _secondarySource);

      final secondaryCode = find.byWidgetPredicate(
        (widget) =>
            widget is CodeEditor &&
            identical(widget.controller, secondary.controller),
      );
      expect(secondaryCode, findsOneWidget);
      expect(
        _isWavy(
          secondary.controller.buildTextSpan(
            context: tester.element(secondaryCode),
            index: 1,
            textSpan: const TextSpan(text: '  "owner" true'),
            style: const TextStyle(),
          ),
        ),
        isTrue,
      );
      await tester.tap(
        find.byKey(const ValueKey('editor-problems-status')).hitTestable(),
      );
      await _pumpUntil(
        tester,
        () => find.byType(EditorProblemsPanel).evaluate().isNotEmpty,
        'The actual Problems panel did not open.',
      );
      final problemRow = find.descendant(
        of: find.byKey(const ValueKey('editor-problems-list')),
        matching: find.byType(ListTile),
      );
      expect(problemRow, findsOneWidget);
      await tester.tap(problemRow);
      await tester.pump();
      expect(editor.current, same(secondary));
      expect(secondary.controller.selection.baseIndex, 1);
      expect(secondary.controller.selection.baseOffset, 10);
      expect(secondary.controller.selection.extentIndex, 1);
      expect(secondary.controller.selection.extentOffset, 11);
      fixture.expectDisk(_primarySource, _secondarySource);
      await tester.tap(find.byKey(const ValueKey('close-editor-problems')));
      await tester.pump();

      // Problems navigation deliberately selects the offending character.
      // A non-collapsed selection replaces the shared AppBar actions with the
      // selection toolbar, so restore a caret before opening the document tool.
      secondary.controller.selection = const CodeLineSelection.collapsed(
        index: 1,
        offset: 10,
      );
      final documentAction = find.byTooltip('编辑与预览').hitTestable();
      await _pumpUntil(
        tester,
        () => documentAction.evaluate().length == 1,
        'The document-tool action did not return after collapsing the selection.',
      );

      // Open the product's actual document tool through EditorPage, rather
      // than constructing a request or replacing the profile with a fake hook.
      await tester.tap(documentAction);
      await _pumpUntil(
        tester,
        () => find.byType(JsonDocumentPage).evaluate().isNotEmpty,
        'The JSON document tool did not open.',
      );
      // Complete the route transition before interacting with its controls.
      await tester.pump(const Duration(milliseconds: 350));
      final document = tester.widget<JsonDocumentPage>(
        find.byType(JsonDocumentPage),
      );
      expect(document.request.path, fixture.secondaryFile.path);
      expect(document.request.projectPath, fixture.secondary.path);
      expect(document.request.name, 'data.json');
      expect(document.request.text, _unsavedError);
      expect(document.request.readOnly, isFalse);
      final sourceField = find.byKey(const Key('json-document-source'));
      expect(
        tester.widget<TextField>(sourceField).controller!.text,
        _unsavedError,
      );

      // The request must retain its opened file even if another same-name tab
      // becomes current while the document route remains open.
      editor.select(0);
      await tester.pump();
      expect(editor.current, same(primary));
      await tester.enterText(sourceField, _savedSecondary);
      await tester.tap(find.byTooltip('保存'));
      await _pumpUntil(
        tester,
        () =>
            secondary.controller.text == _savedSecondary &&
            !secondary.dirty &&
            fixture.secondaryFile.readAsStringSync() == _savedSecondary &&
            find.text('已保存').evaluate().isNotEmpty,
        'DocumentToolRequest.save did not finish saving its secondary owner.',
      );
      expect(editor.current, same(primary));
      expect(primary.controller.text, _primarySource);
      expect(primary.dirty, isFalse);
      expect(secondary.controller.text, _savedSecondary);
      expect(secondary.dirty, isFalse);
      fixture.expectDisk(_primarySource, _savedSecondary);

      await tester.pageBack();
      await _pumpUntil(
        tester,
        () => find.byType(JsonDocumentPage).evaluate().isEmpty,
        'The saved document tool did not return to EditorPage.',
      );
      editor.select(1);
      await _pumpUntil(
        tester,
        () =>
            analysis.checked && !analysis.pending && analysis.problems.isEmpty,
        'The secondary diagnostics did not clear after the document-tool save.',
      );
      expect(secondary.diagnostics!.problems, isEmpty);
      expect(find.text(problem.message), findsNothing);
      expect(
        _isWavy(
          secondary.controller.buildTextSpan(
            context: tester.element(secondaryCode),
            index: 1,
            textSpan: TextSpan(text: _savedSecondary.split('\n')[1]),
            style: const TextStyle(),
          ),
        ),
        isFalse,
      );
      expect(primary.controller.text, _primarySource);
      fixture.expectDisk(_primarySource, _savedSecondary);

      primary.controller.selection = const CodeLineSelection.collapsed(
        index: 1,
        offset: 3,
      );
      secondary.controller.selection = const CodeLineSelection.collapsed(
        index: 2,
        offset: 5,
      );
      await tester.pump();
      await tester.pumpWidget(const SizedBox.shrink());
      final saved = await fixture.readHistory(tester);
      expect(saved.documents.map((document) => document.projectPath), [
        fixture.primary.path,
        fixture.secondary.path,
      ]);
      expect(saved.documents.map((document) => document.relativePath), [
        'data.json',
        'data.json',
      ]);
      expect(saved.documents.map((document) => document.isActive), [
        false,
        true,
      ]);
      expect(saved.openFiles, ['data.json']);
      expect(saved.activeFile, isNull);
      expect(saved.workspaceRoots, [
        fixture.primary.path,
        fixture.secondary.path,
      ]);
      expect(saved.documents.last.cursor.baseIndex, 2);
      expect(saved.documents.last.cursor.baseOffset, 5);

      analysis = await fixture.mount(tester);
      final restored = analysis.editor;
      expect(restored, isNot(same(editor)));
      expect(restored.files.map((file) => file.path), [
        fixture.primaryFile.path,
        fixture.secondaryFile.path,
      ]);
      expect(restored.current, same(restored.files[1]));
      expect(restored.current!.projectRootPath, fixture.secondary.path);
      expect(restored.current!.ownerProjectName, fixture.secondary.name);
      expect(restored.current!.projectType, 'json');
      _expectCursor(restored.files.first.controller.selection, _primaryCursor);
      expect(restored.current!.controller.selection.baseIndex, 2);
      expect(restored.current!.controller.selection.baseOffset, 5);
      expect(restored.current!.controller.selection.extentIndex, 2);
      expect(restored.current!.controller.selection.extentOffset, 5);
      expect(restored.files.first.controller.text, _primarySource);
      expect(restored.current!.controller.text, _savedSecondary);
      expect(restored.files.every((file) => !file.dirty), isTrue);
      expect(analysis.problems, isEmpty);
      fixture.expectDisk(_primarySource, _savedSecondary);
      expect(tester.takeException(), isNull);
    },
  );
}

class _JsonRoots {
  _JsonRoots(this.directory, this.primary, this.secondary, this.store);

  final Directory directory;
  final Project primary;
  final Project secondary;
  final ProjectStore store;
  final auth = AuthStore();
  final settings = SettingsStore();

  File get primaryFile => File(p.join(primary.path, 'data.json'));
  File get secondaryFile => File(p.join(secondary.path, 'data.json'));

  static Future<_JsonRoots> create() async {
    final directory = await Directory.systemTemp.createTemp('json_multi_root_');
    final primary = Project.create(
      name: 'Primary JSON',
      path: p.join(directory.path, 'primary'),
      language: 'JSON',
      type: 'json',
    );
    final secondary = Project.create(
      name: 'Secondary JSON',
      path: p.join(directory.path, 'secondary'),
      language: 'JSON',
      type: 'json',
    );
    await Directory(primary.path).create();
    await Directory(secondary.path).create();
    await File(p.join(primary.path, 'data.json')).writeAsString(_primarySource);
    await File(
      p.join(secondary.path, 'data.json'),
    ).writeAsString(_secondarySource);
    final registry = File(p.join(directory.path, 'projects.json'));
    await registry.writeAsString(
      jsonEncode({
        'projects': [primary.toJson(), secondary.toJson()],
      }),
    );
    final store = ProjectStore(storageFile: registry);
    await store.load();
    await ProjectHistory.save(
      primary.path,
      cursors: const {},
      openFiles: const [],
      activeFile: null,
      documents: [
        ProjectDocumentSession(
          projectPath: primary.path,
          relativePath: 'data.json',
          cursor: _primaryCursor,
        ),
        ProjectDocumentSession(
          projectPath: secondary.path,
          relativePath: 'data.json',
          cursor: _secondaryCursor,
          isActive: true,
        ),
      ],
    );
    await ProjectHistory.saveWorkspaceRoots(primary.path, [
      primary.path,
      secondary.path,
    ]);
    return _JsonRoots(directory, primary, secondary, store);
  }

  Future<EditorAnalysisController> mount(WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: EditorPage(
          project: primary,
          auth: auth,
          store: store,
          settings: settings,
        ),
      ),
    );
    EditorAnalysisController? analysis;
    await _pumpUntil(
      tester,
      () {
        final bars = find.byType(EditorProblemsBar);
        if (bars.evaluate().isEmpty) return false;
        analysis = tester.widget<EditorProblemsBar>(bars.first).analysis;
        return analysis!.editor.files.length == 2 &&
            analysis!.editor.current?.path == secondaryFile.path &&
            analysis!.checked &&
            !analysis!.pending;
      },
      'The JSON child editor did not restore both owned tabs and analyze the active root.',
    );
    return analysis!;
  }

  Future<ProjectSession> readHistory(WidgetTester tester) async {
    ProjectSession? session;
    ProjectHistory.load(primary.path).then((value) => session = value);
    await _pumpUntil(
      tester,
      () => session != null,
      'The child-product history did not finish its queued writes.',
    );
    return session!;
  }

  void expectDisk(String primaryText, String secondaryText) {
    expect(primaryFile.readAsStringSync(), primaryText);
    expect(secondaryFile.readAsStringSync(), secondaryText);
  }
}

void _expectCursor(CodeLineSelection selection, FileCursor cursor) {
  expect(selection.baseIndex, cursor.baseIndex);
  expect(selection.baseOffset, cursor.baseOffset);
  expect(selection.extentIndex, cursor.extentIndex);
  expect(selection.extentOffset, cursor.extentOffset);
}

bool _isWavy(InlineSpan span) =>
    span is TextSpan &&
    (span.style?.decorationStyle == TextDecorationStyle.wavy ||
        (span.children?.any(_isWavy) ?? false));

Future<void> _pumpUntil(
  WidgetTester tester,
  bool Function() done,
  String reason,
) async {
  for (var attempt = 0; attempt < 200; attempt++) {
    // The real JSON compute isolate and queued file IO need wall time as well
    // as frames. Keep this bounded so an ownership regression fails clearly.
    await tester.pump(const Duration(milliseconds: 20));
    if (done()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(done(), isTrue, reason: reason);
}
