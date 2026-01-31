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
#include <map>
#include "message_docs.h"


using namespace AMPS;


namespace ampspy
{
  namespace message
  {

    static int _ctor(obj* self)
    {
      self->isOwned = true;
      self->pMessage = new Message();
      return 0;
    }

    static void _dtor(obj* self)
    {
      if (self->isOwned)
      {
        delete self->pMessage;
      }
      self->pMessage = 0;
      shims::free(self);
    }

    static PyObject* reset(obj* self, PyObject* args)
    {
      if (self->pMessage)
      {
        self->pMessage->reset();
      }
      Py_INCREF((PyObject*)self); return (PyObject*)self;
    }

//  def get_bookmark_seq_no(self)
    static PyObject* get_bookmark_seq_no(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T(self->pMessage->getBookmarkSeqNo());
    }
    static PyObject* __deepcopy__(obj* self, PyObject* args)
    {
      // make a new AMPS.Message
      PyObject* o = PyObject_CallObject(ampspy::message::message_type.pPyObject(), NULL);

      // Set it equal to a deep copy of self's Message
      *(((obj*)o)->pMessage) = self->pMessage->deepCopy();

      return o;
    }

    static PyObject* __copy__(obj* self, PyObject* args)
    {
      // make a new AMPS.Message
      PyObject* o = PyObject_CallObject(ampspy::message::message_type.pPyObject(), NULL);

      // use the same underlying AMPS::Message
      *(((obj*)o)->pMessage) = *(self->pMessage);

      return o;

    }

#define MSG_FIELD(x, y) \
  static PyObject* set##y(obj* self, PyObject* args)\
  {\
    const char *data;\
    Py_ssize_t len = 0;\
    if(!PyArg_ParseTuple(args,"s#",&data,&len)) \
    { \
      PyErr_SetString(PyExc_TypeError, "A string is expected in set_" #x);\
      return NULL;\
    } \
    self->pMessage->set##y(data,len);\
    Py_INCREF((PyObject*)self); return (PyObject*)self;\
  }\
  static PyObject* get##y(obj* self, PyObject* args)\
  {\
    Message::Field f = self->pMessage->get##y();\
    return PyString_FromStringAndSize(f.data(),f.len());\
  }
    MSG_FIELD(ack_type, AckType);
    MSG_FIELD(batch_size, BatchSize);
    MSG_FIELD(bookmark, Bookmark);
    MSG_FIELD(client_name, ClientName);
    MSG_FIELD(command, Command);
    MSG_FIELD(command_id, CommandId);
    MSG_FIELD(correlation_id, CorrelationId);
    MSG_FIELD(data, Data);
    MSG_FIELD(expiration, Expiration);
    MSG_FIELD(filter, Filter);
    MSG_FIELD(group_seq_no, GroupSequenceNumber);
    MSG_FIELD(heartbeat, Heartbeat);
    MSG_FIELD(lease_period, LeasePeriod);
    MSG_FIELD(matches, Matches);
    MSG_FIELD(message_size, MessageLength);
    MSG_FIELD(message_type, MessageType);
    MSG_FIELD(options, Options);
    MSG_FIELD(order_by, OrderBy);
    MSG_FIELD(password, Password);
    MSG_FIELD(query_id, QueryID);
    MSG_FIELD(reason, Reason);
    MSG_FIELD(records_inserted, RecordsInserted);
    MSG_FIELD(records_returned, RecordsReturned);
    MSG_FIELD(records_updated, RecordsUpdated);
    MSG_FIELD(sequence, Sequence);
    MSG_FIELD(sow_deleted, SowDelete);
    MSG_FIELD(sow_key, SowKey);
    MSG_FIELD(sow_keys, SowKeys);
    MSG_FIELD(status, Status);
    MSG_FIELD(sub_id, SubscriptionId);
    MSG_FIELD(sub_ids, SubscriptionIds);
    MSG_FIELD(timeout_interval, TimeoutInterval);
    MSG_FIELD(timestamp, Timestamp);
    MSG_FIELD(top_n, TopNRecordsReturned);
    MSG_FIELD(topic, Topic);
    MSG_FIELD(topic_matches, TopicMatches);
    MSG_FIELD(user_id, UserId);
    MSG_FIELD(version, Version);

    static PyObject* get_data_raw(obj* self, PyObject* args) // -V524
    {
      Message::Field f = self->pMessage->getData(); \
      return PyBytes_FromStringAndSize(f.data(), f.len()); \
    }

    static PyObject* ack(obj* self, PyObject* args)
    {
      char* options = NULL;
      if (!PyArg_ParseTuple(args, "|s", &options))
      {
        return NULL;
      }
      CALL_RETURN_NONE(self->pMessage->ack(options));
    }

    namespace options
    {

      void setOpt(const char* arg, std::string& opts, Py_ssize_t argLen);

      void recurseSetOpt(const char* arg, std::string& opts)
      {
        for (const char* next = arg; next && *next != ')'; )
        {
          while (next && (*next == '(' || *next == '[' || *next == '\'' || *next == ',' ||
                          *next == ' ' || *next == ']'))
          {
            ++next;
          }
          if (next && *next != ')')
          {
            const char* start = next;
            while (*next != '\'' && *next != ')' && *next != ']')
            {
              ++next;
            }
            setOpt(start, opts, (Py_ssize_t)(next - start));
          }
        }
      }

      void setOpt(const char* arg, std::string& opts, Py_ssize_t argLen)
      {
        if (arg[0] == '(' || arg[0] == '[')
        {
          recurseSetOpt(arg, opts);
        }
        else if (argLen >= 3 && strncmp(arg, "set", 3) == 0)
        {
          recurseSetOpt(arg + 3, opts);
        }
        else
        {
          opts += std::string(arg, argLen);
        }
      }

      std::string parseOption(PyObject* argObj)
      {
        std::string opts;
        PyObject* iter = NULL;
        if (PyString_Check(argObj))
        {
          return PyString_AsString(argObj);
        }
        else if ((iter = PyObject_GetIter(argObj)))
        {
          PyObject* item = NULL;
          while ((item = PyIter_Next(iter)))
          {
            opts += parseOption(item);
            Py_DECREF(item);
          }
          Py_DECREF(iter);
        }
        else
        {
          PyObject* newString = PyObject_Str(argObj);
          if (newString)
          {
            char* arg = NULL;
            Py_ssize_t len = 0;
            PyString_AsStringAndSize(newString, &arg, &len);
            setOpt(arg, opts, len);
            Py_DECREF(newString);
          }
        }
        return opts;
      }

//    def __init__(self, *args):
      static int _ctor(obj* self, PyObject* args, PyObject* kwds)
      {
        std::string opts;
        for (Py_ssize_t i = 0; i < PyTuple_Size(args); ++i)
        {
          PyObject* argObj = PyTuple_GetItem(args, i);
          opts += parseOption(argObj);
        }
        self->pOptions = new Message::Options(opts);
        return 0;
      }

      static void _dtor(obj* self)
      {
        delete self->pOptions;
        self->pOptions = 0;
        shims::free(self);
      }

//    def set_none(void)
      static PyObject* set_none(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setNone());
      }

//    def set_live(void)
      static PyObject* set_live(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setLive());
      }

//    def set_OOF(void)
      static PyObject* set_OOF(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setOOF());
      }

//    def set_replace(void)
      static PyObject* set_replace(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setReplace());
      }

//    def set_no_empties(void)
      static PyObject* set_no_empties(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setNoEmpties());
      }

//    def set_no_sowkey(void)
      static PyObject* set_no_sowkey(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setNoSowKey());
      }

//    def set_send_keys(void)
      static PyObject* set_send_keys(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setSendKeys());
      }

//    def set_timestamp(void)
      static PyObject* set_timestamp(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setTimestamp());
      }

//    def set_cancel(void)
      static PyObject* set_cancel(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setCancel());
      }

//    def set_resume(void)
      static PyObject* set_resume(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setResume());
      }

//    def set_pause(void)
      static PyObject* set_pause(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setPause());
      }

//    def set_fully_durable(void)
      static PyObject* set_fully_durable(obj* self, PyObject* args)
      {
        CALL_RETURN_SELF(self->pOptions->setFullyDurable());
      }

//    def set_max_backlog(int)
      static PyObject* set_max_backlog(obj* self, PyObject* args_)
      {
        int max_backlog = 0;
        if (!PyArg_ParseTuple(args_, "i", &max_backlog))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setMaxBacklog(max_backlog));
      }

//    def set_conflation(string)
      static PyObject* set_conflation(obj* self, PyObject* args_)
      {
        char* conflation = NULL;
        if (!PyArg_ParseTuple(args_, "s", &conflation))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setConflation(conflation));
      }

//    def set_conflation_key(string)
      static PyObject* set_conflation_key(obj* self, PyObject* args_)
      {
        char* conflation_key = NULL;
        if (!PyArg_ParseTuple(args_, "s", &conflation_key))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setConflationKey(conflation_key));
      }

//    def set_top_n(int)
      static PyObject* set_top_n(obj* self, PyObject* args_)
      {
        int top_n = 0;
        if (!PyArg_ParseTuple(args_, "i", &top_n))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setTopN(top_n));
      }

//    def set_rate(string)
      static PyObject* set_rate(obj* self, PyObject* args_)
      {
        char* rate = NULL;
        if (!PyArg_ParseTuple(args_, "s", &rate))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setRate(rate));
      }

//    def set_rate_max_gap(string)
      static PyObject* set_rate_max_gap(obj* self, PyObject* args_)
      {
        char* rate_max_gap = NULL;
        if (!PyArg_ParseTuple(args_, "s", &rate_max_gap))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setRateMaxGap(rate_max_gap));
      }

//    def set_skip_n(int)
      static PyObject* set_skip_n(obj* self, PyObject* args_)
      {
        int skip_n = 0;
        if (!PyArg_ParseTuple(args_, "i", &skip_n))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setSkipN(skip_n));
      }

//    def set_projection(string)
      static PyObject* set_projection(obj* self, PyObject* args_)
      {
        char* projection = NULL;
        if (!PyArg_ParseTuple(args_, "s", &projection))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setProjection(projection));
      }

//    def set_grouping(string)
      static PyObject* set_grouping(obj* self, PyObject* args_)
      {
        char* grouping = NULL;
        if (!PyArg_ParseTuple(args_, "s", &grouping))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setGrouping(grouping));
      }

//    def set_bookmark_not_found
      static PyObject* set_bookmark_not_found(obj* self, PyObject* args_)
      {
        char* action = NULL;
        if (!PyArg_ParseTuple(args_, "s", &action))
        {
          return NULL;
        }
        CALL_RETURN_SELF(self->pOptions->setBookmarkNotFound(action));
      }

//    def set_bookmark_not_found_now
      static PyObject* set_bookmark_not_found_now(obj* self, PyObject* )
      {
        CALL_RETURN_SELF(self->pOptions->setBookmarkNotFoundNow());
      }

//    def set_bookmark_not_found_epoch
      static PyObject* set_bookmark_not_found_epoch(obj* self, PyObject* )
      {
        CALL_RETURN_SELF(self->pOptions->setBookmarkNotFoundEpoch());
      }

//    def set_bookmark_not_found_fail
      static PyObject* set_bookmark_not_found_fail(obj* self, PyObject* )
      {
        CALL_RETURN_SELF(self->pOptions->setBookmarkNotFoundFail());
      }

      static PyObject* str(PyObject* opts)
      {
        obj* self = (obj*)opts;
        CALL_RETURN_STRING(self->pOptions->operator const std::string());
      }


      static PyObject* MaxBacklog(void* unused_, PyObject* args_)
      {
        int max_backlog = 0;
        if (!PyArg_ParseTuple(args_, "i", &max_backlog))
        {
          return NULL;
        }
        return PyString_FromFormat("max_backlog=%d,", max_backlog);
      }

      static PyObject* Conflation(void* unused_, PyObject* args_)
      {
        char* conflation = 0;
        if (!PyArg_ParseTuple(args_, "s", &conflation))
        {
          return NULL;
        }
        return PyString_FromFormat("conflation=%s,", conflation);
      }

      static PyObject* ConflationKey(void* unused_, PyObject* args_)
      {
        char* conflation = 0;
        if (!PyArg_ParseTuple(args_, "s", &conflation))
        {
          return NULL;
        }
        return PyString_FromFormat("conflation_key=%s,", conflation);
      }

      static PyObject* TopN(void* unused_, PyObject* args_)
      {
        int top_n = 0;
        if (!PyArg_ParseTuple(args_, "i", &top_n))
        {
          return NULL;
        }
        return PyString_FromFormat("top_n=%d,", top_n);
      }

      static PyObject* Rate(void* unused_, PyObject* args_)
      {
        char* rate = NULL;
        if (!PyArg_ParseTuple(args_, "s", &rate))
        {
          return NULL;
        }
        return PyString_FromFormat("rate=%s,", rate);
      }

      static PyObject* RateMaxGap(void* unused_, PyObject* args_)
      {
        char* rate = NULL;
        if (!PyArg_ParseTuple(args_, "s", &rate))
        {
          return NULL;
        }
        return PyString_FromFormat("rate_max_gap=%s,", rate);
      }

      static PyObject* SkipN(void* unused_, PyObject* args_)
      {
        int skip_n = 0;
        if (!PyArg_ParseTuple(args_, "i", &skip_n))
        {
          return NULL;
        }
        return PyString_FromFormat("skip_n=%d,", skip_n);
      }

      static PyObject* Projection(void* unused_, PyObject* args_)
      {
        char* projection = NULL;
        if (!PyArg_ParseTuple(args_, "s", &projection))
        {
          return NULL;
        }
        return PyString_FromFormat("projection=[%s],", projection);
      }

      static PyObject* Grouping(void* unused_, PyObject* args_)
      {
        char* grouping = NULL;
        if (!PyArg_ParseTuple(args_, "s", &grouping))
        {
          return NULL;
        }
        return PyString_FromFormat("grouping=[%s],", grouping);
      }

      static PyObject* Select(void* unused_, PyObject* args_)
      {
        char* select = NULL;
        if (!PyArg_ParseTuple(args_, "s", &select))
        {
          return NULL;
        }
        return PyString_FromFormat("select=[%s],", select);
      }

      static PyObject* AckConflationInterval(void* unused_, PyObject* args_)
      {
        char* interval = NULL;
        if (!PyArg_ParseTuple(args_, "s", &interval))
        {
          return NULL;
        }
        return PyString_FromFormat("ack_conflation=%s,", interval);
      }

      static PyObject* BookmarkNotFound(void* unused_, PyObject* args_)
      {
        char* action = NULL;
        if (!PyArg_ParseTuple(args_, "s", &action))
        {
          return NULL;
        }
        return PyString_FromFormat("bookmark_not_found=%s,", action);
      }

      ampspy::ampspy_type_object options_type;
      void setup_options_type(void)
      {
        options_type.setName("AMPS.Options")
        .setBasicSize(sizeof(obj))
        .setDestructorFunction(&_dtor)
        .setConstructorFunction(&_ctor)
        .setDoc(amps_message_options_class_docs)
        .setStrFunction(str)
        .setReprFunction(str)
        .addMethod("set_none", set_none, "Clears options set on self.")
        .addMethod("set_live", set_live, OPTIONS_CONSTANT_DOC(live))
        .addMethod("set_OOF", set_OOF, OPTIONS_CONSTANT_DOC(oof))
        .addMethod("set_replace", set_replace, OPTIONS_CONSTANT_DOC(replace))
        .addMethod("set_no_empties", set_no_empties, OPTIONS_CONSTANT_DOC(no_empties))
        .addMethod("set_no_sowkey", set_no_sowkey, OPTIONS_CONSTANT_DOC(no_sowkey))
        .addMethod("set_send_keys", set_send_keys, OPTIONS_CONSTANT_DOC(send_keys))
        .addMethod("set_timestamp", set_timestamp, OPTIONS_CONSTANT_DOC(timestamp))
        .addMethod("set_cancel", set_cancel, OPTIONS_CONSTANT_DOC(cancel))
        .addMethod("set_resume", set_resume, OPTIONS_CONSTANT_DOC(resume))
        .addMethod("set_pause", set_pause, OPTIONS_CONSTANT_DOC(pause))
        .addMethod("set_fully_durable", set_fully_durable, OPTIONS_CONSTANT_DOC(fully_durable))
        .addMethod("set_max_backlog", set_max_backlog, amps_message_options_maxbacklog_docs)
        .addMethod("set_conflation", set_conflation, amps_message_options_conflation_docs)
        .addMethod("set_conflation_key", set_conflation_key, amps_message_options_conflation_key_docs)
        .addMethod("set_top_n", set_top_n, amps_message_options_top_n_docs)
        .addMethod("set_rate", set_rate, amps_message_options_rate_docs)
        .addMethod("set_rate_max_gap", set_rate_max_gap, amps_message_options_rate_max_gap_docs)
        .addMethod("set_skip_n", set_skip_n, amps_message_options_skip_n_docs)
        .addMethod("set_projection", set_projection, amps_message_options_projection_docs)
        .addMethod("set_grouping", set_grouping, amps_message_options_grouping_docs)
        .addMethod("set_bookmark_not_found", set_bookmark_not_found, amps_message_options_bookmark_not_found_docs)
        .addMethod("set_bookmark_not_found_now", set_bookmark_not_found_now, amps_message_options_bookmark_not_found_now_docs)
        .addMethod("set_bookmark_not_found_epoch", set_bookmark_not_found_epoch, amps_message_options_bookmark_not_found_epoch_docs)
        .addMethod("set_bookmark_not_found_fail", set_bookmark_not_found_fail, amps_message_options_bookmark_not_found_fail_docs)
        .addStaticMethod("MaxBacklog", MaxBacklog, NULL)
        .addStaticMethod("Conflation", Conflation, NULL)
        .addStaticMethod("ConflationKey", ConflationKey, NULL)
        .addStaticMethod("TopN", TopN, NULL)
        .addStaticMethod("Rate", Rate, NULL)
        .addStaticMethod("RateMaxGap", RateMaxGap, NULL)
        .addStaticMethod("SkipN", SkipN, NULL)
        .addStaticMethod("Projection", Projection, NULL)
        .addStaticMethod("Grouping", Grouping, NULL)
        .addStaticMethod("Select", Select, NULL)
        .addStaticMethod("AckConflationInterval", AckConflationInterval, NULL)
        .addStaticMethod("BookmarkNotFound", BookmarkNotFound, NULL)
        .addMethod("__deepcopy__", __deepcopy__, NULL)
        .createType()
        .addStatic("None", PyString_FromString(""))
        .addStatic("Live", PyString_FromString("live,"))
        .addStatic("OOF", PyString_FromString("oof,"))
        .addStatic("Replace", PyString_FromString("replace,"))
        .addStatic("NoEmpties", PyString_FromString("no_empties,"))
        .addStatic("NoSowKey", PyString_FromString("no_sowkey,"))
        .addStatic("SendKeys", PyString_FromString("send_keys,"))
        .addStatic("Timestamp", PyString_FromString("timestamp,"))
        .addStatic("Cancel", PyString_FromString("cancel,"))
        .addStatic("Resume", PyString_FromString("resume,"))
        .addStatic("Pause", PyString_FromString("pause,"))
        .addStatic("FullyDurable", PyString_FromString("fully_durable,"))
        .addStatic("Expire", PyString_FromString("expire,"))
        .addStatic("BookmarkNotFoundNow", PyString_FromString("bookmark_not_found=now,"))
        .addStatic("BookmarkNotFoundEpoch", PyString_FromString("bookmark_not_found=epoch,"))
        .addStatic("BookmarkNotFoundFail", PyString_FromString("bookmark_not_found=fail,"));
      }

    } // namespace options

#define MSG_DECL(x,y) \
  .addMethod("set_"#x, &set##y,  set_##x ##_docs)\
  .addMethod("get_"#x, &get##y,  get_##x ##_docs)\
  .addMethod("set"#y, &set##y,   set_##x ##_docs)\
  .addMethod("get"#y, &get##y,   get_##x ##_docs)\
  .addGetterSetter(#x, &get##y, &set##y, NULL, NULL)

    ampspy::ampspy_type_object commands_type;
    void setup_commands_type(void)
    {
      commands_type.setName("AMPS.Command")
      .setDoc(commands_class_doc)
      .createType()
      .addStatic("Unknown", PyString_FromString(""))
      .addStatic("Publish", PyString_FromString("publish"))
      .addStatic("Subscribe", PyString_FromString("subscribe"))
      .addStatic("Unsubscribe", PyString_FromString("unsubscribe"))
      .addStatic("SOW", PyString_FromString("sow"))
      .addStatic("Heartbeat", PyString_FromString("heartbeat"))
      .addStatic("Logon", PyString_FromString("logon"))
      .addStatic("StartTimer", PyString_FromString("start_timer"))
      .addStatic("StopTimer", PyString_FromString("stop_timer"))
      .addStatic("SOWAndSubscribe", PyString_FromString("sow_and_subscribe"))
      .addStatic("DeltaPublish", PyString_FromString("delta_publish"))
      .addStatic("DeltaSubscribe", PyString_FromString("delta_subscribe"))
      .addStatic("SOWAndDeltaSubscribe", PyString_FromString("sow_and_delta_subscribe"))
      .addStatic("SOWDelete", PyString_FromString("sow_delete"))
      .addStatic("GroupBegin", PyString_FromString("group_begin"))
      .addStatic("GroupEnd", PyString_FromString("group_end"))
      .addStatic("OOF", PyString_FromString("oof"))
      .addStatic("Ack", PyString_FromString("ack"))
      .addStatic("UnknownEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::Unknown))
      .addStatic("PublishEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::Publish))
      .addStatic("SubscribeEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::Subscribe))
      .addStatic("UnsubscribeEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::Unsubscribe))
      .addStatic("SOWEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::SOW))
      .addStatic("HeartbeatEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::Heartbeat))
      .addStatic("LogonEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::Logon))
      .addStatic("StartTimerEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::StartTimer))
      .addStatic("StopTimerEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::StopTimer))
      .addStatic("SOWAndSubscribeEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::SOWAndSubscribe))
      .addStatic("DeltaPublishEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::DeltaPublish))
      .addStatic("DeltaSubscribeEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::DeltaSubscribe))
      .addStatic("SOWAndDeltaSubscribeEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::SOWAndDeltaSubscribe))
      .addStatic("SOWDeleteEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::SOWDelete))
      .addStatic("GroupBeginEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::GroupBegin))
      .addStatic("GroupEndEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::GroupEnd))
      .addStatic("OOFEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::OOF))
      .addStatic("AckEnum", PyLong_FromUnsignedLong((unsigned long)Message::Command::Ack));
    }

    ampspy::ampspy_type_object acktypes_type;
    void setup_acktypes_type(void)
    {
      acktypes_type.setName("AMPS.AckType")
      .setDoc(acktypes_class_doc)
      .createType()
      .addStatic("None_", PyString_FromString("none"))
      .addStatic("Received", PyString_FromString("received"))
      .addStatic("Parsed", PyString_FromString("parsed"))
      .addStatic("Persisted", PyString_FromString("persisted"))
      .addStatic("Processed", PyString_FromString("processed"))
      .addStatic("Completed", PyString_FromString("completed"))
      .addStatic("Stats", PyString_FromString("stats"))
      .addStatic("NoneEnum", PyLong_FromUnsignedLong((unsigned long)Message::AckType::None))
      .addStatic("ReceivedEnum", PyLong_FromUnsignedLong((unsigned long)Message::AckType::Received))
      .addStatic("ParsedEnum", PyLong_FromUnsignedLong((unsigned long)Message::AckType::Parsed))
      .addStatic("PersistedEnum", PyLong_FromUnsignedLong((unsigned long)Message::AckType::Persisted))
      .addStatic("ProcessedEnum", PyLong_FromUnsignedLong((unsigned long)Message::AckType::Processed))
      .addStatic("CompletedEnum", PyLong_FromUnsignedLong((unsigned long)Message::AckType::Completed))
      .addStatic("StatsEnum", PyLong_FromUnsignedLong((unsigned long)Message::AckType::Stats));
    }

    AMPSDLL ampspy::ampspy_type_object message_type;
    void add_types(PyObject* module_)
    {
      setup_commands_type();
      setup_acktypes_type();
      options::setup_options_type();

      message_type.setName("AMPS.Message")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(&_dtor)
      .setDoc(amps_message_class_docs)
      .setConstructorFunction(&_ctor)
      .addMethod("reset", &reset, "Resets the contents of this message.")
      .addMethod("get_bookmark_seq_no", &get_bookmark_seq_no, "Returns the bookmark sequence number for this Message. This\n"
                                                              "field is only used internally by bookmark store implementations\n"
                                                              "to cache a tracking index for undiscarded messages, so they can be\n"
                                                              "looked up quickly when discarded for a bookmark subscription. There\n"
                                                              "is generally no reason for end-user applications to use this.\n\n"
                                                              ":returns: The bookmark sequence number for this message.")
      .addMethod("__deepcopy__", &__deepcopy__, "returns a deep copy of self.")
      .addMethod("__copy__", &__copy__, "returns a shallow copy of self.")
      MSG_DECL(ack_type, AckType)
      MSG_DECL(batch_size, BatchSize)
      MSG_DECL(bookmark, Bookmark)
      MSG_DECL(client_name, ClientName)
      MSG_DECL(command, Command)
      MSG_DECL(command_id, CommandId)
      MSG_DECL(correlation_id, CorrelationId)
      MSG_DECL(expiration, Expiration)
      MSG_DECL(filter, Filter)
      MSG_DECL(group_seq_no, GroupSequenceNumber)
      MSG_DECL(heartbeat, Heartbeat)
      MSG_DECL(lease_period, LeasePeriod)
      MSG_DECL(matches, Matches)
      MSG_DECL(message_size, MessageLength)
      MSG_DECL(message_type, MessageType)
      MSG_DECL(options, Options)
      MSG_DECL(order_by, OrderBy)
      MSG_DECL(password, Password)
      MSG_DECL(query_id, QueryID)
      MSG_DECL(reason, Reason)
      MSG_DECL(records_inserted, RecordsInserted)
      MSG_DECL(records_returned, RecordsReturned)
      MSG_DECL(records_updated, RecordsUpdated)
      MSG_DECL(sequence, Sequence)
      MSG_DECL(sow_deleted, SowDelete)
      MSG_DECL(sow_key, SowKey)
      MSG_DECL(sow_keys, SowKeys)
      MSG_DECL(status, Status)
      MSG_DECL(sub_id, SubscriptionId)
      MSG_DECL(sub_ids, SubscriptionIds)
      MSG_DECL(timeout_interval, TimeoutInterval)
      MSG_DECL(timestamp, Timestamp)
      MSG_DECL(top_n, TopNRecordsReturned)
      MSG_DECL(topic, Topic)
      MSG_DECL(topic_matches, TopicMatches)
      MSG_DECL(user_id, UserId)
      MSG_DECL(version, Version)
      MSG_DECL(data, Data)
      .addMethod("ack", &ack, R"docstring(ack(options=None)
      Acknowledges a message queue message.

      :param options: An optional string to include in the ack such as ``cancel``.
      )docstring")
      .addMethod("get_data_raw", get_data_raw, "Gets the value of ``data`` for this message as a Python bytes object.\n\n"
                                               ":returns: The data of this message as a Python bytes object.")
      .createType()
      .registerType("Message", module_)
      .addStatic("Command", commands_type)
      .addStatic("AckType", acktypes_type)
      .addStatic("Options", options::options_type);
    }

    AMPSDLL PyObject* toPythonMessage(AMPS::Message& message_)
    {
      message::obj* pPyMessage = (message::obj*)_PyObject_New(ampspy::message::message_type);
      pPyMessage->pMessage = &message_;
      pPyMessage->isOwned = false;
      return (PyObject*) pPyMessage;
    }

    AMPSDLL void setCppMessage(obj* pPythonMessage_, const AMPS::Message& cppMessage_)
    {
      *(pPythonMessage_->pMessage) = cppMessage_;
      pPythonMessage_->isOwned = true;
    }

  } // namespace message

} // namespace ampspy
