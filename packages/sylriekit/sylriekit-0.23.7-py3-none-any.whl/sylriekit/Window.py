import ast
import base64
import inspect
import mimetypes
import os
import re
import tempfile
import threading
import time
import types
from typing import Callable, Optional
from urllib.parse import quote

from webviewpy import Webview


class Window:
    HINT_NONE = 0
    HINT_MIN = 1
    HINT_MAX = 2
    HINT_FIXED = 3

    DEFAULT_INDEX = "index.html"
    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 600
    DEFAULT_TITLE = "Window"
    DEFAULT_DEBUG = False
    DEFAULT_SYNTAX = r"!python\.(\w+)\((.*?)\);"

    _WEBVIEW = None
    _BINDINGS = {}
    _RUNNING = False
    _THREAD = None
    _LOADED_HTML = None
    _CALLER_NAMESPACE = None
    _LOCK = threading.Lock()
    _THREADS = {}
    _THREAD_COUNTER = 0
    _BASE_DIR = None
    _TEMP_FILE = None

    @classmethod
    def load_config(cls, config: dict):
        if "Window" in config.keys():
            window_config = config["Window"]
            cls.DEFAULT_INDEX = window_config.get("DEFAULT_INDEX", cls.DEFAULT_INDEX)
            cls.DEFAULT_WIDTH = window_config.get("DEFAULT_WIDTH", cls.DEFAULT_WIDTH)
            cls.DEFAULT_HEIGHT = window_config.get("DEFAULT_HEIGHT", cls.DEFAULT_HEIGHT)
            cls.DEFAULT_TITLE = window_config.get("DEFAULT_TITLE", cls.DEFAULT_TITLE)
            cls.DEFAULT_DEBUG = window_config.get("DEFAULT_DEBUG", cls.DEFAULT_DEBUG)
            cls.DEFAULT_SYNTAX = window_config.get("DEFAULT_SYNTAX", cls.DEFAULT_SYNTAX)

    @classmethod
    def load(cls, index: Optional[str] = None, navigate: bool = False) -> bool:
        if navigate and cls._WEBVIEW is not None and cls._RUNNING:
            return cls.navigate(index)

        cls._BINDINGS = {}

        index = index or cls.DEFAULT_INDEX
        caller_frame = inspect.stack()[1]
        caller_dir = os.path.dirname(os.path.abspath(caller_frame.filename))
        cls._CALLER_NAMESPACE = caller_frame.frame.f_globals
        cls._CALLER_NAMESPACE['Window'] = cls
        if not os.path.isabs(index):
            index = os.path.join(caller_dir, index)
        if not os.path.isfile(index):
            raise FileNotFoundError(f"Index file not found: {index}")
        base_dir = os.path.dirname(os.path.abspath(index))
        cls._BASE_DIR = base_dir

        html = cls._load_html_with_assets(index)
        html = cls._process_python_tags(html, base_dir)
        html = cls._process_python_calls(html)
        cls._LOADED_HTML = html

        if cls._WEBVIEW is None:
            cls._WEBVIEW = Webview(debug=cls.DEFAULT_DEBUG)

        cls._WEBVIEW.set_title(cls.DEFAULT_TITLE)
        cls._WEBVIEW.set_size(cls.DEFAULT_WIDTH, cls.DEFAULT_HEIGHT, cls.HINT_NONE)
        for name, func in cls._BINDINGS.items():
            cls._WEBVIEW.bind(name, func)

        cls._TEMP_FILE = os.path.join(base_dir, f'.temp_window_{os.getpid()}.html')
        with open(cls._TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(html)

        file_url = cls._path_to_file_uri(cls._TEMP_FILE)
        cls._WEBVIEW.navigate(file_url)

        return True

    @classmethod
    def navigate(cls, index: Optional[str] = None) -> bool:
        if cls._WEBVIEW is None:
            raise RuntimeError("No window open. Call load() and open() first.")

        cls._BINDINGS = {}

        index = index or cls.DEFAULT_INDEX
        caller_frame = inspect.stack()[1]
        caller_dir = os.path.dirname(os.path.abspath(caller_frame.filename))

        if cls._CALLER_NAMESPACE is None:
            cls._CALLER_NAMESPACE = caller_frame.frame.f_globals
            cls._CALLER_NAMESPACE['Window'] = cls

        if not os.path.isabs(index):
            index = os.path.join(caller_dir, index)
        if not os.path.isfile(index):
            raise FileNotFoundError(f"Index file not found: {index}")

        base_dir = os.path.dirname(os.path.abspath(index))
        cls._BASE_DIR = base_dir
        html = cls._load_html_with_assets(index)
        html = cls._process_python_tags(html, base_dir)
        html = cls._process_python_calls(html)
        cls._LOADED_HTML = html

        for name, func in cls._BINDINGS.items():
            cls._WEBVIEW.bind(name, func)

        cls._WEBVIEW.set_title(cls.DEFAULT_TITLE)

        cls._TEMP_FILE = os.path.join(base_dir, f'.temp_window_{os.getpid()}.html')
        with open(cls._TEMP_FILE, 'w', encoding='utf-8') as f:
            f.write(html)

        file_url = cls._path_to_file_uri(cls._TEMP_FILE)
        cls._WEBVIEW.navigate(file_url)

        return True

    @classmethod
    def javascript(cls):
        def decorator(func: Callable) -> Callable:
            cls._BINDINGS[func.__name__] = func
            return func

        return decorator

    @classmethod
    def open(cls, threaded: bool = False) -> int:
        if cls._WEBVIEW is None:
            raise RuntimeError("No window loaded. Call load() first.")
        if threaded:
            cls._THREAD_COUNTER += 1
            thread_id = cls._THREAD_COUNTER

            def run_thread():
                cls._RUNNING = True
                cls._WEBVIEW.run()
                cls._RUNNING = False
                cls._cleanup_temp_file()
                if thread_id in cls._THREADS:
                    del cls._THREADS[thread_id]

            thread = threading.Thread(target=run_thread, daemon=True)
            cls._THREADS[thread_id] = {'thread': thread, 'running': True}
            cls._THREAD = thread
            thread.start()
            return thread_id
        else:
            cls._RUNNING = True
            cls._WEBVIEW.run()
            cls._RUNNING = False
            cls._cleanup_temp_file()
            return 0

    @classmethod
    def _cleanup_temp_file(cls):
        if cls._TEMP_FILE and os.path.exists(cls._TEMP_FILE):
            try:
                os.remove(cls._TEMP_FILE)
            except Exception:
                pass
            cls._TEMP_FILE = None

    @classmethod
    def loaded(cls, thread_id: int, time_between_checks: int = 100):
        check_interval = time_between_checks / 1000.0

        while cls._RUNNING:
            with cls._LOCK:
                yield True
            if cls._RUNNING:
                time.sleep(check_interval)

    @classmethod
    def close(cls, thread_id: int = 0) -> bool:
        if cls._WEBVIEW is None:
            return False

        cls._RUNNING = False

        try:
            cls._WEBVIEW.eval("document.body.innerHTML = '';")
        except Exception:
            pass

        def do_terminate():
            try:
                cls._WEBVIEW.terminate()
            except Exception:
                pass

        try:
            cls._WEBVIEW.dispatch(do_terminate)
        except Exception:
            pass

        cls._cleanup_temp_file()
        return True

    @classmethod
    def python_api_syntax(cls, syntax: str) -> bool:
        cls.DEFAULT_SYNTAX = syntax
        return True

    @classmethod
    def bind(cls, name: str, func: Callable) -> bool:
        cls._BINDINGS[name] = func
        if cls._WEBVIEW is not None:
            cls._WEBVIEW.bind(name, func)
        return True

    @classmethod
    def get_base_dir(cls) -> str:
        return cls._BASE_DIR or ""

    ### PRIVATE UTILITIES START
    @classmethod
    def _path_to_file_uri(cls, filepath: str) -> str:
        filepath = os.path.abspath(filepath)
        filepath = filepath.replace('\\', '/')
        if len(filepath) > 1 and filepath[1] == ':':
            return 'file:///' + filepath
        return 'file://' + filepath

    @classmethod
    def _process_python_calls(cls, html: str) -> str:
        html = cls._process_js_declarations(html)
        html = cls._process_html_replacements(html)
        return html

    @classmethod
    def _process_python_tags(cls, html: str, base_dir: str) -> str:
        pattern = r'<python(?:\s+src=["\']([^"\']+)["\'])?\s*>(.*?)</python>'

        def process_tag(match):
            src = match.group(1)
            inline_code = match.group(2).strip()
            if src:
                if not os.path.isabs(src):
                    src = os.path.join(base_dir, src)
                if os.path.isfile(src):
                    with open(src, 'r', encoding='utf-8') as f:
                        code = f.read()
                    cls._execute_python_definitions(code)
            if inline_code:
                cls._execute_python_definitions(inline_code)
            return ''

        return re.sub(pattern, process_tag, html, flags=re.DOTALL | re.IGNORECASE)

    @classmethod
    def _execute_python_definitions(cls, code: str) -> None:
        namespace = cls._CALLER_NAMESPACE if cls._CALLER_NAMESPACE else {'Window': cls}
        exec(code, namespace)
        for name, obj in namespace.items():
            if name.startswith('_'):
                continue
            if name in ('Window',):
                continue
            if isinstance(obj, types.ModuleType):
                continue
            if isinstance(obj, type):
                continue
            if callable(obj):
                cls._BINDINGS[name] = obj

    @classmethod
    def _process_js_declarations(cls, html: str) -> str:
        script_pattern = r'(<script[^>]*>)(.*?)(</script>)'

        def process_script(match):
            open_tag = match.group(1)
            content = match.group(2)
            close_tag = match.group(3)
            content = re.sub(cls.DEFAULT_SYNTAX, '', content)
            return f'{open_tag}{content}{close_tag}'

        return re.sub(script_pattern, process_script, html, flags=re.DOTALL)

    @classmethod
    def _process_html_replacements(cls, html: str) -> str:
        def is_in_script(match, text):
            pos = match.start()
            before = text[:pos]
            open_scripts = len(re.findall(r'<script[^>]*>', before))
            close_scripts = len(re.findall(r'</script>', before))
            return open_scripts > close_scripts

        def replacer(match):
            if is_in_script(match, html):
                return match.group(0)
            func_name = match.group(1)
            args_str = match.group(2).strip()
            if func_name not in cls._BINDINGS:
                return match.group(0)
            try:
                if args_str:
                    args = ast.literal_eval(f"({args_str},)")
                else:
                    args = ()
                result = cls._BINDINGS[func_name](*args)
                return str(result) if result is not None else ""
            except Exception:
                return match.group(0)

        return re.sub(cls.DEFAULT_SYNTAX, replacer, html)

    @classmethod
    def _load_html_with_assets(cls, html_path: str) -> str:
        base_dir = os.path.dirname(os.path.abspath(html_path))
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        css_pattern = r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\'][^>]*>'
        css_pattern_alt = r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\'][^>]*>'

        def replace_css(match):
            href = match.group(1)
            if href.startswith(('http://', 'https://', '//')):
                return match.group(0)
            css_path = os.path.join(base_dir, href)
            if os.path.isfile(css_path):
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                return f'<style>\n{css_content}\n</style>'
            return match.group(0)

        html = re.sub(css_pattern, replace_css, html)
        html = re.sub(css_pattern_alt, replace_css, html)
        js_pattern = r'<script[^>]+src=["\']([^"\']+)["\'][^>]*></script>'

        def replace_js(match):
            src = match.group(1)
            if src.startswith(('http://', 'https://', '//')):
                return match.group(0)
            js_path = os.path.join(base_dir, src)
            if os.path.isfile(js_path):
                with open(js_path, 'r', encoding='utf-8') as f:
                    js_content = f.read()
                js_content = re.sub(cls.DEFAULT_SYNTAX, '', js_content)
                return f'<script>\n{js_content}\n</script>'
            return match.group(0)

        html = re.sub(js_pattern, replace_js, html)
        return html
    ### PRIVATE UTILITIES END
