import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/app_paths.dart';

import '../content/json_content_repository.dart';
import 'json_catalog_verification.dart';

class JsonVerificationPage extends StatefulWidget {
  const JsonVerificationPage({super.key});
  @override
  State<JsonVerificationPage> createState() => _JsonVerificationPageState();
}

class _JsonVerificationPageState extends State<JsonVerificationPage> {
  String _status = '正在加载随包离线内容…';
  bool _passed = false;
  @override
  void initState() {
    super.initState();
    _verify();
  }

  Future<void> _verify() async {
    Map<String, Object?> result;
    try {
      final root = await AppPaths.storageDirectory();
      if (root == null) throw const FileSystemException('找不到应用可写沙盒');
      result = await verifyJsonCatalog(
        await JsonContentRepository().load(),
        root,
        progress: (status) {
          debugPrint('QFLI_JSON_VERIFY_PROGRESS $status');
          if (mounted) setState(() => _status = status);
        },
      );
      await File(
        p.join(root, 'json_verification_result.json'),
      ).writeAsString(jsonEncode(result), flush: true);
    } on Object catch (error, stack) {
      result = {'passed': false, 'error': '$error', 'stack': '$stack'};
    }
    debugPrint(
      'QFLI_JSON_VERIFY_RESULT ${jsonEncode(result)}',
      wrapWidth: 100000,
    );
    if (mounted) {
      setState(() {
        _passed = result['passed'] == true;
        _status = const JsonEncoder.withIndent('  ').convert(result);
      });
    }
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    home: Scaffold(
      appBar: AppBar(title: const Text('JSON 离线目标验证')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              _passed ? Icons.check_circle : Icons.fact_check_outlined,
              size: 36,
            ),
            const SizedBox(height: 12),
            SelectableText(_status),
          ],
        ),
      ),
    ),
  );
}
