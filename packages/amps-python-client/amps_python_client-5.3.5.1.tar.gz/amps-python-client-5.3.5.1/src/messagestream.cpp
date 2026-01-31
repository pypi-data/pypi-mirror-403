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
#include "messagestream_docs.h"
#include <deque>

using namespace AMPS;
namespace ampspy
{
  namespace messagestream
  {
    /**
     * The guts of the message stream are held in this non-ref counted
     *  implementation object which allows us to not hold a reference
     *  to the message stream inside the client. When the last reference
     *  to the message stream goes away, enqueue a request on the client's
     *  message router which will result in the impl being destroyed.
     */
    struct MessageStreamImpl : public AMPS::ConnectionStateListener
    {
      typedef char flags_type;
      typedef AMPS_ATOMIC_TYPE_8 atomic_flags_type;
      static const flags_type ms_is_stats                    = 0x1;
      static const flags_type ms_is_acks                     = 0x1;
      static const flags_type ms_is_sow                      = 0x2;
      static const flags_type ms_is_active                   = 0x4;
      static const flags_type ms_is_disconnected_in_progress = 0x8;
      static const flags_type ms_is_conflated                = 0x10;
      static const flags_type ms_received_group_end          = 0x20;
      static const flags_type ms_received_stats_ack          = 0x40;

      MessageStreamImpl(AMPS::Client& client_,
                        bool          isSow_,
                        bool          isStats_,
                        bool          sendCompleted_)
        : _client(client_),
          _timeout(0),
          _maxDepth(client_.getDefaultMaxDepth()),
          _flags(ms_is_active),
          _requestedAcks(0),
          _isAutoAck(_client.getAutoAck()),
          _sendCompleted(sendCompleted_)
      {
        if (isSow_)
        {
          _flags |= ms_is_sow;
          _flags |= ms_is_stats;
          _requestedAcks = AMPS::Message::AckType::Completed;
        }
        if (isStats_)
        {
          _flags |= ms_is_stats;
          _requestedAcks = AMPS::Message::AckType::Stats;
        }

        CALL_AND_DONT_RETURN(_client.addConnectionStateListener(this));
      }

      ~MessageStreamImpl(void)
      {
      }

      void connectionStateChanged(AMPS::ConnectionStateListener::State newState_)
      {
        if (newState_ == AMPS::ConnectionStateListener::Disconnected)
        {
          AMPS_FETCH_AND_8((&_flags), ~ms_is_active);
          AMPS_FETCH_OR_8((&_flags), ms_is_disconnected_in_progress);
        }
        else if (newState_ == AMPS::ConnectionStateListener::Connected
                 && _commandId.empty()
                 && _subId.empty()
                 && _queryId.empty())
        {
          AMPS_FETCH_OR_8((&_flags), ms_is_active);
          AMPS_FETCH_AND_8((&_flags), ~ms_is_disconnected_in_progress);
        }
      }

      void unsubscribe(const std::string& id_, bool active_ = false)
      {
        if (id_.empty() || !_client.isValid())
        {
          return;
        }
        CALL_AND_DONT_RETURN(_client.removeMessageHandler(id_));
        if (_flags & (ms_is_active | ms_is_disconnected_in_progress)
            || active_)
        {
          try
          {
            UnlockGIL unlockGuard;
            _client.unsubscribe(id_);
          }
          catch (DisconnectedException&)
          {;}
          catch (AMPSException& aex)
          {
            _client.getExceptionListener().exceptionThrown(aex);
          }
        }
      }

      void close(void)
      {
        bool active = (_flags & (ms_is_active | ms_is_disconnected_in_progress)) != 0;
        AMPS_FETCH_AND_8((&_flags), ~(ms_is_active | ms_is_disconnected_in_progress));
        if (_client.isValid())
        {
          UnlockGIL unlockGuard;
          _client.removeConnectionStateListener(this);
        }
        unsubscribe(_commandId, active);
        unsubscribe(_subId, active);
        unsubscribe(_queryId, active);
        _previousTopic.clear();
        _previousBookmark.clear();
        if (_client.isValid())
        {
          CALL_AND_DONT_RETURN(_client.deferredExecution(MessageStreamImpl::destroy, this));
        }
      }

      PyObject*
      next(void)
      {
        if (!_previousTopic.empty() && !_previousBookmark.empty())
        {
          try
          {
            _client.ackDeferredAutoAck(_previousTopic, _previousBookmark);
          }
#ifdef _WIN32
          catch (const AMPSException&)
#else
          catch (const AMPSException& e)
#endif
          {
            _previousTopic.clear();
            _previousBookmark.clear();
            NONE;
          }
          _previousTopic.clear();
          _previousBookmark.clear();
        }
        ampspy::message::obj* o = (ampspy::message::obj*)_PyObject_New(ampspy::message::message_type);
        o->pMessage = new AMPS::Message(AMPS::Message::EMPTY);
        o->isOwned = true;
        bool isActive = true;
        bool isTimeout = false;
        long waitTimeout = (long)((_timeout < 1000UL) ? _timeout : 1000UL);
        const unsigned long defaultSpinMillis = 10;
        // LOCKING: Keep the GIL free while we take our internal lock.
        if (1)
        {
          UNLOCKGIL;
          Lock<Mutex> lock(_stateLock);
          Timer timer((double)_timeout);
          timer.start();
          while (_messageList.empty() && (_flags & ms_is_active))
          {
            if (_timeout)
            {
              if (!_stateLock.wait(waitTimeout))
              {
                // nothing in the timeout.
                if (timer.checkAndGetRemaining(&waitTimeout))
                {
                  // we'll just return None, but we are still alive.
                  isTimeout = true;
                  break;
                }
                waitTimeout = (waitTimeout < 1000L) ? waitTimeout : 1000L;
              }
            }
            else
            {
              // no user timeout specified, but we still spin to catch Ctrl-C.
              if (!_stateLock.wait(defaultSpinMillis))
              {
                Unlock<Mutex> lock(_stateLock);
                if (1)
                {
                  LOCKGIL;
                  PyErr_CheckSignals();
                  if (PyErr_Occurred())
                  {
                    Py_DecRef((PyObject*)o);
                    return NULL;
                  }
                }
              }
            }
          }
          if (!isTimeout && !_messageList.empty())
          {
            *(o->pMessage) = _messageList.front();
            if (_messageList.size() >= _maxDepth)
            {
              _stateLock.signalAll();
            }
            _messageList.pop_front();
            if (_flags & ms_is_conflated)
            {
              std::string sowKey = o->pMessage->getSowKey();
              if (sowKey.length())
              {
                _sowKeyMap.erase(sowKey);
              }
            }
            else if (o->pMessage->getCommandEnum() == AMPS::Message::Command::Publish
                     && _isAutoAck
                     && !o->pMessage->getLeasePeriod().empty()
                     && !o->pMessage->getBookmark().empty())
            {
              _previousTopic = o->pMessage->getTopic().deepCopy();
              _previousBookmark = o->pMessage->getBookmark().deepCopy();
            }
          }
          else if (!isTimeout)
          {
            isActive = false;
          }
        }
        if (isTimeout)
        {
          // nothing in the timeout. we'll just return None, but we are still alive.
          Py_DecRef((PyObject*)o);
          NONE;
        }
        else if (!isActive)
        {
          if (_flags & ms_is_disconnected_in_progress)
          {
            PyErr_SetString(exc::DisconnectedException, "An AMPS disconnect occurred while this message stream was active.");
          }
          else
          {
            PyErr_SetString(PyExc_StopIteration, "No more messages.");
          }
          Py_DecRef((PyObject*)o);
          return NULL;
        }
        else
        {
          const bool isSow = ((_flags & ms_is_sow) != 0);
          const bool isStats = ((_flags & ms_is_stats) != 0);

          unsigned command = o->pMessage->getCommandEnum();
          if (isSow && command == AMPS::Message::Command::GroupEnd)
          {
            AMPS_FETCH_OR_8((&_flags), ms_received_group_end);
            if (!isStats || (_flags & ms_received_stats_ack))
            {
              AMPS_FETCH_AND_8((&_flags), ~ms_is_active);
            }
          }
          else if (isStats && command == AMPS::Message::Command::Ack)
          {
            unsigned ackType = o->pMessage->getAckTypeEnum();
            _requestedAcks &= ~ackType;
            if (_requestedAcks == 0)
            {
              AMPS_FETCH_OR_8((&_flags), ms_received_stats_ack);
              if (!isSow || (_flags & ms_received_group_end))
              {
                AMPS_FETCH_AND_8((&_flags), ~ms_is_active);
              }
            }
            if (isSow && !_sendCompleted && ackType == AMPS::Message::AckType::Completed)
            {
              return next();
            }
          }
          return (PyObject*) o;
        }
      }

      void
      onMessage(const AMPS::Message& message_)
      {
        // Take the copy and, if we need it, the SOW key, outside of
        //  the lock.
        Message copyOfMessage = message_.deepCopy();
        if (!(_flags & ms_is_conflated))
        {
          Lock<Mutex> lock(_stateLock);
          if (!(_flags & ms_is_active))
          {
            return;
          }
          if (_maxDepth && _messageList.size() >= _maxDepth)
          {
            // This is handled internally as a time to check and
            // send heartbeats. The same Message will return to
            // this call.
            throw MessageStreamFullException("Python stream full");
          }
          _messageList.push_back(copyOfMessage);
          if (message_.getCommandEnum() == AMPS::Message::Command::Publish
              && _isAutoAck
              && !message_.getLeasePeriod().empty()
              && !message_.getBookmark().empty())
          {
            message_.setIgnoreAutoAck();
          }
          _stateLock.signalAll();
        }
        else
        {
          std::string sowkey = copyOfMessage.getSowKey();
          if (sowkey.length())
          {
            Lock<Mutex> lock(_stateLock);
            if (!(_flags & ms_is_active))
            {
              return;
            }
            SOWKeyMap::iterator it = _sowKeyMap.find(sowkey);
            if (it != _sowKeyMap.end())
            {
              *(it->second) = copyOfMessage;
              _stateLock.signalAll();
            }
            else
            {
              if (_maxDepth && _messageList.size() >= _maxDepth)
              {
                // This is handled internally as a time to
                // check and send heartbeats. The same Message
                // will return to this call.
                throw MessageStreamFullException("Python stream full");
              }
              _messageList.push_back(copyOfMessage);
              _sowKeyMap[sowkey] = &_messageList.back();
              _stateLock.signalAll();
            }
          }
          else
          {
            Lock<Mutex> lock(_stateLock);
            if (!(_flags & ms_is_active))
            {
              return;
            }
            _messageList.push_back(copyOfMessage);
            if (message_.getCommandEnum() == AMPS::Message::Command::Publish
                && _isAutoAck
                && !message_.getLeasePeriod().empty()
                && !message_.getBookmark().empty())
            {
              message_.setIgnoreAutoAck();
            }
            _stateLock.signalAll();
          }
        }
      }

      void setConflated(void)
      {
        AMPS_FETCH_OR_8((&_flags), ms_is_conflated);
      }
      void setTimeout(unsigned long timeout_)
      {
        _timeout = timeout_;
      }
      void setMaxDepth(unsigned long maxDepth_)
      {
        _maxDepth = maxDepth_;
      }
      unsigned long getMaxDepth()
      {
        return _maxDepth;
      }
      size_t getDepth()
      {
        return _messageList.size();
      }
      void setAcksOnly(unsigned requestedAcks_)
      {
        _requestedAcks = requestedAcks_;
        AMPS_FETCH_OR_8((&_flags), ms_is_acks);
      }

      static void destroy(void* pMessageStreamImpl_)
      {
        delete ((MessageStreamImpl*)pMessageStreamImpl_);
      }

      typedef std::deque<AMPS::Message> MessageList;
      typedef std::map<std::string, AMPS::Message*> SOWKeyMap;

      AMPS::Client&                   _client;
      AMPS::Mutex                     _stateLock;
      MessageList                     _messageList;
      std::string                     _commandId;
      std::string                     _queryId;
      std::string                     _subId;
      SOWKeyMap                       _sowKeyMap;
      unsigned long                   _timeout;
      unsigned long                   _maxDepth;
      atomic_flags_type               _flags;
      AMPS::Field                     _previousTopic;
      AMPS::Field                     _previousBookmark;
      unsigned                        _requestedAcks;
      bool                            _isAutoAck;
      bool                            _sendCompleted;
    };

    void
    obj::internalInit(PyObject*     pPythonClient_,
                      AMPS::Client* pClient_,
                      bool          isSow_,
                      bool          isStats_,
                      bool          sendCompleted_ = true)
    {
      _client = *pClient_;
      _pImpl = new MessageStreamImpl(_client, isSow_, isStats_, sendCompleted_);
      _pPythonClient = pPythonClient_;
      Py_IncRef(_pPythonClient);
    }

    AMPS::MessageHandler obj::messageHandler()
    {
      return AMPS::MessageHandler(messageCallback, (void*)(MessageStreamImpl*)_pImpl);
    }

    const std::string&
    obj::commandId(void) const
    {
      return ((MessageStreamImpl*)_pImpl)->_commandId;
    }

    std::string&
    obj::commandId(void)
    {
      return ((MessageStreamImpl*)_pImpl)->_commandId;
    }

    const std::string&
    obj::subId(void) const
    {
      return ((MessageStreamImpl*)_pImpl)->_subId;
    }

    std::string&
    obj::subId(void)
    {
      return ((MessageStreamImpl*)_pImpl)->_subId;
    }

    const std::string&
    obj::queryId(void) const
    {
      return ((MessageStreamImpl*)_pImpl)->_queryId;
    }

    std::string&
    obj::queryId(void)
    {
      return ((MessageStreamImpl*)_pImpl)->_queryId;
    }

    void
    obj::setAcksOnly(unsigned requestedAcks_)
    {
      ((MessageStreamImpl*)_pImpl)->setAcksOnly(requestedAcks_);
    }

    //    def __init__(self, name):
    static int _ctor(obj* self, PyObject* args, PyObject* kwds)
    {
      self->_pImpl = (MessageStreamImpl*)NULL;
      new (&self->_client) AMPS::Client(0);
      return 0;
    }

    static PyObject* close(obj* self, PyObject* args)
    {
      MessageStreamImpl* pImpl = (MessageStreamImpl*)AMPSPY_IEX_GET(&self->_pImpl, (MessageStreamImpl*)0);
      if (pImpl)
      {
        pImpl->close();
        {
          UNLOCKGIL;
          self->_client.AMPS::Client::~Client();
        }
        Py_XDECREF(self->_pPythonClient);
        self->_pPythonClient = NULL;
      }
      NONE;
    }
    static void _dtor(obj* self)
    {
      MessageStreamImpl* pImpl = (MessageStreamImpl*)AMPSPY_IEX_GET(&self->_pImpl, (MessageStreamImpl*)0);
      if (pImpl)
      {
        pImpl->close();
        {
          UNLOCKGIL;
          self->_client.AMPS::Client::~Client();
        }
        Py_XDECREF(self->_pPythonClient);
        self->_pPythonClient = NULL;
      }
      shims::free(self);
    }

    static PyObject* timeout(obj* self, PyObject* args)
    {
      unsigned long timeout = 0;
      if ((MessageStreamImpl*)self->_pImpl)
      {
        if (!PyArg_ParseTuple(args, "k", &timeout))
        {
          return NULL;
        }
        ((MessageStreamImpl*)self->_pImpl)->setTimeout(timeout);
      }
      Py_INCREF(self);
      return reinterpret_cast<PyObject*>(self);
    }

    static PyObject* conflate(obj* self, PyObject* args)
    {
      if ((MessageStreamImpl*)self->_pImpl)
      {
        ((MessageStreamImpl*)self->_pImpl)->setConflated();
      }
      Py_INCREF(self);
      return reinterpret_cast<PyObject*>(self);
    }
    static PyObject* max_depth(obj* self, PyObject* args)
    {
      if ((MessageStreamImpl*)self->_pImpl)
      {
        unsigned long maxDepth = 0;
        if (!PyArg_ParseTuple(args, "k", &maxDepth))
        {
          return NULL;
        }
        ((MessageStreamImpl*)self->_pImpl)->setMaxDepth(maxDepth);
      }
      Py_INCREF(self);
      return reinterpret_cast<PyObject*>(self);
    }
    static PyObject* get_max_depth(obj* self, PyObject* args)
    {
      if ((MessageStreamImpl*)self->_pImpl)
      {
        CALL_RETURN_SIZE_T(((MessageStreamImpl*)self->_pImpl)->getMaxDepth());
      }
      return NULL;
    }
    static PyObject* get_depth(obj* self, PyObject* args)
    {
      if ((MessageStreamImpl*)self->_pImpl)
      {
        CALL_RETURN_SIZE_T(((MessageStreamImpl*)self->_pImpl)->getDepth());
      }
      return NULL;
    }
    static PyObject* next(obj* self, PyObject* args)
    {
      if ((MessageStreamImpl*)self->_pImpl)
      {
        return ((MessageStreamImpl*)self->_pImpl)->next();
      }
      PyErr_SetString(PyExc_StopIteration, "No more messages.");
      return NULL;
    }
    static PyObject* __iter__(obj* self, PyObject* args)
    {
      Py_INCREF((PyObject*)self);
      return (PyObject*)self;
    }
    AMPSDLL void messageCallback(const AMPS::Message& message, void* void_self)
    {
      MessageStreamImpl* pImpl = (MessageStreamImpl*)void_self;
      pImpl->onMessage(message);
    }

    AMPSDLL void discardImpl(void* pImpl_)
    {
      delete (MessageStreamImpl*)pImpl_;
    }

    AMPSDLL ampspy::ampspy_type_object messagestream_type;

    void add_types(PyObject* module_)
    {
      messagestream_type.setName("AMPS.MessageStream")
      .setBasicSize(sizeof(obj))
      .setDestructorFunction(_dtor)
      .setConstructorFunction(_ctor)
      .setDoc(messagestream_class_doc)
      .setIterFunction(__iter__)
      .setIterNextFunction(next)
      .addMethod("close", ampspy::messagestream::close, close_doc)
      .addMethod("timeout", timeout, timeout_doc)
      .addMethod("conflate", conflate, conflate_doc)
      .addMethod("max_depth", max_depth, max_depth_doc)
      .addMethod("get_max_depth", get_max_depth, get_max_depth_doc)
      .addMethod("get_depth", get_depth, get_depth_doc)
      .createType()
      .registerType("MessageStream", module_);
    }
  }
}
