import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/format.dart';
import '../core/theme.dart';
import '../models/analysis_result.dart';
import '../state/app_state.dart';
import '../widgets/common.dart';
import 'result_screen.dart';

/// Saved results (text only, encrypted on the device). Swipe left to delete one.
class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key, required this.onStartScan});

  final VoidCallback onStartScan;

  Future<void> _deleteAll(BuildContext context) async {
    final confirmed = await confirmAction(
      context,
      title: 'Delete all saved results?',
      message: 'Every saved result on this device will be removed. This cannot be undone.',
      confirmLabel: 'Delete all',
      destructive: true,
    );
    if (confirmed && context.mounted) await context.read<AppState>().clearHistory();
  }

  @override
  Widget build(BuildContext context) {
    final history = context.watch<AppState>().history;
    final text = Theme.of(context).textTheme;
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Row(
            children: [
              Expanded(child: Text('History', style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700))),
              if (history.isNotEmpty) TextButton(onPressed: () => _deleteAll(context), child: const Text('Delete all')),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Saved results stay encrypted on this device. Photos are never saved.',
            style: text.bodySmall?.copyWith(color: Palette.slate),
          ),
          const SizedBox(height: 16),
          if (history.isEmpty)
            _EmptyHistory(onStartScan: onStartScan)
          else
            for (final result in history)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Dismissible(
                  key: ValueKey(result.requestId),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    decoration: BoxDecoration(color: Palette.danger, borderRadius: BorderRadius.circular(18)),
                    child: const Icon(Icons.delete_outline, color: Colors.white),
                  ),
                  onDismissed: (_) {
                    context.read<AppState>().deleteFromHistory(result.requestId);
                    showSnack(context, 'Result deleted');
                  },
                  child: _HistoryTile(result: result),
                ),
              ),
        ],
      ),
    );
  }
}

class _HistoryTile extends StatelessWidget {
  const _HistoryTile({required this.result});

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
          decoration: BoxDecoration(borderRadius: BorderRadius.circular(18), border: Border.all(color: Palette.line)),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: Palette.mist,
                child: Text(
                  result.skinTypeLabel.isEmpty ? '?' : result.skinTypeLabel[0],
                  style: const TextStyle(color: Palette.lagoon, fontWeight: FontWeight.w800),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${result.skinTypeLabel} (${result.skinTypeLabelId})',
                      style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    Text(
                      '${percent(result.confidence)} confidence, ${formatDateTime(result.createdAt)}',
                      style: text.bodySmall?.copyWith(color: Palette.slate),
                    ),
                  ],
                ),
              ),
              if (result.lowConfidence) const Icon(Icons.warning_amber_rounded, color: Palette.amber),
              const Icon(Icons.chevron_right, color: Palette.slate),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyHistory extends StatelessWidget {
  const _EmptyHistory({required this.onStartScan});

  final VoidCallback onStartScan;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18)),
      child: Column(
        children: [
          const Icon(Icons.history, size: 40, color: Palette.slate),
          const SizedBox(height: 10),
          Text('No saved results yet', style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text(
            'After a scan, tap "Save to history" on the recommendations page to keep the result here.',
            textAlign: TextAlign.center,
            style: text.bodyMedium?.copyWith(color: Palette.slate),
          ),
          const SizedBox(height: 16),
          FilledButton(onPressed: onStartScan, child: const Text('Start a scan')),
        ],
      ),
    );
  }
}
