import 'dart:io';

import 'package:flutter/material.dart';

import '../widgets/common.dart';
import 'analyzing_screen.dart';

/// Lets the user check the photo before it is sent (CD-3 flowchart: "Konfirmasi & Kirim").
class ConfirmPhotoScreen extends StatelessWidget {
  const ConfirmPhotoScreen({super.key, required this.imagePath});

  final String imagePath;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Check your photo')),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: Image.file(File(imagePath), fit: BoxFit.cover, width: double.infinity),
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  BulletLine('Your whole face is visible and centred'),
                  BulletLine('Soft, even daylight without flash glare or strong shadows'),
                  BulletLine('Clean skin: no makeup, filters or beauty mode'),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Retake')),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: FilledButton(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(builder: (_) => AnalyzingScreen(imagePath: imagePath)),
                      ),
                      child: const Text('Analyze photo'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
