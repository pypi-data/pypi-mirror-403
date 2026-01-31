# PyxBlend - Ultimate Python Obfuscation Suite

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

`pyxblend` is a professional-grade Python code protection suite designed for developers who need to secure their intellectual property. It moves beyond simple obfuscation by integrating advanced cryptographic layering and native Cython compilation.

## Installation

```bash
pip install pyxblend
```

## Quick Start & Examples

Here is how to use each encryption method to protect your Python scripts.

### Basic Setup

First, import the library and initialize the encryptor:

```python
from pyxblend import PyxBlend

# Initialize the encryptor
encryptor = PyxBlend()

# The code you want to protect
source_code = """
def secret_function():
    print("This is highly confidential code!")
    print("Logic hidden from prying eyes.")

if __name__ == "__main__":
    secret_function()
"""
```

### Method 1: Enhanced Compression (m1)
**Best for:** General purpose obfuscation where file size and speed are important.

```python
# Encrypt using Method 1
encrypted_code = encryptor.encrypt(source_code, method=1)

# Save to a new file
with open("protected_script_m1.py", "w") as f:
    f.write(encrypted_code)

print("Saved protected_script_m1.py")
```

### Method 2: Junk Code & Base85 (m2)
**Best for:** Confusing static analysis tools and decompilers by injecting junk code.

```python
# Encrypt using Method 2
encrypted_code = encryptor.encrypt(source_code, method=2)

# Save to a new file
with open("protected_script_m2.py", "w") as f:
    f.write(encrypted_code)

print("Saved protected_script_m2.py")
```

### Method 3: Pure Cython Compilation (m3) - ULTRA SECURE
**Best for:** Production releases. This compiles your Python code into a C-extension binary.
*Note: This method generates a loader that compiles the code on the target machine. Ensure `gcc` is available.*

```python
# Encrypt using Method 3
encrypted_code = encryptor.encrypt(source_code, method=3)

if encrypted_code:
    # Save to a new file
    with open("protected_script_m3.py", "w") as f:
        f.write(encrypted_code)
    print("Saved protected_script_m3.py")
else:
    print("Encryption failed! Ensure Cython and GCC are installed.")
```

### Advanced: Random Layering
**Best for:** Maximum confusion. Apply multiple layers of random obfuscation before the final lock.

```python
# Apply 5 layers of random m1/m2 encryption
layered_code = encryptor.random_encrypt(source_code, iterations=5)

# Then apply the final Cython lock (Method 3)
final_product = encryptor.encrypt(layered_code, method=3)

with open("ultra_secure_script.py", "w") as f:
    f.write(final_product)
```

## Methods Guide

| Method | Description | Security Level |
|--------|-------------|----------------|
| **m1** | **Enhanced Compression**: Variable renaming + Lambda wrapping + LZMA/Base64. | Medium |
| **m2** | **Obfuscation**: Junk code injection + Minification + Base85 encoding. | Medium-High |
| **m3** | **Native Compilation**: Encrypts source, converts to C via Cython, compiles to binary. | **Ultra High** |

## Requirements

- Python 3.8+
- `cython` (for method 3)
- `python_minifier`
- GCC or Clang (for method 3 compilation)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
