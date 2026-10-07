import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Oval face guide with corner brackets, a thirds grid and a centre point (CD-3 scan interface).
class FaceGuideOverlay extends StatelessWidget {
  const FaceGuideOverlay({super.key});

  @override
  Widget build(BuildContext context) => CustomPaint(painter: _FaceGuidePainter(), size: Size.infinite);
}

class _FaceGuidePainter extends CustomPainter {
  static const Color _accent = Color(0xFF7FE0D3);

  @override
  void paint(Canvas canvas, Size size) {
    final ovalWidth = size.width * 0.68;
    final ovalHeight = math.min(ovalWidth * 1.32, size.height * 0.6);
    final center = Offset(size.width / 2, size.height * 0.42);
    final oval = Rect.fromCenter(center: center, width: ovalWidth, height: ovalHeight);

    final dim = Path()
      ..fillType = PathFillType.evenOdd
      ..addRect(Offset.zero & size)
      ..addOval(oval);
    canvas.drawPath(dim, Paint()..color = Colors.black.withAlpha(110));
    canvas.drawOval(
      oval,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..color = Colors.white.withAlpha(230),
    );

    canvas.save();
    canvas.clipPath(Path()..addOval(oval));
    final grid = Paint()
      ..color = Colors.white.withAlpha(55)
      ..strokeWidth = 1;
    for (var i = 1; i < 3; i++) {
      final dx = oval.left + oval.width * i / 3;
      final dy = oval.top + oval.height * i / 3;
      canvas.drawLine(Offset(dx, oval.top), Offset(dx, oval.bottom), grid);
      canvas.drawLine(Offset(oval.left, dy), Offset(oval.right, dy), grid);
    }
    canvas.restore();

    final bracket = Paint()
      ..color = _accent
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    const length = 26.0;
    final frame = oval.inflate(14);
    for (final corner in [frame.topLeft, frame.topRight, frame.bottomLeft, frame.bottomRight]) {
      final sx = corner.dx < center.dx ? 1.0 : -1.0;
      final sy = corner.dy < center.dy ? 1.0 : -1.0;
      canvas.drawLine(corner, corner + Offset(length * sx, 0), bracket);
      canvas.drawLine(corner, corner + Offset(0, length * sy), bracket);
    }
    canvas.drawCircle(center, 3, Paint()..color = _accent);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
