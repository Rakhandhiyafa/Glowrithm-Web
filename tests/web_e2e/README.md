# Web app end-to-end test

Drives the web test build like a phone user in headless Chromium (390 x 844 viewport, fake camera): consent,
profile validation (including the under-18 guardian rule), live-camera capture, analysis, test details,
recommendations, saving to history, saved results without images, server connection test, gallery upload,
quality-gate rejection of a dark photo, and erasing all data when consent is withdrawn.

```bash
pip install scikit-image                  # once, for the fixtures
python make_fixtures.py fixtures
npm install
# start the backend in another terminal: cd backend && GLOWRITHM_DEMO_MODE=1 PYTHONPATH=../ml uvicorn app.main:app --port 8000
npm run e2e                               # or: CHROME_PATH=/usr/bin/chromium npm run e2e
```

Screenshots and `e2e_log.json` are written to `out/`. One console error (HTTP 422) is expected: it is the
dark photo rejected by the quality gate.
