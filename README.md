# POS AHASS Performance Dashboard

Dashboard statis berbahasa Indonesia untuk memonitor performa POS AHASS berdasarkan sheet `Form Responses 1` dari file laporan.

## Isi dashboard

- Filter POS AHASS dan periode laporan.
- Ringkasan KPI: total UE, revenue, UE KPB, dan rata-rata mekanik hadir per laporan.
- Tren bulanan Unit Entry dan revenue.
- Breakdown UE Reguler/KPB 1–4 dan revenue jasa/oli/HGP.
- Tabel detail laporan dan ekspor CSV sesuai filter aktif.
- Link tampilan spesifik POS melalui tombol **Salin Link POS**.

### Definisi yang digunakan

- **Total UE** = UE Reguler + KPB 1 + KPB 2 + KPB 3 + KPB 4.
- **Total Revenue** = Revenue Jasa + Revenue Oli + Revenue HGP.
- **Rata-rata mekanik hadir** = jumlah mekanik hadir pada semua laporan yang masuk / jumlah laporan.
- Dashboard tidak menampilkan persentase pencapaian target karena file sumber tidak menyediakan target per POS.

## Cara publish melalui GitHub Pages

1. Buat repository baru di GitHub, misalnya `pos-ahass-dashboard`.
2. Upload isi folder ini: `index.html`, `data.js`, `.nojekyll`, `README.md`, dan `generate_data.py`. **Jangan upload workbook Excel mentah**.
3. Buka **Settings → Pages**.
4. Pada **Build and deployment**, pilih **Deploy from a branch**, pilih branch `main` dan folder `/(root)`, lalu klik **Save**.
5. Setelah proses deployment selesai, buka URL yang ditampilkan di bagian Pages.

Dokumentasi resmi: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Link untuk masing-masing POS

Di dashboard, pilih POS lalu klik **Salin Link POS**. Link akan berisi parameter `?pos=<id-pos>` dan membuka tampilan dengan pilihan POS dikunci. Link ini memudahkan distribusi dashboard, tetapi **bukan sistem login atau pembatasan akses yang aman**.

## Penting: privasi dan akses

GitHub Pages biasanya menerbitkan website ke internet. Walaupun repository bersifat private, website Pages tetap publik kecuali organisasi memakai GitHub Enterprise Cloud dan mengatur visibilitas Pages menjadi private. Karena itu:

- Jangan publikasikan data revenue/operasional perusahaan sebelum mendapat persetujuan pihak berwenang.
- Filter dan link POS spesifik hanya mengubah tampilan; pengguna yang mendapatkan URL tetap dapat memeriksa source website dan `data.js`.
- Jika setiap kabeng/PIC **wajib hanya dapat mengakses POS miliknya**, dashboard perlu autentikasi sungguhan dan aturan akses di backend, misalnya Supabase Auth + Row Level Security atau sistem internal perusahaan. Jangan mengandalkan dropdown, URL rahasia, atau menyembunyikan data di JavaScript sebagai keamanan.

Dokumentasi visibilitas GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site

## Cara memperbarui data dari Excel

1. Simpan file Excel terbaru di komputer Anda.
2. Pastikan sheet sumber bernama `Form Responses 1` dan kolomnya masih sama.
3. Jalankan di folder dashboard:

   ```bash
   python generate_data.py "Laporan Pos Sumatera Selatan (Responses).xlsx"
   ```

4. Script menghasilkan ulang `data.js`, hanya dari kolom performa POS yang diperlukan. Sheet transaksi servis lain yang berisi detail pelanggan tidak dibaca atau diekspor.
5. Upload/commit perubahan `data.js` ke repository GitHub.

Dashboard statis ini tidak terhubung otomatis ke Excel atau Google Form. Pembaruan baru akan tampil setelah `data.js` diperbarui dan di-deploy ulang.

## Catatan kualitas data pada file yang digunakan

File sumber yang diproses berisi 143 laporan untuk 15 POS, dengan tanggal laporan antara Januari–Desember 2026. Terdapat laporan bertanggal setelah 16 Oktober 2026 pada file sumber. Dashboard menandai periode mendatang dan membukanya secara default pada bulan berjalan bila data tersedia. Periksa tanggal tersebut sebelum menggunakan nilainya sebagai realisasi.
