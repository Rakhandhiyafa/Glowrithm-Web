# Draf Revisi CD-1, CD-2, dan CD-3 — Glowrithm

Teks pengganti yang siap ditempel ke dokumen Word. Setiap butir merujuk kode kekurangan di `KRITIK_DAN_REKOMENDASI_REVISI.md`.

**Cara pakai**
1. **Cari lokasinya.** Gunakan kutipan "Teks semula" untuk menemukan bagian yang diganti.
2. **Tempel teks usulan.** Bagian yang diawali tanda `>` adalah teks usulan.
3. **Format ulang di Word.**
   - Kata yang ditulis `*seperti ini*` dicetak miring (istilah asing).
   - Tabel markdown ditempel sebagai tabel Word dan diberi judul sesuai format.
   - Tanda `[isi ...]` adalah bagian yang harus Anda lengkapi.
4. **Sesuaikan nomor.** Nomor tabel, gambar, dan referensi mengikuti dokumen masing-masing; sesuaikan bila ada pergeseran.
5. **Bahas dulu dengan pembimbing.** Revisi yang mengubah keputusan desain (terutama R3-1) sebaiknya disetujui pembimbing sebelum diterapkan.

---

## CD-1 — Usulan Gagasan dan Pemilihan Topik

### R1-1 · Bukti masalah inti di latar belakang (D1)
**Lokasi:** 1.1 Latar Belakang Masalah, sisipkan setelah paragraf yang membahas studi *cosmetovigilance* (hal. 4).

> Permasalahan tersebut diperparah oleh ketidakakuratan konsumen dalam menilai jenis kulitnya sendiri. Mercurio dkk. [6] membandingkan penilaian klinis dengan pengukuran instrumental dalam menentukan jenis kulit; [isi temuan utama setelah membaca ulang makalah]. Untuk memperoleh gambaran kondisi di Indonesia, tim melakukan survei terhadap [isi jumlah] responden mahasiswa pada [isi bulan dan tahun]. Hasilnya, [isi]% responden memilih produk *skincare* berdasarkan rekomendasi media sosial, [isi]% tidak yakin dengan jenis kulitnya sendiri, dan [isi]% pernah mengalami iritasi atau jerawat setelah mencoba produk baru. Temuan ini menunjukkan perlunya alat bantu yang menilai kondisi kulit secara objektif sebelum konsumen memilih kandungan bahan aktif.

**Alasan:** data pasar global menunjukkan industri tumbuh, tetapi belum membuktikan bahwa konsumen salah memilih bahan karena tidak mengetahui jenis kulitnya.

**Pertanyaan survei yang disarankan** (Google Form, 5 menit):
1. Apa jenis kulit Anda? (kering / normal / berminyak / kombinasi / tidak tahu)
2. Seberapa yakin Anda dengan jawaban tersebut? (skala 1–5)
3. Apa pertimbangan utama Anda memilih produk? (rekomendasi teman / media sosial / *influencer* / kandungan bahan / harga / lainnya)
4. Apakah Anda membaca daftar kandungan bahan sebelum membeli? (selalu / kadang / tidak pernah)
5. Dalam satu tahun terakhir, pernahkah kulit Anda mengalami iritasi, kemerahan, atau jerawat setelah mencoba produk baru? (ya / tidak)

Jika survei tidak dilakukan, hapus kalimat survei dan pertahankan kalimat pertama dan kedua.

### R1-2 · Pembanding dengan aplikasi yang sudah ada (D2)
**Lokasi:** bagian 2 Analisis Solusi yang Ada, tambahkan subbab baru setelah 2.6.

> **2.7 Perbandingan dengan Aplikasi yang Telah Beredar**
>
> Selain pendekatan penelitian di atas, beberapa aplikasi komersial telah menawarkan analisis kulit berbasis foto. Perbandingan aplikasi tersebut dengan solusi yang diusulkan ditunjukkan pada Tabel 2.1.

| Aplikasi | Masukan | Keluaran | Penjelasan hasil (XAI) | Acuan regulasi BPOM | Perlakuan foto |
|---|---|---|---|---|---|
| Olay Skin Advisor | [verifikasi] | [verifikasi] | [verifikasi] | [verifikasi] | [verifikasi] |
| Neutrogena Skin360 | [verifikasi] | [verifikasi] | [verifikasi] | [verifikasi] | [verifikasi] |
| Analisis kulit YouCam | [verifikasi] | [verifikasi] | [verifikasi] | [verifikasi] | [verifikasi] |
| Kuesioner jenis kulit pada aplikasi belanja kecantikan lokal | Jawaban kuesioner | Jenis kulit, rekomendasi produk | Tidak | [verifikasi] | Tidak memakai foto |
| **Glowrithm (usulan)** | Foto wajah, usia, jenis kelamin | Jenis kulit, *confidence*, rutinitas bahan aktif | Ya (Grad-CAM) | Ya (status regulasi bahan) | Diproses di memori, tidak disimpan |

> Berdasarkan perbandingan tersebut, keunggulan yang ditawarkan solusi ini adalah penjelasan visual atas hasil klasifikasi, rekomendasi pada tingkat kandungan bahan aktif yang tidak terikat merek, pemeriksaan status regulasi BPOM, serta pemrosesan foto tanpa penyimpanan.

**Alasan:** penguji hampir pasti menanyakan perbedaan dengan aplikasi yang sudah ada. Isi kolom bertanda [verifikasi] dengan mencoba aplikasinya atau membaca halaman resminya; jangan menebak.

### R1-3 · Istilah multimodel dan multimodal (B1)
**Lokasi 1:** 1.2.1 Aspek Teknis, paragraf kedua (hal. 5).
**Teks semula:** "…memerlukan pendekatan multimodel yang mampu menyelaraskan berbagai jenis data secara efisien."

> …memerlukan pendekatan yang mampu menyelaraskan berbagai jenis data (multimodal) secara efisien.

**Lokasi 2:** 3 Kesimpulan, paragraf ketiga (hal. 10). Ganti seluruh paragraf.

> Oleh karena itu, solusi yang diusulkan adalah sistem rekomendasi yang memadukan tiga sumber informasi: hasil klasifikasi jenis kulit dari citra wajah, basis pengetahuan kandungan bahan aktif yang mengacu pada prinsip dermatologi dan regulasi BPOM, serta profil pengguna. Pada tingkat model, klasifikasi hanya menggunakan satu jenis data, yaitu citra, tetapi memanfaatkan beberapa arsitektur CNN yang fiturnya digabungkan (*multimodel ensemble*) agar lebih akurat daripada satu arsitektur. Integrasi ini memungkinkan sistem menghasilkan rekomendasi yang objektif, personal, dan aman. Sistem ini diharapkan mampu mengatasi keterbatasan metode sebelumnya sehingga relevan untuk dijadikan proyek *capstone design*.

**Alasan:** *multimodal* berarti beberapa jenis data, sedangkan *multimodel* berarti beberapa model. CD-3 memilih multimodel dengan satu modalitas (citra) dan menolak solusi multimodal (Solusi 3), sehingga kesimpulan CD-1 perlu diselaraskan.

### R1-4 · Tujuan yang terukur (D6)
**Lokasi:** 1.3 Tujuan Capstone. Ganti paragraf pertama, pertahankan paragraf aplikasi *mobile*.

> Tujuan *Capstone Design* ini adalah sebagai berikut.
> 1. Mengembangkan model klasifikasi jenis kulit wajah (normal, kering, berminyak) dari citra dengan akurasi minimal 90% pada data uji.
> 2. Menyediakan penjelasan visual berbasis Grad-CAM untuk setiap hasil klasifikasi agar keputusan model dapat dipahami pengguna.
> 3. Menghasilkan rekomendasi kandungan bahan aktif yang sesuai dengan jenis kulit dan memperhatikan status regulasi BPOM.
> 4. Mengimplementasikan sistem dalam aplikasi Android dengan waktu respons rata-rata maksimal 5 detik dan skor *System Usability Scale* (SUS) di atas 70.
> 5. Memproses data wajah sesuai prinsip UU PDP, yaitu persetujuan eksplisit, komunikasi terenkripsi, dan tanpa penyimpanan foto.

**Alasan:** tujuan yang terukur memudahkan CD-5 menilai keberhasilan solusi. Angka 90% sudah dipakai di CD-3; target lain dikonfirmasi bersama pembimbing.

### Usulan baris *Timeline Revisi Dokumen* CD-1

| Versi, Tanggal | Revisi | Perbaikan yang dilakukan | Halaman revisi |
|---|---|---|---|
| 4, [isi tanggal] | Bukti masalah inti belum spesifik | Ditambahkan kajian penilaian jenis kulit dan hasil survei | [isi] |
| | Belum ada pembanding aplikasi komersial | Ditambahkan subbab 2.7 dan tabel perbandingan | [isi] |
| | Istilah multimodel dan multimodal tercampur | Istilah diseragamkan, kesimpulan diselaraskan dengan CD-3 | [isi] |
| | Tujuan belum terukur | Tujuan dirumuskan dengan target kuantitatif | [isi] |

---

## CD-2 — Spesifikasi dan Batasan Solusi

### R2-1 · Tabel spesifikasi terukur (A4)
**Lokasi:** 2.2 Spesifikasi Sistem. Sisipkan setelah Tabel 2.2 sebagai tabel baru.

> Agar setiap spesifikasi dapat diuji secara objektif, parameter dan target kuantitatif setiap spesifikasi ditetapkan pada Tabel 2.3. Target yang belum dinyatakan pada dokumen sebelumnya ditetapkan bersama dosen pembimbing.

| Kode | Spesifikasi | Parameter terukur | Target | Metode verifikasi (CD-5) |
|---|---|---|---|---|
| S1 | Input data | Validasi format dan ukuran berkas | JPEG/PNG, ≤ 8 MB; 100% kasus uji benar | Uji *black-box* |
| S2 | Kualitas foto | Penolakan foto gelap, buram, berpantulan, wajah terlalu kecil | 100% kasus uji benar | Uji *black-box* |
| S3 | Akurasi klasifikasi | Akurasi data uji (dengan IK 95%) | ≥ 90% | Evaluasi data uji |
| S4 | Kestabilan model | Simpangan baku akurasi validasi silang 5-*fold* | ≤ 5 poin persentase | Validasi silang |
| S5 | Manfaat multimodel | Uji McNemar *ensemble* vs model tunggal | p < 0,05; jika tidak, dipilih model ringan | Uji statistik |
| S6 | Ketahanan | Penurunan akurasi pada gangguan cahaya, buram, kompresi | ≤ 10 poin persentase | Uji ketahanan |
| S7 | Interpretabilitas | AUC *deletion test* Grad-CAM dibanding urutan acak | Lebih kecil, p < 0,05 | *Deletion test* |
| S8 | Validasi lapangan | Kappa Cohen terhadap uji kertas minyak | ≥ 0,61 | Data uji lokal |
| S9 | Waktu respons | Rata-rata unggah hingga hasil tampil (4G) | ≤ 5 s | Pengukuran aplikasi |
| S10 | *Usability* | Skor SUS | > 70 | Kuesioner SUS |
| S11 | Keamanan data | Skenario uji keamanan dan privasi | 100% berhasil | Uji keamanan |
| S12 | Kompatibilitas | Fungsi utama pada Android 10 ke atas | 2 perangkat, 100% fungsi | Uji perangkat |

**Alasan:** tanpa target angka, CD-5 tidak dapat menyatakan spesifikasi terpenuhi atau tidak. Target S4, S6, S7, S8, dan S9 adalah usulan tim yang perlu disepakati pembimbing.

### R2-2 · Tabel spesifikasi teknis (B2, B8)
**Lokasi:** 2.3 Spesifikasi Teknis, Tabel 2.3. Ganti isi kolom Target.

| Nama Spesifikasi | Target |
|---|---|
| Bahasa pemrograman | *Python* 3.11 (model dan *backend*) dan *Dart* (aplikasi, *framework Flutter*) |
| IDE | *Jupyter Notebook*, *Google Colaboratory*, *Visual Studio Code*, dan *Android Studio* |
| *Library* utama | *TensorFlow/Keras*, *OpenCV*, *scikit-learn*, *FastAPI* (*backend*); *camera*, *image_picker*, *http*, *provider*, *flutter_secure_storage* (aplikasi) |
| Prosesor | *Multi-core processor* (Intel Core i5 / AMD Ryzen 5 atau setara) |
| Memori | Minimal 8 GB RAM pada stasiun kerja pengembangan |
| Penyimpanan dan perangkat uji | SSD minimal 250 GB; perangkat Android 10 (API 29) atau lebih baru, arsitektur arm64, RAM minimal 4 GB |

**Alasan:** Flutter adalah *framework*, bahasanya Dart. Retrofit adalah pustaka HTTP untuk Android *native* sehingga tidak dipakai di Flutter. Firebase tidak digunakan pada implementasi; jika ingin dipertahankan, tuliskan sebagai "opsional untuk pengembangan lanjutan".

### R2-3 · Nama karakteristik ISO/IEC 25010:2023 (B4)
**Lokasi:** bagian 1, paragraf kedua (hal. 4).
**Teks semula:** "…karakteristik kualitas perangkat lunak, seperti functional suitability, reliability, usability, efficiency, maintainability, dan security [2]."

> …karakteristik kualitas produk perangkat lunak, antara lain *functional suitability*, *performance efficiency*, *compatibility*, *interaction capability*, *reliability*, *security*, *maintainability*, *flexibility*, dan *safety* [2].

**Alasan:** edisi 2023 mengganti beberapa nama karakteristik (misalnya *usability* menjadi *interaction capability*) dan menambahkan *safety*. **Verifikasi daftar ini ke dokumen standarnya.** Jika tim sebenarnya mengacu edisi 2011, ganti referensi [2] menjadi ISO/IEC 25010:2011 dan pertahankan nama lama.

### R2-4 · Spesifikasi yang tidak sesuai desain (A1, B5)
**Lokasi:** Tabel 2.2 Spesifikasi Sistem dan Fungsional (hal. 8).

**Baris *Preprocessing*, ganti deskripsi:**
> Melakukan koreksi orientasi foto (EXIF), deteksi wajah, *crop* persegi di sekitar wajah, normalisasi dimensi citra (*resizing*) ke 224 × 224 piksel, normalisasi nilai piksel di dalam model, pemeriksaan kualitas foto, augmentasi data latih, serta penanganan ketidakseimbangan kelas dengan *oversampling* [7], [9].

**Baris "Ekstraksi & Seleksi Fitur", ganti nama menjadi "Ekstraksi dan Penggabungan Fitur":**
> Mengekstraksi karakteristik visual spasial citra wajah secara otomatis melalui lapisan konvolusi ResNet50V2 dan EfficientNetB0, meringkasnya dengan *global average pooling*, lalu menggabungkan kedua vektor fitur (*feature concatenation*). Pemilihan fitur yang relevan terjadi secara implisit melalui bobot lapisan *dense*, sedangkan *dropout* dan regularisasi L2 menekan risiko *overfitting* [7], [9].

**Tabel 3.1, baris "Validasi & Preprocessing":**
- Deskripsi pengujian:
  > Mengeksekusi koreksi orientasi, deteksi wajah, *crop*, normalisasi dimensi, dan pemeriksaan kualitas foto (kecerahan, pantulan, ketajaman, ukuran wajah).
- Standar keberhasilan:
  > Citra persegi 384 × 384 piksel dan masukan model 224 × 224 piksel dihasilkan tanpa galat, sedangkan foto yang tidak layak ditolak dengan pesan perbaikan.

**Alasan:** "standardisasi kontras", "seleksi fitur", dan "pembersihan piksel rusak" tidak ada pada desain maupun implementasi, sehingga tidak dapat diverifikasi di CD-5.

### R2-5 · Aspek etika dan keamanan data (D4, D5)
**Lokasi:** 2.4 Spesifikasi Nonteknis, butir a (hal. 10). Ganti seluruh butir.

> a. Aspek Etika dan Keamanan Data: Pengembangan sistem ini mengedepankan perlindungan privasi digital pengguna. Foto wajah termasuk data pribadi yang bersifat spesifik (biometrik) menurut UU PDP [4], sehingga pemrosesannya memerlukan penilaian risiko pelindungan data. Pengelolaan data dirancang mengacu pada UU PDP dan kontrol keamanan informasi yang relevan dari ISO/IEC 27001 [1]. Kontrol tersebut meliputi persetujuan eksplisit sebelum pemrosesan, komunikasi terenkripsi melalui *Hypertext Transfer Protocol Secure* (HTTPS), dan pemrosesan foto di memori tanpa penyimpanan permanen. Profil dan riwayat disimpan terenkripsi di perangkat tanpa foto. Sistem juga memberikan kontrol kepada pengguna untuk menghapus data, mewajibkan persetujuan orang tua atau wali bagi pengguna di bawah 18 tahun, dan membatasi akses API dengan kunci akses. Hasil penilaian risiko dan mitigasinya dipaparkan pada CD-4.

**Alasan:** ISO/IEC 27001 adalah standar sistem manajemen keamanan informasi organisasi, sehingga aplikasi tidak dapat "memenuhi" standar itu sendiri. Lebih tepat menyatakan mengacu pada kontrol-kontrolnya.

### R2-6 · Batasan kondisi pengambilan citra (A2)
**Lokasi:** Tabel 2.1 Batasan Sistem, baris "Batasan Kondisi Pengambilan Citra". Ganti deskripsi.

> Sistem tidak mengontrol faktor eksternal di lingkungan pengguna secara otomatis, seperti tingkat pencahayaan (*lux*), resolusi sensor kamera, dan sudut kemiringan wajah. Sebagai gantinya, sistem memandu pengguna melalui protokol pengambilan foto (wajah dibersihkan, cahaya alami merata, tanpa *flash*) dan menolak foto yang terlalu gelap, terlalu terang, buram, mengandung pantulan berlebih, atau memuat wajah yang terlalu kecil [11], [12], [13].

**Alasan:** batasan tetap berlaku, tetapi sistem kini punya mekanisme untuk mengurangi dampaknya. Ini menjawab pertanyaan "bagaimana jika fotonya buruk?".

### Usulan baris *Timeline Revisi Dokumen* CD-2

| Versi, Tanggal | Revisi | Perbaikan yang dilakukan | Halaman revisi |
|---|---|---|---|
| 2, [isi tanggal] | Spesifikasi belum terukur | Ditambahkan tabel spesifikasi terukur dengan target dan metode verifikasi | [isi] |
| | Spesifikasi teknis tidak sesuai implementasi | Bahasa, pustaka, dan perangkat uji diperbarui | [isi] |
| | Proses praproses dan seleksi fitur tidak sesuai desain | Deskripsi praproses dan penggabungan fitur diperbaiki | [isi] |
| | Aspek keamanan data | Ditambahkan status data biometrik dan penilaian risiko; rujukan ISO/IEC 27001 diperjelas | [isi] |

---

## CD-3 — Desain Rancangan Solusi

### R3-1 · Matriks keputusan (A5)
**Lokasi:** 2.2 Mekanisme Pemilihan Solusi, Tabel 2.1 dan paragraf sesudahnya.

**Perubahan tabel:** rating "Kesesuaian Regulasi" Solusi 1 diubah dari 3 menjadi 2, karena solusi terpilih juga memproses usia dan jenis kelamin.

| Kriteria | Bobot | Solusi 1 | Nilai | Solusi 2 | Nilai | Solusi 3 | Nilai |
|---|---|---|---|---|---|---|---|
| Akurasi & Stabilitas | 30% | 3 | 0,90 | 3 | 0,90 | 2 | 0,60 |
| Interpretabilitas (XAI) | 25% | 3 | 0,75 | 2 | 0,50 | 2 | 0,50 |
| Kesesuaian Regulasi | 15% | **2** | **0,30** | 3 | 0,45 | 2 | 0,30 |
| Efisiensi Komputasi | 15% | 2 | 0,30 | 1 | 0,15 | 2 | 0,30 |
| Kemudahan Pengembangan | 15% | 2 | 0,30 | 1 | 0,15 | 2 | 0,30 |
| **Total** | 100% | | **2,55** | | **2,15** | | **2,00** |

Peringkat tidak berubah, sehingga Solusi 1 tetap terpilih.

**Paragraf tambahan setelah tabel:**

> Rating pada kriteria akurasi dan stabilitas merupakan estimasi berdasarkan hasil penelitian terdahulu [6], [10], bukan hasil eksperimen pada *dataset* penelitian ini. Rating tersebut diverifikasi pada CD-5 melalui uji ablasi, yaitu perbandingan model gabungan dengan model satu *backbone* (ResNet50V2 saja dan EfficientNetB0 saja) menggunakan uji statistik McNemar. Apabila model gabungan tidak lebih baik secara signifikan, model yang lebih ringan akan dipilih sesuai bobot kriteria efisiensi komputasi. Rating kesesuaian regulasi Solusi 1 bernilai 2 karena selain citra wajah, sistem juga memproses usia dan jenis kelamin; data ini hanya digunakan untuk personalisasi rekomendasi, bukan sebagai masukan model.

**Alasan:** rating akurasi > 90% sebelum eksperimen mudah dipertanyakan, dan Solusi 3 dinilai lebih rendah karena metadata padahal Solusi 1 juga memakai metadata. Koreksi ini membuat matriks konsisten tanpa mengubah keputusan.

### R3-2 · Persamaan EfficientNet (B3)
**Lokasi:** 3.7.2, setelah Persamaan (3.2)–(3.4) (hal. 20).
**Teks semula:** "Dengan batasan : α . β . γ2 ≈ dan α ≥ 1, β ≥ 1, γ ≥ 1"

> Dengan batasan α · β² · γ² ≈ 2, dengan α ≥ 1, β ≥ 1, dan γ ≥ 1. Batasan ini membuat setiap kenaikan koefisien φ sebesar satu kira-kira menggandakan kebutuhan komputasi (FLOPS) jaringan.

(Tulis ulang dengan *equation editor* Word: α·β²·γ² ≈ 2.)

### R3-3 · Varian model (B6)
**Lokasi:** 3.7, tambahkan di akhir paragraf pembuka (hal. 17).

> Varian yang digunakan adalah ResNet50V2, yaitu ResNet 50 lapis dengan *pre-activation* yang tetap menerapkan blok residual pada Persamaan (3.1), dan EfficientNetB0. Keduanya memakai bobot awal ImageNet dengan resolusi masukan 224 × 224 piksel.

**Gambar 3.2:**
- **Pilihan 1:** tambahkan keterangan "Gambar 3.2 Ilustrasi blok residual pada ResNet-34; implementasi menggunakan ResNet50V2".
- **Pilihan 2:** ganti dengan diagram arsitektur model gabungan dari CD-4.

### R3-4 · Makna *ensemble* (B1)
**Lokasi:** 1.1.1 Deskripsi Alternatif Solusi 1, tambahkan di akhir paragraf kedua (hal. 4–5).

> Istilah *ensemble* pada rancangan ini merujuk pada fusi tingkat fitur (*feature-level fusion*). Kedua *backbone* berada dalam satu model, vektor fiturnya digabungkan, dan keduanya dilatih bersama; pendekatan ini berbeda dari *ensemble* yang merata-ratakan prediksi beberapa model yang dilatih terpisah. Rancangan ini tetap menggunakan satu modalitas data, yaitu citra, sehingga berbeda dari pendekatan multimodal pada Solusi 3.

### R3-5 · Metrik untuk tiga kelas (B7)
**Lokasi:** 3.7, setelah Persamaan (3.8) (hal. 21).

> Karena klasifikasi terdiri atas tiga kelas, Persamaan (3.5)–(3.8) dihitung untuk setiap kelas dengan pendekatan *one-vs-rest*, yaitu kelas yang dievaluasi dianggap positif dan dua kelas lainnya negatif. Nilai presisi, *recall*, dan F1-*score* kemudian dirata-ratakan secara makro sehingga setiap kelas berbobot sama, misalnya F1 makro = (1/K) Σ F1_c dengan K = 3. Akurasi keseluruhan dihitung sebagai jumlah prediksi benar dibagi jumlah seluruh data uji, dan dilengkapi interval kepercayaan 95%.

### R3-6 · Istilah diagnostik dan klaim berlebihan (C1–C4)
**Lokasi:** 3.9 Desain Antarmuka Aplikasi dan *mock-up* (hal. 22–25).

| Teks semula | Teks pengganti |
|---|---|
| *Diagnostic Scan Interface* / Halaman Pemindaian Kamera | Halaman Pemindaian Kulit (*Skin Scan*) |
| *Diagnostic Scan Results* / Halaman Hasil Diagnostik | Halaman Hasil Analisis Kulit (*Scan Results*) |
| "*calibrate your clinical skin analysis*" | "*adjust which ingredients are prioritised*" |
| "AI DIAGNOSTIC ACTIVE" | "*AI analysis active*" |
| "hasil klasifikasi medis komputasional" | "hasil klasifikasi jenis kulit" |
| "rekomendasi bahan aktif tingkat klinis (*clinical-grade ingredients*)" | "rekomendasi kandungan bahan aktif" |
| "hasil analisis topologi resolusi tinggi" | "hasil analisis" |
| "*Oily Type IV*" | "*Oily* (Berminyak)" |
| "label keamanan lingkungan/kulit (misal: *EWG Green*)" | "status regulasi BPOM (diizinkan atau dibatasi)" |
| "pengalih lampu kilat (*flash*)" | dihapus |
| "DermaCare" | "Glowrithm" |

**3.9.3, ganti paragraf penjelasan:**

> Setelah komputasi selesai, halaman ini menyajikan hasil analisis kulit pengguna. Bagian teratas menampilkan peta Grad-CAM, yaitu visualisasi *Explainable AI* (XAI) yang menumpangkan *heatmap* berwarna pada citra wajah pengguna [4]. Warna hangat (merah/kuning) menunjukkan area yang paling memengaruhi keputusan model, sedangkan warna biru menunjukkan pengaruh yang rendah. Peta ini menjelaskan bagian citra yang diperhatikan model dan bukan pengukuran kadar minyak atau kelembapan kulit. Di bawahnya ditampilkan jenis kulit (misalnya "*Oily*/Berminyak") beserta skor keyakinan (*confidence score*), probabilitas ketiga kelas, serta tombol menuju rekomendasi bahan aktif.

**Alasan:** CD-2 menegaskan sistem adalah alat bantu keputusan, bukan diagnosis. Istilah "*diagnostic*" dan "*clinical*" bertentangan dengan batasan itu. Label "*Type IV*" berasal dari skala Fitzpatrick untuk warna kulit, yang tidak diklasifikasikan oleh model.

### R3-7 · Peran usia dan jenis kelamin (C5)
**Lokasi 1:** 3.9.1 Halaman Personalisasi Profil, ganti paragraf penjelasan (hal. 22–23).

> Halaman ini menjadi gerbang awal sebelum analisis. Pengguna memasukkan usia dan jenis kelamin biologis. Data ini tidak digunakan sebagai masukan model klasifikasi, melainkan oleh modul rekomendasi untuk menyesuaikan prioritas bahan aktif melalui aturan personalisasi yang transparan, misalnya kehati-hatian penggunaan *salicylic acid* bagi pengguna di bawah 18 tahun. Pengguna di bawah 18 tahun wajib mendapatkan persetujuan orang tua atau wali. Data profil disimpan terenkripsi di perangkat, dan halaman ini menampilkan pemberitahuan keamanan data sesuai regulasi pelindungan data pribadi [9].

**Lokasi 2:** 3.10.2 Diagram Alir Sistem (hal. 26).
**Teks semula:** "Berdasarkan jenis kulit yang terdeteksi serta data pengguna berupa usia dan jenis kelamin, sistem melakukan seleksi bahan aktif yang sesuai."

> Berdasarkan probabilitas setiap jenis kulit, sistem menghitung skor kecocokan setiap bahan aktif. Usia dan jenis kelamin hanya menggeser skor tersebut dalam rentang kecil melalui aturan personalisasi, dan bahan yang dilarang BPOM tidak pernah direkomendasikan.

**Alasan:** "kalibrasi *baseline* hormonal pada algoritma" tidak diimplementasikan dan bertentangan dengan batasan CD-2 yang tidak memproses faktor internal seperti hormon.

### R3-8 · Referensi bahan aktif (D3)
**Lokasi:** 3.3 Rekomendasi Bahan Aktif dan Daftar Pustaka (hal. 15 dan 32).

| Referensi | Masalah | Tindakan |
|---|---|---|
| [14] J. Smith *et al.*, gel *salicylic acid* | Nama penulis generik, tanpa DOI, sulit dilacak | Cari judulnya di Google Scholar atau situs jurnal. Jika tidak ditemukan, ganti dengan sumber yang dapat diverifikasi, misalnya ulasan tentang *salicylic acid* di jurnal dermatologi [verifikasi sebelum dipakai] |
| [5] Grad-CAM untuk pemrosesan teks medis | Kurang relevan untuk klasifikasi citra | Rujuk Selvaraju dkk. [4] saja, atau ganti dengan penerapan Grad-CAM pada citra medis/kulit |
| [13] serum niacinamide | Dipakai juga untuk vitamin C dan *sunscreen* | Gunakan [13] hanya untuk niacinamide; tambahkan referensi terpisah untuk vitamin C dan untuk fotoproteksi [isi] |

**3.3.2, ganti kalimat terakhir:**

> Bahan aktif yang direkomendasikan meliputi niacinamide [13], vitamin C [isi referensi], dan *sunscreen* [isi referensi] karena berperan menjaga fungsi pelindung kulit serta membantu melindungi kulit dari radikal bebas dan sinar ultraviolet.

### R3-9 · Protokol pengambilan citra dan pemeriksaan kualitas (A2)
**Lokasi:** tambahkan subbab baru setelah 3.6 Metodologi Permodelan.

> **3.x Protokol Pengambilan Citra dan Pemeriksaan Kualitas Foto**
>
> Kilap kulit merupakan ciri utama kulit berminyak, sementara pantulan *flash* atau lampu menghasilkan kilap serupa. Karena itu, kualitas pengambilan citra sangat menentukan ketepatan klasifikasi. Aplikasi memandu pengguna melalui protokol: wajah dicuci dengan pembersih lembut, ditunggu sekitar satu jam tanpa produk, foto diambil menghadap cahaya alami yang merata tanpa *flash*, serta tanpa riasan, kacamata, dan filter.
>
> Sebelum model dijalankan, sistem memeriksa kualitas citra wajah hasil *crop*:
> - kecerahan rata-rata;
> - proporsi piksel jenuh sebagai indikator pantulan;
> - ketajaman berdasarkan variansi operator Laplacian;
> - ukuran wajah relatif terhadap lebar foto.
>
> Foto yang tidak memenuhi ambang ditolak beserta saran perbaikan, sehingga model hanya menganalisis foto yang layak. Ambang awal dikalibrasi terhadap distribusi *dataset* latih, dan nilainya dipaparkan pada CD-4.

### R3-10 · Batas resolusi dan Gambar 3.1 (A1)
**Lokasi:** 3.2 Definisi dan Klasifikasi Jenis Kulit (hal. 13).

**Gambar 3.1:** ganti dengan contoh foto wajah dari *dataset* yang digunakan, sesuai lisensi *dataset* dan dengan mata disamarkan. Jika gambar lama dipertahankan, ubah keterangannya menjadi "Ilustrasi tekstur permukaan kulit pada pengamatan jarak dekat [10]".

**Paragraf tambahan setelah penjelasan Gambar 3.1:**

> Perlu diperhatikan bahwa sistem menganalisis foto seluruh wajah yang diperkecil menjadi 224 × 224 piksel, sehingga satu piksel mewakili sekitar 0,8 mm permukaan wajah. Pada resolusi ini detail mikro seperti pori dan sisik halus tidak sepenuhnya terlihat. Karakteristik yang paling mungkin dimanfaatkan model adalah kilap, kehalusan, dan kerataan warna kulit pada area dahi, hidung, dan pipi. Keterbatasan ini diuji pada CD-5 dan menjadi dasar pengembangan lanjutan berupa analisis per area wajah pada resolusi lebih tinggi.

### R3-11 · Uraian *dataset* (A3)
**Lokasi:** 3.11.3 *Dataset* dan Bahan Penelitian (hal. 29). Ganti kalimat "*Dataset* diperoleh dari repositori publik seperti Kaggle…".

> *Dataset* yang digunakan adalah [isi nama *dataset*, penyusun, tautan, dan lisensi] yang berisi [isi jumlah] citra wajah berlabel kering, normal, dan berminyak. Sebelum digunakan, *dataset* diaudit dalam empat langkah:
> 1. menghitung jumlah citra per kelas;
> 2. menghapus citra identik (*hash* MD5) dan mengelompokkan citra hampir identik (*difference hash*) agar tidak terpisah ke data latih dan data uji;
> 3. menghapus citra yang labelnya saling bertentangan;
> 4. membagi data secara terstratifikasi 70/15/15 berbasis grup.
>
> Selain *dataset* publik, disiapkan data uji lokal dari [isi jumlah] relawan di Indonesia yang difoto pada tiga kondisi cahaya dengan label acuan dari uji kertas minyak. Data ini digunakan untuk menilai kinerja model pada pengguna sasaran.

### R3-12 · Pustaka sistem (B2)
**Lokasi:** 3.11.2, butir *Backend* dan *Database* (hal. 28).

> - ***FastAPI* dan *Uvicorn*:** layanan REST API untuk menerima foto, menjalankan inferensi dan Grad-CAM, serta mengirimkan rekomendasi.
> - ***flutter_secure_storage*:** penyimpanan lokal terenkripsi untuk persetujuan, profil, dan riwayat tanpa foto.
> - ***Docker* dan *Caddy*:** pengemasan layanan dan HTTPS otomatis pada *server*.
> - ***Firebase*** (opsional): disiapkan sebagai pengembangan lanjutan bila diperlukan sinkronisasi riwayat antarperangkat.

### R3-13 · Catatan RAB
**Lokasi:** 4.2 Rencana Anggaran Biaya, keterangan baris 2.a (hal. 31). Tambahkan:

> Paket VPS dipilih dengan RAM minimal 2 GB (disarankan 4 GB) karena model berukuran sekitar 110 MB dan dijalankan bersama TensorFlow.

### Usulan baris *Timeline Revisi Dokumen* CD-3

| Versi, Tanggal | Revisi | Perbaikan yang dilakukan | Halaman revisi |
|---|---|---|---|
| 4, [isi tanggal] | Rating matriks keputusan belum berbasis bukti | Rating regulasi Solusi 1 dikoreksi; ditambahkan rencana verifikasi ablasi dan uji McNemar | [isi] |
| | Kesalahan persamaan dan varian model | Batasan *compound scaling* diperbaiki; varian ResNet50V2 dan EfficientNetB0 ditegaskan | [isi] |
| | Istilah diagnostik dan klaim berlebihan | Istilah antarmuka dan makna *heatmap* diperbaiki | [isi] |
| | Kondisi pengambilan citra belum dipandu | Ditambahkan protokol pengambilan citra dan *quality gate* | [isi] |
| | Uraian *dataset* dan referensi | *Dataset* diaudit; referensi bahan aktif diverifikasi | [isi] |

---

## Pemeriksaan akhir sebelum dikumpulkan

- [ ] Semua istilah asing dicetak miring dan konsisten (*ensemble*, *heatmap*, *confidence score*, *dataset*).
- [ ] Tidak ada lagi kata "diagnostik", "klinis", atau "*clinical-grade*" yang mengacu pada sistem.
- [ ] Nomor tabel, gambar, persamaan, dan referensi telah disesuaikan.
- [ ] Semua tanda [isi …] dan [verifikasi] telah dilengkapi.
- [ ] Revisi CD-1–CD-3 konsisten dengan draf CD-4 dan CD-5.
