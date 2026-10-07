// Data classes for the /api/v1/analyze response (mirrors backend/app/schemas.py).

List<String> _strings(Object? value) =>
    (value as List<dynamic>? ?? const <dynamic>[]).map((item) => item.toString()).toList();

Map<String, dynamic> _map(Object? value) => value as Map<String, dynamic>? ?? const <String, dynamic>{};

List<Map<String, dynamic>> _maps(Object? value) =>
    (value as List<dynamic>? ?? const <dynamic>[]).whereType<Map<String, dynamic>>().toList();

class RegulatoryInfo {
  const RegulatoryInfo({
    required this.status,
    required this.label,
    required this.note,
    required this.reference,
    required this.verified,
  });

  factory RegulatoryInfo.fromJson(Map<String, dynamic> json) => RegulatoryInfo(
        status: json['status'] as String? ?? 'unknown',
        label: json['label'] as String? ?? '',
        note: json['note'] as String? ?? '',
        reference: json['reference'] as String? ?? '',
        verified: json['verified'] as bool? ?? false,
      );

  /// permitted | restricted | prohibited (BPOM)
  final String status;
  final String label;
  final String note;
  final String reference;
  final bool verified;

  Map<String, dynamic> toJson() =>
      {'status': status, 'label': label, 'note': note, 'reference': reference, 'verified': verified};
}

class IngredientRec {
  const IngredientRec({
    required this.id,
    required this.name,
    required this.role,
    required this.benefits,
    required this.howToUse,
    required this.evidence,
    required this.match,
    required this.matchPercent,
    required this.regulatory,
    required this.personalNotes,
    this.alias,
    this.inci,
    this.caution,
  });

  factory IngredientRec.fromJson(Map<String, dynamic> json) => IngredientRec(
        id: json['id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        alias: json['alias'] as String?,
        inci: json['inci'] as String?,
        role: json['function'] as String? ?? '',
        benefits: _strings(json['benefits']),
        howToUse: json['how_to_use'] as String? ?? '',
        caution: json['caution'] as String?,
        evidence: _strings(json['evidence']),
        match: (json['match'] as num? ?? 0).toDouble(),
        matchPercent: (json['match_percent'] as num? ?? 0).round(),
        regulatory: RegulatoryInfo.fromJson(_map(json['regulatory'])),
        personalNotes: _strings(json['personal_notes']),
      );

  final String id;
  final String name;
  final String? alias;
  final String? inci;
  final String role;
  final List<String> benefits;
  final String howToUse;
  final String? caution;
  final List<String> evidence;
  final double match;
  final int matchPercent;
  final RegulatoryInfo regulatory;
  final List<String> personalNotes;

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'alias': alias,
        'inci': inci,
        'function': role,
        'benefits': benefits,
        'how_to_use': howToUse,
        'caution': caution,
        'evidence': evidence,
        'match': match,
        'match_percent': matchPercent,
        'regulatory': regulatory.toJson(),
        'personal_notes': personalNotes,
      };
}

class RoutineStep {
  const RoutineStep({
    required this.order,
    required this.key,
    required this.title,
    required this.goal,
    required this.ingredients,
  });

  factory RoutineStep.fromJson(Map<String, dynamic> json) => RoutineStep(
        order: (json['order'] as num? ?? 0).toInt(),
        key: json['key'] as String? ?? '',
        title: json['title'] as String? ?? '',
        goal: json['goal'] as String? ?? '',
        ingredients: _maps(json['ingredients']).map(IngredientRec.fromJson).toList(),
      );

  final int order;
  final String key;
  final String title;
  final String goal;
  final List<IngredientRec> ingredients;

  Map<String, dynamic> toJson() => {
        'order': order,
        'key': key,
        'title': title,
        'goal': goal,
        'ingredients': ingredients.map((item) => item.toJson()).toList(),
      };
}

class AvoidItem {
  const AvoidItem({required this.name, required this.reason});

  factory AvoidItem.fromJson(Map<String, dynamic> json) =>
      AvoidItem(name: json['name'] as String? ?? '', reason: json['reason'] as String? ?? '');

  final String name;
  final String reason;

  Map<String, dynamic> toJson() => {'name': name, 'reason': reason};
}

class Recommendations {
  const Recommendations({
    required this.skinType,
    required this.headline,
    required this.summary,
    required this.steps,
    required this.avoid,
    required this.notes,
  });

  factory Recommendations.fromJson(Map<String, dynamic> json) => Recommendations(
        skinType: json['skin_type'] as String? ?? '',
        headline: json['headline'] as String? ?? '',
        summary: json['summary'] as String? ?? '',
        steps: _maps(json['steps']).map(RoutineStep.fromJson).toList(),
        avoid: _maps(json['avoid']).map(AvoidItem.fromJson).toList(),
        notes: _strings(json['notes']),
      );

  final String skinType;
  final String headline;
  final String summary;
  final List<RoutineStep> steps;
  final List<AvoidItem> avoid;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'skin_type': skinType,
        'headline': headline,
        'summary': summary,
        'steps': steps.map((step) => step.toJson()).toList(),
        'avoid': avoid.map((item) => item.toJson()).toList(),
        'notes': notes,
      };
}

class QualityCheck {
  const QualityCheck({required this.name, required this.status, required this.message, this.value});

  factory QualityCheck.fromJson(Map<String, dynamic> json) => QualityCheck(
        name: json['name'] as String? ?? '',
        status: json['status'] as String? ?? 'ok',
        message: json['message'] as String? ?? '',
        value: (json['value'] as num?)?.toDouble(),
      );

  final String name;
  final String status; // ok | warn | fail
  final String message;
  final double? value;

  Map<String, dynamic> toJson() => {'name': name, 'status': status, 'message': message, 'value': value};
}

class QualityReport {
  const QualityReport({required this.passed, required this.mode, required this.checks, required this.issues});

  factory QualityReport.fromJson(Map<String, dynamic> json) => QualityReport(
        passed: json['passed'] as bool? ?? true,
        mode: json['mode'] as String? ?? 'off',
        checks: _maps(json['checks']).map(QualityCheck.fromJson).toList(),
        issues: _strings(json['issues']),
      );

  final bool passed;
  final String mode;
  final List<QualityCheck> checks;
  final List<String> issues;

  Map<String, dynamic> toJson() => {
        'passed': passed,
        'mode': mode,
        'checks': checks.map((check) => check.toJson()).toList(),
        'issues': issues,
      };
}

class AnalysisResult {
  const AnalysisResult({
    required this.requestId,
    required this.skinType,
    required this.skinTypeLabel,
    required this.skinTypeLabelId,
    required this.skinTypeDescription,
    required this.confidence,
    required this.probabilities,
    required this.lowConfidence,
    required this.faceDetected,
    required this.explanation,
    required this.recommendations,
    required this.disclaimer,
    required this.modelVersion,
    required this.demoMode,
    required this.createdAt,
    this.faceImageB64,
    this.heatmapImageB64,
    this.quality,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) => AnalysisResult(
        requestId: json['request_id'] as String? ?? DateTime.now().microsecondsSinceEpoch.toString(),
        skinType: json['skin_type'] as String? ?? 'normal',
        skinTypeLabel: json['skin_type_label'] as String? ?? '',
        skinTypeLabelId: json['skin_type_label_id'] as String? ?? '',
        skinTypeDescription: json['skin_type_description'] as String? ?? '',
        confidence: (json['confidence'] as num? ?? 0).toDouble(),
        probabilities: _map(json['probabilities']).map((key, value) => MapEntry(key, (value as num).toDouble())),
        lowConfidence: json['low_confidence'] as bool? ?? false,
        faceDetected: json['face_detected'] as bool? ?? true,
        explanation: json['explanation'] as String? ?? '',
        faceImageB64: json['face_image'] as String?,
        heatmapImageB64: json['heatmap_image'] as String?,
        quality: json['quality'] is Map<String, dynamic> ? QualityReport.fromJson(json['quality'] as Map<String, dynamic>) : null,
        recommendations: Recommendations.fromJson(_map(json['recommendations'])),
        disclaimer: json['disclaimer'] as String? ?? '',
        modelVersion: json['model_version'] as String? ?? '',
        demoMode: json['demo_mode'] as bool? ?? false,
        createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
      );

  final String requestId;
  final String skinType;
  final String skinTypeLabel;
  final String skinTypeLabelId;
  final String skinTypeDescription;
  final double confidence;
  final Map<String, double> probabilities;
  final bool lowConfidence;
  final bool faceDetected;
  final String explanation;
  final String? faceImageB64;
  final String? heatmapImageB64;
  final QualityReport? quality;
  final Recommendations recommendations;
  final String disclaimer;
  final String modelVersion;
  final bool demoMode;
  final DateTime createdAt;

  /// History never keeps the photo or the heat map (data minimisation).
  AnalysisResult withoutImages() => AnalysisResult(
        requestId: requestId,
        skinType: skinType,
        skinTypeLabel: skinTypeLabel,
        skinTypeLabelId: skinTypeLabelId,
        skinTypeDescription: skinTypeDescription,
        confidence: confidence,
        probabilities: probabilities,
        lowConfidence: lowConfidence,
        faceDetected: faceDetected,
        explanation: explanation,
        recommendations: recommendations,
        disclaimer: disclaimer,
        modelVersion: modelVersion,
        demoMode: demoMode,
        createdAt: createdAt,
        quality: quality,
      );

  Map<String, dynamic> toJson({bool includeImages = false}) => {
        'request_id': requestId,
        'skin_type': skinType,
        'skin_type_label': skinTypeLabel,
        'skin_type_label_id': skinTypeLabelId,
        'skin_type_description': skinTypeDescription,
        'confidence': confidence,
        'probabilities': probabilities,
        'low_confidence': lowConfidence,
        'face_detected': faceDetected,
        'explanation': explanation,
        'face_image': includeImages ? faceImageB64 : null,
        'heatmap_image': includeImages ? heatmapImageB64 : null,
        'recommendations': recommendations.toJson(),
        'disclaimer': disclaimer,
        'model_version': modelVersion,
        'demo_mode': demoMode,
        'created_at': createdAt.toIso8601String(),
        'quality': quality?.toJson(),
      };
}
