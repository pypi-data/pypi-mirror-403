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
import zipfile
import re
from datetime import datetime

class PyShielder:
    def __init__(self):
        self.temp_dir = ".pyshielder_temp"
        self.zip_path = 'PyShielderPackage'
        self.arm64_path = '.PYSHIELDER/arm64-v8a'
        self.armv7_path = '.PYSHIELDER/armeabi-v7a'
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def _generate_random_string(self, length):
        letters = string.ascii_lowercase
        return random.choice(string.ascii_lowercase) + ''.join(random.choice(letters + string.digits) for _ in range(length - 1))

    def _generate_strong_key(self, length=256):
        chars = string.ascii_letters + string.digits + string.punctuation
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
        return hashlib.sha512(key.encode()).hexdigest()

    def _remove_comments(self, content):
        out = []
        i = 0
        n = len(content)
        while i < n:
            if i + 1 < n and content[i] == '/' and content[i+1] == '*':
                i += 2
                while i + 1 < n and not (content[i] == '*' and content[i+1] == '/'):
                    i += 1
                i += 2
            elif i + 1 < n and content[i] == '/' and content[i+1] == '/':
                i += 2
                while i < n and content[i] != '\n':
                    i += 1
            else:
                out.append(content[i])
                i += 1
        return "".join(out)

    def _multi_layer_obfuscation(self, code, layers=5):
        for i in range(layers):
            compiled_code = compile(code, f'<pyshielder_{i}>', 'exec')
            serialized_code = marshal.dumps(compiled_code)
            code = f'import marshal\nexec(marshal.loads({serialized_code}))'
            
            if i % 2 == 0:
                compressed = zlib.compress(code.encode('utf-8'))
                code = f'import zlib\nexec(zlib.decompress({compressed}))'
            
            if i % 3 == 0:
                encoded = base64.b64encode(code.encode('utf-8'))
                code = f'import base64\nexec(base64.b64decode({encoded}))'
        
        return code

    def _xor_obfuscate(self, data, key):
        Layers = len(key)
        encrypted_text = ''.join(chr(ord(c) ^ ord(key[i % Layers])) for i, c in enumerate(data))
        merged_text = ''.join(encrypted_text[i] + key[i % Layers] for i in range(len(encrypted_text)))
        return merged_text

    def _xor_deobfuscate(self, data_with_key, Layers):
        encrypted_text = ''.join(data_with_key[i*2] for i in range(len(data_with_key) // 2))
        key = ''.join(data_with_key[i*2 + 1] for i in range(len(data_with_key) // 2))
        return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted_text))

    def _advanced_layer_obfuscation(self, code):
        try:
            compiled_1 = compile(code, f'<pyshielder_core>', 'exec')
            serialized_1 = marshal.dumps(compiled_1)
            
            compressed_1 = zlib.compress(serialized_1)
            
            loader_2 = f"import zlib, marshal; exec(marshal.loads(zlib.decompress({compressed_1!r})))"
            compiled_2 = compile(loader_2, f'<pyshielder_loader>', 'exec')
            serialized_2 = marshal.dumps(compiled_2)
            
            encoded_3 = base64.b64encode(serialized_2).decode('utf-8')
            
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
        key = '\u200b\u200c\u200d'
        obfuscated_code = self._xor_obfuscate(code, key)
        
        obfuscated_wrapper = f'''
def _xor_deobfuscate(data_with_key, Layers):
    encrypted_text = ''.join(data_with_key[i*2] for i in range(len(data_with_key) // 2))
    key = ''.join(data_with_key[i*2 + 1] for i in range(len(data_with_key) // 2))
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted_text))

Layers = {len(key)}
Encrypted_Code = {obfuscated_code!r}
decoded_code = _xor_deobfuscate(Encrypted_Code, Layers)
exec(compile(decoded_code, filename="<pyshielder>", mode="exec"))
'''
        
        layered_code = self._multi_layer_obfuscation(obfuscated_wrapper, layers=3)
        
        key2 = self._generate_strong_key()
        byte_array = bytearray(layered_code.encode('utf-8'))
        key_bytes = key2.encode('utf-8')
        encrypted = bytearray()
        
        key_len = len(key_bytes)
        for i, b in enumerate(byte_array):
            k = key_bytes[i % key_len]
            encrypted.append(b ^ k)
            
        hex_encoded = encrypted.hex()
        
        final_obfuscated = f'''
import hashlib

def _decrypt():
    _k = "{key2}"
    _e = bytes.fromhex("{hex_encoded}")
    _kb = _k.encode('utf-8')
    _d = bytearray()
    _kl = len(_kb)
    for _i, _b in enumerate(_e):
        _d.append(_b ^ _kb[_i % _kl])
    return _d.decode('utf-8')

exec(compile(_decrypt(), "<pyshielder>", "exec"))
'''
        return final_obfuscated

    def _get_c_main(self, name_clean):
        return f'''
#if PY_MAJOR_VERSION < 3
int main(int argc, char** argv) {{
#elif defined(WIN32) || defined(MS_WINDOWS)
int wmain(int argc, wchar_t **argv) {{
#else
static int __Pyx_main(int argc, wchar_t **argv) {{
#endif
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

#if PY_MAJOR_VERSION >= 3 && !defined(WIN32) && !defined(MS_WINDOWS)
int main(int argc, char **argv) {{
    return __Pyx_main(argc, (wchar_t**)0);
}}
#endif
'''

    def _create_package(self, zip_path, arm64_exists, armv7_exists):
        loader_code = '''E=print
B=''
A=chr
import zipfile as I,os as C,shutil as K,tempfile as L,sys as D,platform as M
def F():
    N=C.path.dirname(C.path.abspath(D.argv[0]));G=L.mkdtemp()
    try:
        O=C.path.abspath(D.argv[0])
        with I.ZipFile(O,'r')as P:P.extractall(G)
        F=M.machine();J={"arm64":".PYSHIELDER/arm64-v8a","armeabi":".PYSHIELDER/armeabi-v7a"}
        if F not in J:E("Unsupported architecture: %s"%F);D.exit(1)
        Q=J[F];H=C.path.join(G,Q)
        if not C.path.exists(H):E("Architecture binary not found: %s"%F);D.exit(1)
        C.chmod(H,493);C.chdir(N);R="export PYTHONHOME=%s && export PYTHON_EXECUTABLE=%s && ./%s %s"%(D.prefix,D.executable,H,' '.join(D.argv[1:]));C.system(R)
    except I.BadZipFile:E("Invalid PyShielder package")
    except Exception as S:E("Error: %s"%S)
    finally:K.rmtree(G)
if __name__=="__main__":F()'''
        
        with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('__main__.py', loader_code)
            if arm64_exists:
                with open(self.arm64_path,'rb') as f: 
                    arm64_data = f.read()
                zipf.writestr('arm64-v8a', arm64_data)
            if armv7_exists:
                with open(self.armv7_path,'rb') as f: 
                    armv7_data = f.read()
                zipf.writestr('armeabi-v7a', armv7_data)

    def encrypt(self, code, output_file=None, mode="auto"):
        temp_dir = f"{self.temp_dir}_{self._generate_random_string(6)}"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        try:
            print("[*] Applying obfuscation layers...")
            obfuscated_source = self._obfuscate_source(code)
            if not obfuscated_source:
                return None
            
            rand_name = self._generate_random_string(8)
            if rand_name[0].isdigit():
                rand_name = "mod_" + rand_name
                
            py_file = os.path.join(temp_dir, f"{rand_name}.py")
            
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(f"import os\n{obfuscated_source}")
            
            print("[*] Compiling with Cython...")
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

            c_file_path = os.path.join(temp_dir, f"{rand_name}.c")
            if not os.path.exists(c_file_path):
                c_file_path = f"{rand_name}.c"
                
            if not os.path.exists(c_file_path):
                print("Error: Could not find generated C file.")
                return None
                
            with open(c_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                c_content = f.read()
                
            if os.path.exists(f"{rand_name}.c"):
                os.remove(f"{rand_name}.c")

            c_content = c_content.replace(
                '#define CYTHON_COMPILING_IN_CPYTHON 1',
                '#define CYTHON_COMPILING_IN_CPYTHON 1\n#define CYTHON_COMPRESS_STRINGS 0\n#define CYTHON_UNPACK_METHODS 0\n#define CYTHON_FAST_THREAD_STATE 0'
            )
            c_content = self._remove_comments(c_content)
            
            print("[*] Compiling ELF binaries...")
            
            name_clean = rand_name.replace(".py", "")
            c_code_content = self._get_c_main(name_clean)
            full_c_content = c_content + c_code_content
            
            armv7_script = f'''import os
import sys
PREFIX=sys.prefix
EXECUTE_FILE="{self.armv7_path}"
EXPORT_PYTHONHOME="export PYTHONHOME="+sys.prefix
EXPORT_PYTHON_EXECUTABLE="export PYTHON_EXECUTABLE="+ sys.executable
RUN="./"+ EXECUTE_FILE
if os.path.isfile(EXECUTE_FILE):
    os.system(EXPORT_PYTHONHOME +" && "+ EXPORT_PYTHON_EXECUTABLE +" && "+ RUN)
    exit(0)
C_SOURCE = r"""{full_c_content}"""
C_FILE = "{rand_name}.c"
PYTHON_VERSION = ".".join(sys.version.split(" ")[0].split(".")[:-1])
COMPILE_FILE = ('gcc -I' + PREFIX + '/include/python' + PYTHON_VERSION + ' -o ' + EXECUTE_FILE + ' ' + C_FILE + ' -L' + PREFIX + '/lib -lpython' + PYTHON_VERSION)
with open(C_FILE,'w') as f:
    f.write(C_SOURCE)
os.makedirs(os.path.dirname(EXECUTE_FILE), exist_ok=True)
os.system(EXPORT_PYTHONHOME + " && " + EXPORT_PYTHON_EXECUTABLE + " && " + COMPILE_FILE + " && " + RUN)
os.remove(C_FILE)'''
            
            arm64_script = f'''import os
import sys
PREFIX=sys.prefix
EXECUTE_FILE="{self.arm64_path}"
EXPORT_PYTHONHOME="export PYTHONHOME="+sys.prefix
EXPORT_PYTHON_EXECUTABLE="export PYTHON_EXECUTABLE="+ sys.executable
RUN="./"+ EXECUTE_FILE
if os.path.isfile(EXECUTE_FILE):
    os.system(EXPORT_PYTHONHOME +" && "+ EXPORT_PYTHON_EXECUTABLE +" && "+ RUN)
    exit(0)
C_SOURCE = r"""{full_c_content}"""
C_FILE = "{rand_name}.c"
PYTHON_VERSION = ".".join(sys.version.split(" ")[0].split(".")[:-1])
COMPILE_FILE = ('gcc -I' + PREFIX + '/include/python' + PYTHON_VERSION + ' -o ' + EXECUTE_FILE + ' ' + C_FILE + ' -L' + PREFIX + '/lib -lpython' + PYTHON_VERSION)
with open(C_FILE,'w') as f:
    f.write(C_SOURCE)
os.makedirs(os.path.dirname(EXECUTE_FILE), exist_ok=True)
os.system(EXPORT_PYTHONHOME + " && " + EXPORT_PYTHON_EXECUTABLE + " && " + COMPILE_FILE + " && " + RUN)
os.remove(C_FILE)'''
            
            with open(os.path.join(temp_dir, 'compile_armv7.py'), 'w') as f:
                f.write(armv7_script)
            
            with open(os.path.join(temp_dir, 'compile_arm64.py'), 'w') as f:
                f.write(arm64_script)
            
            try:
                subprocess.run(f'python3 {os.path.join(temp_dir, "compile_armv7.py")}', shell=True)
                subprocess.run(f'python3 {os.path.join(temp_dir, "compile_arm64.py")}', shell=True)
            except Exception as e:
                print(f"[!] ELF compilation error: {e}")
            
            arm64_exists = os.path.exists(self.arm64_path)
            armv7_exists = os.path.exists(self.armv7_path)
            
            if arm64_exists and armv7_exists and mode == "package":
                print("[*] Creating package...")
                self._create_package(self.zip_path, arm64_exists, armv7_exists)
                
                with open(self.zip_path, 'rb') as f:
                    package_data = f.read()
                
                package_base64 = base64.b64encode(package_data).decode('utf-8')
                
                loader_script = f'''import os
import tempfile
import base64
import zipfile

PYSHIELDER_DATA = {package_base64!r}

def run_pyshielder():
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pys') as tmp:
            tmp.write(base64.b64decode(PYSHIELDER_DATA))
            tmp_path = tmp.name
        
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall('.pyshielder_temp')
        
        os.system('cd .pyshielder_temp && python3 __main__.py')
        
    except Exception as e:
        print(f"PyShielder Error: {{e}}")
    finally:
        try:
            if 'tmp_path' in locals():
                os.unlink(tmp_path)
            if os.path.exists('.pyshielder_temp'):
                import shutil
                shutil.rmtree('.pyshielder_temp')
        except:
            pass

if __name__ == "__main__":
    run_pyshielder()
'''
                return loader_script
            else:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
                unique_id = hashlib.md5(timestamp.encode()).hexdigest()[:16]
                
                loader_script = f'''import os, sys, hashlib, platform, subprocess, base64, marshal, zlib , shutil

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
            self._cleanup()

    def _cleanup(self):
        try:
            if os.path.exists('.PYSHIELDER'):
                shutil.rmtree('.PYSHIELDER')
            if os.path.exists(self.zip_path):
                os.remove(self.zip_path)
        except Exception as e:
            pass

def encrypt(code, output_file=None, mode="auto"):
    shielder = PyShielder()
    return shielder.encrypt(code, output_file, mode)

def main():
    parser = argparse.ArgumentParser(description="PyShielder - Advanced Python Code Protection")
    parser.add_argument("file", help="The Python file to encrypt")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-m", "--mode", choices=["auto", "package", "standalone"], default="auto", help="Encryption mode")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found")
        sys.exit(1)
        
    with open(args.file, 'r', encoding='utf-8') as f:
        code = f.read()
        
    print(f"[*] Encrypting {args.file}...")
    encrypted_code = encrypt(code, args.output, args.mode)
    
    if encrypted_code:
        out_path = args.output
        if not out_path:
            base = os.path.splitext(args.file)[0]
            if args.mode == "package":
                out_path = f"{base}_protected.pys"
            else:
                out_path = f"{base}_protected.py"
            
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(encrypted_code)
        print(f"[+] Success! Protected script saved to {out_path}")
    else:
        print("[-] Encryption failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
