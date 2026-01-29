# 📊 CHANGELOG - Sofinco

## [3.0.0] - 2026-01-24

### 🎉 Major Release - Production-Ready Features

#### ✨ New Features
- **REPL Interactive Mode**: Interactive shell untuk eksperimen cepat dengan history dan namespace management
- **Decompiler**: Convert Sofinco code kembali ke Python dengan command `sofinco decompile`
- **Syntax Checker**: Validasi syntax tanpa eksekusi dengan `sofinco check`
- **Code Formatter**: Auto-format kode dengan custom indentation `sofinco format`
- **AST Viewer**: Visualisasi Abstract Syntax Tree dalam format tree atau JSON
- **Profiler**: Analisis performa program dengan cProfile integration
- **Linter**: Deteksi masalah kode seperti mixed indentation, trailing whitespace, missing colons
- **Benchmark**: Ukur kecepatan eksekusi dengan multiple iterations dan statistik lengkap
- **Documentation System**: Built-in docs untuk semua keyword dengan `sofinco docs`
- **Package Manager**: Install dan list Python packages dengan `sofinco install` dan `sofinco list`
- **JavaScript Transpiler**: Experimental transpilation ke JavaScript

#### 🔧 Improvements
- Enhanced CLI dengan 15 commands total
- Better error messages dengan line numbers dan context
- Improved keyword mapping dengan 200+ mappings
- Production-ready codebase tanpa demo files
- Comprehensive help system

#### 📝 Commands Available
- `run` - Execute Sofinco programs
- `convert` - Python to Sofinco conversion
- `decompile` - Sofinco to Python conversion
- `check` - Syntax validation
- `format` - Code formatting
- `ast` - Show Abstract Syntax Tree
- `repl` - Interactive mode
- `version` - Version information
- `install` - Install packages
- `list` - List packages
- `profile` - Performance profiling
- `lint` - Code linting
- `benchmark` - Performance benchmarking
- `docs` - Keyword documentation
- `transpile` - JavaScript transpilation

#### 🗑️ Removed
- Demo files (contoh.py, contoh2.py, test_sofinco.txt)
- Development documentation files
- Duplicate vscode-extension folder
- Build artifacts

### 📦 Dependencies
- Python >= 3.8
- No external dependencies required

---

## [2.1.0] - 2026-01-22

### 🎉 Critical Bug Fix - Execution Context

#### 🐛 Fixed
- **Major Fix**: Programs with `if __name__ == "__main__":` now execute correctly
  - Fixed `exec()` namespace to include `__name__ = "__main__"`
  - Resolved issue where main blocks weren't running
  - All complex programs now work as expected

#### ✅ Verified
- Successfully converted and ran 26 files from sofintwerk-test project
- All Python syntax validation passed
- Complex programs with imports, classes, and exception handling work perfectly

#### 📦 Tested Projects
- Sofintwerk Network Tool (26 files, 100% success)
- All syntax features validated in production code

---

## [2.0.0] - 2026-01-22

### 🎉 Major Release - Python to Sofinco Converter

#### ✨ Added
- **Python to Sofinco Converter**: Convert Python files to Sofinco syntax
  - Single file conversion: `sofinco convert file.py`
  - Recursive directory conversion: `sofinco convert /path/to/dir/`
  - Non-recursive option: `sofinco convert /path/to/dir/ --no-recursive`
- **Subcommands**: New CLI structure with `run` and `convert` commands
- **Backward Compatibility**: Old syntax `sofinco file.sofinco` still works
- **Context-Sensitive Conversion**: Smart handling of keywords like `as`, `with`, `import`, `except`
- **100+ Keyword Mappings**: Complete Python to Sofinco syntax mapping
- **Comprehensive Example**: `contoh2.sofinco` with 467 lines demonstrating all syntax features

#### 🔧 Enhanced
- Improved `convert_sofinco_to_python()` with context-aware keyword handling
- Better error messages and progress indicators
- Enhanced documentation with conversion examples
- Updated all syntax highlighting files (Vim, VSCode, Sublime, Nano, LazyVim)

#### 🐛 Fixed
- Multi-word operators (`not in`, `is not`) conversion
- Import statements with aliases (`import x as y`, `from x import y as z`)
- Exception handling with aliases (`except ValueError as e`)
- With statements (`with open() as f`)

#### 📊 Technical Details
- Core module expanded to 633 lines (from 343 lines)
- Added reverse mapping dictionary (PYTHON_TO_SOFINCO)
- Implemented smart pattern matching for context-sensitive keywords
- Full test coverage with complex example file

---

## [1.4.0] - 2026-01-21

### ✨ Added
- **100+ Keyword Baru** dalam Bahasa Bugis-Makassar:
  - Data types: bilanga, aksara, desimal, daptar, tupel, peta, himpunan, bolean, bytes, objek
  - Control flow: nakko, nakkopa, narekko, ulangi, sedding, tappai, laoi, lewati
  - Functions: pangngaseng, baliki, lambda, yield, async, await
  - Built-in functions: paccerak, passuluak, jangka, carakna, jumlahki, palingciddi, palinglompo
  - String methods: sappai, gantiki, lompo, ciddi, pecaki, gabungki
  - List methods: tambai, burakne, urutkanki, balikidaptar, sisipki, hapuski, bersihki
  - Operators: rilaleng, taniarilaleng, sisamaya, taniasisamaya, dan, atau, tania
  - Exception handling: coba, nakkosala, nakkosedding, bangkitki, kudu
  - File operations: bukka, baca, tulis, tutup, bacabarisa, bacasemua

- **🎨 Syntax Highlighting Support** untuk:
  - ✅ VSCode (full extension dengan auto-indent, bracket matching)
  - ✅ Vim/Neovim (classic syntax highlighting)
  - ✅ LazyVim (modern Neovim dengan Treesitter support)
  - ✅ Sublime Text (full syntax support)
  - ✅ Nano (basic syntax highlighting)

- **📁 Folder `sofinco-syntax/`** berisi:
  - VSCode extension (siap install)
  - Vim syntax files
  - LazyVim plugin config
  - Sublime Text syntax
  - Nano syntax config
  - Panduan instalasi lengkap (INSTALL.md)

### 🔄 Changed
- Update deskripsi dari "Bahasa Makassar" → "Bahasa Bugis-Makassar"
- Update README.md dengan info syntax highlighting
- Perbaikan keyword map dengan kategori yang lebih terorganisir

### 📝 Documentation
- Tambah INSTALL.md untuk panduan instalasi syntax highlighting
- Tambah README.md di folder sofinco-syntax
- Update README utama dengan quick install guide

---

## [1.3.2] - Previous Version
- Initial release dengan keyword dasar

---

## 🚀 Cara Update

```bash
pip install --upgrade sofinco
```

## 📦 Install Syntax Highlighting

Lihat [sofinco-syntax/INSTALL.md](sofinco-syntax/INSTALL.md) untuk panduan lengkap.

**Quick Install LazyVim:**
```bash
cp sofinco-syntax/lazyvim/lua/plugins/sofinco.lua ~/.config/nvim/lua/plugins/
cp sofinco-syntax/vim/syntax/sofinco.vim ~/.config/nvim/syntax/
cp sofinco-syntax/vim/ftdetect/sofinco.vim ~/.config/nvim/ftdetect/
```

**Quick Install VSCode:**
```bash
cp -r sofinco-syntax/vscode ~/.vscode/extensions/sofinco-vscode
```

Restart editor setelah instalasi!
