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
#include <amps/CompositeMessageBuilder.hpp>

using namespace AMPS;
namespace ampspy
{
  namespace compositemessagebuilder
  {

    static ampspy::ampspy_type_object composite_message_builder_type;

    //    def __init__(self, initialCapacity):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      int initialCapacity = 16384;
      self->pCompositeMessageBuilder = NULL;
      if (!PyArg_ParseTuple(args, "|i", &initialCapacity))
      {
        return -1;
      }
      self->pCompositeMessageBuilder = new CompositeMessageBuilder(initialCapacity);
      return 0;
    }

    static void _dtor(obj* self)
    {
      delete self->pCompositeMessageBuilder;
      self->pCompositeMessageBuilder = NULL;
      shims::free(self);
    }

    //    def append(self, data)
    static PyObject* append(obj* self, PyObject* args)
    {
      const char* data = NULL;
      Py_ssize_t length = 0;
      if (!PyArg_ParseTuple(args, "s#", &data, &length))
      {
        return NULL;
      }
      CALL_RETURN_SELF(self->pCompositeMessageBuilder->append(data, length));
    }

    //  def get_data(self)
    static PyObject* get_data(obj* self, PyObject* args)
    {
      CALL_RETURN_BYTES_AND_SIZE(self->pCompositeMessageBuilder->data(),
                                 self->pCompositeMessageBuilder->length());
    }

    //  def clea(self)
    static PyObject* clear(obj* self, PyObject* args)
    {
      CALL_RETURN_SELF(self->pCompositeMessageBuilder->clear());
    }

    static PyObject* str(obj* self)
    {
      CALL_RETURN_STRING_AND_SIZE(self->pCompositeMessageBuilder->data(),
                                  self->pCompositeMessageBuilder->length());
    }

    void add_types(PyObject* module_)
    {
      composite_message_builder_type.setName("AMPS.CompositeMessageBuilder")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(&_dtor)
      .setStrFunction(str)
      .setReprFunction(str)
      .setBaseType()
      .setDoc("AMPS CompositeMessageBuilder Object")
      .setConstructorFunction(&_ctor)
      .addMethod("append", append,
                 "append(value)\n\nAppends a message part to this object.\n")
      .addMethod("get_data", get_data,
                 "get_data()\n\nReturns the composite message's data.\n")
      .addMethod("clear", clear,
                 "clear()\n\nClears this object. Does not resize or free internal buffer.")
      .notCopyable()
      .createType()
      .registerType("CompositeMessageBuilder", module_);
    }
  } // namespace fixbuilder
} // namespace ampspy
