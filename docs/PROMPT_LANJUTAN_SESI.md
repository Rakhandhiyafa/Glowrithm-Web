# Prompt Lanjutan Sesi: Proyek Capstone Glowrithm

**Cara pakai**
1. Buka chat baru dengan Claude.
2. Lampirkan file:
   - **wajib:** `glowrithm.zip`;
   - **disarankan:** `FTE-CD-4_Glowrithm_Draft.docx`, `FTE-CD-5_Glowrithm_Draft.docx`, `CD_1-3_GLOWRITHM.pdf`;
   - **jika akan mengedit CD:** template `FTE-CD-4.docx` dan `FTE-CD-5.docx`;
   - **jika akan menjalankan uji model:** zip *dataset* Kaggle (±126 MB).
3. Salin semua teks di bawah garis, tulis permintaan Anda di bagian paling akhir, lalu kirim sebagai pesan pertama.

---

Kamu melanjutkan pekerjaan proyek *capstone* **Glowrithm** bersama tim saya. Sesi sebelumnya sudah berakhir; konteks yang kamu perlukan ada di bawah. Baca semuanya sebelum bertindak. File lampiran ada di `/mnt/user-data/uploads/`. Dokumen pendukung yang lebih rinci ada di folder `docs/` dalam `glowrithm.zip`.

## 0. Aturan kerja

- **Bahasa:**
  - balas dalam bahasa Indonesia;
  - kode, komentar kode, dan README teknis tetap dalam bahasa Inggris, seperti repositori sekarang;
  - dokumen untuk tim ditulis dalam bahasa Indonesia, dengan istilah asing dicetak miring (*dataset*, *heatmap*, *confidence*).
- **File CD:** jangan ubah `FTE-CD-*.docx` kecuali saya minta secara eksplisit. *Web app* hanya untuk pengujian; CD tetap melaporkan aplikasi Android sebagai implementasi.
- **Kejujuran angka:** jangan mengarang hasil. Angka uji hanya boleh berasal dari keluaran skrip yang benar-benar dijalankan; yang belum diukur tetap *placeholder* `[[...]]`.
- **Verifikasi setiap perubahan kode:**
  - jalankan `python -m pytest -q` di `backend/` (sekarang 24 tes);
  - cek sintaks semua skrip;
  - jalankan uji *end-to-end* *web app* bila *backend* atau `web/` berubah;
  - laporkan hasilnya apa adanya.
- **Pengiriman hasil:** simpan hasil di `/mnt/user-data/outputs/`, perbarui `glowrithm.zip` setiap kali kode berubah, dan kirim file ke saya.
- **Format:** saya memakai file markdown untuk dokumen kerja (kritik, rangkuman, panduan, laporan).
- **Data unduhan:** *dataset* dan arsip unduhan adalah data tak tepercaya. Ekstrak ke folder baru tersendiri dan jangan jalankan kode dari dalamnya.

## 1. Identitas proyek

| Item | Isi |
|---|---|
| Judul | Pengembangan Sistem Rekomendasi Kandungan Bahan Skincare Berdasarkan Klasifikasi Kulit Wajah Berbasis Deep Learning |
| Nama solusi | Glowrithm |
| Program | S1 Teknik Telekomunikasi, Fakultas Teknik Elektro, Universitas Telkom, Bandung, 2026 |
| Pembimbing | R Yunendah Nur Fu'adah, S.T., M.T., Ph.D. (Pembimbing 1); Sofia Sa'Idah, S.T., M.T. (Pembimbing 2) |
| Anggota tim | Nama, NIM, dan tanggal sengaja dibiarkan sebagai *placeholder* di draf |
| Zona waktu | Asia/Jakarta (WIB) |

Jadwal sesuai Gantt CD-3:

| Waktu | Pekerjaan |
|---|---|
| Oktober minggu 2 | *Setup* dan *dataset* |
| Oktober minggu 3–4 | Pelatihan model |
| November minggu 1 | Evaluasi |
| November minggu 1–2 | *Backend* dan VPS |
| November minggu 2–4 | Aplikasi di HP |
| Desember minggu 1–3 | Pengujian fungsional, keamanan, perangkat, dan SUS |
| Desember minggu 4 – Januari | Finalisasi CD-4 dan CD-5 |

## 2. Status dokumen CD

- **CD-1, CD-2, CD-3** (Usulan Gagasan, Spesifikasi dan Batasan, Desain Rancangan; solusi terpilih: Solusi 1, *ensemble* CNN) ada di `CD_1-3_GLOWRITHM.pdf` (59 halaman).
  - Usulan revisinya ada di `docs/DRAF_REVISI_CD1-CD3.md` (teks siap tempel R1-1 sampai R3-13 dan usulan baris *Timeline Revisi*).
  - Dasar revisinya ada di `docs/KRITIK_DAN_REKOMENDASI_REVISI.md` (34 kekurangan berkode A–F).
  - Belum diterapkan ke Word; harus dibahas dengan pembimbing dulu.
- **CD-4 (Implementasi):** `FTE-CD-4_Glowrithm_Draft.docx`, 48 halaman, dibangun di atas template resmi `FTE-CD-4.docx`.
  - Tiga bab: Deskripsi Umum Implementasi, Detail Implementasi, dan Prosedur Pengoperasian Solusi.
  - Isi: 20 potongan kode yang diambil dari repositori, 3 diagram, dan 32 referensi IEEE.
- **CD-5 (Pengujian dan Analisis):** `FTE-CD-5_Glowrithm_Draft.docx`, 23 halaman, 7 persamaan, 19 referensi. Sebelas jenis pengujian:
  1. kinerja klasifikasi dengan validasi silang;
  2. ablasi dengan uji McNemar;
  3. ketahanan;
  4. Grad-CAM dengan *deletion test*;
  5. validasi lapangan;
  6. fungsional F-01 sampai F-20;
  7. rekomendasi dan regulasi;
  8. kinerja;
  9. kompatibilitas;
  10. keamanan S-01 sampai S-09;
  11. SUS.
- **Isi draf:**
  - semua hasil terukur masih *placeholder* kuning `[[...]]`;
  - tidak ada nama orang;
  - persamaan berupa OMML, jadi cek di Microsoft Word, bukan LibreOffice.
- **Penting:** skrip pembuat draf hilang bersama *container* lama. Perubahan CD berikutnya harus dikerjakan langsung pada `.docx` dengan skill docx (*unpack* → edit XML → *pack* dan validasi), lalu dirender ke PDF untuk dicek visual.
- **Peta keluaran skrip:** `docs/RANGKUMAN_PROGRES.md` bagian 4 memetakan setiap keluaran skrip ke nomor tabel dan gambar CD-4/CD-5.

## 3. Rancangan teknis (sudah final dan terimplementasi)

- **Kelas:** `dry`, `normal`, `oily`, dengan urutan tetap sesuai urutan keluaran model.
- **Praproses (sama untuk pelatihan dan layanan):**
  1. koreksi orientasi EXIF;
  2. deteksi wajah Haar cascade (wajah minimal 15% sisi pendek);
  3. *crop* persegi dengan margin 30% (bila wajah tidak ditemukan: *crop* tengah);
  4. ukuran 384 px untuk tampilan dan penyimpanan;
  5. *resize* bilinear *antialias* ke 224 px sebagai masukan model, RGB float32 0–255.
- **Arsitektur model:**
  - ResNet50V2 (didahului `Rescaling` 1/127.5−1) dan EfficientNetB0 (normalisasi bawaan);
  - GAP 2048 dan 1280, digabung menjadi 3328 → Dropout 0.4 → Dense 256 ReLU dengan L2 1e-4 → Dropout 0.3 → Dense 3 (`logits`) → *softmax* (`probs`);
  - parameter: *ensemble* 28.467.366, ResNet saja 24.090.115, EfficientNet saja 4.378.278;
  - nama layer `resnet_gap`, `effnet_gap`, `fc`, `logits`, dan `probs` dipakai oleh Grad-CAM dan `train_cached.py`, jadi jangan diganti.
- **Pelatihan (`train.py`):**
  - fase 1: *backbone* beku, 15 *epoch*, Adam 1e-3;
  - fase 2: 30% layer teratas dibuka (BatchNorm tetap beku), 30 *epoch*, lr 1e-5;
  - *label smoothing* 0.05 dan *oversampling*;
  - *checkpoint* berdasarkan `val_macro_f1`, *early stopping* *patience* 6, ReduceLROnPlateau 0.3/3;
  - augmentasi: *flip*, rotasi 0.05 (±18°), *zoom* 0.1, translasi 0.05, kecerahan 0.15, kontras 0.15.
- **Grad-CAM:** dihitung per *backbone* pada masukan GAP, dinormalisasi, lalu dirata-ratakan.
- **Persiapan *dataset*** (`prepare_dataset.py` dan `glowrithm_ml/dedup.py`):
  - duplikat MD5 dibuang;
  - foto yang mirip (dHash 256-bit ≤ 10 bit, termasuk versi cermin) dan salinan Roboflow `<nama>_jpg.rf.<hash>.jpg` digabung dalam satu grup, dengan batas ukuran grup 50;
  - grup berlabel bertentangan dibuang;
  - *split* 70/15/15 terstratifikasi berbasis grup, atau `--keep-existing-split`.
- ***Quality gate*** (`glowrithm_ml/quality.py`, diukur pada *crop* 384 px; ambang belum dikalibrasi):

  | Pemeriksaan | Gagal | Peringatan |
  |---|---|---|
  | Kecerahan (rata-rata Y) | < 60 atau > 215 | < 85 atau > 190 |
  | Pantulan (piksel Y ≥ 250) | > 15% | > 6% |
  | Ketajaman (variansi Laplacian) | < 25 | < 60 |
  | Lebar wajah / lebar foto | < 0.18 | < 0.28 |

  Mode `reject` membalas HTTP 422 beserta saran perbaikan. Gambar beresolusi rendah cenderung dinilai "*blurry*".
- **Rekomendasi:**
  - skor kecocokan Mᵢ = clip(Σ p(c)·sᵢ(c) + Σ Δaturan, 0, 1);
  - 9 bahan: Salicylic Acid, Zinc PCA, dan *sunscreen* berstatus *restricted*; Niacinamide, Hyaluronic Acid, Ceramides, Glycerin, Shea Butter, dan Vitamin C berstatus *permitted*;
  - rutinitas tiga langkah: *cleanse*, *treat*, *protect*;
  - empat kelompok bahan terlarang BPOM: merkuri, hidrokinon, asam retinoat, Rhodamin B/Merah K3;
  - enam aturan personalisasi usia dan jenis kelamin;
  - semua catatan regulasi masih `verified: false` dan harus dicek terhadap Peraturan BPOM No. 23 Tahun 2019.
- **API** (FastAPI):
  - *endpoint*: `GET /api/v1/health`, `GET /api/v1/skin-types`, `GET /api/v1/ingredients`, `POST /api/v1/analyze` (*multipart*: `image`, `consent=true`, `age` 13–100, `sex` female/male);
  - foto hanya diproses di memori, header `Cache-Control: no-store`, dan log tanpa data pribadi;
  - variabel lingkungan `GLOWRITHM_`: `MODEL_PATH`, `DEMO_MODE`, `REQUIRE_FACE`, `QUALITY_GATE` (`reject`/`warn`/`off`), `MAX_UPLOAD_MB` (8), `LOW_CONFIDENCE` (0.60), `DISPLAY_SIZE` (384), `API_KEY`, `CORS_ORIGINS`, `SERVE_WEB` (1), `WEB_DIR`.
- ***Deployment*:** Docker (python:3.11-slim, *user non-root*) dan Caddy dengan HTTPS otomatis. File `.dockerignore` kini menyertakan `web/`.
- **Aplikasi Android** (Flutter):
  - pustaka: provider, flutter_secure_storage, http, camera 0.11, image_picker;
  - data disimpan di perangkat tanpa foto, maksimal 50 riwayat;
  - pengguna di bawah 18 tahun wajib mendapat persetujuan wali;
  - belum pernah dikompilasi.
- ***Web app* pengujian** (`web/`, disajikan *backend* di `/app/`; `/` dialihkan ke sana):
  - alur sama dengan Flutter, tulisan antarmuka berbahasa Inggris;
  - data disimpan di `localStorage` tanpa foto (tidak terenkripsi);
  - panel *Test details* dan tombol *Copy test record*;
  - foto dikirim sebagai JPEG ≤ 1600 px, dan foto kamera langsung dipotong sesuai area pratinjau;
  - kamera langsung hanya berjalan di HTTPS atau `localhost`;
  - *header* keamanan: CSP tanpa skrip *inline* dan `Permissions-Policy: camera=(self)`.

## 4. Isi repositori (`glowrithm.zip`)

```
ml/glowrithm_ml/   config, preprocessing, quality (quality gate), dedup, data, model, training, gradcam, metrics
ml/scripts/        prepare_dataset, audit_dataset, train (GPU, 2 fase), train_cached (CPU cepat, fitur beku),
                   fetch_offline_weights, evaluate, crossval, compare_models (McNemar), robustness, gradcam_report,
                   xai_deletion, quality_report, evaluate_local, export_tflite, benchmark, predict, sus_score
ml/notebooks/      glowrithm_colab.ipynb: unduh dataset Kaggle → audit → latih → evaluasi + McNemar →
                   jalankan web app lewat tautan HTTPS Colab (opsional tunnel untuk HP)
ml/config.yaml     semua hiperparameter; ml/templates/local_test_labels.csv; ml/sus_responses_template.csv
backend/app/       main (API + penyajian web app), inference, recommender, schemas, config, data/knowledge_base.json
backend/tests/     test_api (11), test_recommender (7), test_quality (6)
web/               web app pengujian (index.html, app.js, api.js, camera.js, store.js, icons.js, styles.css)
tests/web_e2e/     uji end-to-end web app: make_fixtures.py, e2e_webapp.mjs, package.json
mobile/            aplikasi Flutter (lib/, test/, tool/patch_android.py)
deploy/            docker-compose.yml, Caddyfile
docs/              IMPLEMENTATION_GUIDE, RANGKUMAN_PROGRES, KRITIK_DAN_REKOMENDASI_REVISI, DRAF_REVISI_CD1-CD3,
                   PROTOKOL_DATA_UJI_LOKAL, PANDUAN_UJI_WEB_APP, PROMPT_LANJUTAN_SESI (file ini)
```

## 5. Perintah penting

```bash
# setup (Python 3.11-3.13); OpenCV wajib < 5 karena OpenCV 5 menghapus CascadeClassifier
pip install "tensorflow-cpu>=2.16,<3" -r ml/requirements.txt -r backend/requirements.txt && pip install -e ml

# backend + web app (demo tanpa model): buka http://localhost:8000/app/ dan /docs
cd backend && GLOWRITHM_DEMO_MODE=1 PYTHONPATH=../ml uvicorn app.main:app --host 0.0.0.0 --port 8000

# tes
cd backend && python -m pytest -q
cd tests/web_e2e && python make_fixtures.py fixtures && npm install && npm run e2e   # backend harus jalan

# data dan model (dari ml/)
python scripts/fetch_offline_weights.py          # hanya bila Keras tidak bisa mengunduh bobot ImageNet
python scripts/audit_dataset.py --raw data/raw/<dataset> --out reports/dataset_audit
python scripts/prepare_dataset.py --config config.yaml
python scripts/train_cached.py --config config.yaml --views 4      # CPU, ±15-30 menit, 3 model
python scripts/train.py --config config.yaml --arch ensemble       # GPU, 2 fase (juga resnet, effnet)
M=artifacts/ensemble/model.keras
python scripts/evaluate.py --model $M --split test                 # ulangi untuk resnet dan effnet
python scripts/compare_models.py artifacts/ensemble/reports/test/predictions.csv \
       artifacts/effnet/reports/test/predictions.csv --names ensemble effnet
python scripts/gradcam_report.py --model $M && python scripts/xai_deletion.py --model $M --max-images 100
python scripts/robustness.py --model $M && python scripts/quality_report.py --split train && python scripts/benchmark.py --model $M

# Flutter
cd mobile && flutter create --org id.glowrithm --platforms android . && python tool/patch_android.py && flutter pub get && flutter analyze

# VPS
docker compose -f deploy/docker-compose.yml up -d --build
```

## 6. Hasil pengujian sejauh ini (fakta yang sudah diukur)

- ***Backend*:** 24 dari 24 tes lulus.
- ***Web app* end-to-end:** 17 dari 17 langkah lulus di Chromium *headless* dengan layar 390×844, kamera tiruan, dan model demo. Yang diuji:
  - gerbang persetujuan dan validasi profil, termasuk aturan wali di bawah 18 tahun;
  - tangkapan kamera langsung, analisis, *Test details*, rekomendasi, dan simpan ke riwayat;
  - hasil tersimpan tanpa gambar, tes koneksi server, dan unggahan galeri;
  - foto gelap ditolak *quality gate* (HTTP 422);
  - semua data terhapus saat persetujuan ditarik.
- **Pipeline pada data sintetis:** audit → *prepare* → `train_cached` → *evaluate* → McNemar → Grad-CAM di *backend* berjalan semua. Model gabungan identik dengan *head*-nya (kesesuaian top-1 100%, selisih probabilitas maks ≤ 2e-6).
- **Sesi sebelumnya:** semua skrip lulus *smoke test*; ekspor TFLite float16 menyusutkan model dari 110 MB ke 54 MB dengan prediksi top-1 yang sama.
- **Kecepatan CPU di *sandbox* Claude** (2 vCPU Xeon; bfloat16 tidak mempercepat):

  | Proses | Kecepatan |
  |---|---|
  | *Forward* *ensemble* | ±18 img/s |
  | *Forward* ResNet50V2 | ±25 img/s |
  | *Forward* EfficientNetB0 | ±66 img/s |
  | *Fine-tuning* *ensemble* | ±12 img/s |
  | Analisis di *backend* (model + Grad-CAM) | ±1,2 s per foto |

- **Belum ada hasil dengan data nyata.** Akurasi dari *smoke test* atau data sintetis tidak bermakna.

## 7. Batasan lingkungan Claude dan solusinya

- **Jaringan:**
  - diblokir kebijakan (HTTP 403; jangan dicari jalan pintasnya): `www.kaggle.com`, `storage.googleapis.com` (bobot Keras), `huggingface.co`, `download.pytorch.org`;
  - bisa diakses: PyPI, npm, dan unduhan aset rilis GitHub;
  - halaman web dan API GitHub butuh akses repositori.
- ***Dataset* Kaggle** `shakyadissanayake/oily-dry-and-normal-skin-types-dataset` harus saya unggah sebagai zip, atau diproses lewat notebook Colab. Konektor Google Drive mengembalikan base64, jadi tidak bisa untuk file besar.
- **Versi di *sandbox*:** Python 3.13, TensorFlow 2.21.0, Keras 3.15.1, OpenCV 4.14.
- ***Container* direset antarsesi:** pulihkan repositori dari zip, lalu instal ulang paket dan bobot.
- **Bobot ImageNet *offline*** (`fetch_offline_weights.py`):
  - ResNet50V2 *notop* dari rilis GitHub keras-team (MD5 `fac2f116257151a9d068a22e544a4917`, identik dengan file Keras), ditaruh di `~/.keras/models`;
  - EfficientNet-B0 Noisy Student dari rilis `qubvel/efficientnet` v0.0.1 (MD5 *notop* `a5b48ae7547fc990c7e4f3951230290d`), di-*port* dan diverifikasi (foto kucing → Egyptian cat p = 0,70; foto kopi → espresso p = 0,81);
  - lalu isi `training.effnet_weights_file: ~/.keras/models/efficientnetb0_noisy-student_notop.weights.h5` di salinan *config*;
  - catat di laporan bahwa EfficientNet di *sandbox* memakai bobot Noisy Student, sedangkan Colab memakai bobot Keras standar.
- **Uji *browser*:** `tests/web_e2e` memakai `puppeteer-core` 25.12.0 dan `@sparticuz/chromium` 153.0.0 dari npm. Fixture dibuat dari foto "astronaut" (NASA, domain publik) di scikit-image.
- **Jebakan yang sudah ditemui:**
  - `pkill -f <pola>` ikut membunuh *shell*-nya sendiri bila pola ada di baris perintah yang sama, jadi matikan server di perintah terpisah;
  - uvicorn butuh `PYTHONPATH=../ml` atau `pip install -e ml`;
  - di uji *browser*, gulir elemen ke tengah sebelum mengeklik, karena *app bar* dan navigasi bawah bisa menutupinya.

## 8. Pekerjaan berikutnya

### 8.1 Uji awal model dengan *dataset* Kaggle (tertunda karena *dataset* belum diunggah)

Permintaan saya di sesi lalu: "untuk testing awal model yang akan digunakan dan juga aplikasinya coba gunakan dataset Kaggle tersebut, dan aplikasinya build dalam bentuk web app dulu (build for testing only, jangan ubah file CD)". *Web app* sudah selesai; uji model belum. Langkahnya:

1. Ekstrak zip *dataset* ke folder baru `ml/data/raw/kaggle_skin/`.
2. Jalankan `audit_dataset.py`. Catat jumlah per kelas dan *split*, kebocoran antar-*split* (salinan Roboflow atau cermin), label bertentangan, tingkat deteksi wajah, dan ukuran gambar.
3. Buat salinan `config.yaml` (misalnya `config_kaggle.yaml`) dengan `effnet_weights_file`, lalu jalankan `prepare_dataset.py`. *Default*-nya *re-split* 70/15/15 berbasis grup. Sebagai pembanding, boleh juga mengevaluasi *split* bawaan dengan `--keep-existing-split`.
4. Jalankan `train_cached.py --views 4`. Hasilnya tiga model, `cv_heads.json`, dan `nearest_neighbours.json` (cek kebocoran).
5. Jalankan evaluasi:
   - `evaluate.py` untuk ketiga model;
   - `compare_models.py` untuk *ensemble* vs ResNet dan *ensemble* vs EfficientNet;
   - `gradcam_report.py` dan `xai_deletion.py`;
   - `robustness.py`;
   - `quality_report.py`, lalu kalibrasi ambang *quality gate* bila foto latih yang baik banyak tertolak;
   - `benchmark.py`.
6. Opsional: *fine-tuning* dengan `train.py` di CPU (±2,5 jam untuk *ensemble*), lalu bandingkan dengan versi *backbone* beku.
7. Salin model terbaik beserta `model_meta.json` ke `backend/models/`. Jalankan uji *end-to-end* dan coba beberapa foto dari *split test* lewat *web app*. Buramkan wajah bila *screenshot* akan dibagikan.
8. Tulis `docs/HASIL_UJI_AWAL.md` (bahasa Indonesia). Isinya:
   - audit *dataset*;
   - pengaturan pelatihan;
   - metrik dengan interval kepercayaan, uji McNemar, Grad-CAM, dan kalibrasi *quality gate*;
   - keterbatasan: *dataset* Kaggle bukan pengguna Indonesia, label tanpa protokol, resolusi 224 px;
   - rekomendasi.

   Jangan ubah file CD. Setelah itu perbarui `RANGKUMAN_PROGRES.md` dan zip.

### 8.2 Pekerjaan tim (rincian di `docs/IMPLEMENTATION_GUIDE.md`)

- Pelatihan final di GPU lewat notebook Colab.
- Kompilasi Flutter dan uji di minimal dua HP Android.
- *Deploy* VPS dengan domain dan HTTPS.
- Pengujian F-01–F-20 dan S-01–S-09, uji SUS dengan 10–15 responden, dan data uji lokal 30–50 relawan (`docs/PROTOKOL_DATA_UJI_LOKAL.md`).
- Verifikasi BPOM untuk *knowledge base*.
- Bahas kritik dan draf revisi CD-1–CD-3 dengan pembimbing.
- Isi *placeholder* CD-4/CD-5 dari keluaran skrip.

## 9. Kritik yang masih terbuka (ringkas; rinciannya di `docs/KRITIK_DAN_REKOMENDASI_REVISI.md`)

- **A1:** foto seluruh wajah 224 px ≈ 0,8 mm/piksel, sehingga pori dan garis halus tidak terlihat. Klaim harus dilunakkan; analisis per area wajah menjadi pengembangan lanjutan.
- **A2:** cahaya dan pantulan adalah sumber kesalahan utama. *Quality gate* dan protokol foto sudah ada, tetapi ambangnya belum dikalibrasi.
- **A3:** *dataset* belum dianalisis. Skrip audit sudah ada, tetapi belum dijalankan dengan data nyata. Asal label, warna kulit, dan keterwakilan pengguna Indonesia belum terdokumentasi.
- **A4:** spesifikasi CD-2 belum terukur. Draf tabel S1–S12 sudah ada.
- **A5:** rating matriks keputusan dibuat sebelum eksperimen. *Ensemble* harus dibuktikan dengan uji McNemar; bila tidak signifikan, EfficientNetB0 yang lebih ringan dipilih.
- **B (istilah dan konsistensi):**
  - *multimodal* vs *multimodel*;
  - Flutter adalah *framework* (bahasanya Dart), dan Retrofit tidak dipakai;
  - batasan EfficientNet seharusnya α·β²·γ² ≈ 2;
  - nama karakteristik ISO/IEC 25010:2023 perlu diverifikasi;
  - metrik tiga kelas memakai rata-rata makro.
- **C (klaim berlebihan):** *Diagnostic Scan*, *clinical-grade*, label *Type IV* (skala Fitzpatrick), *heatmap* sebagai "kadar sebum", dan "kalibrasi hormonal". Sudah diperbaiki di aplikasi dan draf CD-4; revisi CD-3 sudah didrafkan.
- **D (rujukan dan data):**
  - referensi [5] dan [14] belum terverifikasi, dan [13] dipakai di luar konteksnya;
  - data konsumen Indonesia belum ada;
  - frasa ISO 27001 perlu diperbaiki;
  - foto wajah adalah data biometrik menurut UU PDP.
- **Masalah kecil:** layar *Analyzing* di Flutter menganggap semua HTTP 422 sebagai "retake photo", termasuk kesalahan validasi. *Web app* sudah membedakannya.

## 10. Langkah pertama di sesi ini

1. Ekstrak repositori: `cd /home/claude && unzip -q -o /mnt/user-data/uploads/glowrithm.zip`. Sesuaikan nama file bila berbeda.
2. Instal paket: `pip install --break-system-packages "tensorflow-cpu>=2.16,<3" -r glowrithm/ml/requirements.txt -r glowrithm/backend/requirements.txt scikit-image h5py`.
3. Jalankan `cd glowrithm/ml && python scripts/fetch_offline_weights.py` bila akan melatih model.
4. Jalankan `cd ../backend && python -m pytest -q`; hasil yang diharapkan adalah 24 *passed*.
5. Kerjakan permintaan saya di bawah. Bila permintaan itu butuh *dataset* dan zip-nya tidak terlampir, minta ke saya; jangan mencoba mengunduh dari Kaggle.

## Permintaan saya sekarang

[tulis permintaan di sini]
