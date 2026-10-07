import 'package:flutter/material.dart';

/// Colour tokens taken from the CD-3 interface mock-ups: deep teal on clean, light surfaces.
class Palette {
  Palette._();

  static const Color lagoon = Color(0xFF0E5C58);
  static const Color lagoonDark = Color(0xFF0A4441);
  static const Color mist = Color(0xFFE3F0ED);
  static const Color canvas = Color(0xFFF5F8F7);
  static const Color ink = Color(0xFF15211F);
  static const Color slate = Color(0xFF5A6B68);
  static const Color line = Color(0xFFDCE7E4);
  static const Color amber = Color(0xFFA86B12);
  static const Color amberSoft = Color(0xFFFFF4E0);
  static const Color danger = Color(0xFFB3261E);
}

ThemeData buildTheme() {
  final scheme = ColorScheme.fromSeed(seedColor: Palette.lagoon, primary: Palette.lagoon, surface: Colors.white);
  final base = ThemeData(useMaterial3: true, colorScheme: scheme, scaffoldBackgroundColor: Palette.canvas);
  const shape = RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(14)));
  const label = TextStyle(fontSize: 16, fontWeight: FontWeight.w600);
  return base.copyWith(
    textTheme: base.textTheme.apply(bodyColor: Palette.ink, displayColor: Palette.ink),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(minimumSize: const Size(64, 52), shape: shape, textStyle: label),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(64, 52),
        shape: shape,
        textStyle: label,
        side: const BorderSide(color: Palette.lagoon),
      ),
    ),
    navigationBarTheme: const NavigationBarThemeData(backgroundColor: Colors.white, indicatorColor: Palette.mist),
    snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
  );
}
