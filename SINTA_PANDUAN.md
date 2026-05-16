# SINTA — SNBT Intelligent Tutor Assistant

SINTA adalah asisten belajar SNBT yang membantu kamu latihan soal, memahami konsep, mengecek jawaban, dan menyusun strategi belajar.

## Cara Menggunakan

1. Buka bagian `Pengaturan` di halaman utama.
2. Masukkan `Gemini API Key` lalu aktifkan SINTA.
3. Tulis pertanyaan atau minta latihan soal.
4. Pilih mapel dan tingkat kesulitan jika ingin hasil yang lebih terarah.
5. Aktifkan pencarian web bila ingin informasi yang lebih baru.
6. Unggah PDF jika ingin SINTA belajar dari bahan kamu sendiri.

## Peran Bagian-Bagian SINTA

- **Penyusun Soal**: membuat latihan soal sesuai mapel dan tingkat kesulitan.
- **Penilai Jawaban**: memeriksa jawaban kamu dan memberi umpan balik.
- **Pemberi Saran**: memberi strategi belajar dan langkah berikutnya.
- **Tanya Jawab Umum**: menjawab pertanyaan penjelasan materi.
- **Pengarah Topik**: memastikan pertanyaan kamu diarahkan ke bantuan yang tepat.
- **Pencari Konteks**: mengambil materi pendukung dari catatan atau PDF yang kamu unggah.

## Sidebar

Sidebar sekarang dipakai untuk:

- memilih proyek belajar,
- berpindah antar sesi percakapan,
- melihat ringkasan sesi,
- melihat log kuis terakhir,
- menyembunyikan atau menampilkan sidebar.

## Penyimpanan Offline

Semua data disimpan offline di database SQLite lokal:

- percakapan,
- proyek,
- hasil kuis,
- log kuis.

File database tersimpan di folder aplikasi dan bisa dipakai lagi saat SINTA dibuka ulang.

## Tips Pakai

- Kalau ingin latihan, sebutkan mapel dan level.
- Kalau ingin pembahasan, kirim jawabanmu setelah mengerjakan soal.
- Kalau ingin konsep, tulis topik spesifik seperti peluang, listrik, atau stoikiometri.
- Kalau ingin jawaban terbaru, aktifkan pencarian web.

## Yang Tidak Perlu Diketahui Pengguna

SINTA sengaja menampilkan nama dan fungsi yang sederhana. Detail teknis internal seperti model, alur pemrosesan, atau istilah infrastruktur tidak perlu muncul di tampilan utama.
