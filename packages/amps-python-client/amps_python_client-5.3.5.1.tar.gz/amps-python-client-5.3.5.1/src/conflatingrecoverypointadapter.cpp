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
#include "ampspy_recoverypointadapter.hpp"

using namespace AMPS;
namespace ampspy
{
  namespace conflatingrecoverypointadapter
  {

    AMPSDLL ampspy::ampspy_type_object type;

//    def __init__(self, delegate, update_threshold, timeout_millis,
//                 update_interval_millis):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      static const char* kwlist[] = { "delegate", "update_threshold",
                                      "timeout_millis", "update_interval_millis",
                                      NULL
                                    };
      int updateThreshold = 10;
      double timeoutMillis = 2000.0;
      long updateIntervalMillis = 2000;
      if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)"O|idl", (char**)kwlist,
                                       &(self->pDelegate), &updateThreshold,
                                       &timeoutMillis, &updateIntervalMillis))
      {
        return -1;
      }
      if (sowrecoverypointadapter::type.isInstanceOf(self->pDelegate))
      {
        Py_INCREF(self->pDelegate);
        self->pImpl = new ConflatingRecoveryPointAdapter(
          ((sowrecoverypointadapter::obj*)(self->pDelegate))->pImpl,
          (unsigned)updateThreshold,
          timeoutMillis,
          updateIntervalMillis);
      }
      else
      {
        self->pImpl = new ConflatingRecoveryPointAdapter(
          std::make_shared<recoverypointadapter::wrapper>(self->pDelegate),
          (unsigned)updateThreshold,
          timeoutMillis,
          updateIntervalMillis);
        // pDelegate is managed by wrapper now
        self->pDelegate = nullptr;
      }
      self->adapter = RecoveryPointAdapter(self->pImpl, false);
      return 0;
    }

    static void _dtor(obj* self)
    {
      {
        UNLOCKGIL;
        self->adapter = RecoveryPointAdapter();
        delete self->pImpl;
      }
      Py_XDECREF(self->pDelegate);
      shims::free(self);
    }

    static PyObject* next(obj* self, PyObject* args)
    {
      RecoveryPoint current;
      bool hasNext = false;
      CALL_AND_CAPTURE_RETURN_VALUE(self->pImpl->next(current), hasNext);
      PyObject* pRecoveryPoint = NULL;
      recoverypoint::obj* pRecoverypointObj = PyObject_New(recoverypoint::obj,
                                                           recoverypoint::type);
      pRecoveryPoint = (PyObject*)pRecoverypointObj;
      if (hasNext)
      {
        pRecoverypointObj->subId = strdup(((std::string)(current.getSubId())).c_str());
        pRecoverypointObj->bookmark = strdup(((std::string)(current.getBookmark())).c_str());
      }
      else
      {
        pRecoverypointObj->subId = NULL;
        pRecoverypointObj->bookmark = NULL;
      }
      return pRecoveryPoint;
    }

    static PyObject* update(obj* self, PyObject* args)
    {
      ampspy::recoverypoint::obj* pPythonRecoveryPoint = NULL;
      if (!PyArg_ParseTuple(args, "O!",
                            recoverypoint::type.pPyObject(),
                            &pPythonRecoveryPoint))
      {
        return NULL;
      }
      RecoveryPoint recoveryPoint(new FixedRecoveryPoint(
                                    pPythonRecoveryPoint->subId,
                                    pPythonRecoveryPoint->bookmark));
      CALL_RETURN_NONE(self->pImpl->update(recoveryPoint));
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

    static const char* conflatingrecoverypointadapter_class_doc = R"docstring(
    This class can be used as an adapter on an :class:`AMPS.MemoryBookmarkStore`.
    It is a pass-through to another adapter type that provides conflation of
    updates to help reduce the load on the underlying adapter. Conflation can be
    on an interval, a set number of updates or both.
    )docstring";

    void add_types(PyObject* module_)
    {
      type.setName("AMPS.ConflatingRecoveryPointAdapter")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setBaseType()
      .setDoc(conflatingrecoverypointadapter_class_doc)
      .notCopyable()
      .addMethod("next", next,
                 "next()\n\n"
                 "Returns the next :class:`RecoveryPoint` from the delegate or an empty one if\n"
                 "recovery has completed.\n")
      .addMethod("update", update,
                 "update(recovery_point)\n\n"
                 "Conflate the new information in ``recovery_point``.\n\n"
                 ":param recovery_point: The new recovery information to save.\n"
                 ":type recovery_point: recoveryPoint\n")
      .addMethod("purge", purge,
                 "purge(sub_id)\n\n"
                 "If ``sub_id`` is provided, remove all records related to ``sub_id``.\n"
                 "If no ``sub_id`` is provided, remove all records for this client.\n\n"
                 ":param sub_id: The optional ``sub_id`` to remove or all if none.\n")
      .addMethod("close", close,
                 "close(subid, bookmark)\n\n"
                 "Close the delegate.\n")
      .addMethod("prune", prune,
                 "prune()\n\n"
                 "Tell the delegate to prune.\n")
      .createType()
      .registerType("ConflatingRecoveryPointAdapter", module_);
    }

  } // namespace conflatingrecoverypointadapter
} // namespace ampspy
