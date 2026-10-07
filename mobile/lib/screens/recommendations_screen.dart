import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../models/analysis_result.dart';
import '../state/app_state.dart';
import '../widgets/common.dart';
import '../widgets/ingredient_card.dart';

/// Recommended ingredients (CD-3 Figure 3.5): cleanse, treat, protect routine with BPOM status.
class RecommendationsScreen extends StatelessWidget {
  const RecommendationsScreen({super.key, required this.result, this.fromHistory = false});

  final AnalysisResult result;
  final bool fromHistory;

  Future<void> _save(BuildContext context) async {
    await context.read<AppState>().saveToHistory(result);
    if (context.mounted) showSnack(context, 'Saved to history');
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final recs = result.recommendations;
    final saved = context.watch<AppState>().isSaved(result.requestId);
    return Scaffold(
      appBar: AppBar(title: const Text('Recommended ingredients')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
        children: [
          Text(recs.headline, style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text(recs.summary, style: text.bodyMedium?.copyWith(color: Palette.slate, height: 1.45)),
          const SizedBox(height: 20),
          for (final step in recs.steps) ...[
            _StepHeader(step: step),
            const SizedBox(height: 10),
            for (final ingredient in step.ingredients) IngredientCard(ingredient: ingredient),
            const SizedBox(height: 14),
          ],
          if (recs.avoid.isNotEmpty) ...[
            SectionCard(
              icon: Icons.block,
              title: 'Avoid or use with care',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final item in recs.avoid)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item.name, style: text.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 2),
                          Text(item.reason, style: text.bodySmall?.copyWith(color: Palette.slate, height: 1.4)),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 14),
          ],
          if (recs.notes.isNotEmpty)
            SectionCard(
              icon: Icons.lightbulb_outline,
              title: 'Good habits',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [for (final note in recs.notes) BulletLine(note)],
              ),
            ),
          const SizedBox(height: 20),
          if (!fromHistory) ...[
            OutlinedButton.icon(
              onPressed: saved ? null : () => _save(context),
              icon: Icon(saved ? Icons.bookmark : Icons.bookmark_border),
              label: Text(saved ? 'Saved to history' : 'Save to history'),
            ),
            const SizedBox(height: 10),
          ],
          FilledButton(
            onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
            child: const Text('Done'),
          ),
          const SizedBox(height: 16),
          DisclaimerNote(text: result.disclaimer.isEmpty ? null : result.disclaimer),
        ],
      ),
    );
  }
}

class _StepHeader extends StatelessWidget {
  const _StepHeader({required this.step});

  final RoutineStep step;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CircleAvatar(
          radius: 15,
          backgroundColor: Palette.lagoon,
          child: Text('${step.order}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Step ${step.order}: ${step.title}', style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              Text(step.goal, style: text.bodySmall?.copyWith(color: Palette.slate)),
            ],
          ),
        ),
      ],
    );
  }
}
