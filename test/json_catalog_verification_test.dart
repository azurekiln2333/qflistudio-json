import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_json/json/json_catalog_verification.dart';
import 'package:qfli_json/main.dart' show jsonProfile;
import 'package:qfli_studio_core/content/content_repository.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'device audit harness runs every bundled example through the real profile Run route',
    () async {
      final previous = StudioProfile.current;
      final root = Directory.systemTemp.createTempSync('json_catalog_runner_');
      try {
        StudioProfile.current = jsonProfile;
        final catalog = ContentCatalog.fromJson(
          tutorialsSource: File(
            'assets/content/tutorials.json',
          ).readAsStringSync(),
          examplesSource: File(
            'assets/content/examples.json',
          ).readAsStringSync(),
        );
        final result = await verifyJsonCatalog(catalog, root.path);
        expect(result['failures'], isEmpty);
        expect(result['passed'], isTrue);
        expect(result['examples'], 340);
        expect(result['runnerPasses'], 340);
        expect(result['lessons'], 340);
        expect(result['exerciseAnswers'], 440);
        expect(result['fixtures'], 340);
        expect(result['tools'], 16);
        expect(result['semanticOperations'], 10);
        expect(Directory('${root.path}/json_verification').listSync(), isEmpty);
      } finally {
        StudioProfile.current = previous;
        root.deleteSync(recursive: true);
      }
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );
}
