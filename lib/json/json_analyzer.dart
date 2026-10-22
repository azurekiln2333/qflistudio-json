import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/code_analysis.dart';

import 'json_workbench.dart';

/// Checks the editor's exact in-memory snapshots, including unsaved edits.
/// Pure Dart parsing is used on every platform; no server or executable needed.
class JsonCodeAnalyzer implements CodeAnalyzer {
  const JsonCodeAnalyzer();
  @override
  Future<CodeAnalysisResult> analyze(CodeAnalysisRequest request) async {
    if (p.extension(request.activeFilePath).toLowerCase() != '.json') {
      return const CodeAnalysisResult(unavailableReason: 'JSON 版仅检查 .json 文档');
    }
    if (!request.documents.any(
      (d) => p.equals(d.path, request.activeFilePath),
    )) {
      return const CodeAnalysisResult(unavailableReason: '当前文档快照不可用');
    }
    return CodeAnalysisResult(
      diagnostics: await compute(
        _analyzeSnapshots,
        request.documents
            .where((d) => p.extension(d.path).toLowerCase() == '.json')
            .toList(),
      ),
    );
  }
}

List<CodeDiagnostic> _analyzeSnapshots(List<CodeDocumentSnapshot> documents) =>
    [
      for (final document in documents)
        for (final problem in JsonWorkbench.inspect(document.text).problems)
          CodeDiagnostic(
            filePath: document.path,
            startOffset: problem.offset,
            endOffset: problem.offset < document.text.length
                ? problem.offset + 1
                : problem.offset,
            message: problem.message,
            source: 'JSON',
            code: 'json.syntax',
          ),
    ];
