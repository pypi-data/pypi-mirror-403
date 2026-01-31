import os
import shutil
import subprocess
import hashlib
import random
import string
import sys
import argparse
import base64
import zlib
import marshal
import time
from datetime import datetime

class PyShielder:
    def __init__(self):
        pass

    def _generate_random_string(self, length):
        letters = string.ascii_lowercase
        # Ensure start with a letter for valid module names
        return random.choice(string.ascii_lowercase) + ''.join(random.choice(letters + string.digits) for _ in range(length - 1))

    def _generate_strong_key(self, length=256):
        chars = string.ascii_letters + string.digits + string.punctuation
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
        return hashlib.sha512(key.encode()).hexdigest()

    def _advanced_layer_obfuscation(self, code):
        """
        Applies multiple layers of encoding including Zlib, Base64, and Marshal.
        Matches the 'Russian Doll' technique to make static analysis extremely difficult.
        """
        try:
            # Layer 1: Compile original source
            compiled_1 = compile(code, f'<pyshielder_core>', 'exec')
            serialized_1 = marshal.dumps(compiled_1)
            
            # Layer 2: Compress
            compressed_1 = zlib.compress(serialized_1)
            
            # Layer 3: Create a script that decompresses and runs Layer 2
            # We compile THIS script to bytecode so the compression logic is hidden
            loader_2 = f"import zlib, marshal; exec(marshal.loads(zlib.decompress({compressed_1!r})))"
            compiled_2 = compile(loader_2, f'<pyshielder_loader>', 'exec')
            serialized_2 = marshal.dumps(compiled_2)
            
            # Layer 4: Base64 Encode the serialized Layer 3
            encoded_3 = base64.b64encode(serialized_2).decode('utf-8')
            
            # Layer 5: "Vector" obfuscation style (from user snippet)
            # We create a dummy byte array that decodes to the source string
            # This distracts from the actual payload
            
            # Generates a random variable name
            var_name = self._generate_random_string(6)
            
            decoder_script = f"""
import base64, marshal
{var_name} = "{encoded_3}"
exec(marshal.loads(base64.b64decode({var_name})))
"""
            return decoder_script
            
        except Exception as e:
            print(f"Error during obfuscation layers: {e}")
            return None

    def _obfuscate_source(self, code):
        """
        Encrypts the source code using XOR with a rolling key derived from SHA-512.
        Returns the Python code string that decrypts and executes it.
        """
        # First apply the advanced layering
        layered_code = self._advanced_layer_obfuscation(code)
        if not layered_code:
            return None
            
        key = self._generate_strong_key()
        byte_array = bytearray(layered_code.encode('utf-8'))
        key_bytes = key.encode('utf-8')
        encrypted = bytearray()
        
        # Enhanced XOR with index dependency and key rolling
        key_len = len(key_bytes)
        for i, b in enumerate(byte_array):
            # Rotate key usage based on index
            k = key_bytes[i % key_len]
            # Simple rolling XOR
            encrypted.append(b ^ k)
            
        hex_encoded = encrypted.hex()
        
        # The obfuscated loader logic (this goes INTO the C file eventually)
        obfuscated = f'''
import hashlib
import builtins

def _d():
    _k = "{key}"
    _e = bytes.fromhex("{hex_encoded}")
    _kb = _k.encode('utf-8')
    _d = bytearray()
    _kl = len(_kb)
    for _i, _b in enumerate(_e):
        _d.append(_b ^ _kb[_i % _kl])
    return _d.decode('utf-8')

exec(compile(_d(), "<pyshielder>", "exec"))
'''
        return obfuscated

    def _remove_comments(self, content):
        """
        Aggressively removes C-style comments to reduce file size and readability.
        """
        out = []
        i = 0
        n = len(content)
        while i < n:
            # Check for block comment /* ... */
            if i + 1 < n and content[i] == '/' and content[i+1] == '*':
                i += 2
                while i + 1 < n and not (content[i] == '*' and content[i+1] == '/'):
                    i += 1
                i += 2
            # Check for line comment // ...
            elif i + 1 < n and content[i] == '/' and content[i+1] == '/':
                i += 2
                while i < n and content[i] != '\n':
                    i += 1
            else:
                out.append(content[i])
                i += 1
        return "".join(out)

    def _get_c_main(self, name_clean):
        # We need to make sure the C code can initialize properly as a module
        # This part handles Python 3 module initialization
        return f'''
#if PY_MAJOR_VERSION < 3
int main(int argc, char** argv) {{
#elif defined(WIN32) || defined(MS_WINDOWS)
int wmain(int argc, wchar_t **argv) {{
#else
static int __Pyx_main(int argc, wchar_t **argv) {{
#endif
    /* Boilerplate main function for embedding */
    if (argc && argv)
        Py_SetProgramName(argv[0]);
    Py_Initialize();
    if (argc && argv)
        PySys_SetArgv(argc, argv);
    {{
      PyObject* m = NULL;
      __pyx_module_is_main_{name_clean} = 1;
      #if PY_MAJOR_VERSION < 3
          init{name_clean}();
      #elif CYTHON_PEP489_MULTI_PHASE_INIT
          m = PyInit_{name_clean}();
      #else
          m = PyInit_{name_clean}();
      #endif
      if (PyErr_Occurred()) {{
          PyErr_Print();
          return 1;
      }}
      Py_XDECREF(m);
    }}
    Py_Finalize();
    return 0;
}}

/* Standard main entry point wrapper */
#if PY_MAJOR_VERSION >= 3 && !defined(WIN32) && !defined(MS_WINDOWS)
int main(int argc, char **argv) {{
    return __Pyx_main(argc, (wchar_t**)0); // Simplified for embedded usage
}}
#endif
'''

    def encrypt(self, code, output_file=None):
        temp_dir = f".pyshielder_temp_{self._generate_random_string(6)}"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        try:
            # 1. Encrypt the python source with advanced layering
            obfuscated_source = self._obfuscate_source(code)
            if not obfuscated_source:
                return None
            
            # 2. Create a temporary .py file with the encrypted source
            rand_name = self._generate_random_string(8)
            # Ensure valid python identifier for module name (start with letter, no digits at start)
            if rand_name[0].isdigit():
                rand_name = "mod_" + rand_name
                
            py_file = os.path.join(temp_dir, f"{rand_name}.py")
            
            # The .py file to be cythonized contains the decryption logic
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(f"import os\n{obfuscated_source}")
                
            # 3. Use Cython to compile .py -> .c
            # We use subprocess to call cython command line
            cmd = [
                sys.executable, '-m', 'cython', 
                py_file, 
                '--3str', 
                '-X', 'boundscheck=False',
                '-X', 'wraparound=False', 
                '-X', 'cdivision=True', 
                '-X', 'always_allow_keywords=False', 
                '-X', 'profile=False'
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: Cython compilation failed: {e.stderr.decode()}")
                return None
            except FileNotFoundError:
                 print("Error: Cython module not found. Please install it with 'pip install cython'")
                 return None

            # 4. Read the generated .c file
            c_file_path = os.path.join(temp_dir, f"{rand_name}.c")
            if not os.path.exists(c_file_path):
                # Sometimes cython outputs to current dir?
                c_file_path = f"{rand_name}.c"
                
            if not os.path.exists(c_file_path):
                print("Error: Could not find generated C file.")
                return None
                
            with open(c_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                c_content = f.read()
                
            # Cleanup local .c if it was generated in root
            if os.path.exists(f"{rand_name}.c"):
                os.remove(f"{rand_name}.c")

            # 5. Optimization & Cleanup of C code
            c_content = c_content.replace(
                '#define CYTHON_COMPILING_IN_CPYTHON 1',
                '#define CYTHON_COMPILING_IN_CPYTHON 1\n#define CYTHON_COMPRESS_STRINGS 0\n#define CYTHON_UNPACK_METHODS 0\n#define CYTHON_FAST_THREAD_STATE 0'
            )
            # Remove comments to reduce size and readability
            c_content = self._remove_comments(c_content)
            
            # 6. Generate the Loader Script
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            unique_id = hashlib.md5(timestamp.encode()).hexdigest()[:16]
            
            loader_script = f'''import os, sys, hashlib, platform, subprocess, base64, marshal, zlib

UID = "{unique_id}"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".pyshielder_cache", UID)
EXECUTE_FILE = os.path.join(CACHE_DIR, f"run_{{UID}}")
C_FILE = os.path.join(CACHE_DIR, f"src_{{UID}}.c")

def _setup_env():
    env = os.environ.copy()
    if 'PYTHONHOME' not in env:
        env['PYTHONHOME'] = sys.prefix
    return env

def _compile_and_run():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
        
    if os.path.exists(EXECUTE_FILE) and os.access(EXECUTE_FILE, os.X_OK):
        subprocess.call([EXECUTE_FILE], env=_setup_env())
        return

    C_SOURCE = r"""{c_content}"""
    with open(C_FILE, "w", encoding="utf-8") as f:
        f.write(C_SOURCE)
        
    py_version = f"{{sys.version_info.major}}.{{sys.version_info.minor}}"
    include_path = os.path.join(sys.prefix, "include", f"python{{py_version}}")
    if not os.path.exists(include_path):
        include_path = os.path.join(sys.prefix, "include", f"python{{py_version}}m")
        
    lib_path = os.path.join(sys.prefix, "lib")
    
    cmd = ["gcc", "-O3", "-fPIC", "-w", "-s", "-DNDEBUG", "-fno-strict-aliasing"]
    # Check if we are on Android/Termux where clang is default
    if os.path.exists("/data/data/com.termux/files/usr/bin/clang"):
        cmd[0] = "clang"
    elif shutil.which("clang"):
        cmd[0] = "clang"

    cmd.extend(["-I", include_path])
    cmd.extend(["-o", EXECUTE_FILE, C_FILE])
    cmd.extend(["-L", lib_path])
    cmd.extend([f"-lpython{{py_version}}"])
    
    cmd.extend(["-lm"])
    if platform.system() != "Windows":
        cmd.extend(["-ldl", "-lpthread"])
        if platform.system() == "Linux":
            cmd.extend(["-lutil"])

    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chmod(EXECUTE_FILE, 0o755)
        subprocess.call([EXECUTE_FILE], env=_setup_env())
    except Exception as e:
        # Fallback: simple execution if compilation fails (only for debug/dev, removed in prod usually)
        # But for protection we fail silently or exit.
        # User asked to make it work on phone.
        # If compilation fails, we print a helpful message if it's likely missing tools
        if not os.path.exists(EXECUTE_FILE):
             print("Error: Could not compile protection layer.")
             print("Please ensure 'clang' or 'gcc' and 'python-dev' are installed.")
             print("Termux: pkg install clang python")
    finally:
        if os.path.exists(C_FILE):
             try: os.remove(C_FILE) 
             except: pass

if __name__ == "__main__":
    _compile_and_run()
'''
            return loader_script

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

def encrypt(code):
    shielder = PyShielder()
    return shielder.encrypt(code)

def main():
    parser = argparse.ArgumentParser(description="PyShielder - Protect Python Scripts")
    parser.add_argument("file", help="The Python file to encrypt")
    parser.add_argument("-o", "--output", help="Output file path")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found")
        sys.exit(1)
        
    with open(args.file, 'r', encoding='utf-8') as f:
        code = f.read()
        
    print(f"Encrypting {args.file}...")
    encrypted_code = encrypt(code)
    
    if encrypted_code:
        out_path = args.output
        if not out_path:
            base = os.path.splitext(args.file)[0]
            out_path = f"{base}_protected.py"
            
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(encrypted_code)
        print(f"Success! Protected script saved to {out_path}")
    else:
        print("Encryption failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
