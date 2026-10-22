import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:qfli_studio_core/content/content_repository.dart';

/// Product-owned, bundled curriculum. Loading never falls back to a server or
/// another product's catalog, including when an asset is missing or malformed.
class JsonContentRepository implements ContentRepository {
  JsonContentRepository({AssetBundle? bundle}) : _bundle = bundle ?? rootBundle;

  static const tutorialAsset = 'assets/content/tutorials.json';
  static const exampleAsset = 'assets/content/examples.json';
  static const auditAsset = 'assets/content/catalog_audit.json';

  final AssetBundle _bundle;
  Future<ContentCatalog>? _catalog;

  @override
  Future<ContentCatalog> load() => _catalog ??= _load();

  Future<ContentCatalog> _load() async {
    final sources = await Future.wait([
      _bundle.loadString(tutorialAsset),
      _bundle.loadString(exampleAsset),
    ]);
    return compute(_parse, sources, debugLabel: 'json-offline-curriculum');
  }

  @override
  Future<List<TutorialContent>> tutorials({
    ContentFilter filter = const ContentFilter(),
  }) async => [
    for (final tutorial in (await load()).tutorials)
      if (filter.matches(tutorial)) tutorial,
  ];

  @override
  Future<List<ExampleContent>> examples({
    ContentFilter filter = const ContentFilter(),
  }) async => [
    for (final example in (await load()).examples)
      if (filter.matches(example)) example,
  ];
}

ContentCatalog _parse(List<String> sources) => ContentCatalog.fromJson(
  tutorialsSource: sources[0],
  examplesSource: sources[1],
);
