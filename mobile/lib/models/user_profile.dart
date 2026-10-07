enum BiologicalSex { female, male }

class UserProfile {
  const UserProfile({required this.age, required this.sex, this.guardianConsent = false});

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        age: (json['age'] as num).toInt(),
        sex: BiologicalSex.values.byName(json['sex'] as String),
        guardianConsent: json['guardian_consent'] as bool? ?? false,
      );

  final int age;
  final BiologicalSex sex;

  /// Required for users under 18 (UU PDP: children's data needs a parent's or guardian's consent).
  final bool guardianConsent;

  String get sexLabel => sex == BiologicalSex.female ? 'Female' : 'Male';

  Map<String, dynamic> toJson() => {'age': age, 'sex': sex.name, 'guardian_consent': guardianConsent};
}

class ConsentRecord {
  const ConsentRecord({required this.version, required this.grantedAt});

  factory ConsentRecord.fromJson(Map<String, dynamic> json) => ConsentRecord(
        version: json['version'] as String,
        grantedAt: DateTime.parse(json['granted_at'] as String),
      );

  final String version;
  final DateTime grantedAt;

  Map<String, dynamic> toJson() => {'version': version, 'granted_at': grantedAt.toIso8601String()};
}
