////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2016-2025 60East Technologies Inc., All Rights Reserved.
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
namespace ampspy
{
  PyFailedWriteHandler::PyFailedWriteHandler(PyObject* self_)
    : _self(self_), _newStyle(true), _message(NULL)
  {
    LOCKGIL;
    Py_INCREF(_self);
    _message = (ampspy::message::obj*)_PyObject_New(ampspy::message::message_type);
    _message->isOwned = false;
  }

  PyFailedWriteHandler::~PyFailedWriteHandler()
  {
    // we need a python thread state in order to do this
    try
    {
      LOCKGIL;
      Py_DECREF(_self);
    }
    catch (...)
    {
      // LOCKGIL will throw if python is shutting down; avoid this.
    }
  }

  void
  PyFailedWriteHandler::failedWrite(const AMPS::Message& message_,
                                    const char* reason_, size_t reasonLength_)
  {
    PyObject* returnValue = NULL;
    LOCKGIL;
    if (_newStyle)
    {
      _message->pMessage = (AMPS::Message*)&message_;
      returnValue = PyObject_CallFunction(_self, (char*)"(Os#)",
                                          _message, reason_, reasonLength_);
      if (returnValue)
      {
        Py_DECREF(returnValue);
        return;
      }
      if (PyErr_ExceptionMatches(PyExc_TypeError))
      {
        // This will fall through
        _newStyle = false;
        PyErr_Clear();
      }
      else if (PyErr_ExceptionMatches(PyExc_SystemExit))
      {
        ampspy::unhandled_exception();
      }
      else
      {
        exc::throwError();
      }
    }
    const char* topic, *data, *correlationId;
    size_t topicLength, dataLength, correlationIdLength;
    message_.getRawTopic(&topic, &topicLength);
    message_.getRawData(&data, &dataLength);
    message_.getRawCorrelationId(&correlationId, &correlationIdLength);
    amps_uint64_t sequence = amps_message_get_field_uint64(message_.getMessage(),
                                                           AMPS_Sequence);
    returnValue = PyObject_CallFunction(_self, (char*)"(Kbs#s#s#s#)",
                                        sequence,
                                        (char)message_.getCommandEnum(),
                                        topic, topicLength,
                                        data, dataLength,
                                        correlationId, correlationIdLength,
                                        reason_, reasonLength_);
    if (returnValue == NULL)
    {
      if (PyErr_ExceptionMatches(PyExc_SystemExit))
      {
        ampspy::unhandled_exception();
      }
      else // includes PyExc_TypeError
      {
        exc::throwError();
      }
    }
    Py_DECREF(returnValue);
  }

} // namespace ampspy

