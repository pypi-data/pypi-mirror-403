#!/usr/bin/env python
############################################################################
##
## Copyright (c) 2012-2025 60East Technologies Inc., All Rights Reserved.
##
## This computer software is owned by 60East Technologies Inc. and is
## protected by U.S. copyright laws and other laws and by international
## treaties.  This computer software is furnished by 60East Technologies
## Inc. pursuant to a written license agreement and may be used, copied,
## transmitted, and stored only in accordance with the terms of such
## license agreement and with the inclusion of the above copyright notice.
## This computer software or any other copies thereof may not be provided
## or otherwise made available to any other person.
##
## U.S. Government Restricted Rights.  This computer software: (a) was
## 5.3.5.1ed at private expense and is in all respects the proprietary
## information of 60East Technologies Inc.; (b) was not 5.3.5.1ed with
## government funds; (c) is a trade secret of 60East Technologies Inc.
## for all purposes of the Freedom of Information Act; and (d) is a
## commercial item and thus, pursuant to Section 12.212 of the Federal
## Acquisition Regulations (FAR) and DFAR Supplement Section 227.7202,
## Government's use, duplication or disclosure of the computer software
## is subject to the restrictions set forth by 60East Technologies Inc..
##
############################################################################
import os, glob, sys
if "bdist_egg" in sys.argv:
  from setuptools import setup
else:
  from distutils.core import setup
from distutils.extension import Extension
from distutils.sysconfig import get_config_var
#import mybuild as build

if get_config_var("OPT") is not None:
  os.environ["OPT"] = get_config_var("OPT").replace("-Wstrict-prototypes","")

# check for AMPS_CPP_DIR set
if "AMPS_CPP_DIR" not in os.environ:
    # use the included cpp client.
    amps_cpp_dir = os.path.join(os.path.dirname(os.path.relpath(__file__)), "src","cpp")
else:
    amps_cpp_dir = os.environ["AMPS_CPP_DIR"]
    sys.stderr.write("AMPS_CPP_DIR is set. Using alternate C++ client in %s\n"%amps_cpp_dir)

if not os.path.exists(os.path.join(amps_cpp_dir, 'include', 'amps', 'ampsplusplus.hpp')):
    sys.stderr.write("No ampsplusplus.hpp found in an include directory under %s\n"%amps_cpp_dir)
    # If the current directory has a .gitmodules, we're probably being called from a git clone, not a package.
    # Advise the user to run git submodule update --init to fetch the src/cpp directory.
    if(os.path.exists(os.path.join(os.path.dirname(os.path.relpath(__file__)), ".gitmodules"))):
        sys.stderr.write("""
It looks like this client is a git clone, not a packaged client build.
To download the necessary AMPS C++ client files, issue a `git submodule` command, such as:

    git submodule update --init

For more information, check the README.md.\n""")
    exit(-1)

amps_client_sources=glob.glob(os.path.join(amps_cpp_dir, 'src','*.c'))

if sys.platform != "win32":
    if os.path.exists('src/cpp/lib/libamps.a'):
        build = False
        last_build_time = os.path.getmtime('src/cpp/lib/libamps.a')
        for src in amps_client_sources:
            build = build | (os.path.getmtime(src) >= last_build_time)
        if not build:
            for header in glob.glob(os.path.join(amps_cpp_dir, 'include', 'amps', '*.h*')):
                build = build | (os.path.getmtime(header) >= last_build_time)
            if not build:
              sys.exit(0)
    import subprocess
    f = open("foo.c", "w+")
    f.write("#include <stdatomic.h>");
    f.close()
    try:
        subprocess.check_call("gcc -std=gnu11 -c foo.c -o foo.o", shell=True)
        os.environ['CFLAGS'] = "-std=gnu11 -Wall"
    except Exception as e:
        print("Exception %s using 99" % (e))
        os.environ['CFLAGS'] = "-std=gnu99 -Wall"
    os.remove("foo.c")
    try:
        os.remove("foo.o")
    except:
        pass
elif "shared" in sys.argv or "AMPS_SHARED" in os.environ:
    os.environ['CFLAGS'] = "/LD /DAMPS_SHARED /DAMPS_BUILD"
    if "shared" in sys.argv:
        sys.argv.remove("shared")

setup(name='amps-c-client',
      description='AMPS C Client',
      version='5.3.5.1',
      maintainer='60East Technologies, Incorporated',
      maintainer_email='support@crankuptheamps.com',
      url='https://crankuptheamps.com',
      libraries = [('amps',{'sources':amps_client_sources, 'include_dirs':[ os.path.join(amps_cpp_dir, 'src'), os.path.join(amps_cpp_dir, 'include'), 'include'] })],
      )


