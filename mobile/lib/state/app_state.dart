import 'package:flutter/foundation.dart';

import '../core/config.dart';
import '../models/analysis_result.dart';
import '../models/user_profile.dart';
import '../services/api_service.dart';
import '../services/secure_store.dart';

/// App-wide state: consent, profile, saved history and server address.
/// Every mutation updates memory and notifies listeners first, then persists (encrypted).
class AppState extends ChangeNotifier {
  AppState(this._store);

  final SecureStore _store;
  bool _loaded = false;
  ConsentRecord? _consent;
  UserProfile? _profile;
  List<AnalysisResult> _history = const [];
  String _serverUrl = AppConfig.defaultApiBaseUrl;

  bool get isLoaded => _loaded;
  bool get hasConsent => _consent != null;
  ConsentRecord? get consent => _consent;
  UserProfile? get profile => _profile;
  List<AnalysisResult> get history => _history;
  String get serverUrl => _serverUrl;
  ApiService get api => ApiService(_serverUrl);

  Future<void> load() async {
    try {
      final consent = await _store.readJson(SecureStore.consentKey);
      final profile = await _store.readJson(SecureStore.profileKey);
      final history = await _store.readJson(SecureStore.historyKey);
      final url = await _store.readString(SecureStore.serverUrlKey);
      final record = consent is Map<String, dynamic> ? ConsentRecord.fromJson(consent) : null;
      // A new consent text version means the user must agree again.
      _consent = record != null && record.version == AppConfig.consentVersion ? record : null;
      _profile = profile is Map<String, dynamic> ? UserProfile.fromJson(profile) : null;
      _history = history is List
          ? history.whereType<Map<String, dynamic>>().map(AnalysisResult.fromJson).toList()
          : const [];
      if (url != null && url.isNotEmpty) _serverUrl = url;
    } catch (error) {
      debugPrint('Stored data could not be read ($error); starting fresh.');
      await _store.deleteAll();
    }
    _loaded = true;
    notifyListeners();
  }

  Future<void> grantConsent() async {
    final record = ConsentRecord(version: AppConfig.consentVersion, grantedAt: DateTime.now());
    _consent = record;
    notifyListeners();
    await _store.writeJson(SecureStore.consentKey, record.toJson());
  }

  Future<void> saveProfile(UserProfile profile) async {
    _profile = profile;
    notifyListeners();
    await _store.writeJson(SecureStore.profileKey, profile.toJson());
  }

  bool isSaved(String requestId) => _history.any((item) => item.requestId == requestId);

  Future<void> saveToHistory(AnalysisResult result) async {
    if (isSaved(result.requestId)) return;
    _history = [result.withoutImages(), ..._history].take(AppConfig.maxHistoryEntries).toList();
    notifyListeners();
    await _persistHistory();
  }

  Future<void> deleteFromHistory(String requestId) async {
    _history = _history.where((item) => item.requestId != requestId).toList();
    notifyListeners();
    await _persistHistory();
  }

  Future<void> clearHistory() async {
    _history = const [];
    notifyListeners();
    await _store.delete(SecureStore.historyKey);
  }

  Future<void> setServerUrl(String url) async {
    _serverUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
    notifyListeners();
    await _store.writeString(SecureStore.serverUrlKey, _serverUrl);
  }

  /// UU PDP right to erasure: withdrawing consent deletes every piece of personal data on this device.
  Future<void> withdrawConsentAndErase() async {
    _consent = null;
    _profile = null;
    _history = const [];
    notifyListeners();
    await _store.deleteAll();
    await _store.writeString(SecureStore.serverUrlKey, _serverUrl); // a setting, not personal data
  }

  Future<void> _persistHistory() =>
      _store.writeJson(SecureStore.historyKey, _history.map((item) => item.toJson()).toList());
}
