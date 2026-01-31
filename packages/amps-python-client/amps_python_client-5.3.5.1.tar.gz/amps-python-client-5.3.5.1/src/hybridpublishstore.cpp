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
#include <amps/HybridPublishStore.hpp>
#include "hybridpublishstore_docs.h"

using namespace AMPS;
namespace ampspy
{
  namespace hybridpublishstore
  {

    AMPSDLL ampspy::ampspy_type_object hybridpublishstore_type;

//    def __init__(self, name):
    static void* __ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      static const char* kwargs[] = { "filename", "maxMemoryCapacity", "errorOnPublishGap", "blockSize", NULL };
      char* filename = NULL;
      unsigned long maxMemoryCapacity = 0;
      unsigned long blockSize = 2048; // DEFAULT_BLOCK_SIZE
      PyObject* value = NULL;
      if (!PyArg_ParseTupleAndKeywords(args, kwds, "sk|O!k", (char**)kwargs, &filename, &maxMemoryCapacity, &PyBool_Type, &value, &blockSize))
      {
        return NULL;
      }
      assert(filename != NULL);
      bool errorOnPublishGap = value && value == Py_True;

      std::string fileName(filename);
      try
      {
        UNLOCKGIL;
        self->impl = new Store(new HybridPublishStore(fileName, (size_t)maxMemoryCapacity, blockSize, errorOnPublishGap));
      } DISPATCH_EXCEPTION;
      self->resizeHandler = NULL;
      return (void*)self;
    }

    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      if (__ctor(self, args, kwds) == NULL)
      {
        return -1;
      }
      return 0;
    }

    static void _dtor(obj* self)
    {
      {
        UNLOCKGIL;
        delete self->impl;
      }
      self->impl = 0;
      Py_XDECREF(self->resizeHandler);
      shims::free(self);
    }

    static PyObject* store(obj* self, PyObject* args)
    {
      Store* pStore = self->impl;
      PyObject* pPyMessage = NULL;
      if (!PyArg_ParseTuple(args, "O", &pPyMessage))
      {
        return NULL;
      }
      Message* pMessage = ((ampspy::message::obj*)pPyMessage)->pMessage;
      CALL_RETURN_UINT64_T(pStore->store(*pMessage));
    }

    static PyObject* discard_up_to(obj* self, PyObject* args)
    {
      Store* pStore = self->impl;
      unsigned long long seq = 0ULL;
      if (!PyArg_ParseTuple(args, "K", &seq))
      {
        return NULL;
      }
      CALL_RETURN_NONE(pStore->discardUpTo(seq));
    }

    class PyClientStoreReplayer : public AMPS::StoreReplayer
    {
      PyObject* _pPyHandler;
      ampspy::message::obj* _pMessage;
      PyObject* _pMessageArgs;
    public:
      PyClientStoreReplayer(PyObject* pPyHandler)
      : _pPyHandler(pPyHandler)
      {
        Py_INCREF(_pPyHandler);
        _pMessage = (ampspy::message::obj*)_PyObject_New(
                          ampspy::message::message_type);
        _pMessage->isOwned = false;
        assert(_pMessage);
        _pMessageArgs = Py_BuildValue("(O)", _pMessage);
        assert(_pMessageArgs);
      }

      virtual void execute(Message& message_)
      {
        LOCKGIL;
        _pMessage->pMessage = (Message*)&message_;
        PyObject* result = PyObject_Call(_pPyHandler, _pMessageArgs,
                                         (PyObject*)NULL);
        if (result == NULL)
        {
          if (PyErr_ExceptionMatches(PyExc_SystemExit))
          {
            ampspy::unhandled_exception();
          }
          else
          {
            // translate amps py exception into amps cpp, throw
            exc::throwError();
          }
        }
        else
        {
          Py_DECREF(result);
        }
      }

      virtual ~PyClientStoreReplayer()
      {
        Py_CLEAR(_pPyHandler);
        Py_CLEAR(_pMessage);
        Py_CLEAR(_pMessageArgs);
      }
    };

    static PyObject* replay(obj* self, PyObject* args)
    {
      Store* pStore = self->impl;
      PyObject* pOnMessage = NULL;
      if (!PyArg_ParseTuple(args, "O", &pOnMessage))
      {
        return NULL;
      }
      PyClientStoreReplayer replayer(pOnMessage);
      CALL_RETURN_NONE(pStore->replay(replayer));
    }

    static PyObject* replay_single(obj* self, PyObject* args)
    {
      Store* pStore = self->impl;
      PyObject* pOnMessage = NULL;
      unsigned long long seq = 0;
      if (!PyArg_ParseTuple(args, "OK", &pOnMessage, &seq))
      {
        return NULL;
      }
      PyClientStoreReplayer replayer(pOnMessage);
      CALL_RETURN_NONE(pStore->replaySingle(replayer, seq));
    }

    static PyObject* get_unpersisted_count(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T(self->impl->unpersistedCount());
    }

    static PyObject* get_lowest_unpersisted(obj* self, PyObject* args)
    {
      Store* pStore = self->impl;
      CALL_RETURN_UINT64_T(pStore->getLowestUnpersisted());
    }

    static PyObject* get_last_persisted(obj* self, PyObject* args)
    {
      Store* pStore = self->impl;
      CALL_RETURN_UINT64_T(pStore->getLastPersisted());
    }

    bool
    call_resize_handler(StoreImpl* store, size_t size, void* vp)
    {
      LOCKGIL;
      obj* s = (obj*)vp;
#if defined(_WIN32) && !defined(_WIN64)
      PyObject* args = Py_BuildValue("(Oi)", s, size);
#else
      PyObject* args = Py_BuildValue("(Ol)", s, size);
#endif
      PyObject* pyRet = PyObject_Call(s->resizeHandler, args, (PyObject*)NULL);
      Py_DECREF(args);
      if (pyRet == NULL || PyErr_Occurred())
      {
        Py_XDECREF(pyRet);
        if (PyErr_ExceptionMatches(PyExc_SystemExit))
        {
          ampspy::unhandled_exception();
        }
        throw StoreException("The resize handler threw an exception");
      }
      bool ret = (PyObject_IsTrue(pyRet) != 0);
      Py_DECREF(pyRet);
      return ret;
    }

    static PyObject* set_resize_handler(obj* self, PyObject* args)
    {
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (!PyCallable_Check(callable))
      {
        PyErr_SetString(PyExc_TypeError, "argument must be callable.");
        return NULL;
      }
      Py_INCREF(callable);
      if (self->resizeHandler)
      {
        Py_DECREF(self->resizeHandler);
      }
      self->resizeHandler = callable;
      CALL_RETURN_NONE(self->impl->setResizeHandler((AMPS::PublishStoreResizeHandler)call_resize_handler, self));
    }

    static PyObject* get_error_on_publish_gap(obj* self, PyObject* args)
    {
      CALL_RETURN_BOOL(self->impl->getErrorOnPublishGap());
    }

    static PyObject* set_error_on_publish_gap(obj* self, PyObject* args)
    {
      PyObject* value = NULL;
      if (!PyArg_ParseTuple(args, "O!", &PyBool_Type, &value))
      {
        return NULL;
      }
      CALL_RETURN_NONE(self->impl->setErrorOnPublishGap(value == Py_True));
    }

    void add_types(PyObject* module_)
    {
      hybridpublishstore_type.setName("AMPS.HybridPublishStore")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setDoc(hybridpublishstore_class_doc)
      .setBaseType()
      .notCopyable()
      .addMethod("store", store, store_doc)
      .addMethod("discard_up_to", discard_up_to, discard_up_to_doc)
      .addMethod("replay", replay, replay_doc)
      .addMethod("replay_single", replay_single, replay_single_doc)
      .addMethod("get_unpersisted_count", get_unpersisted_count, get_unpersisted_count_doc)
      .addMethod("get_lowest_unpersisted", get_lowest_unpersisted, get_lowest_unpersisted_doc)
      .addMethod("get_last_persisted", get_last_persisted, get_last_persisted_doc)
      .addMethod("set_resize_handler", set_resize_handler, set_resize_handler_doc)
      .addMethod("get_error_on_publish_gap", get_error_on_publish_gap, get_error_on_publish_gap_doc)
      .addMethod("set_error_on_publish_gap", set_error_on_publish_gap, set_error_on_publish_gap_doc)
      .createType()
      .registerType("HybridPublishStore", module_);

    }

  } // namespace hybridpublishstore
} // namespace ampspy
