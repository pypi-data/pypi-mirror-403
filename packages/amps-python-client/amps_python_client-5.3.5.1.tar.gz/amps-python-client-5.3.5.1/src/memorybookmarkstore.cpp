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
#include <amps/RecoveryPointAdapter.hpp>
#include "memorybookmarkstore_docs.h"
#include "ampspy_recoverypointadapter.hpp"

using namespace AMPS;
namespace ampspy
{
  namespace memorybookmarkstore
  {
//    def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      self->pAdapter = Py_None;
      if (!PyArg_ParseTuple(args, "|O", &self->pAdapter))
      {
        return -1;
      }
      if (self->pAdapter == Py_None)
      {
        // Create normally without an adapter
        self->impl = new BookmarkStore(new MemoryBookmarkStore());
      }
      else if (ampspy::conflatingrecoverypointadapter::type.isInstanceOf(self->pAdapter))
      {
        // A C++ RecoveryPointAdapter implementation; set it directly.
        Py_INCREF(self->pAdapter);
        self->impl = new BookmarkStore(new MemoryBookmarkStore(((ampspy::conflatingrecoverypointadapter::obj*)self->pAdapter)->adapter));
      }
      else if (ampspy::sowrecoverypointadapter::type.isInstanceOf(self->pAdapter))
      {
        Py_INCREF(self->pAdapter);
        // A C++ RecoveryPointAdapter implementation; set it directly.
        self->impl = new BookmarkStore(new MemoryBookmarkStore(((ampspy::sowrecoverypointadapter::obj*)self->pAdapter)->adapter));
      }
      else
      {
        // Assume this is a python object that implements the required
        // recovery point adapter methods. If it does not, the first missing
        // method will result in an exception.
        Py_INCREF(self->pAdapter);
        self->impl = new BookmarkStore(new MemoryBookmarkStore(RecoveryPointAdapter(new recoverypointadapter::wrapper(self->pAdapter), false)));
      }
      return 0;
    }

    static void _dtor(obj* self)
    {
      {
        UNLOCKGIL;
        delete self->impl;
      }
      Py_XDECREF(self->resizeHandler);
      Py_XDECREF(self->pAdapter);
      shims::free(self);
    }

    static PyObject*
    log(obj* self, PyObject* args)
    {
      ampspy::message::obj* pPythonMessage = NULL;
      if (!PyArg_ParseTuple(args, "O!",
                            ampspy::message::message_type.pPyObject(),
                            &pPythonMessage))
      {
        return NULL;
      }

      AMPS::Message* pMessage = pPythonMessage->pMessage;

      CALL_RETURN_SIZE_T(self->impl->log(*pMessage));
    }

    static PyObject*
    discard_message(obj* self, PyObject* args)
    {
      ampspy::message::obj* pPythonMessage = NULL;
      if (!PyArg_ParseTuple(args, "O!",
                            ampspy::message::message_type.pPyObject(),
                            &pPythonMessage))
      {
        return NULL;
      }

      AMPS::Message* pMessage = pPythonMessage->pMessage;

      CALL_RETURN_NONE(self->impl->discard(*pMessage));
    }

    static PyObject*
    discard(obj* self, PyObject* args)
    {
      const char*           subId       = NULL;
      Py_ssize_t            subIdLength = 0;
      unsigned PY_LONG_LONG sequence    = 0;

      if (!PyArg_ParseTuple(args, "s#K",
                            &subId,
                            &subIdLength,
                            &sequence))
      {
        return NULL;
      }

      CALL_RETURN_NONE(self->impl->discard(AMPS::Field(subId, subIdLength),
                                           (size_t)sequence));
    }

    static PyObject*
    get_most_recent(obj* self, PyObject* args)
    {
      const char*  subId          = NULL;
      Py_ssize_t   subIdLength    = 0;

      if (!PyArg_ParseTuple(args, "s#",
                            &subId,
                            &subIdLength))
      {
        return NULL;
      }

      // getMostRecent returns a Field that must be cleared
      AMPS::Field recent = self->impl->getMostRecent(AMPS::Field(subId,
                                                                 subIdLength));
      std::string recentStr = (std::string)recent;
      recent.clear();
      CALL_RETURN_STRING(recentStr);
    }

    static PyObject*
    is_discarded(obj* self, PyObject* args)
    {
      ampspy::message::obj* pPythonMessage = NULL;
      if (!PyArg_ParseTuple(args, "O!",
                            ampspy::message::message_type.pPyObject(),
                            &pPythonMessage))
      {
        return NULL;
      }

      AMPS::Message* pMessage = pPythonMessage->pMessage;
      CALL_RETURN_BOOL(self->impl->isDiscarded(*pMessage));
    }

    static PyObject*
    persisted(obj* self, PyObject* args)
    {
      const char*  subId          = NULL;
      Py_ssize_t   subIdLength    = 0;
      const char*  bookmark       = NULL;
      Py_ssize_t   bookmarkLength = 0;

      if (!PyArg_ParseTuple(args, "s#s#",
                            &subId,
                            &subIdLength,
                            &bookmark,
                            &bookmarkLength))
      {
        return NULL;
      }

      CALL_RETURN_NONE(self->impl->persisted(
                         AMPS::Field(subId, subIdLength),
                         AMPS::Field(bookmark, bookmarkLength)));
    }

    static PyObject*
    persisted_index(obj* self, PyObject* args)
    {
      const char*           subId          = NULL;
      Py_ssize_t            subIdLength    = 0;
      unsigned PY_LONG_LONG bookmark       = 0;

      if (!PyArg_ParseTuple(args, "s#K",
                            &subId,
                            &subIdLength,
                            &bookmark))
      {
        return NULL;
      }

      CALL_RETURN_NONE(self->impl->persisted(
                         AMPS::Field(subId, subIdLength),
                         (size_t)bookmark));
    }

    static PyObject*
    purge(obj* self, PyObject* args)
    {
      CALL_RETURN_NONE(self->impl->purge());
    }

    static PyObject*
    purge_sub_id(obj* self, PyObject* args)
    {
      const char*           subId       = NULL;
      Py_ssize_t            subIdLength = 0;

      if (!PyArg_ParseTuple(args, "s#",
                            &subId,
                            &subIdLength))
      {
        return NULL;
      }

      CALL_RETURN_NONE(self->impl->purge(AMPS::Field(subId, subIdLength)));
    }

    static PyObject*
    get_oldest_bookmark_seq(obj* self, PyObject* args)
    {
      const char*  subId          = NULL;
      Py_ssize_t   subIdLength    = 0;

      if (!PyArg_ParseTuple(args, "s#",
                            &subId,
                            &subIdLength))
      {
        return NULL;
      }

      CALL_RETURN_SIZE_T(self->impl->getOldestBookmarkSeq(
                           AMPS::Field(subId, subIdLength)));
    }

    static PyObject*
    set_server_version(obj* self, PyObject* args)
    {
      unsigned PY_LONG_LONG version = 0;

      if (!PyArg_ParseTuple(args, "K",
                            &version))
      {
        return NULL;
      }

      CALL_RETURN_NONE(self->impl->setServerVersion((size_t)version));
    }

    bool
    call_resize_handler(BookmarkStoreImpl* store, const Message::Field& subId,  size_t size, void* vp)
    {
      LOCKGIL;
      obj* s = (obj*)vp;
      PyObject* pySubId = PyString_FromStringAndSize(subId.data(), subId.len());
#if defined(_WIN32) && !defined(_WIN64)
      PyObject* args = Py_BuildValue("(OiO)", s, size, pySubId);
#else
      PyObject* args = Py_BuildValue("(OlO)", s, size, pySubId);
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
        throw StoreException("The bookmark resize handler threw an exception");
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
      Py_XDECREF(self->resizeHandler);
      self->resizeHandler = callable;
      CALL_RETURN_NONE(self->impl->setResizeHandler((AMPS::BookmarkStoreResizeHandler)call_resize_handler, self));
    }

    AMPSDLL ampspy::ampspy_type_object memorybookmarkstore_type;
    void add_types(PyObject* module_)
    {
      memorybookmarkstore_type.setName("AMPS.MemoryBookmarkStore")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setBaseType()
      .setDoc(memorybookmarkstore_class_doc)
      .notCopyable()
      .addMethod("log", log,
                 "log(message)\n\n"
                 "Log a bookmark to the log and return the corresponding sequence "
                 "number.\n")
      .addMethod("discard_message", discard_message,
                 "discard_message(message)\n\n"
                 "Log a message as discarded from the store.\n")
      .addMethod("discard", discard,
                 "discard(subid,sequence)\n\n"
                 "Log a discard-bookmark entry to the persisted log.")
      .addMethod("get_most_recent", get_most_recent,
                 "get_most_recent(subid)\n\n"
                 "Returns the most recent bookmark from the log, which is used\n"
                 "when placing a subscription.\n")
      .addMethod("is_discarded", is_discarded,
                 "is_discarded(message)\n\n"
                 "Called for each arriving message to determine if the application has\n"
                 "already seen this bookmark and should not be reprocessed. Returns\n"
                 "True if the bookmark is in the log and should not be re-processed;\n"
                 "False otherwise.\n")
      .addMethod("persisted", persisted,
                 "persisted(subid, bookmark)\n\n"
                 "Mark all bookmarks up to the provided one as replicated to all\n"
                 "replication destinations for the given subscription.\n")
      .addMethod("persisted_index", persisted_index,
                 "persisted_index(subid, bookmark_index)\n\n"
                 "Mark all bookmarks up to the provided index as replicated to all\n"
                 "replication destinations for the given subscription.\n")
      .addMethod("purge", purge,
                 "purge()\n\n"
                 "Called to purge the contents of this store. Removes any tracking\n"
                 "history associated with publishers and received messages, and may\n"
                 "delete or truncate on-disk representations as well.\n")
      .addMethod("purge_sub_id", purge_sub_id,
                 "purge_sub_id()\n\n"
                 "Called to purge the contents of this store for a given subscription\n"
                 "ID. Removes any tracking history associated with publishers and \n"
                 "received messages, and may delete or truncate on-disk representations\n"
                 "as well.\n")
      .addMethod("get_oldest_bookmark_seq", get_oldest_bookmark_seq,
                 "get_oldest_bookmark_seq(subid)\n\n"
                 "Called to find the oldest bookmark sequence in the store.\n")
      .addMethod("set_server_version", set_server_version,
                 "set_server_version(version)\n\n"
                 "Internally used to set the server version so the store knows how to\n"
                 "deal with persisted acks and calls to ``get_most_recent()``.\n")
      .addMethod("set_resize_handler", set_resize_handler,
                 "set_resize_handler()\n\n"
                 "Sets the object to call when the store needs to resize.\n")
      .createType()
      .registerType("MemoryBookmarkStore", module_);
    }

  } // namespace memorybookmarkstore
} // namespace ampspy
