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
#ifdef _WIN32
#pragma warning(disable: 4996)
#endif
#include <amps/ampsplusplus.hpp>
#include <ampspy_types.hpp>
#include <ampspy_defs.hpp>
#include <amps/HAClient.hpp>
#include "haclient_docs.h"
#include <ampspy_bookmarkstore.hpp>

using namespace AMPS;
namespace ampspy
{

  static std::map<std::string, PyObject*> exception_name_translator;

  server_chooser_wrapper::server_chooser_wrapper(PyObject* self_) : _self(self_), _authBridge(NULL)
  {
    Py_INCREF(_self);
  }

  server_chooser_wrapper::~server_chooser_wrapper()
  {
    try
    {
      LOCKGIL;
      // now let go of any reference to any outstanding authenticator.
      Py_XDECREF(_authBridge.getPythonAuthenticator());
      Py_DECREF(_self);
    }
    catch (ampspy_shutdown_exception&)
    {
      // LOCKGIL can throw exceptions when we are in the middle of shutting
      // down the interpreter. We want to just mask these.
    }
  }

  std::string server_chooser_wrapper::getCurrentURI()
  {
    LOCKGIL;
    AMPSPyReference<> p = PyObject_CallMethod((PyObject*)_self, (char*)"get_current_uri", NULL);

    if (p.isNull() && PyErr_ExceptionMatches(PyExc_SystemExit))
    {
      ampspy::unhandled_exception();
    }
    // Check if previous invocation of python code has resulted in a Ctrl-C delivered.
    if (ampspy::_is_signaled)
    {
      PyErr_SetNone(PyExc_KeyboardInterrupt);
    }

    exc::throwError();
    if (p.asPyObject() == Py_None)
    {
      return "";
    }
    const char* returnValue = PyString_AsString(p);
    std::string returnedStr(returnValue);
    if (returnedStr.find("tcps:") == 0)
    {
      PyObject* initResult = ampspy::ampspy_ssl_init(NULL, NULL);
      if (initResult == NULL)
      {
        exc::throwError();
      }
      else
      {
        Py_DECREF(initResult);
      }
    }

    return returnedStr;
  }

  ///
  /// Returns the Authenticator instance associated with the current URI.
  ///
  /// \return An Authenticator or NULL if none is required for logon.
  Authenticator& server_chooser_wrapper::getCurrentAuthenticator()
  {
    LOCKGIL;
    AMPSPyReference<> p = PyObject_CallMethod((PyObject*)_self, (char*)"get_current_authenticator", NULL);
    if (p.isNull() && PyErr_ExceptionMatches(PyExc_SystemExit))
    {
      ampspy::unhandled_exception();
    }
    exc::throwError();
    if (p == Py_None)
    {
      return DefaultAuthenticator::instance();
    }
    // we always keep a reference, here from our server chooser, for the recent authenticator we've returned
    // it is released the next time we return one out of here, when we take a reference to a new one,
    // or in the destructor.
    Py_INCREF(p);
    Py_XDECREF(_authBridge.getPythonAuthenticator());
    _authBridge.setPythonAuthenticator(p);


    return _authBridge;
  }

  void server_chooser_wrapper::setPyExceptionState(const AMPSException& exception_)
  {
    // It's always AMPSException, for now.
    PyObject* type = exc::AMPSException;
    std::map<std::string, PyObject*>::const_iterator val = exception_name_translator.find(exception_.getClassName());
    if (val != exception_name_translator.end())
    {
      type = val->second;
    }
    PyErr_SetString(type, exception_.what());

  }
  void server_chooser_wrapper::reportFailure(const AMPSException& exception_,
                                             const ConnectionInfo& info_)
  {
    LOCKGIL;
    AMPSPyReference<> dict = PyDict_New();
    for (ConnectionInfo::const_iterator i = info_.begin(); i != info_.end(); ++i)
    {
      AMPSPyReference<> val = PyString_FromString(i->second.c_str());
      PyDict_SetItemString(dict, i->first.c_str(), val);
    }
    // we use our exception translation code to turn exception_ into a PyObject*.
    setPyExceptionState(exception_);

    // Because of what happens in DISPATCH_EXCEPTION, the Python thread exception
    // state is all set up for us. We're going to pull the PyObject exception out
    // and pass it to the python report_failure method.
    PyException ex; // pulls the current python exception and clears it.

    AMPSPyReference<> p = PyObject_CallMethod((PyObject*)_self, (char*)"report_failure", (char*)"(OO)",
                                              ex.value(), (PyObject*)dict);
    if ((PyObject*)p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
    {
      ampspy::unhandled_exception();
    }
    exc::throwError();
  }

  std::string server_chooser_wrapper::getError()
  {
    LOCKGIL;

    //Check to see if get_error has been implemented.  If not, return empty string.
    AMPSPyReference<> callback = PyObject_GetAttrString((PyObject*)_self, "get_error");
    if ((PyObject*)callback == NULL || !PyCallable_Check(callback))
    {
      return "";
    }

    AMPSPyReference<> p = PyObject_CallMethod((PyObject*)_self, (char*)"get_error", NULL);

    if ((PyObject*)p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
    {
      ampspy::unhandled_exception();
    }
    // Check if previous invocation of python code has resulted in a Ctrl-C delivered.
    if (ampspy::_is_signaled)
    {
      PyErr_SetNone(PyExc_KeyboardInterrupt);
    }

    exc::throwError();
    // Convert server chooser's return value to a string.
    AMPSPyReference<> asString = PyObject_Str(p);
    const char* returnValue = PyString_AsString(asString);
    std::string returnedStr(returnValue);

    return returnedStr;
  }

  void server_chooser_wrapper::reportSuccess(const ConnectionInfo& info_)
  {
    LOCKGIL;
    AMPSPyReference<> dict = PyDict_New();
    for (ConnectionInfo::const_iterator i = info_.begin(); i != info_.end(); ++i)
    {
      AMPSPyReference<> val = PyString_FromString(i->second.c_str());
      PyDict_SetItemString(dict, i->first.c_str(), val);
    }
    AMPSPyReference<> p = PyObject_CallMethod((PyObject*)_self, (char*)"report_success", (char*)"(O)",
                                              (PyObject*)dict);
    if ((PyObject*)p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
    {
      ampspy::unhandled_exception();
    }
    exc::throwError();
  }

  void server_chooser_wrapper::add(const std::string& uri_)
  {
    LOCKGIL;
    AMPSPyReference<> p = PyObject_CallMethod((PyObject*)_self, (char*)"add",
                                              (char*)"(s)", (char*)uri_.c_str());
    if ((PyObject*)p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
    {
      ampspy::unhandled_exception();
    }
    exc::throwError();
  }

  void server_chooser_wrapper::remove(const std::string& uri_)
  {
    LOCKGIL;
    AMPSPyReference<> p = PyObject_CallMethod((PyObject*)_self, (char*)"remove",
                                              (char*)"(s)", (char*)uri_.c_str());
    if ((PyObject*)p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
    {
      ampspy::unhandled_exception();
    }
    exc::throwError();
  }

  class reconnect_delay_strategy_wrapper
    : public AMPS::ReconnectDelayStrategyImpl
  {
  public:
    reconnect_delay_strategy_wrapper(PyObject* impl_)
      : _impl(impl_)
    {
      Py_INCREF(_impl);
    }
    ~reconnect_delay_strategy_wrapper(void)
    {
      try
      {
        LOCKGIL;
        Py_DECREF(_impl);
      }
      catch (...)
      {
        // absorb any exception here.
      }
    }

    unsigned int getConnectWaitDuration(const std::string& uri_)
    {
      LOCKGIL;
      AMPSPyReference<> result = PyObject_CallMethod((PyObject*)_impl,
                                                     (char*)"get_connect_wait_duration", (char*)"(s)",
                                                     (char*)uri_.c_str());
      if ((PyObject*)result == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
      {
        ampspy::unhandled_exception();
      }
      if (PyErr_ExceptionMatches(PyExc_AttributeError))
      {
        throw std::runtime_error("The supplied reconnect delay strategy"
                                 " object is missing the required"
                                 " \"get_connect_wait_duration\" method.");
      }
      exc::throwError();

      long returnValue = PyInt_AsLong(result);
      if (returnValue == -1)
      {
        throw std::runtime_error("The supplied reconnect delay strategy object "
                                 "returned an invalid value from get_connect_wait_duration.");
      }
      return returnValue;
    }

    void reset(void)
    {
      LOCKGIL;
      AMPSPyReference<> result = PyObject_CallMethod((PyObject*)_impl,
                                                     (char*)"reset", NULL);
      if ((PyObject*)result == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
      {
        ampspy::unhandled_exception();
      }
      if (PyErr_ExceptionMatches(PyExc_AttributeError))
      {
        throw std::runtime_error("The supplied reconnect delay strategy"
                                 " object is missing the required"
                                 " \"reset\" method.");
      }
      exc::throwError();
    }
  private:
    PyObject*     _impl;

  };

  class failed_resubscribe_handler_wrapper
    : public AMPS::FailedResubscribeHandler
  {
  public:
    failed_resubscribe_handler_wrapper(PyObject* impl_)
      : _impl(impl_)
    {
      Py_INCREF(_impl);
      message = (ampspy::message::obj*)_PyObject_New(ampspy::message::message_type);
      message->isOwned = false;
    }
    virtual ~failed_resubscribe_handler_wrapper(void)
    {
      try
      {
        LOCKGIL;
        Py_DECREF(_impl);
      }
      catch (...)
      {
        // absorb any exception here.
      }
    }

    virtual bool failure(const Message& message_, const MessageHandler&,
                         unsigned requestedAckTypes_,
                         const AMPSException& exception_)
    {
      LOCKGIL;
      message->pMessage = (Message*)&message_;
      PyObject* ctor_args = Py_BuildValue("(s)", exception_.what());
      if (ctor_args == NULL)
      {
        ampspy::unhandled_exception();
        return false;
      }
      PyObject* exception = PyObject_CallObject(ampspy::exc::AMPSException, ctor_args);
      Py_DECREF(ctor_args);
      if (exception == NULL)
      {
        ampspy::unhandled_exception();
        return false;
      }
      PyObject* args = Py_BuildValue("(OkO)", message, (unsigned long)requestedAckTypes_, exception);
      PyObject* result = PyObject_Call(_impl, args, (PyObject*)NULL);
      Py_DECREF(args);
      Py_DECREF(exception);
      if (result == NULL)
      {
        ampspy::unhandled_exception();
        return false;
      }
      bool retVal = PyObject_IsTrue(result) != 0;
      Py_DECREF(result);
      exc::throwError();
      return retVal;
    }

  private:
    PyObject*     _impl;
    message::obj* message;
  };

  namespace haclient
  {

//    def __init__(self, name):
    static int ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      const unsigned MEMORY_PUBLISH_STORE_INITIAL_SIZE = 10000;
      char* name = NULL, *publish_store = NULL, *bookmark_store = NULL;
      int no_store = 0;

      static const char* kwargs[] = { "name", "publish_store", "bookmark_store", "no_store", NULL };
      if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|ssi", (char**)kwargs, &name, &publish_store, &bookmark_store, &no_store))
      {
        return -1;
      }
      self->_client.pClient = new AMPS::HAClient(name);

      if (publish_store)
      {
        ((AMPS::Client*)self->_client.pClient)->setPublishStore(Store(new PublishStore(publish_store)));
      }
      else if (!no_store)
      {
        ((AMPS::Client*)self->_client.pClient)->setPublishStore(Store(new MemoryPublishStore(MEMORY_PUBLISH_STORE_INITIAL_SIZE)));
      }

      if (bookmark_store)
      {
        ((AMPS::Client*)self->_client.pClient)->setBookmarkStore(BookmarkStore(
                                                  new MMapBookmarkStore(bookmark_store)));
      }
      else if (!no_store)
      {
        ((AMPS::Client*)self->_client.pClient)->setBookmarkStore(BookmarkStore(new MemoryBookmarkStore()));
      }

      ampspy::client::_initializeInternals(&self->_client);
      self->_pyServerChooser = NULL;
      self->_pyDelayStrategy = NULL;

      return 0;
    }
    static void dtor(obj* self)
    {
      if (self->_pyServerChooser)
      {
        Py_DECREF(self->_pyServerChooser);
      }
      // invoke the 'destructor' for the client, who in turn deletes the AMPS::Client.
      client::destructor((PyObject*)self);
    }

    static PyObject* set_server_chooser(obj* self, PyObject* args)
    {
      if (self->_pyServerChooser)
      {
        Py_DECREF(self->_pyServerChooser);
      }
      if (!PyArg_ParseTuple(args, "O", &self->_pyServerChooser))
      {
        return NULL;
      }
      Py_INCREF(self->_pyServerChooser);

      // we assume anything you pass is a server chooser, duck-typed
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);

      haClient.setServerChooser(ServerChooser(new server_chooser_wrapper(self->_pyServerChooser)));

      NONE;
    }

    static PyObject* get_server_chooser(obj* self, PyObject* args)
    {
      CALL_RETURN_PYOBJECT(self->_pyServerChooser);
    }

    static PyObject* set_logon_options(obj* self, PyObject* args)
    {
      const char* options = NULL;
      if (!PyArg_ParseTuple(args, "s", &options))
      {
        return NULL;
      }

      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);
      haClient.setLogonOptions(options);

      NONE;
    }

    static PyObject* get_logon_options(obj* self, PyObject* args)
    {
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);
      CALL_RETURN_STRING(haClient.getLogonOptions());
    }

    static PyObject* connect_and_logon(obj* self, PyObject* args)
    {
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);

      CALL_RETURN_NONE(haClient.connectAndLogon());
    }

    static PyObject* connect(obj* self, PyObject* args) // -V524
    {
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);
      CALL_RETURN_NONE(haClient.connectAndLogon());
    }

    static PyObject* logon(obj* self, PyObject* args)
    {
      PyErr_SetString(PyExc_TypeError, "To an HAClient, provide a ServerChooser via set_server_chooser(), and then call connect_and_logon().");
      return NULL;
    }

    static PyObject* set_timeout(obj* self, PyObject* args)
    {
      int timeout = 0;

      if (!PyArg_ParseTuple(args, "i", &timeout))
      {
        return NULL;
      }
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);
      CALL_RETURN_NONE(haClient.setTimeout(timeout));
    }

    static PyObject* set_reconnect_delay(obj* self, PyObject* args)
    {
      int reconnectDelay = 0;

      if (!PyArg_ParseTuple(args, "i", &reconnectDelay))
      {
        return NULL;
      }
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);
      CALL_RETURN_NONE(haClient.setReconnectDelay(reconnectDelay));
    }

    static PyObject* set_reconnect_delay_strategy(obj* self, PyObject* args)
    {
      PyObject* delayStrategy;
      if (!PyArg_ParseTuple(args, "O", &delayStrategy))
      {
        return NULL;
      }
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);
      Py_XDECREF(self->_pyDelayStrategy);
      self->_pyDelayStrategy = delayStrategy;
      Py_INCREF(self->_pyDelayStrategy);

      // is it one of our types?
      if (exponentialdelaystrategy::type.isInstanceOf(delayStrategy))
      {
        exponentialdelaystrategy::obj* obj =
          reinterpret_cast<exponentialdelaystrategy::obj*> (delayStrategy);
        CALL_RETURN_NONE(haClient.setReconnectDelayStrategy(obj->impl));
      }
      else if (fixeddelaystrategy::type.isInstanceOf(delayStrategy))
      {
        fixeddelaystrategy::obj* obj =
          reinterpret_cast<fixeddelaystrategy::obj*> (delayStrategy);
        CALL_RETURN_NONE(haClient.setReconnectDelayStrategy(obj->impl));
      }

      haClient.setReconnectDelayStrategy(
        new reconnect_delay_strategy_wrapper(delayStrategy));
      NONE;
    }

    static PyObject* get_reconnect_delay_strategy(obj* self, PyObject* args)
    {
      Py_XINCREF(self->_pyDelayStrategy);
      return self->_pyDelayStrategy;
    }

    static PyObject* discard(obj* self, PyObject* args)
    {
      ampspy::message::obj* message;
      if (!PyArg_ParseTuple(args, "O!", ampspy::message::message_type.pPyObject(), &message))
      {
        return NULL;
      }

      AMPS::Message& ampsMessage = * message->pMessage;
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);

      CALL_RETURN_NONE(haClient.getBookmarkStore().discard(ampsMessage));
    }

    static PyObject* prune_store(obj* self, PyObject* args)
    {
      const char* tmpFileName = NULL;
      if (!PyArg_ParseTuple(args, "|s", &tmpFileName))
      {
        return NULL;
      }

      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);

      CALL_RETURN_NONE(haClient.getBookmarkStore().prune(tmpFileName ? std::string(tmpFileName) : std::string()));
    }

    static PyObject* get_most_recent(obj* self, PyObject* args)
    {
      const char* subId;
      if (!PyArg_ParseTuple(args, "s", &subId))
      {
        return NULL;
      }
      HAClient& haClient = *(HAClient*)(AMPS::Client*)(self->_client.pClient);
      // getMostRecent returns a Field that must be cleared
      AMPS::Field recent = haClient.getBookmarkStore().getMostRecent(subId);
      std::string recentStr = (std::string)recent;
      recent.clear();
      CALL_RETURN_STRING(recentStr);
    }

    static PyObject* get_resubscription_timeout(obj* self, PyObject* args)
    {
      MemorySubscriptionManager* subMgr = (MemorySubscriptionManager*)(((AMPS::Client*)self->_client.pClient)->getSubscriptionManager());
      CALL_RETURN_SIZE_T((size_t)(subMgr->getResubscriptionTimeout()));
    }

    static PyObject* set_resubscription_timeout(obj* self, PyObject* args)
    {
      int timeout = 0;
      if (!PyArg_ParseTuple(args, "i", &timeout))
      {
        return NULL;
      }
      MemorySubscriptionManager* subMgr = (MemorySubscriptionManager*)(((AMPS::Client*)self->_client.pClient)->getSubscriptionManager());
      CALL_RETURN_NONE(subMgr->setResubscriptionTimeout(timeout));
    }

    static PyObject* get_default_resubscription_timeout(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T((size_t)(MemorySubscriptionManager::getDefaultResubscriptionTimeout()));
    }

    static PyObject* set_default_resubscription_timeout(obj* self, PyObject* args)
    {
      int timeout = 0;
      if (!PyArg_ParseTuple(args, "i", &timeout))
      {
        return NULL;
      }
      CALL_RETURN_NONE(MemorySubscriptionManager::setDefaultResubscriptionTimeout(timeout));
    }

    static PyObject* set_failed_resubscribe_handler(obj* self, PyObject* args)
    {
      PyObject* handler = NULL;
      if (!PyArg_ParseTuple(args, "O", &handler))
      {
        return NULL;
      }
      if (!handler || !PyCallable_Check(handler))
      {
        PyErr_SetString(PyExc_TypeError, "argument must be a callable");
        return NULL;
      }
      std::shared_ptr<failed_resubscribe_handler_wrapper> wrapper(new failed_resubscribe_handler_wrapper(handler));
      CALL_RETURN_NONE(((AMPS::Client*)self->_client.pClient)->getSubscriptionManager()->setFailedResubscribeHandler(wrapper));
    }

    AMPSDLL ampspy::ampspy_type_object haclient_type;

    void add_types(PyObject* module_)
    {
      exception_name_translator["UsageException"] = exc::AMPSException;
      exception_name_translator["StoreException"] = exc::AMPSException;
      exception_name_translator["DisconnectedException"] = exc::DisconnectedException;
      exception_name_translator["AlreadyConnectedException"] = exc::AlreadyConnectedException;
      exception_name_translator["RetryOperationException"] = exc::RetryOperationException;
      exception_name_translator["AuthenticationException"] = exc::AuthenticationException;
      exception_name_translator["NotEntitledException"] = exc::NotEntitledException;
      exception_name_translator["TimedOutException"] = exc::TimedOutException;
      exception_name_translator["ConnectionRefusedException"] = exc::ConnectionRefusedException;
      exception_name_translator["InvalidURIException"] = exc::InvalidUriException;
      exception_name_translator["TransportTypeException"] = exc::TransportTypeException;
      exception_name_translator["BadFilterException"] = exc::BadFilterException;
      exception_name_translator["BadRegexTopicException"] = exc::BadRegexTopicException;
      exception_name_translator["InvalidTopicException"] = exc::InvalidTopicException;
      exception_name_translator["NameInUseException"] = exc::NameInUseException;
      exception_name_translator["SubscriptionAlreadyExistsException"] = exc::SubscriptionAlreadyExistsException;
      exception_name_translator["SubidInUseException"] = exc::SubidInUseException;
      exception_name_translator["UnknownException"] = exc::UnknownException;
      exception_name_translator["CommandException"] = exc::CommandException;
      exception_name_translator["ConnectionException"] = exc::ConnectionException;
      exception_name_translator["AMPSException"] = exc::AMPSException;

      haclient_type.setName("AMPS.HAClient")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(dtor)
      .setConstructorFunction(ctor)
      .setBaseType()
      .setBase(client::client_type)
      .setDoc(class_doc)
      .notCopyable()
      .addMethod("set_server_chooser", set_server_chooser, set_server_chooser_doc)
      .addMethod("get_server_chooser", get_server_chooser, get_server_chooser_doc)
      .addMethod("set_logon_options", set_logon_options, set_logon_options_doc)
      .addMethod("get_logon_options", get_logon_options, get_logon_options_doc)
      .addMethod("connect_and_logon", connect_and_logon, connect_and_logon_doc)
      .addMethod("set_timeout", set_timeout, set_timeout_doc)
      .addMethod("set_reconnect_delay", set_reconnect_delay, set_reconnect_delay_doc)
      .addMethod("set_reconnect_delay_strategy", set_reconnect_delay_strategy, set_reconnect_delay_strategy_doc)
      .addMethod("get_reconnect_delay_strategy", get_reconnect_delay_strategy, get_reconnect_delay_strategy_doc)
      .addMethod("discard", discard, discard_doc)
      .addMethod("prune_store", prune_store, prune_store_doc)
      .addMethod("get_most_recent", get_most_recent, get_most_recent_doc)
      .addMethod("connect", connect, connect_and_logon_doc)
      .addMethod("logon", logon, haclient_connect_doc)
      .addMethod("get_default_resubscription_timeout", get_default_resubscription_timeout, get_default_resubscription_timeout_doc)
      .addMethod("set_default_resubscription_timeout", set_default_resubscription_timeout, set_default_resubscription_timeout_doc)
      .addMethod("get_resubscription_timeout", get_resubscription_timeout, get_resubscription_timeout_doc)
      .addMethod("set_resubscription_timeout", set_resubscription_timeout, set_resubscription_timeout_doc)
      .addMethod("set_failed_resubscribe_handler", set_failed_resubscribe_handler, set_failed_resubscribe_handler_doc)
      .createType()
      .registerType("HAClient", module_);
    }

  } // namespace haclient

} // namespace ampspy
