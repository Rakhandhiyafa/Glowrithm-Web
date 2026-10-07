import 'package:flutter/material.dart';

import 'history_screen.dart';
import 'home_screen.dart';
import 'profile_screen.dart';
import 'scan_screen.dart';

/// Bottom navigation (Home, Scan, History, Profile) as in the CD-3 mock-ups.
/// Only the visible tab is built, so the camera is released when the Scan tab is left.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  void _go(int index) => setState(() => _index = index);

  @override
  Widget build(BuildContext context) {
    final Widget page = switch (_index) {
      1 => const ScanScreen(),
      2 => HistoryScreen(onStartScan: () => _go(1)),
      3 => const ProfileScreen(),
      _ => HomeScreen(onStartScan: () => _go(1)),
    };
    return Scaffold(
      body: page,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: _go,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.camera_alt_outlined), selectedIcon: Icon(Icons.camera_alt), label: 'Scan'),
          NavigationDestination(icon: Icon(Icons.history), label: 'History'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
