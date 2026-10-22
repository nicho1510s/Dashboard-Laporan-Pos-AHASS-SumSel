# Dashboard Laporan POS AHASS Sumatera Selatan — Google Sheets Auto Sync

Repository ini memuat dashboard POS AHASS, snapshot data operasional, data UE bulanan per kelas HIGH/MIDDLE/LOW, generator data, dan workflow GitHub Pages. Workflow mengambil data dari spreadsheet yang ditautkan pengguna secara otomatis setiap 6 jam dan menerbitkan ulang dashboard.

## File utama

- `index.html` — dashboard.
- `data.js` — data laporan operasional (UE Reguler/KPB, revenue, mekanik) yang dapat diperbarui otomatis jika sumber Google Sheets juga memiliki tab `Form Responses 1` dengan layout yang sesuai.
- `ue_class_data.js` — data bulanan POS Service per kelas.
- `generate_data.py` — generator laporan operasional dari tab `Form Responses 1`.
- `generate_ue_class_data.py` — generator UE bulanan dari tab seperti `UE POS JUN`, `UE POS JUL`, `UE POS AUG`, `UE POS SEP`, `UE POS OKT`, dan seterusnya.
- `sync_google_sheet.py` — mengunduh spreadsheet dari tautan yang sudah dikonfigurasi dan menjalankan generator yang sesuai.
- `.github/workflows/pages.yml` — sinkronisasi otomatis dan deploy ke GitHub Pages.

## Satu kali setup

1. Pastikan file Google Sheets dapat dibaca oleh GitHub Actions tanpa login interaktif. Di Google Sheets, klik **Share / Bagikan → General access / Akses umum → Anyone with the link / Siapa saja yang memiliki link → Viewer / Pelihat**. Lakukan ini hanya jika data memang boleh diakses publik. Karena dashboard di-host di GitHub Pages publik, data yang ditampilkan di dashboard juga dapat dilihat publik.
2. Unduh ZIP repository lengkap, ekstrak, lalu salin **seluruh isi folder** ke folder repository lokal yang sudah di-clone menggunakan GitHub Desktop. Pilih replace/overwrite untuk file yang sama.
3. Commit semua perubahan ke branch `main` dan klik **Push origin**.
4. Di GitHub buka **Settings → Pages → Build and deployment → Source**, pilih **GitHub Actions**.
5. Buka tab **Actions → Sync Google Sheets and publish POS AHASS dashboard → Run workflow**. Biarkan input `year` kosong untuk memakai tahun WIB saat ini; atau isi tahun yang sesuai bila sheet berisi data tahun tertentu.
6. Pastikan workflow berakhir hijau. Kunjungi website Pages dan refresh dengan `Ctrl+F5`.

## Update otomatis

Workflow dijadwalkan setiap enam jam, sekitar pukul 03.37, 09.37, 15.37, dan 21.37 WIB. GitHub dapat menunda workflow terjadwal saat antrean padat, jadi ini bukan update real-time tepat saat sel Google Sheets diedit. Anda juga dapat menjalankannya manual dari tab Actions.

Workflow mengunduh file XLSX dari spreadsheet dengan ID `17uQxNnFVIUxRWOZ4DISYrpUzoD3OQmTq`. Setelah file didapat, workflow memperbarui data di lingkungan build dan menerbitkan versi website terbaru. Dataset hasil build tidak otomatis di-commit balik ke branch `main`; yang berubah adalah salinan file yang diterbitkan di GitHub Pages.

## Penting: sumber data harus memiliki tab yang sesuai

- Jika workbook memuat tab bulanan seperti `UE POS JUN`, `UE POS JUL`, dan seterusnya, `ue_class_data.js` akan diperbarui.
- Jika workbook juga memuat tab `Form Responses 1` dengan format kolom yang sama seperti sumber laporan operasional lama, `data.js` juga akan diperbarui.
- Jika tab `Form Responses 1` tidak ada, workflow akan mempertahankan `data.js` lama. Bagian laporan harian/revenue dengan demikian tidak berubah; hanya data UE bulanan/kelas yang diperbarui. Untuk menjadikan bagian itu otomatis juga, sediakan tab `Form Responses 1` yang sesuai di workbook ini atau tambahkan sumber spreadsheet kedua.
- Tab UE bulanan perlu mengikuti struktur yang saat ini dibaca generator: mulai data pada baris 6; B=kode AHASS, D=kelas, F=nama POS, G:AK=UE harian hari 1–31, AL=Total, AM=Target Fix, AN=ACV, AO=status SIP.
- Nama tab seperti `UE POS JUN` tidak mencantumkan tahun. Workflow menggunakan tahun saat ini di zona waktu Asia/Jakarta. Jika workbook memuat bulan dari tahun lain, jalankan workflow manual dan isi `year` yang benar. Jangan menggabungkan dua tahun pada tab tanpa penanda tahun yang jelas.

## Jika workflow gagal

1. Buka repository → **Actions** → klik run yang gagal → buka langkah **Refresh data from Google Sheets**.
2. `HTTP 401/403`, HTML login, atau respons bukan XLSX: periksa akses **Anyone with the link / Viewer** dan pastikan tautan masih aktif.
3. Tidak menemukan tab `UE POS ...`: periksa bahwa tautan mengarah ke workbook yang benar dan nama tab sesuai format.
4. Pastikan **Settings → Pages → Source** menggunakan GitHub Actions.

## Keamanan

Repository dan website ini publik. Google Sheets yang diatur `Anyone with the link` dapat dibaca oleh siapa pun yang memperoleh tautannya. Jangan gunakan cara ini untuk data pelanggan, informasi pribadi, atau KPI rahasia yang tidak disetujui untuk publik. Untuk dashboard privat per PIC/Kabeng, gunakan backend dengan autentikasi dan otorisasi per POS; filter di HTML bukan kontrol akses.
