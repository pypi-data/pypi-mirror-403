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
#pragma once

#include <Python.h>

/////////////////////////////////////////////////////////////////////////////
//
// ampspy::shims
//
// A very small dynamic loader/shim library so we can use non ABI3 python
// functions but still be version-independent across 3.x versions. We're only
// working around the ABI for a minimal set of functions:
//
// _Py_Finalizing/Py_IsFinalizing: Our client creates its own thread and
//    calls Python code from it, and it also holds important resources.
//    Before calling PyThreadState_Ensure(), we have to make sure the
//    interpreter isn't shutting down, else PyThreadState_Ensure()
//    will call pthread_exit() on us, which is unacceptable. (In Python 2.x
//    we simulate this via a static that is set from an exitfunc).
//
// _PyThreadState_Current: If shutdown begins while we're holding the GIL,
//    then calling PyGILState_Release() will crash shutdown. We have to
//    have a way to detect if the GIL thinks it is still being held by us
//    to safely release the GIL from a non-python thread.
//
// _PyUnicode_AsUTF8AndSize: This was added to ABI3 for 3.10; we need it
//    in older Python 3 versions to get access to the internal utf-8 rep
//    of strings a user passes to us.
//
// free(), type_name(): provides a unified interface to tp_free and
//    tp_name since PyTypeObject is opaque under ABI3.
//
/////////////////////////////////////////////////////////////////////////////
namespace ampspy
{
  namespace shims
  {
    extern const char* g_shimExitFuncName;
    typedef bool (*Py_IsFinalizing_t)(void);
    typedef PyObject* (*PyErr_GetRaisedException_t)(void);
    typedef const char* (*PyUnicode_AsUTF8AndSize_t)(PyObject*, Py_ssize_t*);
    typedef PyThreadState* (*PyThreadState_UncheckedGet_t)(void);

    extern Py_IsFinalizing_t Py_IsFinalizing;
    extern PyErr_GetRaisedException_t PyErr_GetRaisedException;
    extern PyUnicode_AsUTF8AndSize_t PyUnicode_AsUTF8AndSize;
    extern PyThreadState_UncheckedGet_t PyThreadState_UncheckedGet;

    bool init(PyObject* module_);
    PyObject* _shimExitFunc(void);

    inline void free(void* pObject_)
    {
      PyObject* pObject = (PyObject*)pObject_;
      if (pObject)
      {
#if PY_MAJOR_VERSION < 3
        Py_TYPE(pObject)->tp_free(pObject);
#else
        ((freefunc)PyType_GetSlot((PyTypeObject*)PyObject_Type(pObject), Py_tp_free))(pObject);
#endif
      }
    }
    inline const char* type_name(PyTypeObject* pyTypeObject_)
    {
      if (pyTypeObject_)
      {
#if PY_MAJOR_VERSION < 3
        return pyTypeObject_->tp_name;
#else
        Py_ssize_t ignored = 0;
        PyObject* name = PyObject_GetAttrString((PyObject*)pyTypeObject_, "__name__");
        const char* result = PyUnicode_AsUTF8AndSize(name, &ignored);
        Py_XDECREF(name);

        return result;
#endif
      }
      return NULL;
    }

#if PY_MAJOR_VERSION >= 3
    inline const char* PyUnicode_AsUTF8(PyObject* pyObject_)
    {
      Py_ssize_t unused = 0;
      return ampspy::shims::PyUnicode_AsUTF8AndSize(pyObject_, &unused);
    }
#endif

  }

}
