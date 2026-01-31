# Code Cantation

_A safe, embeddable code executor for Python—usable both as a library and via a CLI._

---

## Features

- **Script execution**: Run arbitrary Python scripts with stdout capture.
- **Function execution**: Define functions in code snippets and invoke them (with or without parameters).
- **Safety checks**: Static AST-based analysis blocks imports of unsafe modules (e.g. `os`, `subprocess`) and calls to dangerous functions (`eval`, `exec`, etc.).
- **Error reporting**: Any runtime errors are captured and returned in the output object.
- **Process isolation**: Code runs in a separate process with configurable timeout and resource limits.
- **Dual usage**: Importable as a Python package, or installed as a `cantation` CLI tool. Server mode is optional.

---

## Installation

Install from PyPI (library + CLI):

```bash
pip install code-cantation
```

To include FastAPI/uvicorn for server mode (optional extra):
```bash
pip install code-cantation[server]
```

Or install from source in editable mode:

```bash
git clone https://github.com/your-repo/code-cantation.git
cd code-cantation
pip install -e .
```

---

## Usage as a Library

Import and invoke the `Executor` directly in your code:

```python
from code_cantation import Executor

exe = Executor()

# 1. Run a simple script:
script = """
a = 10
b = 20
print('sum =', a + b)
"""  # note: no `return` in script mode
result = exe.execute(code=script)
print("Console:", result.console_log)

# 2. Call a function without parameters:
func_no_args = """
def greet():
    print('hello')
    return 'hello'
"""
res2 = exe.execute(code=func_no_args, code_type="FUNCTION")
print("Return:", res2.captured_output)

# 3. Call a function with parameters:
func_with_args = """
def add(a, b):
    print('adding', a, b)
    return a + b
"""
res3 = exe.execute(
    code=func_with_args,
    code_type="FUNCTION",
    input_values=[5, 7]
)
print("Return:", res3.captured_output)

# 4. Restrict file access to a specific folder:
restricted = exe.execute(
    code="open('data.txt', 'w').write('ok')",
    allowed_root="/sandbox/work"  # work_dir defaults to allowed_root
)
print("Error:", restricted.exec_error)

# 5. Check safety violation:
unsafe = "import requests"
res4 = exe.execute(code=unsafe)
print("Safety error:", res4.safety_violation)
```

The `execute(...)` method returns a `CodeExecutorOutput` object with the following attributes:

- `console_log` (str): Captured stdout from the snippet.
- `captured_output` (any): Return value of a FUNCTION snippet (or `None` for scripts).
- `exec_error` (str): Runtime error message if execution failed.
- `safety_violation` (str): Description if safety checks failed.

By default, execution runs in a separate process with a 5s timeout, 5s CPU limit,
and a 256MB memory limit. These can be overridden per call.
If `allowed_root` is set, file access is restricted to that directory (read/write),
which can also block imports from outside the allowed root.

---

## Usage via CLI

Once installed, the `cantation` command is available on your PATH. All options mirror the library’s `Executor.execute()` parameters and always emit a JSON representation of the `CodeExecutorOutput`.

```bash
cantation [--code CODE  | --file FILE]
          [--no-safety]
          [--code-type {SCRIPT,FUNCTION}]
          [--input JSON_LIST]
          [--unsafe-modules MODULE [MODULE ...]]
          [--unsafe-functions FUNC [FUNC ...]]
          [--override-default-safety]
          [--timeout-sec SECONDS]
          [--cpu-time-limit-sec SECONDS]
          [--memory-limit-mb MB]
          [--allowed-root DIR]
          [--work-dir DIR]
```

### Common Examples

1. **Run an inline script**
   ```bash
   cantation \
     --code "print('Hello from CLI'); x = 1 + 2; print('x =', x)"
   ```
   **Output**
   ```json
   {
     "console_log": "Hello from CLI x = 3",
     "captured_output": null,
     "exec_error": null,
     "safety_violation": null
   }
   ```

2. **Execute a Python file**
   ```bash
   cantation --file path/to/script.py
   ```

3. **Invoke a no-arg function**
   ```bash
   cantation \
     --code "def greet():
    print('Hi there'); return 'Hi'" \
     --code-type FUNCTION
   ```
   **Output**
   ```json
   {
     "console_log": "Hi there",
     "captured_output": "Hi",
     "exec_error": null,
     "safety_violation": null
   }
   ```

4. **Invoke a function with parameters**
   ```bash
   cantation \
     --code "def add(a, b):
    return a + b" \
     --code-type FUNCTION \
     --input '[5, 7]'
   ```
   **Output**
   ```json
   {
     "console_log": "",
     "captured_output": 12,
     "exec_error": null,
     "safety_violation": null
   }
   ```

5. **Disable safety checks**
   ```bash
   cantation --file my_script.py --no-safety
   ```

6. **Override unsafe modules/functions**
   ```bash
   # Disallow use of 'os' and 'eval'
   cantation --file my_script.py \
     --unsafe-modules os \
     --unsafe-functions eval
   ```  
   
7. **Install Libraries Required For Code Execution**
   ```bash
   cantation \
    --install pyfiglet \
   --code "import pyfiglet; print(pyfiglet.figlet_format('Hello'))"

   ```
8. **Set resource limits**
   ```bash
   cantation \
     --code "print('hello')" \
     --timeout-sec 3 \
     --cpu-time-limit-sec 2 \
     --memory-limit-mb 128
   ```
   Set any of these to `0` to disable that limit.

9. **Restrict file access**
   ```bash
   cantation \
     --code "open('data.txt','w').write('ok')" \
     --allowed-root /sandbox/work
   ```

---

## Usage As Server  
Code Cantation can be run as a server/rest api. The server execute one code at time and therefore has 
an internal queue for requests.   

Server mode requires the optional FastAPI/uvicorn extras:
```bash
pip install code-cantation[server]
```
If you only installed the core package, `cantation --server` will fail with a message
telling you to install the server extras.

### Start server (basic)

```bash
cantation --server --install pyfiglet fastapi uvicorn \
          --host 127.0.0.1 --port 9000
```   
If you already installed the server extra, you can omit `--install fastapi uvicorn`.

### Start server with allowed root (client-enforced)

The server reads `allowed_root` and `work_dir` from each request. Use these in your API payloads
to restrict file access to a specific directory.

### Start server securely (no Docker)

Run as a dedicated user with a restricted working directory:
```bash
sudo useradd -m cantation
sudo mkdir -p /srv/cantation/work
sudo chown -R cantation:cantation /srv/cantation
sudo -u cantation cantation --server --host 127.0.0.1 --port 9000
```

Optionally apply OS limits in the same shell:
```bash
ulimit -t 5 -v 1048576 -n 128 -u 64
sudo -u cantation cantation --server --host 127.0.0.1 --port 9000
```

### Start server with Docker hardening (recommended)

```bash
docker run --rm -it \
  --read-only \
  --cap-drop=ALL \
  --security-opt no-new-privileges \
  --user 1000:1000 \
  --pids-limit 256 \
  --memory 1g \
  --cpus 2 \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -p 9000:9000 \
  -v /host/allowed:/sandbox/work:rw \
  your-image \
  cantation --server --host 0.0.0.0 --port 9000
```

### Call The API

```bash
curl -X POST http://127.0.0.1:9000/execute \
     -H "Content-Type: application/json" \
     -d '{
           "code": "import pyfiglet; print(pyfiglet.figlet_format(\"API\"))",
           "timeout_sec": 3,
           "cpu_time_limit_sec": 2,
           "memory_limit_mb": 128,
           "allowed_root": "/sandbox/work",
           "work_dir": "/sandbox/work"
         }'
```
Use `0` to disable a limit per request.

Recommended: always set `allowed_root` (and optionally `work_dir`) in requests to
restrict file access to a specific directory. Combine this with container-level
restrictions for stronger isolation.

---

## Docker Run Recipes

These examples assume your app is installed inside the container and that you want to
restrict file access to a single host directory mounted at `/sandbox/work`.

### Library / CLI (interactive)

```bash
docker run --rm -it \
  --read-only \
  --cap-drop=ALL \
  --security-opt no-new-privileges \
  --user 1000:1000 \
  --pids-limit 128 \
  --memory 512m \
  --cpus 1 \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -v /host/allowed:/sandbox/work:rw \
  your-image \
  cantation \
    --code "open('data.txt','w').write('ok')" \
    --allowed-root /sandbox/work
```

### FastAPI Server

```bash
docker run --rm -it \
  --read-only \
  --cap-drop=ALL \
  --security-opt no-new-privileges \
  --user 1000:1000 \
  --pids-limit 256 \
  --memory 1g \
  --cpus 2 \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -p 9000:9000 \
  -v /host/allowed:/sandbox/work:rw \
  your-image \
  cantation --server --host 0.0.0.0 --port 9000
```

Note: ensure your image includes the server extra (`pip install code-cantation[server]`).

Recommended: set `allowed_root` to `/sandbox/work` in your requests so file access
is restricted to the mounted directory.





## How It Works
> If you don't provide the code type, the library will try to figure it out itself.  

### Executor Code Flow Logic
![Internal Code Flow](code-executor-flow.png "Internal Code Flow Logic")


## Testing

A test script (`test/test.py`) is provided to exercise:

1. Script execution
2. Function execution (no args)
3. Function execution (with args)
4. Safety-check failures
5. CLI behaviors

Run:

```bash
python test/test.py
```

---

## Contributing

1. Fork the repo and create your branch: `git checkout -b feature/YourFeature`
2. Make your changes & add tests
3. Run tests: `python sample_test.py`
4. Submit a pull request

---


