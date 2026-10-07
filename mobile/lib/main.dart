import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'app.dart';
import 'services/secure_store.dart';
import 'state/app_state.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // The camera guide and layouts are designed for portrait use.
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  runApp(
    ChangeNotifierProvider<AppState>(
      create: (_) => AppState(SecureStore())..load(),
      child: const GlowrithmApp(),
    ),
  );
}
