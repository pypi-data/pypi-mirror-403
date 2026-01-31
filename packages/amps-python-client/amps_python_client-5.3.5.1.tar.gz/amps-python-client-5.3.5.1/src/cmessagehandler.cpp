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
  namespace cmessagehandler
  {

    ampspy::ampspy_type_object cmessagehandler_type;

    static PyObject* toPySizeT(PyObject* object)
    {
      PyObject* ctypesModule = PyImport_ImportModule("ctypes");
      PyObject* ctypesDict = PyModule_GetDict(ctypesModule);
      // Get cast function
      PyObject* castFunction = PyDict_GetItemString(ctypesDict, "cast");
      // Get c_void_p constant
      PyObject* c_void_p = PyDict_GetItemString(ctypesDict, "c_void_p");


      PyObject* result = PyObject_CallFunctionObjArgs(castFunction, object, c_void_p);
      PyObject* value = PyObject_GetAttrString(result, "value");
      Py_XDECREF(result);
      Py_XDECREF(c_void_p);
      Py_XDECREF(castFunction);
      Py_DECREF(ctypesDict);
      Py_DECREF(ctypesModule);
      return value;
    }

    static void* toCPtr(PyObject* pySizeT)
    {
      if (PyInt_Check(pySizeT))
      {
        return (void*)PyInt_AsSsize_t(pySizeT);
      }
      return NULL;
    }
//    def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      PyObject* function = NULL;
      PyObject* userdata = NULL;
      if (!PyArg_ParseTuple(args, "O|O", &function, &userdata) || !function)
      {
        return -1;
      }

      // Use the ctypes module to establish the real function pointer and any userdata.
      self->function = toPySizeT(function);
      self->userdata = toPySizeT(userdata);

      Py_XINCREF(self->function);
      Py_XINCREF(self->userdata);
      return 0;
    }

    AMPSDLL AMPS::MessageHandler getMessageHandler(PyObject* pySelf)
    {
      obj* self = (obj*)pySelf;

      // now extract the void ptr
      AMPS::MessageHandlerFunc pFunction = (AMPS::MessageHandlerFunc)toCPtr(
                                             self->function);
      void* pUserdata = (void*)toCPtr(self->userdata);
      return AMPS::MessageHandler(pFunction, pUserdata);
    }

    static void _dtor(obj* self)
    {
      Py_XDECREF(self->function);
      Py_XDECREF(self->userdata);
      shims::free(self);
    }


    static PyObject* call(obj* self, PyObject* args, PyObject* kw)
    {
      message::obj* myMessage;
      if (!PyArg_ParseTuple(args, "O!", message::message_type.pPyObject(),
                            ( (PyObject**)&myMessage) ))
      {
        return NULL;
      }
      getMessageHandler((PyObject*)self).invoke(*(myMessage->pMessage));

      NONE;
    }
    static const char* cmessage_doc = R"docstring(
    Wraps a C/C++ message handler function for use as a higher-performance AMPS message handler.
    To use, create a shared library or DLL with an exported function of type ``AMPS::MessageHandlerFunc``.

    For example::

      extern "C" void my_message_handler(const AMPS::Message& message, void* userdata) { ... }

    and then use the Python ``ctypes`` module to load and supply it::
    
      import ctypes
      client = AMPS.Client(...)
      
      my_dll = ctypes.CDLL("./mymessagehandler.so") # load my DLL
      client.subscribe( AMPS.CMessageHandler( my_dll.my_message_handler, "user data"), "my_amps_topic" )

    As messages arrive, they are sent directly to ``my_message_handler`` without passing through the Python interpreter
    or taking the Python Global Interpreter Lock (GIL), resulting in potentially higher performance.

      .. note:: No checking is performed to make sure your C/C++ function is of the appropriate signature. Supplying
        a function of a different signature than that shown, results in undefined behavior.
    )docstring";

    bool isCHandler(PyObject* obj)
    {
      return cmessagehandler_type.isInstanceOf(obj);
    }

    void add_types(PyObject* module_)
    {
      cmessagehandler_type.setName("AMPS.CMessageHandler")
      .setBasicSize(sizeof(obj))
      .setBaseType()
      .setConstructorFunction(&_ctor)
      .setDestructorFunction(&_dtor)
      .setCallFunction(&call)
      .setDoc(cmessage_doc)
      .notCopyable()
      .createType()
      .registerType("CMessageHandler", module_);
    }

  } // namespace cmessagehandler
} // namespace ampspy
