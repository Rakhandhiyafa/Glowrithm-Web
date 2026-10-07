import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../services/api_service.dart';
import '../state/app_state.dart';
import 'result_screen.dart';

/// Sends the photo to the API and shows progress; on success it is replaced by the result screen.
class AnalyzingScreen extends StatefulWidget {
  const AnalyzingScreen({super.key, required this.imagePath});

  final String imagePath;

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen> {
  static const List<String> _stages = [
    'Uploading over a secure connection',
    'Finding and cropping your face',
    'Classifying with ResNet50V2 and EfficientNetB0',
    'Building the Grad-CAM heat map',
    'Matching ingredients to your skin',
  ];

  Timer? _ticker;
  int _stage = 0;
  String? _error;
  int? _statusCode;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _run());
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  Future<void> _run() async {
    final state = context.read<AppState>();
    final profile = state.profile;
    if (profile == null) return;
    setState(() {
      _error = null;
      _statusCode = null;
      _stage = 0;
    });
    _ticker?.cancel();
    _ticker = Timer.periodic(const Duration(milliseconds: 900), (_) {
      if (mounted && _stage < _stages.length - 1) setState(() => _stage++);
    });
    try {
      final result = await state.api.analyze(imagePath: widget.imagePath, age: profile.age, sex: profile.sex.name);
      if (!mounted) return;
      Navigator.of(context).pushReplacement(MaterialPageRoute<void>(builder: (_) => ResultScreen(result: result)));
    } on ApiException catch (error) {
      if (mounted) {
        setState(() {
          _error = error.message;
          _statusCode = error.statusCode;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = 'Something went wrong: $error');
    } finally {
      _ticker?.cancel();
    }
  }

  @override
  Widget build(BuildContext context) {
    final error = _error;
    return Scaffold(
      appBar: AppBar(title: const Text('Analyzing')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: error == null ? _buildProgress(context) : _buildFailure(context, error),
        ),
      ),
    );
  }

  Widget _buildProgress(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        const Center(child: SizedBox(width: 64, height: 64, child: CircularProgressIndicator(strokeWidth: 5))),
        const SizedBox(height: 28),
        Text('Analyzing your skin', style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
        Text('This usually takes a few seconds.', style: text.bodyMedium?.copyWith(color: Palette.slate)),
        const SizedBox(height: 24),
        for (var i = 0; i < _stages.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                Icon(
                  i < _stage ? Icons.check_circle : (i == _stage ? Icons.radio_button_checked : Icons.radio_button_unchecked),
                  size: 20,
                  color: i <= _stage ? Palette.lagoon : Palette.line,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _stages[i],
                    style: text.bodyMedium?.copyWith(color: i <= _stage ? Palette.ink : Palette.slate),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildFailure(BuildContext context, String message) {
    final text = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 12),
        Icon(_statusCode == 422 ? Icons.camera_alt_outlined : Icons.cloud_off, size: 56, color: Palette.amber),
        const SizedBox(height: 16),
        Text(
          _statusCode == 422 ? 'Retake your photo' : 'The analysis did not finish',
          textAlign: TextAlign.center,
          style: text.titleLarge?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        Text(message, textAlign: TextAlign.center, style: text.bodyMedium?.copyWith(color: Palette.slate, height: 1.45)),
        const Spacer(),
        if (_statusCode == 422) // rejected by the photo-quality gate: a new photo is needed
          FilledButton(
            onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
            child: const Text('Retake photo'),
          )
        else
          FilledButton(onPressed: _run, child: const Text('Try again')),
        const SizedBox(height: 10),
        OutlinedButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Back')),
      ],
    );
  }
}
