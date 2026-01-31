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
  namespace reason
  {

//    def __init__(self):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      return 0;
    }
    static void _dtor(obj* self)
    {
      shims::free(self);
    }

    AMPSDLL ampspy::ampspy_type_object reason_type;

    void add_types(PyObject* module_)
    {
      reason_type.setName("AMPS.Reason")
      .setBasicSize(sizeof(obj))
      .setDoc("AMPS Reason Object")
      .setConstructorFunction(_ctor)
      .setDestructorFunction(_dtor)
      .createType()
      .addStatic("Duplicate", PyString_FromString("duplicate"))
      .addStatic("BadFilter", PyString_FromString("bad filter"))
      .addStatic("BadRegexTopic", PyString_FromString("bad regex topic"))
      .addStatic("SubscriptionAlreadyExists", PyString_FromString("subscription already exists"))
      .addStatic("NameInUse", PyString_FromString("name in use"))
      .addStatic("AuthFailure", PyString_FromString("authentication failure"))
      .addStatic("NotEntitled", PyString_FromString("not entitled"))
      .addStatic("AuthDisabled", PyString_FromString("authentication disabled"))
      .addStatic("NoTopic", PyString_FromString("no topic"))
      .registerType("Reason", module_);
    }

  } // namespace reason
} // namespace ampspy
