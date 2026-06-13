# SINTA - SNBT Intelligent Tutor Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
SINTA adalah aplikasi tutor SNBT berbasis Streamlit. Aplikasi ini membantu pengguna bertanya materi, meminta latihan soal, mengecek jawaban, membaca pembahasan, mengelola sesi belajar, dan menyimpan riwayat secara offline di SQLite.

Fokus produk:

- Chat belajar yang terasa seperti tutor pribadi.
- Proyek dan sesi percakapan seperti workspace belajar.
- Latihan soal SNBT dengan evaluasi jawaban.
- Penyimpanan offline yang tidak memotong isi pesan utama.
- Dukungan LaTeX/KaTeX untuk rumus dan opsi jawaban numerik.
- Database lokal berisi use case belajar untuk QA dan presentasi.

## Fitur Utama

- Chat tutor SNBT dengan konteks percakapan.
- Routing otomatis untuk tanya jawab, quiz, evaluasi, dan rekomendasi belajar.
- Proyek belajar dan sesi percakapan di sidebar.
- Ubah nama proyek dan sesi.
- Hapus proyek dan sesi aktif langsung dari sidebar.
- Reset database dari `Pengaturan`.
- Penyimpanan offline menggunakan SQLite.
- Log kuis dan ringkasan performa sesi.
- Upload PDF untuk bahan belajar RAG.
- Pencarian web opsional untuk konteks terbaru.
- Output panjang dengan auto-continuation agar jawaban tidak berhenti di tengah.
- Metadata model untuk diagnosis internal, termasuk finish reason dan token config.

## Tampilan Aplikasi

Halaman utama berisi percakapan. Sidebar dipakai untuk:

- memilih proyek,
- memilih sesi,
- membuat proyek baru,
- membuat sesi baru,
- mengubah nama proyek atau sesi,
- menghapus proyek atau sesi aktif,
- melihat ringkasan sesi,
- melihat log kuis terakhir,
- mengatur API Gemini (Future Update: OpenAI API),
- memilih mapel dan tingkat kesulitan,
- mengaktifkan pencarian web,
- mengunggah PDF,
- mereset database.

## Struktur Data

Database utama:

```text
sinta_offline.db
```

Tabel utama:

- `projects`: daftar proyek belajar.
- `conversations`: sesi percakapan per proyek.
- `messages`: pesan user dan assistant.
- `quiz_attempts`: histori latihan soal dan evaluasi.

Catatan penting:

- Isi pesan utama disimpan penuh di `messages.content`.
- State percakapan di `conversations.state_json` dibuat compact supaya database tidak membengkak.
- Metadata model disimpan di `messages.model_metadata_json`.

## Data Demo Lokal

Database lokal dapat diisi dengan skenario belajar yang realistis, bukan sekadar data dummy pendek.

Contoh proyek:

- `Aisyah - Target Kedokteran PTN`
- `Raka - Gap Year Teknik Informatika`
- `Nabila - IPS Ekonomi UI`
- `Dimas - Remedial Tryout 535`
- `Sari - RAG PDF Materi Sekolah`
- `Fajar - Takut Matematika`
- `Mira - Kecepatan Literasi`
- `Bima - Saintek Numerik`
- `Lina - Sprint 14 Hari`
- `Demo QA - Output, KaTeX, dan Continuation`

Contoh sesi demo yang baik berisi alur percakapan multi-turn:

- diagnosis konteks siswa,
- penjelasan konsep,
- latihan soal,
- jawaban siswa,
- evaluasi,
- bedah jebakan opsi,
- rencana tindak lanjut,
- catatan belajar.

File database aktif saat ini adalah `sinta_offline.db`. Reset database dapat dilakukan dari sidebar aplikasi melalui `Pengaturan`.

## Menjalankan Aplikasi

Install dependency:

```bash
pip install -r requirements.txt
```

Jalankan Streamlit:

```bash
streamlit run app.py
```

Lalu buka sidebar `Pengaturan` dan masukkan Gemini API key.

## Cara Pakai

1. Buka aplikasi dengan `streamlit run app.py`.
2. Masukkan Gemini API key di `Pengaturan`.
3. Pilih proyek atau buat proyek baru.
4. Pilih sesi atau buat sesi baru.
5. Tulis pertanyaan, minta soal, atau jawab soal dengan A/B/C/D/E.
6. Gunakan upload PDF jika ingin SINTA memakai materi sendiri.
7. Gunakan reset database jika ingin mengosongkan database aktif.

Contoh prompt:

```text
Jelaskan peluang bersyarat dari nol dengan contoh SNBT.
```

```text
Buatkan soal TPS kuantitatif level sedang.
```

```text
Aku jawab C, tolong nilai dan jelaskan jebakannya.
```

```text
Pendek banget, jelaskan lebih lengkap.
```

## LaTeX dan KaTeX

SINTA merender rumus melalui Markdown Streamlit. Output matematika perlu memakai delimiter:

- inline: `$...$`
- block: `$$...$$`

Opsi jawaban numerik juga dinormalisasi agar angka seperti `80%`, `1/2`, atau `0,25` tampil sebagai:

```markdown
$80\%$
$\frac{1}{2}$
$0,25$
```

## Reset dan Hapus Data

Di sidebar:

- `Hapus sesi`: menghapus sesi aktif beserta pesan dan quiz attempt di dalamnya.
- `Hapus proyek`: menghapus proyek aktif beserta semua sesi, pesan, dan quiz attempt di dalamnya.
- `Reset database`: mengosongkan database aktif dan membuat workspace default baru.

Reset database memakai dua konfirmasi di UI. Hapus proyek/sesi dibuat sederhana seperti aplikasi chat: pilih item aktif, lalu klik hapus.

## Struktur File

```text
app.py                       UI utama Streamlit
agent_graph.py               Workflow tutor dan pemanggilan LLM
rag_engine.py                RAG PDF dan pencarian web
sinta_store.py               Storage SQLite offline
knowledge_base.py            Pengetahuan bawaan
ui/theme.py                  Konstanta tema
ui/components.py             CSS dan komponen UI
requirements.txt             Dependency Python
SINTA_PANDUAN.md             Panduan singkat pengguna
```

## Validasi

Compile file Python utama:

```bash
python -m py_compile app.py agent_graph.py sinta_store.py rag_engine.py knowledge_base.py
```

Jika `python` di Windows mengarah ke Microsoft Store stub dan gagal, gunakan interpreter Python/Conda yang aktif di mesin.

## Catatan Teknis

- Runtime LLM memakai Gemini melalui `langchain_google_genai`.
- `agent_graph.py` memiliki auto-continuation untuk output yang kena batas token.
- `sinta_store.py` memakai SQLite dengan foreign key cascade untuk proyek, sesi, pesan, dan quiz attempt.
- State sesi sengaja dibuat compact agar `state_json` tidak membuat database membesar ekstrem.
- `messages.content` tetap menyimpan jawaban penuh.

## Lisensi

Belum ditetapkan.
