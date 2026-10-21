# Folder sumber UE bulanan

Untuk memperbarui panel UE bulanan secara otomatis, unggah workbook Excel terbaru dengan nama persis:

`UE POS AHASS.xlsx`

Letakkan file di folder `source-data/` ini. Setelah file dikomit ke branch `main`, GitHub Actions akan membuat ulang `ue_class_data.js` dan menerbitkan dashboard.

**Peringatan:** repository saat ini bersifat publik. Jika workbook diunggah ke sini, salinan workbook tersebut dapat dilihat pengunjung repository. Panel dashboard hanya membutuhkan data ringkasan UE, kelas, target, dan status SIP. Jika perusahaan tidak menyetujui publikasi workbook, jangan unggah XLSX mentah; proses di komputer sendiri menggunakan `generate_ue_class_data.py`, lalu unggah hanya file output `ue_class_data.js`.

Jangan menaruh workbook `Laporan Pos Sumatera Selatan (Responses).xlsx` ke repository publik. Workbook tersebut berukuran besar dan mempunyai sheet transaksi tambahan yang tidak perlu dipublikasikan.
