# Panduan Pengujian Web App Glowrithm

*Web app* ini adalah versi *browser* dari alur aplikasi Android, khusus untuk pengujian: model, *backend*, dan alur pengguna dapat diuji tanpa membangun APK. *Web app* memanggil REST API yang sama dengan aplikasi Android dan disajikan langsung oleh *backend* di alamat `/app/`.

> *Web app* ini hanya untuk pengujian internal. Dokumen CD tidak berubah: implementasi yang dilaporkan tetap aplikasi Android.

## 1. Menjalankan

Siapkan lingkungan Python seperti pada `docs/IMPLEMENTATION_GUIDE.md` (bagian *Setup*), lalu pilih salah satu cara berikut.

| Cara | Perintah / langkah | Kamera langsung | Cocok untuk |
|---|---|---|---|
| Laptop | `cd backend && PYTHONPATH=../ml uvicorn app.main:app --host 0.0.0.0 --port 8000`, lalu buka `http://localhost:8000/app/` | Ya (webcam) | Uji cepat alur dan model |
| HP di Wi-Fi yang sama | Jalankan seperti di atas, lalu buka `http://<IP laptop>:8000/app/` di HP | Tidak (HTTP); tombol *Take or choose a photo* membuka aplikasi kamera HP | Uji foto dari kamera HP |
| Colab (HTTPS) | Jalankan notebook `ml/notebooks/glowrithm_colab.ipynb` sampai bagian 5 | Ya | Uji dengan model hasil pelatihan GPU |
| VPS dengan Caddy (HTTPS) | `docker compose -f deploy/docker-compose.yml up -d --build`, lalu buka `https://<domain>/app/` | Ya | Uji lapangan dan uji SUS |

- **Tanpa model terlatih:** tambahkan `GLOWRITHM_DEMO_MODE=1`. Hasilnya acak, jadi hanya berguna untuk menguji alur.
- **Dengan model terlatih:** salin `model.keras` dan `model_meta.json` dari `ml/artifacts/ensemble/` ke `backend/models/`.
- **Mencari IP laptop:** Windows `ipconfig`, macOS/Linux `ip addr` atau `ifconfig`. *Firewall* laptop harus mengizinkan port 8000.

## 2. Skenario uji

Jalankan semua skenario pada minimal satu laptop dan dua HP (satu Android, satu iPhone bila ada). Catat *browser* dan versinya.

| ID | Skenario | Langkah | Hasil yang diharapkan |
|---|---|---|---|
| W-01 | Gerbang persetujuan | Buka `/app/` pertama kali | Halaman persetujuan tampil; tombol *Agree and continue* aktif hanya setelah kotak dicentang |
| W-02 | Validasi profil | Kosongkan usia, isi 12, isi 16 tanpa centang wali | Pesan kesalahan sesuai; usia 16 wajib persetujuan wali |
| W-03 | Kamera langsung | Buka *Scan* lewat HTTPS atau `localhost` | Pratinjau kamera depan, panduan oval, tombol rana aktif, tanpa *flash* |
| W-04 | Foto dari galeri | Pilih foto JPEG atau PNG | Halaman *Check your photo* menampilkan foto |
| W-05 | Analisis berhasil | *Analyze photo* dengan foto wajah yang baik | Jenis kulit, *confidence*, tiga probabilitas, *heat map* Grad-CAM dengan penggeser *opacity* |
| W-06 | *Quality gate*: gelap | Foto di ruangan gelap | Halaman *Retake your photo* dengan saran "too dark" |
| W-07 | *Quality gate*: buram dan pantulan | Foto bergerak; foto dengan lampu mengarah ke wajah | Ditolak atau diberi peringatan *blurry* / *reflections* |
| W-08 | *Confidence* rendah | Foto miring atau sebagian wajah | Catatan *Low confidence* tampil |
| W-09 | Rekomendasi | *See recommended ingredients* | Tiga langkah rutinitas, label BPOM, detail bahan saat diketuk |
| W-10 | Simpan dan riwayat | *Save to history*, buka *History* | Hasil tersimpan tanpa foto; detail menampilkan "Images are not stored" |
| W-11 | Hapus data | *Profile* > *Withdraw consent and erase data* | Kembali ke halaman persetujuan; tidak ada data tersisa |
| W-12 | Server tidak terjangkau | Matikan *backend*, lalu analisis | Pesan "Cannot reach the server …" dan tombol *Try again* |
| W-13 | Waktu respons | Ulangi analisis 10 kali | Catat *Round trip in the browser* dari *Test details*; rata-rata ≤ 5 s (CD-2 S9) |

## 3. Mencatat hasil

Setiap hasil analisis memiliki panel **Test details** (versi model, waktu proses, nilai *quality gate*). Tombol **Copy test record** menyalin satu catatan JSON tanpa foto, usia, atau jenis kelamin. Tempelkan ke lembar uji bersama dengan kolom: tanggal, penguji, perangkat, *browser*, kondisi cahaya, ID skenario, hasil (lulus/gagal), catatan, dan *test record*.

## 4. Privasi selama pengujian

- Gunakan foto anggota tim atau relawan yang sudah menandatangani persetujuan (lihat `docs/PROTOKOL_DATA_UJI_LOKAL.md`).
- Tautan *tunnel* Colab bersifat publik selama berjalan: jangan bagikan dan matikan setelah selesai.
- Data uji di *browser* dihapus melalui *Withdraw consent and erase data*.

## 5. Perbedaan dengan aplikasi Android

- **Penyimpanan:** data disimpan di `localStorage` *browser*, yang tidak terenkripsi seperti Android Keystore.
- **Kamera langsung:** hanya berjalan di halaman HTTPS atau `localhost`. Foto kamera langsung dipotong sesuai area yang terlihat di pratinjau.
- **Fitur khusus pengujian:** panel *Test details* dan tombol *Copy test record* tidak ada di aplikasi Android.
