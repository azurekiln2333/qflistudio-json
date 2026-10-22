import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_json/json/json_schema.dart';
import 'package:qfli_json/json/json_workbench.dart';
import 'package:qfli_json/main.dart' show jsonProfile;

void main() {
  test('JSON profile keeps every shared online surface disabled', () {
    expect(jsonProfile.isOffline, isTrue);
    expect(jsonProfile.offlineOnly, isTrue);
    expect(jsonProfile.supportedFileExtensions, ['.json']);
  });

  test('offline release manifests do not request internet access', () {
    final ohos = File('ohos/entry/src/main/module.json5').readAsStringSync();
    final android = File(
      'android/app/src/main/AndroidManifest.xml',
    ).readAsStringSync();

    expect(ohos, isNot(contains('ohos.permission.INTERNET')));
    expect(android, isNot(contains('android.permission.INTERNET')));
    // File selection, clipboard and local sharing remain available offline.
    expect(ohos, contains('ohos.permission.READ_PASTEBOARD'));
  });

  test('JSON data and schema references never create an HTTP client', () {
    var clientsCreated = 0;
    HttpOverrides.runZoned(
      () {
        final document = JsonWorkbench.inspect(
          '{"endpoint":"https://example.invalid/api","enabled":true}',
        );
        expect(document.valid, isTrue);
        expect(
          JsonWorkbench.select(document.value, '/endpoint'),
          'https://example.invalid/api',
        );
        expect(
          LocalJsonSchema.validate(document.value, {
            r'$schema': 'https://json-schema.org/draft/2020-12/schema',
            r'$defs': {
              'urlText': {'type': 'string'},
            },
            'type': 'object',
            'properties': {
              'endpoint': {r'$ref': r'#/$defs/urlText'},
            },
          }),
          isEmpty,
        );
        for (final reference in [
          'https://example.invalid/schema.json',
          'http://127.0.0.1:8080/schema.json',
          '//example.invalid/schema.json',
          'file:///private/schema.json',
          '../schema.json',
        ]) {
          expect(
            LocalJsonSchema.validate(document.value, {r'$ref': reference}),
            isNotEmpty,
            reason: 'External schema reference must fail locally: $reference',
          );
        }
      },
      createHttpClient: (_) {
        clientsCreated++;
        throw StateError('The offline JSON workbench attempted HTTP access');
      },
    );
    expect(clientsCreated, 0);
  });

  test('active OHOS host does not register login or external URL routing', () {
    final entry = File(
      'ohos/entry/src/main/ets/entryability/EntryAbility.ets',
    ).readAsStringSync();

    expect(entry, isNot(contains('qflistudio/huawei_account')));
    expect(entry, isNot(contains('HuaweiIDProvider')));
    expect(entry, isNot(contains('AuthenticationController')));
    expect(entry, isNot(matches(RegExp(r'\brouter\s*\.\s*pushUrl\s*\('))));
    expect(entry, isNot(matches(RegExp(r'\.\s*startAbility\s*\('))));
    expect(entry, contains('handlePickerCall'));
    expect(entry, contains('systemShare.ShareController'));
  });
}
