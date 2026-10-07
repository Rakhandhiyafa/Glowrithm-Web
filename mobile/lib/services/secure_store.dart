import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Encrypted key-value storage (Android Keystore-backed) for consent, profile, history and settings.
class SecureStore {
  SecureStore([FlutterSecureStorage? storage]) : _storage = storage ?? const FlutterSecureStorage();

  static const String consentKey = 'consent';
  static const String profileKey = 'profile';
  static const String historyKey = 'history';
  static const String serverUrlKey = 'server_url';

  final FlutterSecureStorage _storage;

  Future<Object?> readJson(String key) async {
    final raw = await _storage.read(key: key);
    return raw == null ? null : jsonDecode(raw);
  }

  Future<void> writeJson(String key, Object? value) => _storage.write(key: key, value: jsonEncode(value));

  Future<String?> readString(String key) => _storage.read(key: key);

  Future<void> writeString(String key, String value) => _storage.write(key: key, value: value);

  Future<void> delete(String key) => _storage.delete(key: key);

  Future<void> deleteAll() => _storage.deleteAll();
}
