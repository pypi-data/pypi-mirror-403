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

#include "fixshredder_docs.h"

using namespace AMPS;
namespace ampspy
{
  namespace fixshredder
  {

    static ampspy::ampspy_type_object fixshredder_type;

    static int ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      self->fs = 1;
      const char* kwlist[] = {"separator", NULL};
      if (!PyArg_ParseTupleAndKeywords(args, kwds, "|c", (char**)kwlist, &(self->fs)))
      {
        return -1;
      }
      return 0;
    }
    static void dtor(obj* self)
    {
      shims::free(self);
    }

    static PyObject* to_map(obj* self, PyObject* args)
    {
      const char* input;
      Py_ssize_t inputLength;
      if (!PyArg_ParseTuple(args, "s#", &input, &inputLength))
      {
        return NULL;
      }
      FIX fix(input, inputLength, self->fs);
      PyObject* dict = PyDict_New();
      for (FIX::iterator iterator = fix.begin() ; iterator != fix.end() ; ++iterator)
      {
        AMPSPyReference<> key = PyString_FromStringAndSize((*iterator).first.data(),
                                                           (*iterator).first.len());
        if (key.isNull())
        {
          PyErr_SetString(PyExc_TypeError, "null key");
          return NULL;
        }
        AMPSPyReference<> numeric_key = PyNumber_Int(key);
        if (numeric_key.isNull())
        {
          PyErr_SetString(PyExc_TypeError, "non-numeric key");
          return NULL;
        }
        AMPSPyReference<> val = PyString_FromStringAndSize((*iterator).second.data(),
                                                           (*iterator).second.len());
        PyDict_SetItem(dict, numeric_key, val);
      }
      return dict;
    }
    void add_types(PyObject* module_)
    {
      fixshredder_type.setName("AMPS.FIXShredder")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(dtor)
      .setConstructorFunction(ctor)
      .setBaseType()
      .setDoc(fixshredder_class_doc)
      .notCopyable()
      .addMethod("to_map", to_map, to_map_doc)
      .createType()
      .registerType("FIXShredder", module_);
    }


  } // namespace fixshredder

} // namespace ampspy
