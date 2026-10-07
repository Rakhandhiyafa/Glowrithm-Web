import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/config.dart';
import '../core/format.dart';
import '../core/theme.dart';
import '../models/analysis_result.dart';
import '../state/app_state.dart';
import '../widgets/common.dart';
import 'result_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key, required this.onStartScan});

  final VoidCallback onStartScan;

  @override
  Widget build(BuildContext context) {
    final history = context.watch<AppState>().history;
    final latest = history.isEmpty ? null : history.first;
    final text = Theme.of(context).textTheme;
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Row(
            children: [
              const BrandMark(compact: true),
              const Spacer(),
              IconButton(
                tooltip: 'About Glowrithm',
                icon: const Icon(Icons.info_outline),
                onPressed: () => showAboutDialog(
                  context: context,
                  applicationName: 'Glowrithm',
                  applicationVersion: AppConfig.appVersion,
                  applicationLegalese: defaultDisclaimer,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _HeroCard(onStartScan: onStartScan),
          if (latest != null) ...[const SizedBox(height: 16), _LatestResultCard(result: latest)],
          const SizedBox(height: 24),
          Text('How it works', style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          const _StepTile(
            number: 1,
            title: 'Take a clear photo',
            body: 'Face the camera in soft, even light, without makeup or glasses.',
          ),
          const _StepTile(
            number: 2,
            title: 'AI reads your skin',
            body: 'Two neural networks, ResNet50V2 and EfficientNetB0, classify your skin as dry, normal or oily.',
          ),
          const _StepTile(
            number: 3,
            title: 'See why',
            body: 'A Grad-CAM heat map highlights the areas that drove the result.',
          ),
          const _StepTile(
            number: 4,
            title: 'Get your ingredients',
            body: 'A cleanse, treat and protect routine with ingredients that suit your skin, plus their BPOM status.',
          ),
          const SizedBox(height: 16),
          const DisclaimerNote(),
        ],
      ),
    );
  }
}

class _HeroCard extends StatelessWidget {
  const _HeroCard({required this.onStartScan});

  final VoidCallback onStartScan;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: Palette.lagoon, borderRadius: BorderRadius.circular(22)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Know your skin type before you buy',
            style: text.headlineSmall?.copyWith(color: Colors.white, fontWeight: FontWeight.w700, height: 1.2),
          ),
          const SizedBox(height: 8),
          Text(
            'One photo gives you your skin type, the reason behind it and the ingredients worth looking for.',
            style: text.bodyMedium?.copyWith(color: Colors.white.withAlpha(220), height: 1.45),
          ),
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Palette.lagoon),
              onPressed: onStartScan,
              icon: const Icon(Icons.camera_alt_outlined),
              label: const Text('Start skin analysis'),
            ),
          ),
        ],
      ),
    );
  }
}

class _LatestResultCard extends StatelessWidget {
  const _LatestResultCard({required this.result});

  final AnalysisResult result;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(builder: (_) => ResultScreen(result: result, fromHistory: true)),
        ),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Palette.line),
          ),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(color: Palette.mist, borderRadius: BorderRadius.circular(14)),
                child: const Icon(Icons.history, color: Palette.lagoon),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Last saved result', style: text.labelMedium?.copyWith(color: Palette.slate)),
                    const SizedBox(height: 2),
                    Text(
                      '${result.skinTypeLabel} skin, ${percent(result.confidence)} confidence',
                      style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    Text(formatDateTime(result.createdAt), style: text.bodySmall?.copyWith(color: Palette.slate)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Palette.slate),
            ],
          ),
        ),
      ),
    );
  }
}

class _StepTile extends StatelessWidget {
  const _StepTile({required this.number, required this.title, required this.body});

  final int number;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 15,
            backgroundColor: Palette.mist,
            child: Text('$number', style: const TextStyle(color: Palette.lagoon, fontWeight: FontWeight.w700)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: text.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(body, style: text.bodyMedium?.copyWith(color: Palette.slate, height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
