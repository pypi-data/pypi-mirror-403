import json
import warnings
import pickle
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError

from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr
from RestrictedPython.PrintCollector import PrintCollector

warnings.filterwarnings("ignore", category=SyntaxWarning, module="RestrictedPython")


class Template:
    FORBIDDEN_ATTRIBUTES = {
        '__class__', '__bases__', '__subclasses__', '__code__',
        '__globals__', '__builtins__', '__mro__', '__closure__',
        '__func__', '__self__', '__module__', '__dict__', '__call__',
    }
    DEFAULT_ALLOWED_IMPORTS = {
        'math', 'random', 'datetime', 'json', 're',
        'collections', 'itertools', 'functools', 'string',
    }

    TEMPLATES = {}
    PROFILES = {}
    ACTIVE_PROFILE = "default"
    DEFAULT_TIMEOUT = 60
    TEMPLATE_DIRECTORY = "./templates"

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config.get("api_key", {})
        env_variables = config.get("env", {})
        if "Template" in config.keys():
            template_config = config["Template"]
            cls.DEFAULT_TIMEOUT = template_config.get("DEFAULT_TIMEOUT", cls.DEFAULT_TIMEOUT)
            cls.ACTIVE_PROFILE = template_config.get("ACTIVE_PROFILE", cls.ACTIVE_PROFILE)
            cls.TEMPLATE_DIRECTORY = template_config.get("TEMPLATE_DIRECTORY", cls.TEMPLATE_DIRECTORY)

    @classmethod
    def run(
            cls,
            template_id: str,
            update_context: bool = True,
            profile: str = None,
            timeout: int = None,
            use_template_profile: bool = True
    ) -> dict:
        cls._ensure_template(template_id)

        if use_template_profile and cls.TEMPLATES[template_id].get("profile") is not None:
            profile_data = cls.TEMPLATES[template_id]["profile"]
            temp_profile_id = f"_template_{template_id}"
            cls.PROFILES[temp_profile_id] = profile_data
            profile = temp_profile_id
        elif profile is None:
            profile = cls.ACTIVE_PROFILE

        cls._ensure_profile(profile)

        if timeout is None:
            timeout = cls.PROFILES[profile]["default_timeout"]

        code = cls.TEMPLATES[template_id]["code"]
        context = cls.PROFILES[profile]["context"]
        pre_code = cls.PROFILES[profile].get("pre_code", "")

        if timeout > 0:
            local_vars = cls._run_with_timeout(code, context, timeout, pre_code)
        else:
            local_vars = cls._run_direct(code, context, pre_code)

        if update_context:
            local_vars.pop("_print", None)
            cls.PROFILES[profile]["context"].update(local_vars)

        return local_vars

    @classmethod
    def save(cls, template_id: str, save_profile: bool = True, profile_id: str = None, file_path: str = None):
        cls._ensure_template(template_id)

        template_data = {
            "code": cls.TEMPLATES[template_id]["code"],
            "profile": None
        }

        if save_profile:
            if profile_id is None:
                profile_id = cls.ACTIVE_PROFILE
            cls._ensure_profile(profile_id)
            template_data["profile"] = cls._serialize_profile(profile_id)

        if file_path is None:
            file_path = f"{cls.TEMPLATE_DIRECTORY}/template.{template_id}.json"

        cls._ensure_directory(file_path)

        with open(file_path, "w") as f:
            f.write(json.dumps(template_data, indent=2))

        return file_path

    @classmethod
    def save_file(
            cls,
            target_file_path: str,
            template_id: str,
            save_profile: bool = True,
            profile_id: str = None,
            template_file_path: str = None
    ) -> str:
        cls._ensure_template(template_id)

        if profile_id is None:
            profile_id = cls.ACTIVE_PROFILE
        cls._ensure_profile(profile_id)

        profile = cls.PROFILES[profile_id]
        template_code = cls.TEMPLATES[template_id]["code"]

        lines = []

        if save_profile:
            pre_code = profile.get("pre_code", "")
            initial_data = profile.get("initial_data", {})

            if initial_data:
                lines.append("### INITIAL DATA START")
                for key, value in initial_data.items():
                    lines.append(f"{key} = {repr(value)}")
                lines.append("### INITIAL DATA END")
                lines.append("")

            if pre_code.strip():
                lines.append("### PRE CODE START")
                lines.append(pre_code.strip())
                lines.append("### PRE CODE END")
                lines.append("")

        lines.append("### TEMPLATE CODE START")
        lines.append(template_code.strip())
        lines.append("### TEMPLATE CODE END")

        if template_file_path:
            lines.insert(0, f"### TEMPLATE SOURCE: {template_file_path}")
            lines.insert(1, f"### TEMPLATE ID: {template_id}")
            lines.insert(2, f"### PROFILE ID: {profile_id}")
            lines.insert(3, "")

        file_content = "\n".join(lines) + "\n"

        cls._ensure_directory(target_file_path)

        with open(target_file_path, "w") as f:
            f.write(file_content)

        return target_file_path

    @classmethod
    def load(cls, file_path: str, template_id: str = None, use_profile: bool = True) -> str:
        with open(file_path, "r") as f:
            template_data = json.loads(f.read())

        if template_id is None:
            template_id = cls._extract_template_id(file_path)

        cls.TEMPLATES[template_id] = {
            "code": template_data["code"],
            "profile": None
        }

        if use_profile and template_data.get("profile") is not None:
            cls.TEMPLATES[template_id]["profile"] = cls._deserialize_profile(template_data["profile"])

        return template_id

    @classmethod
    def create_profile(
            cls,
            name: str,
            context: dict = None,
            default_timeout: int = None,
            pre_code: str = "",
            context_options: dict = None,
            initial_data: dict = None
    ):
        if context_options is None:
            context_options = {}
        if initial_data is None:
            initial_data = {}
        if context is None:
            context = cls.build_context(data=initial_data, **context_options)
        if default_timeout is None:
            default_timeout = cls.DEFAULT_TIMEOUT
        cls.PROFILES[name] = {
            "context": context,
            "default_timeout": default_timeout,
            "pre_code": pre_code,
            "context_options": context_options,
            "initial_data": initial_data
        }

    @classmethod
    def build_context(
            cls,
            data: dict = None,
            use_restrictions: bool = True,
            allow_imports: bool = False,
            allowed_imports: list = None,
            allow_print: bool = True,
            allow_getattr: bool = True,
            extra_builtins: dict = None,
    ) -> dict:
        if data is None:
            data = {}
        if not use_restrictions:
            context = {"__builtins__": __builtins__}
            context.update(data)
            return context

        context = safe_globals.copy()
        context["_getiter_"] = default_guarded_getiter
        context["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence

        if allow_print:
            context["_print_"] = PrintCollector
        if allow_getattr:
            context["_getattr_"] = cls._getattr_guard
        if allow_imports:
            if allowed_imports:
                context["__builtins__"]["__import__"] = cls._create_import_guard(allowed_imports)
            else:
                context["__builtins__"]["__import__"] = cls._import_guard
        if extra_builtins:
            for name, func in extra_builtins.items():
                context["__builtins__"][name] = func

        context.update(data)
        return context

    @classmethod
    def set_active_profile(cls, profile: str):
        cls._ensure_profile(profile)
        cls.ACTIVE_PROFILE = profile

    @classmethod
    def get_context_var(cls, var_name: str, profile: str = None):
        if profile is None:
            profile = cls.ACTIVE_PROFILE
        cls._ensure_profile(profile)
        return cls.PROFILES[profile]["context"].get(var_name)

    @classmethod
    def register_template(cls, template_id: str, code: str):
        cls.TEMPLATES[template_id] = {"code": code, "profile": None}

    ### PRIVATE UTILITIES START

    @classmethod
    def _ensure_profile(cls, profile: str):
        if profile not in cls.PROFILES:
            cls.PROFILES[profile] = {
                "context": cls.build_context(),
                "default_timeout": cls.DEFAULT_TIMEOUT,
                "pre_code": ""
            }

    @classmethod
    def _ensure_template(cls, template_id: str):
        if template_id not in cls.TEMPLATES:
            raise KeyError(f"Template '{template_id}' not found")

    @classmethod
    def _ensure_directory(cls, file_path: str):
        import os
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    @classmethod
    def _extract_template_id(cls, file_path: str) -> str:
        import os
        filename = os.path.basename(file_path)
        if filename.startswith("template.") and filename.endswith(".json"):
            return filename[9:-5]
        return filename.replace(".json", "")

    @classmethod
    def _serialize_profile(cls, profile_id: str) -> dict:
        profile = cls.PROFILES[profile_id]

        return {
            "default_timeout": profile["default_timeout"],
            "pre_code": profile.get("pre_code", ""),
            "context_options": profile.get("context_options", {}),
            "initial_data": profile.get("initial_data", {})
        }

    @classmethod
    def _deserialize_profile(cls, profile_data: dict) -> dict:
        context_options = profile_data.get("context_options", {})
        initial_data = profile_data.get("initial_data", {})

        context = cls.build_context(data=initial_data, **context_options)

        return {
            "context": context,
            "default_timeout": profile_data.get("default_timeout", cls.DEFAULT_TIMEOUT),
            "pre_code": profile_data.get("pre_code", ""),
            "context_options": context_options,
            "initial_data": initial_data
        }

    @classmethod
    def _run_direct(cls, code: str, context: dict, pre_code: str = "") -> dict:
        local_vars = {}

        if pre_code:
            pre_namespace = {"__builtins__": __builtins__}
            exec(pre_code, pre_namespace)
            for key, value in pre_namespace.items():
                if key != "__builtins__":
                    local_vars[key] = value

        byte_code = compile_restricted(code, "<template>", "exec")
        exec(byte_code, context, local_vars)

        if "_print" in local_vars:
            output = local_vars["_print"]()
            if output:
                print(output, end="")

        return local_vars

    @classmethod
    def _run_with_timeout(cls, code: str, context: dict, timeout: int, pre_code: str = "") -> dict:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(cls._run_restricted_process, code, context, pre_code)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                raise TimeoutError(f"Execution timed out after {timeout} seconds")

    @staticmethod
    def _getattr_guard(obj, name, default=None):
        forbidden = {
            '__class__', '__bases__', '__subclasses__', '__code__',
            '__globals__', '__builtins__', '__mro__', '__closure__',
            '__func__', '__self__', '__module__', '__dict__', '__call__',
        }
        if name.startswith('_') and name in forbidden:
            raise AttributeError(f"Access to '{name}' is not allowed")
        return safer_getattr(obj, name, default)

    @staticmethod
    def _import_guard(name, globals=None, locals=None, fromlist=(), level=0):
        allowed = {
            'math', 'random', 'datetime', 'json', 're',
            'collections', 'itertools', 'functools', 'string',
        }
        if name not in allowed:
            raise ImportError(f"Import of '{name}' is not allowed")
        return __import__(name, globals, locals, fromlist, level)

    @staticmethod
    def _create_import_guard(allowed_imports: list):
        def _custom_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name not in allowed_imports:
                raise ImportError(f"Import of '{name}' is not allowed. Allowed: {allowed_imports}")
            return __import__(name, globals, locals, fromlist, level)

        return _custom_import

    @staticmethod
    def _run_restricted_process(code: str, context: dict, pre_code: str = "") -> dict:
        local_vars = {}

        if pre_code:
            pre_namespace = {"__builtins__": __builtins__}
            exec(pre_code, pre_namespace)
            for key, value in pre_namespace.items():
                if key != "__builtins__":
                    local_vars[key] = value

        byte_code = compile_restricted(code, "<template>", "exec")
        exec(byte_code, context, local_vars)

        if "_print" in local_vars:
            output = local_vars["_print"]()
            if output:
                print(output, end="")

        result = {}
        for key, value in local_vars.items():
            try:
                pickle.dumps(value)
                result[key] = value
            except (pickle.PicklingError, TypeError, AttributeError):
                pass

        return result

    ### PRIVATE UTILITIES END