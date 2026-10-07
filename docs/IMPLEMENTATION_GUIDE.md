# Glowrithm implementation guide

This guide takes you from the code in this repository to a working system and the results you
need for CD-4 (Implementasi) and CD-5 (Pengujian dan Analisis). Follow the steps in order.
Everything marked **[CD-4]** or **[CD-5]** produces material for those documents.

## 0. Suggested schedule (aligned with the CD-3 Gantt chart)

| When (2026) | Work | Output |
|---|---|---|
| Oct, week 2 | Environment setup, dataset download and preparation (step 2) | `summary.json`, dataset table **[CD-4]** |
| Oct, weeks 3-4 | Train ResNet50V2, EfficientNetB0 and the ensemble on Colab (step 3) | three `model.keras` files |
| Nov, week 1 | Evaluation, robustness, Grad-CAM figures, benchmark (step 4) | all **[CD-5]** model tables and figures |
| Nov, weeks 1-2 | Backend locally, then VPS with HTTPS (steps 5-6) | live API, Swagger screenshot **[CD-4]** |
| Nov, weeks 2-4 | App on real phones, screenshots, demo video (step 7) | screenshots **[CD-4]** |
| Dec, weeks 1-3 | Functional, security, device and SUS tests (step 8) | test tables **[CD-5]** |
| Dec, week 4 to Jan | Fill CD-4/CD-5 placeholders, final report (step 9) | submitted documents |

If you are behind schedule, do steps 5 and 7 with **demo mode** while the model trains: the app
team does not need to wait for the ML team.

## 1. Environment setup

**Python (ML + backend), 3.11 recommended**
```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r ml/requirements.txt     # CPU-only laptop: replace tensorflow with tensorflow-cpu
pip install -e ml                      # makes `glowrithm_ml` importable everywhere
pip install -r backend/requirements.txt
```

**Flutter**: install the Flutter SDK (3.27 or newer) and Android Studio (SDK + emulator), then run
`flutter doctor` until it reports no problems for Android.

**Colab**: upload this repository as a zip to Google Drive and use
`ml/notebooks/glowrithm_colab.ipynb` (Runtime > Change runtime type > GPU).

## 2. Dataset **[CD-4: tabel distribusi dataset]**

1. Download a labelled dataset of face images with dry / normal / oily classes. The initial test uses
   Kaggle `shakyadissanayake/oily-dry-and-normal-skin-types-dataset` (about 126 MB; the Colab notebook
   downloads it). Record its name, author, licence and URL for the references.
2. Put it under `ml/data/raw/`. Any folder depth works as long as each image sits below a folder
   named `dry`, `normal` or `oily` (Indonesian `kering`/`berminyak` also work), e.g.
   `ml/data/raw/train/oily/img001.jpg`.
3. Audit it first, then prepare it:
   ```bash
   cd ml
   python scripts/audit_dataset.py --raw data/raw --out reports/dataset_audit   # counts, duplicates, leakage, faces
   python scripts/prepare_dataset.py --config config.yaml
   ```
   The audit reports how many photos appear in more than one of the dataset's own splits (mirrored copies and
   Roboflow-style augmented copies included); report this in CD-4/CD-5. Preparation then removes exact
   duplicates, keeps near-duplicates and copies of one source photo in one split (no train/test leakage),
   drops near-duplicates with conflicting labels, crops the face (Haar cascade, 30 % margin)
   and writes 70/15/15 stratified splits to `data/processed/manifest.csv`.
4. Read the printed table and `data/processed/summary.json`:
   - **Face detection rate** below about 70 % means many images are close-ups or tilted faces.
     Look at some crops in `data/processed/<class>/`. If close-ups dominate, set
     `crop_faces: false` in `config.yaml` (the same setting is then used by the API automatically).
   - Large class imbalance is handled by `balance_strategy: oversample`.
   - Many duplicates removed is normal for public datasets; note the numbers in CD-4.
5. To keep the dataset's own split instead, add `--keep-existing-split`.

## 3. Training (Colab GPU) **[CD-4: hyperparameter table, training curves]**

Without a GPU, `python scripts/train_cached.py --config config.yaml --views 4` gives a quick first result for
all three architectures on a CPU: the backbones stay frozen, their features are cached (four augmented views
per training image) and only the classification heads are trained. It also cross-validates the heads and checks
how similar each test image is to its closest training image (leakage check). Use it for initial tests, and
`train.py` (two phases, with fine-tuning) on a GPU for the final model.

If Keras cannot download ImageNet weights (restricted networks), run `python scripts/fetch_offline_weights.py`
and set `training.effnet_weights_file` to the file it prints. It installs the official ResNet50V2 file from
the keras-team GitHub release into the Keras cache (MD5-checked) and ports the EfficientNet-B0 Noisy Student
ImageNet weights of the qubvel/efficientnet release, verified by classifying two sample photos.

```bash
cd ml
python scripts/train.py --config config.yaml --arch ensemble   # main model (CD-3 solution 1)
python scripts/train.py --config config.yaml --arch resnet     # baseline for the ablation test
python scripts/train.py --config config.yaml --arch effnet     # baseline for the ablation test
```
Each run writes `artifacts/<arch>/model.keras`, `model_meta.json`, `history.csv`,
`training_curves.png` and `model_summary.txt`. Use the same config and seed for all three runs so
the comparison in CD-5 is fair.

Run `python scripts/train.py --config config.yaml --smoke-test` first on a new machine: it runs
one short epoch per phase to check the whole pipeline in a minute.

**Reading the curves and what to change**

| Symptom | Likely cause | Try |
|---|---|---|
| Train accuracy high, validation much lower (overfitting) | small dataset | more augmentation (`rotation`, `zoom`), `dropout_1: 0.5`, smaller `unfreeze_fraction` (0.2) |
| Both accuracies low and flat (underfitting) | head too small or learning rate too low | `head.epochs: 25`, `finetune.learning_rate: 3.0e-5`, `unfreeze_fraction: 0.4` |
| Validation loss jumps after fine-tuning starts | learning rate too high for the backbones | `finetune.learning_rate: 5.0e-6` |
| One class always wrong | label noise or too few images | inspect that class's crops; check `summary.json` |
| Colab runs out of memory | batch too large | `batch_size: 16` |

Change one thing at a time and keep a short log (date, change, val accuracy, val macro-F1):
examiners like to see that hyper-parameters were chosen deliberately.

Download `artifacts/` back to your laptop/Drive when done (the notebook's last cell does this).

## 4. Evaluation for CD-5 **[CD-5: sections 2.1-2.4 and 2.7]**

```bash
cd ml
M=artifacts/ensemble/model.keras
python scripts/evaluate.py --model $M --split test                       # metrics, confusion matrix, ROC
python scripts/evaluate.py --model artifacts/resnet/model.keras --split test
python scripts/evaluate.py --model artifacts/effnet/model.keras --split test
python scripts/crossval.py --arch ensemble --folds 5                    # mean +/- SD and 95% CI
python scripts/compare_models.py artifacts/ensemble/reports/test/predictions.csv \
    artifacts/effnet/reports/test/predictions.csv --names ensemble effnet   # McNemar test
python scripts/xai_deletion.py --model $M --max-images 100              # Grad-CAM faithfulness
python scripts/quality_report.py --split train                          # calibrate quality-gate thresholds
python scripts/robustness.py --model $M                                  # lighting, blur, noise, JPEG, tilt
python scripts/gradcam_report.py --model $M --per-class 3                # interpretability figures
python scripts/export_tflite.py --model $M --quantize float16            # optional on-device model
python scripts/benchmark.py --model $M --image some_face.jpg --tflite artifacts/ensemble/model_float16.tflite
```

The CD-4/CD-5 table and figure numbers for every output file are listed in `docs/RANGKUMAN_PROGRES.md`, section 4.

**If the ensemble is below the 90 % target from CD-3:** report the honest number, show the
ablation and robustness results, and explain the likely causes in CD-5 section 3 (dataset size,
label quality, lighting). An honest analysis scores better than an inflated number, and the
deduplicated split means your number is trustworthy. Also report `accuracy_on_confident` from
`metrics.json`: accuracy on predictions above the 60 % confidence threshold, which is what users
actually see without a "retake" warning.

## 5. Backend locally **[CD-4: Swagger screenshot; CD-5: functional tests]**

```bash
cd backend
cp .env.example .env
mkdir -p models && cp ../ml/artifacts/ensemble/model.keras ../ml/artifacts/ensemble/model_meta.json models/
uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file .env
```
- Open `http://localhost:8000/docs`, run `GET /api/v1/health` (expect `"model_loaded": true`)
  and try `POST /api/v1/analyze` with a photo. Screenshot the docs page for CD-4.
- Before the model exists, set `GLOWRITHM_DEMO_MODE=1` in `.env`.
- The **web test build** of the app is served at `http://localhost:8000/app/` (`GLOWRITHM_SERVE_WEB=0` turns it
  off). It runs the whole Android flow in a browser against this API; see `docs/PANDUAN_UJI_WEB_APP.md`.
- `GLOWRITHM_QUALITY_GATE=reject` (default) answers HTTP 422 with advice for dark, blurry, glare-heavy or far-away photos; use `warn` while calibrating thresholds with `quality_report.py`.
- Run the automated tests: `python -m pytest -q` (record the "N passed" line for CD-5).
- Train and serve with the same TensorFlow/Keras minor version; the API logs a warning if
  `model_meta.json` says otherwise.

## 6. Deployment on the VPS (HTTPS) **[CD-4: deployment table]**

1. Rent a VPS (2 vCPU, 4 GB RAM recommended; 2 GB minimum), Ubuntu 22.04/24.04, install Docker.
2. Point a domain's DNS A record (e.g. `api.glowrithm.my.id`) to the VPS IP.
3. On the VPS:
   ```bash
   git clone <your repo> glowrithm && cd glowrithm
   cp ../model.keras ../model_meta.json backend/models/        # upload them with scp first
   cp backend/.env.example backend/.env                         # set GLOWRITHM_API_KEY to a long random value
   nano deploy/Caddyfile                                        # replace api.example.id with your domain
   docker compose -f deploy/docker-compose.yml up -d --build
   curl https://api.glowrithm.my.id/api/v1/health
   ```
4. Caddy obtains the Let's Encrypt certificate automatically. Logs:
   `docker compose -f deploy/docker-compose.yml logs -f api`.
5. Updating the model later: copy the new files into `backend/models/` and run the same
   `up -d --build` command.

## 7. Mobile app **[CD-4: screenshots of every screen]**

```bash
cd mobile
flutter create --org id.glowrithm --platforms android .
python tool/patch_android.py
flutter pub get && flutter test
flutter run --dart-define=API_BASE_URL=http://<laptop-LAN-IP>:8000   # or the VPS https URL
```
Take screenshots (on a real phone, light theme) of: consent, profile, home, scan, photo check,
analyzing, results with heat map, recommendations, ingredient detail sheet, history, profile.
Record a 2-4 minute demo video for the CD-4 section *Video Demonstrasi*.

Release APK: `flutter build apk --release --dart-define=API_BASE_URL=https://<domain> --dart-define=API_KEY=<key>`.

Optional extensions (only if time allows): on-device classification with `tflite_flutter` and
`model_float16.tflite` (no heat map offline); Firebase sync of history (requires an account flow
and an updated consent text).

## 8. Testing for CD-5

| Test | How | Record |
|---|---|---|
| Functional (black box), cases F-01 to F-20 in the CD-5 black-box table | Run each case on the phone; screenshot evidence | Berhasil/Gagal per case |
| Recommendation correctness | `pytest -q backend/tests/test_recommender.py` + optional review by a pharmacist/dermatologist | passed count, expert scores |
| API performance | `benchmark.py` on the VPS; `timings_ms` in responses; stopwatch on the phone over Wi-Fi and 4G (10 runs each) | mean / p50 / p95 in ms |
| Device compatibility | At least two Android phones (different versions/brands) | per-device checklist |
| Security and privacy | Cases S-01 to S-09 in the CD-5 security table (HTTPS, consent, API key, no stored photos, erase data, guardian rule) | Berhasil/Gagal |
| Usability (SUS) | 10-15 respondents do tasks T1-T5, then fill the 10 SUS items (Likert 1-5). Put answers in a CSV like `ml/sus_responses_template.csv` and run `python ml/scripts/sus_score.py responses.csv` | per-respondent and mean SUS |
| Field validation | Follow `docs/PROTOKOL_DATA_UJI_LOKAL.md`, then `python ml/scripts/evaluate_local.py --model ... --csv ... --images ...` | accuracy, Cohen's kappa, per-lighting results, quality-gate impact |

Use a consent form for respondents too, and do not keep their photos.

## 9. Finishing CD-4 and CD-5

The drafts mark everything you must fill in with **yellow highlighted [brackets]**: cover names,
approval sheet, dataset numbers, screenshots, measured results and analysis sentences. Search for
`[` in Word to find them. Then:
- Update *Jumlah Halaman* and the revision table after each supervisor review.
- Replace placeholder figures with the generated PNGs listed above.
- Keep the code listings in CD-4 in sync if you change the code (they were taken from this repository).
- Equations are native Word equations (OMML). Open the drafts in Microsoft Word to check them: LibreOffice
  without its Math module and some online viewers show them as blank. If one ever looks wrong, retype it
  with Insert > Equation.
- Mark tables of numbers as final only after re-running the scripts on your real dataset; the drafts contain
  no measured results, only placeholders.

## 10. Design decisions to be ready to defend

| Question | Answer |
|---|---|
| Why ResNet50V2 and not "ResNet" as drawn in CD-3? | Same residual learning (CD-3 Eq. 3.1); V2 uses pre-activation and has ImageNet weights in Keras; its input scaling is a standard `Rescaling` layer, so the saved model needs no custom code. |
| Why concatenate features instead of averaging predictions? | Concatenation lets the classifier learn how to combine texture features (ResNet) with efficient multi-scale features (EfficientNet); averaging fixes the combination. The ablation test shows the gain. |
| Does the heat map show oil? | No. Grad-CAM shows which regions most influenced the model's decision. It is an explanation of the model, not a measurement. |
| Are age and sex model inputs? | No. They only re-rank ingredients through transparent rules (`personalization_rules` in the knowledge base), consistent with the CD-2 limitation on internal factors. |
| Why server-side inference? | Grad-CAM needs gradients, which TFLite does not provide; the model can be updated without an app update. TFLite export exists for the efficiency comparison and future offline mode. |
| How is privacy handled? | Explicit consent per request, HTTPS, photos processed in memory and never stored or logged, encrypted on-device storage without photos, right to erase, guardian consent under 18. |
| How do you know the accuracy is not inflated? | Exact and near-duplicate images are grouped so they never cross the train/test boundary. |

## 11. Before release: verify the knowledge base

`backend/app/data/knowledge_base.json` is a draft:
- Check every `regulatory.note` (salicylic acid, zinc salts, UV filters) against the annexes of
  Peraturan BPOM No. 23 Tahun 2019 and set `"verified": true` only after checking.
- Add references where the file says "Citation needed" (zinc PCA, vitamin C, sunscreen).
- Ask a pharmacist or dermatologist to review the `suitability` scores and personalization rules;
  this review is a strong addition to CD-5.
- Double-check CD-3 references [5] and [14] (no DOI); replace them if you cannot find the source.

## 12. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: glowrithm_ml` | `pip install -e ml` from the repository root |
| API health says `model_loaded: false` | read `detail`; usually `backend/models/model.keras` is missing |
| App: "Cannot reach the server" | phone and laptop on the same Wi-Fi, uvicorn started with `--host 0.0.0.0`, firewall allows port 8000, check Profile > Server settings |
| Release APK cannot connect over HTTP | expected: release builds need HTTPS (use the VPS) |
| Camera black screen | grant the camera permission; the emulator needs a virtual camera configured in AVD settings |
| `flutter_secure_storage` errors after reinstalling | uninstall the app completely, then reinstall (backups are disabled on purpose) |
| `tf.lite.Interpreter` deprecation warning (TF 2.20+) | harmless for the scripts; for new code use the LiteRT interpreter (`pip install ai-edge-litert`) |
| API answers 422 "Photo quality is too low" | follow the advice; if good photos are rejected, calibrate the thresholds with `quality_report.py` or set `GLOWRITHM_QUALITY_GATE=warn` while testing |
| `AttributeError: module 'cv2' has no attribute 'CascadeClassifier'` | OpenCV 5 removed the Haar cascade: `pip install "opencv-python-headless>=4.8,<5"` (already pinned in the requirements) |
| Web app: live camera does not start on a phone | browsers allow the live camera only on HTTPS or `localhost`; use *Take or choose a photo*, or the Colab/VPS HTTPS link |
| Keras load error on the server | install the same TensorFlow version that trained the model (`model_meta.json` > `versions`) |
