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
is_setuptools = False


# Upgrade wheel, pip if required.
if sys.argv[1] == "bdist_wheel":
    import wheel
    version_tuple = wheel.__version__.split(".")
    if int(version_tuple[0]) == 0 and int(version_tuple[1]) < 30:
        import subprocess, site
        if sys.version_info.major >= 3:
            from importlib import reload
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "setuptools"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "wheel"])
        sys.path.insert(0, site.getusersitepackages())
        reload(wheel)

try:
    from setuptools import setup, Extension
    is_setuptools = True
except:
    sys.stderr.write("NOTE: setuptools is unavailable; falling back to distutils.\n")
    from distutils.core import setup
    from distutils.extension import Extension


from distutils.sysconfig import get_config_var
#import mybuild as build

# Remove the "-Wstrict-prototypes" compiler option, which isn't valid for C++.
import distutils.sysconfig
cfg_vars = distutils.sysconfig.get_config_vars()
for key, value in cfg_vars.items():
    if type(value) == str:
        cfg_vars[key] = value.replace("-Wstrict-prototypes", "")

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

extension_sources = glob.glob(os.path.join('src','*.cpp'))

amps_client_sources=glob.glob(os.path.join(amps_cpp_dir, 'src','*.c'))

libraries_list = []
extra_args = []
link_args = []
PY_LIMITED_API_version = "Py_LIMITED_API=0x03060000"
if sys.platform != "win32":
    libraries_list.append("amps")
    if sys.platform[:5] == "linux":
        libraries_list.append("rt")
    import subprocess
    f = open("foo.cpp", "w+")
    f.write("#include <atomic>");
    f.close()
    try:
        subprocess.check_call("g++ -std=c++11 -c foo.cpp -o foo.o", shell=True)
        extra_args.append("-std=c++11")
    except Exception as e:
        print("Exception %s using 0x" % (e))
        extra_args.append("-std=c++0x")
    os.remove("foo.cpp")
    try:
        os.remove("foo.o")
    except:
        pass
    extra_args.append("-Wall")
    if "AMPS_DEBUG" in os.environ:
        extra_args.append("-O0")
        extra_args.append("-g")
    else:
        extra_args.append("-O3")

    extra_args.append("-D" + PY_LIMITED_API_version) # the minimum version we want to support
    import subprocess
    subprocess.check_call(['{1} setup_amps.py build -b {0} -t {0} '.format(os.path.join(amps_cpp_dir, 'lib'), sys.executable) ], shell=True)
    os.environ['CFLAGS'] = ""

else:
    if sys.version_info[0] < 3 and "VS90COMNTOOLS" not in os.environ:
        if "AMPS_VC_VERSION" in os.environ and "VS140COMNTOOLS" in os.environ:
            os.environ["VS90COMNTOOLS"] = os.environ["VS140COMNTOOLS"]
        else:
            import re
            comntools = re.compile(r"VS(\d+)COMNTOOLS")
            matches = [ ]
            for env_var in os.environ:
                match = comntools.match(env_var)
                if match:
                    matches.append(int(match.group(1)))
            maxver = 0
            if len(matches) > 0:
                for ver in matches:
                    if ver > maxver:
                        maxver = ver
                os.environ["VS90COMNTOOLS"] = os.environ["VS{0}COMNTOOLS".format(maxver)]
            else:
              sys.stderr.write("The Visual Studio environment variables do not appear to be set. Re-run this setup script from a Visual Studio Command Prompt.")
              exit(-1)

    libraries_list.append("ws2_32")
    extra_args.append("/EHs")
    extra_args.append("/WX")
    extra_args.append("/D_CRT_SECURE_NO_WARNINGS")
    extra_args.append("/D" + PY_LIMITED_API_version)
    if "shared" in sys.argv or ("AMPS_SHARED" in os.environ and os.environ["AMPS_SHARED"] != "0"):
        extra_args.append("/DAMPS_SHARED")
        extra_args.append("/DAMPS_BUILD")
        extra_args.append("/LD")
        extra_args.append("/D_USRDLL")
        extra_args.append("/D_WINDLL")
        if "shared" in sys.argv:
            sys.argv.remove("shared")
    extension_sources = extension_sources + amps_client_sources
    if 'amps_old_windows' in os.environ:
        extra_args.append("/D_WIN32_WINNT=0x0501")

AMPSModule = Extension('AMPS', 
  extension_sources,
  [ os.path.join(amps_cpp_dir, 'src'), os.path.join(amps_cpp_dir, 'include'), 'include'],
  libraries=libraries_list,
  extra_compile_args=extra_args,
  extra_link_args=link_args,
  library_dirs=[os.path.join(amps_cpp_dir, 'lib')]
  )

# Do this here so that we avoid the warning from distutils.
AMPSModule.py_limited_api = True

# Will be replaced with the actual version number by build.xml
module_version="5.3.5.1"

if module_version.startswith('@'):
    # Running this on a bare repository or source tree; try finding the branch name.
    try:
        import subprocess
        process = subprocess.Popen(["git","rev-parse","--abbrev-ref","HEAD"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        result = process.communicate()
        module_version = result[0].decode('utf-8').strip()
        if module_version == "5.3.5.1" or module_version[:5] == "auto-":
            module_version = "99.99.99.99"
        print("VERSION %s"%module_version)
    except:
        #Branch name unknown and the version is unset, so default to UNKNOWN.
        #import traceback
        #traceback.print_exc()
        module_version = "UNKNOWN"


long_descr=open("README.md")
setup(name='amps-python-client',
      description='AMPS Python Client',
      maintainer='60East Technologies, Incorporated',
      maintainer_email='support@crankuptheamps.com',
      url='https://crankuptheamps.com',
      version=module_version,
      long_description=long_descr.read(),
      long_description_content_type="text/markdown",
      classifiers=["License :: Other/Proprietary License"],
      license="Commercial/Proprietary :: see LICENSE",
      platforms=["Linux","Windows"],
      ext_modules=[AMPSModule,]
      )
long_descr.close()

