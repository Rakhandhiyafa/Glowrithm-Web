# Glowrithm web test build

The Android app's flow (`mobile/lib/screens`) as a browser app, for testing the model and the analysis before
the Android app is built: consent, profile, live camera or photo upload with the face oval, photo check,
analysis, result with the Grad-CAM heat map, recommended ingredients, history and profile. It calls the same
REST API as the Android app and is served by the backend at `/app/`.

Plain HTML, CSS and JavaScript modules: no build step and no external requests (fonts, scripts or icons).

| File | Purpose |
|---|---|
| `index.html` | Page shell: view container, bottom navigation, dialog, toast |
| `app.js` | Router, consent/profile gate and every screen |
| `api.js` | API client (`/api/v1/health`, `/api/v1/analyze`) and error messages |
| `camera.js` | Live camera, capture of exactly what the preview shows, photo re-encoding to JPEG |
| `store.js` | Consent, profile, history and settings in this browser's `localStorage` (no photos) |
| `icons.js` | Material Symbols paths used by the app (Apache License 2.0) |
| `styles.css` | Colour tokens and components of the Flutter app |

## Run it

```bash
# from the repository root, with the Python requirements installed (see docs/IMPLEMENTATION_GUIDE.md)
cd backend
GLOWRITHM_DEMO_MODE=1 PYTHONPATH=../ml uvicorn app.main:app --host 0.0.0.0 --port 8000   # demo model
# or, with a trained model in backend/models/model.keras:
PYTHONPATH=../ml uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000/app/> (the root `/` redirects there). `GLOWRITHM_SERVE_WEB=0` turns the web app off.

- **Laptop:** the live camera works on `localhost`.
- **Phone on the same Wi-Fi:** open `http://<laptop IP>:8000/app/`. Browsers allow the live camera only on
  HTTPS pages, so on plain HTTP the scan screen offers *Take or choose a photo*, which opens the phone's camera app.
- **HTTPS** (VPS with Caddy, or the Colab notebook's link): every feature works, including the live camera.

## Differences from the Android app

- Saved data lives in the browser's `localStorage`, which is not encrypted like the Android Keystore. The
  consent text says "kept only in this browser" instead of "encrypted on this device".
- The photo is re-encoded as a JPEG of at most 1600 px in the browser (orientation applied, metadata such as GPS
  location removed), like the Android app's image picker. A live-camera photo is cropped to what the preview shows.
- The result screen has a **Test details** panel (model version, timings, quality-gate values) with
  *Copy test record*, a JSON line without photo, age or sex for the team's test log.

## End-to-end test

`tests/web_e2e/` drives this app in headless Chromium like a phone user (17 checks); see its README.

## Security headers

The backend sends, for `/app/*`: a Content Security Policy without inline scripts, `Permissions-Policy:
camera=(self)`, `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, and `Cache-Control: no-cache`
so testers always get the latest build.
