/// Build-time configuration.
///
/// Point the app at your API without editing code:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000
///   flutter build apk --release --dart-define=API_BASE_URL=https://api.example.id --dart-define=API_KEY=...
/// The server address can also be changed at runtime in Profile > Server settings.
class AppConfig {
  AppConfig._();

  /// 10.0.2.2 is the host computer as seen from the Android emulator.
  static const String defaultApiBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
  static const String apiKey = String.fromEnvironment('API_KEY');
  static const String appVersion = '1.0.0';
  static const String consentVersion = '1.0';
  static const int minAge = 13;
  static const int adultAge = 18;
  static const int maxAge = 100;
  static const int maxHistoryEntries = 50;
  static const Duration requestTimeout = Duration(seconds: 60);
}
