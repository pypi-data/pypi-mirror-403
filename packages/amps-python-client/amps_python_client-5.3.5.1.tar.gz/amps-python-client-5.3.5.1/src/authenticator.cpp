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
  namespace authenticator
  {
    ampspy::ampspy_type_object authenticator_type;

    // def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      return 0;
    }
    static void _dtor(obj* self)
    {
      shims::free(self);
    }

    // wait, why are these here?
    // really only here in case someone wants to derive DefaultAuthenticator in python,
    // and they call the base class.  otherwise, it's us calling them.
    static PyObject* authenticate(obj* self, PyObject* args)
    {
      const char* username, *password;
      if (!PyArg_ParseTuple(args, "ss", &username, &password))
      {
        return NULL;
      }

      return ret(password);
    }

    static PyObject* retry(obj* self, PyObject* args) // -V524
    {
      const char* username, *password;
      if (!PyArg_ParseTuple(args, "ss", &username, &password))
      {
        return NULL;
      }

      return ret(password);
    }

    static PyObject* completed(obj* self, PyObject* /*args*/)
    {
      NONE;
    }

    static const char* authenticate_doc = R"docstring(authenticate(username,password)
    Authenticates self to an external system.

    :param username: The current username supplied in a URI.
    :type username: str
    :param password: The current password supplied in a  URI.
    :type password: str
    :returns: The new password to be sent to the server in the logon request.
    )docstring";

    static const char* retry_doc = R"docstring(retry(username, password)
    Called when the server indicates a retry is necessary to complete authentication.

    :param username: The username supplied to the server.
    :type username: str
    :param password: The password or authentication token returned by the server in the last logon request.
    :type password: str
    :returns: The new password or authentication token to be sent to the server.
    )docstring";

    static const char* completed_doc = R"docstring(completed(username, password, reason)
    Called when authentication is completed, with the username and password returned by the server in the final acknowledgement for the logon sequence.

    :param username: The username returned by the server
    :type username: str
    :param password: The password or authentication token returned by the server in the last logon request.
    :type password: str
    :param reason: The reason the server provided for finishing the logon sequence. (For example, the logon might have succeeded, authentication might be disabled, and so on.)
    :type reason: str
    )docstring";

    void add_types(PyObject* module_)
    {
      authenticator_type.setName("AMPS.DefaultAuthenticator")
      .setBasicSize(sizeof(obj))
      .setBaseType()
      .setConstructorFunction(&_ctor)
      .setDestructorFunction(&_dtor)
      .setDoc("AMPS Authenticator Object")
      .addMethod("authenticate", authenticate, authenticate_doc)
      .addMethod("retry", retry, retry_doc)
      .addMethod("completed", completed, completed_doc)
      .notCopyable()
      .createType()
      .registerType("DefaultAuthenticator", module_);
    }

  } // namespace authenticator
} // namespace ampspy