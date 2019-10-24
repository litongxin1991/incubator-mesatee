import os
import sgx_cffi
import _cffi_backend as backend

ffi = sgx_cffi.FFI(backend)

ffi.embedding_api("void mesapy_setup_model(const char *);")
ffi.embedding_api("void mesapy_run_tests();")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "perm.py")) as f:
    ffi.embedding_init_code(f.read())
ffi.set_source('acs_py_enclave', '')
ffi.emit_c_code(os.environ.get('PYPY_FFI_OUTDIR', ".") + "/acs_py_enclave.c")
