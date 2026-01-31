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

#include "serverchooser_docs.h"

using namespace AMPS;
namespace ampspy
{
  namespace serverchooser
  {

//    def __init__(self, name):
    static int ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      self->impl = new AMPS::DefaultServerChooser();
      return 0;
    }
    static void dtor(obj* self)
    {
      delete self->impl;
      shims::free(self);
    }

#define M(x,desc) { #x, (PyCFunction)&x,METH_VARARGS, desc}
#define M2(x,x2,desc) { x2, (PyCFunction)&x,METH_VARARGS, desc}
#define MK(x,desc) { #x, (PyCFunction)&x,METH_VARARGS|METH_KEYWORDS, desc}
#define MK2(x,x2,desc) { x2, (PyCFunction)&x,METH_VARARGS|METH_KEYWORDS, desc}

    static PyObject* add(obj* self, PyObject* args)
    {
      const char* uri;
      if (!PyArg_ParseTuple(args, "s", &uri))
      {
        return NULL;
      }

      self->impl->add(uri);
      NONE;
    }

    class PyListContainer
    {
    public:
      class const_iterator
      {
      public:
        const char* operator*()
        {
          PyObject* strObj = PyList_GetItem(_list, _next);
          if (PyString_Check(strObj))
          {
            return PyString_AsString(strObj);
          }
          return NULL;
        }
        const_iterator& operator++()
        {
          ++_next;
          return *this;
        }
        bool operator!=(const const_iterator& rhs_) const
        {
          return _next != rhs_._next || _list != rhs_._list;
        }
        bool operator==(const const_iterator& rhs_) const
        {
          return _next == rhs_._next && _list == rhs_._list;
        }
        const_iterator(PyObject* list_, bool end_ = false)
          : _list(list_), _next(0)
        {
          if (end_)
          {
            _next = PyList_Size(_list);
          }
        }
      private:
        PyObject* _list;
        size_t _next;
      };
      PyListContainer(PyObject* list_) : _list(list_) {}
      const_iterator begin() const
      {
        return const_iterator(_list);
      }
      const_iterator end() const
      {
        return const_iterator(_list, true);
      }
    private:
      PyObject* _list;
    };

    static PyObject* add_all(obj* self, PyObject* args)
    {
      PyObject* list;
      if (!PyArg_ParseTuple(args, "O", &list))
      {
        return NULL;
      }
      if (!PyList_Check(list))
      {
        PyErr_SetString(PyExc_TypeError, "list required for argument.");
        return NULL;
      }
      PyListContainer container(list);
      self->impl->addAll(container);
      NONE;
    }

    static PyObject* get_current_uri(obj* self, PyObject* args)
    {
      return ret(self->impl->getCurrentURI());
    }

    static PyObject* get_current_authenticator(obj* self, PyObject* args)
    {
      NONE;
    }

    std::map<std::string, std::string>
    string_map_from_dictionary(PyObject* dictionary)
    {
      std::map<std::string, std::string> returnValue;
      Py_ssize_t pos = 0;
      PyObject* key, *value;
      while (PyDict_Next(dictionary, &pos, &key, &value))
      {
        returnValue[PyString_AsString(key)] = PyString_AsString(value);
      }
      return returnValue;
    }


    static PyObject* report_failure(obj* self, PyObject* args)
    {
      PyObject* ex, *dict;
      if (!PyArg_ParseTuple(args, "OO", &ex, &dict))
      {
        return NULL;
      }
      if (!PyDict_Check(dict))
      {
        PyErr_SetString(PyExc_TypeError, "dictionary required for argument 2.");
        return NULL;
      }

      PyObject* ex_as_string = PyObject_Str(ex);
      std::string message(PyString_AsString(ex_as_string));
      Py_XDECREF(ex_as_string);

      // map the python dictionary to a ConnectionInfo
      ConnectionInfo ci = string_map_from_dictionary(dict);

      self->impl->reportFailure(ConnectionException(message, AMPS_E_CONNECTION), ci);
      NONE;
    }

    static PyObject* get_error(obj* self, PyObject* args)
    {
      return ret(self->impl->getError());
    }

    static PyObject* report_success(obj* self, PyObject* args)
    {
      PyObject* dict;
      if (!PyArg_ParseTuple(args, "O", &dict))
      {
        return NULL;
      }
      if (!PyDict_Check(dict))
      {
        PyErr_SetString(PyExc_TypeError, "dictionary required for argument 2.");
        return NULL;
      }
      self->impl->reportSuccess( string_map_from_dictionary( dict ) );

      NONE;
    }

    static PyObject* next(obj* self, PyObject* args)
    {
      self->impl->next();
      NONE;
    }

    ampspy::ampspy_type_object defaultserverchooser_type;

    void add_types(PyObject* module_)
    {
      defaultserverchooser_type.setName("AMPS.DefaultServerChooser")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(dtor)
      .setConstructorFunction(ctor)
      .setBaseType()
      .setDoc(serverchooser_class_doc)
      .notCopyable()
      .addMethod("add", add, "add(uri)\n\nAdds a URI to this server chooser.\n\n:param uri: The URI of an AMPS instance that may be chosen.\n:type uri: str")
      .addMethod("add_all", add_all, "add_all(uris)\n\nAdds a list of URIs to this server chooser.\n\n:param uris: The list of URIs of AMPS instances that may be chosen.\n:type uri: list")
      .addMethod("get_current_uri", get_current_uri,
                 "get_current_uri()\n\nCalled by the :class:`HAClient` to retrieve the current URI to connect to.\n\n:returns: A URI to connect to, or None if no server should be connected to.")
      .addMethod("get_current_authenticator", get_current_authenticator,
                 "get_current_authenticator()\n\nCalled by :class:`HAClient` to retrieve an :class:`Authenticator` to use for authentication with the current server.\n\n:returns: The current :class:`Authenticator`.")
      .addMethod("report_failure", report_failure,
                 "report_failure(exception, connectionInfo)\n\nInvoked by :class:`HAClient` to indicate a connection failure occurred.\n\n:param exception: An exception object containing an error message.\n:type exception: :class:`Exception`\n:param connectionInfo: A dictionary of properties associated with the failed connection.\n:type connectionInfo: dict(str, str)\n")
      .addMethod("get_error", get_error,
                 "get_error()\n\nProvides additional detail to be included in an exception thrown by when the AMPS instance(s) are not available. Called by the :class:`HAClient` when creating an exception.\n\n:returns: A string with information about the connection that failed and the reason for the failure. When no further information is available, returns an empty string.")
      .addMethod("report_success", report_success,
                 "report_success(connectionInfo)\n\nInvoked by :class:`HAClient` to indicate a connection attempt was successful.\n\n:param connectionInfo: A dictionary of properties associated with the successful connection.\n:type connectionInfo: dict(str, str)\n")
      .addMethod("next", next, "next()\n\nInvoked to advance to the next server.")
      .createType()
      .registerType("DefaultServerChooser", module_);
    }

  } // namespace serverchooser

} // namespace ampspy
