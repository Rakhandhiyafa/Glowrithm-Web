import 'package:flutter/material.dart';

import '../core/format.dart';
import '../core/theme.dart';
import '../models/analysis_result.dart';
import '../widgets/common.dart';
import '../widgets/gradcam_viewer.dart';
import 'recommendations_screen.dart';

/// Scan results (CD-3 Figure 3.4): Grad-CAM map, skin type, confidence and the next step.
class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key, required this.result, this.fromHistory = false});

  final AnalysisResult result;
  final bool fromHistory;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final face = result.faceImageB64;
    final heat = result.heatmapImageB64;
    final qualityIssues = result.quality?.checks
            .where((check) => check.status != 'ok' && check.name != 'face')
            .map((check) => check.message)
            .toList() ??
        const <String>[];
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          tooltip: 'Close',
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
        ),
        title: Text(fromHistory ? 'Saved result' : 'Scan results'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
        children: [
          if (result.demoMode) ...[
            const NoteCard(
              icon: Icons.science_outlined,
              tone: NoteTone.warning,
              title: 'Demo mode',
              body: 'The server is running an untrained demo model, so this result is random. Use it only to test the app.',
            ),
            const SizedBox(height: 12),
          ],
          Text(
            fromHistory ? 'Saved on ${formatDateTime(result.createdAt)}' : 'Here is what the model found in your photo.',
            style: text.bodyMedium?.copyWith(color: Palette.slate),
          ),
          const SizedBox(height: 14),
          SectionCard(
            icon: Icons.thermostat,
            title: 'Grad-CAM heat map',
            child: face != null && heat != null
                ? GradCamViewer(faceBase64: face, heatmapBase64: heat)
                : const NoteCard(
                    icon: Icons.lock_outline,
                    title: 'Images are not stored',
                    body: 'Photos and heat maps are never saved, to protect your privacy. Run a new scan to see the heat map.',
                  ),
          ),
          const SizedBox(height: 14),
          _ClassificationCard(result: result),
          if (result.lowConfidence) ...[
            const SizedBox(height: 12),
            const NoteCard(
              icon: Icons.warning_amber_rounded,
              tone: NoteTone.warning,
              title: 'Low confidence',
              body: 'Retake the photo facing soft, even light, without makeup, before relying on this result.',
            ),
          ],
          if (!result.faceDetected) ...[
            const SizedBox(height: 12),
            const NoteCard(
              icon: Icons.face,
              tone: NoteTone.warning,
              title: 'No face detected',
              body: 'The centre of the photo was analysed instead. Fill the oval with your face for a better result.',
            ),
          ],
          if (qualityIssues.isNotEmpty) ...[
            const SizedBox(height: 12),
            NoteCard(
              icon: Icons.camera_alt_outlined,
              tone: NoteTone.warning,
              title: 'Photo quality',
              body: qualityIssues.join('\n'),
            ),
          ],
          const SizedBox(height: 14),
          SectionCard(
            icon: Icons.science_outlined,
            title: 'Next step',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(result.recommendations.summary, style: text.bodyMedium?.copyWith(height: 1.45)),
                const SizedBox(height: 14),
                FilledButton(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => RecommendationsScreen(result: result, fromHistory: fromHistory),
                    ),
                  ),
                  child: const Text('See recommended ingredients'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          DisclaimerNote(text: result.disclaimer.isEmpty ? null : result.disclaimer),
        ],
      ),
    );
  }
}

class _ClassificationCard extends StatelessWidget {
  const _ClassificationCard({required this.result});

  final AnalysisResult result;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final entries = result.probabilities.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    return SectionCard(
      icon: Icons.insights,
      title: 'Skin type',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                result.skinTypeLabel,
                style: text.headlineMedium?.copyWith(fontWeight: FontWeight.w800, color: Palette.lagoonDark),
              ),
              const SizedBox(width: 10),
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(result.skinTypeLabelId, style: text.titleMedium?.copyWith(color: Palette.slate)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(result.skinTypeDescription, style: text.bodyMedium?.copyWith(height: 1.45)),
          const SizedBox(height: 16),
          ConfidenceBar(label: 'Model confidence', value: result.confidence, emphasize: true),
          const SizedBox(height: 16),
          Text('All skin types', style: text.labelLarge?.copyWith(color: Palette.slate)),
          const SizedBox(height: 8),
          for (final entry in entries) ...[
            ConfidenceBar(label: capitalize(entry.key), value: entry.value),
            const SizedBox(height: 10),
          ],
          Text(result.explanation, style: text.bodySmall?.copyWith(color: Palette.slate, height: 1.4)),
        ],
      ),
    );
  }
}
