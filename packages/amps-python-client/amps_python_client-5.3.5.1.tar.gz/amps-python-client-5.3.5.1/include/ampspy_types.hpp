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
#ifndef __AMPSPY_TYPES_HPP
#define __AMPSPY_TYPES_HPP

#include <ampspy_shims.hpp>
#include <amps/util.hpp>
#include <amps/ampsplusplus.hpp>
#include <amps/CompositeMessageBuilder.hpp>
#include <amps/CompositeMessageParser.hpp>
#include <amps/DefaultServerChooser.hpp>
#include <amps/MMapBookmarkStore.hpp>
#include <amps/MemoryPublishStore.hpp>
#include <amps/PublishStore.hpp>
#include <amps/ReconnectDelayStrategy.hpp>
#include <amps/RecoveryPoint.hpp>
#include <amps/RecoveryPointAdapter.hpp>
#include <amps/RingBookmarkStore.hpp>
#include <amps/SOWRecoveryPointAdapter.hpp>
#include <ampspy_type_object.hpp>

#include <deque>
#include <memory>
#include <vector>

// It's a little strange to define _PyThreadState_Current for >= 3.5,
//  since that is still the name of a global in python (albeit with static
//  linkage). Instead we make the equivalent python 3 function available in 2.x.
#if PY_VERSION_HEX < 0x03000000 && !defined(_PyThreadState_UncheckedGet)
  #define _PyThreadState_UncheckedGet() _PyThreadState_Current
#elif PY_VERSION_HEX < 0x03050000 && !defined(_PyThreadState_UncheckedGet)
  #define _PyThreadState_UncheckedGet() ((PyThreadState*)_Py_atomic_load_relaxed(&_PyThreadState_Current))
#endif

#if __cplusplus >= 201100L || _MSC_VER >= 1900
  #include <atomic>
  #define AMPSPY_ATOMIC(x) std::atomic<x>
  #define AMPSPY_IEX_GET(x, y) std::atomic_exchange(x, y)
#else
  #define AMPSPY_ATOMIC(x) x volatile
  #ifdef _WIN64
    #define AMPSPY_IEX_GET(ptr,value) _InterlockedExchange64((LONG64*)(ptr), (LONG64)(value))
  #elif defined(_WIN32 )
    #define AMPSPY_IEX_GET(ptr,value) _InterlockedExchange((long*)(ptr), (LONG)(value))
  #else
    #define AMPSPY_IEX_GET(ptr, value) __sync_lock_test_and_set(ptr, value)
  #endif
#endif

class ampspy_shutdown_exception : public std::runtime_error
{
public:
  ampspy_shutdown_exception(void)
    : std::runtime_error("The python interpreter is shutting down.")
  {;}
};

class AMPSDLL LockGIL
{
  PyGILState_STATE state;
public:
  // due to bugs.python.org/issue1856, we can't safely Ensure while the interpreter is shutting down.
  // we have an at-exit handler registered that sets this flag, which should exit any thread
  // about to attempt to call back into python from here, while the main thread finishes up.
  LockGIL()
  {
    if (ampspy::shims::Py_IsFinalizing())
    {
      throw ampspy_shutdown_exception();
    }
    state = PyGILState_Ensure();
  }
  ~LockGIL()
  {
    if (ampspy::shims::Py_IsFinalizing())
    {
      return;
    }

    if (ampspy::shims::PyThreadState_UncheckedGet() == PyGILState_GetThisThreadState())
    {
      PyGILState_Release(state);
    }
    else
    {
      // We're here because we think we are the current thread and own
      // the GIL, and yet _PyThreadState_Current says we're not the
      // current thread. Calling Release here will abort(). This
      // seems to happen after the shutdown sequence has initiated,
      // inside threads other than the interpreter thread.
      ;
    }
  }
};

#define LOCKGIL LockGIL _lock_;
class AMPSDLL UnlockGIL
{
  PyThreadState* state;
public:
  UnlockGIL()
  {
    state = PyEval_SaveThread();
  }
  ~UnlockGIL()
  {
    if (state)
    {
      PyEval_RestoreThread(state);
    }
  }
  void restore()
  {
    PyEval_RestoreThread(state);
    state = NULL;
  }
};

template<class Object = PyObject>
class AMPSDLL AMPSPyReference
{
  Object* _self;
public:

  AMPSPyReference(Object* self_) : _self(self_)
  {
  }

  ~AMPSPyReference()
  {
    Py_XDECREF((PyObject*)_self);
  }
  operator Object* ()
  {
    return _self;
  }
  Object* operator*(void)
  {
    return _self;
  }
  Object* operator->(void)
  {
    return _self;
  }

  bool isNull(void) const
  {
    return _self == NULL;
  }
  PyObject* asPyObject(void)
  {
    return (PyObject*)_self;
  }

  PyObject* release(void)
  {
    PyObject* self = (PyObject*)_self;
    _self = NULL;
    return self;
  }
};



#define UNLOCKGIL UnlockGIL _lock_;

//
// Defines an AMPSException subclass that wraps a Python exception/value/traceback.
// Keeps references to the fetched error and clears the error state. Can restore self
// to the python error state, or just the value can be extracted and borrowed. Takes
// care of removing references when it's all done, or if it is used to restore the
// error state.
class PyException : public AMPS::AMPSException
{
  PyObject* _type, *_value, *_traceback;
  void operator=(const PyException& rhs);
public:
  PyException(const PyException& rhs):
    AMPS::AMPSException(rhs.what(), AMPS_E_OK),
    _type(rhs._type),
    _value(rhs._value),
    _traceback(rhs._traceback)
  {
    Py_XINCREF(_type);
    Py_XINCREF(_value);
    Py_XINCREF(_traceback);
  }

  // this error message is seen when the exception is examined from C++ land,
  // including in the "reason" entry in the dictionary passed to ServerChooser's
  // report_failure.
  PyException() : AMPS::AMPSException("a python exception occurred.", AMPS_E_OK)
  {
    _type = NULL;
    _value = NULL;
    _traceback = NULL;
    PyErr_Fetch(&_type, &_value, &_traceback);
    PyErr_NormalizeException(&_type, &_value, &_traceback);

    // attempt to create a textual description of the error, and set our own "what" to it
    std::string text;
    if (_type)
    {
      PyObject* typeName = PyObject_GetAttrString(_type, "__name__");
      if (typeName)
      {
#if PY_MAJOR_VERSION >= 3
        text.append(ampspy::shims::PyUnicode_AsUTF8(typeName));
#else
        text.append(PyString_AsString(typeName));
#endif
        text.append(": ");
        Py_DECREF(typeName); // -V1067
      }
    }
    if (_value)
    {
      PyObject* strVal = PyObject_Str(_value);
#if PY_MAJOR_VERSION >= 3
      if (strVal)
      {
        text.append(ampspy::shims::PyUnicode_AsUTF8(strVal));
      }
#else
      if (strVal)
      {
        text.append(PyString_AsString(strVal));
      }
#endif
      Py_XDECREF(strVal); // -V1067
    }

    // re-set our message if we've got something useful
    if (!text.empty())
    {
      *((AMPS::AMPSException*)this) = AMPS::AMPSException(text, AMPS_E_OK);
    }
  }

  void restore()
  {
    if (_type)
    {
      PyErr_Restore(_type, _value, _traceback);
      _type = _value = _traceback = NULL;
    }
  }

  PyObject* value() const
  {
    return _value;
  }
  PyObject* traceback() const
  {
    return _traceback;
  }

  ~PyException() throw()
  {
    try
    {
      LockGIL lock;
      Py_XDECREF(_type);
      Py_XDECREF(_value);
      Py_XDECREF(_traceback);
    }
    catch (...)
    {
      // ignore exception from locking the GIL.
      // We are shutting down and have been caught without a running interpreter.
      // We can no longer safely remove references from the type/value/traceback.
    }
  }
};

#define AMPS_EX_TRAN(x,y) \
  catch(const x & in_ex) \
  {\
    if(ampspy::_is_signaled == true) \
    {\
      PyErr_SetNone(PyExc_KeyboardInterrupt);\
      ampspy::_is_signaled = false; \
    } else {\
      PyErr_SetString(exc::y, in_ex.what());\
    }\
    return NULL;\
  }

#define DISPATCH_EXCEPTION \
  catch(PyException & ex) \
  {\
    ex.restore();\
    return NULL;\
  }\
  AMPS_EX_TRAN(BadSowKeyException, BadSowKeyException)\
  AMPS_EX_TRAN(DuplicateLogonException, DuplicateLogonException)\
  AMPS_EX_TRAN(InvalidBookmarkException, InvalidBookmarkException)\
  AMPS_EX_TRAN(InvalidOptionsException, InvalidOptionsException)\
  AMPS_EX_TRAN(InvalidOrderByException, InvalidOrderByException)\
  AMPS_EX_TRAN(InvalidSubIdException, InvalidSubIdException)\
  AMPS_EX_TRAN(LogonRequiredException, LogonRequiredException)\
  AMPS_EX_TRAN(MissingFieldsException, MissingFieldsException)\
  AMPS_EX_TRAN(PublishException, PublishException)\
  AMPS_EX_TRAN(UsageException, AMPSException) \
  AMPS_EX_TRAN(PublishStoreGapException, AMPSException) \
  AMPS_EX_TRAN(StoreException, AMPSException) \
  AMPS_EX_TRAN(DisconnectedException, DisconnectedException)\
  AMPS_EX_TRAN(AlreadyConnectedException, AlreadyConnectedException)\
  AMPS_EX_TRAN(RetryOperationException, RetryOperationException)\
  AMPS_EX_TRAN(AuthenticationException, AuthenticationException)\
  AMPS_EX_TRAN(NotEntitledException, NotEntitledException)\
  AMPS_EX_TRAN(TimedOutException, TimedOutException)\
  AMPS_EX_TRAN(ConnectionRefusedException, ConnectionRefusedException)\
  AMPS_EX_TRAN(InvalidURIException, InvalidUriException)\
  AMPS_EX_TRAN(TransportTypeException, TransportTypeException)\
  AMPS_EX_TRAN(BadFilterException, BadFilterException)\
  AMPS_EX_TRAN(BadRegexTopicException, BadRegexTopicException)\
  AMPS_EX_TRAN(InvalidTopicException, InvalidTopicException)\
  AMPS_EX_TRAN(NameInUseException, NameInUseException)\
  AMPS_EX_TRAN(SubscriptionAlreadyExistsException, SubscriptionAlreadyExistsException)\
  AMPS_EX_TRAN(SubidInUseException, SubidInUseException)\
  AMPS_EX_TRAN(UnknownException, UnknownException)\
  AMPS_EX_TRAN(CommandException, CommandException)\
  AMPS_EX_TRAN(ConnectionException, ConnectionException)\
  AMPS_EX_TRAN(AMPSException, AMPSException)\
  catch (const std::exception& ex)\
  {\
    if(ampspy::_is_signaled == true) \
    {\
      PyErr_SetNone(PyExc_KeyboardInterrupt);\
      ampspy::_is_signaled = false; \
    } else \
      PyErr_SetString(PyExc_RuntimeError, ex.what());\
    return NULL;\
  } catch(...)\
  {\
    if(ampspy::_is_signaled == true) \
    {\
      PyErr_SetNone(PyExc_KeyboardInterrupt);\
      ampspy::_is_signaled = false; \
    } else \
      PyErr_SetString(PyExc_RuntimeError, "An unknown error has occured.");\
    return NULL;\
  }

#define AMPS_EX_TRAN_NO_RETURN(x,y) \
  catch(const x & in_ex) \
  {\
    if(ampspy::_is_signaled == true) \
    {\
      PyErr_SetNone(PyExc_KeyboardInterrupt);\
      ampspy::_is_signaled = false; \
    } else \
      PyErr_SetString(exc::y, in_ex.what());\
  }

#define DISPATCH_EXCEPTION_NO_RETURN \
  catch(PyException & ex) \
  {\
    ex.restore();\
  }\
  AMPS_EX_TRAN_NO_RETURN(BadSowKeyException, BadSowKeyException)\
  AMPS_EX_TRAN_NO_RETURN(DuplicateLogonException, DuplicateLogonException)\
  AMPS_EX_TRAN_NO_RETURN(InvalidBookmarkException, InvalidBookmarkException)\
  AMPS_EX_TRAN_NO_RETURN(InvalidOptionsException, InvalidOptionsException)\
  AMPS_EX_TRAN_NO_RETURN(InvalidOrderByException, InvalidOrderByException)\
  AMPS_EX_TRAN_NO_RETURN(InvalidSubIdException, InvalidSubIdException)\
  AMPS_EX_TRAN_NO_RETURN(LogonRequiredException, LogonRequiredException)\
  AMPS_EX_TRAN_NO_RETURN(MissingFieldsException, MissingFieldsException)\
  AMPS_EX_TRAN_NO_RETURN(PublishException, PublishException)\
  AMPS_EX_TRAN_NO_RETURN(UsageException, AMPSException) \
  AMPS_EX_TRAN_NO_RETURN(PublishStoreGapException, AMPSException) \
  AMPS_EX_TRAN_NO_RETURN(StoreException, AMPSException) \
  AMPS_EX_TRAN_NO_RETURN(DisconnectedException, DisconnectedException)\
  AMPS_EX_TRAN_NO_RETURN(AlreadyConnectedException, AlreadyConnectedException)\
  AMPS_EX_TRAN_NO_RETURN(RetryOperationException, RetryOperationException)\
  AMPS_EX_TRAN_NO_RETURN(AuthenticationException, AuthenticationException)\
  AMPS_EX_TRAN_NO_RETURN(NotEntitledException, NotEntitledException)\
  AMPS_EX_TRAN_NO_RETURN(TimedOutException, TimedOutException)\
  AMPS_EX_TRAN_NO_RETURN(ConnectionRefusedException, ConnectionRefusedException)\
  AMPS_EX_TRAN_NO_RETURN(InvalidURIException, InvalidUriException)\
  AMPS_EX_TRAN_NO_RETURN(TransportTypeException, TransportTypeException)\
  AMPS_EX_TRAN_NO_RETURN(BadFilterException, BadFilterException)\
  AMPS_EX_TRAN_NO_RETURN(BadRegexTopicException, BadRegexTopicException)\
  AMPS_EX_TRAN_NO_RETURN(InvalidTopicException, InvalidTopicException)\
  AMPS_EX_TRAN_NO_RETURN(NameInUseException, NameInUseException)\
  AMPS_EX_TRAN_NO_RETURN(SubscriptionAlreadyExistsException, SubscriptionAlreadyExistsException)\
  AMPS_EX_TRAN_NO_RETURN(SubidInUseException, SubidInUseException)\
  AMPS_EX_TRAN_NO_RETURN(UnknownException, UnknownException)\
  AMPS_EX_TRAN_NO_RETURN(CommandException, CommandException)\
  AMPS_EX_TRAN_NO_RETURN(ConnectionException, ConnectionException)\
  AMPS_EX_TRAN_NO_RETURN(AMPSException, AMPSException)\
  catch (const std::exception& ex)\
  {\
    if(ampspy::_is_signaled == true) \
    {\
      PyErr_SetNone(PyExc_KeyboardInterrupt);\
      ampspy::_is_signaled = false; \
    } else \
      PyErr_SetString(PyExc_RuntimeError, ex.what());\
  } catch(...)\
  {\
    if(ampspy::_is_signaled == true) \
    {\
      PyErr_SetNone(PyExc_KeyboardInterrupt);\
      ampspy::_is_signaled = false; \
    } else \
      PyErr_SetString(PyExc_RuntimeError, "An unknown error has occured.");\
  }

namespace ampspy
{
// used to initiate an exit process after a callback has requested it.
  AMPSDLL void unhandled_exception();

  namespace exc
  {
    extern PyObject* AMPSException;
    extern PyObject* CommandException;
    extern PyObject* CommandTypeError;
    extern PyObject* TimedOutException;
    extern PyObject* BadFilterException;
    extern PyObject* BadFilter;
    extern PyObject* BadRegexTopicException;
    extern PyObject* BadRegexTopic;
    extern PyObject* InvalidTopicException;
    extern PyObject* InvalidTopicError;
    extern PyObject* SubidInUseException;
    extern PyObject* SubscriptionAlreadyExistsException;
    extern PyObject* SubscriptionAlreadyExists;
    extern PyObject* UnknownException;
    extern PyObject* UnknownError;
    extern PyObject* ConnectionException;
    extern PyObject* AlreadyConnectedException;
    extern PyObject* AlreadyConnected;
    extern PyObject* AuthenticationException;
    extern PyObject* AuthenticationError;
    extern PyObject* ConnectionRefusedException;
    extern PyObject* ConnectionRefused;
    extern PyObject* DisconnectedException;
    extern PyObject* Disconnected;
    extern PyObject* InvalidUriException;
    extern PyObject* InvalidUriFormat;
    extern PyObject* MessageTypeError;
    extern PyObject* MessageTypeException;
    extern PyObject* MessageTypeNotFound;
    extern PyObject* InvalidMessageTypeOptions;
    extern PyObject* NameInUseException;
    extern PyObject* ClientNameInUse;
    extern PyObject* NotEntitledException;
    extern PyObject* NotEntitledError;
    extern PyObject* RetryOperationException;
    extern PyObject* RetryOperation;
    extern PyObject* StreamException;
    extern PyObject* StreamError;
    extern PyObject* TransportException;
    extern PyObject* TransportError;
    extern PyObject* InvalidTransportOptionsException;
    extern PyObject* InvalidTransportOptions;
    extern PyObject* TransportTypeException;
    extern PyObject* TransportNotFound;
    extern PyObject* BadSowKeyException;
    extern PyObject* DuplicateLogonException;
    extern PyObject* InvalidBookmarkException;
    extern PyObject* InvalidOptionsException;
    extern PyObject* InvalidOrderByException;
    extern PyObject* InvalidSubIdException;
    extern PyObject* LogonRequiredException;
    extern PyObject* MissingFieldsException;
    extern PyObject* PublishException;

    AMPSDLL void throwError();
  }

  class PyExceptionListener : public AMPS::ExceptionListener
  {
    volatile PyObject* _callable;
  public:

    void exceptionThrown(const std::exception& ex) const
    {
      LOCKGIL;
      if (!_callable)
      {
        return;
      }
      PyObject* ctor_args = Py_BuildValue("(s)", ex.what());
      if (ctor_args == NULL)
      {
        ampspy::unhandled_exception();
      }
      PyObject* exception = NULL;
      PyObject* traceback = NULL;
#if defined(_CPPRTTI) || defined(__GXX_RTTI)
      // IF we have RTTI on, we can check if the exception has a python
      // exception buried in it, and just pass that thing in, instead
      // of manufacturing an AMPSException object.
      // Without RTTI, the python exception listener will always see an
      // AMPSException.
      const PyException* pyException = dynamic_cast<const PyException*>(&ex);

      if ( pyException != NULL )
      {
        exception = pyException->value();
        Py_XINCREF(exception);
        traceback = pyException->traceback();
        Py_XINCREF(traceback);
      }
#endif
      if (exception == NULL)
      {
        exception = PyObject_CallObject(ampspy::exc::AMPSException, ctor_args);
      }
      if (exception == NULL)
      {
        ampspy::unhandled_exception();
      }
      if (traceback == NULL)
      {
        traceback = Py_None;
        Py_XINCREF(traceback);
      }
      PyObject* exception_tuple = Py_BuildValue("(OO)", exception, traceback);
      if (exception_tuple == NULL)
      {
        ampspy::unhandled_exception();
      }
      PyObject* retval = PyObject_Call((PyObject*)_callable, exception_tuple, (PyObject*)NULL);
      if (retval == NULL)
      {
        PyErr_Clear();
        // try it without the traceback
        Py_XDECREF(exception_tuple);
        exception_tuple = Py_BuildValue("(O)", exception);
        retval = PyObject_Call((PyObject*)_callable, exception_tuple, (PyObject*)NULL);
        if (retval == NULL)
        {
          ampspy::unhandled_exception();
        }
      }
      Py_XDECREF(retval);
      Py_XDECREF(exception_tuple);
      Py_XDECREF(exception);
      Py_XDECREF(ctor_args);
      Py_XDECREF(traceback);
    }
    PyExceptionListener() : _callable(NULL) {;}
    PyExceptionListener(PyObject* callable)
      : _callable(callable)
    {
      LOCKGIL;
      Py_INCREF(callable);
    }
    ~PyExceptionListener()
    {
      try
      {
        LOCKGIL;
        Py_XDECREF(_callable);
      }
      catch (...)
      {
        // Shutdown can throw locking the GIL
      }
    }
    void set(PyObject* callable)
    {
      try
      {
        LOCKGIL;
        Py_XDECREF(_callable);
        _callable = callable;
        Py_XINCREF(callable);
      }
      catch (...)
      {
        // Shutdown can throw locking the GIL
      }
    }
    volatile PyObject* callable(void)
    {
      return _callable;
    }
  };

  class PyAuthenticator;

  namespace message
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
      AMPS::Message* pMessage;
      bool isOwned;
    };
    namespace options
    {
      struct AMPSDLL obj
      {
        PyObject_HEAD
        AMPS::Message::Options* pOptions;
      };
    } //namespace options

    AMPSDLL_EXTERN ampspy::ampspy_type_object message_type;
    void add_types(PyObject* module_);
    AMPSDLL PyObject* toPythonMessage(AMPS::Message& message_);
    AMPSDLL void setCppMessage(obj* pMessage_, const AMPS::Message& message_);
  } // namespace message

  namespace cmessagehandler
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
      PyObject* function;
      PyObject* userdata;
    };
    AMPSDLL AMPS::MessageHandler getMessageHandler(PyObject* obj);
    AMPSDLL bool isCHandler(PyObject* obj);
    void add_types(PyObject*);
  }
  namespace client
  {
    struct AMPSDLL callback_info;
    class TransportFilter;
    typedef std::list<callback_info*> callback_infos;
    typedef std::map<PyObject*, AMPS::ConnectionStateListener*> connection_state_listeners;
    typedef std::vector<void*> message_stream_list;
    struct obj
    {
      PyObject_HEAD
      PyObject* weakreflist;
      AMPSPY_ATOMIC(AMPS::Client*) pClient;
      PyObject* disconnectHandler;
      std::shared_ptr<AMPS::ExceptionListener> exceptionHandler;
      AMPSPY_ATOMIC(callback_infos*) callbackInfos;
      message::obj* message;
      PyObject* message_args;
      AMPSPY_ATOMIC(connection_state_listeners*) connectionStateListeners;
      TransportFilter* transportFilter;
      PyObject* threadCreatedCallback;
    };
    namespace connection_state_listener
    {
      struct AMPSDLL obj
      {
        PyObject_HEAD
      };
    } // namespace connection_state_listener
    AMPSDLL_EXTERN ampspy_type_object client_type;
    void add_types(PyObject* module_);
    void _initializeInternals(obj*);
    AMPSDLL void* copy_route(void*);
    AMPSDLL void remove_route(void*);
    AMPSDLL void destructor(PyObject*);
    AMPSDLL void clear_callback_infos(void*);
    AMPSDLL void amps_python_client_atfork_prepare();
    AMPSDLL void amps_python_client_atfork_child();
    AMPSDLL void amps_python_client_atfork_parent();
  }
  namespace reason
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
    };
    AMPSDLL_EXTERN ampspy::ampspy_type_object reason_type;
    void add_types(PyObject* module_);
  }
  namespace store
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
    };
    void add_types(PyObject* module_);
  }
  namespace fixbuilder
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
      AMPS::FIXBuilder* pFIXBuilder;
    };
    void add_types(PyObject* module_);
  }
  namespace nvfixbuilder
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
      AMPS::NVFIXBuilder* pNVFIXBuilder;
    };
    void add_types(PyObject* module_);
  }

  namespace authenticator
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
    };
    void add_types(PyObject* module_);
  }

  namespace serverchooser
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
      AMPS::DefaultServerChooser* impl;
    };
    void add_types(PyObject* module_);
  }

  namespace fixshredder
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
      char fs;
    };
    void add_types(PyObject* module_);
  }

  namespace nvfixshredder
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD
      char fs;
    };
    void add_types(PyObject* module_);
  }
  namespace haclient
  {
    struct AMPSDLL obj
    {
      client::obj _client;
      PyObject* _pyServerChooser;
      PyObject* _pyDelayStrategy;
    };
    AMPSDLL_EXTERN ampspy_type_object haclient_type;
    void add_types(PyObject* module_);
  }
  namespace messagestream
  {
    struct obj;
    AMPSDLL void messageCallback(const AMPS::Message& message, void* void_self);
    class CustomConnectionStateListener : public AMPS::ConnectionStateListener
    {
      obj* _self;
    public:
      CustomConnectionStateListener(obj* self_ = NULL) : _self(self_) {}
      void connectionStateChanged(AMPS::ConnectionStateListener::State state_);
    };
    struct MessageStreamImpl;
    struct obj
    {
      PyObject_HEAD
      AMPSPY_ATOMIC(MessageStreamImpl*) _pImpl;
      PyObject*          _pPythonClient;
      AMPS::Client       _client;

      void internalInit(PyObject*, AMPS::Client*, bool, bool, bool);

      AMPS::MessageHandler messageHandler();

      const std::string& commandId(void) const;
      std::string& commandId(void);
      const std::string& queryId(void) const;
      std::string& queryId(void);
      const std::string& subId(void) const;
      std::string& subId(void);
      void setAcksOnly(unsigned);
    };
    AMPSDLL_EXTERN ampspy::ampspy_type_object messagestream_type;
    AMPSDLL void discardImpl(void*);
    void add_types(PyObject*);
  }
  namespace command
  {
    struct obj
    {
      PyObject_HEAD
      AMPS::Command command;
    };
    AMPSDLL_EXTERN ampspy_type_object command_type;
    void add_types(PyObject*);
  }
  namespace memorybookmarkstore
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::BookmarkStore* impl;
      PyObject* resizeHandler;
      PyObject* pAdapter;
    };
    AMPSDLL_EXTERN ampspy_type_object memorybookmarkstore_type;
    void add_types(PyObject*);
  }
  namespace memorypublishstore
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::Store* impl;
      PyObject* resizeHandler;
    };
    AMPSDLL_EXTERN ampspy_type_object memorypublishstore_type;
    void add_types(PyObject*);
  }
  namespace hybridpublishstore
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::Store* impl;
      PyObject* resizeHandler;
    };
    AMPSDLL_EXTERN ampspy_type_object hybridpublishstore_type;
    void add_types(PyObject*);
  }
  namespace publishstore
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::PublishStore* impl;
      PyObject* resizeHandler;
    };
    AMPSDLL_EXTERN ampspy_type_object publishstore_type;
    void add_types(PyObject*);
  }
  namespace mmapbookmarkstore
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::BookmarkStore* impl;
      PyObject* resizeHandler;
      PyObject* pAdapter;
    };
    AMPSDLL_EXTERN ampspy_type_object mmapbookmarkstore_type;
    void add_types(PyObject*);
  }
  namespace ringbookmarkstore
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::BookmarkStore* impl;
      PyObject* resizeHandler;
    };
    AMPSDLL_EXTERN ampspy_type_object ringbookmarkstore_type;
    void add_types(PyObject*);
  }


  namespace exponentialdelaystrategy
  {
    struct obj
    {
      PyObject_HEAD;
      AMPS::ReconnectDelayStrategy impl;
    };
    AMPSDLL_EXTERN ampspy_type_object type;
    void add_types(PyObject*);
  }

  namespace fixeddelaystrategy
  {
    struct obj
    {
      PyObject_HEAD;
      AMPS::ReconnectDelayStrategy impl;
    };
    AMPSDLL_EXTERN ampspy_type_object type;
    void add_types(PyObject*);
  }

  namespace compositemessagebuilder
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::CompositeMessageBuilder* pCompositeMessageBuilder;
    };
    void add_types(PyObject* module_);
  }

  namespace compositemessageparser
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::CompositeMessageParser* pCompositeMessageParser;
      std::string* pLastParsed;
    };
    void add_types(PyObject* module_);
  }

  namespace versioninfo
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      AMPS::VersionInfo* pVersionInfo;
    };
    AMPSDLL_EXTERN ampspy_type_object versioninfo_type;
    void add_types(PyObject*);
  }

  namespace recoverypoint
  {
    struct AMPSDLL obj
    {
      PyObject_HEAD;
      char* subId;
      char* bookmark;
    };
    AMPSDLL_EXTERN ampspy::ampspy_type_object type;
    void add_types(PyObject*);
  }

  namespace sowrecoverypointadapter
  {
    struct obj
    {
      PyObject_HEAD;
      std::shared_ptr<AMPS::SOWRecoveryPointAdapter> pImpl;
      AMPS::RecoveryPointAdapter adapter;
      std::shared_ptr<AMPS::ExceptionListener> exceptionListener;
    };
    AMPSDLL_EXTERN ampspy::ampspy_type_object type;
    void add_types(PyObject*);
  }

  namespace conflatingrecoverypointadapter
  {
    struct obj
    {
      PyObject_HEAD;
      AMPS::ConflatingRecoveryPointAdapter* pImpl;
      AMPS::RecoveryPointAdapter adapter;
      PyObject* pDelegate;
    };
    AMPSDLL_EXTERN ampspy::ampspy_type_object type;
    void add_types(PyObject*);
  }

  class PyAuthenticator : public AMPS::DefaultAuthenticator
  {
    PyObject* _self;
  public:

    // No reference to the authenticator is taken; caller is responsible
    // for ensuring authenticator still exists for lifetime of this bridge.
    PyAuthenticator(PyObject* self) : _self(self) {}
    void setPythonAuthenticator(PyObject* new_)
    {
      _self = new_;
    }
    PyObject* getPythonAuthenticator(void)
    {
      return _self;
    }

    // Allows the authenticator to return a Unicode in Py 3.x,
    // a bytes-like object, a string, None, or any object that
    // has a __str__ method defined.
    std::string extractReturnedPassword(PyObject* pyObject_)
    {
      assert(pyObject_);
#if PY_MAJOR_VERSION >= 3
      if (PyUnicode_Check(pyObject_))
      {
        const char* data = shims::PyUnicode_AsUTF8(pyObject_);
        exc::throwError();
        if (data)
        {
          return std::string(data);
        }
      }
#endif
      if (PyBytes_Check(pyObject_))
      {
        const char* data = PyBytes_AsString(pyObject_);
        exc::throwError();
        if (data)
        {
          return std::string(data);
        }
      }
      else if (pyObject_ == Py_None)
      {
        return "";
      }
      else
      {
        PyObject* pyStringRep = PyObject_Str(pyObject_);
        if (pyStringRep)
        {
          const char* bytes = NULL;
#if PY_MAJOR_VERSION >= 3
          bytes = shims::PyUnicode_AsUTF8(pyStringRep);
#else
          bytes = PyString_AsString(pyStringRep);
#endif
          std::string retVal(bytes);
          if (bytes)
          {
            retVal = bytes;
          }
          Py_DECREF(pyStringRep);
          exc::throwError();
          if (!retVal.empty())
          {
            return retVal;
          }
        }
      }

      throw AMPS::AMPSException("Unknown return type returned by authenticator.", AMPS_E_OK);
    }

    virtual std::string authenticate(const std::string& userName_, const std::string& password_)
    {
      LOCKGIL;
      PyObject* p = PyObject_CallMethod((PyObject*)_self, (char*)"authenticate", (char*)"(ss)", userName_.c_str(), password_.c_str());
      if (p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
      {
        ampspy::unhandled_exception();
      }
      exc::throwError();
      if (!p)
      {
        return password_;
      }

      std::string returnValue = extractReturnedPassword(p);
      Py_DECREF(p);

      return returnValue;
    }
    ///
    virtual std::string retry(const std::string& userName_, const std::string& password_)
    {
      LOCKGIL;
      PyObject* p = PyObject_CallMethod((PyObject*)_self, (char*)"retry", (char*)"(ss)", userName_.c_str(), password_.c_str());
      if (p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
      {
        ampspy::unhandled_exception();
      }
      exc::throwError();
      if (!p)
      {
        return password_;
      }
      std::string returnValue = extractReturnedPassword(p);
      Py_DECREF(p);

      return returnValue;
    }
    virtual void completed(const std::string& userName_, const std::string& password_, const std::string& reason_)
    {
      LOCKGIL;
      PyObject* p = PyObject_CallMethod((PyObject*)_self, (char*)"completed", (char*)"(sss)", userName_.c_str(), password_.c_str(), reason_.c_str());
      if (p == NULL && PyErr_ExceptionMatches(PyExc_SystemExit))
      {
        ampspy::unhandled_exception();
      }
      exc::throwError();
      Py_XDECREF(p);
    }
  };

  class server_chooser_wrapper : public AMPS::ServerChooserImpl
  {
    PyObject* _self;
    PyAuthenticator _authBridge;
  public:
    server_chooser_wrapper(PyObject* self_);
    ~server_chooser_wrapper();
    virtual std::string getCurrentURI();
    virtual AMPS::Authenticator& getCurrentAuthenticator();
    virtual void reportFailure(const AMPS::AMPSException& exception_,
                               const AMPS::ConnectionInfo& info_);
    virtual std::string getError();
    virtual void reportSuccess(const AMPS::ConnectionInfo& info_);
    virtual void add(const std::string& uri_);
    virtual void remove(const std::string& uri_);
  private:
    static void setPyExceptionState(const AMPS::AMPSException&);
  };

  class PyFailedWriteHandler : public AMPS::FailedWriteHandler
  {
    PyObject* _self;
    bool _newStyle;
    ampspy::message::obj* _message;
    PyFailedWriteHandler(const PyFailedWriteHandler&);  // not implemented
    void operator=(const PyFailedWriteHandler&); // not implemented
  public:
    PyFailedWriteHandler(PyObject* self_);
    ~PyFailedWriteHandler();
    virtual void failedWrite(const AMPS::Message& message_,
                             const char* reason_, size_t reasonLength_);
  };

}

// Used to add dummy __copy__ and __deepcopy__ methods to a type, so as
// to make it not copyable.
AMPSDLL PyObject* not_copyable(PyObject* self, PyObject* args);
#define NOT_COPYABLE \
  { "__copy__", (PyCFunction)&::not_copyable, METH_VARARGS, "not supported."}, \
  { "__deepcopy__", (PyCFunction)&::not_copyable, METH_VARARGS, "not supported."}

#endif // __AMPSPY_TYPES_HPP

