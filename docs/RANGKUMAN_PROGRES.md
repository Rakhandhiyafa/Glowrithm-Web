# Rangkuman Progres Capstone Glowrithm

Sistem rekomendasi kandungan bahan *skincare* berdasarkan klasifikasi kulit wajah berbasis *deep learning*.
Status per 7 Oktober 2026.

## Ringkasan status

| Komponen | Status | Yang masih kurang |
|---|---|---|
| Draf CD-4 (Implementasi) | Draf diperbarui, 48 halaman | Isi *placeholder* kuning, *screenshot*, hasil pelatihan |
| Draf CD-5 (Pengujian dan Analisis) | Draf diperbarui, 23 halaman | Semua hasil pengujian dan analisis |
| Kode model *deep learning* | Selesai, diuji dengan data sintetis | Pelatihan dengan *dataset* nyata |
| *Backend* API | Selesai, 24/24 tes lulus | *Deploy* ke VPS dengan HTTPS |
| *Web app* untuk pengujian | Selesai, uji *end-to-end* di *browser* lulus (mode demo) | Diuji dengan model terlatih dan di ponsel tim |
| Uji awal model dengan *dataset* Kaggle | Skrip siap (audit, pelatihan CPU/GPU, notebook Colab) | Menunggu *dataset* (Kaggle diblokir di *workspace* Claude) |
| Aplikasi *mobile* | Kode selesai | Dikompilasi dan dijalankan di ponsel |
| *Deployment* | Konfigurasi siap | Dijalankan di VPS |
| Panduan | `docs/IMPLEMENTATION_GUIDE.md` | – |
| Kritik dan draf revisi CD-1–CD-3 | Selesai | Dibahas dengan pembimbing, lalu diterapkan ke dokumen Word |
| Prioritas 1 (*quality gate*, evaluasi statistik, data uji lokal) | Kode selesai, diuji dengan data sintetis | Kalibrasi ambang, data nyata, pengumpulan data lokal |

---

## Pembaruan: *web app* pengujian dan persiapan uji awal *dataset* Kaggle

- ***Web app* pengujian** (`web/`, disajikan *backend* di `/app/`): alur aplikasi Android di *browser*, yaitu persetujuan, profil, kamera langsung atau unggah foto dengan panduan oval, cek foto, analisis, hasil dengan Grad-CAM, rekomendasi, riwayat, dan profil. Panel *Test details* dan tombol *Copy test record* membantu pencatatan uji. Panduan: `docs/PANDUAN_UJI_WEB_APP.md`.
- **Uji *end-to-end*:** 17 langkah di Chromium *headless* (layar ponsel, kamera tiruan) lulus dengan model demo, termasuk penolakan foto gelap oleh *quality gate* dan penghapusan data saat persetujuan ditarik.
- **Perbaikan yang ditemukan saat pengujian:**
  - OpenCV 5 menghapus detektor wajah Haar, jadi versinya dikunci `<5`;
  - foto kamera langsung kini dipotong sesuai area pratinjau agar pemeriksaan ukuran wajah adil di webcam laptop;
  - notifikasi tidak lagi menghalangi tombol rana.
- **Persiapan uji *dataset*:**
  - `audit_dataset.py`: jumlah per kelas, duplikat termasuk salinan cermin dan salinan Roboflow, kebocoran antar-*split*, deteksi wajah;
  - deduplikasi bersama di `glowrithm_ml/dedup.py`, dengan batas ukuran grup agar rantai kemiripan tidak menggabungkan orang berbeda;
  - `train_cached.py`: pelatihan cepat di CPU dengan fitur beku;
  - `fetch_offline_weights.py`: bobot ImageNet dari rilis resmi GitHub;
  - notebook Colab kini mengaudit *dataset*, menjalankan uji McNemar, dan membuka *web app* lewat HTTPS.
- **Status:** Kaggle diblokir di *workspace* Claude, jadi pelatihan dengan *dataset* tersebut belum dijalankan. Lampirkan zip *dataset* untuk dijalankan di sini, atau jalankan notebook Colab.

---

## Pembaruan sebelumnya: revisi dan prioritas 1

- **Kritik dan draf revisi.** `KRITIK_DAN_REKOMENDASI_REVISI.md` memuat 34 kekurangan berkode (A–F) beserta rekomendasi, evaluasi Flutter, dan alternatif pendekatan. `DRAF_REVISI_CD1-CD3.md` berisi teks pengganti siap tempel (R1-1 sampai R3-13) dan usulan baris *Timeline Revisi Dokumen*.
- ***Quality gate*.** `ml/glowrithm_ml/quality.py` memeriksa kecerahan, pantulan, ketajaman, dan ukuran wajah sebelum model dijalankan. *Backend* membalas kode 422 beserta saran perbaikan (mode `GLOWRITHM_QUALITY_GATE`: `reject`, `warn`, `off`).
- **Aplikasi.** *Flash* dimatikan dan tombolnya dihapus, protokol foto tampil otomatis, tombol *Retake photo* muncul untuk foto yang ditolak, peringatan kualitas tampil di halaman hasil, dan teks diganti menjadi "AI analysis active".
- **Evaluasi statistik.** `crossval.py` (validasi silang 5-*fold*), interval Wilson di `evaluate.py`, `compare_models.py` (uji McNemar dan IK *bootstrap*), `xai_deletion.py` (*deletion test* Grad-CAM dengan uji Wilcoxon), dan `quality_report.py` (kalibrasi ambang).
- **Data uji lokal.** `docs/PROTOKOL_DATA_UJI_LOKAL.md` (protokol, rubrik uji kertas minyak, formulir persetujuan), `ml/templates/local_test_labels.csv`, dan `evaluate_local.py` (akurasi, kappa Cohen, hasil per kondisi cahaya, dampak *quality gate*).
- **Pengujian.** 22/22 tes *backend* lulus (9 API, 7 rekomendasi, 6 *quality gate*). Semua skrip baru berjalan dari awal sampai akhir pada data sintetis, dan sintaks Dart bersih.
- **Draf CD-4 dan CD-5 diperbarui.**
  - CD-4 memuat subbab *quality gate*, perbandingan *framework*, penilaian risiko pelindungan data, dan alat evaluasi baru.
  - CD-5 memuat validasi silang, uji McNemar, *deletion test*, subbab validasi lapangan, kasus F-17 sampai F-20, dan rekap 11 indikator.

---

## 1. Yang sudah dikerjakan

### 1.1 Draf dokumen CD-4 dan CD-5

Kedua draf dibangun langsung di atas *template* Word asli, jadi sampul, lembar pengesahan, dan *footer* Telkom tetap utuh. Nama, NIM, pembimbing, dan tanggal dibiarkan sebagai *placeholder*, dan tabel revisi dikosongkan.

**CD-4 (Implementasi)** berisi:
- **Deskripsi umum:** wujud akhir solusi, tahapan implementasi, alat dan bahan, serta tabel penyesuaian terhadap rancangan CD-3.
- **Detail implementasi:**
  - 20 potongan kode beserta penjelasannya, diambil otomatis dari repositori;
  - 3 diagram (arsitektur sistem, arsitektur model, alur data);
  - 9 persamaan Word dan tabel jumlah parameter model;
  - 13 kotak *placeholder* untuk *screenshot* dan grafik.
- **Prosedur pengoperasian:** untuk pengembang/operator dan untuk pengguna aplikasi, ditambah tabel penanganan masalah.
- **Daftar Pustaka:** 32 referensi IEEE.

**CD-5 (Pengujian dan Analisis)** berisi:
- **Skenario umum:** 11 pengujian yang dipetakan ke spesifikasi CD-2, lengkap dengan lokasi, waktu, pihak, lingkungan, dan data uji.
- **Detail pengujian:**
  - kinerja klasifikasi (dengan validasi silang), ablasi (dengan uji McNemar), ketahanan, Grad-CAM (dengan *deletion test*), dan validasi lapangan;
  - 20 kasus *black-box*, 6 kasus rekomendasi, dan 9 kasus keamanan;
  - kinerja/efisiensi, kompatibilitas perangkat, dan SUS (10 pernyataan berbahasa Indonesia).
- **Analisis:** rekap pemenuhan spesifikasi, faktor pendukung dan penghambat, keterbatasan, serta kesimpulan dan saran.
- **Daftar Pustaka:** 19 referensi.

> Tidak ada angka hasil yang dikarang. Semua angka yang harus diukur ditandai *placeholder* kuning `[…]`. Satu-satunya angka yang terisi adalah jumlah parameter model, yang dihitung langsung dari kode.

### 1.2 Model *deep learning* (`ml/`)

**Arsitektur** mengikuti Solusi 1 di CD-3, yaitu *ensemble* CNN homogen dengan *feature concatenation*:

```
foto RGB 224×224 ─┬─ Rescaling → ResNet50V2 → GAP (2048) ─┐
                  └─ EfficientNetB0 ────────→ GAP (1280) ─┴─ Concatenate (3328)
                     → Dropout 0,4 → Dense 256 ReLU + L2 → Dropout 0,3 → Dense 3 (logits) → Softmax
```

| Model | Jumlah parameter |
|---|---|
| *Ensemble* ResNet50V2 + EfficientNetB0 (usulan) | 28.467.366 |
| ResNet50V2 saja (pembanding ablasi) | 24.090.115 |
| EfficientNetB0 saja (pembanding ablasi) | 4.378.278 |

**Berkas yang dibuat:**

| Berkas | Fungsi |
|---|---|
| `glowrithm_ml/preprocessing.py` | Koreksi orientasi EXIF, deteksi wajah *Haar cascade*, *crop* persegi (margin 30%), *resize* 384 → 224. Dipakai bersama oleh pelatihan dan API. |
| `glowrithm_ml/data.py` | *Pipeline* `tf.data`, augmentasi, *oversampling* atau *class weight* |
| `glowrithm_ml/model.py` | Model *ensemble*, model pembanding, model demo, pembekuan *backbone* |
| `glowrithm_ml/gradcam.py` | Grad-CAM per *backbone*, fusi, dan pewarnaan JET |
| `glowrithm_ml/metrics.py` | TP/FP/FN/TN, presisi, *recall*, F1, ROC-AUC, dan grafik |
| `scripts/prepare_dataset.py` | Deduplikasi MD5 + dHash, buang label konflik, *crop* wajah, *split* 70/15/15 berbasis grup |
| `scripts/train.py` | Pelatihan dua tahap, menyimpan `model.keras` + `model_meta.json` |
| `scripts/evaluate.py` | Metrik data uji, *confusion matrix*, ROC, cek target 90% |
| `scripts/robustness.py` | 8 gangguan: gelap, terang, kontras rendah, cahaya hangat, buram, derau, JPEG 30, miring 15° |
| `scripts/gradcam_report.py` | Gambar Grad-CAM untuk prediksi benar dan salah per kelas |
| `scripts/export_tflite.py` | Ekspor TFLite float16/dinamis dan cek kesamaan prediksi |
| `scripts/benchmark.py` | Latensi praproses, prediksi, Grad-CAM, TFLite; ukuran model |
| `scripts/predict.py` | Klasifikasi satu foto dan simpan *overlay* Grad-CAM |
| `scripts/sus_score.py` | Menghitung skor SUS dari CSV kuesioner |
| `config.yaml` | Seluruh *hyperparameter* |
| `notebooks/glowrithm_colab.ipynb` | Pelatihan di Google Colab (GPU) |

**Konfigurasi pelatihan:**

| Parameter | Nilai |
|---|---|
| Tahap 1 (*backbone* beku) | Maks. 15 *epoch*, Adam lr 1×10⁻³ |
| Tahap 2 (*fine-tuning*) | Maks. 30 *epoch*, lr 1×10⁻⁵, 30% lapisan teratas dibuka (*BatchNorm* tetap beku) |
| Regularisasi | *Dropout* 0,4 dan 0,3; L2 1×10⁻⁴; *label smoothing* 0,05 |
| Ketidakseimbangan kelas | *Oversampling* (peluang sama per kelas) |
| *Callback* | *Checkpoint* F1 makro validasi terbaik, *early stopping* (*patience* 6), *ReduceLROnPlateau* (0,3 / 3) |
| *Batch* / *seed* | 32 / 42 |

### 1.3 *Backend* API (`backend/`)

- ***Endpoint*:** `GET /api/v1/health`, `GET /api/v1/skin-types`, `GET /api/v1/ingredients`, dan `POST /api/v1/analyze`.
- **Isi respons `/analyze`:** label jenis kulit, *confidence*, probabilitas 3 kelas, citra wajah dan *heatmap* 384×384, rekomendasi, serta waktu proses.
- **Privasi:**
  - persetujuan wajib (tanpa persetujuan ditolak dengan kode 400);
  - ukuran foto maksimal 8 MB (413) dan hanya JPEG/PNG (415);
  - usia dibatasi 13–100 tahun;
  - foto tidak disimpan atau dicatat di log, dan respons diberi `Cache-Control: no-store`;
  - kunci API opsional.
- ***Knowledge base*:**
  - 9 bahan aktif, 3 rutinitas *Cleanse–Treat–Protect*, 4 kelompok bahan terlarang BPOM, dan 6 aturan personalisasi usia/jenis kelamin;
  - semua catatan BPOM masih bertanda `verified: false`.
- **Skor kecocokan:** `Mᵢ = clip(Σ p(c)·sᵢ(c) + Σ Δ aturan, 0, 1)`. Bahan berstatus dilarang tidak pernah direkomendasikan.
- **Mode demo:** `GLOWRITHM_DEMO_MODE=1` menjalankan model kecil tanpa pelatihan, supaya aplikasi bisa dicoba sebelum model asli siap.
- **Tes:** 22 kasus (9 API, 7 rekomendasi, 6 *quality gate*), semuanya lulus.

### 1.4 Aplikasi *mobile* (`mobile/`)

Aplikasi Flutter untuk Android, terdiri dari 25 berkas Dart (sekitar 3.000 baris) dan mengikuti *mock-up* CD-3.

| Halaman | Isi |
|---|---|
| *Consent* | Penjelasan pemrosesan data (UU PDP), wajib dicentang |
| Profil | Usia dan jenis kelamin; di bawah 18 tahun wajib persetujuan orang tua/wali |
| Beranda | Tombol mulai analisis, hasil terakhir, cara kerja |
| *Scan* | Kamera *live*, panduan oval wajah, ganti kamera, lampu, galeri, tips |
| Konfirmasi foto | *Retake* atau *Analyze photo* |
| Proses analisis | Tahapan proses, pesan galat, dan *Try again* |
| Hasil | Grad-CAM dengan *slider* opasitas, jenis kulit, *confidence*, probabilitas, peringatan |
| Rekomendasi | *Cleanse–Treat–Protect*, % kecocokan, status BPOM, detail bahan, *Save to history* |
| Riwayat | Hasil tersimpan tanpa foto, geser untuk hapus, hapus semua |
| Profil dan privasi | Edit profil, hapus data, tarik persetujuan, pengaturan alamat *server* + uji koneksi |

Komponen pendukung:
- **Klien API:** unggah *multipart*, *timeout* 60 detik, dan pesan galat yang mudah dipahami.
- **Penyimpanan:** terenkripsi dengan `flutter_secure_storage`.
- ***State*:** dikelola dengan Provider.
- **Konfigurasi:** alamat API lewat `--dart-define`, atau diubah langsung di aplikasi.
- **Tes:** 3 kasus uji.
- **Skrip `tool/patch_android.py`:** mengatur izin, mematikan *backup*, dan mengizinkan HTTP hanya di versi *debug*.

### 1.5 *Deployment* dan dokumentasi

- **`backend/Dockerfile`:** Python 3.11 *slim*, TensorFlow-CPU, berjalan sebagai pengguna non-*root*, dengan *health check*.
- **`deploy/docker-compose.yml` dan `deploy/Caddyfile`:** API di belakang Caddy dengan HTTPS otomatis (Let's Encrypt).
- **Dokumentasi:** `README.md` (*quick start* mode demo), `mobile/README.md`, dan `docs/IMPLEMENTATION_GUIDE.md` (panduan langkah demi langkah).

### 1.6 Yang sudah dan belum diuji

| Bagian | Sudah diuji | Belum diuji |
|---|---|---|
| *Pipeline* ML | Semua skrip berjalan dari awal sampai akhir pada *dataset* sintetis kecil (TF 2.21, Keras 3.15) | Pelatihan dengan *dataset* nyata dan bobot ImageNet; akurasi nyata |
| Ekspor TFLite | 110 MB → 54 MB (float16), prediksi identik dengan Keras | Inferensi di ponsel (opsional) |
| *Backend* | 22/22 tes lulus; API dengan model hasil latih merespons normal | Berjalan di VPS dengan HTTPS |
| Aplikasi | Cek sintaks 27 berkas Dart (0 galat), konsistensi impor dan simbol | `flutter analyze`, kompilasi, uji di ponsel |
| Dokumen | Lolos validasi struktur Word; tampilan halaman diperiksa | Tampilan persamaan di Microsoft Word |

---

## 2. Keputusan desain yang perlu dipahami tim

Pertanyaan-pertanyaan ini kemungkinan besar muncul saat bimbingan atau sidang.

| Topik | Keputusan | Alasan |
|---|---|---|
| Varian ResNet | ResNet50V2 | Blok residual sama (Persamaan 3.1 CD-3); bobot ImageNet tersedia; normalisasi cukup dengan lapisan `Rescaling` |
| Penggabungan model | *Feature concatenation* | *Classifier* belajar sendiri cara menggabungkan fitur; manfaatnya dibuktikan lewat uji ablasi |
| Arti *heatmap* | Area yang paling memengaruhi keputusan model | Grad-CAM menjelaskan model, bukan alat ukur minyak (koreksi dari CD-3) |
| Label keamanan | Status BPOM, bukan EWG | Sesuai regulasi Indonesia yang diacu CD-2/CD-3 |
| Usia dan jenis kelamin | Hanya mengubah skor kecocokan bahan, bukan masukan model | Konsisten dengan batasan CD-2 (tidak memproses faktor hormon) |
| Lokasi inferensi | Di *server* | Grad-CAM butuh gradien; model bisa diperbarui tanpa *update* aplikasi |
| Penyimpanan | Terenkripsi di ponsel, tanpa akun, tanpa foto | Minimisasi data sesuai UU PDP; Firebase jadi pengembangan lanjutan |
| Akurasi bisa dipercaya | Duplikat dan *near-duplicate* tidak menyeberang *split* | Mencegah kebocoran data latih ke data uji |

---

## 3. Yang perlu dilanjutkan

Urutan di bawah mengikuti Gantt CD-3. Detail perintah ada di `docs/IMPLEMENTATION_GUIDE.md`.

### Tahap A — Persiapan dan uji mode demo (Oktober, minggu 2)
- [ ] Ekstrak `glowrithm.zip`, buat *virtual environment* Python 3.11, lalu `pip install -r ml/requirements.txt`, `pip install -e ml`, dan `pip install -r backend/requirements.txt`.
- [ ] Jalankan *backend* mode demo: `GLOWRITHM_DEMO_MODE=1 uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- [ ] Siapkan aplikasi: `flutter create --org id.glowrithm --platforms android .`, lalu `python tool/patch_android.py` dan `flutter pub get`.
- [ ] Jalankan `flutter analyze` dan perbaiki galat kompilasi bila ada (aplikasi belum pernah dikompilasi).
- [ ] Jalankan aplikasi di *emulator* atau ponsel dan coba semua halaman dengan mode demo.

### Tahap B — *Dataset* (Oktober, minggu 2–3)
- [ ] Pilih *dataset* tiga kelas (kering, normal, berminyak); catat nama, penyusun, lisensi, dan tautannya.
- [ ] Letakkan di `ml/data/raw/`, lalu jalankan `python scripts/prepare_dataset.py --config config.yaml`.
- [ ] Periksa `data/processed/summary.json`. Jika deteksi wajah di bawah ±70%, cek hasil *crop*; bila banyak foto *close-up*, set `crop_faces: false`.

### Tahap C — Pelatihan di Colab (Oktober minggu 3 – November minggu 1)
- [ ] Unggah `glowrithm.zip` ke Google Drive dan buka `ml/notebooks/glowrithm_colab.ipynb` dengan GPU.
- [ ] Jalankan `--smoke-test` dulu, lalu latih `--arch ensemble`, `--arch resnet`, dan `--arch effnet`.
- [ ] Simpan folder `artifacts/` ke Drive dan catat log eksperimen (perubahan, akurasi validasi, F1 validasi).
- [ ] Jika *overfitting* atau *underfitting*, ikuti tabel penyesuaian di panduan langkah 3. Ubah satu hal setiap kali.

### Tahap D — Evaluasi model (November, minggu 1)
- [ ] Jalankan `evaluate.py` untuk ketiga model.
- [ ] Jalankan `crossval.py --arch ensemble --folds 5` (dan model pembanding bila waktu cukup).
- [ ] Jalankan `compare_models.py` untuk *ensemble* vs ResNet50V2 dan *ensemble* vs EfficientNetB0 (uji McNemar).
- [ ] Jalankan `xai_deletion.py` (*deletion test* Grad-CAM) dan `quality_report.py`, lalu kalibrasi ambang *quality gate*.
- [ ] Jalankan `robustness.py`, `gradcam_report.py --per-class 3`, `export_tflite.py --quantize float16`, dan `benchmark.py`.
- [ ] Jika akurasi di bawah 90%, laporkan apa adanya beserta analisis ablasi dan ketahanan. Jangan menaikkan angka.

### Tahap E — *Backend* dan *deployment* (November, minggu 1–2)
- [ ] Salin `model.keras` dan `model_meta.json` ke `backend/models/`, jalankan `python -m pytest -q`, lalu ambil *screenshot* Swagger (`/docs`).
- [ ] Sewa VPS (disarankan 2 vCPU, RAM 4 GB), arahkan domain ke IP VPS, dan ubah domain di `deploy/Caddyfile`.
- [ ] Isi `GLOWRITHM_API_KEY` di `backend/.env`, lalu jalankan `docker compose -f deploy/docker-compose.yml up -d --build`.
- [ ] Pastikan `https://<domain>/api/v1/health` menampilkan `model_loaded: true`.

### Tahap F — Aplikasi di ponsel (November, minggu 2–4)
- [ ] Jalankan aplikasi di minimal dua ponsel Android yang terhubung ke *server* HTTPS.
- [ ] Ambil *screenshot* 11 halaman untuk CD-4 (Gambar 2.5–2.15).
- [ ] Rekam video demo 2–4 menit untuk CD-4 bagian 2.15.
- [ ] Bangun APK rilis dengan `flutter build apk --release --dart-define=API_BASE_URL=https://<domain> --dart-define=API_KEY=<kunci>`.

### Tahap G — Pengujian untuk CD-5 (Desember, minggu 1–3)
- [ ] Jalankan kasus *black-box* F-01–F-20, kasus rekomendasi R-01–R-06, dan kasus keamanan S-01–S-09; simpan *screenshot* sebagai bukti.
- [ ] Ukur waktu respons dari aplikasi: 10 kali lewat Wi-Fi dan 10 kali lewat 4G. Jalankan juga `benchmark.py` di VPS.
- [ ] Lakukan uji kompatibilitas di dua ponsel atau lebih.
- [ ] Kumpulkan data uji lokal sesuai `docs/PROTOKOL_DATA_UJI_LOKAL.md` (30–50 relawan, tiga kondisi cahaya, uji kertas minyak), lalu jalankan `evaluate_local.py`.
- [ ] Lakukan uji SUS dengan 10–15 responden (tugas T1–T5), lalu olah hasilnya dengan `python ml/scripts/sus_score.py responses.csv`.
- [ ] (Opsional, sangat disarankan) Minta apoteker atau dokter spesialis kulit memvalidasi rekomendasi.

### Tahap H — Finalisasi dokumen (Desember minggu 4 – Januari)
- [ ] Isi semua *placeholder* kuning: cari tanda `[` di Word.
- [ ] Ganti kotak *placeholder* dengan gambar hasil skrip (lihat bagian 4).
- [ ] Buka draf di **Microsoft Word** dan periksa persamaan: CD-4 (2.1)–(2.9) dan CD-5 (2.1)–(2.7).
- [ ] Perbarui tabel revisi, nomor revisi, tanggal, dan jumlah halaman setelah setiap bimbingan.
- [ ] Verifikasi catatan BPOM di `knowledge_base.json` terhadap lampiran Peraturan BPOM No. 23/2019, lalu ubah `verified` menjadi `true`.
- [ ] Konfirmasi ke pembimbing kriteria CD-5 yang ditetapkan tim (uji ketahanan, Grad-CAM, waktu respons, validasi lapangan) dan rubrik uji kertas minyak.
- [ ] Bahas `KRITIK_DAN_REKOMENDASI_REVISI.md` dengan pembimbing, lalu terapkan teks dari `DRAF_REVISI_CD1-CD3.md` ke CD-1–CD-3.

---

## 4. Peta hasil skrip ke dokumen

Nomor di bawah dihitung otomatis dari draf terbaru.

| Berkas hasil | Masuk ke |
|---|---|
| `data/processed/summary.json` | CD-4 Tabel 2.2 |
| `data/processed/quality_report.json` | CD-4 Tabel 2.4 |
| `artifacts/<arch>/model_meta.json` | CD-4 Tabel 2.8; CD-5 Tabel 1.3 |
| `artifacts/<arch>/training_curves.png` | CD-4 Gambar 2.3; CD-5 Gambar 2.3 |
| *Screenshot* Swagger `/docs` | CD-4 Gambar 2.4 |
| Spesifikasi VPS, domain, ukuran APK | CD-4 Tabel 1.3; CD-4 Tabel 2.17 |
| `reports/test/metrics.json`, `per_class_metrics.csv` | CD-5 Tabel 2.1; CD-5 Tabel 2.2; CD-5 Tabel 2.3 |
| `confusion_matrix_normalized.png`, `roc_curves.png` | CD-5 Gambar 2.1; CD-5 Gambar 2.2 |
| `artifacts/cv/<arch>/crossval.json` | CD-5 Tabel 2.4 |
| `metrics.json` ketiga model + `benchmark.json` | CD-5 Tabel 2.5 |
| `reports/test/compare_<A>_vs_<B>.json` | CD-5 Tabel 2.6 |
| `reports/robustness/robustness.csv` dan `.png` | CD-5 Tabel 2.8; CD-5 Gambar 2.4 |
| `reports/xai_deletion/deletion.json` dan `.png` | CD-5 Tabel 2.9; CD-5 Gambar 2.5 |
| `reports/gradcam/gradcam_<kelas>.png` | CD-5 Tabel 2.10; CD-5 Gambar 2.6 |
| `reports/local/local_metrics.json` | CD-5 Tabel 2.12; CD-5 Tabel 2.13; CD-5 Tabel 2.14 |
| `reports/benchmark.json` (dijalankan di VPS) | CD-5 Tabel 2.19; CD-5 Tabel 2.20 |
| Keluaran `pytest` dan `flutter test` | CD-5 Tabel 2.16 |
| Keluaran `sus_score.py` | CD-5 Tabel 2.26 |
| *Screenshot* 11 halaman aplikasi | CD-4 Gambar 2.5–2.15 |

---

## 5. Catatan penting

- **Referensi baru perlu dicek** sebelum dokumen dikumpulkan:
  - He dkk. (2016, dua makalah), Tan & Le (2019), Viola & Jones (2001), Buda dkk. (2018), Srivastava dkk. (2014);
  - Kingma & Ba (2015), Szegedy dkk. (2016), Luebberding dkk. (2013), Abadi dkk. (2016), Bradski (2000);
  - Pedregosa dkk. (2011), Deng dkk. (2009), Sokolova & Lapalme (2009), Hendrycks & Dietterich (2019);
  - Brooke (1996), Bangor dkk. (2008), Sauro (2011);
  - McNemar (1947), Dietterich (1998), Cohen (1960), Landis & Koch (1977), Wilson (1927), Petsiuk dkk. (2018), Kohavi (1995), Wilcoxon (1945), Pertuz dkk. (2013).
  
  Isi juga entri *dataset* yang masih *placeholder*, dan cek ulang referensi CD-3 [5] dan [14] yang tidak memiliki DOI.
- **Versi TensorFlow/Keras saat pelatihan dan di *server* harus sama.** Versi pelatihan tercatat di `model_meta.json`.
- **Rilis wajib HTTPS.** APK rilis menolak koneksi HTTP; HTTP hanya diizinkan di versi *debug* untuk pengembangan lokal.
- **Lindungi data responden.** Gunakan formulir persetujuan dan jangan simpan foto mereka setelah pengujian.
- **Hapus `ml/data/` dan `ml/artifacts/` sebelum repositori dibagikan.** Keduanya sudah masuk `.gitignore`.
- **Fitur opsional yang belum dibuat** (kerjakan hanya jika waktu cukup):
  - mode *offline* dengan TFLite di ponsel (tanpa *heatmap*);
  - sinkronisasi riwayat lewat Firebase (butuh alur akun dan teks persetujuan baru).

---

## 6. Berkas yang sudah diserahkan

| Berkas | Isi |
|---|---|
| `FTE-CD-4_Glowrithm_Draft.docx` | Draf CD-4 Implementasi |
| `FTE-CD-5_Glowrithm_Draft.docx` | Draf CD-5 Pengujian dan Analisis |
| `IMPLEMENTATION_GUIDE.md` | Panduan implementasi langkah demi langkah |
| `glowrithm.zip` | Kode lengkap: `ml/`, `backend/`, `mobile/`, `deploy/`, `docs/` (86 berkas) |
| `RANGKUMAN_PROGRES_GLOWRITHM.md` | Dokumen ini |
| `KRITIK_DAN_REKOMENDASI_REVISI.md` | Kritik, daftar kekurangan berkode, rekomendasi, dan alternatif |
| `DRAF_REVISI_CD1-CD3.md` | Teks revisi siap tempel untuk CD-1, CD-2, dan CD-3 |
| `docs/PROTOKOL_DATA_UJI_LOKAL.md` (dalam zip) | Protokol pengumpulan data uji lokal dan formulir persetujuan |
