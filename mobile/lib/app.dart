import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme.dart';
import 'screens/consent_screen.dart';
import 'screens/home_shell.dart';
import 'screens/profile_setup_screen.dart';
import 'state/app_state.dart';

class GlowrithmApp extends StatelessWidget {
  const GlowrithmApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Glowrithm',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: const _StartGate(),
    );
  }
}

/// Chooses the first screen from stored state: consent, then profile, then the main app.
class _StartGate extends StatelessWidget {
  const _StartGate();

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    if (!state.isLoaded) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (!state.hasConsent) return const ConsentScreen();
    if (state.profile == null) return const ProfileSetupScreen();
    return const HomeShell();
  }
}
