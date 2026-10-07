# Kritik Teknis dan Rekomendasi Revisi — Glowrithm

Telaah kritis terhadap CD-1 (Usulan Gagasan), CD-2 (Spesifikasi dan Batasan Solusi), dan CD-3 (Desain Rancangan Solusi), ditambah catatan untuk draf CD-4/CD-5 dan kode. Status per 7 Oktober 2026.

Setiap kekurangan diberi kode (misalnya **A1**, **B3**). Teks pengganti yang siap ditempel ada di `DRAF_REVISI_CD1-CD3.md` dengan kode revisi **R1-x** (CD-1), **R2-x** (CD-2), dan **R3-x** (CD-3).

**Keterangan status:**
- **Sudah ditangani:** sudah diterapkan di kode dan/atau draf CD-4/CD-5.
- **Draf tersedia:** teks revisi sudah disiapkan, tinggal diterapkan tim ke dokumen Word setelah disetujui pembimbing.
- **Perlu tim:** butuh data, pengukuran, atau keputusan tim.

---

## 1. Ringkasan penilaian

### Yang sudah baik
- **Struktur runtut.** Analisis masalah mencakup aspek teknis, medis, etika, dan ekonomi.
- **Keputusan terdokumentasi.** CD-3 memakai matriks keputusan berbobot, sehingga pemilihan solusi bisa ditelusuri.
- **Kesadaran regulasi sejak awal.** Privasi (UU PDP, ISO/IEC 27001) dan keamanan bahan (BPOM) sudah muncul di CD-2.
- **Pembeda yang jelas.** Penjelasan visual (Grad-CAM) membuat solusi ini lebih transparan daripada aplikasi sejenis.
- **Rencana kerja realistis.** RAB masuk akal dan Gantt chart rinci.

### Kelemahan utama (urut dampak)
1. **Resolusi masukan tidak sesuai klaim.** Foto seluruh wajah diperkecil ke 224 × 224 piksel (sekitar 0,8 mm per piksel), sehingga pori dan garis halus yang diklaim praktis tidak terlihat.
2. **Pencahayaan dan pantulan belum dipandu atau diperiksa**, padahal kilap dari *flash* atau lampu menyerupai kulit berminyak.
3. ***Dataset* belum dianalisis** dan belum ada validasi pada pengguna Indonesia.
4. **Spesifikasi CD-2 belum terukur.** Target angka baru muncul di matriks keputusan CD-3.
5. **Rating matriks keputusan belum berbasis bukti** dan tidak konsisten soal pemakaian metadata.

---

## 2. Daftar kekurangan

### A. Masalah mendasar (berpengaruh pada hasil)

| Kode | Lokasi | Kekurangan | Rekomendasi | Prioritas | Status |
|---|---|---|---|---|---|
| A1 | CD-2 Tabel 2.2; CD-3 3.2 (Gambar 3.1), 3.7 | Klaim mengenali pori, garis halus, dan tekstur; Gambar 3.1 berupa tekstur kulit jarak dekat, bukan foto wajah seperti masukan sistem | Akui batas resolusi, ganti Gambar 3.1, rencanakan analisis per area wajah | Tinggi | Draf tersedia (R2-4, R3-10); analisis per area: perlu tim |
| A2 | CD-2 Tabel 2.1 (batasan kondisi citra); CD-3 3.9.2 | Tidak ada protokol pengambilan foto; tombol *flash* justru disediakan | Protokol foto + *quality gate*; hapus *flash* | Tinggi | Sudah ditangani (kode, CD-4); draf R2-6, R3-9 |
| A3 | CD-3 3.11.3 | *Dataset* hanya disebut "Kaggle": tanpa jumlah per kelas, asal label, kondisi foto, komposisi warna kulit | Audit *dataset*, deduplikasi, data uji lokal | Tinggi | Skrip & protokol tersedia; pengumpulan data: perlu tim |
| A4 | CD-2 Tabel 2.2 | Spesifikasi hanya deskripsi fungsi, tanpa target | Tabel spesifikasi terukur | Tinggi | Draf tersedia (R2-1) |
| A5 | CD-3 2.1–2.2, Tabel 2.1 | Rating akurasi 3 (>90%) sebelum eksperimen; Solusi 3 dinilai rendah karena metadata padahal Solusi 1 juga memakai usia dan jenis kelamin; tidak ada pembanding model tunggal | Nyatakan rating sebagai estimasi literatur, koreksi rating regulasi Solusi 1, verifikasi lewat ablasi + McNemar | Tinggi | Draf tersedia (R3-1); skrip uji tersedia |

### B. Inkonsistensi teknis

| Kode | Lokasi | Kekurangan | Rekomendasi | Prioritas | Status |
|---|---|---|---|---|---|
| B1 | CD-1 1.2.1 dan Kesimpulan; CD-3 | Istilah *multimodal* (banyak jenis data) dan *multimodel* (banyak model) tercampur; kesimpulan CD-1 merekomendasikan multimodal, CD-3 memilih multimodel satu modalitas | Definisikan sebagai *ensemble* berbasis fusi fitur dengan satu modalitas (citra) | Sedang | Draf tersedia (R1-3, R3-4) |
| B2 | CD-2 Tabel 2.3 | Flutter ditulis sebagai bahasa pemrograman (bahasanya Dart); Retrofit (pustaka Android *native*) dan Firebase SDK dicantumkan | Sesuaikan dengan teknologi yang dipakai | Sedang | Draf tersedia (R2-2) |
| B3 | CD-3 Pers. (3.2)–(3.4) | Batasan *compound scaling* tertulis "α . β . γ2 ≈" | Benar: α · β² · γ² ≈ 2 | Sedang | Draf tersedia (R3-2) |
| B4 | CD-2 bagian 1 dan 2 | ISO/IEC 25010:2023 dikutip dengan nama karakteristik edisi lama | Sesuaikan nama (verifikasi ke standar) | Rendah | Draf tersedia (R2-3) |
| B5 | CD-2 Tabel 2.2 dan 3.1; CD-3 3.6 | "Seleksi fitur", "standardisasi kontras piksel", "pembersihan piksel rusak" tidak ada di desain maupun implementasi | Ganti dengan proses yang benar-benar dilakukan | Sedang | Draf tersedia (R2-4) |
| B6 | CD-3 Gambar 3.2, 3.7 | Gambar ResNet-34; varian EfficientNet dan ukuran masukan tidak disebut | ResNet50V2, EfficientNetB0, masukan 224 × 224 | Rendah | Draf tersedia (R3-3) |
| B7 | CD-3 Pers. (3.5)–(3.8) | Rumus metrik untuk dua kelas | *One-vs-rest* + rata-rata makro | Rendah | Sudah di CD-4/CD-5; draf R3-5 |
| B8 | CD-2 Tabel 2.3 | "Perangkat Android dengan arsitektur minimum tertentu" tidak terukur | Android 10 (API 29)+, arm64, RAM 4 GB | Rendah | Draf tersedia (R2-2) |

### C. Klaim berlebihan

| Kode | Lokasi | Kekurangan | Rekomendasi | Prioritas | Status |
|---|---|---|---|---|---|
| C1 | CD-3 3.9 dan *mock-up* | "Diagnostic Scan", "clinical skin analysis", "clinical-grade ingredients", "hasil klasifikasi medis" bertentangan dengan batasan CD-2 (bukan diagnosis) | Ganti istilah | Tinggi | Sudah di aplikasi; draf R3-6 |
| C2 | CD-3 3.9.3 | "Analisis topologi resolusi tinggi", padahal Grad-CAM berasal dari peta fitur 7 × 7 | Hapus | Sedang | Draf R3-6 |
| C3 | CD-3 Gambar 3.4 | Label "Type IV" adalah skala Fitzpatrick (warna kulit), bukan jenis kulit | Hapus | Sedang | Sudah di aplikasi; draf R3-6 |
| C4 | CD-3 3.9.3 | Warna hangat *heatmap* disebut "konsentrasi sebum" | Area yang paling memengaruhi keputusan model | Tinggi | Sudah di aplikasi & CD-4; draf R3-6 |
| C5 | CD-3 3.9.1 dan 3.10.2 | Usia dan jenis kelamin untuk "kalibrasi *baseline* hormonal ... algoritma"; tidak diimplementasikan dan bertentangan dengan CD-2 | Aturan personalisasi yang transparan | Tinggi | Sudah di kode & CD-4; draf R3-7 |

### D. Landasan dan referensi

| Kode | Lokasi | Kekurangan | Rekomendasi | Prioritas | Status |
|---|---|---|---|---|---|
| D1 | CD-1 1.1 | Data pasar kosmetik global tidak membuktikan masalah inti; belum ada data Indonesia | Bukti salah menilai jenis kulit sendiri + survei kecil | Sedang | Draf R1-1; survei: perlu tim |
| D2 | CD-1 bagian 2 | Belum ada pembanding produk nyata (Olay Skin Advisor, Neutrogena Skin360, analisis kulit YouCam) | Tabel pembanding | Sedang | Draf R1-2; fitur produk perlu diverifikasi |
| D3 | CD-3 Daftar Pustaka [5], [13], [14] | [14] "J. Smith et al." sulit dilacak; [5] (Grad-CAM untuk teks medis) kurang relevan; [13] (serum niacinamide) dipakai untuk vitamin C dan *sunscreen* | Verifikasi atau ganti | Sedang | Draf R3-8 |
| D4 | CD-2 bagian 1 dan 2.4 | Klaim mengacu ISO/IEC 27001, padahal itu standar sistem manajemen organisasi | "Mengacu pada kontrol yang relevan" | Rendah | Draf R2-5 |
| D5 | CD-2 2.4 | Foto wajah adalah data pribadi spesifik (biometrik) menurut UU PDP; belum ada penilaian risiko | Tabel risiko dan mitigasi | Sedang | Sudah di CD-4; draf R2-5 |
| D6 | CD-1 1.3 | Tujuan belum terukur | Tujuan dengan target angka | Sedang | Draf R1-4 |

### E. Keputusan teknis yang perlu justifikasi tertulis

| Kode | Lokasi | Kekurangan | Rekomendasi | Status |
|---|---|---|---|---|
| E1 | CD-2/CD-3 | Pemilihan Flutter belum dibandingkan alternatif | Tabel pembanding *framework* | Sudah di CD-4 |
| E2 | CD-3 | Manfaat *ensemble* belum dibuktikan | Ablasi + uji McNemar + aturan keputusan | Skrip tersedia; perlu dijalankan |
| E3 | CD-3 3.4 dan 3.11.2 | TFLite di perangkat dan *backend* disebut bersamaan | Inferensi di *server*; TFLite sebagai pembanding efisiensi | Sudah di CD-4 |

### F. Kritik terhadap draf CD-4/CD-5 dan kode yang saya buat

| Kode | Kekurangan | Perbaikan | Status |
|---|---|---|---|
| F1 | Tombol lampu (*torch*) di halaman *Scan* menimbulkan pantulan | Tombol dihapus, *flash* dimatikan | Sudah |
| F2 | Teks "AI diagnostic active" bernada diagnosis | Menjadi "AI analysis active" | Sudah |
| F3 | Kriteria Grad-CAM di CD-5 (≥ 80% fokus pada kulit) subjektif | *Deletion test* kuantitatif + penilaian visual | Sudah |
| F4 | Uji ablasi hanya membandingkan angka | Uji McNemar + IK *bootstrap* selisih F1 | Sudah |
| F5 | Evaluasi hanya satu kali *split* | Validasi silang 5-*fold* + IK Wilson | Sudah |
| F6 | Belum ada validasi pada pengguna sasaran | Validasi lapangan (protokol + skrip) | Sudah; data: perlu tim |
| F7 | Ambang *quality gate* belum dikalibrasi | `quality_report.py` | Perlu tim |

---

## 3. Rekomendasi perbaikan teknis

### Prioritas 1 — sudah dikerjakan

1. **Protokol foto dan *quality gate*.**
   - **Alasan:** kesalahan terbesar pada analisis kulit dari foto berasal dari cahaya dan pantulan, bukan dari arsitektur model.
   - **Kode:**
     - `ml/glowrithm_ml/quality.py` memeriksa kecerahan, pantulan, ketajaman (variansi Laplacian), dan ukuran wajah sebelum model dijalankan.
     - *Backend* membalas 422 beserta saran perbaikan untuk foto yang tidak layak.
     - Aplikasi menampilkan protokol (cuci muka, tunggu ±1 jam, cahaya alami, tanpa *flash*), menyediakan tombol *Retake photo*, dan menampilkan peringatan kualitas.
2. **Evaluasi yang lebih kuat.**
   - **Alasan:** satu angka akurasi dari satu *split* kecil mudah dipertanyakan.
   - **Skrip:**
     - `crossval.py`: validasi silang 5-*fold* berbasis grup, hasil rata-rata ± SD dan IK 95%;
     - `evaluate.py`: kini juga mengeluarkan IK Wilson;
     - `compare_models.py`: uji McNemar dan IK *bootstrap* selisih F1;
     - `xai_deletion.py`: *deletion test* Grad-CAM dengan uji Wilcoxon.
3. **Data uji lokal.**
   - **Alasan:** inilah bukti paling langsung bahwa solusi menjawab masalah CD-1 untuk pengguna Indonesia.
   - **Bahan:**
     - `docs/PROTOKOL_DATA_UJI_LOKAL.md`: protokol, rubrik uji kertas minyak, dan formulir persetujuan;
     - `ml/templates/local_test_labels.csv`: templat pencatatan;
     - `evaluate_local.py`: akurasi, kappa Cohen, hasil per kondisi cahaya, dan dampak *quality gate*.
4. **Rapikan istilah dan klaim.**
   - **Alasan:** inkonsistensi kecil memberi kesan desain tidak dipahami.
   - **Bahan:** semua teks pengganti ada di `DRAF_REVISI_CD1-CD3.md`; draf CD-4/CD-5 sudah memakai istilah yang diperbaiki.

### Prioritas 2 — jika waktu cukup
5. **Analisis per area wajah.** Ambil potongan dahi, hidung, dan pipi pada resolusi asli dengan bantuan *landmark* wajah (ML Kit/MediaPipe). Ini menjawab A1 sekaligus memungkinkan kelas kulit kombinasi.
6. **Kuesioner singkat adaptif.** Tanyakan kulit sensitif dan alergi, terutama saat *confidence* rendah. Citra tidak bisa melihat alergi, padahal itu aspek keamanan terpenting.
7. **Aturan keputusan *ensemble*.** Jika uji McNemar tidak signifikan, pakai EfficientNetB0 tunggal (sekitar 6,5 kali lebih kecil). Ini sesuai bobot efisiensi di matriks CD-3 sendiri.

### Prioritas 3 — pengembangan lanjutan (ditulis di saran CD-5)
8. **Inferensi di perangkat dengan CAM.** CAM tidak memerlukan gradien, sehingga foto tidak pernah meninggalkan ponsel.
9. **Pemindai daftar bahan (OCR INCI) pada kemasan.** Hasilnya dicocokkan dengan jenis kulit dan status BPOM.

---

## 4. Evaluasi pilihan Flutter

**Kesimpulan:** tetap gunakan Flutter. Aplikasi bersifat *thin client* karena inferensi dan Grad-CAM berjalan di *server*, jadi yang dibutuhkan hanya kamera, UI, dan HTTP, dan semuanya didukung *plugin* yang matang. Flutter juga sudah disetujui di CD-2/CD-3.

| *Framework* | Kelebihan | Kekurangan | Sesuai jika |
|---|---|---|---|
| Flutter (dipilih) | Satu kode Android/iOS, *hot reload*, *plugin* matang | Kontrol kamera terbatas (tanpa kunci *white balance*), ML di perangkat lewat *plugin* komunitas | Inferensi di *server* |
| Kotlin + Jetpack Compose | Kontrol penuh CameraX/Camera2, integrasi resmi LiteRT/MediaPipe/ML Kit | Hanya Android, pengembangan lebih lama | Inferensi dipindah ke ponsel |
| React Native | Ekosistem JavaScript, VisionCamera dengan *frame processor* | Konfigurasi *native* rumit | Tim menguasai JavaScript |
| Web (PWA) | Tanpa instalasi, mudah dibagikan untuk uji SUS | Kontrol kamera paling lemah | Prototipe atau demo cepat |

Tabel ini sudah dimasukkan ke CD-4 sebagai justifikasi tertulis.

---

## 5. Alternatif pendekatan untuk mencapai tujuan CD

Tujuan CD: membantu pengguna memilih bahan aktif yang cocok secara objektif, transparan, aman, dan menjaga privasi.

| Alternatif | Ide | Kelebihan | Kekurangan |
|---|---|---|---|
| A. Desain sekarang | *Ensemble* CNN di *server* + Grad-CAM + *knowledge base* | Sudah jadi, sesuai CD-3 | Bergantung internet, sensitif cahaya |
| B. Inferensi di perangkat + CAM | Model ringan di ponsel, penjelasan tanpa gradien | Foto tidak keluar dari ponsel, bisa *offline*, tanpa biaya *server* | Model harus kecil, kepala klasifikasi harus linear |
| C. Analisis per area | Klasifikasi potongan dahi, hidung, dan pipi lalu digabung | Tekstur kulit terjaga, bisa mendeteksi kulit kombinasi | Butuh *landmark* dan label tambahan |
| D. Prediksi atribut | Nilai kilap, pori, kekeringan, kemerahan, jerawat, lalu petakan dengan aturan | Paling mudah dijelaskan | Butuh label per atribut |
| E. Citra + kuesioner | Probabilitas model digabung dengan kuesioner tervalidasi | Menangkap sensitivitas dan alergi | Ada unsur subjektif |
| F. Alat bantu murah | Kertas minyak atau lensa makro jepit | Pengukuran lebih objektif | Kurang praktis |
| G. Pemindai daftar bahan | OCR kemasan dicocokkan dengan jenis kulit dan BPOM | Langsung menjawab "produk ini cocok?" | Fokus bergeser |

**Rekomendasi:**
- Pertahankan A sebagai inti.
- Unsur F sudah dipakai sebagai label acuan validasi lapangan.
- Unsur E dapat ditambahkan untuk keamanan (alergi dan sensitivitas).
- C layak dicoba jika waktu cukup.
- B dan G cocok ditulis sebagai pengembangan lanjutan di CD-5.

---

## 6. Cara memproses revisi

1. Bahas daftar ini dengan pembimbing, dimulai dari prioritas tinggi (A1–A5, C1, C4, C5).
2. Terapkan teks dari `DRAF_REVISI_CD1-CD3.md` ke dokumen Word CD-1, CD-2, dan CD-3 yang sudah disetujui.
3. Isi tabel *Timeline Revisi Dokumen* setiap CD (usulan barisnya ada di draf revisi), naikkan nomor revisi, dan perbarui jumlah halaman.
4. Pastikan CD-4/CD-5 tetap konsisten dengan revisi. Draf terbaru sudah memakai istilah dan desain yang diperbaiki.
5. Verifikasi semua butir bertanda "[verifikasi]" dan semua referensi baru sebelum dokumen dikumpulkan.
