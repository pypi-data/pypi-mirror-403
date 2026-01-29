# SOFINCO - Bahasa Pemrograman Bahasa Bugis-Makassar

Bahasa pemrograman dengan sintaks Bahasa Bugis-Makassar yang berjalan di atas Python. Semua fitur Python bisa digunakan dengan nama dalam Bahasa Bugis-Makassar!

## 🚀 FITUR BARU v3.0

### 🔥 Fitur Production-Ready
- ✅ **REPL Interactive Mode** - Mode interaktif untuk eksperimen cepat
- ✅ **Decompiler** - Convert Sofinco kembali ke Python
- ✅ **Syntax Checker** - Validasi syntax tanpa eksekusi
- ✅ **Code Formatter** - Format kode otomatis
- ✅ **AST Viewer** - Visualisasi Abstract Syntax Tree
- ✅ **Profiler** - Analisis performa program
- ✅ **Linter** - Deteksi masalah kode
- ✅ **Benchmark** - Ukur kecepatan eksekusi
- ✅ **Docs** - Dokumentasi keyword built-in
- ✅ **Package Manager** - Install library Python
- ✅ **Transpiler JS** - Experimental JavaScript output

## 📦 CARA INSTAL
```bash
pip install sofinco
```

## 🚀 CARA PAKAI

### Menjalankan Program Sofinco
```bash
sofinco run namafile.sofinco
# atau
sofinco namafile.sofinco
```

Opsi tambahan:
```bash
sofinco run namafile.sofinco --nosv  # Tidak menyimpan file Python hasil konversi
```

### Convert Python ke Sofinco

**Convert single file:**
```bash
sofinco convert file.py
```

**Convert direktori (rekursif):**
```bash
sofinco convert /path/to/directory
```

**Convert direktori (non-rekursif):**
```bash
sofinco convert /path/to/directory --no-recursive
```

### Decompile Sofinco ke Python

```bash
sofinco decompile program.sofinco
sofinco decompile program.sofinco -o output.py
```

### Check Syntax

```bash
sofinco check program.sofinco
```

### Format Code

```bash
sofinco format program.sofinco           # Buat file baru
sofinco format program.sofinco -i        # Format in-place
sofinco format program.sofinco --indent 2  # Custom indentation
```

### REPL Interactive Mode

```bash
sofinco repl
```

### Profiling & Benchmarking

```bash
sofinco profile program.sofinco
sofinco profile program.sofinco -o profile.txt
sofinco benchmark program.sofinco
sofinco benchmark program.sofinco --iterations 1000
```

### Linting

```bash
sofinco lint program.sofinco
```

### AST Viewer

```bash
sofinco ast program.sofinco
sofinco ast program.sofinco --format json
```

### Documentation

```bash
sofinco docs              # List semua keyword
sofinco docs paccerak     # Detail keyword tertentu
```

### Package Management

```bash
sofinco install requests
sofinco list
```

### Transpile to JavaScript (Experimental)

```bash
sofinco transpile program.sofinco
```

### Version Info

```bash
sofinco version
sofinco --version
```

## 📝 CONTOH PROGRAM

### Test Suite Lengkap
Jalankan test suite komprehensif yang mencakup semua fitur:
```bash
sofinco run test.sofinco
```

Test suite mencakup:
- ✅ Tipe Data Dasar (Integer, String, Float, Boolean, None)
- ✅ Struktur Data (List, Tuple, Dict, Set)
- ✅ Operasi List (append, sort, reverse, dll)
- ✅ Operasi Dictionary (keys, values, items, dll)
- ✅ Operasi String (upper, lower, split, join, dll)
- ✅ Fungsi (definisi, rekursif, parameter default)
- ✅ Kondisi (if-elif-else, nested)
- ✅ Loop (for, while, break, continue)
- ✅ Operator Logika (and, or, not, in, is)
- ✅ Exception Handling (try-except-finally)
- ✅ Built-in Functions (range, len, sum, min, max, dll)
- ✅ Kelas dan Objek (class, __init__, methods)
- ✅ Lambda Function
- ✅ List Comprehension
- ✅ Import Module
- ✅ Advanced Features (unpacking, formatting)
- ✅ Stress Test (nested loops, large data)

### Program Sederhana
```sofinco
# Program sederhana
paccerak("Assalamu Alaikum!")

# Fungsi
pangngaseng sapa(jeneng):
    paccerak("Halo,", jeneng)
    baliki "Selamat datang!"

hasil = sapa("Makassar")

# Kondisi
umuru = 20
nakko umuru >= 18:
    paccerak("Dewasa")
nakkopa umuru >= 13:
    paccerak("Remaja")
narekko:
    paccerak("Anak-anak")

# Loop
ulangi i rilaleng jangka(1, 6):
    paccerak(i)

# List operations
daptar_nama = daptar(["Ali", "Budi", "Citra"])
daptar_nama.tambai("Dedi")
paccerak("Jumlah:", carakna(daptar_nama))

# Exception handling
coba:
    bilanga("abc")
nakkosala ValueError siaganga e:
    paccerak("Error:", e)
nakkosedding:
    paccerak("Selesai")
```

## 🔤 REFERENSI LENGKAP SYNTAX

### 📥 Input/Output
| Sofinco | Python | Arti |
|---------|--------|------|
| paccerak | print | Cetak ke layar |
| cetak | print | Cetak ke layar (alternatif) |
| passuluak | input | Terima input |
| terima | input | Terima input (alternatif) |

### 🔢 Tipe Data
| Sofinco | Python | Arti |
|---------|--------|------|
| bilanga | int | Bilangan bulat |
| uwinru | int | Bilangan bulat (alternatif) |
| aksara | str | String/teks |
| sura | str | String/teks (alternatif) |
| desimal | float | Bilangan desimal |
| daptar | list | List/daftar |
| kumpulan | list | List/daftar (alternatif) |
| tupel | tuple | Tuple |
| peta | dict | Dictionary |
| pada | dict | Dictionary (alternatif) |
| himpunan | set | Set |
| bolean | bool | Boolean |

### ✅ Nilai Boolean
| Sofinco | Python | Arti |
|---------|--------|------|
| makanja | True | Benar |
| makasiri | True | Benar (alternatif) |
| demakanja | False | Salah |
| tamakasiri | False | Salah (alternatif) |
| taniaapa | None | Kosong/None |
| kosong | None | Kosong/None |
| tannia | None | Kosong/None (alternatif) |

### 🔀 Kontrol Alur
| Sofinco | Python | Arti |
|---------|--------|------|
| nakko | if | Jika |
| wennang | if | Jika (alternatif) |
| nakkopa | elif | Jika lagi |
| wennangpa | elif | Jika lagi (alternatif) |
| narekko | else | Selain itu |
| naiya | else | Selain itu (alternatif) |
| ulangi | for | Perulangan untuk |
| sedding | while | Perulangan selama |
| tappai | break | Hentikan loop |
| laoi | continue | Lanjut iterasi |
| lewati | pass | Lewati/pass |
| pilih | match | Pilih kasus (Python 3.10+) |
| kasus | case | Kasus (Python 3.10+) |

### 🔧 Fungsi & Kelas
| Sofinco | Python | Arti |
|---------|--------|------|
| pangngaseng | def | Definisi fungsi |
| pangngadereng | def | Definisi fungsi (alternatif) |
| baliki | return | Kembalikan nilai |
| pole | return | Kembalikan nilai (alternatif) |
| fungsi_singkat | lambda | Fungsi lambda |
| kelas | class | Definisi kelas |
| pangngassengang | class | Definisi kelas (alternatif) |
| inisialisasi | __init__ | Konstruktor |
| statis | staticmethod | Metode statis |
| kelas_metode | classmethod | Metode kelas |
| properti | property | Properti |
| induk | super | Super class |

### ⚠️ Exception Handling
| Sofinco | Python | Arti |
|---------|--------|------|
| coba | try | Coba eksekusi |
| nakkosala | except | Tangkap error |
| nakkosedding | finally | Akhirnya |
| bangkitki | raise | Bangkitkan error |
| kudu | assert | Pastikan kondisi |

### 📦 Import & Module
| Sofinco | Python | Arti |
|---------|--------|------|
| impor | import | Import modul |
| riboko | from | Dari modul |
| siaganga | as | Sebagai alias |

### 📁 Operasi File
| Sofinco | Python | Arti |
|---------|--------|------|
| bukka | open | Buka file |
| tulis | write | Tulis ke file |
| baca | read | Baca file |
| bacabarisa | readline | Baca per baris |
| bacasemua | readlines | Baca semua baris |
| tutup | close | Tutup file |
| modetulis | "w" | Mode tulis |
| modebaca | "r" | Mode baca |
| modeambah | "a" | Mode tambah |
| modebiner | "b" | Mode biner |

### 🛠️ Fungsi Built-in
| Sofinco | Python | Arti |
|---------|--------|------|
| jangka | range | Rentang angka |
| carakna | len | Panjang/jumlah |
| jumlahki | sum | Jumlahkan |
| palingciddi | min | Nilai minimum |
| palinglompo | max | Nilai maksimum |
| urutki | sorted | Urutkan (baru) |
| balikkidaptar | reversed | Balik urutan |
| hitungurut | enumerate | Hitung dengan urutan |
| gabung_daptar | zip | Gabung list |
| petakan | map | Petakan fungsi |
| saring | filter | Saring data |
| semua | all | Semua benar |
| ada | any | Ada yang benar |
| mutlak | abs | Nilai mutlak |
| bulatki | round | Bulatkan |
| pangkat | pow | Pangkat |
| tipe | type | Tipe data |
| daftar_atribut | dir | Daftar atribut |
| variabel | vars | Variabel objek |
| bantuan | help | Bantuan |
| evaluasi | eval | Evaluasi ekspresi |
| eksekusi | exec | Eksekusi kode |
| kompilasi | compile | Kompilasi kode |
| formatki | format | Format string |
| karakter | chr | Karakter dari kode |
| nilai_karakter | ord | Kode dari karakter |
| heksadesimal | hex | Konversi ke hex |
| oktal | oct | Konversi ke oktal |
| biner | bin | Konversi ke biner |
| iris | slice | Slice objek |
| induk | super | Akses parent class |

### 📋 Metode List
| Sofinco | Python | Arti |
|---------|--------|------|
| tambai | append | Tambah di akhir |
| burakne | pop | Ambil & hapus |
| urutkanki | sort | Urutkan (in-place) |
| balikidaptar | reverse | Balik urutan |
| sisipki | insert | Sisipkan di posisi |
| hapuski | remove | Hapus nilai |
| bersihki | clear | Kosongkan |
| hitungki | count | Hitung kemunculan |
| indexki | index | Cari indeks |
| extendki | extend | Gabung list |
| copyaki | copy | Salin list |

### 📚 Metode Dictionary
| Sofinco | Python | Arti |
|---------|--------|------|
| kunci | keys | Ambil semua kunci |
| nilai | values | Ambil semua nilai |
| pasangan | items | Ambil pasangan key-value |
| ambilki | get | Ambil nilai |
| perbaharui | update | Perbarui dictionary |
| bersihki | clear | Kosongkan |
| burakne | pop | Ambil & hapus |
| salinki | copy | Salin dictionary |

### 🔢 Metode Set
| Sofinco | Python | Arti |
|---------|--------|------|
| tambahki | add | Tambah elemen |
| buangki | discard | Buang elemen |
| hapuski | remove | Hapus elemen |
| bersihki | clear | Kosongkan |
| gabungan | union | Gabungan set |
| irisan | intersection | Irisan set |
| selisih | difference | Selisih set |
| selisih_simetris | symmetric_difference | Selisih simetris |

### 📝 Metode String
| Sofinco | Python | Arti |
|---------|--------|------|
| sappai | find | Cari posisi |
| gantiki | replace | Ganti teks |
| lompo | upper | Huruf besar |
| ciddi | lower | Huruf kecil |
| kapital | capitalize | Kapital awal |
| judul | title | Format judul |
| potongki | strip | Potong spasi |
| pecaki | split | Pecah string |
| gabungki | join | Gabung string |
| mulai_dengan | startswith | Mulai dengan |
| akhiri_dengan | endswith | Akhiri dengan |
| huruf_semua | isalpha | Cek huruf semua |
| angka_semua | isdigit | Cek angka semua |
| huruf_angka | isalnum | Cek huruf/angka |
| spasi_semua | isspace | Cek spasi semua |
| ciddi_semua | islower | Cek huruf kecil |
| lompo_semua | isupper | Cek huruf besar |
| isi_nol | zfill | Isi dengan nol |
| tengahki | center | Rata tengah |
| kiri_rata | ljust | Rata kiri |
| kanan_rata | rjust | Rata kanan |
| tukar_huruf | swapcase | Tukar besar-kecil |
| enkode | encode | Encode string |
| dekode | decode | Decode string |

### 🔗 Operator Logika
| Sofinco | Python | Arti |
|---------|--------|------|
| rilaleng | in | Di dalam |
| taniarilaleng | not in | Tidak di dalam |
| sisamaya | is | Adalah (identitas) |
| taniasisamaya | is not | Bukan (identitas) |
| dan | and | Dan |
| atau | or | Atau |
| tania | not | Tidak |

## 💡 CONTOH LENGKAP

### Convert Python ke Sofinco
```bash
# File Python
cat example.py
```
```python
def greet(name):
    print(f"Hello, {name}!")
    return True

for i in range(5):
    print(i)
```

```bash
# Convert ke Sofinco
sofinco convert example.py
```

```bash
# Hasil: example.sofinco
cat example.sofinco
```
```sofinco
pangngaseng greet(name):
    paccerak(f"Hello, {name}!")
    baliki makanja

ulangi i rilaleng jangka(5):
    paccerak(i)
```

### Operasi File
```sofinco
# Tulis file
siaganga bukka("data.txt", modetulis) siaganga berkas:
    berkas.tulis("Halo Makassar!\n")

# Baca file
siaganga bukka("data.txt", modebaca) siaganga berkas:
    isi = berkas.baca()
    paccerak(isi)
```

### Exception Handling
```sofinco
coba:
    angka = bilanga(passuluak("Masukkan angka: "))
    hasil = 100 / angka
    paccerak("Hasil:", hasil)
nakkosala ValueError:
    paccerak("Input bukan angka!")
nakkosala ZeroDivisionError:
    paccerak("Tidak bisa dibagi nol!")
nakkosedding:
    paccerak("Program selesai")
```

### Kelas & Objek
```sofinco
kelas Manusia:
    pangngaseng inisialisasi(diri, nama, umur):
        diri.nama = nama
        diri.umur = umur
    
    pangngaseng perkenalan(diri):
        paccerak("Nama saya", diri.nama)
        paccerak("Umur saya", diri.umur)

orang = Manusia("Ahmad", 25)
orang.perkenalan()
```

### List & Dictionary
```sofinco
# List operations
angka = daptar([5, 2, 8, 1, 9])
angka.urutkanki()
paccerak("Terurut:", angka)
paccerak("Terkecil:", palingciddi(angka))
paccerak("Terbesar:", palinglompo(angka))

# Dictionary
data = peta({"nama": "Budi", "umur": 20})
paccerak(data.get("nama"))
```

### Loop & Kondisi
```sofinco
# Loop dengan break dan continue
ulangi i rilaleng jangka(1, 11):
    nakko i == 5:
        laoi  # Skip angka 5
    nakko i == 8:
        tappai  # Berhenti di 8
    paccerak(i)

# While loop
hitung = 0
sedding hitung < 5:
    paccerak("Hitung:", hitung)
    hitung = hitung + 1
```

## ⚙️ PERSYARATAN SISTEM
- Python 3.8 atau lebih baru
- Sofinco **TIDAK BISA** berjalan tanpa Python (transpiler berbasis Python)

## 🎨 SYNTAX HIGHLIGHTING

Sofinco mendukung syntax highlighting di berbagai editor!

**Supported Editors:**
- VSCode
- Vim/Neovim
- LazyVim
- Sublime Text
- Nano

**Quick Install (LazyVim):**
```bash
cp sofinco-syntax/lazyvim/lua/plugins/sofinco.lua ~/.config/nvim/lua/plugins/
cp sofinco-syntax/vim/syntax/sofinco.vim ~/.config/nvim/syntax/
cp sofinco-syntax/vim/ftdetect/sofinco.vim ~/.config/nvim/ftdetect/
```

**Quick Install (VSCode):**
```bash
cp -r sofinco-syntax/vscode ~/.vscode/extensions/sofinco-vscode
```

Lihat dokumentasi lengkap di [GitHub](https://github.com/levouinse/sofinco-language) untuk panduan instalasi syntax highlighting.

## 🤝 KONTRIBUSI
Kontribusi sangat diterima! Silakan buat issue atau pull request di GitHub.

## 📄 LISENSI
MIT License

## 🔗 LINKS
- PyPI: https://pypi.org/project/sofinco/
- GitHub: https://github.com/levouinse/sofinco-language
- Dokumentasi: https://github.com/levouinse/sofinco-language/wiki

