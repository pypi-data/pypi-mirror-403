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
#include <ampspy_bookmarkstore.hpp>

namespace ampspy
{
  namespace bookmarkstore
  {
    wrapper::wrapper(PyObject* object_)
    {
      assert(object_);
      _pImpl = object_;
      Py_INCREF(_pImpl);
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
    size_t wrapper::log(AMPS::Message& message_)
    {
      LockGIL lockGil;
      PyObject* pPythonMessage = ampspy::message::toPythonMessage(message_);

      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"log", (char*)"(O)",
                                              pPythonMessage);

      if (pResult == NULL)
      {
        exc::throwError();
      }

      size_t result =
        static_cast<size_t>(PyInt_AsUnsignedLongLongMask(pResult));
      Py_XDECREF(pResult);
      Py_DECREF(pPythonMessage);

      return result;
    }

    void wrapper::discard(const AMPS::Message::Field& subId_,
                          size_t bookmarkSeqNo_)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"discard",
                                              (char*)"(s#K)",
                                              subId_.data(), subId_.len(),
                                              bookmarkSeqNo_);

      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    void wrapper::discard(const AMPS::Message& message_)
    {
      LockGIL lockGil;
      // Casting away const because there's no concept of a const object in Python
      PyObject* pPythonMessage = ampspy::message::toPythonMessage(
                                   const_cast<AMPS::Message&>(message_));
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"discard_message",
                                              (char*)"(O)", pPythonMessage);
      Py_DECREF(pPythonMessage);
      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    AMPS::Message::Field wrapper::getMostRecent(const AMPS::Message::Field& subId_)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"get_most_recent",
                                              (char*)"(s#)",
                                              subId_.data(), subId_.len());
      if (pResult == NULL)
      {
        exc::throwError();
      }
      char* buffer = NULL;
      Py_ssize_t length = 0;
      PyString_AsStringAndSize(pResult, &buffer, &length);
      // The returned buffer is cached in the Unicode object and will be freed
      // when that goes out of scope. We need to return a new buffer.
#ifdef _WIN32
      buffer = _strdup(buffer);
#else
      buffer = strdup(buffer);
#endif
      AMPS::Message::Field result(buffer, length);

      Py_XDECREF(pResult);
      return result;
    }

    bool wrapper::isDiscarded(AMPS::Message& message_)
    {
      LockGIL lockGil;
      PyObject* pPythonMessage = ampspy::message::toPythonMessage(message_);
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"is_discarded",
                                              (char*)"(O)", pPythonMessage);
      Py_DECREF(pPythonMessage);
      if (pResult == NULL)
      {
        exc::throwError();
      }

      bool result = pResult == Py_True;
      Py_XDECREF(pResult);
      return result;
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
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"purge_sub_id",
                                              (char*)"(s#)",
                                              subId_.data(), subId_.len());
      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    size_t wrapper::getOldestBookmarkSeq(const AMPS::Message::Field& subId_)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl,
                                              (char*)"get_oldest_bookmark_seq",
                                              (char*)"(s#)", subId_.data(), subId_.len());

      if (pResult == NULL)
      {
        exc::throwError();
      }
      size_t result = static_cast<size_t>(PyInt_AsUnsignedLongLongMask(pResult));
      Py_XDECREF(pResult);

      return result;
    }

    void wrapper::persisted(const AMPS::Message::Field& subId_,
                            const AMPS::Message::Field& bookmark_)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"persisted",
                                              (char*)"(s#s#)", subId_.data(), subId_.len(),
                                              bookmark_.data(), bookmark_.len());
      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }

    AMPS::Message::Field wrapper::persisted(const AMPS::Message::Field& subId_,
                                            size_t bookmark_)
    {
      // This is not called by the client.
      assert(false);
      return AMPS::Message::Field();
    }

    void wrapper::setServerVersion(const AMPS::VersionInfo& version_)
    {
      setServerVersion(version_.getOldStyleVersion());
    }

    void wrapper::setServerVersion(size_t version_)
    {
      LockGIL lockGil;
      PyObject* pResult = PyObject_CallMethod(_pImpl, (char*)"set_server_version",
                                              (char*)"(K)", version_);
      if (pResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(pResult);
      }
    }
  } // namespace bookmarkstore
} // namespace ampspy


