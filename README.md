# POS AHASS Performance Dashboard — Repository Lengkap

Repository ini merupakan satu paket website statis GitHub Pages untuk POS AHASS Sumatera Selatan, terdiri dari dashboard laporan operasional lama dan dashboard UE bulanan berdasarkan kelas HIGH, MIDDLE, dan LOW.

## Isi repository

- `index.html` — tampilan dashboard lengkap: filter POS/periode, kartu KPI, grafik UE dan revenue, komposisi KPI, catatan performa, tabel laporan, filter kelas UE bulanan, ringkasan kelas HIGH/MIDDLE/LOW, tabel detail UE, dan ekspor CSV.
- `data.js` — snapshot data dari sheet `Form Responses 1` di workbook laporan POS yang diberikan pada percakapan ini (143 laporan, 15 POS). Workbook mentah tidak disertakan.
- `ue_class_data.js` — snapshot 5 bulan UE bulanan pada workbook yang diberikan (Juni–Oktober 2026; 58 POS, 290 baris POS-bulan).
- `generate_data.py` — membangun ulang `data.js` dari workbook laporan utama; hanya membaca sheet `Form Responses 1` dan field ringkasan operasional yang diperlukan.
- `generate_ue_class_data.py` — membangun ulang `ue_class_data.js` dari workbook UE bulanan.
- `.github/workflows/pages.yml` — secara otomatis menerbitkan website ketika file dashboard/data berubah. Jika workbook bernama `source-data/UE POS AHASS.xlsx` diunggah, workflow juga membuat ulang dataset kelas.
- `source-data/README.md` — petunjuk pembaruan UE bulanan.
- `.nojekyll` — memastikan GitHub Pages menyajikan file statis tanpa pemrosesan Jekyll.

## Cara memasang seluruh dashboard ke repository yang sudah ada

Paket ZIP ini berisi seluruh file yang diperlukan. Agar repository tidak menumpuk salinan patch/ZIP lama:

1. Unduh ZIP repository lengkap ini dan ekstrak di komputer.
2. Buat backup repository lama terlebih dahulu atau unduh ZIP repository saat ini dari GitHub.
3. Buka repository `nicho1510s/Dashboard-Laporan-Pos-AHASS-SumSel` menggunakan GitHub Desktop dan pastikan branch `main` sudah tersinkron.
4. Salin **seluruh isi folder hasil ekstraksi** ke folder repository lokal. Pilih **Replace/Overwrite** ketika diminta.
5. Jika masih ada file lama bernama `pos-ahass-dashboard.zip` di folder repository, hapus file arsip lama tersebut. File ZIP tidak diperlukan oleh website.
6. Di GitHub Desktop, periksa daftar perubahan: `index.html`, `data.js`, `ue_class_data.js`, script generator, README, dan workflow harus tersedia. Jangan menaruh file ZIP atau workbook laporan utama di root repository.
7. Commit dengan pesan `Replace with complete POS AHASS dashboard repository`, lalu klik **Push origin**.
8. Di GitHub, buka **Settings → Pages → Build and deployment → Source** dan pilih **GitHub Actions**. Simpan jika belum menggunakan pilihan ini.
9. Buka tab **Actions**. Tunggu workflow **Build and publish POS AHASS dashboard** selesai dengan status hijau. Kemudian buka **Settings → Pages → Visit site**.

URL tetap menggunakan repository yang sama. Biasanya formatnya `https://nicho1510s.github.io/Dashboard-Laporan-Pos-AHASS-SumSel/`.

## Pembaruan UE bulanan — cukup upload workbook

Workflow telah disiapkan agar Anda tidak perlu mengedit kode untuk pembaruan biasa.

1. Buka repository GitHub, lalu masuk ke folder `source-data/`.
2. Pilih **Add file → Upload files**.
3. Unggah workbook UE terbaru dengan nama persis `UE POS AHASS.xlsx`. Jika workbook bulan lalu masih ada, gunakan nama/path yang sama untuk menggantinya, bukan membuat file bernama baru setiap bulan.
4. Commit perubahan ke branch `main`.
5. Buka **Actions → Build and publish POS AHASS dashboard** untuk melihat prosesnya. Workflow akan membaca tab bulanan, membuat `ue_class_data.js`, lalu menerbitkan halaman terbaru.
6. Setelah workflow hijau, refresh website dengan `Ctrl + F5`.

Jika mengunggah file XLSX di folder lain atau memakai nama berbeda, workflow tidak akan membaca workbook tersebut. Nama tab harus seperti `UE POS JUN`, `UE POS JUL`, `UE POS AUG`, `UE POS SEP`, `UE POS OKT`, `UE POS NOV`, dan seterusnya. Kolom kelas, nama POS, daily UE, total UE, Target Fix, ACV, dan status SIP harus tetap sesuai struktur workbook sumber.

### Tahun pada workbook

Nama sheet bulanan pada workbook yang diberikan tidak mencantumkan tahun. Secara otomatis workflow menggunakan tahun kalender Jakarta saat dijalankan. Jika memproses workbook yang sheet-nya milik tahun berbeda dari tahun sekarang, jalankan workflow secara manual lewat **Actions → Build and publish POS AHASS dashboard → Run workflow** dan isi input `year` dengan tahun yang benar.

## Pembaruan dashboard laporan utama

`data.js` saat ini merupakan snapshot dari workbook `Laporan Pos Sumatera Selatan (Responses).xlsx` yang diberikan. Untuk memperbaruinya, proses workbook terbaru di komputer Anda dengan:

```bash
python generate_data.py "Laporan Pos Sumatera Selatan (Responses).xlsx"
```

Lalu unggah **file `data.js` hasil generator saja** ke root repository dan commit. Workflow akan menerbitkan dashboard ulang. Jangan mengunggah workbook laporan utama mentah ke repository publik: workbook tersebut besar dan mempunyai sheet transaksi tambahan yang tidak perlu dipublikasikan.

## Definisi KPI

- Total UE laporan utama = UE Reguler + KPB 1 + KPB 2 + KPB 3 + KPB 4.
- Total revenue laporan utama = Revenue Jasa + Revenue Oli + Revenue HGP.
- ACV kelas bulanan = total UE aktual seluruh POS kelas tersebut ÷ total Target Fix kelas tersebut.
- Rata-rata UE POS = total UE aktual kelas ÷ jumlah POS yang mempunyai data pada bulan itu.

## Privasi

Repository ini dan website GitHub Pages Anda bersifat publik. `data.js` dan `ue_class_data.js` diterbitkan dan dapat diakses publik. Filter POS dan kelas hanya memfilter tampilan, bukan membatasi hak akses. Unggah workbook mentah ke `source-data/` hanya apabila perusahaan menyetujui workbook ringkasan UE tersebut dipublikasikan. Jangan unggah workbook laporan utama yang memuat sheet transaksi pelanggan.
