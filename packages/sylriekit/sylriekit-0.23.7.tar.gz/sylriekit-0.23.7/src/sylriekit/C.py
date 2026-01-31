import functools
import hashlib
import inspect
import json
import shutil
import subprocess
import textwrap
import warnings
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

if os.getenv("SHOW_SYLRIEKIT_LANG_WARNINGS", "False") == "True":
    def _check_gcc_available() -> bool:
        common_paths = [
            r"C:\msys64\ucrt64\bin\gcc.exe",
            r"C:\msys64\mingw64\bin\gcc.exe",
            r"C:\msys64\mingw32\bin\gcc.exe",
            r"C:\mingw64\bin\gcc.exe",
            r"C:\mingw\bin\gcc.exe",
        ]

        for path in common_paths:
            if Path(path).exists():
                return True

        try:
            result = subprocess.run(
                ["gcc", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False


    if not _check_gcc_available():
        warnings.warn(
            "GCC compiler not found. C language support will not work.\n"
            "To install on Windows:\n"
            "  1. Install MSYS2: winget install --id MSYS2.MSYS2\n"
            "  2. Open MSYS2 UCRT64 terminal and run: pacman -S mingw-w64-ucrt-x86_64-gcc\n"
            "  3. Add C:\\msys64\\ucrt64\\bin to your system PATH",
            RuntimeWarning
        )


class C:
    TEMP_DIR = "temp"
    INDEX_FILE = "index.json"
    EXE_EXTENSION = ".exe"
    C_MAIN_FILE = "main.c"
    BUILD_BIN = "gcc"
    HASH_LENGTH = 12
    JSON_INDENT = 2

    CACHE_DIR = "__ccache__"
    BUILD_TIMEOUT = 60
    GCC_PATH = r"C:\msys64\ucrt64\bin\gcc.exe"

    _head_code: str = ""
    _keep_cached: bool = False
    _auto_warm: bool = False
    _index: Dict[str, Dict[str, Any]] = {}
    _initialized: bool = False

    @classmethod
    def load_config(cls, config: Dict[str, Any]) -> None:
        tool_config = config.get("C", {})
        cls.CACHE_DIR = tool_config.get("CACHE_DIR", cls.CACHE_DIR)
        cls.BUILD_TIMEOUT = tool_config.get("BUILD_TIMEOUT", cls.BUILD_TIMEOUT)
        cls.GCC_PATH = tool_config.get("GCC_PATH", cls.GCC_PATH)

        if "keep_cached" in tool_config:
            cls._keep_cached = tool_config["keep_cached"]
        if "head_code" in tool_config:
            cls._head_code = tool_config["head_code"]

    @classmethod
    def keep_cached(cls, keep: bool = True) -> None:
        cls._keep_cached = keep

    @classmethod
    def auto_warm(cls, warm: bool = True) -> None:
        cls._auto_warm = warm

    @classmethod
    def set_head(cls, code: str) -> None:
        cls._head_code = code.strip()

    @classmethod
    def get_head(cls) -> str:
        return cls._head_code

    @classmethod
    def clear_head(cls) -> None:
        cls._head_code = ""

    @classmethod
    def load(cls, file_path: Optional[str] = None, use_head: bool = True, timeout: Optional[float] = None) -> Callable:
        def decorator(func: Callable) -> Callable:
            if file_path:
                source_file = Path(file_path)
                if not source_file.exists():
                    raise FileNotFoundError(f"File '{file_path}' not found.")
                c_code = source_file.read_text(encoding="utf-8").strip()
            else:
                docstring = func.__doc__
                if not docstring:
                    raise ValueError(f"Function '{func.__name__}' must have a docstring containing C code.")
                c_code = textwrap.dedent(docstring).strip()

            build_id = func.__name__
            sig = inspect.signature(func)
            args_schema = list(sig.parameters.keys())
            type_hints = {
                name: param.annotation
                for name, param in sig.parameters.items()
                if param.annotation != inspect.Parameter.empty
            }

            full_code = cls._generate_main_wrapper(c_code, args_schema, type_hints, use_head=use_head)
            cls.build(full_code, build_id, args_schema)

            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> subprocess.CompletedProcess:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                args_dict = dict(bound.arguments)
                return cls.run(build_id, args_dict, timeout=timeout)

            return wrapper

        return decorator

    @classmethod
    def build(cls, code: str, build_id: str, args_schema: Optional[List[str]] = None) -> str:
        if not code or not code.strip():
            raise ValueError("Code cannot be empty.")
        if not build_id or not build_id.strip():
            raise ValueError("Build ID cannot be empty.")

        cls._initialize()

        build_id = build_id.strip()
        args_schema = args_schema or []
        code_hash = cls._compute_code_hash(code, args_schema)

        if build_id in cls._index:
            cached = cls._index[build_id]
            exe_path = Path(cls.CACHE_DIR) / cached["exe_name"]
            if cached.get("code_hash") == code_hash and exe_path.exists():
                return build_id

        exe_name = cls._generate_exe_name(build_id)
        full_code = cls._get_full_code(code, args_schema)

        temp_dir = Path(cls.CACHE_DIR) / cls.TEMP_DIR / build_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            main_path = temp_dir / cls.C_MAIN_FILE
            main_path.write_text(full_code, encoding="utf-8")

            exe_path = Path(cls.CACHE_DIR) / exe_name

            gcc_cmd, gcc_env = cls._find_gcc()
            cmd = [gcc_cmd, "-O3", "-o", str(exe_path.resolve()), str(main_path.resolve())]

            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(temp_dir),
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=cls.BUILD_TIMEOUT,
                    env=gcc_env
                )
            except FileNotFoundError as error:
                raise FileNotFoundError("GCC is not available in PATH. Please install MinGW-w64 or MSYS2.") from error
            except subprocess.TimeoutExpired as error:
                raise TimeoutError("C build exceeded the configured timeout.") from error

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                raise RuntimeError(f"C build failed: {error_msg}")

            cls._index[build_id] = {
                "exe_name": exe_name,
                "code_hash": code_hash,
                "args_schema": args_schema,
                "build_time": str(Path(exe_path).stat().st_mtime) if exe_path.exists() else None
            }
            cls._save_index()

            if cls._auto_warm and exe_path.exists():
                try:
                    subprocess.run(
                        [str(exe_path.resolve()), "__warmup__"],
                        capture_output=True,
                        timeout=5
                    )
                except (subprocess.TimeoutExpired, OSError):
                    pass

            return build_id

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


    @classmethod
    def run(
        cls,
        build_id: str,
        args: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> subprocess.CompletedProcess:
        cls._initialize()

        if build_id not in cls._index:
            raise ValueError(f"Build ID '{build_id}' not found in cache.")

        cached = cls._index[build_id]
        exe_path = Path(cls.CACHE_DIR) / cached["exe_name"]

        if not exe_path.exists():
            raise FileNotFoundError(f"Executable for '{build_id}' not found.")

        args_schema = cached.get("args_schema", [])
        cmd_args = cls._build_cmd_args(args_schema, args or {})
        cmd = [str(exe_path.resolve())] + cmd_args

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    @classmethod
    def exists(cls, build_id: str) -> bool:
        cls._initialize()

        if build_id not in cls._index:
            return False

        cached = cls._index[build_id]
        exe_path = Path(cls.CACHE_DIR) / cached["exe_name"]
        return exe_path.exists()

    @classmethod
    def remove(cls, build_id: str) -> bool:
        cls._initialize()

        if build_id not in cls._index:
            return False

        cached = cls._index[build_id]
        exe_path = Path(cls.CACHE_DIR) / cached["exe_name"]

        if exe_path.exists():
            exe_path.unlink()

        del cls._index[build_id]
        cls._save_index()
        return True

    @classmethod
    def clear_cache(cls) -> None:
        cache_path = Path(cls.CACHE_DIR)
        if cache_path.exists():
            shutil.rmtree(cache_path)
        cls._index = {}
        cls._initialized = False

    @classmethod
    def list_builds(cls) -> List[str]:
        cls._initialize()
        return list(cls._index.keys())

    @classmethod
    def get_build_info(cls, build_id: str) -> Optional[Dict[str, Any]]:
        cls._initialize()

        if build_id not in cls._index:
            return None

        cached = cls._index[build_id]
        exe_path = Path(cls.CACHE_DIR) / cached["exe_name"]

        return {
            "build_id": build_id,
            "exe_name": cached["exe_name"],
            "exe_path": str(exe_path.resolve()) if exe_path.exists() else None,
            "exists": exe_path.exists(),
            "code_hash": cached.get("code_hash"),
            "args_schema": cached.get("args_schema", []),
            "build_time": cached.get("build_time")
        }

    ### PRIVATE UTILITIES START
    @classmethod
    def _find_gcc(cls) -> tuple:
        import os as _os

        common_paths = [
            r"C:\msys64\ucrt64\bin\gcc.exe",
            r"C:\msys64\mingw64\bin\gcc.exe",
            r"C:\msys64\mingw32\bin\gcc.exe",
            r"C:\mingw64\bin\gcc.exe",
            r"C:\mingw\bin\gcc.exe",
        ]

        if Path(cls.GCC_PATH).exists():
            gcc_dir = str(Path(cls.GCC_PATH).parent)
            env = _os.environ.copy()
            env["PATH"] = gcc_dir + _os.pathsep + env.get("PATH", "")
            return cls.GCC_PATH, env

        for path in common_paths:
            if Path(path).exists():
                gcc_dir = str(Path(path).parent)
                env = _os.environ.copy()
                env["PATH"] = gcc_dir + _os.pathsep + env.get("PATH", "")
                return path, env

        try:
            result = subprocess.run(["gcc", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return "gcc", None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        raise FileNotFoundError(
            "GCC not found. Please install MSYS2 and run: pacman -S mingw-w64-ucrt-x86_64-gcc\n"
            "Then add C:\\msys64\\ucrt64\\bin to your system PATH"
        )

    @classmethod
    def _generate_main_wrapper(cls, c_code: str, args_schema: List[str], type_hints: Dict[str, Any], use_head: bool = True) -> str:
        c_types = {name: cls._python_type_to_c(type_hints.get(name)) for name in args_schema}

        head_includes, head_code_without_includes = cls._extract_head_includes() if use_head else (set(), "")

        required_includes = {"stdio.h", "stdlib.h", "string.h"}
        if args_schema:
            required_includes.add("string.h")

        all_includes = required_includes | head_includes

        var_declarations = []
        parsing_code = []

        for i, name in enumerate(args_schema):
            c_type = c_types[name]
            parsing_code.append(cls._generate_typed_parse_code(name, i + 1, c_type))

        include_block = "\n".join([f'#include <{inc}>' for inc in sorted(all_includes)])

        parse_block = "\n".join(parsing_code) if parsing_code else ""

        warmup_check = '''    // Warmup check - exit immediately if this is a warmup run
    if (argc > 1 && strcmp(argv[1], "__warmup__") == 0) {
        return 0;
    }'''

        parts = [include_block, ""]
        if head_code_without_includes:
            parts.append(head_code_without_includes)
            parts.append("")
        parts.append("int main(int argc, char *argv[]) {")
        parts.append(warmup_check)
        if parse_block:
            parts.append(parse_block)
        parts.append(textwrap.indent(c_code, "    "))
        parts.append("    return 0;")
        parts.append("}")

        full_code = "\n".join(parts)
        return full_code

    @classmethod
    def _extract_head_includes(cls) -> tuple:
        includes = set()
        remaining_code = ""

        if not cls._head_code:
            return includes, remaining_code

        head = cls._head_code
        lines = head.split("\n")
        non_include_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#include"):
                if '<' in stripped and '>' in stripped:
                    start = stripped.find('<') + 1
                    end = stripped.find('>')
                    includes.add(stripped[start:end])
                elif '"' in stripped:
                    non_include_lines.append(line)
            else:
                non_include_lines.append(line)

        remaining_code = "\n".join(non_include_lines).strip()
        return includes, remaining_code

    @classmethod
    def _generate_typed_parse_code(cls, arg_name: str, arg_index: int, c_type: str) -> str:
        if c_type == "int":
            return f"    int {arg_name} = (argc > {arg_index}) ? atoi(argv[{arg_index}]) : 0;"
        elif c_type == "long":
            return f"    long {arg_name} = (argc > {arg_index}) ? atol(argv[{arg_index}]) : 0;"
        elif c_type == "long long":
            return f"    long long {arg_name} = (argc > {arg_index}) ? atoll(argv[{arg_index}]) : 0;"
        elif c_type == "double":
            return f"    double {arg_name} = (argc > {arg_index}) ? atof(argv[{arg_index}]) : 0.0;"
        elif c_type == "float":
            return f"    float {arg_name} = (argc > {arg_index}) ? (float)atof(argv[{arg_index}]) : 0.0f;"
        elif c_type == "char*":
            return f'    char* {arg_name} = (argc > {arg_index}) ? argv[{arg_index}] : "";'
        else:
            return f'    char* {arg_name} = (argc > {arg_index}) ? argv[{arg_index}] : "";'

    @classmethod
    def _python_type_to_c(cls, py_type: Any) -> str:
        if py_type is None:
            return "char*"

        type_map = {
            int: "long long",
            float: "double",
            str: "char*",
            bool: "int",
        }

        if py_type in type_map:
            return type_map[py_type]

        type_name = getattr(py_type, "__name__", str(py_type))
        return type_map.get(type_name, "char*")

    @classmethod
    def _initialize(cls) -> None:
        if cls._initialized:
            return

        cache_path = Path(cls.CACHE_DIR)

        if not cls._keep_cached and cache_path.exists():
            shutil.rmtree(cache_path)

        cache_path.mkdir(parents=True, exist_ok=True)
        (cache_path / cls.TEMP_DIR).mkdir(parents=True, exist_ok=True)

        cls._load_index()
        cls._initialized = True

    @classmethod
    def _load_index(cls) -> None:
        index_path = Path(cls.CACHE_DIR) / cls.INDEX_FILE
        if index_path.exists():
            try:
                content = index_path.read_text(encoding="utf-8")
                cls._index = json.loads(content)
            except (json.JSONDecodeError, IOError):
                cls._index = {}
        else:
            cls._index = {}

    @classmethod
    def _save_index(cls) -> None:
        index_path = Path(cls.CACHE_DIR) / cls.INDEX_FILE
        content = json.dumps(cls._index, indent=cls.JSON_INDENT)
        index_path.write_text(content, encoding="utf-8")

    @classmethod
    def _generate_exe_name(cls, build_id: str) -> str:
        hash_val = hashlib.md5(build_id.encode()).hexdigest()[:cls.HASH_LENGTH]
        return f"{hash_val}{cls.EXE_EXTENSION}"

    @classmethod
    def _get_full_code(cls, code: str, args_schema: List[str]) -> str:
        if "int main(" in code or "void main(" in code:
            return code

        if cls._head_code:
            code = f"{cls._head_code}\n\n{code}"

        if not args_schema:
            return code

        return cls._inject_args_parsing(code, args_schema)

    @classmethod
    def _inject_args_parsing(cls, code: str, args_schema: List[str]) -> str:
        parsing_code = []

        for i, arg_name in enumerate(args_schema):
            arg_index = i + 1
            parsing_code.append(f'    char* {arg_name} = (argc > {arg_index}) ? argv[{arg_index}] : "";')

        injection = "\n".join(parsing_code)

        if "int main(" in code or "void main(" in code:
            main_start = code.find("main(")
            brace_pos = code.find("{", main_start)
            if brace_pos != -1:
                return code[:brace_pos + 1] + "\n" + injection + code[brace_pos + 1:]

        return code

    @classmethod
    def _compute_code_hash(cls, code: str, args_schema: List[str]) -> str:
        full_code = cls._get_full_code(code, args_schema)
        schema_str = json.dumps(args_schema, sort_keys=True)
        combined = f"{full_code}\n{schema_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    @classmethod
    def _build_cmd_args(cls, args_schema: List[str], args: Dict[str, Any]) -> List[str]:
        if not args_schema:
            return []

        cmd_args = []
        for arg_name in args_schema:
            if arg_name not in args:
                raise ValueError(f"Missing required argument: '{arg_name}'")
            value = args[arg_name]
            if isinstance(value, bool):
                cmd_args.append("1" if value else "0")
            else:
                cmd_args.append(str(value))

        return cmd_args
    ### PRIVATE UTILITIES END

