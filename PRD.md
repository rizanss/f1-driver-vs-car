# PRD — F1 Driver vs Car

Oct 1, 2026 · @Riza Nursyah · Status: Draft v2

## Ringkasan

Kita membangun alat analisis yang memisahkan **seberapa cepat driver F1** dari **seberapa cepat mobilnya**, memakai data qualifying 2018–2026. Hasil akhirnya adalah ranking driver dan ranking mobil yang "adil", lengkap dengan tingkat keyakinannya, ditampilkan di dashboard interaktif yang mudah dipahami penggemar F1.

Project ini adalah side project portfolio. Fokusnya murni data science (statistik dan modeling), tanpa LLM. Target selesai versi pertama: 4 minggu.

## Latar belakang dan masalah

Di F1, hasil balapan sangat ditentukan mobil. Driver juara dunia di mobil papan bawah tidak akan menang, dan driver biasa di mobil terbaik bisa terlihat seperti bintang. Akibatnya, perdebatan "siapa driver terbaik" hampir selalu bias oleh mobil.

Ada dua "eksperimen alami" yang bisa kita manfaatkan untuk memisahkan keduanya:

- **Rekan setim.** Dua driver di tim yang sama memakai mobil yang hampir sama. Selisih waktu mereka sebagian besar adalah selisih skill.
- **Driver pindah tim.** Driver yang sama memakai mobil berbeda. Perubahan performanya sebagian besar adalah perbedaan mobil.

Kalau semua perbandingan ini digabung dalam satu model statistik, kita bisa memperkirakan kontribusi driver dan mobil secara terpisah untuk seluruh grid.

## Tujuan dan bukan tujuan

**Tujuan v1:**

1. Menghasilkan rating kecepatan satu lap (one-lap pace) untuk setiap driver per musim, 2018–2026.
2. Menghasilkan rating kecepatan mobil untuk setiap tim per musim.
3. Menampilkan tingkat keyakinan untuk setiap rating, bukan cuma satu angka.
4. Menjawab pertanyaan "bagaimana kalau driver X memakai mobil Y".
5. Menjadi portfolio yang menunjukkan cara berpikir statistik yang rapi dan jujur.

**Bukan tujuan v1:**

- Mengukur kemampuan balapan (menyalip, menjaga ban, strategi). Ini masuk v2.
- Memprediksi pemenang balapan atau juara dunia.
- Analisis kondisi hujan. Sesi basah dikeluarkan dulu.
- Memakai LLM dalam bentuk apa pun.

Karena fokusnya qualifying, nama hasil kita adalah **"one-lap pace rating"**, bukan "skill driver" secara keseluruhan.

## Siapa penggunanya

| Pengguna | Yang mereka cari |
| --- | --- |
| Recruiter dan interviewer data science | Bukti bisa membangun model statistik dari nol sampai hasil yang bisa dibaca |
| Penggemar F1 | Jawaban berbasis data untuk debat "siapa driver terbaik" |
| Riza sendiri | Belajar Bayesian modeling secara mendalam lewat topik yang disukai |

Pertanyaan utama yang harus bisa dijawab:

- Siapa driver tercepat kalau semua memakai mobil yang sama?
- Mobil mana yang paling cepat di tiap musim?
- Seberapa besar peran mobil dibanding driver? Apakah berubah setelah regulasi 2022 dan 2026?
- Bagaimana perkembangan seorang driver dari tahun ke tahun?

## Apa yang dibangun

Ada dua hasil akhir: dashboard dan repository kode yang rapi dengan README singkat.

**Isi dashboard:**

| Fitur | Isinya | Prioritas |
| --- | --- | --- |
| Ranking driver | Rating tiap driver per musim, dengan rentang keyakinan | Wajib |
| Ranking mobil | Rating tiap tim per musim | Wajib |
| Peta perpindahan driver | Gambar jaringan: siapa pernah setim dengan siapa, siapa pindah ke mana | Wajib |
| Perjalanan karier | Grafik rating seorang driver dari tahun ke tahun | Wajib |
| Mobil vs driver | Berapa persen performa dijelaskan mobil vs driver, per era regulasi | Wajib |
| Simulasi tukar mobil | Pilih driver dan mobil, lihat perkiraan selisih ke pole | Wajib |
| Adu dua driver | Peluang driver A lebih cepat dari driver B | Wajib |

**README** berisi ringkasan masalah, cara kerja model dalam beberapa kalimat, hasil validasi, cara menjalankan pipeline, dan screenshot dashboard.

**Cara membaca rating:** angka dalam satuan persen selisih waktu. Contoh: rating -0,3% berarti driver itu sekitar 0,3% lebih cepat dari rata-rata driver di mobil yang sama. Di lap 90 detik, itu sekitar 0,27 detik.

## Data

Semua data gratis dan bisa diambil lewat Python.

| Sumber | Dipakai untuk | Catatan |
| --- | --- | --- |
| FastF1 (library Python) | Waktu Q1/Q2/Q3, info cuaca, lap yang dihapus | Sumber utama, data lengkap sejak 2018 |
| Jolpica (pengganti Ergast) | Data qualifying sebelum 2018 | Opsional, kalau mau memperpanjang ke 2014 |

**Periode:** musim 2018 sampai seri terakhir yang sudah selesai di 2026.

**Satu baris data** = satu waktu terbaik seorang driver di satu bagian qualifying (Q1, Q2, atau Q3). Perkiraan jumlahnya sekitar 1.000 baris per musim, total sekitar 9.000–10.000 baris.

**Aturan pembersihan data:**

1. Buang bagian sesi (Q1/Q2/Q3) yang basah: ada driver yang memasang ban intermediate atau wet di bagian itu. Flag `Rainfall` FastF1 hanya dipakai sebagai cek tambahan karena sering on/off. Simpan daftarnya untuk v2.
2. Buang lap yang dihapus karena melanggar batas lintasan. Pakai waktu resmi Q1/Q2/Q3 dari hasil sesi, yang sudah tidak menghitung lap yang dihapus.
3. Buang driver yang ikut di bagian sesi itu tapi tidak punya waktu (crash, masalah mesin, red flag sebelum sempat lap). Driver yang gugur di bagian sebelumnya bukan data yang dibuang.
4. Buang lap yang tidak serius: waktu yang lebih lambat dari 102% waktu terbaik driver itu sendiri di sesi yang sama (penalti grid, run yang batal karena bendera kuning atau merah), plus jaring pengaman 107% dari waktu tercepat di bagian sesi untuk driver yang hanya punya satu waktu. Patokan ke waktu tercepat grid tidak dipakai karena ikut membuang hampir semua data mobil lambat (contoh: Williams 2019).
5. Sprint qualifying dipakai sebagai sesi tersendiri, dengan definisi per tahun:
   - 2021–2022: "Sprint Qualifying" sebenarnya balapan sprint, jadi **dibuang**. Grid sprint ditentukan qualifying biasa hari Jumat, dan itu tetap dipakai.
   - 2023: "Sprint Shootout" (SQ1/SQ2/SQ3), dipakai.
   - 2024 ke atas: "Sprint Qualifying" (SQ1/SQ2/SQ3), dipakai.
6. Catat setiap baris yang dibuang beserta alasannya di satu file log, supaya bisa dicek ulang.

**Angka yang dimodelkan:** waktu lap diubah ke skala persen (memakai logaritma) supaya sirkuit pendek dan panjang bisa dibandingkan secara adil.

## Cara kerja model

Model menganggap setiap waktu lap tersusun dari lima bagian:

**Waktu lap = kondisi sesi + kecepatan mobil + kecepatan driver + kondisi tim di sesi itu + faktor acak**

| Bagian | Artinya | Contoh |
| --- | --- | --- |
| Kondisi sesi | Semua hal yang sama untuk semua driver di sesi itu | Panjang sirkuit, suhu, aspal makin cepat menjelang Q3 |
| Kecepatan mobil | Seberapa cepat mobil tim tertentu di musim tertentu | Mobil juara 2023 vs mobil papan bawah 2023 |
| Kecepatan driver | Seberapa cepat driver dibanding driver rata-rata di mobil yang sama | Selisih rutin seorang driver ke rekan setimnya |
| Kondisi tim di sesi itu | Hal yang dirasakan bersama dua rekan setim di satu bagian sesi | Mobil kebetulan tidak cocok dengan sirkuit itu, waktu keluar pit yang sama |
| Faktor acak | Hal kecil yang tidak bisa dijelaskan | Angin, sedikit kesalahan di satu tikungan |

Tiga aturan penting di dalam model:

1. **Skill driver boleh berubah pelan-pelan dari musim ke musim.** Driver bisa berkembang atau menurun, tapi tidak melompat drastis tanpa alasan. Driver baru rata-rata membaik di musim keduanya, dan besarnya dipelajari dari data.
2. **Mobil dianggap baru setiap musim.** Terutama karena ada perubahan regulasi besar di 2022 dan 2026, mobil tahun lalu tidak bisa dijadikan patokan.
3. **Model tidak gampang "kaget" oleh lap aneh.** Satu lap yang rusak tidak boleh mengubah rating secara besar.

Model ini memakai **pendekatan Bayesian**. Dalam bahasa sederhana: model tidak hanya memberi satu angka, tapi rentang kemungkinan. Driver dengan banyak data mendapat rentang sempit (yakin). Rookie dengan sedikit data mendapat rentang lebar (belum yakin). Ini lebih jujur daripada ranking biasa.

## Alur end-to-end

&#91;embedded content: alur project · 6 tahap, 1 putaran perbaikan\]

Kalau model gagal di tahap validasi, kita kembali memperbaiki model, bukan langsung lanjut ke dashboard.

## Ukuran keberhasilan

Project dianggap berhasil kalau semua tes di bawah lolos.

| Tes | Pertanyaannya | Lolos kalau |
| --- | --- | --- |
| Lawan pembanding sederhana | Apakah model lebih baik dari sekadar menghitung rata-rata selisih ke rekan setim? | Error prediksi model lebih kecil dari pembanding |
| Tes masa depan | Latih model dengan data sampai 2025, lalu tebak selisih antar rekan setim di 2026 | Tebakan lebih akurat dari pembanding, walau mobil 2026 serba baru |
| Data palsu vs data asli | Kalau model membuat data tiruan, apakah mirip data asli? | Sebaran selisih waktu tiruan mirip yang asli |
| Kesehatan model | Apakah proses perhitungan berjalan stabil? | Tidak ada peringatan teknis (R-hat < 1,01, tanpa divergence) |
| Ketahanan asumsi | Kalau asumsi awal diubah sedikit, apakah ranking berubah drastis? | Urutan 5 besar tetap mirip |
| Akal sehat | Apakah hasil cocok dengan kasus yang sudah diketahui publik? | Kasus driver pindah tim yang terkenal bisa dijelaskan model |

**Definisi dua tes pertama:** yang ditebak adalah selisih waktu ke rekan setim di tiap bagian sesi (dalam persen), pada data yang tidak dipakai untuk latihan. Ukurannya MAE (rata-rata besar melesetnya tebakan).

- **Tebakan pembanding:** pembanding = rata-rata selisih driver ke rekan setim per musim. Tebakan selisih A vs B = (rating A − rating B) / 2, karena tiap selisih terhitung dua kali (dari sisi A dan dari sisi B).
- **Tebakan model:** β_A − β_B, karena mobil dan kondisi sesi saling coret untuk dua rekan setim. Driver-musim yang ditebak dimasukkan ke model sebagai musim tanpa data, jadi tebakannya mengikuti random walk, termasuk efek musim kedua.
- **Tes lawan pembanding:** 20% GP per musim disembunyikan secara acak (satu akhir pekan utuh), diulang dengan 5 pengacakan (seed 0–4). Angka pembanding: MAE 0,315% di seed 0, atau 0,315–0,338% di 5 seed. Lolos kalau model lebih baik di setiap pengacakan.
- **Tes masa depan:** latih dengan data sampai 2025, uji di 2026. Angka pembanding: MAE 0,382%, sedikit lebih buruk dari tebakan "semua rekan setim setara" (0,372%), karena banyak pasangan baru di 2026.

Tes "masa depan" adalah yang paling penting. Regulasi 2026 mengubah mobil secara total, jadi ini membuktikan rating driver benar-benar terbawa ke mobil baru, bukan sekadar menghafal data lama.

**Kriteria tes lainnya (dikunci sebelum melihat hasil):**

- **Data palsu vs data asli:** dari model dibuat 400 dataset tiruan. Kuantil 25, 50, 75, 90, dan 99% dari besar selisih ke rekan setim di data asli harus masuk rentang 90% dataset tiruan.
- **Kesehatan model:** R-hat < 1,01 dan 0 divergence, berlaku untuk model penuh dan semua run latih ulang.
- **Ketahanan asumsi:** prior τ_driver, τ_drift, dan τ_mobil masing-masing dikali ½ dan 2, jadi ada 6 variasi. Lolos kalau minimal 4 dari 5 driver teratas tiap musim tetap sama.
- **Akal sehat:** 6 kasus pindah tim. Lolos kalau bagian terbesar dari perubahan rating cocok dengan yang diharapkan:
  - Karena mobil: ALO 2022→2023, SAI 2024→2025, PER 2020→2021, BOT 2021→2022, dan ALB 2020→2022.
  - Karena driver: RIC 2020→2021.

**Hasil validasi (Tahap 4, model final):** angka lengkapnya ada di `outputs/validation.json`.

| Tes | Hasil | Status |
| --- | --- | --- |
| Lawan pembanding | Model menang di 5 dari 5 pengacakan. MAE model 0,309–0,326% vs pembanding 0,315–0,338% (seed 0: 0,313 vs 0,315) | Lolos |
| Tes masa depan | Model 0,385% vs pembanding 0,382% vs "semua setara" 0,372% | Gagal tipis |
| Data palsu vs asli | 3 dari 5 kuantil masuk. Median selisih tiruan 0,290% vs asli 0,277% (selisih sekitar 5%) | Gagal tipis |
| Kesehatan model | Model penuh: 0 divergence, R-hat 1,004. Run latih ulang: semuanya 0 divergence, tapi 4 dari 12 punya R-hat > 1,01 (tertinggi 1,025) | Gagal di run latih ulang |
| Ketahanan asumsi | Minimal 4 dari 5 driver teratas tetap sama di semua musim dan semua variasi | Lolos |
| Akal sehat | 4 dari 6 cocok. PER (driver +0,076 vs mobil +0,069) dan RIC (dua-duanya di bawah 0,03) nyaris seri | Gagal tipis |

**Catatan hasil:**

- **Tes masa depan:** kekalahan model menumpuk di Red Bull. Model menebak HAD 0,51% lebih lambat dari VER, padahal aslinya 0,10%, dan LAW juga begitu. Di 2026 keunggulan VER atas rekan setimnya mengecil. Di luar Red Bull, model lebih akurat dari pembanding. Contohnya pasangan baru BOT–PER di Cadillac: model meleset 0,65%, pembanding 0,91%.
- **Kesehatan model:** R-hat tinggi berasal dari Haas 2018–2020. MAG dan GRO cuma pernah membawa Haas, jadi porsi mobil dan driver sulit dipisah, apalagi kalau 20% GP disembunyikan. Low-rank mass matrix dari nutpie sudah dicoba dan tidak membantu.
- **Perbaikan model hanya satu putaran:** efek tim × bagian sesi, plus efek musim kedua. Sebelum perbaikan hasilnya: tes masa depan 0,398%, median selisih tiruan 0,364%, akal sehat 5 dari 6. Perbaikan berhenti di situ karena hasil 2026 sudah terlihat, dan perbaikan lebih lanjut berisiko menyesuaikan model ke data uji. Kegagalan yang tersisa dicatat sebagai batasan model.

## Risiko dan batasan

| Risiko | Dampaknya | Cara mengatasi |
| --- | --- | --- |
| Dua driver yang hanya pernah setim satu sama lain | Selisih mereka jelas, tapi posisi mereka dibanding grid kurang akurat | Tampilkan peta perpindahan driver dan beri catatan di dashboard |
| Rookie dengan data sedikit | Rentang keyakinan lebar | Tampilkan rentangnya, jangan disembunyikan |
| Perlakuan tim tidak sama ke dua driver (upgrade duluan, setup beda) | Ikut terhitung sebagai skill driver | Sebutkan sebagai batasan di README |
| Mobil kuat di sirkuit tertentu saja | Rating mobil jadi rata-rata kasar | Sebagian sudah diserap efek tim × bagian sesi. Efek tipe sirkuit ditangani di v2 |
| Data 2026 belum lengkap | Rating 2026 kurang stabil | Update model setiap selesai seri |
| Proses perhitungan lambat | Iterasi jadi lama | Mulai dengan 2–3 musim dulu, baru diperluas; pakai NumPyro kalau perlu |

## Rencana kerja

&#91;embedded content: rencana kerja · 4 minggu, 4 gate\]

Setiap minggu ditutup dengan satu gate. Jangan lanjut ke minggu berikutnya sebelum gate-nya terpenuhi.

## Panduan eksekusi di Claude Code

Kerjakan per tahap, satu tahap satu sesi. Jangan minta Claude Code membangun semuanya sekaligus.

**Tech stack:**

| Kebutuhan | Pilihan |
| --- | --- |
| Bahasa | Python 3.11+ |
| Ambil data | fastf1 |
| Olah data | pandas, pyarrow (simpan sebagai parquet) |
| Model | PyMC (cadangan: NumPyro kalau lambat) |
| Cek hasil model | ArviZ |
| Grafik | matplotlib untuk analisis, Recharts atau Visx untuk dashboard |
| Peta jaringan driver | networkx untuk analisis, react-force-graph untuk dashboard |
| Dashboard | Next.js (static export) yang membaca file JSON hasil model, deploy ke Vercel |
| Tes kode | pytest |

**Struktur folder:**

```
f1-driver-vs-car/
├── CLAUDE.md          # aturan kerja untuk Claude Code
├── PRD.md             # dokumen ini
├── data/
│   ├── raw/           # cache FastF1
│   └── clean/         # parquet siap pakai + log data yang dibuang
├── src/
│   ├── ingest.py      # ambil data qualifying per musim
│   ├── clean.py       # aturan pembersihan data
│   ├── network.py     # peta perpindahan driver
│   ├── baseline.py    # pembanding sederhana
│   ├── model.py       # model Bayesian
│   └── evaluate.py    # semua tes keberhasilan
├── notebooks/         # eksplorasi dan hasil
├── outputs/           # hasil model (JSON rating + sampel posterior, grafik)
├── web/               # dashboard Next.js, baca JSON dari outputs/
└── tests/
```

**Isi CLAUDE.md yang disarankan:**

- Baca PRD.md sebelum mulai tahap baru.
- Kerjakan hanya tahap yang diminta, lalu berhenti dan ringkas hasilnya.
- Jangan download ulang data kalau sudah ada di cache.
- Setiap fungsi pembersihan data wajib punya tes.
- Uji model dengan 2 musim dulu sebelum menjalankan semua musim.

**Spesifikasi model (bagian teknis, untuk Claude Code):**

Target: y = 100 × ln(waktu lap dalam detik). Satuan efek = persen.

```latex
\begin{aligned}
y_i &\sim \text{StudentT}(\nu,\ \mu_i,\ \sigma) \\
\mu_i &= \alpha_{\text{sesi}[i]} + \beta_{\text{driver}[i],\,\text{musim}[i]} + \gamma_{\text{tim}[i],\,\text{musim}[i]} + \delta_{\text{tim}[i],\,\text{sesi}[i]} \\
\beta_{d,s} &\sim \mathcal{N}(\beta_{d,s-1} + \lambda\,\mathbb{1}[s = \text{musim kedua } d],\ \tau_{\text{drift}}), \quad \beta_{d,s_0} \sim \mathcal{N}(0,\ \tau_{\text{driver}}) \\
\gamma_{t,s} &\sim \mathcal{N}(0,\ \tau_{\text{mobil}}), \quad \textstyle\sum_t \gamma_{t,s} = 0 \\
\delta_{t,p} &\sim \mathcal{N}(0,\ \tau_{\text{tim-sesi}}) \\
\textstyle\sum_{d \in D_s} \beta_{d,s} &= 0 \quad \text{(}D_s\text{ = driver yang aktif di musim } s\text{)}
\end{aligned}
```

Catatan implementasi:

- **Kunci nol untuk β:** rata-rata β tiap musim dikunci ke nol karena tidak bisa dibedakan dari α (semua sesi di satu musim kena geseran yang sama). Tanpa kunci ini, random walk membuat rata-rata grid bergeser bebas, dan sampler jadi lambat atau divergen. Caranya: kurangi β mentah dengan rata-ratanya per musim sebelum masuk ke μ.
- **Non-centered parameterization** dipakai untuk efek-efek di model.
- **Driver yang absen satu musim atau lebih** tetap pakai random walk, dengan drift yang diperbesar sesuai jumlah musim yang hilang.
- **δ (kondisi tim di sesi itu)** menangkap hal yang dirasakan bersama dua rekan setim di satu bagian sesi. Tanpa δ, noise dua rekan setim berkorelasi 0,29 dan sebaran data tiruan jadi terlalu lebar.
- **λ (efek musim kedua)** hanya berlaku untuk driver yang debut di 2018 ke atas, jadi bukan veteran yang kembali seperti KUB dan KVY. Hasil estimasinya: driver rata-rata 0,13% lebih cepat di musim keduanya.
- **Sampling:** 4 chain × 2.000 draw.
- **Tampilan rating:** tanda dibalik, supaya angka lebih tinggi = lebih cepat.

**Urutan tahap dan syarat selesai:**

1. **Tahap 1: Data**
   - [x] `ingest.py` mengambil semua qualifying 2018–2026 dan menyimpannya ke cache
   - [x] `clean.py` menerapkan 6 aturan pembersihan dan menulis log data yang dibuang
   - [x] Tes: jumlah baris per musim masuk akal, tidak ada waktu kosong
2. **Tahap 2: Peta dan pembanding**
   - [x] Gambar peta perpindahan driver
   - [x] Pembanding sederhana: rata-rata selisih ke rekan setim
3. **Tahap 3: Model**
   - [x] Model jalan untuk 2 musim tanpa peringatan teknis
   - [x] Model jalan untuk semua musim
   - [x] Simpan rating driver dan mobil ke `outputs/`
4. **Tahap 4: Validasi**
   - [x] Semua tes di bagian Ukuran keberhasilan dijalankan dan hasilnya dicatat
5. **Tahap 5: Dashboard dan README**
   - [ ] Dashboard modern menggunakan Next JS dengan 7 fitur wajib
   - [ ] README singkat

**Contoh prompt pembuka di Claude Code:**

> Baca PRD.md dan CLAUDE.md. Kerjakan Tahap 1 saja. Mulai dengan rencana singkat, lalu eksekusi. Uji dengan musim 2023 dulu sebelum menjalankan semua musim.

## Pengembangan berikutnya (v2)

Setelah v1 selesai dan dipublikasikan, urutan pengembangan yang disarankan:

1. **Race pace:** pakai lap balapan di udara bersih, dikoreksi berat bahan bakar dan umur ban. Ini mengukur kemampuan balapan, bukan cuma satu lap.
2. **Tipe sirkuit:** mobil boleh punya kekuatan berbeda di sirkuit kecepatan tinggi, sirkuit jalan raya, dan sirkuit teknis.
3. **Skill di kondisi basah:** sesi hujan yang dibuang di v1 dipakai untuk rating terpisah.
4. **Update otomatis:** model diperbarui setiap selesai seri, dan dashboard menampilkan perubahannya.
