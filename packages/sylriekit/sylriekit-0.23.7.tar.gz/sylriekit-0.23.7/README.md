## Sylriekit
A personal toolset I made for myself to speed up the creation of some random personal projects.

**Warning**: This is a personal project and may contain bugs or incomplete features. It is mainly coded for convenience over optimization. Use at your own risk.

---
## Tools
+ ### PHP-like tools:
  #### Constants
  - Immutable constants manager. Define values that cannot be modified or deleted after creation.
  #### InlinePython:
  - Python renderer for inline code blocks in files. (similar to php with `<?py ... ?>`)

+ ### AI-related tools:
  #### LLM
  - LLM API client supports OpenAI, Anthropic, xAI, Gemini, and OpenRouter. Handles chat sessions, tool calling, and MCP server integration.
  #### MCP
  - A simple FastMCP extension/wrapper. Adds some logging and error handling built-in tools for convenience. 
  #### TTS
  - Text-to-Speech tool uses ElevenLabs for the audio generation and the pip package miniaudio for playing the audio.

+ ### Execution and Automation:
  #### Template
  - Sandboxed Python execution engine using RestrictedPython with configurable profiles, pre-code injection, import whitelisting, timeout protection, and save/load support for templates with embedded profiles.
  #### Schedule
  - Scheduler for interval, daily, and file-watch tasks with registry management.
  #### Process
  - Subprocess wrapper for running commands with configurable timeouts, environment, shell usage, and output trimming while returning structured results.

+ ### Development Support:
  #### Log
  - Simple logging tool with Log.log(...) or automatic logging with decorators for functions.
  #### Cache
  - A simple function-based cache using decorators.
  #### Profile
  - Timing and profiling helper with context managers, decorators, and direct measurements plus optional memory tracking and stored records.

+ ### Web and GUI:
  #### Website
  - Flask web server with Gunicorn support. Features `<python>` tag rendering, function caching with JS bridge, session management, and API endpoints. Uses Redis for cross-worker session/rate-limit storage.
  #### Window
  - Desktop GUI applications using webviewpy. Supports HTML/CSS/JS with `<python>` tags for defining Python functions callable from JavaScript. Enables hybrid desktop apps with web technologies.
  #### SharedStore
  - Redis-backed storage for cross-worker data sharing. Handles sessions, rate limiting, and function caching. Used internally by Website but can be used standalone.

+ ### Other Tools:
  #### Files
  - File system utilities with searching, reading, editing, directory operations, grep, etc.
  #### API
  - HTTP request helper with configurable presets for headers, endpoints, API keys, and quick call execution returning structured responses.
  #### Git
  - Local git wrapper for managing repositories, branches, commits, and remotes.
  #### Security
  - Cryptography helper for RSA/Symmetric encryption, hashing, and JWT management.
  #### Database
  - Unified interface for interacting with SQLite, PostgreSQL, MySQL, and DynamoDB.

+ ### Languages:
  #### C
  - Compile and run C code from Python with automatic argument parsing and caching.
  #### GoLang
  - Compile and run Go code from Python with automatic argument parsing and caching.
  #### Rust
  - Compile and run Rust code from Python using Cargo with automatic argument parsing and caching.
  #### Nim
  - Compile and run Nim code from Python with automatic argument parsing and caching.

---

## Config
Each tool has class-level defaults that can be overridden via `load_config()`. Pass a dictionary/JSON where keys are tool names and values are dictionaries of settings (Settings/Variables not provided will use the tool's built-in defaults.)

Example config structure:
```
{
  "Files": {
    "MAX_DEPTH_DEFAULT": 42,
    "PATH_SEP": "/"
  }
}
``` 
using `sylriekit.load_config(config:dict)` will load the config for all tools, to centeralize the configuration of multiple tools.

and using `sylriekit.generate_default_config(file_name: str, include_tools="*")` will generate a file that will contain all (or just selected ones with `include_tools=["ToolName1", ...]`) of the configurable values and their defaults.


---

#### Other Stuff
- `sylriekit.tool_functions(tool_name: str) -> list[str]`: Returns all public functions available in a tool.
- `sylriekit.get_code(tool_name: str, function_name: str) -> str`: Returns the source code of a specific tool's function. Use `"*"` as the function name to get the entire source code of the tool.
- `sylriekit.help()`: Prints a short message for how to use the sylriekit's help-related functions.

---

### Change Log:
**0.23.7**:
 - Made the Database tool send back all auto-assigned values when creating a item.

**0.23.4-6**:
 - Attempting and fixing the InlinePython + Website linking of the use_class(key, class) so they work together

**0.23.3**:
 - Fixed req-data tag in the InlinePython tool to allow space delimed input for multiple checks
 - Added dotenv and a `SHOW_SYLRIEKIT_LANG_WARNINGS="True"` check for the language support to disable the warnings by default

**0.23.2**:
 - Added OpenAI's TTS models and COMB.AI's models to the TTS tool so they can be used with it too.

**0.23.1**:
 - Fixed some issues with the Window tool not loading images or files correctly

**0.23.0**:
 - Added four new tools for coding language support that allow C, GoLang, Rust, and Nim to be compiled in a __(LangaugeName)Cache__ folder and be callable from python.

**Previous change log entries are visible in the description of older versions**