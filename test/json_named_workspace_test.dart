import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
// Use the same temporary-path seam as the shared core's Home tests.
// ignore: depend_on_referenced_packages
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:qfli_json/main.dart' show jsonProfile;
import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/editor/editor_controller.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/editor/editor_problems_bar.dart';
import 'package:qfli_studio_core/editor/file_explorer.dart';
import 'package:qfli_studio_core/editor/project_history.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/services/task_activity_service.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/workspace/saved_workspace.dart';
import 'package:qfli_studio_core/workspace/workspace_store.dart';
// Inspect the real editor selection, rather than a parallel session model.
// ignore: depend_on_referenced_packages
import 'package:re_editor/re_editor.dart';

const _name = 'JSON data workbench';
const _primarySource = '{\n  "owner": "primary",\n  "value": 1\n}';
const _secondarySource = '{\n  "owner": "secondary",\n  "value": 2\n}';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Fixture fixture;
  late PathProviderPlatform previousPaths;
  StudioProfile? previousProfile;

  setUpAll(() async {
    fixture = await _Fixture.create();
    previousPaths = PathProviderPlatform.instance;
    PathProviderPlatform.instance = _TemporaryPaths(fixture.directory.path);
    // Home uses WorkspaceStore.instance. Resolve its real AppPaths dependency
    // into this file's isolated temporary directory before mounting any UI.
    expect(await AppPaths.storageDirectory(), fixture.directory.path);
    await TaskActivityService.instance.initialize();
    await WorkspaceStore.instance.load();
  });

  setUp(() {
    previousProfile = StudioProfile.current;
    StudioProfile.current = jsonProfile;
  });
  tearDown(() => StudioProfile.current = previousProfile);
  tearDownAll(() async {
    PathProviderPlatform.instance = previousPaths;
    fixture.disposeStores();
    await fixture.directory.delete(recursive: true);
  });

  testWidgets(
    'real JSON Home saves a named workspace and reopens both owners after app reconstruction',
    (tester) async {
      tester.view.physicalSize = const Size(1100, 850);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(() => fixture.unmountAndDrain(tester));
      expect(StudioProfile.current, same(jsonProfile));
      expect(jsonProfile.productKey, StudioProductCatalog.jsonKey);
      expect(jsonProfile.offlineOnly, isTrue);

      await fixture.mountHome(tester);
      expect(find.text('云端项目'), findsNothing);
      expect(find.byType(FilterChip), findsNothing);
      await tester.tap(find.text(fixture.primary.name).hitTestable());
      await _until(
        tester,
        () => fixture.editor(tester)?.files.length == 1,
        'Opening the JSON Home project did not restore its primary document.',
      );
      await fixture.showTree(tester);
      expect(find.byType(FileExplorer).hitTestable(), findsOneWidget);

      // This must be the named dialog exposed by the actual child profile.
      // A legacy membership-only dialog has no name field and fails here.
      final workspaceAction = find.descendant(
        of: find.byType(FileExplorer),
        matching: find.byWidgetPredicate(
          (widget) => widget is IconButton && widget.tooltip == '工作区项目',
        ),
      );
      await _until(
        tester,
        () => workspaceAction.hitTestable().evaluate().isNotEmpty,
        'The actual workspace settings button did not become interactive.',
      );
      await tester.tap(workspaceAction.hitTestable());
      final nameField = find.byKey(const ValueKey('workspace-name-field'));
      await _until(
        tester,
        () => nameField.evaluate().isNotEmpty,
        'The real JSON profile did not expose named workspace saving.',
      );
      await tester.pump(const Duration(milliseconds: 300));
      final secondaryChoice = find.byKey(
        ValueKey('workspace-project-${fixture.secondary.id}'),
      );
      expect(tester.widget<CheckboxListTile>(secondaryChoice).value, isFalse);
      await tester.tap(secondaryChoice);
      await tester.enterText(nameField, _name);
      await tester.tap(find.widgetWithText(FilledButton, '保存'));
      await _until(
        tester,
        () =>
            WorkspaceStore.instance.workspaces.length == 1 &&
            find.byType(AlertDialog).evaluate().isEmpty &&
            fixture.root(fixture.secondary).evaluate().isNotEmpty,
        'Saving the JSON workspace did not attach both project roots.',
      );
      await tester.pump(const Duration(milliseconds: 300));
      final saved = WorkspaceStore.instance.workspaces.single;
      expect(saved.name, _name);
      expect(saved.memberPaths, [fixture.primary.path, fixture.secondary.path]);
      expect(fixture.document(saved).existsSync(), isTrue);
      expect(
        tester.widget<EditorPage>(find.byType(EditorPage)).workspace?.id,
        saved.id,
      );
      await fixture.drain(tester);
      final projectHistory = fixture.history.readAsBytesSync();

      // Both file operations and tree changes go through the actual editor.
      await fixture.expand(tester, fixture.primary);
      await fixture.expand(tester, fixture.secondary);
      await tester.tap(fixture.entry(fixture.secondary, 'data.json'));
      await _until(
        tester,
        () =>
            fixture.editor(tester)?.files.length == 2 &&
            fixture.editor(tester)?.current?.projectRootPath ==
                fixture.secondary.path,
        'The secondary data.json did not open with its own owner.',
      );
      final editor = fixture.editor(tester)!;
      expect(editor.files.map((file) => file.path), [
        fixture.source(fixture.primary).path,
        fixture.source(fixture.secondary).path,
      ]);
      editor.files.first.controller.selection =
          const CodeLineSelection.collapsed(index: 1, offset: 3);
      editor.files.last.controller.selection =
          const CodeLineSelection.collapsed(index: 2, offset: 4);
      await tester.pump();
      await tester.tap(find.byTooltip('收起文件树').hitTestable());
      await tester.pump(const Duration(milliseconds: 300));
      await fixture.showTree(tester);
      expect(fixture.entry(fixture.primary, 'detail.json'), findsOneWidget);
      expect(fixture.entry(fixture.secondary, 'detail.json'), findsOneWidget);

      // Destroy QfliApp and its retained editor controller, not just the sidebar.
      await fixture.unmountAndDrain(tester);
      final latest = WorkspaceStore.instance.byId(saved.id)!;
      expect(latest.session.documents.map((document) => document.projectPath), [
        fixture.primary.path,
        fixture.secondary.path,
      ]);
      expect(latest.session.documents.map((document) => document.isActive), [
        false,
        true,
      ]);
      expect(latest.session.documents.first.cursor.baseIndex, 1);
      expect(latest.session.documents.first.cursor.baseOffset, 3);
      expect(latest.session.documents.last.cursor.baseIndex, 2);
      expect(latest.session.documents.last.cursor.baseOffset, 4);
      for (final project in [fixture.primary, fixture.secondary]) {
        expect(latest.session.expandedDirs[project.path], contains('nested'));
      }
      // Named sessions own their state; editing their tabs/tree does not
      // overwrite the project's pre-existing standalone history.
      expect(fixture.history.readAsBytesSync(), orderedEquals(projectHistory));
      fixture.expectSourceBytes();

      await tester.runAsync(() async {
        await WorkspaceStore.instance.load(force: true);
        await fixture.recreateStores();
      });
      await fixture.mountHome(tester);
      final workspaceTab = find.widgetWithText(Tab, '工作区');
      expect(workspaceTab, findsOneWidget);
      await tester.tap(workspaceTab);
      await _until(
        tester,
        () => find.text(_name).hitTestable().evaluate().isNotEmpty,
        'The actual JSON Home workspace scope did not list the saved document.',
      );
      await tester.tap(find.text(_name).hitTestable());
      await _until(
        tester,
        () =>
            fixture.editor(tester)?.files.length == 2 &&
            fixture.editor(tester)?.current?.projectRootPath ==
                fixture.secondary.path,
        'The actual Home card did not reconstruct the named JSON session.',
      );
      final restored = fixture.editor(tester)!;
      expect(restored, isNot(same(editor)));
      expect(
        tester.widget<EditorPage>(find.byType(EditorPage)).workspace?.id,
        saved.id,
      );
      expect(restored.files.map((file) => file.path), [
        fixture.source(fixture.primary).path,
        fixture.source(fixture.secondary).path,
      ]);
      expect(restored.files.map((file) => file.ownerProjectName), [
        fixture.primary.name,
        fixture.secondary.name,
      ]);
      expect(
        restored.files.every((file) => file.projectType == 'json'),
        isTrue,
      );
      expect(restored.files.every((file) => !file.dirty), isTrue);
      expect(restored.files.first.controller.text, _primarySource);
      expect(restored.files.last.controller.text, _secondarySource);
      expect(restored.files.first.controller.selection.baseIndex, 1);
      expect(restored.files.first.controller.selection.baseOffset, 3);
      expect(restored.current!.controller.selection.baseIndex, 2);
      expect(restored.current!.controller.selection.baseOffset, 4);
      await fixture.showTree(tester);
      await _until(
        tester,
        () =>
            fixture
                .entry(fixture.primary, 'detail.json')
                .evaluate()
                .isNotEmpty &&
            fixture
                .entry(fixture.secondary, 'detail.json')
                .evaluate()
                .isNotEmpty,
        'The named workspace did not restore both roots\' expanded directories.',
      );
      fixture.expectSourceBytes();
      expect(StudioProfile.current, same(jsonProfile));
      expect(tester.takeException(), isNull);
    },
  );
}

class _Fixture {
  _Fixture(this.directory, this.primary, this.secondary);

  final Directory directory;
  final Project primary;
  final Project secondary;
  late ProjectStore store;
  late AuthStore auth;
  late SettingsStore settings;

  File get registry => File(p.join(directory.path, 'projects.json'));
  File get history => File(p.join(primary.path, 'history.json'));
  File source(Project project) => File(p.join(project.path, 'data.json'));
  File document(SavedWorkspace workspace) =>
      File(p.join(directory.path, 'workspaces', '${workspace.id}.json'));
  Finder root(Project project) =>
      find.byKey(ValueKey('workspace-root-${project.path}'));
  Finder entry(Project project, String name) =>
      find.descendant(of: root(project), matching: find.text(name));

  static Future<_Fixture> create() async {
    final directory = await Directory.systemTemp.createTemp('json_named_ws_');
    Project project(String name, String folder) => Project.create(
      name: name,
      path: p.join(directory.path, folder),
      language: 'JSON',
      type: 'json',
    );
    final fixture = _Fixture(
      directory,
      project('Primary JSON', 'primary'),
      project('Secondary JSON', 'secondary'),
    );
    for (final project in [fixture.primary, fixture.secondary]) {
      await Directory(p.join(project.path, 'nested')).create(recursive: true);
      await File(
        p.join(project.path, 'nested', 'detail.json'),
      ).writeAsString('{"nested":true}');
    }
    await fixture.source(fixture.primary).writeAsString(_primarySource);
    await fixture.source(fixture.secondary).writeAsString(_secondarySource);
    await fixture.registry.writeAsString(
      jsonEncode({
        'projects': [fixture.primary.toJson(), fixture.secondary.toJson()],
      }),
    );
    await ProjectHistory.save(
      fixture.primary.path,
      cursors: const {},
      openFiles: const ['data.json'],
      activeFile: 'data.json',
    );
    await fixture._createStores();
    return fixture;
  }

  Future<void> _createStores() async {
    store = ProjectStore(storageFile: registry);
    auth = AuthStore();
    settings = SettingsStore();
    await store.load();
  }

  Future<void> recreateStores() async {
    disposeStores();
    await _createStores();
  }

  void disposeStores() {
    store.dispose();
    auth.dispose();
    settings.dispose();
  }

  Future<void> mountHome(WidgetTester tester) async {
    await tester.pumpWidget(
      QfliApp(store: store, auth: auth, settings: settings),
    );
    await _until(
      tester,
      () => find.text(primary.name).hitTestable().evaluate().isNotEmpty,
      'The actual JSON Home did not show its registered project.',
    );
  }

  EditorController? editor(WidgetTester tester) {
    final bar = find.byType(EditorProblemsBar).hitTestable();
    if (bar.evaluate().isEmpty) return null;
    return tester.widget<EditorProblemsBar>(bar).analysis.editor;
  }

  Future<void> showTree(WidgetTester tester) async {
    await _until(
      tester,
      () =>
          find.byTooltip('打开文件树').hitTestable().evaluate().isNotEmpty ||
          find.byTooltip('收起文件树').hitTestable().evaluate().isNotEmpty,
      'The editor tree toggle did not become interactive.',
    );
    final closed = find.byTooltip('打开文件树').hitTestable();
    if (closed.evaluate().isNotEmpty) await tester.tap(closed);
    // Start AnimatedAlign at the current fake time before advancing it. A
    // single duration pump starts the animation at its end time; the root's
    // center can then be visible while the settings button is still clipped.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    await _until(
      tester,
      () => root(primary).hitTestable().evaluate().isNotEmpty,
      'The primary project tree did not open.',
    );
  }

  Future<void> expand(WidgetTester tester, Project project) async {
    await _until(
      tester,
      () => entry(project, 'nested').evaluate().isNotEmpty,
      'The ${project.name} folder did not load.',
    );
    await tester.tap(entry(project, 'nested'));
    await _until(
      tester,
      () => entry(project, 'detail.json').evaluate().isNotEmpty,
      'The ${project.name} folder did not expand.',
    );
  }

  Future<void> unmountAndDrain(WidgetTester tester) async {
    FocusManager.instance.primaryFocus?.unfocus();
    await tester.pump();
    await tester.pumpWidget(const SizedBox.shrink());
    await drain(tester);
  }

  Future<void> drain(WidgetTester tester) async {
    var done = false;
    final pending = Future.wait([
      WorkspaceStore.instance.settle(),
      ProjectHistory.load(primary.path),
      store.refresh(),
    ]);
    pending.then((_) => done = true);
    await _until(
      tester,
      () => done,
      'Queued workspace/history writes did not drain.',
    );
    await pending;
  }

  void expectSourceBytes() {
    expect(source(primary).readAsBytesSync(), utf8.encode(_primarySource));
    expect(source(secondary).readAsBytesSync(), utf8.encode(_secondarySource));
    for (final project in [primary, secondary]) {
      expect(
        File(p.join(project.path, 'nested', 'detail.json')).readAsBytesSync(),
        utf8.encode('{"nested":true}'),
      );
    }
  }
}

class _TemporaryPaths extends PathProviderPlatform {
  _TemporaryPaths(this.root);
  final String root;

  @override
  Future<String?> getApplicationSupportPath() async => root;
  @override
  Future<String?> getApplicationDocumentsPath() async => root;
  @override
  Future<String?> getTemporaryPath() async => p.join(root, 'tmp');
}

Future<void> _until(
  WidgetTester tester,
  bool Function() complete,
  String reason,
) async {
  for (var attempt = 0; attempt < 240; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (complete()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(complete(), isTrue, reason: reason);
}
