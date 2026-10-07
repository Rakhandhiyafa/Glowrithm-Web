import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:glowrithm/core/theme.dart';
import 'package:glowrithm/widgets/common.dart';

void main() {
  testWidgets('ConfidenceBar shows a rounded percentage', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildTheme(),
        home: const Scaffold(body: ConfidenceBar(label: 'Model confidence', value: 0.934)),
      ),
    );
    expect(find.text('93%'), findsOneWidget);
    expect(find.text('Model confidence'), findsOneWidget);
  });
}
