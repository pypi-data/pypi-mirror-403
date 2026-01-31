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
#ifndef __AMPSPY_DEFS_HPP
#define __AMPSPY_DEFS_HPP

#include <amps/ampsplusplus.hpp>
#include <amps/MMapBookmarkStore.hpp>
#include <amps/MemoryPublishStore.hpp>
#include <amps/PublishStore.hpp>
#include <amps/util.hpp>

#include <amps/DefaultServerChooser.hpp>
#include <amps/ReconnectDelayStrategy.hpp>
#include <amps/CompositeMessageBuilder.hpp>
#include <amps/CompositeMessageParser.hpp>
#include <amps/amps_ssl.h>
#include <vector>
#include <deque>

#include <ampspy_compat.h>

#define CALL_RETURN_NONE(x) try{\
    UnlockGIL __unlock__; \
    x;\
    __unlock__.restore();\
    Py_INCREF(Py_None); return Py_None; \
  } DISPATCH_EXCEPTION

#define CALL_RETURN_SELF(x) try{\
    UnlockGIL __unlock__; \
    x;\
    __unlock__.restore();\
    Py_INCREF((PyObject*)self); return (PyObject*)self; \
  } DISPATCH_EXCEPTION

#define CALL_RETURN_FIELD(x) try{\
    UnlockGIL __unlock__;\
    AMPS::Field rval = x;\
    __unlock__.restore(); \
    return ret(rval);\
  } DISPATCH_EXCEPTION

#define CALL_RETURN_STRING(x) try{\
    UnlockGIL __unlock__;\
    std::string rval = x;\
    __unlock__.restore(); \
    return ret(rval);\
  } DISPATCH_EXCEPTION
#define CALL_RETURN_STRING_AND_SIZE(x,y) try{\
    UnlockGIL __unlock__;\
    const char* data = x;\
    size_t len = y;\
    __unlock__.restore(); \
    return ret(data,len);\
  } DISPATCH_EXCEPTION
#define CALL_RETURN_BYTES_AND_SIZE(x,y) try{\
    UnlockGIL __unlock__;\
    const char* data = x;\
    size_t len = y;\
    __unlock__.restore(); \
    return PyBytes_FromStringAndSize(data,len);\
  } DISPATCH_EXCEPTION
#define CALL_RETURN_SIZE_T(x) try{\
    UnlockGIL __unlock__;\
    size_t rval = x;\
    __unlock__.restore(); \
    return ret(rval);\
  } DISPATCH_EXCEPTION
#define CALL_RETURN_UINT64_T(x) try{\
    UnlockGIL __unlock__;\
    amps_uint64_t rval = x;\
    __unlock__.restore(); \
    return ret(rval);\
  } DISPATCH_EXCEPTION

#define CALL_RETURN_BOOL(x) try{\
    UnlockGIL __unlock__;\
    bool rval = x;\
    __unlock__.restore();\
    return ret(rval);\
  } DISPATCH_EXCEPTION

#define CALL_RETURN_PYOBJECT(x) try{\
    UnlockGIL __unlock__;\
    PyObject* rval = x;\
    Py_INCREF(rval);\
    __unlock__.restore(); \
    return rval;\
  } DISPATCH_EXCEPTION

#define CALL_AND_CAPTURE_RETURN_VALUE(x,retval) try{\
    UnlockGIL __unlock__;\
    retval = x;\
    __unlock__.restore(); \
  } DISPATCH_EXCEPTION

#define CALL_AND_DONT_RETURN(x) try{\
    UnlockGIL __unlock__;\
    x;\
    __unlock__.restore(); \
  } DISPATCH_EXCEPTION_NO_RETURN

#define CALL_AND_RETURN_ON_FAIL(x) \
  bool __call_failed__ = true;\
  try {\
    UnlockGIL __unlock__;\
    x;\
    __call_failed__ = false;\
    __unlock__.restore(); \
  } DISPATCH_EXCEPTION_NO_RETURN \
  if (__call_failed__) return NULL;

#define NONE Py_INCREF(Py_None); return Py_None;


namespace ampspy
{

  extern bool _is_signaled;

#if PY_MAJOR_VERSION >= 3
  AMPSDLL PyObject* ampspy_ssl_init(PyObject* self, PyObject* args, PyObject* kwds = NULL);
  AMPSDLL PyObject* ssl_init(PyObject* self, PyObject* args, PyObject* kwds = NULL);
  AMPSDLL PyObject* ssl_init_internal(const char*, PyObject*, bool strictCiphersOnly = false);

  AMPSDLL PyObject* ampspy_get_PySSLSocket_from_SSL(_amps_SSL* ssl_);
#else
  AMPSDLL PyObject* ampspy_ssl_init(PyObject* self, PyObject* args);
  AMPSDLL PyObject* ssl_init(PyObject* self, PyObject* args);
#endif

// conversions from c++ types
  inline PyObject* ret(const char* returnValue)
  {
    return PyString_FromString(returnValue);
  }
  inline PyObject* ret(AMPS::Field& field)
  {
    PyObject* pyStr = PyString_FromStringAndSize(field.data(), field.len());
    field.clear();
    return pyStr;
  }
  inline PyObject* ret(const char* returnValue, size_t length)
  {
    return PyString_FromStringAndSize(returnValue, length);
  }
  inline PyObject* ret(const std::string& returnValue)
  {
    return PyString_FromString(returnValue.c_str());
  }
  inline PyObject* ret(const long& returnValue)
  {
    return PyInt_FromLong(returnValue);
  }
  inline PyObject* ret(const size_t& returnValue)
  {
    return PyInt_FromSize_t(returnValue);
  }
  inline PyObject* ret(bool value)
  {
    return PyBool_FromLong(value);
  }
#if (!defined(AMPS_X64) && !defined(__aarch64__)) || defined(__APPLE__)
  inline PyObject* ret(const amps_uint64_t& returnValue)
  {
    return PyLong_FromUnsignedLongLong(returnValue);
  }
#endif
} // namespace ampspy

#endif //__AMPSPY_DEFS_HPP
