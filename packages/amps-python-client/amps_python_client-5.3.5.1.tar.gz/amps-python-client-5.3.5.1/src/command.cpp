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
#include <set>
#include <sstream>
#include "command_docs.h"
#include <deque>

using namespace AMPS;
namespace ampspy
{
  namespace command
  {

    AMPSDLL ampspy::ampspy_type_object command_type;

//    def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      // placement new this object right here; we haven't been properly c++ constructed yet.
      char* command = NULL;
      if (!PyArg_ParseTuple(args, "s", &command))
      {
        return -1;
      }
      new (&(self->command)) AMPS::Command(command);
      return 0;
    }

    static void _dtor(obj* self)
    {
      self->command.~Command();
      shims::free(self);
    }

    static PyObject* get_sequence(obj* self)
    {
      CALL_RETURN_UINT64_T(self->command.getSequence());
    }

    static PyObject* get_ack_type(obj* self)
    {
      CALL_RETURN_STRING(self->command.getAckType());
    }

    static PyObject* get_ack_type_enum(obj* self)
    {
      CALL_RETURN_SIZE_T((size_t)(self->command.getAckTypeEnum()));
    }

#define COMMAND_UINT_SETTER(pyname,cppname) \
  static obj* pyname(obj* self, PyObject *args) \
  { \
    unsigned value; \
    if(!PyArg_ParseTuple(args, "I", &value)) \
    { \
      return NULL; \
    } \
    self->command.cppname (value); \
    Py_INCREF(self);\
    return self; \
  }

#define COMMAND_STRING_SETTER(pyname,cppname) \
  static obj* pyname(obj* self, PyObject *args) \
  { \
    char *value = NULL; \
    Py_ssize_t len = 0;\
    if(!PyArg_ParseTuple(args, "s#", &value,&len)) \
    { \
      return NULL; \
    } \
    self->command.cppname (std::string(value,len)); \
    Py_INCREF(self);\
    return self; \
  }

    COMMAND_STRING_SETTER(reset, reset)
    COMMAND_STRING_SETTER(set_sow_key, setSowKey)
    COMMAND_STRING_SETTER(set_sow_keys, setSowKeys)
    COMMAND_STRING_SETTER(set_command_id, setCommandId)
    COMMAND_STRING_SETTER(set_correlation_id, setCorrelationId)
    COMMAND_STRING_SETTER(set_topic, setTopic)
    COMMAND_STRING_SETTER(set_filter, setFilter)
    COMMAND_STRING_SETTER(set_order_by, setOrderBy)
    COMMAND_STRING_SETTER(set_sub_id, setSubId)
    COMMAND_STRING_SETTER(set_query_id, setQueryId)
    COMMAND_STRING_SETTER(set_bookmark, setBookmark)
    COMMAND_STRING_SETTER(set_options, setOptions)
    COMMAND_STRING_SETTER(set_data, setData)
    COMMAND_STRING_SETTER(add_ack_type, addAckType)
    COMMAND_STRING_SETTER(set_ack_type, setAckType)
    COMMAND_UINT_SETTER(set_ack_type_enum, setAckType)
    COMMAND_UINT_SETTER(set_timeout, setTimeout)
    COMMAND_UINT_SETTER(set_top_n, setTopN)
    COMMAND_UINT_SETTER(set_batch_size, setBatchSize)
    COMMAND_UINT_SETTER(set_expiration, setExpiration)
    COMMAND_UINT_SETTER(set_sequence, setSequence)

    void add_types(PyObject* module_)
    {
      command_type.setName("AMPS.Command")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(&_dtor)
      .setConstructorFunction(&_ctor)
      .setDoc(command_class_doc)
      .notCopyable()
      .addMethod("reset", reset, reset_doc)
      .addMethod("add_ack_type", add_ack_type, add_ack_type_doc)
      .addMethod("set_ack_type", set_ack_type, set_ack_type_doc)
      .addMethod("set_ack_type_enum", set_ack_type_enum, set_ack_type_enum_doc)
      .addMethod("get_ack_type", get_ack_type, get_ack_type_doc)
      .addMethod("get_ack_type_enum", get_ack_type_enum, get_ack_type_enum_doc)
      .addMethod("set_sow_key", set_sow_key, set_sow_key_doc)
      .addMethod("set_sow_keys", set_sow_keys, set_sow_keys_doc)
      .addMethod("set_command_id", set_command_id, set_command_id_doc)
      .addMethod("set_correlation_id", set_correlation_id, set_correlation_id_doc)
      .addMethod("set_topic", set_topic, set_topic_doc)
      .addMethod("set_filter", set_filter, set_filter_doc)
      .addMethod("set_order_by", set_order_by, set_order_by_doc)
      .addMethod("set_sub_id", set_sub_id, set_sub_id_doc)
      .addMethod("set_query_id", set_query_id, set_query_id_doc)
      .addMethod("set_bookmark", set_bookmark, set_bookmark_doc)
      .addMethod("set_options", set_options, set_options_doc)
      .addMethod("set_data", set_data, set_data_doc)
      .addMethod("set_timeout", set_timeout, set_timeout_doc)
      .addMethod("set_top_n", set_top_n, set_top_n_doc)
      .addMethod("set_batch_size", set_batch_size, set_batch_size_doc)
      .addMethod("set_expiration", set_expiration, set_expiration_doc)
      .addMethod("set_sequence", set_sequence, set_sequence_doc)
      .addMethod("get_sequence", get_sequence, get_sequence_doc)
      .createType().registerType("Command", module_);
    }

  }

}
