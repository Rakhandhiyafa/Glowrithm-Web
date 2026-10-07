import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/config.dart';
import '../core/format.dart';
import '../core/theme.dart';
import '../services/api_service.dart';
import '../state/app_state.dart';
import '../widgets/common.dart';
import 'profile_setup_screen.dart';

/// Profile, privacy controls (UU PDP rights) and server settings.
class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  Future<void> _deleteHistory(BuildContext context) async {
    final confirmed = await confirmAction(
      context,
      title: 'Delete saved results?',
      message: 'Every saved result on this device will be removed.',
      confirmLabel: 'Delete',
      destructive: true,
    );
    if (confirmed && context.mounted) await context.read<AppState>().clearHistory();
  }

  Future<void> _withdraw(BuildContext context) async {
    final confirmed = await confirmAction(
      context,
      title: 'Withdraw consent?',
      message: 'Your profile and saved results will be erased from this device and you will return to the consent screen.',
      confirmLabel: 'Withdraw and erase',
      destructive: true,
    );
    if (confirmed && context.mounted) await context.read<AppState>().withdrawConsentAndErase();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final profile = state.profile;
    final consent = state.consent;
    if (profile == null || consent == null) return const SizedBox.shrink();
    final text = Theme.of(context).textTheme;
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Text('Profile', style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          SectionCard(
            icon: Icons.person_outline,
            title: 'Your details',
            trailing: TextButton.icon(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(builder: (_) => const ProfileSetupScreen(editing: true)),
              ),
              icon: const Icon(Icons.edit_outlined, size: 18),
              label: const Text('Edit'),
            ),
            child: Column(
              children: [
                _InfoRow(label: 'Age', value: '${profile.age} years'),
                _InfoRow(label: 'Biological sex', value: profile.sexLabel),
                if (profile.guardianConsent) const _InfoRow(label: 'Guardian consent', value: 'Given'),
              ],
            ),
          ),
          const SizedBox(height: 14),
          SectionCard(
            icon: Icons.privacy_tip_outlined,
            title: 'Privacy and data',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _InfoRow(label: 'Consent given', value: formatDateTime(consent.grantedAt)),
                _InfoRow(label: 'Saved results', value: '${state.history.length}'),
                const SizedBox(height: 4),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.delete_outline),
                  title: const Text('Delete saved results'),
                  onTap: state.history.isEmpty ? null : () => _deleteHistory(context),
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.logout, color: Palette.danger),
                  title: const Text('Withdraw consent and erase data', style: TextStyle(color: Palette.danger)),
                  subtitle: const Text('Removes your profile and history from this device.'),
                  onTap: () => _withdraw(context),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          const SectionCard(icon: Icons.dns_outlined, title: 'Server settings', child: _ServerSettings()),
          const SizedBox(height: 14),
          SectionCard(
            icon: Icons.info_outline,
            title: 'About',
            child: Text(
              'Glowrithm ${AppConfig.appVersion}. $defaultDisclaimer',
              style: text.bodySmall?.copyWith(color: Palette.slate, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(child: Text(label, style: text.bodyMedium?.copyWith(color: Palette.slate))),
          Text(value, style: text.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

/// Change the API address at runtime (useful when the laptop's LAN IP changes) and test it.
class _ServerSettings extends StatefulWidget {
  const _ServerSettings();

  @override
  State<_ServerSettings> createState() => _ServerSettingsState();
}

class _ServerSettingsState extends State<_ServerSettings> {
  late final TextEditingController _controller;
  String? _status;
  bool _testing = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: context.read<AppState>().serverUrl);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  static bool _isValid(String value) {
    final uri = Uri.tryParse(value);
    return uri != null && (uri.scheme == 'http' || uri.scheme == 'https') && uri.host.isNotEmpty;
  }

  Future<void> _save() async {
    final url = _controller.text.trim();
    if (!_isValid(url)) {
      setState(() => _status = 'Enter a full address such as http://192.168.1.20:8000');
      return;
    }
    await context.read<AppState>().setServerUrl(url);
    if (mounted) setState(() => _status = 'Saved. New scans will use $url');
  }

  Future<void> _test() async {
    final url = _controller.text.trim();
    if (!_isValid(url)) {
      setState(() => _status = 'Enter a full address such as http://192.168.1.20:8000');
      return;
    }
    setState(() {
      _testing = true;
      _status = null;
    });
    try {
      final health = await ApiService(url).health();
      final model = health.modelLoaded
          ? 'model ${health.modelVersion ?? 'unknown'}${health.demoMode ? ' (demo mode)' : ''}'
          : 'no model loaded: ${health.detail ?? 'unknown reason'}';
      if (mounted) setState(() => _status = 'Connected. Server status ${health.status}, $model.');
    } on ApiException catch (error) {
      if (mounted) setState(() => _status = error.message);
    } finally {
      if (mounted) setState(() => _testing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _controller,
          keyboardType: TextInputType.url,
          autocorrect: false,
          decoration: InputDecoration(
            labelText: 'API address',
            hintText: 'https://api.example.id',
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: OutlinedButton(onPressed: _testing ? null : _test, child: const Text('Test connection'))),
            const SizedBox(width: 10),
            Expanded(child: FilledButton(onPressed: _save, child: const Text('Save'))),
          ],
        ),
        if (_testing) const Padding(padding: EdgeInsets.only(top: 12), child: LinearProgressIndicator()),
        if (_status != null)
          Padding(
            padding: const EdgeInsets.only(top: 10),
            child: Text(_status!, style: text.bodySmall?.copyWith(color: Palette.slate, height: 1.4)),
          ),
      ],
    );
  }
}
