import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../state/app_state.dart';
import '../widgets/common.dart';

/// Explicit, informed consent before any personal data is processed (UU PDP No. 27/2022).
class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});

  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  bool _agreed = false;
  bool _saving = false;

  Future<void> _continue() async {
    setState(() => _saving = true);
    await context.read<AppState>().grantConsent();
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
          children: [
            const BrandMark(),
            const SizedBox(height: 28),
            Text('Before we look at your skin', style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(
              'Glowrithm estimates your skin type from a face photo and suggests suitable skincare '
              'ingredients. This is exactly what happens with your data.',
              style: text.bodyMedium?.copyWith(color: Palette.slate, height: 1.45),
            ),
            const SizedBox(height: 20),
            const _PolicyItem(
              icon: Icons.face,
              title: 'What we collect',
              body: 'One face photo per analysis, plus your age and biological sex.',
            ),
            const _PolicyItem(
              icon: Icons.memory,
              title: 'How the photo is processed',
              body: "It is sent over an encrypted connection, analysed in the server's memory and discarded "
                  'right away. It is never stored or logged.',
            ),
            const _PolicyItem(
              icon: Icons.lock_outline,
              title: 'What stays on your phone',
              body: 'Your profile and the results you save are encrypted on this device. Photos are never saved.',
            ),
            const _PolicyItem(
              icon: Icons.delete_outline,
              title: 'Your rights',
              body: 'View, edit or delete your data, or withdraw consent at any time in Profile.',
            ),
            const _PolicyItem(
              icon: Icons.local_hospital_outlined,
              title: 'Not a medical diagnosis',
              body: 'Results support your skincare choices. For skin conditions, see a dermatologist.',
            ),
            CheckboxListTile(
              value: _agreed,
              onChanged: _saving ? null : (value) => setState(() => _agreed = value ?? false),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              title: const Text(
                'I agree to the processing of my photo and profile data for skin analysis as described above '
                '(UU PDP No. 27/2022).',
              ),
            ),
            const SizedBox(height: 12),
            FilledButton(onPressed: _agreed && !_saving ? _continue : null, child: const Text('Agree and continue')),
          ],
        ),
      ),
    );
  }
}

class _PolicyItem extends StatelessWidget {
  const _PolicyItem({required this.icon, required this.title, required this.body});

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: Palette.mist, borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: Palette.lagoon, size: 22),
          ),
          const SizedBox(width: 14),
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
