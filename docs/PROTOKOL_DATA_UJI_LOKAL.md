# Protokol Pengumpulan Data Uji Lokal (Validasi Lapangan)

Protokol ini dipakai untuk menguji apakah model bekerja pada pengguna sasaran di Indonesia, bukan hanya pada *dataset* publik. Hasilnya diolah dengan `ml/scripts/evaluate_local.py` dan dilaporkan di CD-5 bagian validasi lapangan.

> Rubrik label di bawah adalah heuristik tim. Konfirmasikan rubrik ini kepada dosen pembimbing (dan bila memungkinkan apoteker atau dokter spesialis kulit) **sebelum** pengumpulan data dimulai.

## 1. Ringkasan desain

| Aspek | Ketentuan |
|---|---|
| Peserta | 30–50 relawan berusia 18 tahun ke atas |
| Foto per peserta | 3 foto wajah: cahaya alami, lampu ruangan, cahaya redup |
| Label acuan | Uji kertas minyak (*blotting paper*) di dahi, hidung, pipi kiri, pipi kanan |
| Keluaran | Akurasi (IK 95%), F1 makro, kappa Cohen, akurasi per kondisi cahaya, dampak *quality gate* |

Dengan 50 foto pada kondisi cahaya alami dan akurasi sekitar 85%, interval kepercayaan 95% berada pada kisaran ±10 poin persentase. Semakin banyak peserta, semakin sempit intervalnya.

## 2. Kriteria peserta

- **Inklusi:** berusia 18 tahun ke atas dan bersedia mengikuti seluruh prosedur. Batas usia dipakai agar tidak memproses data pribadi anak.
- **Eksklusi:** sedang mengalami iritasi, luka, atau peradangan kulit wajah yang berat.
- **Eksklusi:** menggunakan obat kulit resep pada wajah dalam 2 minggu terakhir.

## 3. Etika dan pelindungan data

- **Persetujuan tertulis.** Setiap peserta menandatangani formulir persetujuan (bagian 8) sebelum difoto.
- **ID pseudonim.** Gunakan ID seperti `P001` dan jangan menulis nama di berkas foto atau CSV.
- **Penyimpanan foto.** Foto hanya disimpan di laptop tim dalam folder terenkripsi, tidak diunggah ke layanan lain, dan dihapus setelah evaluasi selesai atau paling lambat [isi tanggal].
- **Pemuatan di laporan.** Jangan memuat foto peserta di CD-5 kecuali ada izin tertulis terpisah; jika dimuat, samarkan bagian mata.
- **Hak mundur.** Peserta boleh mengundurkan diri kapan saja, dan datanya dihapus.

## 4. Persiapan peserta

1. Peserta mencuci muka dengan pembersih wajah yang lembut, lalu mengeringkan wajah dengan handuk bersih.
2. Peserta tidak memakai produk apa pun (pelembap, *sunscreen*, riasan) setelah mencuci muka.
3. Peserta menunggu sekitar 60 menit di ruangan bersuhu normal, tanpa berolahraga dan tanpa menyentuh wajah.

## 5. Pengambilan foto

Ambil **semua foto sebelum uji kertas minyak**, karena kertas minyak mengangkat minyak dari kulit.

1. Gunakan ponsel yang sama untuk semua peserta, kamera depan, tanpa *flash*, dengan mode kecantikan dan filter dimatikan.
2. Jarak wajah ke kamera sekitar 30–40 cm. Wajah menghadap lurus, rambut tidak menutupi dahi, kacamata dilepas.
3. Ambil satu foto pada setiap kondisi cahaya:
   - **alami:** dekat jendela dengan cahaya siang tidak langsung (acuan);
   - **lampu:** lampu ruangan biasa;
   - **redup:** ruangan dengan cahaya minim.
4. Ukur intensitas cahaya di posisi wajah menggunakan *lux meter* atau aplikasi pengukur lux, lalu catat nilainya dalam lux.
5. Beri nama berkas dengan pola `P001_alami.jpg`, `P001_lampu.jpg`, `P001_redup.jpg`.

## 6. Uji kertas minyak dan penilaian

1. Tempelkan satu potong kertas minyak baru pada setiap area (dahi, hidung, pipi kiri, pipi kanan) selama sekitar 10 detik dengan tekanan ringan.
2. Angkat kertas dan amati di depan cahaya. Beri skor setiap area:
   - **0:** tidak tampak minyak;
   - **1:** bercak minyak tipis atau sedikit;
   - **2:** bercak minyak jelas atau luas.
3. Tanyakan apakah kulit terasa kencang (`tight` = 1/0) dan amati apakah tampak sisik halus (`flaky` = 1/0).
4. Agar penilaian konsisten, skor sebaiknya diberikan oleh dua anggota tim secara independen. Jika berbeda, diskusikan hingga sepakat dan catat di kolom `notes`.

**Rubrik label acuan** (sama dengan fungsi `derive_label` di `evaluate_local.py`):

| Kondisi skor | Label acuan |
|---|---|
| Zona T (dahi/hidung) ≥ 1 **dan** pipi ≥ 1 | `oily` (berminyak) |
| Zona T = 2 **dan** pipi = 0 | `combination` (dikecualikan dari akurasi tiga kelas, dilaporkan terpisah) |
| Semua area 0 **dan** (kencang **atau** bersisik) | `dry` (kering) |
| Selain kondisi di atas | `normal` |

Jika pembimbing atau pakar menetapkan label secara langsung, isi kolom `reference_label`. Isi kolom tersebut akan dipakai menggantikan rubrik.

## 7. Pencatatan dan analisis

1. Salin `ml/templates/local_test_labels.csv` ke `ml/data/local_test/labels.csv` dan hapus baris contoh.
2. Isi satu baris per foto. Skor kertas minyak sama untuk ketiga foto peserta yang sama.
3. Letakkan foto di `ml/data/local_test/photos/`, lalu jalankan:

```bash
cd ml
python scripts/evaluate_local.py --model artifacts/ensemble/model.keras \
    --csv data/local_test/labels.csv --images data/local_test/photos
```

4. Hasilnya ada di `artifacts/ensemble/reports/local/`, yaitu `local_metrics.json`, `local_predictions.csv`, dan `confusion_matrix_local.png`. Pindahkan angkanya ke tabel validasi lapangan di CD-5.

Interpretasi kappa Cohen (Landis & Koch, 1977): 0,41–0,60 *moderate*, 0,61–0,80 *substantial*, di atas 0,80 *almost perfect*.

## 8. Formulir persetujuan (contoh)

> **Persetujuan Keikutsertaan dalam Pengujian Aplikasi Glowrithm**
>
> Saya memahami bahwa pengujian ini bertujuan menilai ketepatan aplikasi Glowrithm dalam mengenali jenis kulit wajah. Saya bersedia (1) mencuci muka dan menunggu sekitar satu jam tanpa memakai produk, (2) difoto pada tiga kondisi cahaya, dan (3) menjalani uji kertas minyak pada wajah.
>
> Foto saya hanya digunakan untuk pengujian ini, disimpan dengan kode tanpa nama, tidak dibagikan kepada pihak lain, dan dihapus paling lambat [tanggal]. Foto saya tidak akan dimuat dalam laporan tanpa izin tertulis terpisah. Saya dapat mengundurkan diri kapan saja tanpa konsekuensi, dan data saya akan dihapus.
>
> Kode peserta: ________  Tanda tangan: ________  Tanggal: ________
