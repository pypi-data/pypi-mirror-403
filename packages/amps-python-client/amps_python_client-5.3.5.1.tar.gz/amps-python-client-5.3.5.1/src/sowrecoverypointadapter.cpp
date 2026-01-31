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
#include <amps/SOWRecoveryPointAdapter.hpp>

using namespace AMPS;
namespace ampspy
{
  namespace sowrecoverypointadapter
  {
//    def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      static const char* kwlist[] = { "store_client", "tracked_client_name",
                                      "timeout_millis", "use_timestamp"
                                      "close_client", "update_failure_throws",
                                      "topic", "client_name_field",
                                      "sub_id_field", "bookmark_field", NULL
                                    };
      PyObject* pStoreClient = NULL;
      char* trackedClientName = NULL;
      int timeoutMillis = 5000;
      char useTimestamp = (char)false;
      char closeClient = (char)true;
      char updateFailureThrows = (char)false;
      char* topic = (char*)AMPS_SOW_STORE_DEFAULT_TOPIC;
      char* clientNameField = (char*)AMPS_SOW_STORE_DEFAULT_CLIENT_FIELD;
      char* subIdField = (char*)AMPS_SOW_STORE_DEFAULT_SUB_FIELD;
      char* bookmarkField = (char*)AMPS_SOW_STORE_DEFAULT_BOOKMARK_FIELD;
      if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)"Os|ibbbssss", (char**)kwlist, &pStoreClient, &trackedClientName, &timeoutMillis, &useTimestamp, &closeClient, &updateFailureThrows, &topic,
                                       &clientNameField, &subIdField, &bookmarkField))
      {
        return -1;
      }
      client::obj* pClient = (client::obj*)pStoreClient;
      self->pImpl = std::make_shared<SOWRecoveryPointAdapter>(
                      *(pClient->pClient),
                      trackedClientName,
                      (unsigned)timeoutMillis,
                      useTimestamp != 0,
                      closeClient != 0,
                      updateFailureThrows != 0,
                      topic,
                      clientNameField,
                      subIdField,
                      bookmarkField);
      self->adapter = RecoveryPointAdapter(self->pImpl.get(), false);
      return 0;
    }

    static void _dtor(obj* self)
    {
      {
        UNLOCKGIL;
        self->pImpl.reset();
      }
      self->exceptionListener.reset();
      shims::free(self);
    }

//    def set_exception_listener(self, exception_listener):
    static PyObject* set_exception_listener(obj* self, PyObject* args)
    {
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (!PyCallable_Check(callable) && callable != Py_None)
      {
        PyErr_SetString(PyExc_TypeError, "argument must be callable.");
        return NULL;
      }
      // the ctor/dtor of pyexceptionlistener takes care of reference counts
      self->exceptionListener.reset();
      if (callable == Py_None)
      {
        self->exceptionListener = std::make_shared<PyExceptionListener>();
      }
      else
      {
        self->exceptionListener = std::make_shared<PyExceptionListener>(callable);
      }
      CALL_RETURN_NONE(((AMPS::SOWRecoveryPointAdapter*)(self->pImpl.get()))
                       ->setExceptionListener(self->exceptionListener));
    }

    static PyObject* get_exception_listener(obj* self, PyObject* args)
    {
      if (self->exceptionListener)
      {
        PyObject* object = (PyObject*) ((PyExceptionListener*)(self->exceptionListener.get()))->callable();
        if (object)
        {
          Py_INCREF(object);
          return object;
        }
      }
      NONE;
    }

    static PyObject* next(obj* self, PyObject* args)
    {
      RecoveryPoint current;
      bool hasNext = false;
      CALL_AND_CAPTURE_RETURN_VALUE(self->pImpl->next(current), hasNext);
      PyObject* pRecoveryPoint = NULL;
      recoverypoint::obj* pRecoverypointObj = PyObject_New(recoverypoint::obj, recoverypoint::type);
      pRecoveryPoint = (PyObject*)pRecoverypointObj;
      if (hasNext)
      {
        pRecoverypointObj->subId = strdup(((std::string)(current.getSubId())).c_str());
        pRecoverypointObj->bookmark = strdup(((std::string)(current.getBookmark())).c_str());
      }
      return pRecoveryPoint;
    }

    static PyObject* update(obj* self, PyObject* args)
    {
      ampspy::recoverypoint::obj* pRecoveryPoint = NULL;
      if (!PyArg_ParseTuple(args, "O!",
                            &ampspy::recoverypoint::type,
                            &pRecoveryPoint))
      {
        return NULL;
      }
      RecoveryPoint rp(new FixedRecoveryPoint(pRecoveryPoint->subId,
                                              pRecoveryPoint->bookmark));
      CALL_RETURN_NONE(self->pImpl->update(rp));
    }

// def purge() or purge(subId)
    static PyObject* purge(obj* self, PyObject* args)
    {
      char* subId = NULL;
      if (!PyArg_ParseTuple(args, "|s", &subId))
      {
        return NULL;
      }
      if (subId == NULL)
      {
        CALL_RETURN_NONE(self->pImpl->purge());
      }
      else
      {
        CALL_RETURN_NONE(self->pImpl->purge(subId));
      }
    }

    static PyObject* close(obj* self, PyObject* args)
    {
      CALL_RETURN_NONE(self->pImpl->close());
    }

    static PyObject* prune(obj* self, PyObject* args)
    {
      CALL_RETURN_NONE(self->pImpl->prune());
    }

    static const char* sowrecoverypointadapter_class_doc = R"docstring(
    This class can be used as an adapter on an :class:`AMPS.MemoryBookmarkStore`
    to save enough recovery state information to guarantee no missed
    messages. It must be constructed with a client using json message
    type, connected and logged on to a server on which the chosen topic
    is defined as a SOW topic with key fields equivalent to the chosen
    client name field and sub id field. It also must not be the same
    client that is being tracked, whose name is provided as the
    tracked client name.
    )docstring";

    AMPSDLL ampspy::ampspy_type_object type;

    void add_types(PyObject* module_)
    {
      type.setName("AMPS.SOWRecoveryPointAdapter")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setBaseType()
      .setConstructorFunction(_ctor)
      .setDoc(sowrecoverypointadapter_class_doc)
      .notCopyable()
      .addMethod("set_exception_listener", set_exception_listener,
                 "set_exception_listener(exception_listener)\n\n"
                 "Sets the exception listener instance used for communicating\n"
                 "absorbed exceptions.\n\n"
                 ":param exception_listener: The exception listener instance to invoke\n"
                 "                           for exceptions.\n"
                 ":type exception_listener: :exc:`Exception`\n")
      .addMethod("get_exception_listener", get_exception_listener,
                 "get_exception_listener()\n\n"
                 "Gets the exception listener callable set on self.\n\n"
                 ":returns: The exception listener callable set on self, or None.")
      .addMethod("next", next,
                 "next()\n\n"
                 "Returns the next :class:`RecoveryPoint` from the SOW or an empty one if\n"
                 "recovery has completed.\n")
      .addMethod("update", update,
                 "update(recovery_point)\n\n"
                 "Updates the SOW with the new information in ``recovery_point``.\n\n"
                 ":param recovery_point: The new recovery information to save.\n"
                 ":type recovery_point: recoveryPoint\n")
      .addMethod("purge", purge,
                 "purge(sub_id)\n\n"
                 "If ``sub_id`` is provided, remove all records related to ``sub_id``.\n"
                 "If no ``sub_id`` is provided, remove all records for this client.\n\n"
                 ":param sub_id: The optional ``sub_id`` to remove or all if none.\n")
      .addMethod("close", close,
                 "close(subid, bookmark)\n\n"
                 "Close the store so it can no longer be used. May close the\n"
                 "store client if that option was true when constructed.\n")
      .addMethod("prune", prune,
                 "prune()\n\n"
                 "This has no affect on a :class:`SOWRecoveryPointAdapter`.\n")
      .createType()
      .registerType("SOWRecoveryPointAdapter", module_);
    }

  } // namespace sowrecoverypointadapter
} // namespace ampspy
