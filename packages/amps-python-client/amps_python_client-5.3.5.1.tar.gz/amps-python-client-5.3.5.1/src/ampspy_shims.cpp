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
#include <ampspy_shims.hpp>
#include <ampspy_ssl.hpp>

#ifdef _WIN32
  #include <Windows.h>
  #include <psapi.h>
  #include <vector>
#else

  #include <dlfcn.h>
#endif

namespace ampspy
{
  namespace shims
  {
    const char* g_shimExitFuncName = "_exiter";
    Py_IsFinalizing_t Py_IsFinalizing = 0;
    PyErr_GetRaisedException_t PyErr_GetRaisedException = 0;
    PyUnicode_AsUTF8AndSize_t PyUnicode_AsUTF8AndSize = 0;
    PyThreadState_UncheckedGet_t PyThreadState_UncheckedGet = 0;
    int* Py_Finalizing_36 = 0;

#if PY_MAJOR_VERSION < 3
    static volatile bool g_isFinalizing = false;
    static PyObject* g_previousExitFunc = 0;
    PyObject* _shimExitFunc(void)
    {
      g_isFinalizing = true;
      if (g_previousExitFunc)
      {
        Py_XDECREF(PyObject_CallFunction(g_previousExitFunc, NULL));
        Py_DECREF(g_previousExitFunc);
        g_previousExitFunc = NULL;
      }
      Py_INCREF(Py_None);
      return Py_None;
    }
    bool ampspy2IsFinalizing(void)
    {
      return g_isFinalizing;
    }
    PyThreadState* ampspy2PyThreadState_UncheckedGet(void)
    {
      return (PyThreadState*)_PyThreadState_Current;
    }
#else
    bool ampspy36IsFinalizing(void)
    {
      return *(Py_Finalizing_36) != 0;
    }
    PyObject* _shimExitFunc(void)
    {
      _ampspy_ssl_cleanup();
      Py_INCREF(Py_None);
      return Py_None;
    }
#endif


#ifdef _WIN32
    // Windows: Scan the loaded modules looking for the symbols we need.
    //    (You can't just GetProcAddress() here without the HMODULE for the
    //     DLL you want to look in. We don't necessarily know which DLL
    //     it will be in since the name is version dependent, and symbols
    //     might exist only in the unversioned python DLL).
    //  Set the environment variable VERBOSE=1 if you're debugging failures
    //  here to see more about what we're doing.
    template <class T>
    bool getSymbol(const char* symbol_, T* ppFunction_)
    {
      static const size_t max_modules = 1024;
      const bool isVerbose = getenv("VERBOSE") != 0;
      HANDLE hProcess = GetCurrentProcess();
      std::vector<HMODULE> modules;
      modules.resize(max_modules);
      DWORD returnedByteCount = 0;
      BOOL rc = EnumProcessModules(hProcess, (HMODULE*)modules.data(),
                                   (DWORD)(sizeof(HMODULE) * modules.size()), &returnedByteCount);

      if (!rc)
      {
        if (isVerbose)
        {
          fprintf(stderr, "[AMPS] EnumProcessModules() failed: result %x\n",
                  GetLastError());
        }
        return false;
      }
      if (returnedByteCount / sizeof(HMODULE) < modules.size())
      {
        modules.resize(returnedByteCount / sizeof(HMODULE));
      }
      for (HMODULE hModule : modules)
      {
        // Probe for symbol in every module.
        *ppFunction_ = (T)GetProcAddress(hModule, symbol_);
        if (*ppFunction_)
        {
          if (isVerbose)
          {
            char moduleFileName[MAX_PATH];
            GetModuleFileNameA(hModule, moduleFileName, MAX_PATH);
            moduleFileName[MAX_PATH - 1] = '\0';
            fprintf(stderr, "[AMPS] Located %s in %s -> %p\n", symbol_, moduleFileName,
                    *ppFunction_);
          }
          return true;
        }
      }
      if (isVerbose)
      {
        fprintf(stderr, "[AMPS] Could not locate %s; searched %zu modules:\n", symbol_,
                modules.size());
        for (HMODULE hModule : modules)
        {
          char moduleFileName[MAX_PATH];
          GetModuleFileNameA(hModule, moduleFileName, MAX_PATH);
          moduleFileName[MAX_PATH - 1] = '\0';
          fprintf(stderr, "[AMPS]   %s\n", moduleFileName);
        }
      }
      return false;
    }
#else
    template <class T>
    bool getSymbol(const char* symbol_, T* ppFunction_)
    {
      *ppFunction_ = (T)::dlsym(RTLD_DEFAULT, symbol_);
      if (getenv("VERBOSE") != 0)
      {
        if (*ppFunction_)
        {
          fprintf(stderr, "[AMPS] dlsym(\"%s\") -> %p\n", symbol_, *ppFunction_);
        }
        else
        {
          const char* errStr = dlerror();
          if (!errStr)
          {
            errStr = "Unknown error";
          }
          fprintf(stderr, "[AMPS] dlsym(\"%s\") -> %p: %s\n", symbol_, *ppFunction_,
                  errStr);
        }
      }
      return *ppFunction_;
    }
#endif

    bool init(PyObject* module_)
    {
#if PY_MAJOR_VERSION < 3
      g_previousExitFunc = PySys_GetObject(const_cast<char*>("exitfunc"));
      Py_XINCREF(g_previousExitFunc);
      PySys_SetObject(const_cast<char*>("exitfunc"),
                      PyDict_GetItemString(PyModule_GetDict(module_),
                                           const_cast<char*>(g_shimExitFuncName)));
      ampspy::shims::Py_IsFinalizing = &ampspy2IsFinalizing;
      ampspy::shims::PyThreadState_UncheckedGet = &ampspy2PyThreadState_UncheckedGet;
#else
      // Python 3.6: use _Py_Finalizing bool
      if (getSymbol("_Py_Finalizing", &ampspy::shims::Py_Finalizing_36))
      {
        ampspy::shims::Py_IsFinalizing = &ampspy36IsFinalizing;
      }
      else if (!getSymbol("_Py_IsFinalizing", &ampspy::shims::Py_IsFinalizing)
               && !getSymbol("Py_IsFinalizing", &ampspy::shims::Py_IsFinalizing))
      {
        // Python 3.7 - 3.12: use _Py_IsFinalizing function
        // Python 3.13+: use Py_IsFinalizing function
        PyErr_SetString(PyExc_RuntimeError,
                        "Error locating _Py_Finalizing, _Py_IsFinalizing, or"
                        " Py_IsFinalizing; cannot load AMPS.");
        return false;
      }

      // Python 3.6 - 3.12: use _Py_UncheckedGet function
      // Python 3.13+: use Py_GetUnchecked function
      if (!getSymbol("_PyThreadState_UncheckedGet",
                     &ampspy::shims::PyThreadState_UncheckedGet)
          && !getSymbol("PyThreadState_GetUnchecked",
                        &ampspy::shims::PyThreadState_UncheckedGet))
      {
        PyErr_SetString(PyExc_RuntimeError,
                        "Error locating _PyThreadState_UncheckedGet or"
                        " PyThreadState_GetUnchecked; cannot load AMPS.");
        return false;
      }
      // This one will only be used for python 3.12+
      getSymbol("PyErr_GetRaisedException",
                &ampspy::shims::PyErr_GetRaisedException);
      if (!getSymbol("PyUnicode_AsUTF8AndSize",
                     &ampspy::shims::PyUnicode_AsUTF8AndSize))
      {
        PyErr_SetString(PyExc_RuntimeError,
                        "Error locating PyUnicode_AsUTF8AndSize; cannot load AMPS.");
        return false;
      }
#endif
      return true;
    }
  }
}
