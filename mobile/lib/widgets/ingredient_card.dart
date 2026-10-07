import 'package:flutter/material.dart';

import '../core/theme.dart';
import '../models/analysis_result.dart';
import 'common.dart';

IconData ingredientIcon(String id) {
  switch (id) {
    case 'salicylic_acid':
      return Icons.cleaning_services_outlined;
    case 'zinc_pca':
      return Icons.healing_outlined;
    case 'sunscreen':
      return Icons.wb_sunny_outlined;
    case 'hyaluronic_acid':
      return Icons.water_drop_outlined;
    case 'ceramide':
      return Icons.shield_outlined;
    case 'glycerin':
      return Icons.opacity;
    case 'shea_butter':
      return Icons.spa_outlined;
    case 'vitamin_c':
      return Icons.auto_awesome;
    default:
      return Icons.science_outlined;
  }
}

class Pill extends StatelessWidget {
  const Pill({super.key, required this.text, required this.foreground, required this.background});

  final String text;
  final Color foreground;
  final Color background;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: background, borderRadius: BorderRadius.circular(999)),
      child: Text(text, style: TextStyle(color: foreground, fontSize: 12, fontWeight: FontWeight.w600)),
    );
  }
}

class RegulatoryPill extends StatelessWidget {
  const RegulatoryPill({super.key, required this.info});

  final RegulatoryInfo info;

  @override
  Widget build(BuildContext context) {
    Color foreground = Palette.danger;
    Color background = const Color(0xFFFDE7E5);
    if (info.status == 'permitted') {
      foreground = const Color(0xFF1E6B3A);
      background = const Color(0xFFE3F4E8);
    } else if (info.status == 'restricted') {
      foreground = Palette.amber;
      background = Palette.amberSoft;
    }
    return Pill(text: 'BPOM: ${info.label}', foreground: foreground, background: background);
  }
}

/// One recommended ingredient; tap for benefits, usage, cautions, BPOM status and evidence.
class IngredientCard extends StatelessWidget {
  const IngredientCard({super.key, required this.ingredient});

  final IngredientRec ingredient;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => _showDetails(context),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Palette.line),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: Palette.mist,
                      child: Icon(ingredientIcon(ingredient.id), color: Palette.lagoon),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(ingredient.name, style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                          if (ingredient.alias != null)
                            Text(ingredient.alias!, style: text.bodySmall?.copyWith(color: Palette.slate)),
                        ],
                      ),
                    ),
                    const Icon(Icons.chevron_right, color: Palette.slate),
                  ],
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    Pill(text: '${ingredient.matchPercent}% match', foreground: Colors.white, background: Palette.lagoon),
                    RegulatoryPill(info: ingredient.regulatory),
                  ],
                ),
                const SizedBox(height: 10),
                Text(ingredient.role, style: text.bodyMedium?.copyWith(height: 1.4)),
                for (final note in ingredient.personalNotes) ...[
                  const SizedBox(height: 8),
                  BulletLine(note, icon: Icons.person_outline),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showDetails(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      backgroundColor: Colors.white,
      builder: (sheetContext) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.7,
        minChildSize: 0.4,
        maxChildSize: 0.95,
        builder: (context, controller) => _IngredientDetails(ingredient: ingredient, controller: controller),
      ),
    );
  }
}

class _IngredientDetails extends StatelessWidget {
  const _IngredientDetails({required this.ingredient, required this.controller});

  final IngredientRec ingredient;
  final ScrollController controller;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final heading = text.titleSmall?.copyWith(fontWeight: FontWeight.w700);
    final regulatory = ingredient.regulatory;
    return ListView(
      controller: controller,
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
      children: [
        Text(ingredient.name, style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
        if (ingredient.inci != null) Text('INCI: ${ingredient.inci}', style: text.bodySmall?.copyWith(color: Palette.slate)),
        const SizedBox(height: 12),
        Wrap(spacing: 8, runSpacing: 8, children: [
          Pill(text: '${ingredient.matchPercent}% match', foreground: Colors.white, background: Palette.lagoon),
          RegulatoryPill(info: regulatory),
        ]),
        const SizedBox(height: 16),
        Text(ingredient.role, style: text.bodyLarge),
        const SizedBox(height: 16),
        Text('Benefits', style: heading),
        const SizedBox(height: 8),
        for (final benefit in ingredient.benefits) BulletLine(benefit),
        const SizedBox(height: 8),
        Text('How to use', style: heading),
        const SizedBox(height: 6),
        Text(ingredient.howToUse, style: text.bodyMedium?.copyWith(height: 1.4)),
        if (ingredient.caution != null) ...[
          const SizedBox(height: 16),
          NoteCard(icon: Icons.warning_amber_rounded, tone: NoteTone.warning, title: 'Caution', body: ingredient.caution!),
        ],
        for (final note in ingredient.personalNotes) ...[
          const SizedBox(height: 12),
          NoteCard(icon: Icons.person_outline, title: 'For your profile', body: note),
        ],
        const SizedBox(height: 16),
        Text('Regulatory status (BPOM)', style: heading),
        const SizedBox(height: 6),
        Text(regulatory.note, style: text.bodyMedium?.copyWith(height: 1.4)),
        const SizedBox(height: 4),
        Text(regulatory.reference, style: text.bodySmall?.copyWith(color: Palette.slate)),
        if (!regulatory.verified)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'Not yet verified against the regulation annex by the Glowrithm team.',
              style: text.bodySmall?.copyWith(color: Palette.amber),
            ),
          ),
        if (ingredient.evidence.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('Evidence', style: heading),
          const SizedBox(height: 6),
          for (final item in ingredient.evidence) BulletLine(item, icon: Icons.menu_book_outlined),
        ],
      ],
    );
  }
}
