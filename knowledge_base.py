"""
Knowledge base builder untuk materi SNBT.
Berisi materi built-in TPS, TKA Saintek, dan TKA Soshum.
"""

SNBT_KNOWLEDGE = """
# MATERI TPS (Tes Potensi Skolastik) SNBT

## 1. PENALARAN UMUM

### Logika Deduktif
Logika deduktif adalah proses penarikan kesimpulan dari premis yang bersifat umum ke khusus.
- Silogisme: Semua A adalah B. C adalah A. Maka C adalah B.
- Modus Ponens: Jika P maka Q. P benar. Maka Q benar.
- Modus Tollens: Jika P maka Q. Q salah. Maka P salah.

### Logika Induktif
Penarikan kesimpulan dari hal khusus ke umum berdasarkan observasi.
Contoh: Semua angsa yang pernah diamati berwarna putih → Semua angsa berwarna putih.

### Analogi Verbal
Mencari hubungan antar pasangan kata.
Contoh: Dokter : Rumah Sakit = Guru : Sekolah (hubungan profesi dengan tempat kerja)

### Deret dan Pola Angka
- Deret aritmatika: selisih antar suku tetap (a, a+b, a+2b, ...)
- Deret geometri: rasio antar suku tetap (a, ar, ar², ...)
- Deret Fibonacci: setiap suku = jumlah dua suku sebelumnya

---

## 2. PENGETAHUAN DAN PEMAHAMAN UMUM (PPU)

### Ide Pokok Paragraf
Ide pokok adalah gagasan utama yang menjadi inti pembahasan paragraf. Letaknya bisa di awal (deduktif), akhir (induktif), atau awal-akhir (campuran).

### Makna Kata dalam Konteks
Makna kata harus disesuaikan dengan konteks kalimat, bukan makna harfiah.

### Sinonim dan Antonim Penting
- Absolut ↔ Relatif
- Konkret ↔ Abstrak  
- Konsisten ↔ Inkonsisten
- Kooperatif ↔ Tidak kooperatif

### Ejaan yang Disempurnakan (EYD)
- Huruf kapital: awal kalimat, nama orang, nama tempat, judul
- Tanda baca koma: anak kalimat, perincian, sebelum konjungsi pertentangan
- Penulisan kata: kata baku vs tidak baku

---

## 3. KEMAMPUAN MEMAHAMI BACAAN DAN MENULIS (KMBM)

### Struktur Teks
- Teks argumentasi: tesis → argumen → penegasan ulang
- Teks narasi: orientasi → komplikasi → resolusi → koda
- Teks eksplanasi: pernyataan umum → urutan sebab-akibat → interpretasi

### Koherensi dan Kohesi
- Kohesi: keterkaitan antar kalimat secara gramatikal (penggunaan konjungsi, pronomina)
- Koherensi: keterkaitan antar kalimat secara makna/logika

---

## 4. PENGETAHUAN KUANTITATIF

### Aljabar Dasar
- Persamaan linear: ax + b = c → x = (c-b)/a
- Pertidaksamaan: perhatikan tanda saat kali/bagi dengan bilangan negatif
- Sistem persamaan linear dua variabel (SPLDV): metode substitusi dan eliminasi

### Aritmatika
- FPB (Faktor Persekutuan Terbesar): pakai pohon faktor
- KPK (Kelipatan Persekutuan Terkecil)
- Persentase: a% dari b = (a/100) × b
- Rasio dan proporsi: a/b = c/d → ad = bc

### Geometri Dasar
- Luas persegi = s²
- Luas persegi panjang = p × l
- Luas segitiga = ½ × a × t
- Luas lingkaran = πr²
- Volume balok = p × l × t
- Volume tabung = πr²t
- Teorema Pythagoras: a² + b² = c²

### Statistika Dasar
- Mean (rata-rata) = jumlah data / banyak data
- Median = nilai tengah setelah data diurutkan
- Modus = nilai yang paling sering muncul
- Jangkauan = nilai max - nilai min

---

# MATERI TKA SAINTEK SNBT

## MATEMATIKA SAINTEK

### Fungsi dan Grafik
- Fungsi linear: f(x) = mx + c (grafik berupa garis)
- Fungsi kuadrat: f(x) = ax² + bx + c (grafik berupa parabola)
  - Nilai diskriminan: D = b² - 4ac
  - D > 0: dua akar real berbeda
  - D = 0: dua akar real sama
  - D < 0: tidak ada akar real
- Fungsi eksponen: f(x) = aˣ
- Fungsi logaritma: f(x) = log_a(x)

### Trigonometri
- sin 0° = 0, sin 30° = ½, sin 45° = ½√2, sin 60° = ½√3, sin 90° = 1
- cos 0° = 1, cos 30° = ½√3, cos 45° = ½√2, cos 60° = ½, cos 90° = 0
- tan = sin/cos
- Identitas: sin²x + cos²x = 1
- Aturan sinus: a/sin A = b/sin B = c/sin C
- Aturan cosinus: a² = b² + c² - 2bc cos A

### Kalkulus Dasar
- Turunan fungsi:
  - (xⁿ)' = nxⁿ⁻¹
  - (sin x)' = cos x
  - (cos x)' = -sin x
  - (eˣ)' = eˣ
  - (ln x)' = 1/x
- Integral tak tentu:
  - ∫xⁿ dx = xⁿ⁺¹/(n+1) + C
  - ∫sin x dx = -cos x + C
  - ∫cos x dx = sin x + C
- Aplikasi: gradien garis singgung, nilai ekstrem fungsi

### Kombinatorik dan Peluang
- Permutasi: P(n,r) = n!/(n-r)!
- Kombinasi: C(n,r) = n!/(r!(n-r)!)
- Peluang: P(A) = n(A)/n(S)
- Peluang komplemen: P(A') = 1 - P(A)
- Peluang gabungan: P(A∪B) = P(A) + P(B) - P(A∩B)

---

## FISIKA

### Mekanika
- Hukum Newton I: Benda diam tetap diam, bergerak lurus beraturan tetap begitu jika tidak ada gaya resultan.
- Hukum Newton II: F = ma (gaya = massa × percepatan)
- Hukum Newton III: Aksi = -Reaksi (besarnya sama, arahnya berlawanan)
- GLBB: v = v₀ + at, s = v₀t + ½at², v² = v₀² + 2as
- Gerak melingkar: v = ωr, a_s = v²/r = ω²r
- Energi kinetik: Ek = ½mv²
- Energi potensial: Ep = mgh
- Hukum kekekalan energi mekanik: Ek + Ep = konstan

### Gelombang dan Optika
- Gelombang: v = λf (kecepatan = panjang gelombang × frekuensi)
- Periode: T = 1/f
- Hukum pemantulan: sudut datang = sudut pantul
- Hukum Snell: n₁ sin θ₁ = n₂ sin θ₂
- Cermin cekung/cembung: 1/f = 1/s + 1/s'

### Listrik
- Hukum Ohm: V = IR
- Rangkaian seri: R_total = R₁ + R₂ + ...
- Rangkaian paralel: 1/R_total = 1/R₁ + 1/R₂ + ...
- Daya listrik: P = VI = I²R = V²/R
- Energi listrik: W = Pt = VIt

---

## KIMIA

### Struktur Atom
- Nomor atom = jumlah proton = jumlah elektron (atom netral)
- Nomor massa = proton + neutron
- Konfigurasi elektron: 1s² 2s² 2p⁶ 3s² 3p⁶ 4s² 3d¹⁰ ...

### Stoikiometri
- Mol = massa / massa molar
- Hukum Avogadro: 1 mol = 6,022 × 10²³ partikel
- Volume gas STP: 1 mol = 22,4 L
- Persen komposisi: (massa unsur / massa senyawa) × 100%

### Laju Reaksi dan Kesetimbangan
- Faktor laju reaksi: konsentrasi, suhu, katalis, luas permukaan
- Orde reaksi ditentukan dari eksperimen
- Kesetimbangan kimia: K = [produk]/[reaktan] (masing-masing dipangkatkan koefisien)
- Asas Le Chatelier: sistem merespons perubahan dengan menggeser kesetimbangan

### Asam-Basa
- pH = -log[H⁺]
- pOH = -log[OH⁻]
- pH + pOH = 14
- Asam kuat: HCl, H₂SO₄, HNO₃, HBr, HI, HClO₄
- Basa kuat: NaOH, KOH, Ca(OH)₂, Ba(OH)₂

---

## BIOLOGI

### Sel
- Sel prokariot: tidak punya membran inti (bakteri, archaea)
- Sel eukariot: punya membran inti (tumbuhan, hewan, fungi, protista)
- Organel penting: mitokondria (respirasi), kloroplas (fotosintesis), ribosom (sintesis protein), RE (transpor protein/lipid), badan Golgi (pengepakan)

### Metabolisme
- Fotosintesis: 6CO₂ + 6H₂O + cahaya → C₆H₁₂O₆ + 6O₂
  - Reaksi terang: di membran tilakoid, menghasilkan ATP dan NADPH
  - Siklus Calvin: di stroma, menghasilkan glukosa
- Respirasi aerob: C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + 38 ATP
  - Glikolisis → Dekarboksilasi oksidatif → Siklus Krebs → Rantai transpor elektron

### Genetika
- DNA: menyimpan informasi genetik, basa: Adenin, Timin, Guanin, Sitosin
- RNA: mRNA (pembawa kode), tRNA (pembawa asam amino), rRNA (komponen ribosom)
- Transkripsi: DNA → mRNA (di nukleus)
- Translasi: mRNA → protein (di ribosom)
- Hukum Mendel I: pemisahan alel saat pembentukan gamet
- Hukum Mendel II: kombinasi bebas alel dari gen berbeda

---

# MATERI TKA SOSHUM SNBT

## SEJARAH

### Masa Praaksara Indonesia
- Pithecanthropus erectus: ditemukan di Trinil oleh Eugene Dubois (1890)
- Meganthropus paleojavanicus: ditemukan di Sangiran
- Homo sapiens: manusia modern, ciri-ciri lebih halus

### Kerajaan Hindu-Buddha
- Kutai (Kalimantan, abad 4 M): kerajaan Hindu tertua di Indonesia, Prasasti Yupa
- Tarumanegara (Jawa Barat): Raja Purnawarman, Prasasti Tugu
- Sriwijaya (Sumatera, abad 7-13 M): kerajaan maritim, pusat agama Buddha
- Majapahit (Jawa Timur, 1293-1527): puncak kejayaan era Hayam Wuruk & Gajah Mada, Sumpah Palapa

### Masa Kolonial
- VOC (1602-1799): monopoli perdagangan Belanda
- Cultuurstelsel (1830-1870): Tanam Paksa, digagas Van den Bosch
- Politik Etis (1901): irigasi, edukasi, emigrasi (Trias van Deventer)

### Pergerakan Nasional
- Budi Utomo (1908): organisasi modern pertama, 20 Mei → Hari Kebangkitan Nasional
- Sumpah Pemuda (28 Oktober 1928): satu tanah air, bangsa, bahasa
- BPUPKI (29 April 1945): mempersiapkan kemerdekaan
- Proklamasi (17 Agustus 1945)

---

## GEOGRAFI

### Atmosfer dan Cuaca
- Troposfer (0-12 km): tempat cuaca terjadi, suhu turun seiring ketinggian
- Stratosfer (12-50 km): lapisan ozon melindungi dari UV
- Angin Muson: angin musim hujan (Oktober-April) dan kemarau (April-Oktober)

### Sumber Daya Alam
- SDA dapat diperbaharui: hutan, air, tanah, energi surya, angin
- SDA tidak dapat diperbaharui: minyak bumi, gas alam, batu bara, mineral
- Indonesia: ring of fire → banyak gunung berapi, rawan gempa tetapi tanah subur

### Persebaran Penduduk
- Piramida penduduk muda: negara berkembang, banyak anak-anak
- Piramida penduduk tua: negara maju, lebih banyak usia produktif dan tua
- Transisi demografis: dari angka kelahiran & kematian tinggi ke rendah

---

## SOSIOLOGI

### Stratifikasi Sosial
- Stratifikasi tertutup: kasta (sulit berpindah), contoh: sistem kasta di India
- Stratifikasi terbuka: kelas sosial (mudah berpindah), contoh: masyarakat modern
- Mobilitas sosial: vertikal (naik/turun kelas) dan horizontal (pindah posisi setara)

### Lembaga Sosial
- Fungsi lembaga: mengatur perilaku, memenuhi kebutuhan
- Jenis: keluarga (sosialisasi primer), pendidikan, agama, ekonomi, politik

### Perubahan Sosial
- Faktor internal: pertumbuhan penduduk, penemuan baru, konflik internal
- Faktor eksternal: bencana alam, peperangan, pengaruh budaya asing
- Modernisasi: proses menuju masyarakat modern dengan teknologi dan demokrasi

---

## EKONOMI

### Konsep Dasar
- Kelangkaan: kebutuhan > ketersediaan sumber daya → pilihan dan biaya peluang
- Biaya peluang (opportunity cost): nilai pilihan terbaik yang dikorbankan
- Sistem ekonomi: tradisional, komando (terpusat), pasar (liberal), campuran

### Permintaan dan Penawaran
- Hukum permintaan: harga naik → permintaan turun (ceteris paribus)
- Hukum penawaran: harga naik → penawaran naik (ceteris paribus)
- Keseimbangan pasar: pertemuan kurva permintaan dan penawaran

### Uang dan Perbankan
- Fungsi uang: alat tukar, satuan hitung, penyimpan nilai
- Bank sentral (Bank Indonesia): mengatur kebijakan moneter
- Kebijakan moneter ekspansif: menambah jumlah uang beredar (turunkan suku bunga, beli SBI)
- Kebijakan moneter kontraktif: mengurangi jumlah uang beredar (naikkan suku bunga, jual SBI)

### Pendapatan Nasional
- GDP (Gross Domestic Product): nilai produk yang dihasilkan dalam suatu negara
- GNP (Gross National Product): nilai produk yang dihasilkan warga negara
- Pendekatan penghitungan: produksi, pendapatan, pengeluaran

---

# TIPS DAN STRATEGI SNBT

## Strategi Umum
1. Baca soal dengan cermat dan tentukan kata kunci
2. Manajemen waktu: TPS 150 menit (115 soal), TKA 195 menit (maks 115 soal per kelompok)
3. Sistem poin: benar = 1, salah = -1/3, kosong = 0 (hati-hati menebak!)
4. Kerjakan yang mudah dulu, tandai yang sulit untuk dikerjakan belakangan
5. Untuk soal bacaan, baca pertanyaan terlebih dahulu sebelum teks

## Strategi TPS
- Penalaran Umum: latih logika formal (silogisme, implikasi)
- PPU: perbanyak membaca artikel ilmiah dan berita
- KMBM: pahami struktur teks dan koherensi
- PK: kuasai operasi hitung dasar dan pola angka

## Strategi Pilih TKA
- Pilih kelompok ujian yang sesuai jurusan tujuan
- Saintek: Matematika, Fisika, Kimia, Biologi
- Soshum: Sejarah, Geografi, Sosiologi, Ekonomi

## Jadwal Belajar Ideal
- 3-6 bulan sebelum ujian: kuasai materi fundamental
- 1-3 bulan sebelum: latihan soal intensif dan try out
- 1 bulan sebelum: review kelemahan dan simulasi penuh
- 1 minggu sebelum: review singkat, jaga kondisi fisik dan mental
"""

def get_knowledge_text():
    return SNBT_KNOWLEDGE
