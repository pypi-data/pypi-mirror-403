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
#include <amps/CompositeMessageParser.hpp>

using namespace AMPS;
namespace ampspy
{
  namespace compositemessageparser
  {

    static ampspy::ampspy_type_object compositemessageparser_type;

    //    def __init__(self):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      self->pCompositeMessageParser = new CompositeMessageParser();
      self->pLastParsed = 0;
      return 0;
    }

    static void _dtor(obj* self)
    {
      delete self->pCompositeMessageParser;
      self->pCompositeMessageParser = NULL;
      delete self->pLastParsed;
      self->pLastParsed = NULL;
      shims::free(self);
    }

    //    def parse(self, data or AMPS::Message)
    static PyObject* parse(obj* self, PyObject* args)
    {
      PyObject* data_or_message = NULL;
      if (!PyArg_ParseTuple(args, "O", &data_or_message))
      {
        return NULL;
      }
      const char* data = NULL;
      size_t len = 0;
      if (data_or_message->ob_type == ampspy::message::message_type.pPyTypeObject())
      {
        AMPS::Message* pMessage = ((ampspy::message::obj*)data_or_message)->pMessage;
        pMessage->getRawData(&data, &len);
      }
      else
      {
        Py_ssize_t pysize = 0;
        if (!PyArg_ParseTuple(args, "s#", (char**)&data, &pysize))
        {
          PyErr_SetString(PyExc_TypeError, "argument 1 must be str or AMPS.Message");
          return NULL;
        }
        len = (size_t)pysize;
      }
      // Keep a copy of the data we parsed, since we can't really freeze the incoming string or message.
      if (self->pLastParsed)
      {
        self->pLastParsed->assign(data, len);
      }
      else
      {
        self->pLastParsed = new std::string(data, len);
      }
      CALL_RETURN_SIZE_T(self->pCompositeMessageParser->parse(
                           self->pLastParsed->c_str(), len));
    }
    //  def get_part(self)
    static PyObject* get_part(obj* self, PyObject* args)
    {
      int index = 0;
      if (!PyArg_ParseTuple(args, "I", &index))
      {
        return NULL;
      }
      AMPS::Field data = self->pCompositeMessageParser->getPart(index);
      if (data.data() == NULL)
      {
        NONE;
      }
      return ret(data.data(), data.len());
    }
    //  def get_part_raw(self)
    static PyObject* get_part_raw(obj* self, PyObject* args)
    {
      int index = 0;
      if (!PyArg_ParseTuple(args, "I", &index))
      {
        return NULL;
      }
      AMPS::Field data = self->pCompositeMessageParser->getPart(index);
      if (data.data() == NULL)
      {
        NONE;
      }
      return PyBytes_FromStringAndSize(data.data(), data.len());
    }
    static PyObject* size(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T(self->pCompositeMessageParser->size());
    }
    void add_types(PyObject* module_)
    {
      compositemessageparser_type.setName("AMPS.CompositeMessageParser")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setBaseType()
      .setDoc("AMPS CompositeMessageParser Object")
      .notCopyable()
      .addMethod("parse", parse,
                 "parse(str_or_Message)\n\nParse a composite message body or composite AMPS.Message.\nReturns the number of valid parts parsed.\n")
      .addMethod("get_part", get_part,
                 "get_part(index)\n\nReturns the index'th composite message part, or None if index is invalid.\n")
      .addMethod("get_part_raw", get_part_raw,
                 "get_part_raw(index)\n\nReturns the index'th composite message part as a python bytes object, or None if index is invalid.\n")
      .addMethod("size", size,
                 "size()\n\nReturns the number of message parts last parsed.\n")
      .createType()
      .registerType("CompositeMessageParser", module_);
    }

  } // namespace compositemessageparser
} // namespace ampspy
