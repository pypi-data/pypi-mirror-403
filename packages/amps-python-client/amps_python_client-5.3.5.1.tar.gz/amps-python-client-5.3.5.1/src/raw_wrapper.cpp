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
#ifdef _WIN32
#include <Winsock2.h>
#include <Ws2tcpip.h>
#endif
#include <Python.h>
#include <object.h>
#include <amps/ampsplusplus.hpp>
extern "C" {
#include <amps/amps_impl.h>
#include <amps/amps_ssl.h>
}
#include <ampspy_types.hpp>
#include <ampspy_defs.hpp>
#include <ampspy_ssl.hpp>
#include <ampspyver.h>

using namespace AMPS;

AMPSDLL PyObject* not_copyable(PyObject* self, PyObject* args)
{
  PyErr_SetString(PyExc_TypeError, "This type cannot be copied.");
  return NULL;
}

extern "C"
{
  extern int        (*amps_tcps_close_all)(AMPS_SOCKET, _amps_SSL*);
  extern _amps_SSL* (*amps_tcps_get_socket_and_ssl)(AMPS_SOCKET,
                                                   const char* address_, int port_,
                                                   struct addrinfo*,
                                                   char*, void*);
  void amps_tcps_set_external_error(void* transport, const amps_char* buffer);
}

namespace ampspy
{
  namespace exc
  {
    PyObject* AMPSException;
    PyObject* AlreadyConnected;
    PyObject* AlreadyConnectedException;
    PyObject* AuthenticationError;
    PyObject* AuthenticationException;
    PyObject* BadFilter;
    PyObject* BadFilterException;
    PyObject* BadRegexTopic;
    PyObject* BadRegexTopicException;
    PyObject* BadSowKeyException;
    PyObject* ClientNameInUse;
    PyObject* CommandError;
    PyObject* CommandException;
    PyObject* CommandTimedOut;
    PyObject* CommandTypeError;
    PyObject* ConnectionError;
    PyObject* ConnectionException;
    PyObject* ConnectionRefused;
    PyObject* ConnectionRefusedException;
    PyObject* CorruptedRecord;
    PyObject* Disconnected;
    PyObject* DisconnectedException;
    PyObject* DuplicateLogonException;
    PyObject* InvalidBookmarkException;
    PyObject* InvalidMessageTypeOptions;
    PyObject* InvalidOptionsException;
    PyObject* InvalidOrderByException;
    PyObject* InvalidSubIdException;
    PyObject* InvalidTopicError;
    PyObject* InvalidTopicException;
    PyObject* InvalidTransportOptions;
    PyObject* InvalidTransportOptionsException;
    PyObject* InvalidUriException;
    PyObject* InvalidUriFormat;
    PyObject* LocalStorageError;
    PyObject* LogonRequiredException;
    PyObject* MessageTypeError;
    PyObject* MessageTypeException;
    PyObject* MessageTypeNotFound;
    PyObject* MissingFieldsException;
    PyObject* NameInUseException;
    PyObject* NotEntitledError;
    PyObject* NotEntitledException;
    PyObject* PublishException;
    PyObject* PublishStoreGapException;
    PyObject* RetryOperation;
    PyObject* RetryOperationException;
    PyObject* StoreError;
    PyObject* StoreException;
    PyObject* StreamError;
    PyObject* StreamException;
    PyObject* SubscriptionAlreadyExists;
    PyObject* SubscriptionAlreadyExistsException;
    PyObject* SubidInUseException;
    PyObject* TimedOut;
    PyObject* TimedOutException;
    PyObject* TransportError;
    PyObject* TransportException;
    PyObject* TransportNotFound;
    PyObject* TransportTypeException;
    PyObject* UnknownError;
    PyObject* UnknownException;
    PyObject* UsageException;

    static const char* AMPSException_doc = \
                                           "The base exception class for all exceptions in the AMPS Python Client.";
    static const char* AlreadyConnectedException_doc = \
                                                       "The `AlreadyConnectedException` is raised when a client attempts "
                                                       "multiple connections to an AMPS instance after being successfully "
                                                       "connected.";
    static const char* AlreadyConnected_doc = "deprecated - use :exc:`AlreadyConnectedException`";
    static const char* AuthenticationError_doc = "deprecated - use :exc:`AuthenticationException`";
    static const char* AuthenticationException_doc = \
                                                     "The `AuthenticationException` is raised when the credentials provided "
                                                     "to the client fail in AMPS authentication.";

    static const char* BadFilterException_doc = \
                                                "The `BadFilterException` is raised when a query contains invalid "
                                                "content or is not used against a valid topic or field.";
    static const char* BadFilter_doc = "deprecated - use :exc:`BadFilterException`";
    static const char* BadRegexTopicException_doc = \
                                                    "The `BadRegexTopicException` is raised when a topic query containing a "
                                                    "regular expression is unable to be compiled by the AMPS regular expression "
                                                    "compiler.";
    static const char* BadRegexTopic_doc = "deprecated - use :exc:`BadRegexTopicException`";
    static const char* BadSowKeyException_doc = \
                                                "The `BadSowKeyException` is raised when command uses an invalid SOW key.";

    static const char* ClientNameInUse_doc = "deprecated - use :exc:`NameInUseException`";
    static const char* CommandError_doc = "deprecated - use :exc:`CommandException`";
    static const char* CommandException_doc = \
                                              "The `CommandException` is raised when a Command is used in an improper "
                                              "or unrecognized manner.";
    static const char* CommandTimedOut_doc = "deprecated - legacy exception";
    static const char* CommandTypeError_doc = "deprecated - use :exc:`CommandException`";
    static const char* ConnectionError_doc = "deprecated - use :exc:`ConnectionException`";
    static const char* ConnectionException_doc = \
                                                 "The `ConnectionException` is raised when the client is unable to connect to AMPS.";
    static const char* ConnectionRefusedException_doc =
      "The `ConnectionRefusedException` is raised when the connection to AMPS "
      "is refused due to a socket error.";
    static const char* ConnectionRefused_doc = "deprecated - use :exc:`ConnectionRefusedException`";
    static const char* CorruptedRecord_doc = "deprecated - legacy exception";

    static const char* DisconnectedException_doc = \
                                                   "The `DisconnectedException` is raised when an operation is requested by "
                                                   "the client, but either a connection has yet to be established or the client "
                                                   "was disconnected.";
    static const char* Disconnected_doc = "deprecated - use :exc:`DisconnectedException`";
    static const char* DuplicateLogonException_doc = \
                                                     "The `DuplicateLogonException` is raised when a client is trying to logon "
                                                     "after already logging on.";
    static const char* InvalidBookmarkException_doc = \
                                                      "The `InvalidBookmarkException` is raised when a client uses an invalid bookmark.";
    static const char* InvalidMessageTypeOptions_doc = "deprecated - use :exc:`MessageTypeException`";
    static const char* InvalidOptionsException_doc = \
                                                     "The `InvalidOptionsException` is raised when a client uses an invalid options.";
    static const char* InvalidOrderByException_doc = \
                                                     "The `InvalidOrderByException` is raised when a client uses an invalid orderby clause.";
    static const char* InvalidSubIdException_doc = \
                                                   "The `InvalidSubIdException` is raised when a client uses an invalid subid.";
    static const char* InvalidTopicError_doc = "deprecated - use :exc:`InvalidTopicException`";
    static const char* InvalidTopicException_doc = \
                                                   "The `InvalidTopicException` is raised when a query is performed against "
                                                   "a topic that does not exist.";

    static const char* InvalidTransportOptionsException_doc = \
                                                              "The `InvalidTransportOptionsException` is raised when a URI "
                                                              "string contains invalid options for a given transport.";
    static const char* InvalidTransportOptions_doc = "deprecated - use :exc:`InvalidTransportOptionsException`";
    static const char* InvalidUriException_doc = \
                                                 "The `InvalidUriException` is raised when the format of the URI"
                                                 " is invalid.";
    static const char* InvalidUriFormat_doc = "deprecated - use :exc:`InvalidUriException`";

    static const char* LocalStorageError_doc = "deprecated - legacy exception";
    static const char* LogonRequiredException_doc = \
                                                    "The `LogonRequiredException` is raised when a client attempts to execute a "
                                                    "command before calling logon.";

    static const char* MessageTypeError_doc = "deprecated - use :exc:`MessageTypeException`";
    static const char* MessageTypeException_doc = \
                                                  "The `MessageTypeException` is raised when the message type requested by the "
                                                  "client is unsupported.";
    static const char* MessageTypeNotFound_doc = "deprecated - use :exc:`MessageTypeException`";
    static const char* MissingFieldsException_doc = \
                                                    "The `MissingFieldsException` is raised when a client attempts to execute a "
                                                    "command and required fields are missing.";

    static const char* NameInUseException_doc = \
                                                "The `NameInUseException` is raised when a client attempts to connect and "
                                                "uses the same client name as a currently connected client.";
    static const char* NotEntitledError_doc = "deprecated - use :exc:`NotEntitledException`";
    static const char* NotEntitledException_doc = \
                                                  "The `NotEntitledException` is raised when an authenticated client attempts "
                                                  "to access a resource to which the user has not been granted proper "
                                                  "entitlements.";
    static const char* PublishException_doc = \
                                              "The `PublishException` is raised when a client attempts to publish an "
                                              "invalid message or some other error occurs with the message.";
    static const char* PublishStoreGapException_doc = "The `PublishStoreGapException` is raised when an exception is thrown by the "
                                              "underlying publish store because the client is attempting to logon to a server that "
                                              "appears to be missing messages from this client that are no longer in the publish store.";

    static const char* RetryOperationException_doc = \
                                                     "The `RetryOperationException` is raised when sending of a message has "
                                                     "failed two consecutive attempts. Any sender which receives this can assume "
                                                     "that the message was not delivered to AMPS.";
    static const char* RetryOperation_doc = "deprecated - use :exc:`RetryOperationException`";

    static const char* StoreError_doc = "";
    static const char* StoreException_doc = "The `StoreException` is raised when an exception is thrown by the underlying publish store.";
    static const char* StreamError_doc = "deprecated - use :exc:`StreamException`";
    static const char* StreamException_doc = \
                                             "The `StreamException` is raised when an incoming message is improperly formatted.";
    static const char* SubscriptionAlreadyExistsException_doc = \
                                                                "The `SubscriptionAlreadyExistsException` is raised when a subscription "
                                                                "is placed which matches a subscription that already exists.";
    static const char* SubscriptionAlreadyExists_doc = "deprecated - use :exc:`SubscriptionAlreadyExistsException`";
    static const char* SubidInUseException_doc = \
                                                 "The `SubidInUseException` is raised when a subscription "
                                                 "is placed with the same subscription ID.";
    static const char* TimedOutException_doc = \
                                               "The `TimedOutException` is raised when an operation times out.";
    static const char* TimedOut_doc = "deprecated - use :exc:`TimedOutException`";
    static const char* TransportError_doc = "deprecated - use :exc:`TransportException`";
    static const char* TransportException_doc = \
                                                "The `TransportException` is raised when an AMPS Client transport has an error.";
    static const char* TransportNotFound_doc = "deprecated - use :exc:`TransportException`";
    static const char* TransportTypeException_doc = \
                                                    "The `TransportTypeException` is raised when a Client is unable to connect to a transport.";

    static const char* UnknownError_doc = "deprecated - use :exc:`UnknownException`";
    static const char* UnknownException_doc = \
                                              "The `UnknownException` is raised when the AMPS Python Client is in an "
                                              "unrecoverable state.";
    static const char* UsageException_doc = "The `UsageException` is raised when an attempt is made to incorrectly use "
                                            "an object or function, such as setting ack timeout to 0 when the ack batch "
                                            "size is > 1.";


#if PY_VERSION_HEX < 0x02070000
    /* lifted directly from Python 2.7.5 ... create an exception with docstring */
    PyObject*
    PyErr_NewExceptionWithDoc(char* name, char* doc, PyObject* base, PyObject* dict)
    {
      int result;
      PyObject* ret = NULL;
      PyObject* mydict = NULL; /* points to the dict only if we create it */
      PyObject* docobj;

      if (dict == NULL)
      {
        dict = mydict = PyDict_New();
        if (dict == NULL)
        {
          return NULL;
        }
      }

      if (doc != NULL)
      {
        docobj = PyString_FromString(doc);
        if (docobj == NULL)
        {
          goto failure;
        }
        result = PyDict_SetItemString(dict, "__doc__", docobj);
        Py_DECREF(docobj);
        if (result < 0)
        {
          goto failure;
        }
      }

      ret = PyErr_NewException(name, base, dict);
failure:
      Py_XDECREF(mydict);
      return ret;
    }
#endif

#define STRINGIFY(x) #x

#define STRINGIFYX(x) STRINGIFY(x)

    void init(PyObject* module)
    {
      const char* version = AMPS_PYTHON_VERSION;
      PyModule_AddStringConstant(module, "VERSION", version);
      AMPSException = PyErr_NewExceptionWithDoc((char*)"AMPS.AMPSException", (char*)AMPSException_doc, NULL, NULL);
      PyModule_AddObject(module, (char*)"AMPSException", AMPSException);
      StoreError = PyErr_NewExceptionWithDoc((char*)"AMPS.StoreError", (char*)StoreError_doc, AMPSException, NULL);
      PyModule_AddObject(module, (char*)"StoreError", StoreError);
      StoreException = PyErr_NewExceptionWithDoc((char*)"AMPS.StoreException", (char*)StoreException_doc, StoreError, NULL);
      PyModule_AddObject(module, (char*)"StoreException", StoreException);
      PublishStoreGapException = PyErr_NewExceptionWithDoc((char*)"AMPS.PublishStoreGapException", (char*)PublishStoreGapException_doc, StoreException, NULL);
      PyModule_AddObject(module, (char*)"PublishStoreGapException", PublishStoreGapException);
      LocalStorageError = PyErr_NewExceptionWithDoc((char*)"AMPS.LocalStorageError", (char*)LocalStorageError_doc, AMPSException, NULL);
      PyModule_AddObject(module, (char*)"LocalStorageError", LocalStorageError);
      CorruptedRecord = PyErr_NewExceptionWithDoc((char*)"AMPS.CorruptedRecord", (char*)CorruptedRecord_doc, LocalStorageError, NULL);
      PyModule_AddObject(module, (char*)"CorruptedRecord", CorruptedRecord);
      ConnectionError = PyErr_NewExceptionWithDoc((char*)"AMPS.ConnectionError", (char*)ConnectionError_doc, AMPSException, NULL);
      PyModule_AddObject(module, (char*)"ConnectionError", ConnectionError);
      ConnectionException = PyErr_NewExceptionWithDoc((char*)"AMPS.ConnectionException", (char*)ConnectionException_doc, ConnectionError, NULL);
      PyModule_AddObject(module, (char*)"ConnectionException", ConnectionException);
      TransportTypeException = PyErr_NewExceptionWithDoc((char*)"AMPS.TransportTypeException", (char*)TransportTypeException_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"TransportTypeException", TransportTypeException);
      TransportError = PyErr_NewExceptionWithDoc((char*)"AMPS.TransportError", (char*)TransportError_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"TransportError", TransportError);
      TransportException = PyErr_NewExceptionWithDoc((char*)"AMPS.TransportException", (char*)TransportException_doc, TransportError, NULL);
      PyModule_AddObject(module, (char*)"TransportException", TransportException);
      InvalidTransportOptions = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidTransportOptions", (char*)InvalidTransportOptions_doc, TransportException, NULL);
      PyModule_AddObject(module, (char*)"InvalidTransportOptions", InvalidTransportOptions);
      InvalidTransportOptionsException = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidTransportOptionsException", (char*)InvalidTransportOptionsException_doc, InvalidTransportOptions, NULL);
      PyModule_AddObject(module, (char*)"InvalidTransportOptionsException", InvalidTransportOptionsException);
      TransportNotFound = PyErr_NewExceptionWithDoc((char*)"AMPS.TransportNotFound", (char*)TransportNotFound_doc, TransportException, NULL);
      PyModule_AddObject(module, (char*)"TransportNotFound", TransportNotFound);
      TimedOut = PyErr_NewExceptionWithDoc((char*)"AMPS.TimedOut", (char*)TimedOut_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"TimedOut", TimedOut);
      TimedOutException = PyErr_NewExceptionWithDoc((char*)"AMPS.TimedOutException", (char*)TimedOutException_doc, TimedOut, NULL);
      PyModule_AddObject(module, (char*)"TimedOutException", TimedOutException);
      StreamError = PyErr_NewExceptionWithDoc((char*)"AMPS.StreamError", (char*)StreamError_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"StreamError", StreamError);
      StreamException = PyErr_NewExceptionWithDoc((char*)"AMPS.StreamException", (char*)StreamException_doc, StreamError, NULL);
      PyModule_AddObject(module, (char*)"StreamException", StreamException);
      RetryOperation = PyErr_NewExceptionWithDoc((char*)"AMPS.RetryOperation", (char*)RetryOperation_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"RetryOperation", RetryOperation);
      RetryOperationException = PyErr_NewExceptionWithDoc((char*)"AMPS.RetryOperationException", (char*)RetryOperationException_doc, RetryOperation, NULL);
      PyModule_AddObject(module, (char*)"RetryOperationException", RetryOperationException);
      NotEntitledError = PyErr_NewExceptionWithDoc((char*)"AMPS.NotEntitledError", (char*)NotEntitledError_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"NotEntitledError", NotEntitledError);
      NotEntitledException = PyErr_NewExceptionWithDoc((char*)"AMPS.NotEntitledException", (char*)NotEntitledException_doc, NotEntitledError, NULL);
      PyModule_AddObject(module, (char*)"NotEntitledException", NotEntitledException);
      MessageTypeError = PyErr_NewExceptionWithDoc((char*)"AMPS.MessageTypeError", (char*)MessageTypeError_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"MessageTypeError", MessageTypeError);
      MessageTypeException = PyErr_NewExceptionWithDoc((char*)"AMPS.MessageTypeException", (char*)MessageTypeException_doc, MessageTypeError, NULL);
      PyModule_AddObject(module, (char*)"MessageTypeException", MessageTypeException);
      InvalidMessageTypeOptions = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidMessageTypeOptions", (char*)InvalidMessageTypeOptions_doc, MessageTypeException, NULL);
      PyModule_AddObject(module, (char*)"InvalidMessageTypeOptions", InvalidMessageTypeOptions);
      MessageTypeNotFound = PyErr_NewExceptionWithDoc((char*)"AMPS.MessageTypeNotFound", (char*)MessageTypeNotFound_doc, MessageTypeException, NULL);
      PyModule_AddObject(module, (char*)"MessageTypeNotFound", MessageTypeNotFound);
      InvalidUriFormat = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidUriFormat", (char*)InvalidUriFormat_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"InvalidUriFormat", InvalidUriFormat);
      InvalidUriException = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidUriException", (char*)InvalidUriException_doc, InvalidUriFormat, NULL);
      PyModule_AddObject(module, (char*)"InvalidUriException", InvalidUriException);
      Disconnected = PyErr_NewExceptionWithDoc((char*)"AMPS.Disconnected", (char*)Disconnected_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"Disconnected", Disconnected);
      DisconnectedException = PyErr_NewExceptionWithDoc((char*)"AMPS.DisconnectedException", (char*)DisconnectedException_doc, Disconnected, NULL);
      PyModule_AddObject(module, (char*)"DisconnectedException", DisconnectedException);
      ClientNameInUse = PyErr_NewExceptionWithDoc((char*)"AMPS.ClientNameInUse", (char*)ClientNameInUse_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"ClientNameInUse", ClientNameInUse);
      NameInUseException = PyErr_NewExceptionWithDoc((char*)"AMPS.NameInUseException", (char*)NameInUseException_doc, ClientNameInUse, NULL);
      PyModule_AddObject(module, (char*)"NameInUseException", NameInUseException);
      ConnectionRefused = PyErr_NewExceptionWithDoc((char*)"AMPS.ConnectionRefused", (char*)ConnectionRefused_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"ConnectionRefused", ConnectionRefused);
      ConnectionRefusedException = PyErr_NewExceptionWithDoc((char*)"AMPS.ConnectionRefusedException", (char*)ConnectionRefusedException_doc, ConnectionRefused, NULL);
      PyModule_AddObject(module, (char*)"ConnectionRefusedException", ConnectionRefusedException);
      AuthenticationError = PyErr_NewExceptionWithDoc((char*)"AMPS.AuthenticationError", (char*)AuthenticationError_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"AuthenticationError", AuthenticationError);
      AuthenticationException = PyErr_NewExceptionWithDoc((char*)"AMPS.AuthenticationException", (char*)AuthenticationException_doc, AuthenticationError, NULL);
      PyModule_AddObject(module, (char*)"AuthenticationException", AuthenticationException);
      AlreadyConnected = PyErr_NewExceptionWithDoc((char*)"AMPS.AlreadyConnected", (char*)AlreadyConnected_doc, ConnectionException, NULL);
      PyModule_AddObject(module, (char*)"AlreadyConnected", AlreadyConnected);
      AlreadyConnectedException = PyErr_NewExceptionWithDoc((char*)"AMPS.AlreadyConnectedException", (char*)AlreadyConnectedException_doc, AlreadyConnected, NULL);
      PyModule_AddObject(module, (char*)"AlreadyConnectedException", AlreadyConnectedException);
      CommandError = PyErr_NewExceptionWithDoc((char*)"AMPS.CommandError", (char*)CommandError_doc, AMPSException, NULL);
      PyModule_AddObject(module, (char*)"CommandError", CommandError);
      CommandException = PyErr_NewExceptionWithDoc((char*)"AMPS.CommandException", (char*)CommandException_doc, CommandError, NULL);
      PyModule_AddObject(module, (char*)"CommandException", CommandException);
      UnknownError = PyErr_NewExceptionWithDoc((char*)"AMPS.UnknownError", (char*)UnknownError_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"UnknownError", UnknownError);
      UnknownException = PyErr_NewExceptionWithDoc((char*)"AMPS.UnknownException", (char*)UnknownException_doc, UnknownError, NULL);
      PyModule_AddObject(module, (char*)"UnknownException", UnknownException);
      SubscriptionAlreadyExists = PyErr_NewExceptionWithDoc((char*)"AMPS.SubscriptionAlreadyExists", (char*)SubscriptionAlreadyExists_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"SubscriptionAlreadyExists", SubscriptionAlreadyExists);
      SubscriptionAlreadyExistsException = PyErr_NewExceptionWithDoc((char*)"AMPS.SubscriptionAlreadyExistsException", (char*)SubscriptionAlreadyExistsException_doc, SubscriptionAlreadyExists, NULL);
      PyModule_AddObject(module, (char*)"SubscriptionAlreadyExistsException", SubscriptionAlreadyExistsException);
      CommandTypeError = PyErr_NewExceptionWithDoc((char*)"AMPS.CommandTypeError", (char*)CommandTypeError_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"CommandTypeError", CommandTypeError);
      CommandTimedOut = PyErr_NewExceptionWithDoc((char*)"AMPS.CommandTimedOut", (char*)CommandTimedOut_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"CommandTimedOut", CommandTimedOut);
      InvalidTopicError = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidTopicError", (char*)InvalidTopicError_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"InvalidTopicError", InvalidTopicError);
      InvalidTopicException = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidTopicException", (char*)InvalidTopicException_doc, InvalidTopicError, NULL);
      PyModule_AddObject(module, (char*)"InvalidTopicException", InvalidTopicException);
      BadRegexTopic = PyErr_NewExceptionWithDoc((char*)"AMPS.BadRegexTopic", (char*)BadRegexTopic_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"BadRegexTopic", BadRegexTopic);
      BadRegexTopicException = PyErr_NewExceptionWithDoc((char*)"AMPS.BadRegexTopicException", (char*)BadRegexTopicException_doc, BadRegexTopic, NULL);
      PyModule_AddObject(module, (char*)"BadRegexTopicException", BadRegexTopicException);
      BadFilter = PyErr_NewExceptionWithDoc((char*)"AMPS.BadFilter", (char*)BadFilter_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"BadFilter", BadFilter);
      BadFilterException = PyErr_NewExceptionWithDoc((char*)"AMPS.BadFilterException", (char*)BadFilterException_doc, BadFilter, NULL);
      PyModule_AddObject(module, (char*)"BadFilterException", BadFilterException);
      SubidInUseException = PyErr_NewExceptionWithDoc((char*)"AMPS.SubidInUseException", (char*)SubidInUseException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"SubidInUseException", SubidInUseException);
      BadSowKeyException = PyErr_NewExceptionWithDoc((char*)"AMPS.BadSowKeyException", (char*)BadSowKeyException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"BadSowKeyException", BadSowKeyException);
      DuplicateLogonException = PyErr_NewExceptionWithDoc((char*)"AMPS.DuplicateLogonException", (char*)DuplicateLogonException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"DuplicateLogonException", DuplicateLogonException);
      InvalidBookmarkException = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidBookmarkException", (char*)InvalidBookmarkException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"InvalidBookmarkException", InvalidBookmarkException);
      InvalidOptionsException = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidOptionsException", (char*)InvalidOptionsException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"InvalidOptionsException", InvalidOptionsException);
      InvalidOrderByException = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidOrderByException", (char*)InvalidOrderByException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"InvalidOrderByException", InvalidOrderByException);
      InvalidSubIdException = PyErr_NewExceptionWithDoc((char*)"AMPS.InvalidSubIdException", (char*)InvalidSubIdException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"InvalidSubIdException", InvalidSubIdException);
      LogonRequiredException = PyErr_NewExceptionWithDoc((char*)"AMPS.LogonRequiredException", (char*)LogonRequiredException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"LogonRequiredException", LogonRequiredException);
      MissingFieldsException = PyErr_NewExceptionWithDoc((char*)"AMPS.MissingFieldsException", (char*)MissingFieldsException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"MissingFieldsException", MissingFieldsException);
      PublishException = PyErr_NewExceptionWithDoc((char*)"AMPS.PublishException", (char*)PublishException_doc, CommandException, NULL);
      PyModule_AddObject(module, (char*)"PublishException", PublishException);
      UsageException = PyErr_NewExceptionWithDoc((char*)"AMPS.UsageException", (char*)UsageException_doc, AMPSException, NULL);
      PyModule_AddObject(module, (char*)"UsageException", UsageException);

    }

    std::string getExceptionStr(bool includeExceptionName = false)
    {
      std::string retval;
      PyObject* ptype, *pvalue, *ptraceback;
      PyErr_Fetch(&ptype, &pvalue, &ptraceback);
      Py_XDECREF(ptype);
      Py_XDECREF(ptraceback);

      if (includeExceptionName && ptype)
      {
        PyObject* exTypeStr = PyObject_Str(ptype);
        retval.append("Unexpected Python error occurred of type ");
        retval.append(shims::type_name((PyTypeObject*)ptype));
        retval.append(": ");
        Py_XDECREF(exTypeStr);
      }
      PyObject* strVal = PyObject_Str(pvalue);
      retval.append(PyString_AsString(strVal));
      Py_XDECREF(strVal);
      Py_XDECREF(pvalue);
      return retval;
    }
    AMPSDLL void throwError()
    {
      if (!ampspy::shims::Py_IsFinalizing())
      {
        PyErr_CheckSignals();
        if (PyErr_Occurred())
        {
          throw PyException();
        }
      }
    }

  } // namespace ampspy::exc
  AMPSDLL void unhandled_exception()
  {
    // not looking to print anything, but when the exception type
    // is SystemException, "printing" it in this fashion will trigger
    // the interpreter shutdown we're looking for.
    PyErr_PrintEx(0);
  }
  bool _is_signaled = false;

  // SSL related section
  bool _ssl_is_initialized = false;

#if PY_MAJOR_VERSION >= 3
  // Python provided SSL things we hold onto
  PyObject* _ampspy_ssl_module = NULL;
  PyObject* _ampspy__ssl_module = NULL;
  PyObject* _ampspy_socket_module = NULL;
  PyObject* _ampspy__socket_module = NULL;
  PyObject* _ampspy_ssl_context = NULL;
  PyObject* _ampspy_sslcontext_class = NULL;
  // Holder for the tcps version if we can't get Python to work
  _amps_SSL* (*_ampspy_get_socket_and_ssl)(AMPS_SOCKET,
                                           const char* address_, int port_,
                                           struct addrinfo*, char*, void*);
  // Storage for our Python objects related to each connection
  std::map<_amps_SSL*, std::pair<PyObject*, PyObject*> > _ampspy_ssl_object_map;
  AMPS::Mutex _ampspy_ssl_map_lock;

  // Get the ssl.SSLSocket based on the C lib SSL*. Used in client.
  AMPSDLL PyObject* ampspy_get_PySSLSocket_from_SSL(_amps_SSL* ssl_)
  {
    if (!ssl_)
    {
      Py_INCREF(Py_None);
      return Py_None;
    }
    AMPS::Lock<AMPS::Mutex> guard(_ampspy_ssl_map_lock);
    auto iter = _ampspy_ssl_object_map.find((_amps_SSL*)ssl_);
    if (iter != _ampspy_ssl_object_map.end())
    {
      PyObject* pySSLSocket = iter->second.first;
      Py_INCREF(pySSLSocket);
      return pySSLSocket;
    }
    Py_INCREF(Py_None);
    return Py_None;
  }

  // Remove all our module/type references
  AMPSDLL void _ampspy_ssl_cleanup(void)
  {
    Py_XDECREF(_ampspy_sslcontext_class);
    _ampspy_sslcontext_class = NULL;
    Py_XDECREF(_ampspy_ssl_context);
    _ampspy_ssl_context = NULL;
    Py_XDECREF(_ampspy_socket_module);
    _ampspy_socket_module = NULL;
    Py_XDECREF(_ampspy__socket_module);
    _ampspy__socket_module = NULL;
    Py_XDECREF(_ampspy__ssl_module);
    _ampspy__ssl_module = NULL;
    Py_XDECREF(_ampspy_ssl_module);
    _ampspy_ssl_module = NULL;
  }
#endif // Python 3+ only

  // Init everything to just use the C lib and not have Python objects
  int ssl_init_c_lib(const char* dll_name)
  {
    int rc = amps_ssl_init(dll_name);
    if (rc && !dll_name)
    {
#if PY_MAJOR_VERSION >= 3
      if (!_ampspy_ssl_module)
      {
        // Try to load the Python ssl module, and see if we can use it.
        _ampspy_ssl_module = PyImport_ImportModule("ssl");
        if (!_ampspy_ssl_module)
        {
          PyErr_SetString(ampspy::exc::ConnectionException,
                          "No SSL module found or specified.");
          return rc;
        }
      }
#else
      // Try to load the Python ssl module, and see if we can use it.
      PyObject* _ampspy_ssl_module = PyImport_ImportModule("ssl");
      if (!_ampspy_ssl_module)
      {
        PyErr_SetString(ampspy::exc::ConnectionException,
                        "No SSL module found or specified.");
        return rc;
      }
#endif

      // Does it have a "_ssl" attribute?
      PyObject* ssl_internal_module = PyObject_GetAttrString(_ampspy_ssl_module,
                                                             "_ssl");
      if (!ssl_internal_module)
      {
#if PY_MAJOR_VERSION < 3
        Py_DECREF(_ampspy_ssl_module);
#endif
        PyErr_SetString(ampspy::exc::ConnectionException,
                        "No _SSL module found or specified.");
        return rc;
      }

      // It does, let's get its file name
      PyObject* ssl_internal_filename =
        PyObject_GetAttrString(ssl_internal_module, "__file__");
      Py_DECREF(ssl_internal_module);
      if (!(ssl_internal_filename && PyString_Check(ssl_internal_filename)))
      {
        Py_XDECREF(ssl_internal_filename);
#if PY_MAJOR_VERSION < 3
        Py_DECREF(_ampspy_ssl_module);
#endif
        PyErr_SetString(ampspy::exc::ConnectionException,
                        "No SSL module filename found.");
        return rc;
      }
      dll_name = PyString_AsString(ssl_internal_filename);
#if PY_MAJOR_VERSION < 3
      Py_DECREF(_ampspy_ssl_module);
#endif
      rc = amps_ssl_init(dll_name);
      Py_DECREF(ssl_internal_filename);
    }
    _ssl_is_initialized = (rc == 0);
    return rc;
  }

#if PY_MAJOR_VERSION >= 3
  int getMinorVersion()
  {
    static int pyMinor = 0;
    if (pyMinor == 0)
    {
      const char* pyVer = Py_GetVersion();
      for (size_t i=2; pyVer[i] >= '0' && pyVer[i] <= '9'; ++i)
      {
        pyMinor *= 10;
        pyMinor += (int)pyVer[i] - (int)'0';
      }
    }
    return pyMinor;
  }

  void setErrAsPyErr(void* me_)
  {
    if (getMinorVersion() < 12)
    {
      PyObject *exc_type, *exc_value, *exc_tb;
      PyErr_Fetch(&exc_type, &exc_value, &exc_tb); // < 3.12

      if (exc_type != NULL)
      {
        PyObject *exc_name = PyObject_GetAttrString(exc_type, "__name__");
        PyObject *exc_str = PyObject_Str(exc_value);

        if (exc_name != NULL && exc_str != NULL)
        {
          const char* name = ampspy::shims::PyUnicode_AsUTF8(exc_name);
          const char* str = ampspy::shims::PyUnicode_AsUTF8(exc_str);
          static char errBuf[1024];
          _AMPS_SNPRINTF(errBuf, sizeof(errBuf), "Python Exception %s: %s", name, str);
          amps_tcps_set_external_error(me_, errBuf);
          Py_DECREF(exc_name);
          Py_DECREF(exc_str);
        }
      }
      Py_XDECREF(exc_type);
      Py_XDECREF(exc_value);
      Py_XDECREF(exc_tb);
    }
    else
    { // Python 3.12+
      PyObject* exc = ampspy::shims::PyErr_GetRaisedException();
      if (exc)
      {
        PyObject* excStr = PyObject_Str(exc);
        if (excStr)
        {
          const char* errStr = PyString_AsString(excStr);
          static char errBuf[1024];
          _AMPS_SNPRINTF(errBuf, sizeof(errBuf), "Python Exception %s", errStr);
          amps_tcps_set_external_error(me_, errBuf);
          Py_DECREF(excStr);
        }
        Py_DECREF(exc);
      }

      PyErr_Clear(); // This should be unnecessary as Fetch/GetRaised does it
    }
  }

  // We use the following truncated struct definition to grab
  // otherwise inaccessible members that we need.
  // typedef struct {
  //     PyObject_HEAD
  //     PyObject *Socket; /* weakref to socket on which we're layered */
  //     SSL *ssl;
  // ...
  // } PySSLSocket;
  typedef struct
  {
    PyObject_HEAD
    PyObject *pPySocket; /* weakref to socket on which we're layered */
    _amps_SSL *ssl;
  } ampspy_PySSLSocket;

  // Create a conencted Python ssl.SSLSocket wrapping the given fd_, connected
  // to address_:port_, possibly using sni for hostname_
  AMPSDLL _amps_SSL* _ampspy_SSL_new_wrapped_socket(AMPS_SOCKET fd_,
                                                    const char* address_, int port_,
                                                    struct addrinfo* pAddrInfo_,
                                                    char* hostname_, void* me_)
  {
    LOCKGIL;
    if (!_ampspy_ssl_context)
    {
      ssl_init_internal(NULL, NULL);
      if (!_ampspy_ssl_context)
      {
        amps_tcps_set_external_error(me_, "Failed to initialize SSL and get a context");
        return NULL;
      }
    }
    if (!_ampspy_socket_module)
    {
      _ampspy_socket_module = PyImport_ImportModule("socket");
      if (!_ampspy_socket_module)
      {
        amps_tcps_set_external_error(me_, "Failed to load Python socket module");
        return _ampspy_get_socket_and_ssl(fd_, address_, port_, pAddrInfo_, hostname_, me_);
      }
    }
    PyObject* pySockType = PyObject_GetAttrString(_ampspy_socket_module, "socket");
    if (!pySockType)
    {
      amps_tcps_set_external_error(me_, "Failed to load Python socket type");
      Py_DECREF(_ampspy_socket_module);
      _ampspy_socket_module = NULL;
      return _ampspy_get_socket_and_ssl(fd_, address_, port_, pAddrInfo_, hostname_, me_);
    }
    PyObject* pyFd = NULL;
    if (sizeof(fd_) == 8)
    {
      pyFd = PyLong_FromLongLong((long long)fd_);
    }
    else
    {
      pyFd = PyLong_FromLong((long)fd_);
    }
    // We'll only use keyword arguments
    PyObject* args = PyTuple_New(0);
    PyObject* kwargs = PyDict_New();
    PyObject* pyArg = NULL;
    switch (pAddrInfo_->ai_family)
    {
    case AF_INET:
    {
      pyArg = PyObject_GetAttrString(_ampspy_socket_module, "AF_INET");
    }
    break;
    case AF_INET6:
    {
      pyArg = PyObject_GetAttrString(_ampspy_socket_module, "AF_INET6");
    }
    break;
    case AF_UNIX:
    {
      pyArg = PyObject_GetAttrString(_ampspy_socket_module, "AF_UNIX");
    }
    break;
    default:
    {
      pyArg = PyLong_FromLong((long)pAddrInfo_->ai_family);
    }
    }
    PyDict_SetItemString(kwargs, "family", pyArg);
    PyObject* pyProto = NULL;
    if (pAddrInfo_->ai_protocol)
    {
      pyProto = PyLong_FromLong((long)pAddrInfo_->ai_protocol);
      PyDict_SetItemString(kwargs, "proto", pyProto);
    }
    PyDict_SetItemString(kwargs, "fileno", pyFd);
    PyObject* pySocket = PyObject_Call(pySockType, args, kwargs);
    if (!pySocket)
    {
      if (PyErr_Occurred())
      {
        setErrAsPyErr(me_);
      }
      else
      {
        amps_tcps_set_external_error(me_, "Failed to create Python socket");
      }
      Py_XDECREF(pyProto);
      Py_DECREF(pySockType);
      Py_DECREF(args);
      Py_XDECREF(pyArg);
      Py_DECREF(kwargs);
      return _ampspy_get_socket_and_ssl(fd_, address_, port_, pAddrInfo_, hostname_, me_);
    }
    PyObject* pySSLSocket = NULL;
    PyObject* pyWrapSocket = PyString_FromString("wrap_socket");
    if (hostname_)
    {
      // We're using sni, so we need to set a few things
      PyObject_SetAttrString(_ampspy_ssl_context, "check_hostname", Py_True);
      PyObject* pyVm = PyObject_GetAttrString(_ampspy_ssl_module, "VerifyMode");
      PyObject* pyVerifyMode = PyObject_GetAttrString(pyVm, "CERT_REQUIRED");
      PyObject_SetAttrString(_ampspy_ssl_context, "verify_mode", pyVerifyMode);
      Py_XDECREF(pyVm);
      Py_XDECREF(pyVerifyMode);

      pySSLSocket = PyObject_CallMethodObjArgs(_ampspy_ssl_context,
                                               pyWrapSocket,
                                               pySocket, Py_False, Py_True,
                                               Py_True,
                                               PyString_FromString(hostname_),
                                               NULL);
    }
    else
    {
      pySSLSocket = PyObject_CallMethodObjArgs(_ampspy_ssl_context,
                                               pyWrapSocket,
                                               pySocket, Py_False, NULL);
    }
    Py_DECREF(pyWrapSocket);
    if (!pySSLSocket)
    {
      if (PyErr_Occurred())
      {
        setErrAsPyErr(me_);
      }
      else
      {
        amps_tcps_set_external_error(me_, "Failed to create Python SSLSocket");
      }
      Py_DECREF(pySockType);
      Py_DECREF(pySocket);
      Py_XDECREF(pyProto);
      Py_DECREF(args);
      Py_XDECREF(pyArg);
      Py_DECREF(kwargs);
      return _ampspy_get_socket_and_ssl(fd_, address_, port_, pAddrInfo_, hostname_, me_);
    }

    // connect the socket.socket
    PyObject* retVal = NULL;
    if (pAddrInfo_->ai_addr->sa_family == AF_INET)
    {
      retVal = PyObject_CallMethod(pySSLSocket, "connect", "((si))", address_, port_);
    }
    else if (pAddrInfo_->ai_addr->sa_family == AF_INET6)
    {
#ifdef _WIN32
      SOCKADDR_IN6* pAddr6 = (SOCKADDR_IN6*)(pAddrInfo_->ai_addr->sa_data);
#else
      sockaddr_in6* pAddr6 = (sockaddr_in6*)(pAddrInfo_->ai_addr->sa_data);
#endif
      retVal = PyObject_CallMethod(pySSLSocket, "connect", "((siii))", address_, port_,
                                   pAddr6->sin6_flowinfo, pAddr6->sin6_scope_id);
    }
    if (!retVal)
    {
      if (PyErr_Occurred())
      {
        setErrAsPyErr(me_);
      }
      else
      {
        amps_tcps_set_external_error(me_, "Failed to connect the Python ssl.SSLSocket");
      }

      // We're not going to use these
      Py_DECREF(pySSLSocket);
      Py_DECREF(pySocket);
      Py_DECREF(pySockType);
      Py_XDECREF(pyProto);
      Py_DECREF(args);
      Py_XDECREF(pyArg);
      Py_DECREF(kwargs);
      return NULL;
    }
    Py_DECREF(retVal);

    PyObject* pySSLSocketObj = PyObject_GetAttrString(pySSLSocket, "_sslobj");
    _amps_SSL* ssl = 0;
    if (getMinorVersion() > 6)
    {
      // The _sslobj is a PySSLSocket that is only present on a connected socket
      // Use our truncated struct to get the SSL*
      ampspy_PySSLSocket* sslSocket = (ampspy_PySSLSocket*)pySSLSocketObj;
      ssl = sslSocket->ssl;
    }
    else
    {
      // Python 3.6 _sslobj is an SSLObj wrapper with a PySSLSocket in _sslobj
      pySSLSocketObj = PyObject_GetAttrString(pySSLSocketObj, "_sslobj");
      // Use our truncated struct to get the SSL*
      ampspy_PySSLSocket* sslSocket = (ampspy_PySSLSocket*)pySSLSocketObj;
      ssl = sslSocket->ssl;
    }
    _amps_SSL_ctrl(ssl, AMPS_SSL_CTRL_MODE, AMPS_SSL_AUTO_RETRY, NULL);

    AMPS::Lock<AMPS::Mutex> guard(_ampspy_ssl_map_lock);
    _ampspy_ssl_object_map[ssl] = std::make_pair(pySSLSocket, pySocket);
    Py_XDECREF(pyProto);
    Py_DECREF(args);
    Py_XDECREF(pyArg);
    Py_DECREF(kwargs);
    Py_DECREF(pySSLSocketObj);
    Py_DECREF(pySockType);
    return ssl;
  }

  // Here is where we use Python to close the Python objects
  AMPSDLL int _ampspy_close_all(AMPS_SOCKET fd_, _amps_SSL* pSSL_)
  {
    if (!pSSL_)
    {
      assert(fd_ == AMPS_INVALID_SOCKET);
      if (fd_ != AMPS_INVALID_SOCKET)
      {
#ifdef _WIN32
        shutdown(fd_, SD_BOTH);
        closesocket(fd_);
#else
        shutdown(fd_, SHUT_RDWR);
        close(fd_);
#endif
      }
      return 0;
    }
    PyObject* pySSLSocket = NULL;
    PyObject* pySocket = NULL;
    {
      AMPS::Lock<AMPS::Mutex> guard(_ampspy_ssl_map_lock);
      auto iter = _ampspy_ssl_object_map.find(pSSL_);
      if (iter != _ampspy_ssl_object_map.end())
      {
        pySSLSocket = iter->second.first;
        pySocket = iter->second.second;
        _ampspy_ssl_object_map.erase(iter);
      }
    }
    if (pySSLSocket)
    {
      LOCKGIL;
      // Shutdown everything, then close the connection
      PyObject* arg = PyObject_GetAttrString(_ampspy_socket_module, "SHUT_RDWR");
      PyObject* shutdownStr = PyString_FromString("shutdown");
      PyObject* closeStr = PyString_FromString("close");
      PyObject_CallMethodObjArgs(pySSLSocket, shutdownStr, arg, NULL);
      PyObject_CallMethodObjArgs(pySSLSocket, closeStr, NULL);
      PyObject_SetAttrString(pySSLSocket, "_closed", Py_True);
      PyObject_SetAttrString(pySSLSocket, "connected", Py_False);
      Py_XDECREF(arg);
      Py_DECREF(shutdownStr);
      Py_DECREF(closeStr);
      Py_XDECREF(pySSLSocket);
      Py_XDECREF(pySocket);
    }
    else if (!_ampspy_socket_module)
    {
      // We didn't find python objects, must have been handled in C
      _amps_SSL_shutdown(pSSL_);
      _amps_SSL_free(pSSL_);
    }
    return 0;
  }

  // typedef struct {
  // PyObject_HEAD
  // SSL_CTX *ctx;
  // ...
  // } PySSLContext;
  // The SSL_CTX* is the first item after PyObject_HEAD
  typedef struct
  {
    PyObject_HEAD
    _amps_SSL_CTX *ctx;
  } ampspy_PySSLContext;

  AMPSDLL PyObject* ssl_init_internal(const char* dll_name, PyObject* pyCtx,
                                      bool strictCiphersOnly_)
  {
    if (_ssl_is_initialized)
    {
      Py_INCREF(Py_None);
      return Py_None;
    }

    // Are we being provided an ssl.SSLContext or do we need to create one?
    if (!pyCtx)
    {
      if (dll_name)
      {
        PyObject* modules = PyImport_GetModuleDict();
        PyObject* sslName = PyString_FromString("ssl");
        if (PyDict_Contains(modules, sslName) != 1)
        {
          Py_DECREF(sslName);
          if (ssl_init_c_lib(dll_name))
          {
            PyErr_SetString(ampspy::exc::ConnectionException,
                            "No SSL module found.");
            return NULL;
          }
          PyErr_Clear();
          Py_INCREF(Py_None);
          return Py_None;
        }
        Py_DECREF(sslName);
      }
      // Load the socket module
      if (!_ampspy_socket_module)
      {
        _ampspy_socket_module = PyImport_ImportModule("socket");
      }
      // Try to load the Python ssl module, and see if we can use it.
      if (!_ampspy_ssl_module)
      {
        _ampspy_ssl_module = PyImport_ImportModule("ssl");
        if (!_ampspy_ssl_module)
        {
          if (ssl_init_c_lib(dll_name))
          {
            PyErr_SetString(ampspy::exc::ConnectionException,
                            "No SSL module found.");
            return NULL;
          }
          PyErr_Clear();
          Py_INCREF(Py_None);
          return Py_None;
        }
      }

      if (!_ampspy__ssl_module)
      {
        _ampspy__ssl_module = PyImport_ImportModule("_ssl");
        if (!_ampspy__ssl_module)
        {
          if (ssl_init_c_lib(dll_name))
          {
            Py_DECREF(_ampspy_ssl_module);
            _ampspy_ssl_module = NULL;
            PyErr_SetString(ampspy::exc::ConnectionException,
                            "No _ssl module found.");
            return NULL;
          }
          PyErr_Clear();
          Py_INCREF(Py_None);
          return Py_None;
        }
      }

      // Get the SSLContext class
      if (!_ampspy_sslcontext_class)
      {
        _ampspy_sslcontext_class = PyObject_GetAttrString(_ampspy_ssl_module, "SSLContext");
        if (!_ampspy_sslcontext_class)
        {
          Py_DECREF(_ampspy_ssl_module);
          Py_DECREF(_ampspy__ssl_module);
          _ampspy_ssl_module = NULL;
          _ampspy__ssl_module = NULL;
          if (ssl_init_c_lib(dll_name))
          {
            PyErr_SetString(ampspy::exc::ConnectionException,
                            "No SSLContext in SSL module");
            return NULL;
          }
          PyErr_Clear();
          Py_INCREF(Py_None);
          return Py_None;
        }
      }

      PyObject* tlsClient = PyObject_GetAttrString(_ampspy_ssl_module, "PROTOCOL_TLS_CLIENT");
      if (!tlsClient)
      {
        // From _ssl.c in Python source code: PY_SSL_VERSION_TLS_CLIENT=0x10,
        //long PY_SSL_VERSION_TLS_CLIENT = (long)0x10;
        // Create an SSLContext for our client
        //_ampspy_ssl_context = PyObject_CallFunction(_ampspy_sslcontext_class, "l", (long)0x10);
        _ampspy_ssl_context = PyObject_CallMethod(_ampspy_ssl_module, "create_default_context", NULL);
      }
      else
      {
        _ampspy_ssl_context = PyObject_CallFunctionObjArgs(_ampspy_sslcontext_class, tlsClient, NULL);
        Py_DECREF(tlsClient);
      }
      if (!_ampspy_ssl_context)
      {
        Py_DECREF(_ampspy_ssl_module);
        Py_DECREF(_ampspy__ssl_module);
        Py_DECREF(_ampspy_sslcontext_class);
        _ampspy_ssl_module = NULL;
        _ampspy__ssl_module = NULL;
        _ampspy_sslcontext_class = NULL;
        PyErr_SetString(ampspy::exc::ConnectionException,
                        "Could not create SSLContext");
        return NULL;
      }
    }
    else
    {
      _ampspy_ssl_context = pyCtx;
      Py_INCREF(_ampspy_ssl_context);
    }

    PyObject* ssl_internal_filename = NULL;
    const char* dllName = dll_name;
    if (!dllName)
    {
      if (_ampspy__ssl_module)
      {
        ssl_internal_filename = PyObject_GetAttrString(_ampspy__ssl_module,
                                                       "__file__");
        if (ssl_internal_filename && PyString_Check(ssl_internal_filename))
        {
          dllName = PyString_AsString(ssl_internal_filename);
        }
      }
    }

    if (!strictCiphersOnly_)
    {
      PyObject* retVal = PyObject_CallMethod(_ampspy_ssl_context, "set_ciphers", "(s)", "DEFAULT");
      Py_XDECREF(retVal);
    }
    PyObject_SetAttrString(_ampspy_ssl_context, "check_hostname", Py_False);
    PyObject* pyVm = PyObject_GetAttrString(_ampspy_ssl_module, "VerifyMode");
    if (pyVm)
    {
      PyObject* pyVerifyMode = PyObject_GetAttrString(pyVm, "CERT_NONE");
      if (pyVerifyMode)
      {
        PyObject_SetAttrString(_ampspy_ssl_context,
                               "verify_mode",
                               pyVerifyMode);
        Py_DECREF(pyVerifyMode);
      }
      Py_DECREF(pyVm);
    }

    // typedef struct {
    // PyObject_HEAD
    // SSL_CTX *ctx;
    // ...
    // } PySSLContext;
    // The SSL_CTX* is the first item after PyObject_HEAD
    _amps_SSL_CTX* ctx = ((ampspy_PySSLContext*)_ampspy_ssl_context)->ctx;

    // Init the C++ client with the _amps_SSL_CTX* from the Python object
    int rc = amps_ssl_init_from_context(ctx, dllName);
    Py_XDECREF(ssl_internal_filename);
    if (rc)
    {
      char errbuf[256];
      _AMPS_SNPRINTF(errbuf, sizeof(errbuf), "init from context failed %s ctx is %p ssl_context is %p\n", amps_ssl_get_error(), (void*)ctx, (void*)_ampspy_ssl_context);
      PyErr_SetString(ampspy::exc::ConnectionException, errbuf);
      return NULL;
    }
    _ssl_is_initialized = true;
    // Redirect TCPS calls so we can use python wrapped socket/SSL
    amps_tcps_close_all = _ampspy_close_all;
    _ampspy_get_socket_and_ssl = amps_tcps_get_socket_and_ssl;
    amps_tcps_get_socket_and_ssl = _ampspy_SSL_new_wrapped_socket;

    Py_INCREF(Py_None);
    return Py_None;
  }

  // Make our ssl.SSLContext available
  PyObject* ssl_get_context(PyObject* self, PyObject* args)
  {
    if (_ampspy_ssl_context)
    {
      Py_INCREF(_ampspy_ssl_context);
      return _ampspy_ssl_context;
    }
    else
    {
      Py_INCREF(Py_None);
      return Py_None;
    }
  }
#endif // Python 3+ only

#if PY_MAJOR_VERSION < 3
  PyObject* ampspy_ssl_init(PyObject* self, PyObject* args)
  {
    if (_ssl_is_initialized)
    {
      Py_INCREF(Py_None);
      return Py_None;
    }

    const char* dll_name = NULL;
    if (self && args)
    {
      if (!PyArg_ParseTuple(args, "|s", &dll_name))
      {
        return NULL;
      }
    }
    if (ssl_init_c_lib(dll_name))
    {
      PyErr_SetString(ampspy::exc::ConnectionException,
                      amps_ssl_get_error());
      return NULL;
    }
    Py_INCREF(Py_None);
    return Py_None;
  }

  PyObject* ssl_init(PyObject* self, PyObject* args)
  {
    return ampspy_ssl_init(self, args);
  }

  PyObject* ssl_set_verify(PyObject* self, PyObject* args)
  {
    int mode = 0;
    if (!PyArg_ParseTuple(args, "i", &mode))
    {
      return NULL;
    }

    if (0 == amps_ssl_set_verify(mode ? 1 : 0))
    {
      Py_INCREF(Py_None);
      return Py_None;
    }

    PyErr_SetString(ampspy::exc::ConnectionException,
                    amps_ssl_get_error());
    return NULL;
  }
#else
  int ampspy_ssl_set_verify(int mode_)
  {
    PyObject* pyVm = PyObject_GetAttrString(_ampspy_ssl_module, "VerifyMode");
    PyObject* pyVerifyMode;
    if (mode_ == 0)
    {
      pyVerifyMode = PyObject_GetAttrString(pyVm, "CERT_NONE");
    }
    else
    {
      pyVerifyMode = PyObject_GetAttrString(pyVm, "CERT_REQUIRED");
    }
    int rc = PyObject_SetAttrString(_ampspy_ssl_context, "verify_mode", pyVerifyMode);
    Py_XDECREF(pyVm);
    Py_XDECREF(pyVerifyMode);
    return rc;
  }

  PyObject* ampspy_ssl_init(PyObject* self, PyObject* args, PyObject* kwds)
  {
    static const char* kwargs[] = { "dll_name", "ssl_context", "strict_ciphers_only", NULL };
    const char* dll_name = NULL;
    PyObject* ssl_context = NULL;
    int strict_ciphers_only = 0;
    if (self && args)
    {
      if (!PyArg_ParseTupleAndKeywords(args, kwds, "|sOi", (char**)kwargs,
                                       &dll_name, &ssl_context, &strict_ciphers_only))
      {
        return NULL;
      }
    }

    return ssl_init_internal(dll_name, ssl_context, strict_ciphers_only != 0);
  }

  PyObject* ssl_init(PyObject* self, PyObject* args, PyObject* kwds)
  {
    // If this is called repeatedly, want to make sure that verify mode
    // gets reset to expected value after init.
    PyObject* ret = ampspy_ssl_init(self, args, kwds);
    if (ret && _ampspy_ssl_module)
    {
      ampspy_ssl_set_verify(0);
    }
    return ret;
  }

  PyObject* ssl_set_verify(PyObject* self, PyObject* args)
  {
    int mode = 0;
    if (!PyArg_ParseTuple(args, "i", &mode))
    {
      return NULL;
    }

    if (_ampspy_ssl_module)
    {
      if (0 == ampspy_ssl_set_verify(mode))
      {
        Py_INCREF(Py_None);
        return Py_None;
      }
    }
    else
    {
      if (0 == amps_ssl_set_verify(mode ? 1 : 0))
      {
        Py_INCREF(Py_None);
        return Py_None;
      }
    }

    PyErr_SetString(ampspy::exc::ConnectionException,
                    amps_ssl_get_error());
    return NULL;
  }
#endif

  PyObject* ssl_load_verify_locations(PyObject* self, PyObject* args)
  {
    const char* ca_file = 0L, *ca_path = 0L;
    if (!PyArg_ParseTuple(args, "zz", &ca_file, &ca_path))
    {
      return NULL;
    }

    if (0 == amps_ssl_load_verify_locations(ca_file, ca_path))
    {
      Py_INCREF(Py_None);
      return Py_None;
    }

    PyErr_SetString(ampspy::exc::ConnectionException,
                    amps_ssl_get_error());
    return NULL;
  }
}// namespace ampspy

#ifndef AMPS_MODULE_NAME
  #define AMPS_MODULE_NAME AMPS
#endif

#if PY_MAJOR_VERSION < 3
  #define CONSTRUCT_INIT_FUNC_NAME(MOD) init ## MOD
#else
  #define CONSTRUCT_INIT_FUNC_NAME(MOD) PyInit_ ## MOD
#endif

#define INIT_FUNC_NAME(MOD) CONSTRUCT_INIT_FUNC_NAME(MOD)

// while we're waiting for a lock, check to see if there are any signals outstanding.
// If so, remember that so we can fail operations on non-main threads.
void waiting_function(void)
{
#ifndef _WIN32
  int cancelState = 0;
  int unusedCancelState = 0;
  pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancelState);
#endif
  try
  {
    LOCKGIL;
    if (PyErr_CheckSignals() == -1)
    {
      ampspy::_is_signaled = true;
    }
  }
  catch (...)
  {
    ; // C Function; do not throw from here.
  }
#ifndef _WIN32
  pthread_setcancelstate(cancelState, &unusedCancelState);
#endif
}

void remove_route_function(void* vpData_)
{
  try
  {
    ampspy::client::remove_route(vpData_);
  }
  catch (...)
  {
    ; // C Function; do not throw from here.
  }
}

void* copy_route_function(void* vpData_)
{
  try
  {
    return ampspy::client::copy_route(vpData_);
  }
  catch (...)
  {
    return NULL; // C Function; do not throw from here.
  }
}

static PyMethodDef AMPSMethods[] =
{
  {ampspy::shims::g_shimExitFuncName, (PyCFunction)ampspy::shims::_shimExitFunc, METH_NOARGS, ""},
#if PY_MAJOR_VERSION < 3
  {
    "ssl_init",
    (PyCFunction)ampspy::ssl_init, METH_VARARGS,
    "Initializes SSL support in the AMPS module.\n\n"
    ":param dllpath: The path to the OpenSSL DLL or shared library to use for\n"
    "                SSL functionality."
  },
#else
  {
    "ssl_init",
    (PyCFunction)ampspy::ssl_init, METH_VARARGS | METH_KEYWORDS,
    "Initializes SSL support in the AMPS module.\n\n"
    ":param dllpath: The path to the OpenSSL DLL or shared library to use for\n"
    "                SSL functionality.\n"
    ":param ssl_context: An ssl.SSLContext preconfigured with desired settings\n"
    "                    for tcps connections to the AMPS server.\n"
    ":param strict_ciphers_only: If True, use only the stricter ciphers allowed\n"
    "                            by default in Python version 3.10 and above. The\n"
    "                            default is False, which enables all default\n"
    "                            OpenSSL ciphers for compatibility with some AMPS\n"
    "                            versions using older OpenSSL libraries.\n"
  },
  {
    "ssl_get_context",
    (PyCFunction)ampspy::ssl_get_context, METH_VARARGS,
    "Returns the SSLContext used for SSL connections. Call ssl_init first.\n\n"
  },
#endif
  {
    "ssl_set_verify",
    (PyCFunction)ampspy::ssl_set_verify, METH_VARARGS,
    "Enables or disables peer certificate validation for SSL connections.\n\n"
    ":param enabled: True to enable, False to disable. Default: False (disabled)."
  },
  {
    "ssl_load_verify_locations",
    (PyCFunction)ampspy::ssl_load_verify_locations, METH_VARARGS,
    "Override default CA certificate locations for AMPS SSL connections.\n\n"
    ":param ca_file: Path to a PEM file containing CA certificates.\n"
    ":param ca_path: Path to a directory containing multiple CA certificates as PEM files.\n\n"
    "See OpenSSL's ``SSL_CTX_load_verify_locations`` for more information."
  },
  {NULL, NULL, 0, NULL}
};


#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef ampspy_moduledef =
{
  PyModuleDef_HEAD_INIT,
  STRINGIFYX(AMPS_MODULE_NAME),
  NULL,
  0,
  AMPSMethods,
  NULL,
  NULL,
  NULL,
  NULL
};
#endif

PyMODINIT_FUNC
INIT_FUNC_NAME(AMPS_MODULE_NAME)()
{
  PyObject* module;

#if PY_MAJOR_VERSION >= 3
  module = PyModule_Create(&ampspy_moduledef);
  if (module == NULL)
  {
    return module;
  }
#else
  PyEval_InitThreads();
  module = Py_InitModule(STRINGIFYX(AMPS_MODULE_NAME), AMPSMethods);
  if (module == NULL)
  {
    return;
  }
#endif

  if (!ampspy::shims::init(module))
  {
    // Python error state set wit detailed information; just return none.
    Py_XDECREF(module);
#if PY_MAJOR_VERSION < 3
    return;
#else
    return NULL;
#endif
  }

  // this is an obscure C++ client library feature that allows code to be run while
  // we're waiting for lock acquisition. We use it to communicate python signal state
  // from the main thread elsewhere.
  amps_set_waiting_function((void*)waiting_function);
  amps_set_remove_route_function((void*)remove_route_function);
  amps_set_copy_route_function((void*)copy_route_function);
#ifndef _WIN32
  pthread_atfork(&ampspy::client::amps_python_client_atfork_prepare,
                 &ampspy::client::amps_python_client_atfork_parent,
                 &ampspy::client::amps_python_client_atfork_child);
#endif

  ampspy::message::add_types(module);
  ampspy::client::add_types(module);
  ampspy::reason::add_types(module);
  ampspy::store::add_types(module);
  ampspy::fixbuilder::add_types(module);
  ampspy::nvfixbuilder::add_types(module);
  ampspy::authenticator::add_types(module);
  ampspy::serverchooser::add_types(module);
  ampspy::fixshredder::add_types(module);
  ampspy::nvfixshredder::add_types(module);
  ampspy::publishstore::add_types(module);
  ampspy::hybridpublishstore::add_types(module);
  ampspy::memorypublishstore::add_types(module);
  ampspy::memorybookmarkstore::add_types(module);
  ampspy::mmapbookmarkstore::add_types(module);
  ampspy::ringbookmarkstore::add_types(module);
  ampspy::messagestream::add_types(module);
  ampspy::command::add_types(module);
  ampspy::cmessagehandler::add_types(module);
  ampspy::exponentialdelaystrategy::add_types(module);
  ampspy::fixeddelaystrategy::add_types(module);
  ampspy::compositemessagebuilder::add_types(module);
  ampspy::compositemessageparser::add_types(module);
  ampspy::versioninfo::add_types(module);
  ampspy::recoverypoint::add_types(module);
  ampspy::sowrecoverypointadapter::add_types(module);
  ampspy::conflatingrecoverypointadapter::add_types(module);

  ampspy::exc::init(module);
  ampspy::haclient::add_types(module);
#if PY_MAJOR_VERSION >= 3
  return module;
#endif
}
