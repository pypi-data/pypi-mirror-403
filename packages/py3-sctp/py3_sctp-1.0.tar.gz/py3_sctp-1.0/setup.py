#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform, setuptools, sys

from setuptools.command.build_ext import build_ext

PKG_NAME = 'sctp'
MODS_DIR = f'_{PKG_NAME}'

SYSTEM = platform.system()
if SYSTEM == 'FreeBSD':
    LIBSCTP = 'usrsctp'
    OS = 'HAVE_FREEBSD'
elif SYSTEM == 'Linux':
    LIBSCTP = 'sctp'
    OS = 'HAVE_LINUX'
else:
    raise RuntimeError(f"`{SYSTEM}': OS not supported")

def _check_for_lsctp(lsctp):
    from ctypes import CDLL
    from ctypes.util import find_library

    print(f"Checking for SCTP dynamic library `-l{lsctp}'...", flush=True)
    lib_name = find_library(lsctp)
    if lib_name is None:
        print(
            f"ERROR: can't find dynamic library `-l{lsctp}'", file=sys.stderr
        )
        sys.exit(1)
    print('Checking succeeded.', flush=True)

def check_for_lsctp(cmd_subclass):
    old_run = cmd_subclass.run
    
    def new_run(self):
        _check_for_lsctp(LIBSCTP)
        old_run(self)
        
    cmd_subclass.run = new_run
    return cmd_subclass

@check_for_lsctp
class CmdBuildExt(build_ext):
    pass

def extension(ext):
    return setuptools.Extension(
        '.'.join((MODS_DIR, ext['name'])),
        sources=[f"C/{ext['name']}.c"],
        include_dirs=['C'],
        libraries=[LIBSCTP],
        depends=ext['depends'],
        define_macros=[
            ('PKG_NAME', f'"{PKG_NAME}"'),
            ('MODS_DIR', f'"{MODS_DIR}"'),
            (OS, None)
        ]
    )

EXTENSIONS = (
    {'name': 'sctp', 'depends': ['C/sctp_info_capi.h', 'C/sctp_error.h']},
    {'name': 'sctp_info', 'depends': ['C/sctp_info_capi.h']},
    {'name': 'sctp_event', 'depends': ['C/sctp_error.h']}
)

setuptools.setup(
    py_modules=[PKG_NAME], 
    packages=setuptools.find_packages(),
    ext_modules=[extension(e) for e in EXTENSIONS],
    cmdclass={'build_ext': CmdBuildExt}
)
