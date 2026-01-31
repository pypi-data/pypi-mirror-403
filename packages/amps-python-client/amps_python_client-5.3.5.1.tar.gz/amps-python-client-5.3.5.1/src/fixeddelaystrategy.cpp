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
#include <amps/ReconnectDelayStrategy.hpp>
#include <amps/ReconnectDelayStrategyImpl.hpp>


using namespace AMPS;
namespace ampspy
{
  namespace fixeddelaystrategy
  {

    AMPSDLL ampspy::ampspy_type_object type;

//    def __init__(self, name):
    static int ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      static const char* kwargs[] = { "initial_delay", "maximum", NULL};
      unsigned long initial_delay = 200;
      unsigned long maximum = 0;

      if (!PyArg_ParseTupleAndKeywords(args, kwds, "|II", (char**)kwargs,
                                       &initial_delay, &maximum))
      {
        return -1;
      }
      new (&(self->impl)) ReconnectDelayStrategy(
        new AMPS::FixedDelayStrategy(initial_delay, maximum));
      return 0;
    }
    static void dtor(obj* self)
    {
      self->impl.~ReconnectDelayStrategy();
      shims::free(self);
    }

    static PyObject* get_connect_wait_duration(obj* self, PyObject* args)
    {
      const char* uri = NULL;
      if (!PyArg_ParseTuple(args, "s", &uri))
      {
        return NULL;
      }
      CALL_RETURN_SIZE_T( self->impl.getConnectWaitDuration(uri) );
    }

    static PyObject* reset(obj* self, PyObject* args)
    {
      self->impl.reset();
      NONE;
    }

    static const char* docstring = R"docstring(FixedDelayStrategy(initial_delay, maximum)
    ``FixedDelayStrategy`` is a reconnect delay strategy implementation that waits a
    fixed amount of time before retrying a connection.
    
    By default, a ``FixedDelayStrategy`` waits for 200ms between connection attempts
    and does not have a maximum timeout.

    **Constructor Arguments:**
    
    :param initial_delay: The time (in milliseconds) to wait before reconnecting to a 
                          server for the first time after a failed connection.
    :param maximum: The maximum time (in milliseconds) to keep retrying before giving up.
    )docstring";

    void add_types(PyObject* module_)
    {
      type.setName("AMPS.FixedDelayStrategy")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(dtor)
      .setConstructorFunction(ctor)
      .setDoc(docstring)
      .setBaseType()
      .notCopyable()
      .addMethod("get_connect_wait_duration", get_connect_wait_duration,
                 "Returns the time that the client should delay before connecting "
                 "to the given server URI.")
      .addMethod("reset", reset, "Reset the state of this reconnect delay. AMPS calls this "
                 "method when a connection is established.")
      .createType()
      .registerType("FixedDelayStrategy", module_);
    }

  } // namespace fixeddelaystrategy

} // namespace ampspy
