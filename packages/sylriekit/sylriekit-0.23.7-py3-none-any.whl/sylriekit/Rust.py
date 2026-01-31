import functools
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import textwrap
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

if os.getenv("SHOW_SYLRIEKIT_LANG_WARNINGS", "False") == "True":
    def _check_cargo_available() -> bool:
        try:
            result = subprocess.run(
                ["cargo", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False


    if not _check_cargo_available():
        warnings.warn(
            "Cargo/Rust compiler not found. Rust language support will not work.\n"
            "To install:\n"
            "  Visit https://rustup.rs/ and follow the installation instructions.\n"
            "  Or run: winget install --id Rustlang.Rustup (on Windows)",
            RuntimeWarning
        )


class Rust:
    TEMP_DIR = "temp"
    INDEX_FILE = "index.json"
    EXE_EXTENSION = ".exe"
    RUST_MAIN_FILE = "main.rs"
    CARGO_TOML_FILE = "Cargo.toml"
    SRC_DIR = "src"
    BUILD_BIN = "cargo"
    HASH_LENGTH = 12
    JSON_INDENT = 2

    CACHE_DIR = "__rustcache__"
    BUILD_TIMEOUT = 120
    TOOLCHAIN = "stable-x86_64-pc-windows-gnu"

    _head_code: str = ""
    _keep_cached: bool = False
    _auto_warm: bool = False
    _index: Dict[str, Dict[str, Any]] = {}
    _initialized: bool = False

    @classmethod
    def load_config(cls, config: Dict[str, Any]) -> None:
        tool_config = config.get("Rust", {})
        cls.CACHE_DIR = tool_config.get("CACHE_DIR", cls.CACHE_DIR)
        cls.BUILD_TIMEOUT = tool_config.get("BUILD_TIMEOUT", cls.BUILD_TIMEOUT)
        cls.TOOLCHAIN = tool_config.get("TOOLCHAIN", cls.TOOLCHAIN)

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
                rust_code = source_file.read_text(encoding="utf-8").strip()
            else:
                docstring = func.__doc__
                if not docstring:
                    raise ValueError(f"Function '{func.__name__}' must have a docstring containing Rust code.")
                rust_code = textwrap.dedent(docstring).strip()

            build_id = func.__name__
            sig = inspect.signature(func)
            args_schema = list(sig.parameters.keys())
            type_hints = {
                name: param.annotation
                for name, param in sig.parameters.items()
                if param.annotation != inspect.Parameter.empty
            }

            full_code = cls._generate_main_wrapper(rust_code, args_schema, type_hints, use_head=use_head)
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
            src_dir = temp_dir / cls.SRC_DIR
            src_dir.mkdir(parents=True, exist_ok=True)

            main_path = src_dir / cls.RUST_MAIN_FILE
            main_path.write_text(full_code, encoding="utf-8")

            cargo_toml = temp_dir / cls.CARGO_TOML_FILE
            cargo_content = f'''[package]
name = "{build_id}"
version = "0.1.0"
edition = "2021"

[profile.release]
opt-level = 3
lto = true
'''
            cargo_toml.write_text(cargo_content, encoding="utf-8")

            exe_path = Path(cls.CACHE_DIR) / exe_name
            cmd = [cls.BUILD_BIN, f"+{cls.TOOLCHAIN}", "build", "--release", "--quiet"]

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
                raise FileNotFoundError("Cargo is not available in PATH.") from error
            except subprocess.TimeoutExpired as error:
                raise TimeoutError("Rust build exceeded the configured timeout.") from error

            if result.returncode != 0:
                raise RuntimeError(f"Rust build failed: {result.stderr.strip()}")

            built_exe = temp_dir / "target" / "release" / f"{build_id}{cls.EXE_EXTENSION}"
            if built_exe.exists():
                shutil.copy2(built_exe, exe_path)
            else:
                raise RuntimeError(f"Built executable not found at {built_exe}")

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
    def _generate_main_wrapper(cls, rust_code: str, args_schema: List[str], type_hints: Dict[str, Any], use_head: bool = True) -> str:
        rust_types = {name: cls._python_type_to_rust(type_hints.get(name)) for name in args_schema}

        head_uses, head_code_without_uses = cls._extract_head_uses() if use_head else (set(), "")

        var_declarations = []
        parsing_code = []

        for i, name in enumerate(args_schema):
            rust_type = rust_types[name]
            parsing_code.append(cls._generate_typed_parse_code(name, i + 1, rust_type))

        use_block = ""
        if head_uses:
            use_block = "\n".join([f"use {u};" for u in sorted(head_uses)]) + "\n"

        parse_block = "\n".join(parsing_code) if parsing_code else ""

        warmup_check = '''    let args: Vec<String> = std::env::args().collect();
    // Warmup check - exit immediately if this is a warmup run
    if args.get(1).map(|s| s == "__warmup__").unwrap_or(false) {
        return;
    }'''

        parts = []
        if use_block:
            parts.append(use_block)
        if head_code_without_uses:
            parts.append(head_code_without_uses)
        parts.append("")
        parts.append("fn main() {")
        parts.append(warmup_check)
        if parse_block:
            parts.append(parse_block)
        parts.append(textwrap.indent(rust_code, "    "))
        parts.append("}")

        full_code = "\n".join(parts)
        return full_code

    @classmethod
    def _extract_head_uses(cls) -> tuple:
        uses = set()
        remaining_code = ""

        if not cls._head_code:
            return uses, remaining_code

        head = cls._head_code
        lines = head.split("\n")
        non_use_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("use ") and stripped.endswith(";"):
                use_path = stripped[4:-1].strip()
                uses.add(use_path)
            else:
                non_use_lines.append(line)

        remaining_code = "\n".join(non_use_lines).strip()
        return uses, remaining_code

    @classmethod
    def _generate_typed_parse_code(cls, arg_name: str, arg_index: int, rust_type: str) -> str:
        if rust_type == "i32":
            return f"    let {arg_name}: i32 = args.get({arg_index}).map(|s| s.parse().unwrap_or(0)).unwrap_or(0);"
        elif rust_type == "i64":
            return f"    let {arg_name}: i64 = args.get({arg_index}).map(|s| s.parse().unwrap_or(0)).unwrap_or(0);"
        elif rust_type == "f64":
            return f"    let {arg_name}: f64 = args.get({arg_index}).map(|s| s.parse().unwrap_or(0.0)).unwrap_or(0.0);"
        elif rust_type == "f32":
            return f"    let {arg_name}: f32 = args.get({arg_index}).map(|s| s.parse().unwrap_or(0.0)).unwrap_or(0.0);"
        elif rust_type == "bool":
            return f'    let {arg_name}: bool = args.get({arg_index}).map(|s| s == "true").unwrap_or(false);'
        elif rust_type == "String":
            return f'    let {arg_name}: String = args.get({arg_index}).cloned().unwrap_or_default();'
        else:
            return f'    let {arg_name}: String = args.get({arg_index}).cloned().unwrap_or_default();'

    @classmethod
    def _python_type_to_rust(cls, py_type: Any) -> str:
        if py_type is None:
            return "String"

        type_map = {
            int: "i64",
            float: "f64",
            str: "String",
            bool: "bool",
        }

        if py_type in type_map:
            return type_map[py_type]

        type_name = getattr(py_type, "__name__", str(py_type))
        return type_map.get(type_name, "String")

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
        if "fn main()" in code:
            return code

        if cls._head_code:
            code = f"{cls._head_code}\n\n{code}"

        if not args_schema:
            return code

        return cls._inject_args_parsing(code, args_schema)

    @classmethod
    def _inject_args_parsing(cls, code: str, args_schema: List[str]) -> str:
        parsing_code = []
        parsing_code.append("    let args: Vec<String> = std::env::args().collect();")

        for i, arg_name in enumerate(args_schema):
            arg_index = i + 1
            parsing_code.append(f'    let {arg_name}: String = args.get({arg_index}).cloned().unwrap_or_default();')

        injection = "\n".join(parsing_code)

        if "fn main()" in code:
            main_start = code.find("fn main()")
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
                cmd_args.append("true" if value else "false")
            else:
                cmd_args.append(str(value))

        return cmd_args
    ### PRIVATE UTILITIES END

