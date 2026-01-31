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
#include <amps/util.hpp>

using namespace AMPS;
namespace ampspy
{
  namespace versioninfo
  {
    AMPSDLL ampspy::ampspy_type_object versioninfo_type;

    //    def __init__(self, initialCapacity):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      char* version = NULL;
      self->pVersionInfo = NULL;
      if (!PyArg_ParseTuple(args, "|s", &version))
      {
        return -1;
      }
      if (version)
      {
        self->pVersionInfo = new VersionInfo(version);
      }
      else
      {
        self->pVersionInfo = new VersionInfo();
      }
      return 0;
    }

    static void _dtor(obj* self)
    {
      delete self->pVersionInfo;
      self->pVersionInfo = NULL;
      shims::free(self);
    }

    //    def set_version(self, version)
    static PyObject* set_version(obj* self, PyObject* args)
    {
      const char* version = NULL;
      if (!PyArg_ParseTuple(args, "s", &version))
      {
        return NULL;
      }
      if (!version)
      {
        PyErr_SetString(PyExc_ValueError, "version must be a string.");
        return NULL;
      }
      CALL_RETURN_NONE(self->pVersionInfo->setVersion(version));
    }

    //  def get_version_string(self)
    static PyObject* get_version_string(obj* self)
    {
      CALL_RETURN_STRING(self->pVersionInfo->getVersionString());
    }

    //  def get_version_number(self)
    static PyObject* get_version_number(obj* self)
    {
      CALL_RETURN_UINT64_T(self->pVersionInfo->getVersionUint64());
    }

    //  def get_old_style_version(self)
    static PyObject* get_old_style_version(obj* self)
    {
      CALL_RETURN_SIZE_T(self->pVersionInfo->getOldStyleVersion());
    }

#if PY_MAJOR_VERSION < 3
    //  def versioninfo_cmp(self, other)
    static int versioninfo_cmp(obj* self, obj* other)
    {
      if (*(self->pVersionInfo) < * (other->pVersionInfo))
      {
        return -1;
      }
      else if (*(self->pVersionInfo) > *(other->pVersionInfo))
      {
        return 1;
      }
      else if (*(self->pVersionInfo) == *(other->pVersionInfo))
      {
        return 0;
      }
      // "A tp_compare handler may raise an exception. In this case it should
      //  return a negative value. The caller has to test for an exception
      //  using PyErr_Occurred()."
      PyErr_SetString(PyExc_TypeError, "Comparison not allowed between these types.");
      return -2;
    }

#else
    //  def versioninfo_richcmp(self, other, op)
    static PyObject* versioninfo_richcmp(obj* self, obj* other, int op)
    {
      switch (op)
      {
      case Py_LT: CALL_RETURN_BOOL(*(self->pVersionInfo) < * (other->pVersionInfo)); break;
      case Py_LE: CALL_RETURN_BOOL(*(self->pVersionInfo) <= *(other->pVersionInfo)); break;
      case Py_EQ: CALL_RETURN_BOOL(*(self->pVersionInfo) == *(other->pVersionInfo)); break;
      case Py_NE: CALL_RETURN_BOOL(*(self->pVersionInfo) != *(other->pVersionInfo)); break;
      case Py_GT: CALL_RETURN_BOOL(*(self->pVersionInfo) > *(other->pVersionInfo)); break;
      case Py_GE: CALL_RETURN_BOOL(*(self->pVersionInfo) >= *(other->pVersionInfo)); break;
      default: break;
      }
      PyErr_SetString(PyExc_TypeError, "Comparison not allowed between these types.");
      return NULL;
    }
#endif

    static PyObject* str(obj* self)
    {
      return get_version_string(self);
    }

    void add_types(PyObject* module_)
    {
      versioninfo_type.setName("AMPS.VersionInfo")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setBaseType()
      .setReprFunction(str)
      .setStrFunction(str)
#if PY_MAJOR_VERSION < 3
      .setCompareFunction(versioninfo_cmp)
#else
      .setRichCompareFunction(versioninfo_richcmp)
#endif
      .setDoc("AMPS VersionInfo Object")
      .notCopyable()
      .addMethod("set_version", set_version, "set_version(version)\n\nSets the string version to represent.\n")
      .addMethod("get_version_string", get_version_string, "get_version_string()\n\nReturns the version string.\n")
      .addMethod("get_version_number", get_version_number,
                 "get_version_number()\n\nReturns the version as number with 4 digits for major version, 4 digits for minor version, 5 digits for maintenance version and 5 digits for patch version.\n")
      .addMethod("get_old_style_version", get_old_style_version,
                 "get_old_style_version()\n\nReturns the version as number with 2 digits for major version, 2 digits for minor version, 2 digits for maintenance version and 2 digits for patch version. Any values greater than 99 are represented as 99.\n")
      .createType()
      .registerType("VersionInfo", module_);
    }

  } // namespace versioninfo
} // namespace ampspy
