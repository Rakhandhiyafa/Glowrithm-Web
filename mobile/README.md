# Glowrithm mobile app (Flutter, Android)

Screens follow the CD-3 mock-ups: consent, profile, home, camera scan with face guide,
photo check, analysis, results with Grad-CAM heat map, recommended ingredients, history, profile/privacy.

## First-time setup

```bash
cd mobile
flutter create --org id.glowrithm --platforms android .   # generates android/ (keeps lib/ and test/)
python tool/patch_android.py                              # permissions, no backup, HTTP only in debug
flutter pub get
flutter test
```

## Run against your API

| Where the API runs | Command |
|---|---|
| Laptop, Android emulator | `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000` |
| Laptop, real phone on the same Wi-Fi | `flutter run --dart-define=API_BASE_URL=http://192.168.x.y:8000` (start uvicorn with `--host 0.0.0.0`) |
| VPS with HTTPS | `flutter run --dart-define=API_BASE_URL=https://api.example.id --dart-define=API_KEY=...` |

The address can also be changed inside the app: Profile > Server settings > Test connection.

## Release APK

```bash
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.id --dart-define=API_KEY=<key>
# build/app/outputs/flutter-apk/app-release.apk
```
Release builds refuse plain HTTP (Android cleartext policy), so they need the HTTPS server.

## Code map

| Path | Purpose |
|---|---|
| `lib/core/` | configuration (`--dart-define`), theme tokens, formatting |
| `lib/models/` | API response and profile data classes |
| `lib/services/api_service.dart` | multipart upload to `/api/v1/analyze`, friendly network errors |
| `lib/services/secure_store.dart` | encrypted storage (Android Keystore) |
| `lib/state/app_state.dart` | consent, profile, history (no photos), server URL |
| `lib/screens/` | one file per screen |
| `lib/widgets/` | face guide overlay, Grad-CAM viewer, ingredient card, shared UI |
