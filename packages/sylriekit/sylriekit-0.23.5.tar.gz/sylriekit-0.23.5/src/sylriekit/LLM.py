import os
import json
import threading
import queue
import uuid
import inspect
import re
from typing import Generator, Callable, Any
import requests
import tiktoken

class _LLM_ToolDef:
    def __init__(self, name: str, description: str, parameters: dict, handler: Callable, source: str):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.source = source


class _LLM_ToolCall:
    def __init__(self, id: str, name: str, arguments: dict):
        self.id = id
        self.name = name
        self.arguments = arguments


class _LLM_Chat:
    def __init__(self, chat_id: str):
        self.chat_id = chat_id
        self.messages = []
        self.token_count = 0


class _LLM_CacheEntry:
    def __init__(self, chat_id: str, content: str, is_complete: bool, tool_calls: list = None):
        self.chat_id = chat_id
        self.content = content
        self.is_complete = is_complete
        self.tool_calls = tool_calls or []


class _LLM_ProviderAdapter:
    def format_tools(self, tools: list) -> Any:
        raise NotImplementedError

    def format_messages(self, messages: list) -> Any:
        raise NotImplementedError

    def parse_response(self, response: dict) -> tuple:
        raise NotImplementedError

    def parse_stream_chunk(self, chunk: dict) -> str:
        raise NotImplementedError

    def format_tool_results(self, tool_calls: list, results: list) -> Any:
        raise NotImplementedError

    def is_tool_call(self, response: dict) -> bool:
        raise NotImplementedError

    def get_assistant_message(self, response: dict) -> dict:
        raise NotImplementedError

    def call_api(self, messages: list, tools: list, api_key: str, model: str) -> dict:
        raise NotImplementedError

    def call_api_stream(self, messages: list, tools: list, api_key: str, model: str) -> Generator:
        raise NotImplementedError


class _LLM_AnthropicAdapter(_LLM_ProviderAdapter):
    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def format_tools(self, tools: list) -> list:
        formatted = []
        for tool in tools:
            formatted.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            })
        return formatted

    def format_messages(self, messages: list) -> list:
        return messages

    def parse_response(self, response: dict) -> tuple:
        text_parts = []
        tool_calls = []
        for block in response.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(_LLM_ToolCall(
                    id=block.get("id"),
                    name=block.get("name"),
                    arguments=block.get("input", {})
                ))
        return "".join(text_parts), tool_calls

    def parse_stream_chunk(self, chunk: dict) -> str:
        if chunk.get("type") == "content_block_delta":
            delta = chunk.get("delta", {})
            if delta.get("type") == "text_delta":
                return delta.get("text", "")
        return ""

    def format_tool_results(self, tool_calls: list, results: list) -> dict:
        content = []
        for tc, result in zip(tool_calls, results):
            content.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(result) if not isinstance(result, str) else result
            })
        return {"role": "user", "content": content}

    def is_tool_call(self, response: dict) -> bool:
        return response.get("stop_reason") == "tool_use"

    def get_assistant_message(self, response: dict) -> dict:
        return {"role": "assistant", "content": response.get("content", [])}

    def call_api(self, messages: list, tools: list, api_key: str, model: str) -> dict:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json"
        }
        body = {
            "model": model,
            "max_tokens": 8192,
            "messages": messages
        }
        if tools:
            body["tools"] = tools
        response = requests.post(self.API_URL, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    def call_api_stream(self, messages: list, tools: list, api_key: str, model: str) -> Generator:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json"
        }
        body = {
            "model": model,
            "max_tokens": 8192,
            "messages": messages,
            "stream": True
        }
        if tools:
            body["tools"] = tools
        response = requests.post(self.API_URL, headers=headers, json=body, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = line_str[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue


class _LLM_OpenAICompatAdapter(_LLM_ProviderAdapter):
    API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_url: str = None):
        self.api_url = api_url or self.API_URL

    def format_tools(self, tools: list) -> list:
        formatted = []
        for tool in tools:
            formatted.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return formatted

    def format_messages(self, messages: list) -> list:
        return messages

    def parse_response(self, response: dict) -> tuple:
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "") or ""
        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            args_str = func.get("arguments", "{}")
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(_LLM_ToolCall(
                id=tc.get("id"),
                name=func.get("name"),
                arguments=args
            ))
        return text, tool_calls

    def parse_stream_chunk(self, chunk: dict) -> str:
        choice = chunk.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        return delta.get("content", "") or ""

    def format_tool_results(self, tool_calls: list, results: list) -> list:
        messages = []
        for tc, result in zip(tool_calls, results):
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result) if not isinstance(result, str) else result
            })
        return messages

    def is_tool_call(self, response: dict) -> bool:
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        has_tool_calls = bool(message.get("tool_calls"))
        return has_tool_calls or choice.get("finish_reason") == "tool_calls"

    def get_assistant_message(self, response: dict) -> dict:
        choice = response.get("choices", [{}])[0]
        return choice.get("message", {"role": "assistant", "content": ""})

    def call_api(self, messages: list, tools: list, api_key: str, model: str) -> dict:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": messages
        }
        if tools:
            body["tools"] = tools
        response = requests.post(self.api_url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    def call_api_stream(self, messages: list, tools: list, api_key: str, model: str) -> Generator:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        if tools:
            body["tools"] = tools
        response = requests.post(self.api_url, headers=headers, json=body, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = line_str[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue


class _LLM_GoogleAdapter(_LLM_ProviderAdapter):
    API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    API_URL_STREAM_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"

    def format_tools(self, tools: list) -> list:
        function_declarations = []
        for tool in tools:
            function_declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        return [{"function_declarations": function_declarations}]

    def format_messages(self, messages: list) -> list:
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}] if isinstance(msg["content"], str) else msg["content"]
            })
        return contents

    def parse_response(self, response: dict) -> tuple:
        text_parts = []
        tool_calls = []
        candidates = response.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            for part in content.get("parts", []):
                if "text" in part:
                    text_parts.append(part["text"])
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append(_LLM_ToolCall(
                        id=str(uuid.uuid4()),
                        name=fc.get("name"),
                        arguments=fc.get("args", {})
                    ))
        return "".join(text_parts), tool_calls

    def parse_stream_chunk(self, chunk: dict) -> str:
        candidates = chunk.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            for part in content.get("parts", []):
                if "text" in part:
                    return part["text"]
        return ""

    def format_tool_results(self, tool_calls: list, results: list) -> dict:
        parts = []
        for tc, result in zip(tool_calls, results):
            parts.append({
                "functionResponse": {
                    "name": tc.name,
                    "response": {"result": result} if not isinstance(result, dict) else result
                }
            })
        return {"role": "user", "parts": parts}

    def is_tool_call(self, response: dict) -> bool:
        candidates = response.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            for part in content.get("parts", []):
                if "functionCall" in part:
                    return True
        return False

    def get_assistant_message(self, response: dict) -> dict:
        candidates = response.get("candidates", [])
        if candidates:
            return candidates[0].get("content", {"role": "model", "parts": []})
        return {"role": "model", "parts": []}

    def call_api(self, messages: list, tools: list, api_key: str, model: str) -> dict:
        url = self.API_URL_TEMPLATE.format(model=model) + f"?key={api_key}"
        body = {"contents": messages}
        if tools:
            body["tools"] = tools
        response = requests.post(url, json=body)
        response.raise_for_status()
        return response.json()

    def call_api_stream(self, messages: list, tools: list, api_key: str, model: str) -> Generator:
        url = self.API_URL_STREAM_TEMPLATE.format(model=model) + f"?key={api_key}&alt=sse"
        body = {"contents": messages}
        if tools:
            body["tools"] = tools
        response = requests.post(url, json=body, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = line_str[6:]
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue


class _LLM_OpenRouterAdapter(_LLM_OpenAICompatAdapter):
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self):
        super().__init__(api_url=self.API_URL)

    def call_api(self, messages: list, tools: list, api_key: str, model: str) -> dict:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/user/llm-toolkit",
            "X-Title": "LLM Toolkit"
        }
        body = {
            "model": model,
            "messages": messages
        }
        if tools:
            body["tools"] = tools
        response = requests.post(self.api_url, headers=headers, json=body)
        if not response.ok:
            print(f"[DEBUG] OpenRouter error response: {response.text}")
        response.raise_for_status()
        return response.json()

    def call_api_stream(self, messages: list, tools: list, api_key: str, model: str) -> Generator:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/user/llm-toolkit",
            "X-Title": "LLM Toolkit"
        }
        body = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        if tools:
            body["tools"] = tools
        response = requests.post(self.api_url, headers=headers, json=body, stream=True)
        if not response.ok:
            print(f"[DEBUG] OpenRouter error response: {response.text}")
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = line_str[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue


class LLM:
    SUPPORTED_PROVIDERS = ["anthropic", "openai", "google", "xai", "openrouter"]
    PROVIDER_ALIASES = {
        "claude": "anthropic",
        "gpt": "openai",
        "gemini": "google",
        "grok": "xai"
    }
    DEFAULT_MAX_CONTEXT = 200000
    DEFAULT_TOOL_CALL_PARAM_LENGTH = 25
    DEFAULT_TOKENIZER = "cl100k_base"
    TOOL_SUPPORT_UNTESTED = 0
    TOOL_SUPPORT_WORKS = 1
    TOOL_SUPPORT_SYSTEM_MSG = 2
    DEFAULT_THOUGHTS_START = "%%!--THOUGHTS!"
    DEFAULT_THOUGHTS_END = "!THOUGHTS--!%%"
    THOUGHT_PATTERNS = [
        ("<thinking>", "</thinking>"),
        ("<think>", "</think>"),
        ("<|startofthought|>", "<|endofthought|>"),
        ("<|thinking|>", "<|/thinking|>"),
    ]

    PROVIDER = None
    MODEL = None
    API_KEY = None
    ACTIVE_CHAT_ID = None
    MAX_CONTEXT_LENGTH = 200000
    THREADED_MODE = False
    DETAILED_CACHE_MODE = False
    SHOW_TOOL_CALLS = True
    TOOL_CALL_PARAM_LENGTH = 25
    TOKENIZER_PATH = None
    SHOW_THOUGHTS = True
    THOUGHTS_START_MARKER = "%%!--THOUGHTS!"
    THOUGHTS_END_MARKER = "!THOUGHTS--!%%"

    _TOOLS = {}
    _MCP_SERVERS = {}
    _CHATS = {}
    _PRESETS = {}
    _ADAPTERS = {}
    _REPLY_HANDLERS = {}
    _LIVE_REPLY_HANDLERS = {}
    _RESPONSE_CACHE = []
    _CACHE_LOCK = threading.Lock()
    _WORKER_THREAD = None
    _REQUEST_QUEUE = queue.Queue()
    _CACHE_FORMAT = "chunks"
    _TOKENIZER = None
    _STREAM_TOOL_CALLS = []
    _STREAM_FULL_RESPONSE = None
    _MODEL_TOOL_SUPPORT = {}
    _FIRST_MESSAGE_SENT = False
    _IN_THOUGHT_BLOCK = False
    _CURRENT_THOUGHT_END = None
    _THOUGHT_BUFFER = ""

    class providers:
        ANTHROPIC = "anthropic"
        OPENAI = "openai"
        GOOGLE = "google"
        XAI = "xai"
        OPENROUTER = "openrouter"
        LOCAL = "local"
        CLAUDE = "anthropic"
        GPT = "openai"
        GEMINI = "google"
        GROK = "xai"

    class cache_types:
        CHUNKS = "chunks"
        MESSAGES = "messages"
        CHUNKS_1_CHAR = "chunks_1"
        CHUNKS_10_CHAR = "chunks_10"
        CHUNKS_50_CHAR = "chunks_50"
        CHUNKS_100_CHAR = "chunks_100"

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config.get("api_key", {})
        env_variables = config.get("env", {})
        if "LLM" in config:
            llm_config = config["LLM"]
            cls.PROVIDER = llm_config.get("PROVIDER", cls.PROVIDER)
            cls.MODEL = llm_config.get("MODEL", cls.MODEL)
            cls.MAX_CONTEXT_LENGTH = llm_config.get("MAX_CONTEXT_LENGTH", cls.MAX_CONTEXT_LENGTH)
            cls.THREADED_MODE = llm_config.get("THREADED_MODE", cls.THREADED_MODE)
            cls.SHOW_TOOL_CALLS = llm_config.get("SHOW_TOOL_CALLS", cls.SHOW_TOOL_CALLS)
            cls.TOOL_CALL_PARAM_LENGTH = llm_config.get("TOOL_CALL_PARAM_LENGTH", cls.TOOL_CALL_PARAM_LENGTH)
            cls.DETAILED_CACHE_MODE = llm_config.get("DETAILED_CACHE_MODE", cls.DETAILED_CACHE_MODE)
            cls.SHOW_THOUGHTS = llm_config.get("SHOW_THOUGHTS", cls.SHOW_THOUGHTS)
            cls.THOUGHTS_START_MARKER = llm_config.get("THOUGHTS_START_MARKER", cls.THOUGHTS_START_MARKER)
            cls.THOUGHTS_END_MARKER = llm_config.get("THOUGHTS_END_MARKER", cls.THOUGHTS_END_MARKER)
        if cls.PROVIDER:
            resolved = cls._resolve_provider(cls.PROVIDER)
            key_map = {
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "google": "GOOGLE_API_KEY",
                "xai": "XAI_API_KEY",
                "openrouter": "OPENROUTER_API_KEY"
            }
            key_name = key_map.get(resolved)
            if key_name and key_name in api_keys:
                cls.API_KEY = api_keys[key_name]
        cls._init_adapters()

    @classmethod
    def use_provider(cls, provider):
        if isinstance(provider, str):
            cls.PROVIDER = cls._resolve_provider(provider)
        else:
            cls.PROVIDER = provider
        cls._init_adapters()

    @classmethod
    def use_key(cls, key: str):
        cls.API_KEY = key

    @classmethod
    def use_model(cls, model: str):
        cls.MODEL = model
        cls._FIRST_MESSAGE_SENT = False

    @classmethod
    def use_tokenizer_file(cls, path: str):
        cls.TOKENIZER_PATH = path
        cls._TOKENIZER = None

    @classmethod
    def set_max_context_length(cls, length: int):
        cls.MAX_CONTEXT_LENGTH = length

    @classmethod
    def threaded(cls, enabled: bool):
        cls.THREADED_MODE = enabled
        if enabled and cls._WORKER_THREAD is None:
            cls._start_worker_thread()

    @classmethod
    def cache_format(cls, format_type):
        cls._CACHE_FORMAT = format_type

    @classmethod
    def detailed_cache_mode(cls, enabled: bool):
        cls.DETAILED_CACHE_MODE = enabled

    @classmethod
    def show_tool_calls(cls, enabled: bool):
        cls.SHOW_TOOL_CALLS = enabled

    @classmethod
    def show_thoughts(cls, enabled: bool):
        cls.SHOW_THOUGHTS = enabled

    @classmethod
    def set_thought_markers(cls, start: str, end: str):
        cls.THOUGHTS_START_MARKER = start
        cls.THOUGHTS_END_MARKER = end

    @classmethod
    def get_model_tool_support(cls, model: str = None) -> int:
        target = model or cls.MODEL
        return cls._MODEL_TOOL_SUPPORT.get(target, cls.TOOL_SUPPORT_UNTESTED)

    @classmethod
    def set_model_tool_support(cls, status: int, model: str = None):
        target = model or cls.MODEL
        cls._MODEL_TOOL_SUPPORT[target] = status

    @classmethod
    def use_tool(cls, func: Callable):
        cls._register_tool(func)

    @classmethod
    def tool(cls):
        def decorator(func: Callable):
            cls._register_tool(func)
            return func

        return decorator

    @classmethod
    def use_mcp(cls, path: str):
        config = cls._load_mcp_config(path)
        servers = config.get("mcpServers", {})
        for name, server_config in servers.items():
            cls._connect_mcp_server(name, server_config)

    @classmethod
    def generate_chat(cls) -> str:
        chat_id = str(uuid.uuid4())
        cls._CHATS[chat_id] = _LLM_Chat(chat_id)
        return chat_id

    @classmethod
    def use_chat(cls, chat_id: str):
        if chat_id not in cls._CHATS:
            cls._CHATS[chat_id] = _LLM_Chat(chat_id)
        cls.ACTIVE_CHAT_ID = chat_id

    @classmethod
    def get_current_context_length(cls, chat_id: str = None) -> int:
        cid = chat_id or cls.ACTIVE_CHAT_ID
        if cid and cid in cls._CHATS:
            return cls._CHATS[cid].token_count
        return 0

    @classmethod
    def send(cls, message: str) -> str:
        if cls.THREADED_MODE:
            request_id = str(uuid.uuid4())
            cls._REQUEST_QUEUE.put({
                "id": request_id,
                "chat_id": cls.ACTIVE_CHAT_ID,
                "message": message,
                "stream": False
            })
            return request_id
        return cls._send_sync(message)

    @classmethod
    def send_live(cls, message: str) -> Generator:
        if cls.THREADED_MODE:
            request_id = str(uuid.uuid4())
            cls._REQUEST_QUEUE.put({
                "id": request_id,
                "chat_id": cls.ACTIVE_CHAT_ID,
                "message": message,
                "stream": True
            })
            return iter([request_id])
        return cls._send_stream_sync(message)

    @classmethod
    def get_response_cache(cls):
        with cls._CACHE_LOCK:
            if cls.DETAILED_CACHE_MODE:
                return list(cls._RESPONSE_CACHE)
            else:
                combined = "".join(entry.content for entry in cls._RESPONSE_CACHE)
                return combined

    @classmethod
    def clear_response_cache(cls, processed):
        with cls._CACHE_LOCK:
            if cls.DETAILED_CACHE_MODE and isinstance(processed, list):
                processed_ids = {id(e) for e in processed}
                cls._RESPONSE_CACHE = [e for e in cls._RESPONSE_CACHE if id(e) not in processed_ids]
            else:
                cls._RESPONSE_CACHE = []

    @classmethod
    def on_reply(cls, chat_id: str = None):
        def decorator(func: Callable):
            key = chat_id
            if key not in cls._REPLY_HANDLERS:
                cls._REPLY_HANDLERS[key] = []
            cls._REPLY_HANDLERS[key].append(func)
            return func

        return decorator

    @classmethod
    def on_live_reply(cls, chat_id: str = None):
        def decorator(func: Callable):
            key = chat_id
            if key not in cls._LIVE_REPLY_HANDLERS:
                cls._LIVE_REPLY_HANDLERS[key] = []
            cls._LIVE_REPLY_HANDLERS[key].append(func)
            return func

        return decorator

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        tokenizer = cls._get_tokenizer()
        if tokenizer:
            return len(tokenizer.encode(text))
        return len(text) // 4

    @classmethod
    def save_preset(cls, name: str):
        cls._PRESETS[name] = {
            "PROVIDER": cls.PROVIDER,
            "MODEL": cls.MODEL,
            "API_KEY": cls.API_KEY,
            "MAX_CONTEXT_LENGTH": cls.MAX_CONTEXT_LENGTH,
            "THREADED_MODE": cls.THREADED_MODE,
            "SHOW_TOOL_CALLS": cls.SHOW_TOOL_CALLS,
            "TOOL_CALL_PARAM_LENGTH": cls.TOOL_CALL_PARAM_LENGTH,
            "DETAILED_CACHE_MODE": cls.DETAILED_CACHE_MODE,
            "_CACHE_FORMAT": cls._CACHE_FORMAT
        }

    @classmethod
    def use_preset(cls, name: str):
        if name not in cls._PRESETS:
            raise ValueError(f"Preset '{name}' not found")
        preset = cls._PRESETS[name]
        cls.PROVIDER = preset.get("PROVIDER")
        cls.MODEL = preset.get("MODEL")
        cls.API_KEY = preset.get("API_KEY")
        cls.MAX_CONTEXT_LENGTH = preset.get("MAX_CONTEXT_LENGTH", cls.DEFAULT_MAX_CONTEXT)
        cls.THREADED_MODE = preset.get("THREADED_MODE", False)
        cls.SHOW_TOOL_CALLS = preset.get("SHOW_TOOL_CALLS", True)
        cls.TOOL_CALL_PARAM_LENGTH = preset.get("TOOL_CALL_PARAM_LENGTH", cls.DEFAULT_TOOL_CALL_PARAM_LENGTH)
        cls.DETAILED_CACHE_MODE = preset.get("DETAILED_CACHE_MODE", False)
        cls._CACHE_FORMAT = preset.get("_CACHE_FORMAT", "chunks")
        cls._init_adapters()

    ### PRIVATE UTILITIES START
    @classmethod
    def _resolve_provider(cls, provider: str) -> str:
        lower = provider.lower()
        if lower in cls.PROVIDER_ALIASES:
            return cls.PROVIDER_ALIASES[lower]
        if lower in cls.SUPPORTED_PROVIDERS:
            return lower
        raise ValueError(f"Unknown provider: {provider}")

    @classmethod
    def _init_adapters(cls):
        cls._ADAPTERS = {
            "anthropic": _LLM_AnthropicAdapter(),
            "openai": _LLM_OpenAICompatAdapter(),
            "google": _LLM_GoogleAdapter(),
            "xai": _LLM_OpenAICompatAdapter(api_url="https://api.x.ai/v1/chat/completions"),
            "openrouter": _LLM_OpenRouterAdapter()
        }

    @classmethod
    def _get_adapter(cls) -> _LLM_ProviderAdapter:
        if not cls.PROVIDER:
            raise ValueError("Provider not set. Call use_provider() first.")
        if cls.PROVIDER not in cls._ADAPTERS:
            cls._init_adapters()
        return cls._ADAPTERS[cls.PROVIDER]

    @classmethod
    def _get_model_tool_support(cls) -> int:
        return cls._MODEL_TOOL_SUPPORT.get(cls.MODEL, cls.TOOL_SUPPORT_UNTESTED)

    @classmethod
    def _set_model_tool_support(cls, status: int):
        cls._MODEL_TOOL_SUPPORT[cls.MODEL] = status

    @classmethod
    def _tools_to_system_message(cls) -> str:
        if not cls._TOOLS:
            return ""
        lines = [
            "You have access to the following tools. To use a tool, respond with a JSON object in this exact format:",
            ""]
        lines.append('{"tool_call": {"name": "tool_name", "arguments": {"arg1": "value1"}}}')
        lines.append("")
        lines.append("Available tools:")
        lines.append("")
        for tool in cls._TOOLS.values():
            lines.append(f"**{tool.name}**")
            lines.append(f"Description: {tool.description}")
            params = tool.parameters.get("properties", {})
            required = tool.parameters.get("required", [])
            if params:
                lines.append("Parameters:")
                for param_name, param_info in params.items():
                    req_str = " (required)" if param_name in required else " (optional)"
                    lines.append(f"  - {param_name}: {param_info.get('type', 'string')}{req_str}")
            lines.append("")
        lines.append(
            "If you need to use a tool, respond ONLY with the JSON object. After receiving the tool result, continue your response.")
        return "\n".join(lines)

    @classmethod
    def _parse_tool_call_from_response(cls, text: str) -> tuple:
        try:
            match = re.search(r'\{[\s\S]*"tool_call"[\s\S]*\}', text)
            if match:
                data = json.loads(match.group())
                if "tool_call" in data:
                    tc = data["tool_call"]
                    return tc.get("name"), tc.get("arguments", {})
        except (json.JSONDecodeError, KeyError):
            pass
        return None, None

    @classmethod
    def _process_thoughts_in_text(cls, text: str) -> str:
        if not cls.SHOW_THOUGHTS:
            for start_pattern, end_pattern in cls.THOUGHT_PATTERNS:
                pattern = re.escape(start_pattern) + r'[\s\S]*?' + re.escape(end_pattern)
                text = re.sub(pattern, '', text)
            return text
        for start_pattern, end_pattern in cls.THOUGHT_PATTERNS:
            if start_pattern in text:
                text = text.replace(start_pattern, cls.THOUGHTS_START_MARKER)
                text = text.replace(end_pattern, cls.THOUGHTS_END_MARKER)
        return text

    @classmethod
    def _process_thoughts_streaming(cls, chunk: str) -> str:
        cls._THOUGHT_BUFFER += chunk
        output = ""
        while True:
            if cls._IN_THOUGHT_BLOCK:
                if cls._CURRENT_THOUGHT_END in cls._THOUGHT_BUFFER:
                    end_idx = cls._THOUGHT_BUFFER.index(cls._CURRENT_THOUGHT_END)
                    thought_content = cls._THOUGHT_BUFFER[:end_idx]
                    cls._THOUGHT_BUFFER = cls._THOUGHT_BUFFER[end_idx + len(cls._CURRENT_THOUGHT_END):]
                    cls._IN_THOUGHT_BLOCK = False
                    if cls.SHOW_THOUGHTS:
                        output += thought_content + cls.THOUGHTS_END_MARKER
                    cls._CURRENT_THOUGHT_END = None
                    continue
                else:
                    if cls.SHOW_THOUGHTS:
                        output += cls._THOUGHT_BUFFER
                    cls._THOUGHT_BUFFER = ""
                    break
            found_start = False
            for start_pattern, end_pattern in cls.THOUGHT_PATTERNS:
                if start_pattern in cls._THOUGHT_BUFFER:
                    start_idx = cls._THOUGHT_BUFFER.index(start_pattern)
                    output += cls._THOUGHT_BUFFER[:start_idx]
                    if cls.SHOW_THOUGHTS:
                        output += cls.THOUGHTS_START_MARKER
                    cls._THOUGHT_BUFFER = cls._THOUGHT_BUFFER[start_idx + len(start_pattern):]
                    cls._IN_THOUGHT_BLOCK = True
                    cls._CURRENT_THOUGHT_END = end_pattern
                    found_start = True
                    break
            if not found_start:
                maybe_partial = False
                for start_pattern, _ in cls.THOUGHT_PATTERNS:
                    for i in range(1, len(start_pattern)):
                        if cls._THOUGHT_BUFFER.endswith(start_pattern[:i]):
                            output += cls._THOUGHT_BUFFER[:-i]
                            cls._THOUGHT_BUFFER = cls._THOUGHT_BUFFER[-i:]
                            maybe_partial = True
                            break
                    if maybe_partial:
                        break
                if not maybe_partial:
                    output += cls._THOUGHT_BUFFER
                    cls._THOUGHT_BUFFER = ""
                break
        return output

    @classmethod
    def _reset_thought_state(cls):
        cls._IN_THOUGHT_BLOCK = False
        cls._CURRENT_THOUGHT_END = None
        cls._THOUGHT_BUFFER = ""

    @classmethod
    def _register_tool(cls, func: Callable, name: str = None):
        tool_name = name or func.__name__
        schema = cls._build_tool_schema(func)
        cls._TOOLS[tool_name] = _LLM_ToolDef(
            name=tool_name,
            description=schema.get("description", ""),
            parameters=schema.get("parameters", {}),
            handler=func,
            source="direct"
        )

    @classmethod
    def _build_tool_schema(cls, func: Callable) -> dict:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
            properties[param_name] = {"type": param_type}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        return {
            "description": doc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    @classmethod
    def _execute_tool(cls, name: str, args: dict) -> Any:
        if name not in cls._TOOLS:
            return {"error": f"Tool '{name}' not found"}
        tool = cls._TOOLS[name]
        try:
            return tool.handler(**args)
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def _format_tool_call_display(cls, name: str, args: dict) -> str:
        args_str = json.dumps(args)
        if len(args_str) > cls.TOOL_CALL_PARAM_LENGTH:
            args_str = args_str[:cls.TOOL_CALL_PARAM_LENGTH] + "..."
        return f"[Tool: {name}({args_str})]"

    @classmethod
    def _load_mcp_config(cls, path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def _connect_mcp_server(cls, name: str, config: dict):
        cls._MCP_SERVERS[name] = {
            "config": config,
            "connected": False,
            "tools": []
        }

    @classmethod
    def _get_or_create_chat(cls, chat_id: str = None) -> _LLM_Chat:
        cid = chat_id or cls.ACTIVE_CHAT_ID
        if not cid:
            cid = cls.generate_chat()
            cls.ACTIVE_CHAT_ID = cid
        if cid not in cls._CHATS:
            cls._CHATS[cid] = _LLM_Chat(cid)
        return cls._CHATS[cid]

    @classmethod
    def _append_message(cls, chat_id: str, role: str, content):
        chat = cls._get_or_create_chat(chat_id)
        chat.messages.append({"role": role, "content": content})
        if isinstance(content, str):
            chat.token_count += cls.estimate_tokens(content)

    @classmethod
    def _build_messages(cls, chat_id: str) -> list:
        chat = cls._get_or_create_chat(chat_id)
        return list(chat.messages)

    @classmethod
    def _get_tools_list(cls) -> list:
        return list(cls._TOOLS.values())

    @classmethod
    def _get_tokenizer(cls):
        if cls._TOKENIZER is None:
            if cls.TOKENIZER_PATH:
                cls._TOKENIZER = tiktoken.get_encoding(cls.TOKENIZER_PATH)
            else:
                cls._TOKENIZER = tiktoken.get_encoding(cls.DEFAULT_TOKENIZER)
        return cls._TOKENIZER

    @classmethod
    def _send_sync(cls, message: str) -> str:
        chat = cls._get_or_create_chat(cls.ACTIVE_CHAT_ID)
        cls._append_message(chat.chat_id, "user", message)
        adapter = cls._get_adapter()
        tool_support = cls._get_model_tool_support()
        use_system_msg_tools = tool_support == cls.TOOL_SUPPORT_SYSTEM_MSG
        tools = []
        system_msg = None
        if cls._TOOLS:
            if use_system_msg_tools:
                system_msg = cls._tools_to_system_message()
            else:
                tools = adapter.format_tools(cls._get_tools_list())
        messages = cls._build_messages(chat.chat_id)
        if system_msg:
            messages = [{"role": "system", "content": system_msg}] + messages
        messages = adapter.format_messages(messages)
        full_response = ""
        is_first_attempt = not cls._FIRST_MESSAGE_SENT
        while True:
            try:
                if use_system_msg_tools:
                    response = adapter.call_api(messages, [], cls.API_KEY, cls.MODEL)
                else:
                    response = adapter.call_api(messages, tools, cls.API_KEY, cls.MODEL)
                if is_first_attempt and not use_system_msg_tools and cls._TOOLS:
                    cls._set_model_tool_support(cls.TOOL_SUPPORT_WORKS)
                cls._FIRST_MESSAGE_SENT = True
            except requests.exceptions.HTTPError as e:
                if is_first_attempt and e.response.status_code in (400,
                                                                   404) and cls._TOOLS and not use_system_msg_tools:
                    cls._set_model_tool_support(cls.TOOL_SUPPORT_SYSTEM_MSG)
                    use_system_msg_tools = True
                    system_msg = cls._tools_to_system_message()
                    messages = cls._build_messages(chat.chat_id)
                    messages = [{"role": "system", "content": system_msg}] + messages
                    messages = adapter.format_messages(messages)
                    tools = []
                    continue
                raise
            text, tool_calls = adapter.parse_response(response)
            processed_text = cls._process_thoughts_in_text(text)
            full_response += processed_text
            if use_system_msg_tools:
                tool_name, tool_args = cls._parse_tool_call_from_response(text)
                if tool_name and tool_name in cls._TOOLS:
                    if cls.SHOW_TOOL_CALLS:
                        full_response += cls._format_tool_call_display(tool_name, tool_args) + "\n"
                    result = cls._execute_tool(tool_name, tool_args)
                    result_str = json.dumps(result) if not isinstance(result, str) else result
                    messages.append({"role": "assistant", "content": text})
                    messages.append({"role": "user", "content": f"Tool result: {result_str}"})
                    messages = adapter.format_messages(messages)
                    continue
                else:
                    break
            else:
                if not adapter.is_tool_call(response) or not tool_calls:
                    break
                tool_results = []
                tool_display = ""
                for tc in tool_calls:
                    if cls.SHOW_TOOL_CALLS:
                        tool_display += cls._format_tool_call_display(tc.name, tc.arguments) + "\n"
                    result = cls._execute_tool(tc.name, tc.arguments)
                    tool_results.append(result)
                if cls.SHOW_TOOL_CALLS and tool_display:
                    full_response += tool_display
                assistant_msg = adapter.get_assistant_message(response)
                messages.append(assistant_msg)
                tool_result_msg = adapter.format_tool_results(tool_calls, tool_results)
                if isinstance(tool_result_msg, list):
                    messages.extend(tool_result_msg)
                else:
                    messages.append(tool_result_msg)
        cls._append_message(chat.chat_id, "assistant", full_response)
        return full_response

    @classmethod
    def _send_stream_sync(cls, message: str) -> Generator:
        chat = cls._get_or_create_chat(cls.ACTIVE_CHAT_ID)
        cls._append_message(chat.chat_id, "user", message)
        adapter = cls._get_adapter()
        tool_support = cls._get_model_tool_support()
        use_system_msg_tools = tool_support == cls.TOOL_SUPPORT_SYSTEM_MSG
        tools = []
        system_msg = None
        if cls._TOOLS:
            if use_system_msg_tools:
                system_msg = cls._tools_to_system_message()
            else:
                tools = adapter.format_tools(cls._get_tools_list())
        messages = cls._build_messages(chat.chat_id)
        if system_msg:
            messages = [{"role": "system", "content": system_msg}] + messages
        messages = adapter.format_messages(messages)
        full_response = ""
        is_first_attempt = not cls._FIRST_MESSAGE_SENT
        while True:
            collected_text = ""
            cls._STREAM_TOOL_CALLS = []
            cls._STREAM_FULL_RESPONSE = None
            cls._reset_thought_state()
            try:
                stream_tools = [] if use_system_msg_tools else tools
                stream_iter = adapter.call_api_stream(messages, stream_tools, cls.API_KEY, cls.MODEL)
                for chunk in stream_iter:
                    text = adapter.parse_stream_chunk(chunk)
                    if text:
                        collected_text += text
                        processed_text = cls._process_thoughts_streaming(text)
                        if processed_text:
                            full_response += processed_text
                            yield processed_text
                    if chunk.get("type") == "content_block_start":
                        block = chunk.get("content_block", {})
                        if block.get("type") == "tool_use":
                            cls._STREAM_TOOL_CALLS.append({
                                "id": block.get("id"),
                                "name": block.get("name"),
                                "arguments_str": ""
                            })
                    if chunk.get("type") == "content_block_delta":
                        delta = chunk.get("delta", {})
                        if delta.get("type") == "input_json_delta" and cls._STREAM_TOOL_CALLS:
                            cls._STREAM_TOOL_CALLS[-1]["arguments_str"] += delta.get("partial_json", "")
                    if chunk.get("type") == "message_delta":
                        if chunk.get("delta", {}).get("stop_reason") == "tool_use":
                            cls._STREAM_FULL_RESPONSE = chunk
                if is_first_attempt and not use_system_msg_tools and cls._TOOLS:
                    cls._set_model_tool_support(cls.TOOL_SUPPORT_WORKS)
                cls._FIRST_MESSAGE_SENT = True
            except requests.exceptions.HTTPError as e:
                if is_first_attempt and e.response.status_code in (400,
                                                                   404) and cls._TOOLS and not use_system_msg_tools:
                    cls._set_model_tool_support(cls.TOOL_SUPPORT_SYSTEM_MSG)
                    use_system_msg_tools = True
                    system_msg = cls._tools_to_system_message()
                    messages = cls._build_messages(chat.chat_id)
                    messages = [{"role": "system", "content": system_msg}] + messages
                    messages = adapter.format_messages(messages)
                    tools = []
                    continue
                raise
            if use_system_msg_tools:
                tool_name, tool_args = cls._parse_tool_call_from_response(collected_text)
                if tool_name and tool_name in cls._TOOLS:
                    if cls.SHOW_TOOL_CALLS:
                        display = cls._format_tool_call_display(tool_name, tool_args)
                        full_response += display + "\n"
                        yield display + "\n"
                    result = cls._execute_tool(tool_name, tool_args)
                    result_str = json.dumps(result) if not isinstance(result, str) else result
                    messages.append({"role": "assistant", "content": collected_text})
                    messages.append({"role": "user", "content": f"Tool result: {result_str}"})
                    messages = adapter.format_messages(messages)
                    continue
                else:
                    break
            else:
                if not cls._STREAM_TOOL_CALLS:
                    break
                tool_calls = []
                for tc_data in cls._STREAM_TOOL_CALLS:
                    try:
                        args = json.loads(tc_data["arguments_str"]) if tc_data["arguments_str"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    tool_calls.append(_LLM_ToolCall(
                        id=tc_data["id"],
                        name=tc_data["name"],
                        arguments=args
                    ))
                tool_results = []
                for tc in tool_calls:
                    if cls.SHOW_TOOL_CALLS:
                        display = cls._format_tool_call_display(tc.name, tc.arguments)
                        full_response += display + "\n"
                        yield display + "\n"
                    result = cls._execute_tool(tc.name, tc.arguments)
                    tool_results.append(result)
                assistant_content = [{"type": "text", "text": collected_text}]
                for tc_data in cls._STREAM_TOOL_CALLS:
                    try:
                        args = json.loads(tc_data["arguments_str"]) if tc_data["arguments_str"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tc_data["id"],
                        "name": tc_data["name"],
                        "input": args
                    })
                messages.append({"role": "assistant", "content": assistant_content})
                tool_result_msg = adapter.format_tool_results(tool_calls, tool_results)
                if isinstance(tool_result_msg, list):
                    messages.extend(tool_result_msg)
                else:
                    messages.append(tool_result_msg)
                cls._STREAM_TOOL_CALLS = []
        cls._append_message(chat.chat_id, "assistant", full_response)

    @classmethod
    def _start_worker_thread(cls):
        def worker():
            while True:
                try:
                    request = cls._REQUEST_QUEUE.get(timeout=1)
                except queue.Empty:
                    continue
                chat_id = request.get("chat_id")
                message = request.get("message")
                is_stream = request.get("stream", False)
                old_active = cls.ACTIVE_CHAT_ID
                cls.ACTIVE_CHAT_ID = chat_id
                try:
                    if is_stream:
                        full_content = ""
                        for chunk in cls._send_stream_sync(message):
                            full_content += chunk
                            cls._add_to_cache(chat_id, chunk, False)
                            cls._fire_callbacks(chat_id, chunk, is_live=True)
                        cls._add_to_cache(chat_id, "", True)
                        cls._fire_callbacks(chat_id, full_content, is_live=False)
                    else:
                        response = cls._send_sync(message)
                        cls._add_to_cache(chat_id, response, True)
                        cls._fire_callbacks(chat_id, response, is_live=False)
                except Exception as e:
                    error_msg = f"[Error: {str(e)}]"
                    cls._add_to_cache(chat_id, error_msg, True)
                finally:
                    cls.ACTIVE_CHAT_ID = old_active

        cls._WORKER_THREAD = threading.Thread(target=worker, daemon=True)
        cls._WORKER_THREAD.start()

    @classmethod
    def _add_to_cache(cls, chat_id: str, content: str, is_complete: bool):
        with cls._CACHE_LOCK:
            if cls._CACHE_FORMAT == cls.cache_types.MESSAGES and not is_complete:
                return
            normalized_content = content
            if cls._CACHE_FORMAT in [cls.cache_types.CHUNKS_1_CHAR, cls.cache_types.CHUNKS_10_CHAR,
                                     cls.cache_types.CHUNKS_50_CHAR, cls.cache_types.CHUNKS_100_CHAR]:
                size_map = {
                    cls.cache_types.CHUNKS_1_CHAR: 1,
                    cls.cache_types.CHUNKS_10_CHAR: 10,
                    cls.cache_types.CHUNKS_50_CHAR: 50,
                    cls.cache_types.CHUNKS_100_CHAR: 100
                }
                chunk_size = size_map.get(cls._CACHE_FORMAT, 1)
                normalized_content = cls._normalize_chunks(content, chunk_size)
            entry = _LLM_CacheEntry(chat_id, normalized_content, is_complete)
            cls._RESPONSE_CACHE.append(entry)

    @classmethod
    def _normalize_chunks(cls, content: str, size: int) -> str:
        return content

    @classmethod
    def _fire_callbacks(cls, chat_id: str, content: str, is_live: bool):
        handlers = cls._LIVE_REPLY_HANDLERS if is_live else cls._REPLY_HANDLERS
        global_handlers = handlers.get(None, [])
        specific_handlers = handlers.get(chat_id, [])
        for handler in global_handlers + specific_handlers:
            try:
                handler(content)
            except Exception:
                pass
    ### PRIVATE UTILITIES END