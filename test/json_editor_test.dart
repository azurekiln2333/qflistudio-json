import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_json/json/json_document_page.dart';
import 'package:qfli_json/json/json_tools.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/project_store.dart';

void main() {
  Future<void> load(
    WidgetTester tester,
    String source, {
    Future<String?> Function(String)? save,
    bool readOnly = false,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        home: JsonDocumentPage(
          request: DocumentToolRequest(
            path: '/project/data.json',
            name: 'data.json',
            text: source,
            projectPath: '/project',
            readOnly: readOnly,
            save: save ?? (_) async => null,
          ),
        ),
      ),
    );
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 100)),
    );
    await tester.pumpAndSettle();
  }

  testWidgets(
    'errors underline the source, navigate and clear after correction',
    (tester) async {
      await load(tester, '{\n  "a" true\n}');
      expect(find.textContaining('缺少冒号'), findsOneWidget);
      final field = tester.widget<TextField>(
        find.byKey(const Key('json-document-source')),
      );
      final controller = field.controller! as JsonSourceController;
      expect(controller.problemOffset, 8);
      final context = tester.element(
        find.byKey(const Key('json-document-source')),
      );
      final span = controller.buildTextSpan(
        context: context,
        withComposing: false,
      );
      expect(
        span.children!.whereType<TextSpan>().any(
          (s) => s.style?.decorationStyle == TextDecorationStyle.wavy,
        ),
        isTrue,
      );
      await tester.tap(find.textContaining('缺少冒号'));
      await tester.pump();
      expect(controller.selection.baseOffset, 8);
      await tester.enterText(
        find.byKey(const Key('json-document-source')),
        '{"a":true}',
      );
      await tester.pump(const Duration(milliseconds: 300));
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 100)),
      );
      await tester.pumpAndSettle();
      expect(find.text('JSON 有效'), findsOneWidget);
      expect(controller.problemOffset, isNull);
      expect(find.textContaining('缺少冒号'), findsNothing);
    },
  );
  testWidgets(
    'returning to validated text rejects another source check in flight',
    (tester) async {
      const original = '{"a":1}';
      var saves = 0;
      await load(
        tester,
        original,
        save: (_) async {
          saves++;
          return null;
        },
      );
      final controller =
          tester
                  .widget<TextField>(
                    find.byKey(const Key('json-document-source')),
                  )
                  .controller!
              as JsonSourceController;
      expect(controller.lastValidatedSource, original);
      controller.text = '{"a" true}';
      // Start B's real isolate, then undo to the already-validated A before
      // yielding. B must never become A's accepted inspection.
      tester
          .widget<TextButton>(find.widgetWithText(TextButton, '校验'))
          .onPressed!();
      controller.text = original;
      await tester.pump(const Duration(milliseconds: 300));
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 100)),
      );
      await tester.pumpAndSettle();
      expect(controller.text, original);
      expect(controller.lastValidatedSource, original);
      expect(controller.problemOffset, isNull);
      expect(find.text('JSON 有效'), findsOneWidget);
      expect(find.textContaining('缺少冒号'), findsNothing);
      expect(find.text('data.json •'), findsNothing);
      expect(saves, 0);
    },
  );
  testWidgets('nested arrays expose values and navigate to exact scalar span', (
    tester,
  ) async {
    await load(tester, '{"items":[{"name":"Ada"}]}');
    await tester.tap(find.text('结构'));
    await tester.pumpAndSettle();
    final search = find.widgetWithText(TextField, '搜索 JSON Pointer 路径');
    await tester.enterText(search, '/items/0/name');
    await tester.pump();
    final nodeTitle = find.descendant(
      of: find.byType(ListTile),
      matching: find.text('/items/0/name'),
    );
    expect(nodeTitle, findsOneWidget);
    expect(find.text('"Ada" · string'), findsOneWidget);
    await tester.tap(nodeTitle);
    await tester.pump();
    final controller = tester
        .widget<TextField>(find.byKey(const Key('json-document-source')))
        .controller!;
    expect(controller.selection.textInside(controller.text), '"Ada"');
  });
  testWidgets(
    'save uses current buffer and preserves newer edits during await',
    (tester) async {
      final saving = Completer<String?>();
      String? captured;
      await load(
        tester,
        '{"a":1}',
        save: (source) {
          captured = source;
          return saving.future;
        },
      );
      await tester.enterText(
        find.byKey(const Key('json-document-source')),
        '{"a":2}',
      );
      await tester.tap(find.byTooltip('保存'));
      await tester.pump();
      expect(captured, '{"a":2}');
      await tester.enterText(
        find.byKey(const Key('json-document-source')),
        '{"a":3}',
      );
      saving.complete(null);
      await tester.pumpAndSettle();
      expect(find.text('data.json •'), findsOneWidget);
      expect(find.text('已保存'), findsOneWidget);
    },
  );
  testWidgets('read-only document disables writes', (tester) async {
    await load(tester, '{}', readOnly: true);
    expect(
      tester
          .widget<TextField>(find.byKey(const Key('json-document-source')))
          .readOnly,
      isTrue,
    );
    expect(
      tester
          .widget<IconButton>(
            find.byWidgetPredicate((w) => w is IconButton && w.tooltip == '保存'),
          )
          .onPressed,
      isNull,
    );
  });
  testWidgets(
    'background formatting preserves newer edits and can be retried',
    (tester) async {
      await load(tester, '{"old":1}');
      final source = tester
          .widget<TextField>(find.byKey(const Key('json-document-source')))
          .controller!;
      await tester.tap(find.text('格式化'));
      source.text = '{"new":2}';
      for (var attempt = 0; attempt < 200; attempt++) {
        await tester.pump(const Duration(milliseconds: 20));
        if (tester
                .widget<TextButton>(find.widgetWithText(TextButton, '格式化'))
                .onPressed !=
            null) {
          break;
        }
        await tester.runAsync(
          () => Future<void>.delayed(const Duration(milliseconds: 10)),
        );
      }
      expect(source.text, '{"new":2}');
      expect(find.text('文档已更新，请重新执行'), findsOneWidget);
      await tester.tap(find.text('格式化'));
      for (var attempt = 0; attempt < 200; attempt++) {
        await tester.pump(const Duration(milliseconds: 20));
        if (tester
                .widget<TextButton>(find.widgetWithText(TextButton, '格式化'))
                .onPressed !=
            null) {
          break;
        }
        await tester.runAsync(
          () => Future<void>.delayed(const Duration(milliseconds: 10)),
        );
      }
      expect(source.text, '{\n  "new": 2\n}');
    },
  );
  testWidgets('every JSON operation is directly reachable from the tools tab', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(home: Scaffold(body: jsonToolsTab(ProjectStore(), () {}))),
    );
    for (final op in JsonOperation.values) {
      await tester.scrollUntilVisible(
        find.text(op.title),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text(op.title), findsOneWidget);
    }
  });
  testWidgets('invalid tool input reports an error and clears old result', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: JsonOperationPage(operation: JsonOperation.pointer),
      ),
    );
    await tester.tap(find.text('执行'));
    await finishTool(tester);
    expect(
      tester
          .widget<TextField>(find.byKey(const Key('json-tool-result')))
          .controller!
          .text,
      '1',
    );
    await tester.enterText(
      find.byKey(const Key('json-tool-secondary')),
      '/absent',
    );
    await tester.tap(find.text('执行'));
    await finishTool(tester);
    expect(find.textContaining('路径不存在'), findsOneWidget);
    expect(
      tester
          .widget<TextField>(find.byKey(const Key('json-tool-result')))
          .controller!
          .text,
      isEmpty,
    );
  });
}

Future<void> finishTool(WidgetTester tester) async {
  for (var attempt = 0; attempt < 200; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (find.text('处理中…').evaluate().isEmpty) {
      await tester.pumpAndSettle();
      return;
    }
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  fail('The JSON tool did not finish.');
}
