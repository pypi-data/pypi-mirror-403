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
#include <amps/Field.hpp>
#include <amps/RecoveryPoint.hpp>
#include <ampspy_types.hpp>
#include <ampspy_defs.hpp>

namespace ampspy
{
  namespace recoverypoint
  {

    // __init__(subId, bookmark)
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      static const char* kwlist[] = { "subId", "bookmark", NULL };
      char* subId    = NULL;
      char* bookmark = NULL;

      self->subId     = NULL;
      self->bookmark  = NULL;
      if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ss", (char**)&kwlist,
                                       &(subId), &(bookmark)))
      {
        return -1;
      }
      if (subId != NULL)
      {
        self->subId = strdup(subId);
      }
      if (bookmark != NULL)
      {
        self->bookmark = strdup(bookmark);
      }
      return 0;
    }

    static void _dtor(obj* self)
    {
      free(self->subId);
      free(self->bookmark);
      self->subId = NULL;
      self->bookmark = NULL;
      shims::free(self);
    }

    static PyObject* get_sub_id(obj* self, PyObject* args)
    {
      if (self->subId)
      {
        return ret(self->subId);
      }
      Py_INCREF(Py_None);
      return Py_None;
    }

    static PyObject* get_bookmark(obj* self, PyObject* args)
    {
      if (self->bookmark)
      {
        return ret(self->bookmark);
      }
      Py_INCREF(Py_None);
      return Py_None;
    }

    static PyObject* __copy__(obj* self, PyObject* args)
    {
      PyObject* pRecoveryPoint = NULL;
      recoverypoint::obj* pRecoverypointObj = PyObject_New(recoverypoint::obj, recoverypoint::type);
      pRecoveryPoint = (PyObject*)pRecoverypointObj;
      pRecoverypointObj->subId = strdup(self->subId);
      pRecoverypointObj->bookmark = strdup(self->bookmark);
      return pRecoveryPoint;
    }

    static PyObject* __deepcopy__(obj* self, PyObject* args)
    {
      PyObject* pRecoveryPoint = NULL;
      recoverypoint::obj* pRecoverypointObj = PyObject_New(recoverypoint::obj, recoverypoint::type);
      pRecoveryPoint = (PyObject*)pRecoverypointObj;
      pRecoverypointObj->subId = strdup(self->subId);
      pRecoverypointObj->bookmark = strdup(self->bookmark);
      return pRecoveryPoint;
    }
    static const char* recoverypoint_class_doc = R"docstring(
    This class represents a subscription's recovery point. It consists
    of a ``sub_id`` and a ``bookmark``, which is opaque.
    )docstring";

    AMPSDLL ampspy::ampspy_type_object type;

    void add_types(PyObject* module_)
    {
      type.setName("AMPS.RecoveryPoint")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setDoc(recoverypoint_class_doc)
      .addMethod("__deepcopy__", __deepcopy__, "Returns a deep copy of self.")
      .addMethod("__copy__", __copy__, "Returns a shallow copy of self.")
      .addMethod("get_sub_id", get_sub_id, "Returns the ``sub_id`` of this :class:`RecoveryPoint`.")
      .addMethod("get_bookmark", get_bookmark, "Returns the ``bookmark`` for this :class:`RecoveryPoint`.")
      .createType()
      .registerType("RecoveryPoint", module_);
    }

  } // namespace recoverypoint
} // namespace ampspy


