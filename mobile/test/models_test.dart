import 'package:flutter_test/flutter_test.dart';
import 'package:glowrithm/models/analysis_result.dart';

Map<String, dynamic> sampleResponse() => {
      'request_id': 'abc123',
      'skin_type': 'oily',
      'skin_type_label': 'Oily',
      'skin_type_label_id': 'Berminyak',
      'skin_type_description': 'High sebum output.',
      'confidence': 0.94,
      'probabilities': {'dry': 0.02, 'normal': 0.04, 'oily': 0.94},
      'low_confidence': false,
      'face_detected': true,
      'explanation': 'The model is 94% confident.',
      'face_image': 'AAAA',
      'heatmap_image': 'BBBB',
      'recommendations': {
        'skin_type': 'oily',
        'headline': 'Recommended for oily skin',
        'summary': 'Regulate sebum.',
        'steps': [
          {
            'order': 1,
            'key': 'cleanse',
            'title': 'Cleanse',
            'goal': 'Remove oil.',
            'ingredients': [
              {
                'id': 'salicylic_acid',
                'name': 'Salicylic Acid',
                'alias': 'BHA',
                'function': 'Clears pores',
                'benefits': ['Unclogs pores'],
                'how_to_use': 'Daily',
                'evidence': ['ref'],
                'match': 0.97,
                'match_percent': 97,
                'regulatory': {'status': 'restricted', 'label': 'Restricted', 'note': 'Max 2%', 'reference': 'BPOM', 'verified': false},
                'personal_notes': <String>[],
              },
            ],
          },
        ],
        'avoid': [
          {'name': 'Mercury', 'reason': 'Prohibited'},
        ],
        'notes': ['Patch test'],
      },
      'disclaimer': 'Not a diagnosis.',
      'model_version': 'ensemble-test',
      'demo_mode': false,
      'quality': {
        'passed': true,
        'mode': 'reject',
        'checks': [
          {'name': 'glare', 'value': 0.08, 'status': 'warn', 'message': 'Strong reflections were found.'},
        ],
        'issues': ['Strong reflections were found.'],
      },
    };

void main() {
  test('parses the analyze response', () {
    final result = AnalysisResult.fromJson(sampleResponse());
    expect(result.skinType, 'oily');
    expect(result.probabilities['oily'], closeTo(0.94, 1e-9));
    final ingredient = result.recommendations.steps.first.ingredients.first;
    expect(ingredient.matchPercent, 97);
    expect(ingredient.regulatory.status, 'restricted');
    expect(result.recommendations.avoid.single.name, 'Mercury');
    expect(result.quality?.checks.single.status, 'warn');
  });

  test('history copies drop the photo and heat map but keep the result', () {
    final result = AnalysisResult.fromJson(sampleResponse());
    final stored = result.withoutImages().toJson();
    expect(stored['face_image'], isNull);
    expect(stored['heatmap_image'], isNull);
    final restored = AnalysisResult.fromJson(stored);
    expect(restored.skinTypeLabel, 'Oily');
    expect(restored.recommendations.steps.first.ingredients.first.name, 'Salicylic Acid');
    expect(restored.quality?.passed, isTrue);
  });
}
