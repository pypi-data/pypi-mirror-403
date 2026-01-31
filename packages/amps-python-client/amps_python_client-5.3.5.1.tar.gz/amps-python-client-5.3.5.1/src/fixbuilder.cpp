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

using namespace AMPS;
namespace ampspy
{
  namespace fixbuilder
  {

    static ampspy::ampspy_type_object fixbuilder_type;
//    def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      char fieldSep(1);
      self->pFIXBuilder = NULL;
      if (!PyArg_ParseTuple(args, "|c", &fieldSep))
      {
        return -1;
      }
      self->pFIXBuilder = new FIXBuilder(fieldSep);
      return 0;
    }

    static void _dtor(obj* self)
    {
      delete self->pFIXBuilder;
      shims::free(self);
    }

//    def append(self, tag, value, offset, length)
    static PyObject* append(obj* self, PyObject* args)
    {
      int tag = 0;
      PyObject* valObj = NULL;
      const char* value = NULL;
      size_t offset = 0;
      size_t length = 0;
      if (!PyArg_ParseTuple(args, "iO|kk", &tag, &valObj, &offset, &length))
      {
        return NULL;
      }
      PyObject* newString = NULL;
      if (PyString_Check(valObj))
      {
        value = PyString_AsString(valObj);
      }
      else
      {
        newString = PyObject_Str(valObj);
        if (newString)
        {
          value = PyString_AsString(newString);
        }
      }
      if (value)
      {
        if (length == 0)
        {
          std::string val(value);
          self->pFIXBuilder->append(tag, val);
        }
        else
        {
          self->pFIXBuilder->append(tag, value, offset, length);
        }
      }
      Py_XDECREF(newString);
      Py_INCREF((PyObject*)self);
      return (PyObject*)self;
    }

//  def get_string(self)
    static PyObject* get_string(obj* self, PyObject* args)
    {
      CALL_RETURN_STRING(self->pFIXBuilder->getString());
    }

//  def reset(self)
    static PyObject* reset(obj* self, PyObject* args)
    {
      CALL_RETURN_NONE(self->pFIXBuilder->reset());
    }

    static PyObject* str(PyObject* builder)
    {
      obj* self = (obj*)builder;
      CALL_RETURN_STRING(self->pFIXBuilder->getString());
    }
    void add_types(PyObject* module_)
    {
      fixbuilder_type.setName("AMPS.FIXBuilder")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setStrFunction(str)
      .setReprFunction(str)
      .setBaseType()
      .setDoc("AMPS FIXBuilder Object")
      .addMethod("append", append,
                 "append(tag,value,offset(optional),length(optional))\n\nAppends ``tag=value`` to self.\n\n"
                 ":param tag: The numeric tag to use.\n:type tag: int\n"
                 ":param value: The value for the given tag.\n:type value: str\n"
                 ":param offset: The offset into value at which the value actually starts. *Optional.*\n:type offset: int\n"
                 ":param length: The length of the actual value within value. Only valid and required if offset is also provided. *Optional.*\n:type tag: int\n")
      .addMethod("get_string", get_string,
                 "get_string()\n\n"
                 "Called to get the string FIX message.\n\n"
                 ":returns: The FIX message as a string.\n")
      .addMethod("reset", reset,
                 "reset()\n\n"
                 "Called to clear the state of the FIXBuilder to create a new FIX message.\n")
      .notCopyable()
      .createType()
      .registerType("FIXBuilder", module_);
    }

  } // namespace fixbuilder
} // namespace ampspy
