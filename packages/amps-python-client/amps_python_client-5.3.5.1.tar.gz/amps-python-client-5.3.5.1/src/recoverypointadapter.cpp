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
#include <amps/Field.hpp>
#include <amps/RecoveryPoint.hpp>
#include "ampspy_recoverypointadapter.hpp"

namespace ampspy
{
  namespace recoverypointadapter
  {
    wrapper::wrapper(PyObject* object_)
    {
      assert(object_);
      _pImpl = object_;
      Py_INCREF(_pImpl);
      _closed = false;
    }

    wrapper::~wrapper(void)
    {
      try
      {
        LockGIL lockGil;
        Py_DECREF(_pImpl);
      }
      catch (...)
      {
        ;
      }
      _pImpl = NULL;
    }

    bool wrapper::next(AMPS::RecoveryPoint& current_)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"next", (char*)"()");

      if (pResult == NULL)
      {
        exc::throwError();
      }

      recoverypoint::obj* pRecoveryPoint = (recoverypoint::obj*)pResult;
      bool result = pRecoveryPoint->subId != NULL
                    && pRecoveryPoint->bookmark != NULL;
      if (result)
      {
        current_ = AMPS::RecoveryPoint(new AMPS::FixedRecoveryPoint(
                                         pRecoveryPoint->subId,
                                         pRecoveryPoint->bookmark,
                                         true));
      }
      else
      {
        current_ = AMPS::RecoveryPoint(NULL);
      }
      Py_XDECREF(pResult);
      return result;
    }

    void wrapper::update(AMPS::RecoveryPoint& recoveryPoint_)
    {
      LockGIL lockGil;
      static PyObject* pUpdateString = PyString_FromString("update");
      PyObject* pRecoveryPoint = NULL;
      recoverypoint::obj* pRecoveryPointObj = PyObject_New(recoverypoint::obj, recoverypoint::type);
      pRecoveryPoint = (PyObject*)pRecoveryPointObj;
      pRecoveryPointObj->subId = strdup(((std::string)(recoveryPoint_.getSubId())).c_str());
      pRecoveryPointObj->bookmark = strdup(((std::string)(recoveryPoint_.getBookmark())).c_str());
      PyObject* pResult = PyObject_CallMethodObjArgs(_pImpl, pUpdateString, pRecoveryPoint, NULL);

      Py_DECREF(pRecoveryPoint);
      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    void wrapper::purge(void)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"purge", (char*)"()");

      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    void wrapper::purge(const AMPS::Message::Field& subId_)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"purge", (char*)"(s#)", (char*)subId_.data(), subId_.len());

      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    void wrapper::close(void)
    {
      if (_closed)
      {
        return;
      }
      _closed = true;
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"close", (char*)"()");

      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    void wrapper::prune(void)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"prune", (char*)"()");

      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

  } // namespace recoverypointadapter
} // namespace ampspy


