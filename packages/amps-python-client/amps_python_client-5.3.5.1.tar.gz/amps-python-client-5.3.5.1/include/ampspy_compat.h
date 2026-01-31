////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2017-2025 60East Technologies Inc., All Rights Reserved.
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

///////////////////////////////////////////////////////////////////
//
// ampspy_compat.h
//
// Contains preprocessor macros to aid in portability between Python 2.x and 3.x
//
///////////////////////////////////////////////////////////////////
#ifndef __AMPSPY_COMPAT_H
#define __AMPSPY_COMPAT_H

#if PY_MAJOR_VERSION >= 3

  // Redirect Python 2.x functions to unicode.

  #define PyString_AsString shims::PyUnicode_AsUTF8
  #define PyString_FromString PyUnicode_FromString
  #define PyString_FromStringAndSize PyUnicode_FromStringAndSize
  #define PyString_Check PyUnicode_Check
  #define PyString_AsStringAndSize(obj,str,len) *((const char**)str)=shims::PyUnicode_AsUTF8AndSize(obj,len)
  #define PyString_FromFormat PyUnicode_FromFormat

  // Python 3.x no longer has a separate Int type; everything is a Long
  #define PyInt_FromLong PyLong_FromLong
  #define PyInt_FromSize_t PyLong_FromSize_t
  #define PyNumber_Int PyNumber_Long
  #define PyInt_AsUnsignedLongLongMask PyLong_AsUnsignedLongLongMask
  #define PyInt_Check PyLong_Check
  #define PyInt_AsSsize_t PyLong_AsSsize_t
  #define PyInt_AsLong PyLong_AsLong

  #ifndef PyTuple_GET_ITEM
    #define PyTuple_GET_ITEM PyTuple_GetItem
  #endif

#endif
#endif // __AMPSPY_COMPAT_H


