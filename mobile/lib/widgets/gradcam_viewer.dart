import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../core/theme.dart';

/// Face crop with the Grad-CAM heat map on top; the slider changes the heat-map opacity.
class GradCamViewer extends StatefulWidget {
  const GradCamViewer({super.key, required this.faceBase64, required this.heatmapBase64});

  final String faceBase64;
  final String heatmapBase64;

  @override
  State<GradCamViewer> createState() => _GradCamViewerState();
}

class _GradCamViewerState extends State<GradCamViewer> {
  late final Uint8List _face = base64Decode(widget.faceBase64);
  late final Uint8List _heat = base64Decode(widget.heatmapBase64);
  double _opacity = 0.55;

  @override
  Widget build(BuildContext context) {
    final small = Theme.of(context).textTheme.bodySmall?.copyWith(color: Palette.slate, height: 1.4);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AspectRatio(
          aspectRatio: 1,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Stack(
              fit: StackFit.expand,
              children: [
                Image.memory(_face, fit: BoxFit.cover, gaplessPlayback: true),
                Opacity(
                  opacity: _opacity,
                  child: Image.memory(_heat, fit: BoxFit.cover, gaplessPlayback: true),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            const Icon(Icons.opacity, size: 18, color: Palette.slate),
            Expanded(child: Slider(value: _opacity, onChanged: (value) => setState(() => _opacity = value))),
            SizedBox(width: 44, child: Text('${(100 * _opacity).round()}%', textAlign: TextAlign.end)),
          ],
        ),
        const _HeatLegend(),
        const SizedBox(height: 10),
        Text(
          'Warmer areas influenced the prediction most. The map shows where the model looked; '
          'it is not a measurement of oil or moisture.',
          style: small,
        ),
      ],
    );
  }
}

class _HeatLegend extends StatelessWidget {
  const _HeatLegend();

  @override
  Widget build(BuildContext context) {
    final label = Theme.of(context).textTheme.labelSmall?.copyWith(color: Palette.slate);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          height: 8,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            gradient: const LinearGradient(
              colors: [
                Color(0xFF00008F),
                Color(0xFF0050FF),
                Color(0xFF00E5FF),
                Color(0xFFFFE500),
                Color(0xFFFF3000),
                Color(0xFF8B0000),
              ],
            ),
          ),
        ),
        const SizedBox(height: 4),
        Row(children: [Text('Low influence', style: label), const Spacer(), Text('High influence', style: label)]),
      ],
    );
  }
}
