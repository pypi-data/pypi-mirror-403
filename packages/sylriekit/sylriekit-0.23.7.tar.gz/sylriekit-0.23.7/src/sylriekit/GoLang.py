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
    def _check_go_available() -> bool:
        try:
            result = subprocess.run(
                ["go", "version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False


    if not _check_go_available():
        warnings.warn(
            "Go compiler not found. Go language support will not work.\n"
            "To install:\n"
            "  Visit https://go.dev/dl/ and download the installer.\n"
            "  Or run: winget install --id GoLang.Go (on Windows)",
            RuntimeWarning
        )


class GoLang:
    TEMP_DIR = "temp"
    INDEX_FILE = "index.json"
    EXE_EXTENSION = ".exe"
    GO_MOD_FILE = "go.mod"
    GO_MAIN_FILE = "main.go"
    BUILD_BIN = "go"
    HASH_LENGTH = 12
    JSON_INDENT = 2

    CACHE_DIR = "__gocache__"
    GO_VERSION = "1.21.5"
    GO_MODULE = "gothon_module"
    BUILD_TIMEOUT = 60

    _head_code: str = ""
    _keep_cached: bool = False
    _auto_warm: bool = False
    _index: Dict[str, Dict[str, Any]] = {}
    _initialized: bool = False

    @classmethod
    def load_config(cls, config: Dict[str, Any]) -> None:
        tool_config = config.get("GoLang", {})
        cls.CACHE_DIR = tool_config.get("CACHE_DIR", cls.CACHE_DIR)
        cls.GO_VERSION = tool_config.get("GO_VERSION", cls.GO_VERSION)
        cls.GO_MODULE = tool_config.get("GO_MODULE", cls.GO_MODULE)
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
                go_code = source_file.read_text(encoding="utf-8").strip()
            else:
                docstring = func.__doc__
                if not docstring:
                    raise ValueError(f"Function '{func.__name__}' must have a docstring containing Go code.")
                go_code = textwrap.dedent(docstring).strip()

            build_id = func.__name__
            sig = inspect.signature(func)
            args_schema = list(sig.parameters.keys())
            type_hints = {
                name: param.annotation
                for name, param in sig.parameters.items()
                if param.annotation != inspect.Parameter.empty
            }

            full_code = cls._generate_main_wrapper(go_code, args_schema, type_hints, use_head=use_head)
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
        full_code = cls._ensure_imports(full_code, args_schema)

        temp_dir = Path(cls.CACHE_DIR) / cls.TEMP_DIR / build_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            mod_path = temp_dir / cls.GO_MOD_FILE
            mod_content = f"module {cls.GO_MODULE}\n\ngo {cls.GO_VERSION}\n"
            mod_path.write_text(mod_content, encoding="utf-8")

            main_path = temp_dir / cls.GO_MAIN_FILE
            main_path.write_text(full_code, encoding="utf-8")

            exe_path = Path(cls.CACHE_DIR) / exe_name
            cmd = [cls.BUILD_BIN, "build", "-o", str(exe_path.resolve())]

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
                raise FileNotFoundError("Go toolchain is not available in PATH.") from error
            except subprocess.TimeoutExpired as error:
                raise TimeoutError("Go build exceeded the configured timeout.") from error

            if result.returncode != 0:
                raise RuntimeError(f"Go build failed: {result.stderr.strip()}")

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
    def _generate_main_wrapper(cls, go_code: str, args_schema: List[str], type_hints: Dict[str, Any], use_head: bool = True) -> str:
        go_types = {name: cls._python_type_to_go(type_hints.get(name)) for name in args_schema}

        required_imports = set()
        if args_schema:
            required_imports.add("os")
            for go_type in go_types.values():
                if go_type in ("int", "float64"):
                    required_imports.add("strconv")

        required_imports.add("os")

        if "fmt." in go_code:
            required_imports.add("fmt")

        head_imports, head_code_without_imports = cls._extract_head_imports() if use_head else (set(), "")
        all_imports = required_imports | head_imports

        var_declarations = []
        parsing_code = []

        for i, name in enumerate(args_schema):
            go_type = go_types[name]
            var_declarations.append(f"\tvar {name} {go_type}")
            parsing_code.append(cls._generate_typed_parse_code(name, i + 1, go_type))

        import_block = ""
        if all_imports:
            import_block = "import (\n" + "\n".join([f'\t"{imp}"' for imp in sorted(all_imports)]) + "\n)\n"

        var_block = "\n".join(var_declarations) if var_declarations else ""
        parse_block = "\n".join(parsing_code) if parsing_code else ""

        warmup_check = '''\t// Warmup check - exit immediately if this is a warmup run
\tif len(os.Args) > 1 && os.Args[1] == "__warmup__" {
\t\treturn
\t}'''

        parts = ["package main", ""]
        if import_block:
            parts.append(import_block)
        if head_code_without_imports:
            parts.append(head_code_without_imports)
        parts.append("")
        parts.append("func main() {")
        parts.append(warmup_check)
        if var_block:
            parts.append(var_block)
        if parse_block:
            parts.append(parse_block)
        parts.append(textwrap.indent(go_code, "\t"))
        parts.append("}")

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

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('import(') or line.startswith('import ('):
                start_idx = line.find('(')
                if ')' in line:
                    block = line[start_idx + 1:line.find(')')]
                    for imp in block.split(';'):
                        imp = imp.strip().strip('"').strip("'")
                        if imp:
                            imports.add(imp)
                else:
                    i += 1
                    while i < len(lines) and ')' not in lines[i]:
                        imp = lines[i].strip().strip('"').strip("'")
                        if imp:
                            imports.add(imp)
                        i += 1
            elif line.startswith('import "') or line.startswith("import '"):
                start = line.find('"') + 1 if '"' in line else line.find("'") + 1
                end = line.rfind('"') if '"' in line else line.rfind("'")
                if end > start:
                    imports.add(line[start:end])
            else:
                non_import_lines.append(lines[i])

            i += 1

        remaining_code = "\n".join(non_import_lines).strip()
        return imports, remaining_code

    @classmethod
    def _generate_typed_parse_code(cls, arg_name: str, arg_index: int, go_type: str) -> str:
        if go_type == "int":
            return f"\tif len(os.Args) > {arg_index} {{ {arg_name}, _ = strconv.Atoi(os.Args[{arg_index}]) }}"
        elif go_type == "float64":
            return f"\tif len(os.Args) > {arg_index} {{ {arg_name}, _ = strconv.ParseFloat(os.Args[{arg_index}], 64) }}"
        elif go_type == "bool":
            return f"\tif len(os.Args) > {arg_index} {{ {arg_name} = os.Args[{arg_index}] == \"true\" }}"
        elif go_type == "string":
            return f"\tif len(os.Args) > {arg_index} {{ {arg_name} = os.Args[{arg_index}] }}"
        else:
            return f"\tif len(os.Args) > {arg_index} {{ {arg_name} = os.Args[{arg_index}] }}"

    @classmethod
    def _python_type_to_go(cls, py_type: Any) -> str:
        if py_type is None:
            return "interface{}"

        type_map = {
            int: "int",
            float: "float64",
            str: "string",
            bool: "bool",
        }

        if py_type in type_map:
            return type_map[py_type]

        type_name = getattr(py_type, "__name__", str(py_type))
        return type_map.get(type_name, "interface{}")

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
        if code.strip().startswith("package main"):
            return code

        if cls._head_code:
            code = f"{cls._head_code}\n\n{code}"

        if not args_schema:
            return code

        return cls._inject_args_parsing(code, args_schema)

    @classmethod
    def _inject_args_parsing(cls, code: str, args_schema: List[str]) -> str:
        var_declarations = []
        parsing_code = []

        for i, arg_name in enumerate(args_schema):
            arg_index = i + 1
            var_declarations.append(f"\tvar {arg_name} interface{{}}")
            parsing_code.append(cls._generate_parse_code(arg_name, arg_index))

        injection = "\n".join(var_declarations) + "\n" + "\n".join(parsing_code)

        if "func main()" in code:
            main_start = code.find("func main()")
            brace_pos = code.find("{", main_start)
            if brace_pos != -1:
                return code[:brace_pos + 1] + "\n" + injection + code[brace_pos + 1:]

        return code

    @classmethod
    def _generate_parse_code(cls, arg_name: str, arg_index: int) -> str:
        return f'''	if len(os.Args) > {arg_index} {{
		_parts_{arg_name} := strings.SplitN(os.Args[{arg_index}], ":", 2)
		if len(_parts_{arg_name}) == 2 {{
			switch _parts_{arg_name}[0] {{
			case "int":
				{arg_name}, _ = strconv.Atoi(_parts_{arg_name}[1])
			case "float64":
				{arg_name}, _ = strconv.ParseFloat(_parts_{arg_name}[1], 64)
			case "bool":
				{arg_name} = _parts_{arg_name}[1] == "true"
			default:
				{arg_name} = _parts_{arg_name}[1]
			}}
		}}
	}}'''

    @classmethod
    def _ensure_imports(cls, code: str, args_schema: List[str]) -> str:
        if not args_schema:
            return code

        if code.strip().startswith("package main"):
            return code

        required_imports = ["os", "strconv", "strings"]

        import_match_block = code.find("import (")
        import_match_single = code.find('import "')

        if import_match_block != -1:
            block_start = import_match_block
            block_end = code.find(")", block_start)
            import_block = code[block_start:block_end + 1]

            existing_in_block = []
            for line in import_block.split("\n"):
                if '"' in line:
                    start = line.find('"') + 1
                    end = line.find('"', start)
                    if end > start:
                        existing_in_block.append(line[start:end])

            all_imports = existing_in_block[:]
            for imp in required_imports:
                if imp not in all_imports:
                    all_imports.append(imp)

            new_block = "import (\n" + "\n".join([f'\t"{imp}"' for imp in all_imports]) + "\n)"
            code = code[:block_start] + new_block + code[block_end + 1:]

        elif import_match_single != -1:
            line_start = import_match_single
            line_end = code.find("\n", line_start)
            if line_end == -1:
                line_end = len(code)

            single_line = code[line_start:line_end]
            start = single_line.find('"') + 1
            end = single_line.find('"', start)
            existing_import = single_line[start:end] if end > start else None

            all_imports = []
            if existing_import:
                all_imports.append(existing_import)
            for imp in required_imports:
                if imp not in all_imports:
                    all_imports.append(imp)

            new_block = "import (\n" + "\n".join([f'\t"{imp}"' for imp in all_imports]) + "\n)"
            code = code[:line_start] + new_block + code[line_end:]

        else:
            package_pos = code.find("package")
            package_end = code.find("\n", package_pos)
            import_block = "\n\nimport (\n" + "\n".join([f'\t"{imp}"' for imp in required_imports]) + "\n)"
            code = code[:package_end + 1] + import_block + code[package_end + 1:]

        return code

    @classmethod
    def _compute_code_hash(cls, code: str, args_schema: List[str]) -> str:
        full_code = cls._get_full_code(code, args_schema)
        full_code = cls._ensure_imports(full_code, args_schema)
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
