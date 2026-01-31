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
    def _check_nim_available() -> bool:
        try:
            result = subprocess.run(
                ["nim", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False


    if not _check_nim_available():
        warnings.warn(
            "Nim compiler not found. Nim language support will not work.\n"
            "To install on Windows:\n"
            "  Download from https://nim-lang.org/install.html\n"
            "  Or use: winget install --id nim-lang.nim\n"
            "  Or use choosenim: https://github.com/dom96/choosenim",
            RuntimeWarning
        )


class Nim:
    TEMP_DIR = "temp"
    INDEX_FILE = "index.json"
    EXE_EXTENSION = ".exe"
    NIM_MAIN_FILE = "main.nim"
    BUILD_BIN = "nim"
    HASH_LENGTH = 12
    JSON_INDENT = 2

    CACHE_DIR = "__nimcache__"
    BUILD_TIMEOUT = 120

    _head_code: str = ""
    _keep_cached: bool = False
    _auto_warm: bool = False
    _index: Dict[str, Dict[str, Any]] = {}
    _initialized: bool = False

    @classmethod
    def load_config(cls, config: Dict[str, Any]) -> None:
        tool_config = config.get("Nim", {})
        cls.CACHE_DIR = tool_config.get("CACHE_DIR", cls.CACHE_DIR)
        cls.BUILD_TIMEOUT = tool_config.get("BUILD_TIMEOUT", cls.BUILD_TIMEOUT)

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
                nim_code = source_file.read_text(encoding="utf-8").strip()
            else:
                docstring = func.__doc__
                if not docstring:
                    raise ValueError(f"Function '{func.__name__}' must have a docstring containing Nim code.")
                nim_code = textwrap.dedent(docstring).strip()

            build_id = func.__name__
            sig = inspect.signature(func)
            args_schema = list(sig.parameters.keys())
            type_hints = {
                name: param.annotation
                for name, param in sig.parameters.items()
                if param.annotation != inspect.Parameter.empty
            }

            full_code = cls._generate_main_wrapper(nim_code, args_schema, type_hints, use_head=use_head)
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
            main_path = temp_dir / cls.NIM_MAIN_FILE
            main_path.write_text(full_code, encoding="utf-8")

            exe_path = Path(cls.CACHE_DIR) / exe_name

            cmd = [
                cls.BUILD_BIN, "c",
                "-d:release",
                "--opt:speed",
                "--hints:off",
                "--warnings:off",
                f"-o:{str(exe_path.resolve())}",
                str(main_path.resolve())
            ]

            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(temp_dir),
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=cls.BUILD_TIMEOUT
                )
            except FileNotFoundError as error:
                raise FileNotFoundError("Nim compiler is not available in PATH.") from error
            except subprocess.TimeoutExpired as error:
                raise TimeoutError("Nim build exceeded the configured timeout.") from error

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                raise RuntimeError(f"Nim build failed: {error_msg}")

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
    def _generate_main_wrapper(cls, nim_code: str, args_schema: List[str], type_hints: Dict[str, Any], use_head: bool = True) -> str:
        nim_types = {name: cls._python_type_to_nim(type_hints.get(name)) for name in args_schema}

        head_imports, head_code_without_imports = cls._extract_head_imports() if use_head else (set(), "")

        required_imports = {"strutils", "os"}

        all_imports = required_imports | head_imports

        parsing_code = []

        for i, name in enumerate(args_schema):
            nim_type = nim_types[name]
            parsing_code.append(cls._generate_typed_parse_code(name, i + 1, nim_type))

        import_block = "\n".join([f"import {imp}" for imp in sorted(all_imports)])

        parse_block = "\n".join(parsing_code) if parsing_code else ""

        warmup_check = '''  # Warmup check - exit immediately if this is a warmup run
  if paramCount() >= 1 and paramStr(1) == "__warmup__":
    quit(0)'''

        parts = [import_block, ""]
        if head_code_without_imports:
            parts.append(head_code_without_imports)
            parts.append("")

        parts.append("when isMainModule:")
        parts.append(warmup_check)
        if parse_block:
            parts.append(parse_block)

        indented_code = textwrap.indent(nim_code, "  ")
        parts.append(indented_code)

        full_code = "\n".join(parts)
        return full_code

    @classmethod
    def _extract_head_imports(cls) -> tuple:
        imports = set()
        remaining_code = ""

        if not cls._head_code:
            return imports, remaining_code

        head = cls._head_code
        lines = head.split("\n")
        non_import_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import "):
                import_part = stripped[7:].strip()
                for imp in import_part.split(","):
                    imp = imp.strip()
                    if imp:
                        imports.add(imp)
            elif stripped.startswith("from "):
                non_import_lines.append(line)
            else:
                non_import_lines.append(line)

        remaining_code = "\n".join(non_import_lines).strip()
        return imports, remaining_code

    @classmethod
    def _generate_typed_parse_code(cls, arg_name: str, arg_index: int, nim_type: str) -> str:
        if nim_type == "int":
            return f"  let {arg_name}: int = if paramCount() >= {arg_index}: parseInt(paramStr({arg_index})) else: 0"
        elif nim_type == "int64":
            return f"  let {arg_name}: int64 = if paramCount() >= {arg_index}: parseInt(paramStr({arg_index})).int64 else: 0'i64"
        elif nim_type == "float":
            return f"  let {arg_name}: float = if paramCount() >= {arg_index}: parseFloat(paramStr({arg_index})) else: 0.0"
        elif nim_type == "float64":
            return f"  let {arg_name}: float64 = if paramCount() >= {arg_index}: parseFloat(paramStr({arg_index})) else: 0.0"
        elif nim_type == "bool":
            return f"  let {arg_name}: bool = if paramCount() >= {arg_index}: parseBool(paramStr({arg_index})) else: false"
        elif nim_type == "string":
            return f'  let {arg_name}: string = if paramCount() >= {arg_index}: paramStr({arg_index}) else: ""'
        else:
            return f'  let {arg_name}: string = if paramCount() >= {arg_index}: paramStr({arg_index}) else: ""'

    @classmethod
    def _python_type_to_nim(cls, py_type: Any) -> str:
        if py_type is None:
            return "string"

        type_map = {
            int: "int64",
            float: "float64",
            str: "string",
            bool: "bool",
        }

        if py_type in type_map:
            return type_map[py_type]

        type_name = getattr(py_type, "__name__", str(py_type))
        return type_map.get(type_name, "string")

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
        if "when isMainModule:" in code:
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
            parsing_code.append(f'  let {arg_name} = if paramCount() >= {arg_index}: paramStr({arg_index}) else: ""')

        injection = "\n".join(parsing_code)

        if "when isMainModule:" in code:
            main_start = code.find("when isMainModule:")
            colon_pos = code.find(":", main_start)
            if colon_pos != -1:
                # Find the next line after the when statement
                next_line = code.find("\n", colon_pos)
                if next_line != -1:
                    return code[:next_line + 1] + injection + "\n" + code[next_line + 1:]

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
                cmd_args.append("true" if value else "false")
            else:
                cmd_args.append(str(value))

        return cmd_args
    ### PRIVATE UTILITIES END

