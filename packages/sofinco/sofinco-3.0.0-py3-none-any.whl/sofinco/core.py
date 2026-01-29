import re
import sys
import ast
import json
from pathlib import Path
from typing import Dict, Any
import cProfile
import pstats
from io import StringIO
import time
import subprocess

KEYWORD_MAP = {
    # I/O Operations
    r"\bpaccerak\b": "print",
    r"\bpassuluak\b": "input",
    r"\bbaca_berkas\b": "open",
    r"\bcetak\b": "print",
    r"\bterima\b": "input",
    # Data Types
    r"\bbilanga\b": "int",
    r"\baksara\b": "str",
    r"\bdesimal\b": "float",
    r"\bdaptar\b": "list",
    r"\btupel\b": "tuple",
    r"\bpeta\b": "dict",
    r"\bhimpunan\b": "set",
    r"\bbolean\b": "bool",
    r"\bbytes\b": "bytes",
    r"\bbytearray\b": "bytearray",
    r"\bfrozenset\b": "frozenset",
    r"\bcomplex\b": "complex",
    r"\bmemoryview\b": "memoryview",
    r"\buwinru\b": "int",
    r"\bsura\b": "str",
    r"\bpada\b": "dict",
    r"\bkumpulan\b": "list",
    # Boolean Values
    r"\bmakanja\b": "True",
    r"\bdemakanja\b": "False",
    r"\btaniaapa\b": "None",
    r"\bkosong\b": "None",
    r"\bmakasiri\b": "True",
    r"\btamakasiri\b": "False",
    r"\btannia\b": "None",
    # Control Flow
    r"\bnakko\b": "if",
    r"\bnakkopa\b": "elif",
    r"\bnarekko\b": "else",
    r"\bulangi\b": "for",
    r"\bsedding\b": "while",
    r"\btappai\b": "break",
    r"\blaoi\b": "continue",
    r"\blewati\b": "pass",
    r"\bpilih\b": "match",
    r"\bkasus\b": "case",
    r"\bwennang\b": "if",
    r"\bwennangpa\b": "elif",
    r"\bnaiya\b": "else",
    # Functions & Classes
    r"\bpangngaseng\b": "def",
    r"\bbaliki\b": "return",
    r"\blambda\b": "lambda",
    r"\bfungsi_singkat\b": "lambda",
    r"\bkelas\b": "class",
    r"\bobjek\b": "object",
    r"\binisialisasi\b": "__init__",
    r"\byield\b": "yield",
    r"\basync\b": "async",
    r"\bawait\b": "await",
    r"\bdekorator\b": "decorator",
    r"\bstatis\b": "staticmethod",
    r"\bkelas_metode\b": "classmethod",
    r"\bproperti\b": "property",
    r"\bpangngadereng\b": "def",
    r"\bpole\b": "return",
    r"\bpangngassengang\b": "class",
    # Exception Handling
    r"\bcoba\b": "try",
    r"\bnakkosala\b": "except",
    r"\bnakkosedding\b": "finally",
    r"\bbangkitki\b": "raise",
    r"\bkudu\b": "assert",
    # Import & Module
    r"\bimpor\b": "import",
    r"\briboko\b": "from",
    r"\bsiaganga\b": "as",
    # File Operations
    r"\bsiaganga\b": "with",
    r"\bbukka\b": "open",
    r"\bmodetulis\b": '"w"',
    r"\bmodebaca\b": '"r"',
    r"\bmodeambah\b": '"a"',
    r"\bmodebiner\b": '"b"',
    r"\btulis\b": "write",
    r"\bbaca\b": "read",
    r"\bbacabarisa\b": "readline",
    r"\bbacasemua\b": "readlines",
    r"\btutup\b": "close",
    # Built-in Functions
    r"\bjangka\b": "range",
    r"\bjumlahki\b": "sum",
    r"\bcarakna\b": "len",
    r"\bpalingciddi\b": "min",
    r"\bpalinglompo\b": "max",
    r"\burutki\b": "sorted",
    r"\bbalikkidaptar\b": "reversed",
    r"\benumerate\b": "enumerate",
    r"\bhitungurut\b": "enumerate",
    r"\bzip\b": "zip",
    r"\bgabung_daptar\b": "zip",
    r"\bmap\b": "map",
    r"\bpetakan\b": "map",
    r"\bfilter\b": "filter",
    r"\bsaring\b": "filter",
    r"\ball\b": "all",
    r"\bsemua\b": "all",
    r"\bany\b": "any",
    r"\bada\b": "any",
    r"\babs\b": "abs",
    r"\bmutlak\b": "abs",
    r"\bround\b": "round",
    r"\bbulatki\b": "round",
    r"\bpow\b": "pow",
    r"\bpangkat\b": "pow",
    r"\btype\b": "type",
    r"\btipe\b": "type",
    r"\bisinstance\b": "isinstance",
    r"\bissubclass\b": "issubclass",
    r"\bcallable\b": "callable",
    r"\bhasattr\b": "hasattr",
    r"\bgetattr\b": "getattr",
    r"\bsetattr\b": "setattr",
    r"\bdelattr\b": "delattr",
    r"\bdir\b": "dir",
    r"\bdaftar_atribut\b": "dir",
    r"\bvars\b": "vars",
    r"\bvariabel\b": "vars",
    r"\bid\b": "id",
    r"\bhash\b": "hash",
    r"\bhelp\b": "help",
    r"\bbantuan\b": "help",
    r"\beval\b": "eval",
    r"\bevaluasi\b": "eval",
    r"\bexec\b": "exec",
    r"\beksekusi\b": "exec",
    r"\bcompile\b": "compile",
    r"\bkompilasi\b": "compile",
    r"\bformat\b": "format",
    r"\bformatki\b": "format",
    r"\brepr\b": "repr",
    r"\bascii\b": "ascii",
    r"\bchr\b": "chr",
    r"\bkarakter\b": "chr",
    r"\bord\b": "ord",
    r"\bnilai_karakter\b": "ord",
    r"\bhex\b": "hex",
    r"\bheksadesimal\b": "hex",
    r"\boct\b": "oct",
    r"\boktal\b": "oct",
    r"\bbin\b": "bin",
    r"\bbiner\b": "bin",
    r"\bslice\b": "slice",
    r"\biris\b": "slice",
    r"\bsuper\b": "super",
    r"\binduk\b": "super",
    # List/Dict/Set Methods
    r"\btambai\b": "append",
    r"\bburakne\b": "pop",
    r"\burutkanki\b": "sort",
    r"\bbalikidaptar\b": "reverse",
    r"\bsisipki\b": "insert",
    r"\bhapuski\b": "remove",
    r"\bbersihki\b": "clear",
    r"\bhitungki\b": "count",
    r"\bindexki\b": "index",
    r"\bextendki\b": "extend",
    r"\bcopyaki\b": "copy",
    r"\bsalinki\b": "copy",
    r"\bkeys\b": "keys",
    r"\bkunci\b": "keys",
    r"\bvalues\b": "values",
    r"\bnilai\b": "values",
    r"\bitems\b": "items",
    r"\bpasangan\b": "items",
    r"\bget\b": "get",
    r"\bambilki\b": "get",
    r"\bupdate\b": "update",
    r"\bperbaharui\b": "update",
    r"\bsetdefault\b": "setdefault",
    r"\bpopitem\b": "popitem",
    r"\badd\b": "add",
    r"\btambahki\b": "add",
    r"\bdiscard\b": "discard",
    r"\bbuangki\b": "discard",
    r"\bunion\b": "union",
    r"\bgabungan\b": "union",
    r"\bintersection\b": "intersection",
    r"\birisan\b": "intersection",
    r"\bdifference\b": "difference",
    r"\bselisih\b": "difference",
    r"\bsymmetric_difference\b": "symmetric_difference",
    r"\bselisih_simetris\b": "symmetric_difference",
    # String Methods
    r"\bsappai\b": "find",
    r"\bgantiki\b": "replace",
    r"\blompo\b": "upper",
    r"\bciddi\b": "lower",
    r"\bcapitalize\b": "capitalize",
    r"\bkapital\b": "capitalize",
    r"\btitle\b": "title",
    r"\bjudul\b": "title",
    r"\bstrip\b": "strip",
    r"\bpotongki\b": "strip",
    r"\blstrip\b": "lstrip",
    r"\brstrip\b": "rstrip",
    r"\bpecaki\b": "split",
    r"\bgabungki\b": "join",
    r"\bstartswith\b": "startswith",
    r"\bmulai_dengan\b": "startswith",
    r"\bendswith\b": "endswith",
    r"\bakhiri_dengan\b": "endswith",
    r"\bisalpha\b": "isalpha",
    r"\bhuruf_semua\b": "isalpha",
    r"\bisdigit\b": "isdigit",
    r"\bangka_semua\b": "isdigit",
    r"\bisalnum\b": "isalnum",
    r"\bhuruf_angka\b": "isalnum",
    r"\bisspace\b": "isspace",
    r"\bspasi_semua\b": "isspace",
    r"\bislower\b": "islower",
    r"\bciddi_semua\b": "islower",
    r"\bisupper\b": "isupper",
    r"\blompo_semua\b": "isupper",
    r"\bzfill\b": "zfill",
    r"\bisi_nol\b": "zfill",
    r"\bcenter\b": "center",
    r"\btengahki\b": "center",
    r"\bljust\b": "ljust",
    r"\bkiri_rata\b": "ljust",
    r"\brjust\b": "rjust",
    r"\bkanan_rata\b": "rjust",
    r"\bswapcase\b": "swapcase",
    r"\btukar_huruf\b": "swapcase",
    r"\bencode\b": "encode",
    r"\benkode\b": "encode",
    r"\bdecode\b": "decode",
    r"\bdekode\b": "decode",
    # Operators & Keywords
    r"\brilaleng\b": "in",
    r"\btaniarilaleng\b": "not in",
    r"\bsisamaya\b": "is",
    r"\btaniasisamaya\b": "is not",
    r"\bdan\b": "and",
    r"\batau\b": "or",
    r"\btania\b": "not",
    r"\bglobal\b": "global",
    r"\bmendunia\b": "global",
    r"\bnonlocal\b": "nonlocal",
    r"\btidak_lokal\b": "nonlocal",
    r"\bdel\b": "del",
    r"\bhapus\b": "del",
    r"\bwith\b": "with",
    r"\bdengan\b": "with",
}

# Reverse mapping: Python -> Sofinco
PYTHON_TO_SOFINCO = {
    "print": "paccerak",
    "input": "passuluak",
    "open": "bukka",
    "int": "bilanga",
    "str": "aksara",
    "float": "desimal",
    "list": "daptar",
    "tuple": "tupel",
    "dict": "peta",
    "set": "himpunan",
    "bool": "bolean",
    "True": "makanja",
    "False": "demakanja",
    "None": "taniaapa",
    "if": "nakko",
    "elif": "nakkopa",
    "else": "narekko",
    "for": "ulangi",
    "while": "sedding",
    "break": "tappai",
    "continue": "laoi",
    "pass": "lewati",
    "match": "pilih",
    "case": "kasus",
    "def": "pangngaseng",
    "return": "baliki",
    "lambda": "lambda",
    "class": "kelas",
    "yield": "yield",
    "async": "async",
    "await": "await",
    "try": "coba",
    "except": "nakkosala",
    "finally": "nakkosedding",
    "raise": "bangkitki",
    "assert": "kudu",
    "import": "impor",
    "from": "riboko",
    "as": "siaganga",
    "global": "global",
    "nonlocal": "nonlocal",
    "del": "del",
    "range": "jangka",
    "len": "carakna",
    "sum": "jumlahki",
    "min": "palingciddi",
    "max": "palinglompo",
    "sorted": "urutki",
    "reversed": "balikkidaptar",
    "enumerate": "enumerate",
    "zip": "zip",
    "map": "map",
    "filter": "filter",
    "all": "all",
    "any": "any",
    "abs": "abs",
    "round": "round",
    "pow": "pow",
    "type": "type",
    "dir": "dir",
    "vars": "vars",
    "help": "help",
    "eval": "eval",
    "exec": "exec",
    "compile": "compile",
    "format": "format",
    "chr": "chr",
    "ord": "ord",
    "hex": "hex",
    "oct": "oct",
    "bin": "bin",
    "slice": "slice",
    "super": "super",
    "append": "tambai",
    "pop": "burakne",
    "sort": "urutkanki",
    "reverse": "balikidaptar",
    "insert": "sisipki",
    "remove": "hapuski",
    "clear": "bersihki",
    "count": "hitungki",
    "index": "indexki",
    "extend": "extendki",
    "copy": "copyaki",
    "keys": "keys",
    "values": "values",
    "items": "items",
    "get": "get",
    "update": "update",
    "add": "add",
    "discard": "discard",
    "union": "union",
    "intersection": "intersection",
    "difference": "difference",
    "find": "sappai",
    "replace": "gantiki",
    "upper": "lompo",
    "lower": "ciddi",
    "split": "pecaki",
    "join": "gabungki",
    "strip": "strip",
    "capitalize": "capitalize",
    "title": "title",
    "startswith": "startswith",
    "endswith": "endswith",
    "isalpha": "isalpha",
    "isdigit": "isdigit",
    "isalnum": "isalnum",
    "isspace": "isspace",
    "islower": "islower",
    "isupper": "isupper",
    "in": "rilaleng",
    "not in": "taniarilaleng",
    "is": "sisamaya",
    "is not": "taniasisamaya",
    "and": "dan",
    "or": "atau",
    "not": "tania",
    "read": "baca",
    "write": "tulis",
    "close": "tutup",
    "readline": "bacabarisa",
    "readlines": "bacasemua",
    "__init__": "inisialisasi",
}


def convert_sofinco_to_python(sofinco_code: str) -> str:
    """Convert Sofinco code to Python code"""
    python_code = sofinco_code
    
    # Handle 'siaganga' context-sensitively first
    python_code = re.sub(r'\bnakkosala\s+(\w+)\s+siaganga\s+', r'except \1 as ', python_code)
    python_code = re.sub(r'\bimpor\s+(\S+)\s+siaganga\s+', r'import \1 as ', python_code)
    python_code = re.sub(r'\briboko\s+(\S+)\s+impor\s+(\S+)\s+siaganga\s+', r'from \1 import \2 as ', python_code)
    python_code = re.sub(r'\bsiaganga\s+(.+?)\s+siaganga\s+', r'with \1 as ', python_code)
    
    # Handle standalone keywords
    python_code = re.sub(r'\bnakkosala\b', 'except', python_code)
    python_code = re.sub(r'\bimpor\b', 'import', python_code)
    python_code = re.sub(r'\briboko\s+(\S+)\s+import\s+', r'from \1 import ', python_code)
    
    # Apply other keyword mappings
    for sofinco_keyword, python_keyword in KEYWORD_MAP.items():
        if any(skip in sofinco_keyword for skip in ['siaganga', 'nakkosala', 'impor', 'riboko']):
            continue
        python_code = re.sub(sofinco_keyword, python_keyword, python_code)
    
    python_code = re.sub(r"\bsebagai\b", "as", python_code)
    python_code = re.sub(r"\t", "    ", python_code)
    return python_code


def convert_python_to_sofinco(python_code: str) -> str:
    """Convert Python code to Sofinco code"""
    sofinco_code = python_code
    
    # Handle multi-word operators first
    sofinco_code = re.sub(r'\bnot\s+in\b', 'taniarilaleng', sofinco_code)
    sofinco_code = re.sub(r'\bis\s+not\b', 'taniasisamaya', sofinco_code)
    
    # Handle special patterns
    sofinco_code = re.sub(r'\bexcept\s+(\w+)\s+as\s+', r'nakkosala \1 siaganga ', sofinco_code)
    sofinco_code = re.sub(r'\bimport\s+(\S+)\s+as\s+', r'impor \1 siaganga ', sofinco_code)
    sofinco_code = re.sub(r'\bfrom\s+(\S+)\s+import\s+(\S+)\s+as\s+', r'riboko \1 impor \2 siaganga ', sofinco_code)
    sofinco_code = re.sub(r'\bwith\s+(.+?)\s+as\s+', r'siaganga \1 siaganga ', sofinco_code)
    
    # Handle single keywords
    exclude_keywords = ["not in", "is not", "as", "except", "import", "from", "with"]
    sorted_mappings = sorted(
        [(k, v) for k, v in PYTHON_TO_SOFINCO.items() if k not in exclude_keywords],
        key=lambda x: len(x[0]),
        reverse=True
    )
    
    for python_keyword, sofinco_keyword in sorted_mappings:
        pattern = r'\b' + re.escape(python_keyword) + r'\b'
        sofinco_code = re.sub(pattern, sofinco_keyword, sofinco_code)
    
    return sofinco_code


def run_sofinco_file(file_path: str, save_converted: bool = True) -> None:
    """Run Sofinco file"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")

    with open(file_path, "r", encoding="utf-8") as f:
        sofinco_code = f.read()

    python_code = convert_sofinco_to_python(sofinco_code)

    if save_converted:
        py_file_path = f"{file_path.rsplit('.', 1)[0]}.py"
        with open(py_file_path, "w", encoding="utf-8") as f:
            f.write(python_code)

    try:
        namespace = {"__builtins__": __builtins__, "__name__": "__main__"}
        exec(python_code, namespace)
    except SyntaxError as e:
        raise Exception(
            f"❌ Error sintaks di baris {e.lineno}: {e.text.strip() if e.text else 'N/A'}"
        ) from e
    except Exception as e:
        raise Exception(f"❌ Error eksekusi: {str(e)}") from e


def convert_py_file_to_sofinco(py_file_path: str, output_path: str | None = None) -> None:
    """Convert single Python file to Sofinco"""
    if not py_file_path.endswith(".py"):
        raise ValueError("❌ File harus memiliki ekstensi .py!")
    
    with open(py_file_path, "r", encoding="utf-8") as f:
        python_code = f.read()
    
    sofinco_code = convert_python_to_sofinco(python_code)
    
    if output_path is None:
        output_path = py_file_path.rsplit('.', 1)[0] + ".sofinco"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sofinco_code)
    
    print(f"✅ Converted: {py_file_path} -> {output_path}")


def convert_directory_to_sofinco(directory: str, recursive: bool = True) -> None:
    """Convert all Python files in directory to Sofinco"""
    path = Path(directory)
    
    if not path.exists():
        raise ValueError(f"❌ Direktori tidak ditemukan: {directory}")
    
    if not path.is_dir():
        raise ValueError(f"❌ Path bukan direktori: {directory}")
    
    pattern = "**/*.py" if recursive else "*.py"
    py_files = list(path.glob(pattern))
    
    if not py_files:
        print(f"⚠️  Tidak ada file .py ditemukan di {directory}")
        return
    
    print(f"🔄 Mengkonversi {len(py_files)} file Python ke Sofinco...")
    
    for py_file in py_files:
        try:
            output_path = str(py_file).rsplit('.', 1)[0] + ".sofinco"
            convert_py_file_to_sofinco(str(py_file), output_path)
        except Exception as e:
            print(f"❌ Error converting {py_file}: {e}")
    
    print(f"\n✅ Selesai! {len(py_files)} file telah dikonversi.")


def convert_to_sofinco_cli(path: str, recursive: bool = True) -> None:
    """CLI entry point for Python to Sofinco conversion"""
    path_obj = Path(path)
    
    if path_obj.is_file():
        convert_py_file_to_sofinco(path)
    elif path_obj.is_dir():
        convert_directory_to_sofinco(path, recursive)
    else:
        raise ValueError(f"❌ Path tidak valid: {path}")


def decompile_sofinco_file(sofinco_file: str, output_file: str | None = None) -> None:
    """Decompile Sofinco file to Python file"""
    if not sofinco_file.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(sofinco_file, "r", encoding="utf-8") as f:
        sofinco_code = f.read()
    
    python_code = convert_sofinco_to_python(sofinco_code)
    
    if output_file is None:
        output_file = sofinco_file.rsplit('.', 1)[0] + ".py"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(python_code)
    
    print(f"✅ Decompiled: {sofinco_file} -> {output_file}")


def check_syntax(file_path: str) -> bool:
    """Check Sofinco file syntax without executing"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        sofinco_code = f.read()
    
    python_code = convert_sofinco_to_python(sofinco_code)
    
    try:
        ast.parse(python_code)
        print(f"✅ Syntax valid: {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error di baris {e.lineno}: {e.msg}")
        if e.text:
            print(f"   {e.text.strip()}")
            if e.offset:
                print(f"   {' ' * (e.offset - 1)}^")
        return False


def format_sofinco_code(code: str, indent_size: int = 4) -> str:
    """Format Sofinco code with proper indentation"""
    lines = code.split('\n')
    formatted = []
    indent_level = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            formatted.append('')
            continue
        
        # Decrease indent for closing keywords (but not if it's the start of a new block)
        if stripped.startswith(('narekko', 'naiya', 'nakkopa', 'wennangpa', 'nakkosala', 'nakkosedding')):
            indent_level = max(0, indent_level - 1)
        
        # Add formatted line with current indentation
        formatted.append(' ' * (indent_level * indent_size) + stripped)
        
        # Increase indent after opening keywords (lines ending with :)
        if stripped.endswith(':'):
            indent_level += 1
    
    return '\n'.join(formatted)


def format_sofinco_file(file_path: str, indent_size: int = 4, in_place: bool = False) -> None:
    """Format Sofinco file"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    formatted = format_sofinco_code(code, indent_size)
    
    if in_place:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"✅ Formatted (in-place): {file_path}")
    else:
        output_file = file_path.rsplit('.', 1)[0] + ".formatted.sofinco"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"✅ Formatted: {file_path} -> {output_file}")


def show_ast(file_path: str, output_format: str = "tree") -> None:
    """Show AST of Sofinco file"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        sofinco_code = f.read()
    
    python_code = convert_sofinco_to_python(sofinco_code)
    
    try:
        tree = ast.parse(python_code)
        
        if output_format == "json":
            ast_dict = ast_to_dict(tree)
            print(json.dumps(ast_dict, indent=2, ensure_ascii=False, default=str))
        else:
            print(ast.dump(tree, indent=2))
    except SyntaxError as e:
        print(f"❌ Syntax error: {e.msg} at line {e.lineno}")


def ast_to_dict(node: Any) -> Any:
    """Convert AST node to dictionary"""
    if isinstance(node, ast.AST):
        result: Dict[str, Any] = {"_type": node.__class__.__name__}
        for field, value in ast.iter_fields(node):
            result[field] = ast_to_dict(value)
        return result
    elif isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    else:
        return node


def repl_mode():
    """Interactive REPL mode for Sofinco"""
    print("🔥 Sofinco REPL v2.1.0")
    print("Ketik 'keluar' atau 'exit' untuk keluar")
    print("Ketik 'bantuan' atau 'help' untuk bantuan\n")
    
    namespace = {"__builtins__": __builtins__, "__name__": "__main__"}
    history = []
    
    while True:
        try:
            line = input(">>> ")
            
            if line.strip() in ['keluar', 'exit', 'quit']:
                print("Sampai jumpa! 👋")
                break
            
            if line.strip() in ['bantuan', 'help']:
                print("\n📚 Bantuan Sofinco REPL:")
                print("  - Tulis kode Sofinco dan tekan Enter")
                print("  - Gunakan 'keluar' atau 'exit' untuk keluar")
                print("  - Gunakan 'riwayat' untuk melihat history")
                print("  - Gunakan 'bersih' untuk clear namespace\n")
                continue
            
            if line.strip() == 'riwayat':
                print("\n📜 History:")
                for i, cmd in enumerate(history, 1):
                    print(f"  {i}. {cmd}")
                print()
                continue
            
            if line.strip() == 'bersih':
                namespace = {"__builtins__": __builtins__, "__name__": "__main__"}
                print("✅ Namespace dibersihkan\n")
                continue
            
            if not line.strip():
                continue
            
            history.append(line)
            python_code = convert_sofinco_to_python(line)
            
            try:
                # Try to evaluate as expression first
                result = eval(python_code, namespace)
                if result is not None:
                    print(result)
            except SyntaxError:
                # If not expression, execute as statement
                exec(python_code, namespace)
            
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
            continue
        except EOFError:
            print("\nSampai jumpa! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def show_version():
    """Show Sofinco version"""
    try:
        from . import __version__
        print(f"Sofinco v{__version__}")
    except ImportError:
        print("Sofinco v3.0.0")
    print("Bahasa Pemrograman Bahasa Bugis-Makassar")
    print("https://github.com/levouinse/sofinco-language")


def install_package(package_name: str):
    """Install Python package using pip"""
    print(f"📦 Installing package: {package_name}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Package '{package_name}' installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install package: {e}")


def list_packages():
    """List installed Python packages"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to list packages: {e}")


def profile_sofinco_file(file_path: str, output_file: str | None = None):
    """Profile Sofinco program execution"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        sofinco_code = f.read()
    
    python_code = convert_sofinco_to_python(sofinco_code)
    
    profiler = cProfile.Profile()
    namespace = {"__builtins__": __builtins__, "__name__": "__main__"}
    
    print(f"🔍 Profiling: {file_path}\n")
    
    try:
        profiler.enable()
        exec(python_code, namespace)
        profiler.disable()
        
        s = StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(30)
        
        result = s.getvalue()
        print(result)
        
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"\n✅ Profile saved to: {output_file}")
    
    except Exception as e:
        print(f"❌ Error during profiling: {e}")


def lint_sofinco_file(file_path: str):
    """Lint Sofinco file for common issues"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        sofinco_code = f.read()
    
    issues = []
    lines = sofinco_code.split('\n')
    
    # Check for common issues
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Check for mixed indentation
        if line and not line.lstrip() == line:
            if '\t' in line and ' ' in line[:len(line) - len(line.lstrip())]:
                issues.append(f"Line {i}: Mixed tabs and spaces in indentation")
        
        # Check for trailing whitespace
        if line.endswith(' ') or line.endswith('\t'):
            issues.append(f"Line {i}: Trailing whitespace")
        
        # Check for missing colon after keywords
        if stripped.startswith(('nakko ', 'nakkopa ', 'narekko', 'ulangi ', 'sedding ', 'pangngaseng ', 'kelas ', 'coba', 'nakkosala')):
            if not stripped.endswith(':'):
                issues.append(f"Line {i}: Missing colon after keyword")
    
    # Check Python syntax
    python_code = convert_sofinco_to_python(sofinco_code)
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        issues.append(f"Line {e.lineno}: Syntax error - {e.msg}")
    
    if issues:
        print(f"⚠️  Found {len(issues)} issue(s) in {file_path}:\n")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print(f"✅ No issues found in {file_path}")
        return True


def benchmark_sofinco_file(file_path: str, iterations: int = 100):
    """Benchmark Sofinco program execution"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        sofinco_code = f.read()
    
    python_code = convert_sofinco_to_python(sofinco_code)
    namespace = {"__builtins__": __builtins__, "__name__": "__main__"}
    
    print(f"⏱️  Benchmarking: {file_path} ({iterations} iterations)\n")
    
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        try:
            exec(python_code, namespace.copy())
            end = time.perf_counter()
            times.append(end - start)
        except Exception as e:
            print(f"❌ Error during iteration {i+1}: {e}")
            return
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"📊 Results:")
    print(f"  • Average time: {avg_time*1000:.4f} ms")
    print(f"  • Min time: {min_time*1000:.4f} ms")
    print(f"  • Max time: {max_time*1000:.4f} ms")
    print(f"  • Total time: {sum(times):.4f} s")


def docs_keyword(keyword: str | None = None):
    """Show documentation for Sofinco keywords"""
    docs = {
        "paccerak": "Cetak output ke layar (Python: print)",
        "passuluak": "Terima input dari user (Python: input)",
        "nakko": "Kondisi if (Python: if)",
        "nakkopa": "Kondisi elif (Python: elif)",
        "narekko": "Kondisi else (Python: else)",
        "ulangi": "Loop for (Python: for)",
        "sedding": "Loop while (Python: while)",
        "pangngaseng": "Definisi fungsi (Python: def)",
        "baliki": "Return nilai (Python: return)",
        "kelas": "Definisi class (Python: class)",
        "coba": "Try exception (Python: try)",
        "nakkosala": "Except exception (Python: except)",
        "nakkosedding": "Finally block (Python: finally)",
        "impor": "Import module (Python: import)",
        "riboko": "From module (Python: from)",
        "siaganga": "As alias (Python: as)",
        "bilanga": "Integer (Python: int)",
        "aksara": "String (Python: str)",
        "desimal": "Float (Python: float)",
        "daptar": "List (Python: list)",
        "peta": "Dictionary (Python: dict)",
        "himpunan": "Set (Python: set)",
        "makanja": "True (Python: True)",
        "demakanja": "False (Python: False)",
        "taniaapa": "None (Python: None)",
        "rilaleng": "In operator (Python: in)",
        "dan": "And operator (Python: and)",
        "atau": "Or operator (Python: or)",
        "tania": "Not operator (Python: not)",
        "jangka": "Range function (Python: range)",
        "carakna": "Length function (Python: len)",
        "tambai": "Append to list (Python: append)",
        "burakne": "Pop from list (Python: pop)",
        "urutkanki": "Sort list (Python: sort)",
        "bukka": "Open file (Python: open)",
        "baca": "Read file (Python: read)",
        "tulis": "Write file (Python: write)",
    }
    
    if keyword is None:
        print("📚 Dokumentasi Keyword Sofinco\n")
        print("Gunakan: sofinco docs <keyword> untuk detail\n")
        print("Keyword tersedia:")
        for kw in sorted(docs.keys()):
            print(f"  • {kw}")
    else:
        if keyword in docs:
            print(f"📖 {keyword}: {docs[keyword]}")
        else:
            print(f"❌ Keyword '{keyword}' tidak ditemukan")
            print("Gunakan 'sofinco docs' untuk melihat semua keyword")


def transpile_to_js(file_path: str, output_file: str | None = None):
    """Experimental: Transpile Sofinco to JavaScript"""
    if not file_path.endswith(".sofinco"):
        raise ValueError("❌ File harus memiliki ekstensi .sofinco!")
    
    with open(file_path, "r", encoding="utf-8") as f:
        sofinco_code = f.read()
    
    python_code = convert_sofinco_to_python(sofinco_code)
    
    # Basic Python to JS conversion (very simplified)
    js_code = python_code
    js_code = js_code.replace("print(", "console.log(")
    js_code = js_code.replace("def ", "function ")
    js_code = js_code.replace("True", "true")
    js_code = js_code.replace("False", "false")
    js_code = js_code.replace("None", "null")
    js_code = js_code.replace("elif", "else if")
    
    if output_file is None:
        output_file = file_path.rsplit('.', 1)[0] + ".js"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(js_code)
    
    print(f"⚠️  Experimental feature: Basic transpilation only")
    print(f"✅ Transpiled: {file_path} -> {output_file}")


def main():
    """Main CLI function with all commands"""
    import argparse

    # Check for backward compatibility: sofinco file.sofinco
    if len(sys.argv) > 1 and sys.argv[1].endswith(".sofinco") and sys.argv[1] not in ["run", "convert", "decompile", "check", "format", "ast", "repl", "version", "install", "list", "profile", "lint", "benchmark", "docs", "transpile"]:
        try:
            save_converted = "--nosv" not in sys.argv
            run_sofinco_file(sys.argv[1], save_converted)
            sys.exit(0)
        except Exception as e:
            print(f"\n{str(e)}", file=sys.stderr)
            sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Sofinco - Bahasa Pemrograman Bahasa Bugis-Makassar Berbasis Python",
        usage="sofinco <command> [options]",
        epilog="Contoh: sofinco run program.sofinco | sofinco convert file.py | sofinco repl",
    )
    
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show version information"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run Sofinco program")
    run_parser.add_argument("file", help="Path ke file program Sofinco (ekstensi .sofinco)")
    run_parser.add_argument(
        "--nosv",
        action="store_false",
        dest="save_converted",
        help="Jangan menyimpan file Python hasil konversi",
    )
    
    # Convert command (Python to Sofinco)
    convert_parser = subparsers.add_parser("convert", help="Convert Python to Sofinco")
    convert_parser.add_argument("path", help="Path ke file .py atau direktori")
    convert_parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Jangan convert secara rekursif (hanya untuk direktori)",
    )
    
    # Decompile command (Sofinco to Python)
    decompile_parser = subparsers.add_parser("decompile", help="Decompile Sofinco to Python")
    decompile_parser.add_argument("file", help="Path ke file .sofinco")
    decompile_parser.add_argument(
        "-o", "--output",
        help="Output file path (default: same name with .py extension)"
    )
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check Sofinco syntax without executing")
    check_parser.add_argument("file", help="Path ke file .sofinco")
    
    # Format command
    format_parser = subparsers.add_parser("format", help="Format Sofinco code")
    format_parser.add_argument("file", help="Path ke file .sofinco")
    format_parser.add_argument(
        "-i", "--in-place",
        action="store_true",
        help="Format file in-place"
    )
    format_parser.add_argument(
        "--indent",
        type=int,
        default=4,
        help="Indentation size (default: 4)"
    )
    
    # AST command
    ast_parser = subparsers.add_parser("ast", help="Show Abstract Syntax Tree")
    ast_parser.add_argument("file", help="Path ke file .sofinco")
    ast_parser.add_argument(
        "--format",
        choices=["tree", "json"],
        default="tree",
        help="Output format (default: tree)"
    )
    
    # REPL command
    repl_parser = subparsers.add_parser("repl", help="Start interactive REPL")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install Python package")
    install_parser.add_argument("package", help="Package name to install")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List installed packages")
    
    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Profile Sofinco program execution")
    profile_parser.add_argument("file", help="Path ke file .sofinco")
    profile_parser.add_argument(
        "-o", "--output",
        help="Output file for profile results"
    )
    
    # Lint command
    lint_parser = subparsers.add_parser("lint", help="Lint Sofinco file for issues")
    lint_parser.add_argument("file", help="Path ke file .sofinco")
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark Sofinco program")
    benchmark_parser.add_argument("file", help="Path ke file .sofinco")
    benchmark_parser.add_argument(
        "-n", "--iterations",
        type=int,
        default=100,
        help="Number of iterations (default: 100)"
    )
    
    # Docs command
    docs_parser = subparsers.add_parser("docs", help="Show keyword documentation")
    docs_parser.add_argument("keyword", nargs="?", help="Keyword to show docs for")
    
    # Transpile command
    transpile_parser = subparsers.add_parser("transpile", help="Transpile Sofinco to JavaScript")
    transpile_parser.add_argument("file", help="Path ke file .sofinco")
    transpile_parser.add_argument(
        "-o", "--output",
        help="Output JavaScript file"
    )
    
    args = parser.parse_args()
    
    if args.version:
        show_version()
        sys.exit(0)
    
    try:
        if args.command == "run":
            run_sofinco_file(args.file, args.save_converted)
        elif args.command == "convert":
            convert_to_sofinco_cli(args.path, args.recursive)
        elif args.command == "decompile":
            decompile_sofinco_file(args.file, args.output)
        elif args.command == "check":
            if not check_syntax(args.file):
                sys.exit(1)
        elif args.command == "format":
            format_sofinco_file(args.file, args.indent, args.in_place)
        elif args.command == "ast":
            show_ast(args.file, args.format)
        elif args.command == "repl":
            repl_mode()
        elif args.command == "version":
            show_version()
        elif args.command == "install":
            install_package(args.package)
        elif args.command == "list":
            list_packages()
        elif args.command == "profile":
            profile_sofinco_file(args.file, args.output)
        elif args.command == "lint":
            if not lint_sofinco_file(args.file):
                sys.exit(1)
        elif args.command == "benchmark":
            benchmark_sofinco_file(args.file, args.iterations)
        elif args.command == "docs":
            docs_keyword(args.keyword)
        elif args.command == "transpile":
            transpile_to_js(args.file, args.output)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"\n{str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()