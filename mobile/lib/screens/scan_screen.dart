import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../core/theme.dart';
import '../widgets/common.dart';
import '../widgets/face_guide_overlay.dart';
import 'confirm_photo_screen.dart';

/// Live camera with a face guide (CD-3 "Diagnostic Scan Interface").
class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> with WidgetsBindingObserver {
  List<CameraDescription> _cameras = const [];
  CameraController? _controller;
  CameraDescription? _active;
  static bool _tipsShown = false; // the capture protocol opens once per app session
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _setup();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_tipsShown && mounted) {
        _tipsShown = true;
        _showTips();
      }
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Release the camera in the background and reopen it on return (camera plugin guidance).
    if (state == AppLifecycleState.inactive) {
      final controller = _controller;
      if (controller == null) return;
      setState(() => _controller = null);
      controller.dispose();
    } else if (state == AppLifecycleState.resumed && _controller == null && _active != null) {
      _startCamera(_active!);
    }
  }

  Future<void> _setup() async {
    try {
      _cameras = await availableCameras();
    } on CameraException catch (error) {
      if (mounted) setState(() => _error = _describe(error));
      return;
    }
    if (_cameras.isEmpty) {
      if (mounted) setState(() => _error = 'No camera was found on this device. Choose a photo from your gallery.');
      return;
    }
    final front = _cameras.indexWhere((camera) => camera.lensDirection == CameraLensDirection.front);
    await _startCamera(_cameras[front >= 0 ? front : 0]);
  }

  Future<void> _startCamera(CameraDescription description) async {
    if (!mounted) return;
    final previous = _controller;
    final controller = CameraController(
      description,
      ResolutionPreset.high,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );
    setState(() {
      _controller = null;
      _active = description;
      _error = null;
    });
    await previous?.dispose();
    try {
      await controller.initialize();
    } on CameraException catch (error) {
      await controller.dispose();
      if (mounted) setState(() => _error = _describe(error));
      return;
    }
    try {
      await controller.setFlashMode(FlashMode.off); // flash glare looks like oily skin to the model
    } on CameraException {
      // Front cameras usually have no flash unit.
    }
    if (!mounted) {
      await controller.dispose();
      return;
    }
    setState(() => _controller = controller);
  }

  Future<void> _capture() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized || controller.value.isTakingPicture || _busy) return;
    setState(() => _busy = true);
    try {
      final photo = await controller.takePicture();
      if (mounted) await _review(photo.path);
    } on CameraException catch (error) {
      if (mounted) showSnack(context, _describe(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickFromGallery() async {
    try {
      final picked = await ImagePicker().pickImage(
        source: ImageSource.gallery,
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 90, // re-encodes as JPEG, which the API accepts
      );
      if (picked != null && mounted) await _review(picked.path);
    } catch (error) {
      if (mounted) showSnack(context, 'The photo could not be opened: $error');
    }
  }

  /// Frees the camera while the user reviews the photo, then reopens it.
  Future<void> _review(String path) async {
    final controller = _controller;
    setState(() => _controller = null);
    await controller?.dispose();
    if (!mounted) return;
    await Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => ConfirmPhotoScreen(imagePath: path)));
    final active = _active;
    if (mounted && active != null) await _startCamera(active);
  }

  Future<void> _switchCamera() async {
    final active = _active;
    if (_cameras.length < 2 || active == null) return;
    await _startCamera(_cameras[(_cameras.indexOf(active) + 1) % _cameras.length]);
  }

  String _describe(CameraException error) {
    switch (error.code) {
      case 'CameraAccessDenied':
      case 'CameraAccessDeniedWithoutPrompt':
      case 'CameraAccessRestricted':
        return 'Camera access is turned off. Allow it in your phone settings, or choose a photo from your gallery.';
      default:
        return 'The camera could not start (${error.description ?? error.code}). Choose a photo from your gallery.';
    }
  }

  void _showTips() {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (_) => const SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(24, 0, 24, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Before you scan', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              SizedBox(height: 12),
              BulletLine('Wash your face with a mild cleanser and wait about 1 hour without applying any product.'),
              BulletLine('Face a window or soft daylight. Do not use a flash or a lamp pointed at your face.'),
              BulletLine('Remove makeup and glasses, and turn off filters or beauty mode.'),
              BulletLine('Pull hair away from your forehead, keep your head straight and fill the oval.'),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    final ready = controller != null && controller.value.isInitialized;
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          if (controller != null && controller.value.isInitialized)
            _CameraView(controller: controller)
          else if (_error != null)
            _CameraMessage(message: _error!)
          else
            const Center(child: CircularProgressIndicator(color: Colors.white)),
          if (ready) const IgnorePointer(child: FaceGuideOverlay()),
          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 8, 0),
                  child: Row(
                    children: [
                      const Text(
                        'Skin scan',
                        style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700),
                      ),
                      const Spacer(),
                      IconButton(
                        tooltip: 'Photo tips',
                        color: Colors.white,
                        icon: const Icon(Icons.lightbulb_outline),
                        onPressed: _showTips,
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                if (ready) const _StatusChip(),
                const SizedBox(height: 18),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 28),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _RoundButton(
                        icon: Icons.photo_library_outlined,
                        tooltip: 'Choose from gallery',
                        onPressed: _busy ? null : _pickFromGallery,
                      ),
                      _ShutterButton(busy: _busy, onPressed: ready && !_busy ? _capture : null),
                      _RoundButton(
                        icon: Icons.flip_camera_android,
                        tooltip: 'Switch camera',
                        onPressed: ready && _cameras.length > 1 ? _switchCamera : null,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Fills the screen with the preview (centre-cropped) without distorting it.
class _CameraView extends StatelessWidget {
  const _CameraView({required this.controller});

  final CameraController controller;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // value.aspectRatio is landscape width / height; in portrait the preview is that much taller than wide.
        final width = constraints.maxWidth;
        return ClipRect(
          child: FittedBox(
            fit: BoxFit.cover,
            child: SizedBox(
              width: width,
              height: width * controller.value.aspectRatio,
              child: CameraPreview(controller),
            ),
          ),
        );
      },
    );
  }
}

class _CameraMessage extends StatelessWidget {
  const _CameraMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.camera_alt_outlined, color: Colors.white70, size: 48),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, height: 1.4)),
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
      decoration: BoxDecoration(color: Colors.black.withAlpha(150), borderRadius: BorderRadius.circular(14)),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(color: Color(0xFF7FE0D3), shape: BoxShape.circle),
              ),
              const SizedBox(width: 8),
              const Text(
                'AI analysis active',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13),
              ),
            ],
          ),
          const SizedBox(height: 2),
          const Text('Align your face inside the oval', style: TextStyle(color: Colors.white70, fontSize: 12)),
        ],
      ),
    );
  }
}

class _RoundButton extends StatelessWidget {
  const _RoundButton({required this.icon, required this.tooltip, required this.onPressed});

  final IconData icon;
  final String tooltip;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: tooltip,
      onPressed: onPressed,
      icon: Icon(icon),
      style: IconButton.styleFrom(
        fixedSize: const Size(54, 54),
        backgroundColor: Colors.white.withAlpha(45),
        foregroundColor: Colors.white,
        disabledBackgroundColor: Colors.white.withAlpha(20),
        disabledForegroundColor: Colors.white38,
      ),
    );
  }
}

class _ShutterButton extends StatelessWidget {
  const _ShutterButton({required this.busy, required this.onPressed});

  final bool busy;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      enabled: onPressed != null,
      label: 'Take photo',
      child: GestureDetector(
        onTap: onPressed,
        child: Container(
          width: 80,
          height: 80,
          padding: const EdgeInsets.all(5),
          decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 4)),
          child: DecoratedBox(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: onPressed == null && !busy ? Colors.white38 : Colors.white,
            ),
            child: busy
                ? const Padding(
                    padding: EdgeInsets.all(20),
                    child: CircularProgressIndicator(strokeWidth: 3, color: Palette.lagoon),
                  )
                : null,
          ),
        ),
      ),
    );
  }
}
