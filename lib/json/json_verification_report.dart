import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;

var _runSequence = 0;

/// Invalidates an older result before running and persists failures as well.
/// Device evidence must match this runId in both the log and exported report.
Future<Map<String, Object?>> runJsonVerificationReport({
  required Future<String?> Function() storageDirectory,
  required Future<Map<String, Object?>> Function(String root) verify,
}) async {
  final started = DateTime.now().toUtc();
  final identity = <String, Object?>{
    'runId': '$pid-${started.microsecondsSinceEpoch}-${_runSequence++}',
    'startedUtc': started.toIso8601String(),
  };
  File? report;
  Map<String, Object?> result;
  try {
    final root = await storageDirectory();
    if (root == null) throw const FileSystemException('找不到应用可写沙盒');
    report = File(p.join(root, 'json_verification_result.json'));
    await report.writeAsString(
      jsonEncode({...identity, 'passed': false, 'status': 'running'}),
      flush: true,
    );
    result = await verify(root);
  } on Object catch (error, stack) {
    result = {'passed': false, 'error': '$error', 'stack': '$stack'};
  }
  result = {
    ...result,
    ...identity,
    'finishedUtc': DateTime.now().toUtc().toIso8601String(),
    'passed': result['passed'] == true,
    'status': result['passed'] == true ? 'passed' : 'failed',
  };
  if (report != null) {
    final staged = File('${report.path}.${identity['runId']}.tmp');
    try {
      // Finish and flush the new result before replacing the running/false
      // marker. Even a flush error cannot expose a successful final report.
      await staged.writeAsString(jsonEncode(result), flush: true);
      await staged.rename(report.path);
    } on Object catch (error, stack) {
      // A failed export must never be advertised as a successful audit.
      result = {
        ...identity,
        'finishedUtc': DateTime.now().toUtc().toIso8601String(),
        'passed': false,
        'status': 'failed',
        'error': '无法写入本次验证报告: $error',
        'stack': '$stack',
      };
    } finally {
      try {
        if (await staged.exists()) await staged.delete();
      } on Object catch (error) {
        result = {...result, 'cleanupError': '$error'};
      }
    }
  }
  return result;
}
