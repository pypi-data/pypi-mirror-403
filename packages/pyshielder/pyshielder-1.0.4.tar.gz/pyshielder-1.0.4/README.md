# pyshielder - Python Code Shield

![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

`pyshielder` is a powerful tool to protect your Python code. It combines advanced multi-layer bytecode obfuscation with native compilation to create highly secure executable scripts.

## Features

- **Advanced Layering**: Compiles code to bytecode, serializes with Marshal, compresses with Zlib, encodes with Base64, and obfuscates the structure.
- **Strong Encryption**: Wraps the obfuscated payload in a secure loader encrypted with rolling-key XOR.
- **Native Compilation**: The final loader is compiled into a native C binary using Cython and GCC, executing directly in memory.
- **Tamper Resistant**: No original source code or simple bytecode is visible. Reverse engineering requires reconstructing multiple layers of obscured logic.
- **Self-contained**: The output is a single Python script that self-compiles and executes.

## Installation

```bash
pip install pyshielder
```

*Note: You need `gcc` (or `clang`) and `python3-dev` installed on your system to use the encryption tool and to run the generated protected scripts.*

## Usage

### Command Line Interface

You can use `pyshielder` directly from the command line:

```bash
# Encrypt a file
pyshielder my_script.py

# Specify output directory
pyshielder my_script.py protected_script.py
```

### Python API

```python
from pyshielder import encrypt

# Encrypt a script string
code = "print('Hello, protected world!')"
loader_code = encrypt(code)

# Save the loader to a file
with open("protected_script.py", "w") as f:
    f.write(loader_code)
```

## License

MIT License - see [LICENSE](LICENSE) for details.
