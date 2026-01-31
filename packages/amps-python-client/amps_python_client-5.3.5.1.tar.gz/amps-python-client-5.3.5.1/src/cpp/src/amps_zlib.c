////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2010-2025 60East Technologies Inc., All Rights Reserved.
//
// This computer software is owned by 60East Technologies Inc. and is
// protected by U.S. copyright laws and other laws and by international
// treaties.  This computer software is furnished by 60East Technologies
// Inc. pursuant to a written license agreement and may be used, copied,
// transmitted, and stored only in accordance with the terms of such
// license agreement and with the inclusion of the above copyright notice.
// This computer software or any other copies thereof may not be provided
// or otherwise made available to any other person.
//
// U.S. Government Restricted Rights.  This computer software: (a) was
// developed at private expense and is in all respects the proprietary
// information of 60East Technologies Inc.; (b) was not developed with
// government funds; (c) is a trade secret of 60East Technologies Inc.
// for all purposes of the Freedom of Information Act; and (d) is a
// commercial item and thus, pursuant to Section 12.212 of the Federal
// Acquisition Regulations (FAR) and DFAR Supplement Section 227.7202,
// Government's use, duplication or disclosure of the computer software
// is subject to the restrictions set forth by 60East Technologies Inc..
//
////////////////////////////////////////////////////////////////////////////

#include <amps/amps_impl.h>
#include <amps/amps_zlib.h>

#ifndef _WIN32
#include <dlfcn.h>
#else
#endif
int amps_zlib_is_loaded = 0;
char amps_zlib_last_error[1024];
amps_zlibVersion_t amps_zlibVersion;
amps_deflateInit2_t amps_deflateInit2_;
amps_deflate_t amps_deflate;
amps_deflate_end_t amps_deflateEnd;
amps_inflateInit2_t amps_inflateInit2_;
amps_inflate_t amps_inflate;
amps_inflate_end_t amps_inflateEnd;

#ifdef _WIN32
#define LOAD_AMPS_ZLIB_FUNCTION(name)                                 \
    *((FARPROC*)&amps_##name) = GetProcAddress(hModule, #name);        \
    if (!amps_##name)                                                 \
    {                                                                 \
        _AMPS_SNPRINTF(amps_zlib_last_error,                          \
                       sizeof(amps_zlib_last_error),                  \
                       "Error loading zlib DLL: %s",                  \
                       amps_zlib_get_last_win32_error());             \
        return -1;                                                    \
    }

const char* amps_zlib_get_last_win32_error(void)
{
    __declspec(thread) static char buffer[1024];
    DWORD dwError = GetLastError();
    FormatMessageA(FORMAT_MESSAGE_FROM_SYSTEM, NULL, dwError, 0, buffer, sizeof(buffer), NULL);
    return buffer;
}
int amps_zlib_init(const char* libraryName_)
{
    if (amps_zlib_is_loaded)
    {
        return 0;
    }
    amps_zlib_last_error[0] = '\0';
    HMODULE hModule = LoadLibraryA(libraryName_ ? libraryName_ : "zlib1.dll");
    if (hModule == NULL)
    {
        _AMPS_SNPRINTF(amps_zlib_last_error, sizeof(amps_zlib_last_error), "Could not load zlib DLL: %s", amps_zlib_get_last_win32_error());
        return -1;
    }

    LOAD_AMPS_ZLIB_FUNCTION(zlibVersion)
    LOAD_AMPS_ZLIB_FUNCTION(deflateInit2_)
    LOAD_AMPS_ZLIB_FUNCTION(deflate)
    LOAD_AMPS_ZLIB_FUNCTION(deflateEnd)
    LOAD_AMPS_ZLIB_FUNCTION(inflateInit2_)
    LOAD_AMPS_ZLIB_FUNCTION(inflate)
    LOAD_AMPS_ZLIB_FUNCTION(inflateEnd)
    amps_zlib_is_loaded = 1;

    return 0;
}
#else
#define LOAD_AMPS_ZLIB_FUNCTION(name)                    \
  amps_##name = dlsym(handle, #name); \
  if(!amps_##name)                                     \
  {                                                     \
      _AMPS_SNPRINTF(amps_zlib_last_error,    \
                     sizeof(amps_zlib_last_error),               \
                     "Error loading zlib module: %s",    \
                     dlerror());                        \
      return -1;                                        \
  }
int amps_zlib_init(const char* libraryName_)
{
    amps_zlib_last_error[0] = '\0';
    if (amps_zlib_is_loaded)
    {
        return 0;
    }
    void* handle = dlopen(libraryName_ ? libraryName_ : "libz.so", RTLD_LOCAL | RTLD_LAZY);
    if (!handle)
    {
        _AMPS_SNPRINTF(amps_zlib_last_error,
          sizeof(amps_zlib_last_error),
          "Could not load libz.so: %s",
          dlerror());
        return -1;
    }
    LOAD_AMPS_ZLIB_FUNCTION(zlibVersion)
    LOAD_AMPS_ZLIB_FUNCTION(deflateInit2_)
    LOAD_AMPS_ZLIB_FUNCTION(deflate)
    LOAD_AMPS_ZLIB_FUNCTION(deflateEnd)
    LOAD_AMPS_ZLIB_FUNCTION(inflateInit2_)
    LOAD_AMPS_ZLIB_FUNCTION(inflate)
    LOAD_AMPS_ZLIB_FUNCTION(inflateEnd)
    amps_zlib_is_loaded = 1;
    return 0;
}
#endif
