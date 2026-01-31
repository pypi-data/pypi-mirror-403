#!/usr/bin/python

__version__ = '0.0.0.1'

import sys
import ctypes

class DlInfo(ctypes.Structure):
    _fields_ = [
        ('dli_fname', ctypes.c_char_p),
        ('dli_fbase', ctypes.c_void_p),
        ('dli_sname', ctypes.c_char_p),
        ('dli_saddr', ctypes.c_void_p),
    ]

libc = ctypes.CDLL(None, use_errno=True)

def dladdr(fp):
    dlinfo = DlInfo()
    assert libc.dladdr(fp, ctypes.byref(dlinfo))
    return dlinfo

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('dladdr.py soname func...')
        print('setting soname to "" will check NULL (default handle).')
        exit(1)

    libname = sys.argv[1]
    if libname in ['NULL', 'None']:
        libname = None

    try:
        lib = ctypes.CDLL(libname)
    except OSError:
        print('dlopen(%s) failed' % sys.argv[1])
        raise
    print('dlopen(%s) ok' % sys.argv[1])

    for funcname in sys.argv[2:]:
        try:
            func = getattr(lib, funcname)
            dlinfo = dladdr(func)
            print('dlsym(%s) ok (%s)' % (funcname, dlinfo.dli_fname.decode('utf-8')))
        except AttributeError as e:
            print('dlsym(%s) failed (%s)' % (funcname, e))
