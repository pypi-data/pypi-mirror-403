import sys
import ctypes
from os.path import basename

from dladdr import dladdr

if sys.platform in ('darwin', 'ios',):
    # /usr/lib/system/libsystem_c.dylib
    libcname = 'libsystem_c.dylib'
    libname = 'libiconv.2.dylib'
elif sys.platform.startswith('freebsd'):
    libcname = 'libc.so.7'
    libname = 'libstdc++.so.6'
elif sys.platform.startswith('android'):
    libcname = 'libc.so'
    libname = 'libstdc++.so'
else:
    libcname = 'libc.so.6'
    libname = 'libstdc++.so.6'

def test_dladdr():
    libstdcxx = ctypes.CDLL(libname)
    fp = libstdcxx.printf  # dlsym("printf") succeeds, but it should be from libc, not libstdc++.
    dlinfo = dladdr(fp)
    assert basename(dlinfo.dli_fname).decode('utf-8') == libcname
