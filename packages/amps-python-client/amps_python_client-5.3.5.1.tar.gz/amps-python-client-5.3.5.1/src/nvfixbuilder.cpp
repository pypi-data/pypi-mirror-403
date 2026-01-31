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

#define PY_SSIZE_T_CLEAN 1
#include <Python.h>
#include <amps/ampsplusplus.hpp>
#include <ampspy_types.hpp>
#include <ampspy_defs.hpp>
#include "nvfixbuilder_docs.h"

using namespace AMPS;
namespace ampspy
{
  namespace nvfixbuilder
  {
//    def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      char fieldSep(1);
      self->pNVFIXBuilder = NULL;
      if (!PyArg_ParseTuple(args, "|c", &fieldSep))
      {
        return -1;
      }
      self->pNVFIXBuilder = new NVFIXBuilder(fieldSep);
      return 0;
    }
    static void _dtor(obj* self)
    {
      delete self->pNVFIXBuilder;
      shims::free(self);
    }

//    def append(self, tag, value, offset, length)
    static PyObject* append(obj* self, PyObject* args)
    {
      PyObject* tagObj = NULL;
      const char* tag = NULL;
      PyObject* valObj = NULL;
      const char* value = NULL;
      size_t offset = 0;
      size_t length = 0;
      if (!PyArg_ParseTuple(args, "OO|kk", &tagObj, &valObj, &offset, &length))
      {
        NONE;
      }
      PyObject* newTagString = NULL, *newValueString = NULL;
      if (PyString_Check(tagObj))
      {
        tag = PyString_AsString(tagObj);
      }
      else
      {
        newTagString = PyObject_Str(tagObj);
        if (newTagString)
        {
          tag = PyString_AsString(newTagString);
        }
      }
      if (PyString_Check(valObj))
      {
        value = PyString_AsString(valObj);
      }
      else
      {
        newValueString = PyObject_Str(valObj);
        if (newValueString)
        {
          value = PyString_AsString(newValueString);
        }
      }
      if (tag && value)
      {
        if (length == 0)
        {
          self->pNVFIXBuilder->append(tag, value);
        }
        else
        {
          self->pNVFIXBuilder->append(tag, value, offset, length);
        }
      }
      Py_XDECREF(newTagString);
      Py_XDECREF(newValueString);
      Py_INCREF((PyObject*)self);
      return (PyObject*)self;
    }

//  def get_string(self)
    static PyObject* get_string(obj* self, PyObject* args)
    {
      CALL_RETURN_STRING(self->pNVFIXBuilder->getString());
    }

//  def reset(self)
    static PyObject* reset(obj* self, PyObject* args)
    {
      CALL_RETURN_NONE(self->pNVFIXBuilder->reset());
    }

    static PyObject* str(PyObject* builder)
    {
      obj* self = (obj*)builder;
      CALL_RETURN_STRING(self->pNVFIXBuilder->getString());
    }

    static ampspy::ampspy_type_object nvfixbuilder_type;

    void add_types(PyObject* module_)
    {
      nvfixbuilder_type.setName("AMPS.NVFIXBuilder")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setStrFunction(str)
      .setReprFunction(str)
      .setBaseType()
      .setDoc(nvfixbuilder_class_doc)
      .notCopyable()
      .addMethod("append", append,
                 "append(tag,value,offset(optional),length(optional))\n\nAppends ``tag=value`` to self.\n\n"
                 ":param tag: The tag to use.\n:type tag: str\n"
                 ":param value: The value for the given tag.\n:type value: str\n"
                 ":param offset: The offset into value at which the value actually starts. *Optional.*\n:type offset: int\n"
                 ":param length: The length of the actual value within value. Only valid and required if offset is also provided. *Optional.*\n:type length: int\n")
      .addMethod("get_string", get_string,
                 "get_string()\n\n"
                 "Called to get the string NVFIX message.\n\n"
                 ":returns: The NVFIX message as a string.\n")
      .addMethod("reset", reset,
                 "reset()\n\n"
                 "Called to clear the state of the NVFIXBuilder to create a new NVFIX message.\n")
      .createType()
      .registerType("NVFIXBuilder", module_);
    }

  } // namespace nvfixbuilder
} // namespace ampspy
