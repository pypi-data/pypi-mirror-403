import os, base64, string, random, shutil, marshal, zlib, re, time, sys, zipfile, subprocess
from datetime import datetime

class PyShielder:
    def __init__(self, file_path, output_file='protected_script.py'):
        self.file_path = file_path
        self.output_file = output_file
        
        self.zip_path = 'ShieldPackage'
        self.arm64_path = '.SHIELD/arm64-v8a'
        self.armv7_path = '.SHIELD/armeabi-v7a'
        
        self.loader_code = '''E=print
B=''
A=chr
import zipfile as I,os as C,shutil as K,tempfile as L,sys as D,platform as M
def F():
    N=C.path.dirname(C.path.abspath(D.argv[0]));G=L.mkdtemp()
    try:
        O=C.path.abspath(D.argv[0])
        with I.ZipFile(O,'r')as P:P.extractall(G)
        F=M.machine();J={"arm64":".SHIELD/arm64-v8a","armeabi":".SHIELD/armeabi-v7a"}
        if F not in J:E("Unsupported architecture: %s"%F);D.exit(1)
        Q=J[F];H=C.path.join(G,Q)
        if not C.path.exists(H):E("Architecture binary not found: %s"%F);D.exit(1)
        C.chmod(H,493);C.chdir(N);R="export PYTHONHOME=%s && export PYTHON_EXECUTABLE=%s && ./%s %s"%(D.prefix,D.executable,H,' '.join(D.argv[1:]));C.system(R)
    except I.BadZipFile:E("Invalid Shield package")
    except Exception as S:E("Error: %s"%S)
    finally:K.rmtree(G)
if __name__=="__main__":F()'''
        
        if not os.path.exists("shield_temp/"):
            os.mkdir("shield_temp")

    def generate_random_name(self, length=10):
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def random_string(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

    def remove_comments(self, input_file, output_file):
        with open(input_file, 'r') as input_f:
            content = input_f.read()
        output_content = ''
        in_comment = False
        i = 0
        while i < len(content):
            if content[i:i+2] == '/*':
                in_comment = True
                i += 2
                continue
            elif content[i:i+2] == '*/':
                in_comment = False 
                i += 2
                continue
            if not in_comment:
                output_content += content[i]
            i += 1
        with open(output_file, 'w') as output_f:
            output_f.write(output_content)

    def apply_layers(self, code, layers=5):
        for i in range(layers):
            compiled_code = compile(code, f'Shield{i}', 'exec')
            serialized_code = marshal.dumps(compiled_code)
            code = f'import marshal\nexec(marshal.loads({serialized_code}))'
            
            if i % 2 == 0:
                compressed = zlib.compress(code.encode('utf-8'))
                code = f'import zlib\nexec(zlib.decompress({compressed}))'
            
            if i % 3 == 0:
                encoded = base64.b64encode(code.encode('utf-8'))
                code = f'import base64\nexec(base64.b64decode({encoded}))'
        
        return code

    def xor_encrypt(self, data, key):
        Layers = len(key)
        encrypted_text = ''.join(chr(ord(c) ^ ord(key[i % Layers])) for i, c in enumerate(data))
        merged_text = ''.join(encrypted_text[i] + key[i % Layers] for i in range(len(encrypted_text)))
        return merged_text

    def xor_decrypt(self, data_with_key, Layers):
        encrypted_text = ''.join(data_with_key[i*2] for i in range(len(data_with_key) // 2))
        key = ''.join(data_with_key[i*2 + 1] for i in range(len(data_with_key) // 2))
        return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted_text))

    def cython_to_python(self, cython_code):
        cython_code = re.sub(r'/\*(.+?)\*/', r'"""\1"""', cython_code, flags=re.DOTALL)
        cython_code = re.sub(r'//(.+)', r'#\1', cython_code)
        
        cython_code = re.sub(r'#define\s+(\w+)\s+(.+)', r'# define: \1 = \2', cython_code)
        
        replacements = {
            r'(?:unsigned\s+)?(?:int|long|short|char)\s+(\w+)\s*(?:=\s*([^;]+))?;': r'\1 = \2 if "\2" else 0',
            r'double\s+(\w+)\s*(?:=\s*([^;]+))?;': r'\1 = \2 if "\2" else 0.0',
            r'float\s+(\w+)\s*(?:=\s*([^;]+))?;': r'\1 = \2 if "\2" else 0.0',
            r'char\s*\*\s*(\w+)\s*(?:=\s*([^;]+))?;': r'\1 = \2 if "\2" else ""',
            r'void\s*\*\s*(\w+)\s*;': r'\1 = None',
            r'bool\s+(\w+)\s*(?:=\s*([^;]+))?;': r'\1 = \2 if "\2" else False',
            r'PyObject\s*\*\s*(\w+)\s*(?:=\s*([^;]+))?;': r'\1 = \2 if "\2" else None',
            r'#include\s*[<"](.+)[>"]': r'# import \1',
            r'(static\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{': r'def \3(\4):',
        }
       
        for pattern, replacement in replacements.items():
            cython_code = re.sub(pattern, replacement, cython_code)
        
        api_replacements = {
            "PyDict_New\\(\\)": "dict()",
            "PyList_New\\(0\\)": "[]",
            "PyTuple_New\\(0\\)": "()",
            "PySet_New\\(0\\)": "set()",
            "PyString_FromString\\(([^)]*)\\)": "str(\\1)",
            "PyUnicode_FromString\\(([^)]*)\\)": "str(\\1)",
            "PyBytes_FromString\\(([^)]*)\\)": "bytes(\\1, 'utf-8')",
            "PyInt_FromLong\\(([^)]*)\\)": "int(\\1)",
            "PyLong_FromLong\\(([^)]*)\\)": "int(\\1)",
            "PyFloat_FromDouble\\(([^)]*)\\)": "float(\\1)",
            "PyBool_FromLong\\(([^)]*)\\)": "bool(\\1)",
            "Py_None": "None",
            "Py_True": "True",
            "Py_False": "False",
            "NULL": "None",
        }
        
        for pattern, replacement in api_replacements.items():
            cython_code = re.sub(pattern, replacement, cython_code)

        cython_code = re.sub(r'if\s*\((.+?)\)\s*\{', r'if \1:', cython_code)
        cython_code = re.sub(r'else\s*\{', r'else:', cython_code)
        cython_code = re.sub(r'else\s+if\s*\((.+?)\)\s*\{', r'elif \1:', cython_code)
        cython_code = re.sub(r'while\s*\((.+?)\)\s*\{', r'while \1:', cython_code)
        cython_code = re.sub(r'for\s*\(\s*(\w+)\s+(\w+)\s*=\s*([^;]+);\s*(\w+)\s*([<>!=]=?)\s*([^;]+);\s*(\w+)(\+\+|--|\+=|-=)\s*\)', r'for \2 in range(\3, \6, 1 if "\8" in ["++", "+="] else -1):', cython_code)
        cython_code = re.sub(r';', r'', cython_code)
        cython_code = re.sub(r'\{', r':', cython_code)
        cython_code = re.sub(r'\}', r'', cython_code)

        return cython_code

    def create_package(self, zip_path):
        with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('__main__.py', self.loader_code)
            if os.path.exists(self.arm64_path):
                with open(self.arm64_path,'rb') as f: 
                    arm64_data = f.read()
                zipf.writestr('arm64-v8a', arm64_data)
            if os.path.exists(self.armv7_path):
                with open(self.armv7_path,'rb') as f: 
                    armv7_data = f.read()
                zipf.writestr('armeabi-v7a', armv7_data)

    def generate_c_code(self, name):
        name2 = name.replace(".py", ".c")
        name2_clean = name.replace(".py", "")
        
        c_code = '''
#ifdef __FreeBSD__
#include <dede.h>
#endif
#if PY_MAJOR_VERSION < 3
int main(int argc, char** argv) {
#elif defined(Win32) || defined(MS_WINDOWS)
int wmain(int argc, wchar_t **argv) {
#else
static int __Pyx_main(int argc, wchar_t **argv) {
#endif
#ifdef __FreeBSD__
    fp_except_t m;
    m = fpgetmask();
    fpsetmask(m & ~FP_X_OFL);
#endif
    if (argc && argv)
        Py_SetProgramName(argv[0]);
    Py_Initialize();
    if (argc && argv)
        PySys_SetArgv(argc, argv);
    {
      PyObject* m = NULL;
      __pyx_module_is_main_'''+name2_clean+''' = 1;
      #if PY_MAJOR_VERSION < 3
          init'''+name2_clean+'''();
      #elif CYTHON_PEP489_MULTI_PHASE_INIT
          m = PyInit_'''+name2_clean+'''();
          if (!PyModule_Check(m)) {
              PyModuleDef *mdef = (PyModuleDef *) m;
              PyObject *modname = PyUnicode_FromString("__main__");
              m = NULL;
              if (modname) {
                  m = PyModule_NewObject(modname);
                  Py_DECREF(modname);
                  if (m) PyModule_ExecDef(m, mdef);
              }
          }
      #else
          m = PyInit_'''+name2_clean+'''();
      #endif
      if (PyErr_Occurred()) {
          PyErr_Print();
          #if PY_MAJOR_VERSION < 3
          if (Py_FlushLine()) PyErr_Clear();
          #endif
          return 1;
      }
      Py_XDECREF(m);
    }
#if PY_VERSION_HEX < 0x03060000
    Py_Finalize();
#else
    if (Py_FinalizeEx() < 0)
        return 2;
#endif
    return 0;
}
#if PY_MAJOR_VERSION >= 3 && !defined(Win32) && !defined(MS_WINDOWS)
#include <locale.h>
static wchar_t*
__Pyx_char2wchar(char* arg)
{
    wchar_t *res;
#ifdef HAVE_BROKEN_MBSTOWCS
    size_t argsize = strlen(arg);
#else
    size_t argsize = mbstowcs(NULL, arg, 0);
#endif
    size_t count;
    unsigned char *in;
    wchar_t *out;
#ifdef HAVE_MBRTOWC
    mbstate_t mbs;
#endif
    if (argsize != (size_t)-1) {
        res = (wchar_t *)malloc((argsize+1)*sizeof(wchar_t));
        if (!res)
            goto oom;
        count = mbstowcs(res, arg, argsize+1);
        if (count != (size_t)-1) {
            wchar_t *tmp;
            for (tmp = res; *tmp != 0 &&
                     (*tmp < 0xd800 || *tmp > 0xdfff); tmp++)
                ;
            if (*tmp == 0)
                return res;
        }
        free(res);
    }
#ifdef HAVE_MBRTOWC
    argsize = strlen(arg) + 1;
    res = (wchar_t *)malloc(argsize*sizeof(wchar_t));
    if (!res) goto oom;
    in = (unsigned char*)arg;
    out = res;
    memset(&mbs, 0, sizeof mbs);
    while (argsize) {
        size_t converted = mbrtowc(out, (char*)in, argsize, &mbs);
        if (converted == 0)
            break;
        if (converted == (size_t)-2) {
            fprintf(stderr, "unexpected mbrtowc result -2");
            free(res);
            return NULL;
        }
        if (converted == (size_t)-1) {
            *out++ = 0xdc00 + *in++;
            argsize--;
            memset(&mbs, 0, sizeof mbs);
            continue;
        }
        if (*out >= 0xd800 && *out <= 0xdfff) {
            argsize -= converted;
            while (converted--)
                *out++ = 0xdc00 + *in++;
            continue;
        }
        in += converted;
        argsize -= converted;
        out++;
    }
#else
    res = (wchar_t *)malloc((strlen(arg)+1)*sizeof(wchar_t));
    if (!res) goto oom;
    in = (unsigned char*)arg;
    out = res;
    while(*in)
        if(*in < 128)
            *out++ = *in++;
        else
            *out++ = 0xdc00 + *in++;
    *out = 0;
#endif
    return res;
oom:
    fprintf(stderr, "out of memory");
    return NULL;
}
int
main(int argc, char **argv)
{
    if (!argc) {
        return __Pyx_main(0, NULL);
    }
    else {
        int i, res;
        wchar_t **argv_copy = (wchar_t **)malloc(sizeof(wchar_t*)*argc);
        wchar_t **argv_copy2 = (wchar_t **)malloc(sizeof(wchar_t*)*argc);
        char *oldloc = strdup(setlocale(LC_ALL, NULL));
        if (!argv_copy || !argv_copy2 || !oldloc) {
            fprintf(stderr, "out of memory");
            free(argv_copy);
            free(argv_copy2);
            free(oldloc);
            return 1;
        }
        res = 0;
        setlocale(LC_ALL, "");
        for (i = 0; i < argc; i++) {
            argv_copy2[i] = argv_copy[i] = __Pyx_char2wchar(argv[i]);
            if (!argv_copy[i]) res = 1;
        }
        setlocale(LC_ALL, oldloc);
        free(oldloc);
        if (res == 0)
            res = __Pyx_main(argc, argv_copy);
        for (i = 0; i < argc; i++) {
#if PY_VERSION_HEX < 0x03050000
            free(argv_copy2[i]);
#else
            PyMem_RawFree(argv_copy2[i]);
#endif
        }
        free(argv_copy);
        free(argv_copy2);
        return res;
    }
}
#endif
'''
        return c_code

    def encrypt_file(self):
        name = self.file_path.split("/")[-1]
        temp_name = self.random_string(4) + ".py"
        
        shutil.copyfile(self.file_path, f"shield_temp/{temp_name}")
        
        with open(f"shield_temp/{temp_name}", "r", encoding="utf-8") as f:
            original_code = f.read()
        
        original_code = f"""# ENCODE BY PYSHIELDER
import os
os.system('clear' if os.name != 'nt' else 'cls')
{original_code}"""
        
        key = '\u200b\u200c\u200d'
        obfuscated_code = self.xor_encrypt(original_code, key)
        
        obfuscated_wrapper = f'''
def shield_decrypt(data_with_key, Layers):
    encrypted_text = ''.join(data_with_key[i*2] for i in range(len(data_with_key) // 2))
    key = ''.join(data_with_key[i*2 + 1] for i in range(len(data_with_key) // 2))
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted_text))

Layers = {len(key)}
Encrypted_Code = {obfuscated_code!r}
decoded_code = shield_decrypt(Encrypted_Code, Layers)
exec(compile(decoded_code, filename="<shield>", mode="exec"))
'''
        
        with open(f"shield_temp/{temp_name}", 'w') as f:
            f.write(obfuscated_wrapper)
        
        cython_success = False
        try:
            subprocess.run(f"cython shield_temp/{temp_name} --3str", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cython_success = True
        except Exception:
            pass
        
        c_file = temp_name.replace(".py", ".c")
        
        if cython_success and os.path.exists(f"shield_temp/{c_file}"):
            self.remove_comments(f"shield_temp/{c_file}", f"shield_temp/{c_file}")
            
            name_clean = temp_name.replace(".py", "")
            c_code_content = self.generate_c_code(temp_name)
            
            with open(f"shield_temp/{c_file}", 'r') as f:
                original_c_content = f.read()
            
            full_c_content = original_c_content + c_code_content
            
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
C_SOURCE = r"""''' + full_c_content + '''"""
C_FILE = "{}.c"
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
C_SOURCE = r"""''' + full_c_content + '''"""
C_FILE = "{}.c"
PYTHON_VERSION = ".".join(sys.version.split(" ")[0].split(".")[:-1])
COMPILE_FILE = ('gcc -I' + PREFIX + '/include/python' + PYTHON_VERSION + ' -o ' + EXECUTE_FILE + ' ' + C_FILE + ' -L' + PREFIX + '/lib -lpython' + PYTHON_VERSION)
with open(C_FILE,'w') as f:
    f.write(C_SOURCE)
os.makedirs(os.path.dirname(EXECUTE_FILE), exist_ok=True)
os.system(EXPORT_PYTHONHOME + " && " + EXPORT_PYTHON_EXECUTABLE + " && " + COMPILE_FILE + " && " + RUN)
os.remove(C_FILE)'''
            
            with open('shield_temp/compile_armv7.py', 'w') as f:
                f.write(armv7_script)
            
            with open('shield_temp/compile_arm64.py', 'w') as f:
                f.write(arm64_script)
            
            try:
                subprocess.run('python3 shield_temp/compile_armv7.py', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run('python3 shield_temp/compile_arm64.py', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                pass
        
        if os.path.exists(self.arm64_path) and os.path.exists(self.armv7_path):
            self.create_package(self.zip_path)
            
            with open(self.zip_path, 'rb') as f:
                package_data = f.read()
            
            package_base64 = base64.b64encode(package_data).decode('utf-8')
            
            ff = f'''# Enc by PyShielder

import os
import tempfile
import base64
import zipfile

SHIELD = {package_base64!r}

def run_shield():
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.shield') as tmp:
            tmp.write(base64.b64decode(SHIELD))
            tmp_path = tmp.name
        
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall('.shield_temp')
        
        os.system('cd .shield_temp && python3 __main__.py')
        
    except Exception as e:
        pass
    finally:
        try:
            if 'tmp_path' in locals():
                os.unlink(tmp_path)
            if os.path.exists('.shield_temp'):
                import shutil
                shutil.rmtree('.shield_temp')
        except:
            pass

if __name__ == "__main__":
    run_shield()
'''
            
            with open(self.output_file, 'w') as f:
                f.write(ff)
            
        else:
            with open(f"shield_temp/{temp_name}", 'r') as f:
                ShieldTool = f.read()
            
            shieldtool = self.apply_layers(ShieldTool, layers=5)
            
            final_encoded = base64.b64encode(shieldtool.encode('utf-8')).decode()
            
            ShieldTool = f"""# ENCODE BY PYSHIELDER

import tempfile as SHIELD_TEMP
from os import path as SHIELD_PATH, remove as SHIELD_REMOVE, system as SHIELD_SYSTEM
from base64 import b64decode as SHIELD_DECODE

SHIELD_ENC = {final_encoded!r}

try:
    with SHIELD_TEMP.NamedTemporaryFile(delete=False, suffix='.py') as SHIELD_FILE:
        SHIELD_FILE.write(SHIELD_DECODE(SHIELD_ENC))
        SHIELD_FILEPATH = SHIELD_FILE.name
    SHIELD_SYSTEM('python "' + SHIELD_FILEPATH + '"')
except Exception as SHIELD_ERR:
    pass
finally:
    if 'SHIELD_FILEPATH' in locals() and SHIELD_PATH.exists(SHIELD_FILEPATH):
        SHIELD_REMOVE(SHIELD_FILEPATH)
"""
            
            with open(self.output_file, 'w') as f:
                f.write(ShieldTool)
        
        self.cleanup()
        
        return True

    def cleanup(self):
        try:
            if os.path.exists('shield_temp'):
                shutil.rmtree('shield_temp')
            if os.path.exists('.SHIELD'):
                shutil.rmtree('.SHIELD')
            if os.path.exists(self.zip_path):
                os.remove(self.zip_path)
            if os.path.exists('shield_temp'):
                shutil.rmtree('shield_temp')
        except Exception as e:
            ''

    def run(self):
        try:
            self.encrypt_file()
        except Exception as e:
            pass
        finally:
            self.cleanup()

def encrypt(code):
    """Helper function to encrypt code string"""
    with open('temp_script.py', 'w') as f:
        f.write(code)
    
    encoder = PyShielder('temp_script.py', 'protected_script.py')
    encoder.run()
    
    with open('protected_script.py', 'r') as f:
        result = f.read()
    
    os.remove('temp_script.py')
    os.remove('protected_script.py')
    return result

def main():
    if len(sys.argv) > 1:
        file = sys.argv[1]
    else:
        file = input("File to encode: ").strip()
    
    if not os.path.exists(file):
        sys.exit(1)
    
    output = "protected_script.py"
    if len(sys.argv) > 2:
        output = sys.argv[2]
    elif len(sys.argv) == 1:
        out_input = input("Output file: ").strip()
        if out_input:
            output = out_input
    
    encoder = PyShielder(file, output)
    encoder.run()

if __name__ == "__main__":
    main()
