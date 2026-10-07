import 'package:flutter/material.dart';

import '../core/format.dart';
import '../core/theme.dart';

const String defaultDisclaimer =
    'Glowrithm supports your choice of skincare ingredients. It does not diagnose skin diseases '
    'and is not a substitute for advice from a dermatologist.';

class BrandMark extends StatelessWidget {
  const BrandMark({super.key, this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    final size = compact ? 34.0 : 44.0;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(color: Palette.lagoon, borderRadius: BorderRadius.circular(size * 0.3)),
          child: Icon(Icons.auto_awesome, color: Colors.white, size: size * 0.55),
        ),
        const SizedBox(width: 10),
        Text(
          'Glowrithm',
          style: TextStyle(
            fontSize: compact ? 20 : 24,
            fontWeight: FontWeight.w800,
            color: Palette.lagoonDark,
            letterSpacing: -0.3,
          ),
        ),
      ],
    );
  }
}

class SectionCard extends StatelessWidget {
  const SectionCard({super.key, required this.title, required this.child, this.icon, this.trailing});

  final String title;
  final Widget child;
  final IconData? icon;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Palette.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              if (icon != null) ...[Icon(icon, size: 20, color: Palette.lagoon), const SizedBox(width: 8)],
              Expanded(
                child: Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              ),
              if (trailing != null) trailing!,
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class ConfidenceBar extends StatelessWidget {
  const ConfidenceBar({super.key, required this.label, required this.value, this.emphasize = false});

  final String label;
  final double value;
  final bool emphasize;

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: emphasize ? FontWeight.w700 : FontWeight.w400,
        );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(children: [Expanded(child: Text(label, style: style)), Text(percent(value), style: style)]),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: LinearProgressIndicator(
            value: value.clamp(0.0, 1.0).toDouble(),
            minHeight: emphasize ? 10 : 6,
            backgroundColor: Palette.mist,
            color: emphasize ? Palette.lagoon : Palette.slate,
          ),
        ),
      ],
    );
  }
}

enum NoteTone { info, warning }

class NoteCard extends StatelessWidget {
  const NoteCard({super.key, required this.icon, required this.title, required this.body, this.tone = NoteTone.info});

  final IconData icon;
  final String title;
  final String body;
  final NoteTone tone;

  @override
  Widget build(BuildContext context) {
    final warning = tone == NoteTone.warning;
    final text = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: warning ? Palette.amberSoft : Palette.mist,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: warning ? Palette.amber : Palette.lagoon),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: text.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(body, style: text.bodySmall?.copyWith(height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class BulletLine extends StatelessWidget {
  const BulletLine(this.text, {super.key, this.icon = Icons.check_circle_outline});

  final String text;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: Palette.lagoon),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.4))),
        ],
      ),
    );
  }
}

class DisclaimerNote extends StatelessWidget {
  const DisclaimerNote({super.key, this.text});

  final String? text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.info_outline, size: 16, color: Palette.slate),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text ?? defaultDisclaimer,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Palette.slate, height: 1.4),
          ),
        ),
      ],
    );
  }
}

void showSnack(BuildContext context, String message) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(message)));
}

Future<bool> confirmAction(
  BuildContext context, {
  required String title,
  required String message,
  required String confirmLabel,
  bool destructive = false,
}) async {
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel')),
        FilledButton(
          style: FilledButton.styleFrom(
            minimumSize: const Size(64, 44),
            backgroundColor: destructive ? Palette.danger : null,
          ),
          onPressed: () => Navigator.of(dialogContext).pop(true),
          child: Text(confirmLabel),
        ),
      ],
    ),
  );
  return confirmed ?? false;
}
