///////////////////////////////////////////////////////////////////////////
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
#include <amps/util.hpp>
#include <ampspy_types.hpp>
#include <ampspy_defs.hpp>
#include <algorithm>
#include <set>
#include <sstream>
#include "client_docs.h"
#include <stddef.h>
#include <ampspy_bookmarkstore.hpp>
#include <ampspy_type_object.hpp>

using namespace AMPS;
namespace ampspy
{

  namespace client
  {

    AMPSDLL ampspy::ampspy_type_object client_type;

    namespace connection_state_listener
    {
      const long ORIGINAL_VERSION = 5020100;
      const long VERSION_522 = 5020200;
      const long EXTENDED_STATES = 5020200;

      ampspy::ampspy_type_object connection_state_listener_type;

      void add_types(void)
      {
        connection_state_listener_type.setName("AMPS.ConnectionStateListener")
        .setDoc("\nAMPS ``ConnectionStateListener`` type used to determine the new connection state.\n")
        .createType()
        .addStatic("STATE_DISCONNECTED",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::Disconnected))
        .addStatic("STATE_SHUTDOWN",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::Shutdown))
        .addStatic("STATE_CONNECTED",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::Connected))
        .addStatic("STATE_LOGGED_ON",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::LoggedOn))
        .addStatic("STATE_PUBLISH_REPLAYED",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::PublishReplayed))
        .addStatic("STATE_HEARTBEAT_INITIATED",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::HeartbeatInitiated))
        .addStatic("STATE_RESUBSCRIBED",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::Resubscribed))
        .addStatic("STATE_UNKNOWN",
                   PyInt_FromLong((long)AMPS::ConnectionStateListener::UNKNOWN))
        .addStatic("ORIGINAL_VERSION", PyInt_FromLong(ORIGINAL_VERSION))
        .addStatic("VERSION_522", PyInt_FromLong(VERSION_522))
        .addStatic("EXTENDED_STATES", PyInt_FromLong(EXTENDED_STATES));
      }

    } //namespace connection_state_listener

    class SimpleMutex
    {
      // Not implemented.
      SimpleMutex& operator=(const SimpleMutex& rhs);
      SimpleMutex(const SimpleMutex& rhs);
#ifdef _WIN32
      CRITICAL_SECTION _lock;
    public:
      SimpleMutex()
      {
        InitializeCriticalSection(&_lock);
      }
      ~SimpleMutex()
      {
        DeleteCriticalSection(&_lock);
      }
      void acquireRead()
      {
        EnterCriticalSection(&_lock);
      }
      void releaseRead()
      {
        LeaveCriticalSection(&_lock);
      }
#else
      pthread_mutex_t _lock;
      pthread_cond_t _condition;
    public:
      SimpleMutex()
      {
        pthread_mutexattr_t attr;
        pthread_mutexattr_init(&attr);
        pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
        pthread_mutex_init(&_lock, &attr);
        pthread_mutexattr_destroy(&attr);
      }
      ~SimpleMutex()
      {
        pthread_mutex_destroy(&_lock);
      }
      void acquireRead()
      {
        pthread_mutex_lock(&_lock);
      }
      void releaseRead()
      {
        pthread_mutex_unlock(&_lock);
      }
#endif
    };
    static SimpleMutex _createdHandlersLock;
    static std::set<void*> _createdHandlers;

    AMPSDLL void amps_python_client_atfork_prepare(void)
    {
      _createdHandlersLock.acquireRead();
    }
    AMPSDLL void amps_python_client_atfork_parent(void)
    {
      _createdHandlersLock.releaseRead();
    }
    AMPSDLL void amps_python_client_atfork_child(void)
    {
      // Memset the old and reinitialize a new one on top of it.
      // It is not safe to release the child lock here; you'll likely get EPERM.
      _createdHandlersLock.~SimpleMutex();
      new (&_createdHandlersLock) SimpleMutex();
    }

    class TransportFilter : public AMPS::ConnectionStateListener
    {
    public:
      TransportFilter(PyObject* handler_)
        : _handler(handler_),
          _remain(0)
      {
        Py_INCREF(_handler);
      }
      ~TransportFilter()
      {
        Py_XDECREF(_handler);
        _handler = NULL;
      }

      PyObject* getHandler(void) const
      {
        return _handler;
      }

      void connectionStateChanged(AMPS::ConnectionStateListener::State newState_);
      static void filter(const unsigned char* data_, size_t len_, short direction_,
                         void* vpThis_);
#if PY_MAJOR_VERSION >= 3 || (PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION >= 7)
      // This will use a MemoryView instead of a string so the bytes can be modified
      static void filterModifiable(const unsigned char* data_, size_t len_,
                                   short direction_, void* vpThis_);
#endif

    private:
      PyObject* _handler;
      size_t _remain;
    };

    struct AMPSDLL callback_info
    {
      callback_info(obj* client_, PyObject* handler_)
        : _client(client_),
          _handler(handler_)
      {
        assert(client_->pClient);
        Py_INCREF(_handler);
      }
      ~callback_info()
      {
        Py_CLEAR(_handler);
      }

      void release(void)
      {
        _client = NULL;
        Py_CLEAR(_handler);
        _handler = NULL;
      }

      PyObject* getHandler(void) const
      {
        return _handler;
      }

      obj* getClient(void) const
      {
        return _client;
      }

      static void add(void* vpInfo_);
      static void destroy(void* vpInfo_);

    private:
      obj*      _client;
      PyObject* _handler;
      callback_info(const callback_info&);
      void operator=(const callback_info&);
    };

    void callback_info::destroy(void* vpInfo_)
    {
      callback_info* pInfo = (callback_info*)vpInfo_;
      if (!pInfo->getClient())
      {
        LOCKGIL;
        delete pInfo;
        return;
      }
      callback_infos* pInfos = pInfo->getClient()->callbackInfos;
      // If pInfos is null, this will be deleted in the client destroy function.
      if (pInfos && pInfo->getHandler())
      {
        callback_infos::iterator i = std::find(pInfos->begin(), pInfos->end(),
                                               pInfo);
        if (i != pInfos->end())
        {
          pInfos->erase(i);
        }
        LOCKGIL;
        delete pInfo;
      }
    }

    void callback_info::add(void* vpInfo_)
    {
      callback_info* pInfo = (callback_info*)vpInfo_;
      // If Client is null we're done
      if (pInfo->getClient())
      {
        callback_infos* pInfos = pInfo->getClient()->callbackInfos; // -V826
        // If pInfos is not null, add it
        if (pInfos)
        {
          pInfos->push_back(pInfo);
        }
      }
    }

    void _initializeInternals(obj* self)
    {
      self->disconnectHandler = NULL;
      self->callbackInfos = new callback_infos();
      self->weakreflist = NULL;
      self->connectionStateListeners = new connection_state_listeners();

      self->message = (ampspy::message::obj*)_PyObject_New(
                        ampspy::message::message_type);
      self->message->isOwned = false;
      assert(self->message);
      self->message_args = Py_BuildValue("(O)", self->message);
      assert(self->message_args);

      self->transportFilter = NULL;
      self->threadCreatedCallback = NULL;
    }

//    def __init__(self, name):
    int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      const char* clientName;
      if (!PyArg_ParseTuple(args, "s", &clientName))
      {
        return -1;  // must have a client name
      }
      self->pClient = new Client(clientName);
      _initializeInternals(self);
      return 0;
    }

    static std::shared_ptr<AMPS::ExceptionListener> g_UnsetExceptionListener =
      std::make_shared<AMPS::ExceptionListener>();

    static void _clear(obj* self)
    {
      //                            IMPORTANT
      // We aren't supplying our own tp_alloc or tp_free, so Python is already
      // calling PyObject_GC_Track and PyObject_GC_UnTrack for us. However,
      // it is very important to untrack ourselves before we unlock the GIL
      // below. If we unlock the GIL prior to untracking, it results in self --
      // with zero references -- being potentially processed by python gc,
      // resulting in a double delete and memory corruption inside the gc.
      // By removing it here, we assure GC that we don't need it to track
      // us any more. See the big comment in python's Modules/gcmodule.c:
      // update_refs() for more information.
      PyObject_GC_UnTrack(self);

      AMPS::Client* pClient = (AMPS::Client*)AMPSPY_IEX_GET(&self->pClient,
                              (AMPS::Client*)0);
      callback_infos* pCallbackInfos = (callback_infos*)AMPSPY_IEX_GET(
                                         &self->callbackInfos, (callback_infos*)0); // -V826
      connection_state_listeners* listeners = (connection_state_listeners*)
                                              AMPSPY_IEX_GET(&self->connectionStateListeners, (connection_state_listeners*)0);
      // We don't want to invoke the exception handler again, but we can't reset
      // in case the receive thread is already in its exceptionThrown method. The
      // GIL isn't locked until inside the PyExceptionListener.
      if (self->exceptionHandler)
      {
        ((PyExceptionListener*)(self->exceptionHandler.get()))->set(NULL);
      }
      // Unset any Python objects listening for client events, then delete the
      // client. The Python objects should all still exist at this point in case
      // the reader thread was already at the point of invoking one.
      if (pClient)
      {
        UnlockGIL __unlock__;
        ((AMPS::Client*)pClient)->setExceptionListener(g_UnsetExceptionListener);
        ((AMPS::Client*)pClient)->setTransportFilterFunction(NULL, 0);
        ((AMPS::Client*)pClient)->clearConnectionStateListeners();
        delete pClient;
      }
      // Clear Python connection state listeners
      if (listeners)
      {
        for (connection_state_listeners::iterator i = listeners->begin();
             i != listeners->end(); ++i)
        {
          delete i->second;
          i->second = 0;
        }
        delete listeners;
      }
      // Clear Python message callbacks from created wrappers
      if (pCallbackInfos)
      {
        AMPS::Lock<SimpleMutex> l(_createdHandlersLock);
        for (callback_infos::iterator i = pCallbackInfos->begin();
             i != pCallbackInfos->end(); ++i)
        {
          _createdHandlers.erase(*i);
        }
      }
      // Release Python transport filter
      delete self->transportFilter;
      // Release Python exception handler
      if (self->exceptionHandler)
      {
        self->exceptionHandler.reset();
      }
      // Release Python disconnect handler
      Py_CLEAR(self->disconnectHandler);
      // Release Python message callbacks
      if (pCallbackInfos)
      {
        for (callback_infos::iterator i = pCallbackInfos->begin();
             i != pCallbackInfos->end(); ++i)
        {
          callback_info* pCallbackInfo = *i;
          delete pCallbackInfo;
        }
        delete pCallbackInfos;
      }
      Py_CLEAR(self->threadCreatedCallback);
      Py_CLEAR(self->message_args);
      Py_CLEAR(self->message);
    }

    AMPSDLL void destructor(PyObject* self_)
    {
      obj* self = (obj*)self_;
      if (self->weakreflist)
      {
        PyObject_ClearWeakRefs((PyObject*) self);
      }
      _clear(self);
      shims::free(self_);
    }

    static bool messageHandlerSupplied(PyObject* args, PyObject* kwargs)
    {
      return (kwargs != NULL && PyDict_GetItemString(kwargs, "on_message") != NULL)
             || (PyTuple_Size(args) > 0 &&
                 (   PyCallable_Check(PyTuple_GET_ITEM(args, 0))
                     || cmessagehandler::isCHandler(PyTuple_GET_ITEM(args, 0))));
    }

    static ampspy::messagestream::obj* createMessageStream(obj* pythonClient_,
                                                           AMPS::Client* pClient_,
                                                           bool isSow_,
                                                           bool isStats_,
                                                           bool sendCompleted_ = true)
    {
      ampspy::messagestream::obj* messagestream = (ampspy::messagestream::obj*)
          PyObject_CallObject(ampspy::messagestream::messagestream_type, NULL);
      messagestream->internalInit((PyObject*)pythonClient_, pClient_, isSow_,
                                  isStats_, sendCompleted_);
      return messagestream;
    }
    static ampspy::messagestream::obj* createNoopMessageStream(void)
    {
      ampspy::messagestream::obj* messagestream = (ampspy::messagestream::obj*)
          PyObject_CallObject(ampspy::messagestream::messagestream_type, NULL);
      return messagestream;
    }

    class ConnectionStateListenerWrapperV521 : public AMPS::ConnectionStateListener
    {
      PyObject* _listener;
    public:
      ConnectionStateListenerWrapperV521(PyObject* listener_)
        : _listener(listener_)
      {
        Py_INCREF(listener_);
      }
      ~ConnectionStateListenerWrapperV521()
      {
        try
        {
          LOCKGIL;
          Py_CLEAR(_listener);
        }
        catch (...) { }
      }
      void connectionStateChanged(State newState_)
      {
        LOCKGIL;
        PyObject* args = Py_BuildValue("(O)",
                            (newState_ == AMPS::ConnectionStateListener::Disconnected ||
                             newState_ == AMPS::ConnectionStateListener::Shutdown) ? Py_False : Py_True);
        Py_XDECREF(PyObject_CallObject(_listener, args));
        Py_DECREF(args);
      }
    };

    class ConnectionStateListenerWrapper : public AMPS::ConnectionStateListener
    {
      PyObject* _listener;
    public:
      ConnectionStateListenerWrapper(PyObject* listener_)
        : _listener(listener_)
      {
        Py_INCREF(listener_);
      }
      ~ConnectionStateListenerWrapper()
      {
        LOCKGIL;
        Py_CLEAR(_listener);
      }
      void connectionStateChanged(State newState_)
      {
        LOCKGIL;
        PyObject* pyState = PyInt_FromLong((long)newState_);
        PyObject* args = Py_BuildValue("(O)", pyState);
        Py_XDECREF(PyObject_CallObject(_listener, args));
        Py_DECREF(args);
        Py_DECREF(pyState);
      }
    };


    static PyObject* add_connection_state_listener(obj* self, PyObject* args)
    {
      PyObject* callable;
      int version = connection_state_listener::ORIGINAL_VERSION;
      if (!PyArg_ParseTuple(args, "O|I", &callable, &version))
      {
        return NULL;
      }
      if (!PyCallable_Check(callable))
      {
        PyErr_SetString(PyExc_TypeError, "argument 1 must be a callable");
        return NULL;
      }
      ConnectionStateListener* wrap = NULL;
      if (version >= connection_state_listener::VERSION_522)
      {
        wrap = new ConnectionStateListenerWrapper(callable);
      }
      else
      {
        wrap = new ConnectionStateListenerWrapperV521(callable);
      }
      (*((connection_state_listeners*)self->connectionStateListeners))[callable] =
        wrap;
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->addConnectionStateListener(
                         wrap));
    }

    static PyObject* remove_connection_state_listener(obj* self, PyObject* args)
    {
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (!PyCallable_Check(callable))
      {
        PyErr_SetString(PyExc_TypeError, "argument 1 must be a callable");
        return NULL;
      }
      connection_state_listeners::iterator it = ((connection_state_listeners*)
          self->connectionStateListeners)->find(callable);
      if (it != ((connection_state_listeners*)self->connectionStateListeners)->end())
      {
        {
          UnlockGIL __unlock__;
          ((AMPS::Client*)(self->pClient))->removeConnectionStateListener(
            it->second); // so the client doesn't call it again
        }
        delete it->second; // will remove the reference to the underlying python object.
        ((connection_state_listeners*)self->connectionStateListeners)->erase(it);
      }
      NONE;
    }


//    def connect(self, uri):
    static PyObject* connect(obj* self, PyObject* args)
    {
      const char* uri;
      if (!PyArg_ParseTuple(args, "s", &uri))
      {
        return NULL;
      }
      if (strlen(uri) > 3 && uri[0] == 't' && uri[1] == 'c' && uri[2] == 'p'
          && uri[3] == 's')
      {
        PyObject* initResult = ampspy_ssl_init(NULL, NULL);
        if (initResult == NULL)
        {
          return NULL;
        }
        else
        {
          Py_DECREF(initResult);
        }
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->connect(uri));
    }

//    def logon(self, timeout=0, authenticator=DefaultAuthenticator(), options=""):
    static PyObject* logon(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwargs[] = { "timeout", "authenticator", "options", NULL };
      int timeout = 0;
      PyObject* auth = NULL;
      const char* options = NULL;
      if (!PyArg_ParseTupleAndKeywords(args, kw, "|IOs", (char**)kwargs, &timeout,
                                       &auth, &options))
      {
        return NULL;
      }
      PyAuthenticator bridge(auth);
      if (auth)
      {
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->logon(timeout,
                                                                   bridge,
                                                                   options));
      }
      else
      {
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->logon(options,
                                                                   timeout));
      }

    }

    static PyObject* setName(obj* self, PyObject* args)
    {
      const char* name;
      if (!PyArg_ParseTuple(args, "s", &name))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setName(name));
    }

//    def name(self):
//    def get_name(self):
//    def getName(self):
    static PyObject* getName(obj* self, PyObject* args)
    {
      CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->getName());
    }

//    def get_name_hash(self):
    static PyObject* get_name_hash(obj* self, PyObject* args)
    {
      CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->getNameHash());
    }

//    def get_name_hash_value(self):
    static PyObject* get_name_hash_value(obj* self, PyObject* args)
    {
      CALL_RETURN_UINT64_T(((AMPS::Client*)(self->pClient))->getNameHashValue());
    }

//    def get_logon_correlation_data(self):
    static PyObject* get_logon_correlation_data(obj* self, PyObject* args)
    {
      CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->getLogonCorrelationData());
    }

//    def set_logon_correlation_data(self, data):
    static PyObject* set_logon_correlation_data(obj* self, PyObject* args)
    {
      const char* logonData;
      if (!PyArg_ParseTuple(args, "s", &logonData))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setLogonCorrelationData(
                         logonData));
    }

//    def uri(self):
//    def get_uri(self):
//    def getUri(self):
    static PyObject* getURI(obj* self, PyObject* args)
    {
      CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->getURI());
    }

//    def get_server_version(self):
    static PyObject* get_server_version(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T(((AMPS::Client*)(self->pClient))->getServerVersion());
    }

//    def get_server_version_info(self):
    static PyObject* get_server_version_info(obj* self, PyObject* args)
    {
      PyObject* returnVal = NULL;
      versioninfo::obj* versionInfo = (versioninfo::obj*)PyObject_New(
                                        versioninfo::obj,
                                        versioninfo::versioninfo_type);
      versionInfo->pVersionInfo = new VersionInfo(((AMPS::Client*)(
            self->pClient))->getServerVersionInfo());
      returnVal = (PyObject*)versionInfo;
      return returnVal;
    }

//    def convert_version_to_number(self, version_string)
    static PyObject* convert_version_to_number(obj* self, PyObject* args)
    {
      char* versionStr;
      if (!PyArg_ParseTuple(args, "s", &versionStr))
      {
        return NULL;
      }
      CALL_RETURN_SIZE_T(((AMPS::Client*)(self->pClient))->convertVersionToNumber(
                           versionStr));
    }

//    def disconnect(self):
//    def close(self):
    static PyObject* disconnect(obj* self, PyObject* args)
    {
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->disconnect());
    }

//    def publish(self, topic, data, expiration=None):
    static PyObject* publish(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "topic", "data", "expiration", NULL };
      const char* topic, *data;
      Py_ssize_t topicLength, dataLength;
      unsigned long expiration = 0;
      PyObject* expire = NULL;
      if (!PyArg_ParseTupleAndKeywords(args, kw, "s#s#|O", (char**)kwlist,
                                       &topic, &topicLength, &data, &dataLength, &expire))
      {
        return NULL;
      }
#if PY_MAJOR_VERSION >= 3
      if (!expire || !PyLong_Check(expire) ||
          (expiration = PyLong_AsUnsignedLong(expire)) == (unsigned long) - 1)
#else
      if (!expire || !PyInt_Check(expire) ||
          (expiration = PyInt_AsUnsignedLongMask(expire)) == (unsigned long) - 1)
#endif
      {
        CALL_RETURN_UINT64_T(((AMPS::Client*)(self->pClient))->publish(topic,
                                                                       topicLength,
                                                                       data,
                                                                       dataLength));
      }
      else
      {
        CALL_RETURN_UINT64_T(((AMPS::Client*)(self->pClient))->publish(topic,
                             topicLength, data, dataLength, expiration));
      }
    }

//    def delta_publish(self, topic, data, expiration=None):
//    def deltaPublish(self, topic, data, expiration=None):
    static PyObject* delta_publish(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "topic", "data", "expiration", NULL };
      const char* topic, *data;
      Py_ssize_t topicLength, dataLength;
      unsigned long expiration = 0;
      PyObject* expire = NULL;
      if (!PyArg_ParseTupleAndKeywords(args, kw, "s#s#|O", (char**)kwlist,
                                       &topic, &topicLength, &data, &dataLength, &expire))
      {
        return NULL;
      }
#if PY_MAJOR_VERSION >= 3
      if (!expire || !PyLong_Check(expire) ||
          (expiration = PyLong_AsUnsignedLong(expire)) == (unsigned long) - 1)
#else
      if (!expire || !PyInt_Check(expire) ||
          (expiration = PyInt_AsUnsignedLongMask(expire)) == (unsigned long) - 1)
#endif
      {
        CALL_RETURN_UINT64_T(((AMPS::Client*)(self->pClient))->deltaPublish(topic,
                                                                            topicLength,
                                                                            data,
                                                                            dataLength));
      }
      else
      {
        CALL_RETURN_UINT64_T(((AMPS::Client*)(self->pClient))->deltaPublish(topic,
                                                                            topicLength,
                                                                            data,
                                                                            dataLength,
                                                                            expiration));
      }
    }

//    def unsubscribe(self, sub_id=None):
    static PyObject* unsubscribe(obj* self, PyObject* args)
    {
      const char* subid = NULL;
      if (!PyArg_ParseTuple(args, "|s", &subid))
      {
        return NULL;
      }
      if (subid)
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->unsubscribe(subid));
      }
      else
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->unsubscribe());
      }
    }
//    def allocate_message(self):
//    def allocateMessage(self):
    static PyObject* allocate_message(obj* self, PyObject* args)
    {
      PyObject* o = PyObject_CallObject(ampspy::message::message_type, NULL);

      return o;
    }

// callback function for AMPS messages
//
// Each client has a single Message object we use for reading and
// callbacks, so we don't need to initialize a new python object
// each time. The void pointer points to a callback_info structure
// that contains a pointer to the client, and a pointer to the
// python callable we should call.
//
// In this function, we just make sure the python Message object
// points to the AMPS::Message that was passed in, and then
// we invoke the user callback with the pre-built tuple argument.
    void callback_message(const Message& message, void* vp)
    {
      // most likely messageObject already points to &message based on the way
      // the C++ client works, but we do make a new one on reconnect.
      callback_info* ci = (callback_info*)vp;
      assert(ci);
      LOCKGIL;
      obj* pClient = ci->getClient();
      if (!pClient || !(ci->getHandler()) || !(pClient->message) ||
          !(pClient->message_args))
      {
        return;
      }
      //  message_args is a tuple object around message.
      //    see the line that looks like this:
      //      self->message_args = Py_BuildValue("(O)", self->message);
      //    above.
      pClient->message->pMessage = (Message*)&message;
      PyObject* result = PyObject_Call(ci->getHandler(), pClient->message_args,
                                       (PyObject*)NULL);
      if (result == NULL)
      {
        if (PyErr_ExceptionMatches(PyExc_SystemExit))
        {
          ampspy::unhandled_exception();
        }
        else
        {
          // translate amps py exception into amps cpp, throw
          exc::throwError();
        }
      }
      else
      {
        Py_DECREF(result);
      }
    }

    static AMPS::MessageHandler createMessageHandler(obj* self, PyObject* handler)
    {
      if (cmessagehandler::isCHandler(handler))
      {
        return cmessagehandler::getMessageHandler(handler);
      }
      else
      {
        callback_info* ci = new callback_info(self, handler);
        {
          UNLOCKGIL;
          ((AMPS::Client*)(self->pClient))->deferredExecution(callback_info::add, ci);
        }
        AMPS::Lock<SimpleMutex> l(_createdHandlersLock);
        _createdHandlers.insert((void*)ci);
        return AMPS::MessageHandler(&callback_message, ci);
      }
    }

    AMPSDLL void* copy_route(void* vpCbInfo_)
    {
      // The GIL should not be locked entering this function
      // If it's not one created here, don't copy it
      if (!vpCbInfo_)
      {
        return NULL;
      }
      else
      {
        AMPS::Lock<SimpleMutex> l(_createdHandlersLock);
        if (!_createdHandlers.count(vpCbInfo_))
        {
          return NULL;
        }
      }
      callback_info* pCbInfo = (callback_info*)vpCbInfo_;
      callback_info* retVal = 0;
      {
        LOCKGIL;
        retVal = new callback_info(pCbInfo->getClient(),
                                   pCbInfo->getHandler());
      }
      ((AMPS::Client*)pCbInfo->getClient()->pClient)->deferredExecution(
        callback_info::add, retVal);
      AMPS::Lock<SimpleMutex> l(_createdHandlersLock);
      _createdHandlers.insert((void*)retVal);
      return (void*)retVal;
    }

    AMPSDLL void remove_route(void* vpData_)
    {
      // The GIL should not be locked entering this function
      // If it's not one created here, don't do anything
      if (!vpData_)
      {
        return;
      }
      else
      {
        AMPS::Lock<SimpleMutex> l(_createdHandlersLock);
        if (!_createdHandlers.erase(vpData_))
        {
          return;
        }
      }
      callback_info* pInfo = (callback_info*)vpData_;
      obj* pClientObj = pInfo->getClient();
      if (!pInfo->getHandler() || !pClientObj ||
          !((AMPS::Client*)pClientObj->pClient) ||
          !((AMPS::Client*)pClientObj->pClient)->isValid())
      {
        callback_info::destroy(vpData_);
        return;
      }
      ((AMPS::Client*)pClientObj->pClient)->deferredExecution(callback_info::destroy,
          vpData_);
    }

    static bool isCallback(PyObject* handler)
    {
      if (handler)
      {
        return cmessagehandler::isCHandler(handler) || PyCallable_Check(handler);
      }
      return false;
    }
//    def send(self, message, message_handler=None, timeout=None):
    static PyObject* send(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "message", "message_handler", "timeout", NULL };
      ampspy::message::obj* message;
      PyObject* handler = NULL;
      int timeout = 0;

      if (!PyArg_ParseTupleAndKeywords(args, kw, "O!|Oi", (char**)kwlist,
                                       ampspy::message::message_type.pPyObject(),
                                       &message, &handler, &timeout))
      {
        return NULL;
      }
      if (isCallback(handler))
      {
        AMPS::MessageHandler messageHandler =
          createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->send(messageHandler,
                                                                  *(message->pMessage),
                                                                  timeout));
      }
      else
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->send(*(message->pMessage)));
      }
    }

//    def add_message_handler(self, command_id, message_handler, requested_acks,
    //is_subscribe):
    static PyObject* add_message_handler(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "command_id", "message_handler",
                                      "requested_acks", "is_subscribe", NULL
                                    };
      const char* cmd_id = NULL;
      PyObject* handler = NULL;
      const char* acks = NULL;
      int isSubscribe = 0;
      if (!PyArg_ParseTupleAndKeywords(args, kw, "sOsi", (char**)kwlist, &cmd_id,
                                       &handler, &acks, &isSubscribe))
      {
        return NULL;
      }
      unsigned ackType = 0;
      for (const char* current = acks; current != NULL;
           current = strchr(current, ','))
      {
        // Advance after the , if on one, make sure still valid
        if (*current == ',' && *(++current) == '\0')
        {
          break;
        }
        switch (current[1])
        {
        case 'e': //AckTypeConstants<0>::Lengths[Message::AckType::Received]:
          if (current[0] == 'r')
          {
            ackType |= Message::AckType::Received;
          }
          else if (current[0] == 'p')
          {
            ackType |= Message::AckType::Persisted;
          }
          break;
        case 'a':
          ackType |= Message::AckType::Parsed;
          break;
        case 'r':
          ackType |= Message::AckType::Processed;
          break;
        case 'o':
          ackType |= Message::AckType::Completed;
          break;
        case 't':
          ackType |= Message::AckType::Stats;
          break;
        default:
          break;
        }
      }
      AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->addMessageHandler(cmd_id,
                                                                           msgHandler,
                                                                           ackType,
                                                                           isSubscribe != 0));
    }

//    def remove_message_handler(self, command_id)
    static PyObject* remove_message_handler(obj* self, PyObject* args)
    {
      const char* cmd_id = NULL;
      if (!PyArg_ParseTuple(args, "s", &cmd_id))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->removeMessageHandler(
                         cmd_id));
    }

//    def bookmarkSubscribe(self, on_message, topic, bookmark, filter=None,
    //sub_id=None, options=None, timeout=0):
    static PyObject* bookmark_subscribe(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = {"on_message", "topic", "bookmark", "filter", "sub_id", "options", "timeout", NULL};
      static const char* kwlist_2[] = {"topic", "bookmark", "filter", "sub_id", "options", "timeout", NULL};
      const char* topic = NULL, *filter = NULL, *bookmark = NULL, *sub_id = NULL,
                  *options = NULL;
      int timeout = 0;
      PyObject* handler;
      if (messageHandlerSupplied(args, kw))
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Oss|zssi", (char**)kwlist,
                                         &handler, &topic, &bookmark, &filter,
                                         &sub_id, &options, &timeout))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->bookmarkSubscribe(
                             msgHandler,
                             topic, timeout, bookmark, filter ? filter : "",
                             options ? options : "", sub_id ? sub_id : ""));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "ss|zssi", (char**)kwlist_2,
                                         &topic, &bookmark, &filter, &sub_id,
                                         &options, &timeout))
        {
          return NULL;
        }
        AMPSPyReference<ampspy::messagestream::obj> messageStream = createMessageStream(
              self, self->pClient, false, false);
        Command command("subscribe");
        command.setTopic(topic).setBookmark(bookmark).setTimeout(timeout);
        if (filter)
        {
          command.setFilter(filter);
        }
        if (options)
        {
          command.setOptions(options);
        }
        if (sub_id)
        {
          command.setSubId(sub_id);
        }
        CALL_AND_CAPTURE_RETURN_VALUE(((AMPS::Client*)(
                                         self->pClient))->executeAsyncNoResubscribe(
                                        command,
                                        messageStream->messageHandler()),
                                      messageStream->commandId());
        if (messageStream->commandId().empty())
        {
          messageStream.release();
          return (PyObject*)createNoopMessageStream();
        }
        else if (sub_id)
        {
          messageStream->subId() = sub_id;
        }
        return messageStream.release();
      }
    }

    static std::string optionsFor(const char* userOptions_, PyObject* oofEnabled_,
                                  PyObject* sendEmpties_ = NULL)
    {
      std::ostringstream optsOstr;
      if (oofEnabled_ && PyObject_IsTrue(oofEnabled_) == 1)
      {
        optsOstr << "oof";
      }
      if (sendEmpties_ && PyObject_IsTrue(sendEmpties_) == 0)
      {
        if (optsOstr.tellp() > 0)
        {
          optsOstr << ",";
        }
        optsOstr << "no_empties";
      }
      if (userOptions_)
      {
        if (optsOstr.tellp() > 0)
        {
          optsOstr << ",";
        }
        optsOstr << userOptions_;
      }
      return optsOstr.str();

    }

//def sowAndDeltaSubscribe(self, on_message, topic, filter=None,
//                        batch_size=10, oof_enabled=False, send_empties=False,
//                       timeout=0, top_n=AMPS_DEFAULT_TOP_N, order_by="",
//                       options=""):
    static PyObject* sow_and_delta_subscribe(obj* self, PyObject* args,
        PyObject* kw)
    {
      static const char* kwlist[] = {"on_message", "topic", "filter", "batch_size", "oof_enabled", "send_empties", "timeout", "top_n", "order_by", "options", NULL};
      static const char* kwlist_2[] = {"topic", "filter", "batch_size", "oof_enabled", "send_empties", "timeout", "top_n", "order_by", "options", NULL};
      const char* topic = NULL, *filter = NULL;
      const char* orderBy = NULL;
      const char* options = NULL;
      PyObject* oofEnabled = Py_None, *sendEmpties = Py_None;
      int batch_size = 10, timeout = 0, topN = AMPS_DEFAULT_TOP_N;
      if (messageHandlerSupplied(args, kw))
      {
        PyObject* handler;
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Os|ziOOiizz", (char**)kwlist,
                                         &handler, &topic, &filter, &batch_size,
                                         &oofEnabled, &sendEmpties,
                                         &timeout, &topN, &orderBy, &options))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->sowAndDeltaSubscribe(
                             msgHandler,
                             topic, filter ? filter : "", orderBy ? orderBy : "",
                             batch_size, topN,
                             optionsFor(options, oofEnabled, sendEmpties), timeout));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ziOOiizz", (char**)kwlist_2,
                                         &topic, &filter, &batch_size, &oofEnabled,
                                         &sendEmpties, &timeout, &topN, &orderBy,
                                         &options))
        {
          return NULL;
        }
        AMPSPyReference<ampspy::messagestream::obj> messageStream = createMessageStream(
              self, self->pClient, false, false);
        Command command("sow_and_delta_subscribe");
        command.setTopic(topic).setBatchSize(batch_size).setTimeout(timeout);
        if (filter)
        {
          command.setFilter(filter);
        }
        std::string optionsStr = optionsFor(options, oofEnabled, sendEmpties);
        if (optionsStr.length())
        {
          command.setOptions(optionsStr);
        }
        if (orderBy)
        {
          command.setOrderBy(orderBy);
        }
        if (topN > 0)
        {
          command.setTopN(topN);
        }
        CALL_AND_CAPTURE_RETURN_VALUE(((AMPS::Client*)(
                                         self->pClient))->executeAsyncNoResubscribe(
                                        command,
                                        messageStream->messageHandler()),
                                      messageStream->commandId());
        if (messageStream->commandId().empty())
        {
          messageStream.release();
          return (PyObject*)createNoopMessageStream();
        }
        return messageStream.release();
      }

    }

//    def sow_and_subscribe(self, on_message, topic, filter, batch_size=10,
    //batch_size=10, oof_enabled=False,
    //timeout=0, top_n = AMPS_DEFAULT_TOP_N,
    //order_by="", bookmark="", options=""):
//    def sowAndSubscribe(self, on_message, topic, filter,
    //batch_size=10, oof_enabled=False,
    //timeout=0, top_n = AMPS_DEFAULT_TOP_N,
    //order_by="", bookmark="", options=""):
    static PyObject* sow_and_subscribe(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = {"on_message", "topic", "filter", "batch_size", "oof_enabled", "timeout", "top_n", "order_by", "bookmark", "options", NULL};
      static const char* kwlist_2[] = {"topic", "filter", "batch_size", "oof_enabled", "timeout", "top_n", "order_by", "bookmark", "options", NULL};
      const char* topic = NULL, *filter = NULL;
      const char* orderBy = NULL;
      const char* bookmark = NULL;
      const char* options = NULL;
      int batch_size = 10, timeout = 0, topN = AMPS_DEFAULT_TOP_N;
      PyObject* oof_enabled = Py_None;
      if (messageHandlerSupplied(args, kw))
      {
        PyObject* handler;
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Os|ziOiizzz", (char**)kwlist,
                                         &handler, &topic, &filter, &batch_size,
                                         &oof_enabled, &timeout, &topN, &orderBy,
                                         &bookmark, &options))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->sowAndSubscribe(msgHandler,
                           topic, filter ? filter : "", orderBy ? orderBy : "", bookmark ? bookmark : "",
                           batch_size, topN, optionsFor(options, oof_enabled), timeout));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ziOiizzz",
                                         (char**)kwlist_2, &topic, &filter,
                                         &batch_size, &oof_enabled, &timeout,
                                         &topN, &orderBy, &bookmark, &options))
        {
          return NULL;
        }
        AMPSPyReference<ampspy::messagestream::obj> messageStream = createMessageStream(
              self, self->pClient, false, false);
        Command command("sow_and_subscribe");
        command.setTopic(topic).setBatchSize(batch_size).setTimeout(timeout);
        if (filter)
        {
          command.setFilter(filter);
        }
        std::string optionsStr = optionsFor(options, oof_enabled);
        if (optionsStr.length())
        {
          command.setOptions(optionsStr);
        }
        if (orderBy)
        {
          command.setOrderBy(orderBy);
        }
        if (bookmark)
        {
          command.setBookmark(bookmark);
        }
        if (topN > 0)
        {
          command.setTopN(topN);
        }
        CALL_AND_CAPTURE_RETURN_VALUE(((AMPS::Client*)(
                                         self->pClient))->executeAsyncNoResubscribe(
                                        command,
                                        messageStream->messageHandler()),
                                      messageStream->commandId());
        if (messageStream->commandId().empty())
        {
          messageStream.release();
          return (PyObject*)createNoopMessageStream();
        }
        return messageStream.release();
      }
    }

//    def sow(self, on_message, topic, filter, batch_size=10, timeout=0, top_n=AMPS_DEFAULT_TOP_N, order_by=None, bookmark=None, options=None):
    static PyObject* sow(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = {"on_message", "topic", "filter", "batch_size", "timeout", "top_n", "order_by", "bookmark", "options", NULL};
      static const char* kwlist_2[] = {"topic", "filter", "batch_size", "timeout", "top_n", "order_by", "bookmark", "options", NULL};
      const char* topic = NULL, *filter = NULL;
      const char* orderBy = NULL;
      const char* bookmark = NULL;
      const char* options = NULL;
      int batch_size = 10, timeout = 0, topN = AMPS_DEFAULT_TOP_N;
      PyObject* handler = NULL;
      if (messageHandlerSupplied(args, kw))
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Os|ziiizzz", (char**)kwlist,
                                         &handler, &topic, &filter, &batch_size,
                                         &timeout, &topN, &orderBy, &bookmark,
                                         &options))
        {
          return NULL;
        }
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ziiizzz", (char**)kwlist_2,
                                         &topic, &filter, &batch_size, &timeout,
                                         &topN, &orderBy, &bookmark, &options))
        {
          return NULL;
        }
      }
      if (handler == NULL)
      {
        AMPSPyReference<ampspy::messagestream::obj > messagestream =
          createMessageStream(self, self->pClient, true, false, false);
        AMPS::Command cmd("sow");
        cmd.setTopic(topic).setBatchSize(batch_size);
        if (filter)
        {
          cmd.setFilter(filter);
        }
        if (orderBy)
        {
          cmd.setOrderBy(orderBy);
        }
        if (bookmark)
        {
          cmd.setBookmark(bookmark);
        }
        if (topN != AMPS_DEFAULT_TOP_N)
        {
          cmd.setTopN(topN);
        }
        if (options)
        {
          cmd.setOptions(options);
        }
        if (timeout)
        {
          cmd.setTimeout(timeout);
        }
        cmd.addAckType("completed");
        CALL_AND_CAPTURE_RETURN_VALUE(((AMPS::Client*)(self->pClient))->executeAsync(
                                        cmd, messagestream->messageHandler()),
                                        messagestream->commandId());

        return messagestream.release();
      }
      else
      {
        AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->sow(msgHandler,
                           topic, filter ? filter : "", orderBy ? orderBy : "",
                           bookmark ? bookmark : "", batch_size, topN,
                           options ? options : "", timeout));
      }
    }
//    def subscribe(self, on_message, topic, filter=None, options=None, timeout=0, sub_id=None):
    static PyObject* subscribe(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "on_message", "topic", "filter", "options", "timeout", "sub_id", NULL };
      static const char* kwlist_2[] = { "topic", "filter", "options", "timeout", "sub_id", NULL };
      const char* topic = NULL, *filter = NULL, *options = NULL, *sub_id = NULL;
      int timeout = 0;
      if (messageHandlerSupplied(args, kw))
      {
        PyObject* handler;
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Os|zsis", (char**)kwlist,
                                         &handler, &topic, &filter, &options,
                                         &timeout, &sub_id))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->subscribe(msgHandler,
                                                                       topic, timeout,
                                                                       filter ? filter : "",
                                                                       options ? options : "",
                                                                       sub_id ? sub_id : ""));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "s|zsis", (char**)kwlist_2,
                                         &topic, &filter, &options,
                                         &timeout, &sub_id))
        {
          return NULL;
        }
        AMPSPyReference<ampspy::messagestream::obj> messageStream = createMessageStream(
              self, self->pClient, false, false);
        Command command("subscribe");
        command.setTopic(topic).setTimeout(timeout);
        if (filter)
        {
          command.setFilter(filter);
        }
        if (options)
        {
          command.setOptions(options);
        }
        if (sub_id)
        {
          command.setSubId(sub_id);
        }
        CALL_AND_CAPTURE_RETURN_VALUE(((AMPS::Client*)(
                                         self->pClient))->executeAsyncNoResubscribe(
                                        command,
                                        messageStream->messageHandler()),
                                      messageStream->commandId());
        if (messageStream->commandId().empty())
        {
          messageStream.release();
          return (PyObject*)createNoopMessageStream();
        }
        else if (sub_id)
        {
          messageStream->subId() = sub_id;
        }
        return messageStream.release();
      }
    }

//    def deltaSubscribe(self, on_message, topic, filter=None, options=0, timeout=0):
//    def delta_subscribe(self, on_message, topic, filter=None, options=0, timeout=0):
    static PyObject* delta_subscribe(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "on_message", "topic", "filter", "options", "timeout", "sub_id", NULL };
      static const char* kwlist_2[] = { "topic", "filter", "options", "timeout", "sub_id", NULL };
      const char* topic = NULL, *filter = NULL, *options = NULL, *sub_id = NULL;
      int timeout = 0;
      if (messageHandlerSupplied(args, kw))
      {
        PyObject* handler;
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Os|zsis", (char**)kwlist,
                                         &handler, &topic, &filter, &options,
                                         &timeout, &sub_id))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->deltaSubscribe(msgHandler,
                           topic, timeout, filter ? filter : "",
                           options ? options : "", sub_id ? sub_id : ""));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "s|zsis", (char**)kwlist_2,
                                         &topic, &filter, &options,
                                         &timeout, &sub_id))
        {
          return NULL;
        }
        AMPSPyReference<ampspy::messagestream::obj> messageStream = createMessageStream(
              self, self->pClient, false, false);
        Command command("delta_subscribe");
        command.setTopic(topic).setTimeout(timeout);
        if (filter)
        {
          command.setFilter(filter);
        }
        if (options)
        {
          command.setOptions(options);
        }
        if (sub_id)
        {
          command.setSubId(sub_id);
        }
        CALL_AND_CAPTURE_RETURN_VALUE(((AMPS::Client*)(
                                         self->pClient))->executeAsyncNoResubscribe(
                                        command,
                                        messageStream->messageHandler()),
                                      messageStream->commandId());
        if (messageStream->commandId().empty())
        {
          messageStream.release();
          return (PyObject*)createNoopMessageStream();
        }
        else if (sub_id)
        {
          messageStream->subId() = sub_id;
        }
        return messageStream.release();
      }
    }


//    def sowDelete(self, on_message, topic, filter=None, options=0, timeout=0):
//    def sow_delete(self, on_message, topic, filter=None, options=0, timeout=0):
    static PyObject* sow_delete(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "on_message", "topic", "filter", "timeout", NULL };
      static const char* kwlist_2[] = { "topic", "filter", "timeout", NULL };
      const char* topic, *filter_ = "";
      int timeout_ = 0;
      PyObject* handler;
      if (messageHandlerSupplied(args, kw))
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Oss|i", (char**)kwlist,
                                         &handler, &topic, &filter_, &timeout_))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->sowDelete(msgHandler,
                                                                       topic,
                                                                       filter_,
                                                                       timeout_));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "ss|i", (char**)kwlist_2,
                                         &topic, &filter_, &timeout_))
        {
          return NULL;
        }
        try
        {
          AMPS::Message resultMessage;
          {
            UNLOCKGIL;
            resultMessage = ((AMPS::Client*)(self->pClient))->sowDelete(topic,
                                                                       filter_,
                                                                       timeout_);
          }
          message::obj* message = (message::obj*)allocate_message(self, NULL);
          message::setCppMessage(message, resultMessage);
          return (PyObject*)message;
        } DISPATCH_EXCEPTION
      }
    }

//    def sowDelete(self, on_message, topic, filter=None, options=0, timeout=0):
//    def sow_delete(self, on_message, topic, filter=None, options=0, timeout=0):
    static PyObject* sow_delete_by_keys(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "on_message", "topic", "keys", "timeout", NULL };
      static const char* kwlist_2[] = {"topic", "keys", "timeout", NULL };
      const char* topic, *keys = "";
      int timeout_ = 0;
      PyObject* on_message;
      if (messageHandlerSupplied(args, kw))
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Oss|i", (char**)kwlist,
                                         &on_message, &topic, &keys, &timeout_))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, on_message);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->sowDeleteByKeys(msgHandler,
                                                                             topic,
                                                                             keys,
                                                                             timeout_));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "s|si", (char**)kwlist_2,
                                         &topic, &keys, &timeout_))
        {
          return NULL;
        }
        try
        {
          AMPS::Message resultMessage;
          {
            UNLOCKGIL;
            resultMessage = ((AMPS::Client*)(self->pClient))->sowDeleteByKeys(topic,
                                                                              keys,
                                                                              timeout_);
          }
          message::obj* message = (message::obj*)allocate_message(self, NULL);
          message::setCppMessage(message, resultMessage);
          return (PyObject*)message;
        }
        DISPATCH_EXCEPTION
      }
    }

//    def sowDelete(self, on_message, topic, data, options=0, timeout=0):
//    def sow_delete(self, on_message, topic, data, options=0, timeout=0):
    static PyObject* sow_delete_by_data(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "on_message", "topic", "data", "timeout", NULL };
      static const char* kwlist_2[] = {"topic", "data", "timeout", NULL };
      const char* topic, *data = "";
      Py_ssize_t dataLen = 0;
      int timeout_ = 0;
      if (messageHandlerSupplied(args, kw))
      {
        PyObject* on_message;
        if (!PyArg_ParseTupleAndKeywords(args, kw, "Oss#|i", (char**)kwlist,
                                         &on_message, &topic, &data, &dataLen,
                                         &timeout_))
        {
          return NULL;
        }
        AMPS::MessageHandler msgHandler = createMessageHandler(self, on_message);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->sowDeleteByData(msgHandler,
                                                                             topic,
                                                                             std::string(data, dataLen),
                                                                             timeout_));
      }
      else
      {
        if (!PyArg_ParseTupleAndKeywords(args, kw, "ss#|i", (char**)kwlist_2,
                                         &topic, &data, &dataLen, &timeout_))
        {
          return NULL;
        }
        try
        {
          AMPS::Message resultMessage;
          {
            UNLOCKGIL;
            resultMessage = ((AMPS::Client*)(self->pClient))->sowDeleteByData(topic,
                            std::string(data, dataLen), timeout_);
          }
          message::obj* message = (message::obj*)allocate_message(self, NULL);
          message::setCppMessage(message, resultMessage);
          return (PyObject*) message;
        } DISPATCH_EXCEPTION
      }
    }

//    def set_heartbeat(self, interval_seconds, timeout_seconds=None):
    static PyObject* set_heartbeat(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "interval_seconds", "timeout_seconds", NULL };
      int interval_seconds = 0, timeout_seconds = -1;
      if (!PyArg_ParseTupleAndKeywords(args, kw, "i|i", (char**)kwlist,
                                       &interval_seconds, &timeout_seconds))
      {
        return NULL;
      }
      if (timeout_seconds == -1)
      {
        timeout_seconds = interval_seconds * 2;
      }

      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setHeartbeat(
                         interval_seconds, timeout_seconds));
    }

//    Deprecated
//    def start_timer(self)
    static PyObject* start_timer(obj* self, PyObject* args)
    {
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->startTimer());
    }

//    Deprecated
//    def stop_timer(self)
    static PyObject* stop_timer(obj* self, PyObject* args)
    {
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (isCallback(callable))
      {
        AMPS::MessageHandler msgHandler = createMessageHandler(self, callable);
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->stopTimer(msgHandler));
      }
      else
      {
        PyErr_SetString(PyExc_TypeError, "argument to stop_timer must be callable.");
        return NULL;
      }
    }

    void
    call_disconnect_handler(Client& cli, void* vp)
    {
      LOCKGIL;
      obj* c = (obj*) vp;

      PyObject* args = Py_BuildValue("(O)", c);
      Py_XDECREF(PyObject_Call(c->disconnectHandler, args, (PyObject*)NULL));
      Py_DECREF(args);
      if (PyErr_Occurred())
      {
        if (PyErr_ExceptionMatches(PyExc_SystemExit))
        {
          ampspy::unhandled_exception();
        }
        throw AMPSException("The disconnect handler threw an exception",
                            AMPS_E_CONNECTION);
      }
    }

//    def set_disconnect_handler(self, client_disconnect_handler):
//    def setDisconnectHandler(self, client_disconnect_handler):
    static PyObject* set_disconnect_handler(obj* self, PyObject* args)
    {
      Client& client = *(self->pClient);
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (!PyCallable_Check(callable) && callable != Py_None)
      {
        PyErr_SetString(PyExc_TypeError, "argument must be callable.");
        return NULL;
      }
      if (self->disconnectHandler)
      {
        Py_DECREF(self->disconnectHandler);
      }
      if (callable == Py_None)
      {
        self->disconnectHandler = NULL;
        AMPS::DisconnectHandler no_handler;
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setDisconnectHandler(
                           no_handler));
      }
      else
      {
        Py_INCREF(callable);
        self->disconnectHandler = callable;
        CALL_RETURN_NONE(client.setDisconnectHandler(AMPS::DisconnectHandler(
                           call_disconnect_handler, self)));
      }
    }
//    def set_unhandled_message_handler(self, message_handler):
//    def setUnhandledMessageHandler(self, message_handler):
    static PyObject* set_last_chance_message_handler(obj* self, PyObject* args)
    {
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (isCallback(callable))
      {
        AMPS::MessageHandler msgHandler = createMessageHandler(self, callable);
        CALL_RETURN_NONE(
          ((AMPS::Client*)(self->pClient))->setLastChanceMessageHandler(msgHandler));
      }
      else
      {
        if (callable == Py_None)
        {
          AMPS::MessageHandler no_handler;
          CALL_RETURN_NONE(
            ((AMPS::Client*)(self->pClient))->setLastChanceMessageHandler(no_handler));
        }
        else
        {
          PyErr_SetString(PyExc_TypeError, "argument must be callable.");
          return NULL;
        }
      }
    }

// def set_duplicate_message_handler(self, message_handler):
// def setDuplicateMessageHandler(self, message_handler):
    static PyObject* set_duplicate_message_handler(obj* self, PyObject* args)
    {
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (isCallback(callable))
      {
        AMPS::MessageHandler msgHandler = createMessageHandler(self, callable);
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setDuplicateMessageHandler(
                           msgHandler));
      }
      else
      {
        if (callable == Py_None)
        {
          AMPS::MessageHandler no_handler;
          CALL_RETURN_NONE(
            ((AMPS::Client*)(self->pClient))->setDuplicateMessageHandler(no_handler));
        }
        PyErr_SetString(PyExc_TypeError, "argument must be callable.");
        return NULL;
      }
    }

    static PyObject* get_duplicate_message_handler(obj* self, PyObject* args)
    {
      AMPS::MessageHandler handler = ((AMPS::Client*)(
                                        self->pClient))->getDuplicateMessageHandler();
      if (handler.function() == callback_message)
      {
        callback_info* pCallbackInfo =
          reinterpret_cast<callback_info*>(handler.userData());
        if (pCallbackInfo)
        {
          PyObject* handler = pCallbackInfo->getHandler();
          if (handler)
          {
            Py_INCREF(handler);
            return handler;
          }
        }
      }
      NONE;
    }

//    def set_exception_listener(self, exception_listener):
//    def setExceptionListener(self, exception_listener):
    static PyObject* set_exception_listener(obj* self, PyObject* args)
    {
      PyObject* callable;
      if (!PyArg_ParseTuple(args, "O", &callable))
      {
        return NULL;
      }
      if (!PyCallable_Check(callable) && callable != Py_None)
      {
        PyErr_SetString(PyExc_TypeError, "argument must be callable.");
        return NULL;
      }
      if (callable == Py_None)
      {
        self->exceptionHandler = std::make_shared<PyExceptionListener>();
      }
      else
      {
        self->exceptionHandler = std::make_shared<PyExceptionListener>(callable);
      }
      CALL_RETURN_NONE(
        ((AMPS::Client*)(self->pClient))->setExceptionListener( self->exceptionHandler )
      );
    }

    static PyObject* get_exception_listener(obj* self, PyObject* args)
    {
      if (self->exceptionHandler)
      {
        PyObject* object = (PyObject*) ((PyExceptionListener*)(
                                          self->exceptionHandler.get()))->callable();
        if (object)
        {
          Py_INCREF(object);
          return object;
        }
      }
      NONE;
    }

// def publish_flush(self, timeout=0):
    static PyObject* publish_flush(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "timeout", "ack_type", NULL };
      long timeout = 0;
      unsigned long ackType = AMPS::Message::AckType::Processed;
      if (!PyArg_ParseTupleAndKeywords(args, kw, "|lk", (char**)kwlist, &timeout,
                                       &ackType))
      {
        return NULL;
      }
      CALL_RETURN_NONE(
        ((AMPS::Client*)(self->pClient))->publishFlush(timeout, ackType)
      );
    }

    static size_t _getUnpersistedCount(AMPS::Client& client)
    {
      Store store = client.getPublishStore();
      if (store.isValid())
      {
        return store.unpersistedCount();
      }
      else
      {
        return 0;
      }
    }

    static PyObject* get_unpersisted_count(obj* self, PyObject* args)
    {
      AMPS::Client& client = *(AMPS::Client*)(self->pClient);
      // Want to unlock GIL for all client calls and have exception safety
      CALL_RETURN_SIZE_T(_getUnpersistedCount(client));
    }

    static PyObject* get_error_on_publish_gap(obj* self, PyObject* args)
    {
      CALL_RETURN_BOOL(((AMPS::Client*)(
                          self->pClient))->getPublishStore().getErrorOnPublishGap());
    }

    static PyObject* set_error_on_publish_gap(obj* self, PyObject* args)
    {
      PyObject* value = NULL;
      if (!PyArg_ParseTuple(args, "O!", &PyBool_Type, &value))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(
                          self->pClient))->getPublishStore().setErrorOnPublishGap(value == Py_True));
    }

    static PyObject* set_bookmark_store(obj* self, PyObject* args)
    {
      PyObject* pBookmarkStore;
      if (!PyArg_ParseTuple(args, "O", &pBookmarkStore))
      {
        return NULL;
      }

      if (pBookmarkStore == Py_None)
      {
        // Unset the bookmark store.
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setBookmarkStore(
                           BookmarkStore()));
      }
      else if (ampspy::mmapbookmarkstore::mmapbookmarkstore_type.isInstanceOf(
                 pBookmarkStore))
      {
        // A C++ bookmark store implementation; set it directly.
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setBookmarkStore(*((
                           ampspy::mmapbookmarkstore::obj*)pBookmarkStore)->impl));
      }
      else if (ampspy::memorybookmarkstore::memorybookmarkstore_type.isInstanceOf(
                 pBookmarkStore))
      {
        // A C++ bookmark store implementation; set it directly.
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setBookmarkStore(*((
                           ampspy::memorybookmarkstore::obj*)pBookmarkStore)->impl));
      }
      else
      {
        // Assume this is a python object that implements the required bookmark
        // store methods. If it does not, the first missing method will result in
        // an exception.
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setBookmarkStore(
                           new ampspy::bookmarkstore::wrapper(pBookmarkStore)));
      }
    }

    static PyObject* set_publish_store(obj* self, PyObject* args)
    {
      PyObject* store;
      if (!PyArg_ParseTuple(args, "O", &store))
      {
        return NULL;
      }
      if (ampspy::publishstore::publishstore_type.isInstanceOf(store))
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setPublishStore(((
                           ampspy::publishstore::obj*)store)->impl));
      }
      else if (ampspy::memorypublishstore::memorypublishstore_type.isInstanceOf(store)
               || ampspy::hybridpublishstore::hybridpublishstore_type.isInstanceOf(store))
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setPublishStore(*((
                           ampspy::memorypublishstore::obj*)store)->impl));
      }
      else if (store == Py_None)
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setPublishStore(Store()));
      }
      else
      {
        PyErr_SetString(PyExc_TypeError,
                        "argument must be one of AMPS.PublishStore, AMPS.MemoryPublishStore, AMPS.HybridPublishStore, or None.");
        return NULL;
      }
    }

    static PyObject* set_failed_write_handler(obj* self, PyObject* args)
    {
      PyObject* handler = NULL;
      if (!PyArg_ParseTuple(args, "O", &handler))
      {
        return NULL;
      }

      if (handler == Py_None)
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setFailedWriteHandler(NULL));
      }
      else
      {
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setFailedWriteHandler(
                           new PyFailedWriteHandler(handler)));
      }
    }

    static PyObject* execute_async(obj* self, PyObject* args, PyObject* kw)
    {
      static const char* kwlist[] = { "command", "on_message", NULL };
      PyObject* on_message = NULL;
      command::obj* command;

      if (!PyArg_ParseTupleAndKeywords(args, kw, "O!|O", (char**)kwlist,
                                       command::command_type.pPyObject(), &command, &on_message))
      {
        return NULL;
      }
      if (on_message == NULL || on_message == Py_None)
      {
        CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->executeAsync(
                             command->command, AMPS::MessageHandler()));
      }

      if (!isCallback(on_message))
      {
        PyErr_SetString(PyExc_TypeError, "on_message must be callable");
        return NULL;
      }
      AMPS::MessageHandler msgHandler = createMessageHandler(self, on_message);
      CALL_RETURN_STRING(((AMPS::Client*)(self->pClient))->executeAsync(
                           command->command, msgHandler));
    }

    static PyObject* execute(obj* self, PyObject* args)
    {
      command::obj* pyCommand;
      if (!PyArg_ParseTuple(args, "O!", command::command_type.pPyObject(),
                            &pyCommand))
      {
        return NULL;
      }
      AMPS::Command& command = pyCommand->command;
      AMPS::Message& message = command.getMessage();
      const Message::Command::Type commandType = message.getCommandEnum();
      unsigned requestedAcks = message.getAckTypeEnum();
      // A Command returning no data and no acks needs an empty MessageStream
      if ((commandType & Message::Command::NoDataCommands)
          && (requestedAcks == Message::AckType::Persisted
              || requestedAcks == Message::AckType::None))
      {
        try
        {
          UnlockGIL unlockGuard;
          ((AMPS::Client*)(self->pClient))->executeAsync(command,
              AMPS::MessageHandler());
        } DISPATCH_EXCEPTION;
        return (PyObject*)createNoopMessageStream();
      }

      const bool isStats = command.hasStatsAck();
      const bool isSow = command.isSow();
      const bool sendCompleted = !isSow ||
                                 (requestedAcks & AMPS::Message::AckType::Completed);
      AMPSPyReference<messagestream::obj> messageStream = createMessageStream(self,
          self->pClient, isSow, isStats, sendCompleted);
      if (isSow)
      {
        if (!sendCompleted)
        {
          command.addAckType("completed");
        }
        if (requestedAcks)
        {
          messageStream->setAcksOnly(requestedAcks | AMPS::Message::AckType::Completed);
        }
      }
      else if (!command.isSubscribe())
      {
        messageStream->setAcksOnly( (commandType == Message::Command::Publish
                                     || commandType == Message::Command::DeltaPublish
                                     || commandType == Message::Command::SOWDelete)
                                    ? requestedAcks & ~Message::AckType::Persisted
                                    : requestedAcks);
      }

      CALL_AND_CAPTURE_RETURN_VALUE(
        ((AMPS::Client*)(self->pClient))->executeAsyncNoResubscribe(command,
            messageStream->messageHandler()),
        messageStream->commandId());
      if (command.isSubscribe())
      {
        if (messageStream->commandId().empty())
        {
          messageStream.release();
          return (PyObject*)createNoopMessageStream();
        }
        std::string subId = message.getSubscriptionId();
        if (subId != messageStream->commandId())
        {
          messageStream->subId() = subId;
        }
      }
      std::string queryId = message.getQueryID();
      if (!queryId.empty() && queryId != messageStream->commandId()
          && queryId != messageStream->subId())
      {
        messageStream->queryId() = queryId;
      }
      return messageStream.release();
    }

    void TransportFilter::connectionStateChanged(
      AMPS::ConnectionStateListener::State newState_)
    {
      if (newState_ == AMPS::ConnectionStateListener::Disconnected)
      {
        _remain = 0;
      }
    }

    void TransportFilter::filter(const unsigned char* data_, size_t len_,
                                 short direction_, void* vpThis_)
    {
      TransportFilter* pSelf = (TransportFilter*)vpThis_;
      try
      {
        LOCKGIL;
#if PY_MAJOR_VERSION >= 3
         PyObject* args = Py_BuildValue("(y#O)", data_, len_,
                                        (direction_ ? Py_True : Py_False));
#else
        PyObject* args = Py_BuildValue("(s#O)", data_, len_,
                                       (direction_ ? Py_True : Py_False));
#endif
        Py_XDECREF(PyObject_CallObject(pSelf->_handler, args));
        Py_DECREF(args);
      }
      catch (...) { } // -V565 this is a C callback function, so exceptions must not bubble up.
    }
#if PY_MAJOR_VERSION >= 3 || (PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION >= 7)
    void TransportFilter::filterModifiable(const unsigned char* data_, size_t len_,
                                           short direction_, void* vpThis_)
    {
      TransportFilter* pSelf = (TransportFilter*)vpThis_;
      // Break up the bytes into discrete messages
      size_t processed = 0;
      unsigned char* start = const_cast<unsigned char*>(data_);
      size_t length = len_;

      while (processed < length)
      {
        size_t sz = length;
        if (direction_)
        {
          if (pSelf->_remain)
          {
            start = (unsigned char*)(data_ - pSelf->_remain);
            length += pSelf->_remain;
            pSelf->_remain = (size_t)0;
          }
          if (length - processed < 4)
          {
            break;
          }
          unsigned int len = *(unsigned int*)start;
          sz = (size_t)ntohl(len);
          if (sz == 0)
          {
            break;
          }
          if (length - processed < 4 + sz)
          {
            break;
          }
          start = (unsigned char*)(start + 4);
          processed += 4;
        }
        try
        {
          LOCKGIL;
#if PY_MAJOR_VERSION >= 3
// PyBUF_WRITE currently not in limited API because it's in cpython/object.h, however, it is
// added to the stable API in 3.11 and has been stable since 2.6 and 3.0
#ifndef PyBUF_WRITE
#define PyBUF_WRITE 0x200
#endif
          PyObject* data = PyMemoryView_FromMemory((char*)start, (Py_ssize_t)sz,
                                                   PyBUF_WRITE);
          PyObject* args = Py_BuildValue("(OO)", data,
                                         (direction_ ? Py_True : Py_False));
          Py_XDECREF(PyObject_CallObject(pSelf->_handler, args));
          Py_DECREF(args);
#else
          Py_ssize_t shape[] = { (Py_ssize_t)sz };
          Py_buffer buf;
          buf.buf = start;
          buf.obj = NULL;
          buf.len = (Py_ssize_t) sz;
          buf.itemsize = 1;
          buf.readonly = 0;
          buf.ndim = 1;
          buf.format = NULL;
          buf.shape = shape;
          buf.strides = NULL;
          buf.suboffsets = NULL;
          buf.smalltable[0] = (Py_ssize_t)sz;
          buf.smalltable[1] = 1;
          buf.internal = NULL;
          PyObject* data = PyMemoryView_FromBuffer(&buf);
          PyObject* args = Py_BuildValue("(OO)", data,
                              (direction_ ? Py_True : Py_False));
          Py_XDECREF(PyObject_CallObject(pSelf->_handler, args));
          Py_DECREF(data);
          Py_DECREF(args);
#endif
        }
        catch (...) { } // -V565 this is a C callback function, so exceptions must not bubble up.
        processed += sz;
        start = (unsigned char*)(start + sz);
      }
      if (processed < length)
      {
        pSelf->_remain = length - processed;
      }
    }
#endif

    static PyObject* set_transport_filter(obj* self, PyObject* args)
    {
      PyObject* filterCallback = NULL;
      PyObject* modifiable = NULL;
      if (!PyArg_ParseTuple(args, "O|O!", &filterCallback, &PyBool_Type,
                            &modifiable))
      {
        return NULL;
      }
      if (filterCallback == Py_None)
      {
        // Note: set the filter back to NULL before losing a reference to it.
        {
          // seperate scopes due to CALL_AND_RETURN_ON_FAIL jump label reuse
          CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                     self->pClient))->setTransportFilterFunction(NULL,
                                                                                 0));
        }
        {
          CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                     self->pClient))->
                                      removeConnectionStateListener(self->transportFilter));
        }
        delete self->transportFilter;
        self->transportFilter = NULL;
      }
      else
      {
        if (!PyCallable_Check(filterCallback))
        {
          PyErr_SetString(PyExc_TypeError, "argument must be callable or None");
          return NULL;
        }

        TransportFilter* transportFilter = new TransportFilter(filterCallback);
#if PY_MAJOR_VERSION >= 3 || (PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION >= 7)
        // Replace the filter that we will use before losing the reference to
        // the old one.
        if (modifiable && modifiable == Py_True)
        {
          // safe to attempt to erase a non-existant key, but not NULL
          if (self->transportFilter)
          {
            CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                       self->pClient))->
                                        removeConnectionStateListener(self->transportFilter));
          }
          {
            // seperate scopes due to CALL_AND_RETURN_ON_FAIL jump label reuse
            CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                       self->pClient))->
                                        addConnectionStateListener(transportFilter));
          }
          {
            CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                       self->pClient))->
                                        setTransportFilterFunction(TransportFilter::filterModifiable,
                                                                   transportFilter));
          }
        }
        else
#endif
        {
          CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                     self->pClient))->
                                      setTransportFilterFunction(TransportFilter::filter,
                                                                 transportFilter));
        }
        delete self->transportFilter;
        self->transportFilter = transportFilter;
      }
      NONE;
    }

    static amps_result thread_created_callback(AMPS_THREAD_T, void* void_callable_)
    {
      PyObject* callable = (PyObject*)void_callable_;
      try
      {
        LOCKGIL;
        Py_XDECREF(PyObject_CallObject(callable, NULL));
        return AMPS_E_OK;
      }
      catch (...)
      {
        // this is a C callback function, so exceptions must not bubble up.
        return AMPS_E_RETRY;
      }
    }

    static PyObject* set_thread_created_callback(obj* self, PyObject* args)
    {
      PyObject* threadCreatedCallback = NULL;
      if (!PyArg_ParseTuple(args, "O", &threadCreatedCallback))
      {
        return NULL;
      }
      if (threadCreatedCallback == Py_None)
      {
        // Note: set the filter back to NULL before losing a reference to it.
        CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                   self->pClient))->setThreadCreatedCallback(NULL, 0));
        Py_XDECREF(self->threadCreatedCallback);
      }
      else
      {
        if (!PyCallable_Check(threadCreatedCallback))
        {
          PyErr_SetString(PyExc_TypeError, "argument must be callable or None");
          return NULL;
        }

        // Replace the filter that we will use before losing the reference to the old one.
        CALL_AND_RETURN_ON_FAIL(((AMPS::Client*)(
                                   self->pClient))->
                                    setThreadCreatedCallback(thread_created_callback,
                                                             threadCreatedCallback));
        Py_XDECREF(self->threadCreatedCallback);
        self->threadCreatedCallback = threadCreatedCallback;
        Py_INCREF(self->threadCreatedCallback);
      }
      NONE;
    }


    static PyObject* ack(obj* self, PyObject* args)
    {
      char* topic = NULL;
      char* bookmark = NULL;
      char* options = NULL;
      char* opts = NULL;
      Py_ssize_t topicLen = 0;
      Py_ssize_t bookmarkLen = 0;
      PyObject* message = NULL;

      if (PyArg_ParseTuple(args, "O|s", &message, &options) &&
          message->ob_type == message::message_type.pPyTypeObject())
      {
        AMPS::Message* pMessage = ((ampspy::message::obj*)message)->pMessage;
        if (pMessage)
        {
          CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->ack(*pMessage, options));
        }
        PyErr_SetString(PyExc_TypeError, "This Message is not acknowledgeable.");
        return NULL;
      }
      else if (PyArg_ParseTuple(args, "s#s#|s", &topic, &topicLen, &bookmark,
                                &bookmarkLen, &opts))
      {
        Message::Field topicField(topic, topicLen);
        Message::Field bookmarkField(bookmark, bookmarkLen);
        CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->ack(topicField,
                         bookmarkField, opts));
      }
      else
      {
        PyErr_SetString(PyExc_TypeError,
                        "argument must be AMPS.Message or topic and bookmark string.");
        return NULL;
      }

    }

    static PyObject* set_auto_ack(obj* self, PyObject* args)
    {
      PyObject* value = NULL;
      if (!PyArg_ParseTuple(args, "O!", &PyBool_Type, &value))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setAutoAck(
                         value == Py_True));
    }

    static PyObject* get_auto_ack(obj* self, PyObject* args)
    {
      CALL_RETURN_BOOL(((AMPS::Client*)(self->pClient))->getAutoAck());
    }

    static PyObject* set_ack_timeout(obj* self, PyObject* args)
    {
      unsigned long value = 0;
      if (!PyArg_ParseTuple(args, "k", &value))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setAckTimeout(value));
    }

    static PyObject* get_ack_timeout(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T(((AMPS::Client*)(self->pClient))->getAckTimeout());
    }

    static PyObject* set_retry_on_disconnect(obj* self, PyObject* args)
    {
      PyObject* value = NULL;
      if (!PyArg_ParseTuple(args, "O!", &PyBool_Type, &value))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setRetryOnDisconnect(
                         value == Py_True));
    }

    static PyObject* get_retry_on_disconnect(obj* self, PyObject* args)
    {
      CALL_RETURN_BOOL(((AMPS::Client*)(self->pClient))->getRetryOnDisconnect());
    }

    static PyObject* set_ack_batch_size(obj* self, PyObject* args)
    {
      unsigned long value = 0;
      if (!PyArg_ParseTuple(args, "k", &value))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setAckBatchSize(value));
    }

    static PyObject* get_ack_batch_size(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T(((AMPS::Client*)(self->pClient))->getAckBatchSize());
    }

    static PyObject* set_default_max_depth(obj* self, PyObject* args)
    {
      unsigned long value = 0;
      if (!PyArg_ParseTuple(args, "k", &value))
      {
        return NULL;
      }
      CALL_RETURN_NONE(((AMPS::Client*)(self->pClient))->setDefaultMaxDepth((
                         unsigned)value));
    }

    static PyObject* get_default_max_depth(obj* self, PyObject* args)
    {
      CALL_RETURN_SIZE_T(((AMPS::Client*)(self->pClient))->getDefaultMaxDepth());
    }

//    def set_global_command_type_message_handler(self, command, message_handler)
    static PyObject* set_global_command_type_message_handler(obj* self,
                                                             PyObject* args,
                                                             PyObject* kw)
    {
      static const char* kwlist[] = { "command", "message_handler", NULL};
      const char* cmd = NULL;
      PyObject* handler = NULL;
      if (!PyArg_ParseTupleAndKeywords(args, kw, "sO", (char**)kwlist, &cmd,
                                       &handler))
      {
        return NULL;
      }
      AMPS::MessageHandler msgHandler = createMessageHandler(self, handler);
      CALL_RETURN_NONE(((AMPS::Client*)(
                          self->pClient))->setGlobalCommandTypeMessageHandler(cmd,
                              msgHandler));
    }

#if PY_MAJOR_VERSION >= 3
//    def get_ssl(self)
    static PyObject* get_ssl(obj* self, PyObject* args)
    {
      _amps_SSL* ssl = NULL;
      {
        UNLOCKGIL;
        if (((AMPS::Client*)(self->pClient))->getURI().find("tcps") != std::string::npos)
        {
          ssl = (void*)(amps_tcps_get_SSL(amps_client_get_transport(((AMPS::Client*)(self->pClient))->getHandle())));
        }
      }
      return ampspy_get_PySSLSocket_from_SSL(ssl);
    }
#endif

    static PyObject* add_http_preflight_header(obj* self, PyObject* args)
    {
      const char* header = NULL;
      if (!PyArg_ParseTuple(args, "s", &header))
      {
        return NULL;
      }
      CALL_RETURN_SELF(((AMPS::Client*)self->pClient)->addHttpPreflightHeader(header));
    }

    static PyObject* add_http_preflight_header_key_value(obj* self, PyObject* args)
    {
      const char* key = NULL;
      const char* value = NULL;
      if (!PyArg_ParseTuple(args, "ss", &key, &value))
      {
        return NULL;
      }
      CALL_RETURN_SELF(((AMPS::Client*)self->pClient)->addHttpPreflightHeader(key, value));
    }

    static PyObject* clear_http_preflight_headers(obj* self, PyObject* args)
    {
      CALL_RETURN_SELF(((AMPS::Client*)self->pClient)->clearHttpPreflightHeaders());
    }

    static PyObject* set_publish_batching(obj* self, PyObject* args)
    {
      unsigned long batchSizeBytes, batchTimeoutMillis;
      if (!PyArg_ParseTuple(args, "kk", &batchSizeBytes, &batchTimeoutMillis))
      {
        return NULL;
      }
      CALL_RETURN_SELF(((AMPS::Client*)self->pClient)->setPublishBatching((amps_uint64_t)batchSizeBytes, (amps_uint64_t)batchTimeoutMillis));
    }

///
/// This method is used by python internals for garbage collection.
///
    static int
    traverse(obj* self, visitproc visit, void* arg)
    {
      if (self->disconnectHandler)
      {
        Py_VISIT(self->disconnectHandler);  //-V547
      }
      if (self->exceptionHandler)
      {
        volatile PyObject* callable = ((PyExceptionListener*)(
                                         self->exceptionHandler.get()))->callable();
        if (callable)
        {
          Py_VISIT(callable);
        }
      }
      if (self->transportFilter)
      {
        Py_VISIT(self->transportFilter->getHandler());  //-V547
      }
      if (self->threadCreatedCallback)
      {
        Py_VISIT(self->threadCreatedCallback);  // -V547
      }

      {
        AMPS::Lock<SimpleMutex> l(_createdHandlersLock);
        if ((callback_infos*)self->callbackInfos)
        {
          for (callback_infos::iterator i = ((callback_infos*)
                                             self->callbackInfos)->begin(),
               e = ((callback_infos*)self->callbackInfos)->end();
               i != e; ++i)
          {
            PyObject* handler = (*i)->getHandler();
            Py_VISIT(handler);
          }
        }
      }
      if ((connection_state_listeners*)self->connectionStateListeners)
      {
        typedef connection_state_listeners::iterator conn_state_itr;
        for (conn_state_itr i = ((connection_state_listeners*)
                                 self->connectionStateListeners)->begin(),
             e = ((connection_state_listeners*)self->connectionStateListeners)->end();
             i != e; ++i)
        {
          Py_VISIT(i->first);
        }
      }
      return 0;
    }

    static PyObject* get_as_parameter(obj* self, PyObject* args)
    {
      return PyLong_FromVoidPtr(self->pClient);
    }

    static ampspy::ampspy_type_object bookmarks_type;

    void add_types(PyObject* module_)
    {
      connection_state_listener::add_types();
      bookmarks_type.setName("AMPS.Bookmarks")
      .setDoc(bookmark_class_doc)
      .createType()
      .addStatic("EPOCH", PyString_FromString("0"))
      .addStatic("MOST_RECENT", PyString_FromString("recent"))
      .addStatic("NOW", PyString_FromString("0|1|"));

      client_type.setName("AMPS.Client")
      .setBasicSize(sizeof(obj))
      .setBaseType()
      .setDoc(client_class_doc)
      .setConstructorFunction((void*)_ctor)
      .setDestructorFunction((void*)destructor)
      .setHaveGC()
      .setTraverseFunction((void*)traverse)
      .setClearFunction((void*)_clear)
      .setWeakListOffset(sizeof(PyObject))
      .notCopyable()
      .addMethod("connect", connect, connect_doc)
      .addKeywordMethod("logon", logon, logon_doc)
      .addMethod("execute", execute, execute_doc)
      .addKeywordMethod("execute_async", execute_async, execute_async_doc)
      .addMethod("name", getName, name_doc)
      .addMethod("getName", getName, getName_doc)
      .addMethod("get_name", getName, get_name_doc)
      .addMethod("get_name_hash", get_name_hash, get_name_hash_doc)
      .addMethod("get_name_hash_value", get_name_hash_value, get_name_hash_value_doc)
      .addMethod("setName", setName, setName_doc)
      .addMethod("set_name", setName, set_name_doc)
      .addMethod("get_logon_correlation_data", get_logon_correlation_data,
                 get_logon_correlation_data_doc)
      .addMethod("set_logon_correlation_data", set_logon_correlation_data,
                 set_logon_correlation_data_doc)
      .addMethod("get_server_version", get_server_version, get_server_version_doc)
      .addMethod("get_server_version_info", get_server_version_info,
                 get_server_version_info_doc)
      .addMethod("convert_version_to_number", convert_version_to_number,
                 convert_version_to_number_doc)
      .addMethod("get_unpersisted_count", get_unpersisted_count,
                 get_unpersisted_count_doc)
      .addKeywordMethod("get_uri", getURI, get_uri_doc)
      .addMethod("disconnect", disconnect, disconnect_doc)
      .addMethod("close", disconnect, close_doc)
      .addKeywordMethod("publish", publish, publish_doc)
      .addKeywordMethod("delta_publish", delta_publish, delta_publish_doc)
      .addKeywordMethod("deltaPublish", delta_publish, deltaPublish_doc)
      .addMethod("unsubscribe", unsubscribe, unsubscribe_doc)
      .addKeywordMethod("send", send, send_doc)
      .addKeywordMethod("add_message_handler", add_message_handler,
                        add_message_handler_doc)
      .addMethod("remove_message_handler", remove_message_handler,
                 remove_message_handler_doc)
      .addMethod("allocate_message", allocate_message, allocate_message_doc)
      .addMethod("allocateMessage", allocate_message, allocateMessage_doc)
      .addKeywordMethod("subscribe", subscribe, subscribe_doc)
      .addKeywordMethod("bookmark_subscribe", bookmark_subscribe,
                        bookmark_subscribe_doc)
      .addKeywordMethod("sow", sow, sow_doc)
      .addKeywordMethod("sow_and_subscribe", sow_and_subscribe, sow_and_subscribe_doc)
      .addKeywordMethod("sowAndSubscribe", sow_and_subscribe, sowAndSubscribe_doc )
      .addKeywordMethod("sow_and_delta_subscribe", sow_and_delta_subscribe,
                        sow_and_delta_subscribe_doc)
      .addKeywordMethod("sowAndDeltaSubscribe", sow_and_delta_subscribe,
                        sowAndDeltaSubscribe_doc )
      .addKeywordMethod("sow_delete", sow_delete, sow_delete_doc)
      .addKeywordMethod("sowDelete", sow_delete, sowDelete_doc )
      .addKeywordMethod("sow_delete_by_keys", sow_delete_by_keys,
                        sow_delete_by_keys_doc)
      .addKeywordMethod("sow_delete_by_data", sow_delete_by_data,
                        sow_delete_by_data_doc)
      .addKeywordMethod("delta_subscribe", delta_subscribe, delta_subscribe_doc)
      .addKeywordMethod("deltaSubscribe", delta_subscribe, deltaSubscribe_doc )
      .addKeywordMethod("bookmark_subscribe", bookmark_subscribe,
                        bookmark_subscribe_doc)
      .addKeywordMethod("set_heartbeat", set_heartbeat, set_heartbeat_doc)
      .addMethod("start_timer", start_timer, start_timer_doc)
      .addMethod("stop_timer", stop_timer, stop_timer_doc)
      .addMethod("set_disconnect_handler", set_disconnect_handler,
                 set_disconnect_handler_doc)
      .addMethod("setOnDisconnectHandler", set_disconnect_handler,
                 setOnDisconnectHandler_doc )
      .addMethod("setDisconnectHandler", set_disconnect_handler,
                 setDisconnectHandler_doc )
      .addMethod("set_exception_listener", set_exception_listener,
                 set_exception_listener_doc)
      .addMethod("setExceptionListener", set_exception_listener,
                 setExceptionListener_doc )
      .addMethod("get_exception_listener", get_exception_listener,
                 get_exception_listener_doc)
      .addMethod("set_last_chance_message_handler", set_last_chance_message_handler,
                 set_last_chance_message_handler_doc  )
      .addMethod("set_unhandled_message_handler", set_last_chance_message_handler,
                 set_unhandled_message_handler_doc  )
      .addMethod("setUnhandledMessageHandler", set_last_chance_message_handler,
                 setUnhandledMessageHandler_doc  )
      .addMethod("set_duplicate_message_handler", set_duplicate_message_handler,
                 set_duplicate_message_handler_doc)
      .addMethod("get_duplicate_message_handler", get_duplicate_message_handler,
                 get_duplicate_message_handler_doc)
      .addKeywordMethod("publish_flush", publish_flush, publish_flush_doc)
      .addKeywordMethod("flush", publish_flush, flush_doc )
      .addMethod("set_bookmark_store", set_bookmark_store, set_bookmark_store_doc)
      .addMethod("set_publish_store", set_publish_store, set_publish_store_doc)
      .addMethod("set_failed_write_handler", set_failed_write_handler,
                 set_failed_write_handler_doc)
      .addMethod("add_connection_state_listener", add_connection_state_listener,
                 add_connection_state_listener_doc)
      .addMethod("remove_connection_state_listener", remove_connection_state_listener,
                 remove_connection_state_listener_doc)
      .addMethod("set_transport_filter", set_transport_filter,
                 set_transport_filter_doc)
      .addMethod("set_thread_created_callback", set_thread_created_callback,
                 set_thread_created_callback_doc)
      .addMethod("ack", ack, ack_doc)
      .addMethod("set_ack_batch_size", set_ack_batch_size, set_ack_batch_size_doc)
      .addMethod("get_ack_batch_size", get_ack_batch_size, get_ack_batch_size_doc)
      .addMethod("set_auto_ack", set_auto_ack, set_auto_ack_doc)
      .addMethod("get_auto_ack", get_auto_ack, get_auto_ack_doc)
      .addMethod("set_ack_timeout", set_ack_timeout, set_ack_timeout_doc)
      .addMethod("get_ack_timeout", get_ack_timeout, get_ack_timeout_doc)
      .addMethod("set_retry_on_disconnect", set_retry_on_disconnect,
                 set_retry_on_disconnect_doc)
      .addMethod("get_retry_on_disconnect", get_retry_on_disconnect,
                 get_retry_on_disconnect_doc)
      .addMethod("set_default_max_depth", set_default_max_depth,
                 set_default_max_depth_doc)
      .addMethod("get_default_max_depth", get_default_max_depth,
                 get_default_max_depth_doc)
      .addMethod("set_error_on_publish_gap", set_error_on_publish_gap,
                 set_error_on_publish_gap_doc)
      .addMethod("get_error_on_publish_gap", get_error_on_publish_gap,
                 get_error_on_publish_gap_doc)
      .addKeywordMethod("set_global_command_type_message_handler",
                        set_global_command_type_message_handler,
                        set_global_command_type_message_handler_doc)
#if PY_MAJOR_VERSION >= 3
      .addMethod("get_ssl", get_ssl,
                 "For a tcps client, returns the PySSLSocket of the connection")
#endif
      .addMethod("add_http_preflight_header", add_http_preflight_header,
                 add_http_preflight_header_doc)
      .addMethod("add_http_preflight_header_key_value", add_http_preflight_header_key_value,
                 add_http_preflight_header_key_value_doc)
      .addMethod("clear_http_preflight_headers", clear_http_preflight_headers,
                 clear_http_preflight_headers_doc)
      .addMethod("set_publish_batching", set_publish_batching,
                 set_publish_batching_doc)
      .addGetter("_as_parameter_", (void*)get_as_parameter,
                 "Underlying Client pointer for use with foreign functions and the ctypes module.")
      .createType()
      .registerType("Client", module_)
      .addStatic("Bookmarks", bookmarks_type)
      .addStatic("ConnectionStateListener",
                 connection_state_listener::connection_state_listener_type);
    }

  } // namespace client
} // namespace ampspy
