import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../core/config.dart';
import '../core/theme.dart';
import '../models/user_profile.dart';
import '../state/app_state.dart';
import '../widgets/common.dart';

/// "Personalize your profile" (CD-3 Figure 3.2). Age and biological sex only re-rank ingredients;
/// they are never inputs to the skin-type classifier.
class ProfileSetupScreen extends StatefulWidget {
  const ProfileSetupScreen({super.key, this.editing = false});

  final bool editing;

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _ageController;
  BiologicalSex? _sex;
  bool _guardianConsent = false;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final profile = context.read<AppState>().profile;
    _ageController = TextEditingController(text: profile?.age.toString() ?? '');
    _sex = profile?.sex;
    _guardianConsent = profile?.guardianConsent ?? false;
  }

  @override
  void dispose() {
    _ageController.dispose();
    super.dispose();
  }

  int? get _age => int.tryParse(_ageController.text.trim());

  bool get _isMinor {
    final age = _age;
    return age != null && age >= AppConfig.minAge && age < AppConfig.adultAge;
  }

  String? _validateAge(String? value) {
    final age = int.tryParse((value ?? '').trim());
    if (age == null) return 'Enter your age in years';
    if (age < AppConfig.minAge) return 'Glowrithm is for people aged ${AppConfig.minAge} and over';
    if (age > AppConfig.maxAge) return 'Enter a valid age';
    return null;
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final sex = _sex;
    if (sex == null) {
      showSnack(context, 'Select your biological sex');
      return;
    }
    if (_isMinor && !_guardianConsent) {
      showSnack(context, 'Users under 18 need consent from a parent or guardian');
      return;
    }
    setState(() => _saving = true);
    final profile = UserProfile(age: _age!, sex: sex, guardianConsent: _isMinor && _guardianConsent);
    await context.read<AppState>().saveProfile(profile);
    if (!mounted || !widget.editing) return;
    final messenger = ScaffoldMessenger.of(context);
    Navigator.of(context).pop();
    messenger.showSnackBar(const SnackBar(content: Text('Profile updated')));
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final border = OutlineInputBorder(borderRadius: BorderRadius.circular(14));
    final label = text.titleSmall?.copyWith(fontWeight: FontWeight.w700);
    return Scaffold(
      appBar: widget.editing ? AppBar(title: const Text('Edit profile')) : null,
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              if (!widget.editing) ...[const BrandMark(), const SizedBox(height: 28)],
              Text('Personalize your profile', style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text(
                'Your age and biological sex adjust which ingredients are prioritised. '
                'They are not used to classify your skin.',
                style: text.bodyMedium?.copyWith(color: Palette.slate, height: 1.45),
              ),
              const SizedBox(height: 24),
              Text('Age', style: label),
              const SizedBox(height: 8),
              TextFormField(
                controller: _ageController,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(3)],
                validator: _validateAge,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  hintText: 'e.g. 24',
                  suffixText: 'years',
                  prefixIcon: const Icon(Icons.cake_outlined),
                  filled: true,
                  fillColor: Colors.white,
                  border: border,
                  enabledBorder: border.copyWith(borderSide: const BorderSide(color: Palette.line)),
                ),
              ),
              const SizedBox(height: 24),
              Text('Biological sex', style: label),
              const SizedBox(height: 4),
              Text(
                'Average sebum levels differ between the sexes, so this slightly changes the ingredient order.',
                style: text.bodySmall?.copyWith(color: Palette.slate),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _SexOption(
                      label: 'Female',
                      icon: Icons.female,
                      selected: _sex == BiologicalSex.female,
                      onTap: () => setState(() => _sex = BiologicalSex.female),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _SexOption(
                      label: 'Male',
                      icon: Icons.male,
                      selected: _sex == BiologicalSex.male,
                      onTap: () => setState(() => _sex = BiologicalSex.male),
                    ),
                  ),
                ],
              ),
              if (_isMinor) ...[
                const SizedBox(height: 16),
                CheckboxListTile(
                  value: _guardianConsent,
                  onChanged: (value) => setState(() => _guardianConsent = value ?? false),
                  controlAffinity: ListTileControlAffinity.leading,
                  contentPadding: EdgeInsets.zero,
                  title: const Text('My parent or guardian agrees to this analysis (required under 18).'),
                ),
              ],
              const SizedBox(height: 28),
              FilledButton(
                onPressed: _saving ? null : _save,
                child: Text(widget.editing ? 'Save changes' : 'Continue'),
              ),
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.lock_outline, size: 16, color: Palette.slate),
                  const SizedBox(width: 6),
                  Text('Stored encrypted on this device', style: text.bodySmall?.copyWith(color: Palette.slate)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SexOption extends StatelessWidget {
  const _SexOption({required this.label, required this.icon, required this.selected, required this.onTap});

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: selected,
      child: Material(
        color: selected ? Palette.mist : Colors.white,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 18),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: selected ? Palette.lagoon : Palette.line, width: selected ? 2 : 1),
            ),
            child: Column(
              children: [
                Icon(icon, size: 28, color: selected ? Palette.lagoon : Palette.slate),
                const SizedBox(height: 6),
                Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
