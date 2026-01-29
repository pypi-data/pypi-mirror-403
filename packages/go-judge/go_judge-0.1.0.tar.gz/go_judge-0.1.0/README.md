# go-judge-py

A Pythonic wrapper around [go-judge](https://github.com/criyle/go-judge) that provides **self-managing, lightweight, rootless containers** for secure code execution on Linux.

Unlike standard API clients, `go-judge-py` handles the entire lifecycle: it automatically downloads the sandbox binary, builds a root filesystem (rootfs) from official Linux distribution images (Debian, Alpine, Arch, Fedora), and manages the sandbox server for you.

**Ideal for:**
- 🛡️ **Verifying AI-generated code** (LLM code interpreters)
- ⚖️ **Online Judge systems**
- 🏫 **Computer Science Education** (grading scripts)

## ✨ Features

- **Zero-Dependency Setup**: Automatically fetches the `go-judge` binary and builds the execution environment.
- **Multi-Distro Support**: Create environments based on **Debian**, **Alpine**, **Arch Linux**, or **Fedora**.
- **Rootless & Secure**: Runs entirely in user namespaces (no `sudo` required) using `unshare`.
- **Parallel Execution**: Native support for batch processing with concurrent requests.
- **Resource Control**: Fine-grained limits on CPU, Memory, and Process count.

## 📦 Installation

```bash
pip install go-judge
# or with uv
uv add go-judge
```

*Requirements: Linux system with `unshare` enabled (modern Kernels default).*

### 1. Basic Usage (Python & C++)

The library comes with default configurations for common languages.

```python
from go_judge import Sandbox

# Automatically builds a Debian environment with GCC and Python installed
# This might take a minute the first time to download the rootfs
with Sandbox("standard-env", distribution="debian", packages=["g++", "python3"]) as sb:
    # Run Python
    res = sb.run("python", "print('Hello from the Sandbox!')")
    print(res["stdout"])  # Output: Hello from the Sandbox!

    # Run C++ (Compiles and Executes)
    cpp_code = """
    #include <iostream>
    int main() { std::cout << "Fast C++" << std::endl; }
    """
    res = sb.run("cpp", cpp_code)
    print(res["stdout"])  # Output: Fast C++
```

### 2. Custom Languages & Resource Limits

You can register custom languages (like C) and set strict resource limits.

```python
from go_judge import Sandbox

with Sandbox("custom-env", distribution="debian", packages=["gcc"]) as sb:
    # Register C configuration
    sb.register_language("c", {
        "src_name": "main.c",
        "bin_name": "main",
        "compile": {
            "args": ["/usr/bin/gcc", "main.c", "-o", "main"],
            "env": ["PATH=/usr/bin:/bin"]
        },
        "run": {
            "args": ["./main"],
            "env": ["PATH=/usr/bin:/bin"]
        }
    })

    # Run with constraints: 100ms CPU time, 32MB Memory
    result = sb.run(
        "c", 
        "int main() { return 0; }",
        exec_cpu_limit_ns=100_000_000,
        exec_memory_limit_b=33_554_432
    )

```

### 3. High-Performance Batch Processing

Execute code against multiple inputs in parallel using the built-in thread pool.

```python
inputs = ["1 1", "2 2", "10 20"] # stdin for each test case
code = """
a, b = map(int, input().split())
print(a + b)
"""

with Sandbox("py-worker") as sb:
    # Returns a list of results, preserving order
    results = sb.run_multiple("python", code, inputs)
    
    for res in results:
        print(f"Status: {res['status']}, Output: {res['stdout'].strip()}")
```

## 🛠️ Supported Distributions

`go-judge-py` pulls metadata from the [Linux Containers (LXC)](https://images.linuxcontainers.org/) project to build environments.

| Distro | Keyword | Best For |
| --- | --- | --- |
| **Alpine** | `alpine` | Ultra-lightweight, fast startup. |
| **Debian** | `debian` | Compatibility, standard glibc. |
| **Fedora** | `fedora` | Bleeding edge packages. |
| **Arch** | `arch` | Rolling release updates. |

Example:

```python
# Use a specific version of Debian
sb = Sandbox("old-stable", distribution="debian", release="bullseye")
```

## 💻 Development

Clone the repository and set up the environment using `uv`.

```bash
# Run integration tests (requires Linux)
uv run pytest -s tests/test_integration.py
```
