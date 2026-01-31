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

static const char* client_class_doc = R"docstring(Client(name)
The base AMPS Client object used in AMPS applications. Each Client
object manages a single connection to AMPS. Each AMPS connection has
a name, a specific transport (such as tcp), a protocol (used for framing
messages to AMPS), and a message type (such as FIX or JSON).

The Client object creates and manages a background thread, and sends and
receives messages on that thread. The object provides both a synchronous
interface for processing messages on the calling thread, and an
asynchronous interface suitable for populating a queue to be processed by
worker threads.

Each Client has a name. The AMPS server uses this name for duplicate
message detection, so the name of each instance of the client application
should be unique.

An example of a Python client publishing a JSON message is listed below::

    client = AMPS.Client("test_client")

    try:
      client.connect("tcp://127.0.0.1:9004/amps/json")
      client.logon()
      client.publish("topic_name",'{"a":1,"b":"2"}')
    finally:
      client.close()

**Constructor Arguments:**


:param name: The unique name for this client. AMPS does not enforce
             specific restrictions on the character set used, however some protocols
             (for example, XML) may not allow specific characters. 60East recommends
             that the client name be meaningful, short, human readable, and avoid
             using control characters, newline characters, or square brackets.
)docstring";


static const char* bookmark_class_doc = R"docstring(
This class provides special values for bookmark subscriptions:

 * ``EPOCH`` - Begin the subscription at the beginning of the journal.
 * ``MOST_RECENT`` - Begin the subscription at the first undiscarded message in the bookmark store, or at the end of the bookmark store if all messages have been discarded.
 * ``NOW`` - Begin the subscription at the time that AMPS processes the subscription.

For example, to begin a bookmark subscription at the beginning of the journal,
provide ``AMPS.Client.Bookmarks.EPOCH`` as the bookmark in the call to
:meth:`AMPS.Client.bookmark_subscribe`.
)docstring";


static const char* allocateMessage_doc = R"docstring(allocateMessage()
A legacy method name for :meth:`allocate_message`.
)docstring";


static const char* allocate_message_doc = R"docstring(allocate_message()
Creates a new :class:`Message` appropriate for this client.

This function should be called rarely, since it does allocate a handful of small objects.


:returns: A new *Message* instance.
)docstring";


static const char* execute_doc = R"docstring(execute(command)
Execute the provided command and process responses using a ``MessageStream``. This method creates
a ``Message`` based on the provided ``Command``, sends the ``Message`` to AMPS, and returns a
``MessageStream`` that can be iterated on to process messages returned in response to the command.


:type command: AMPS.Command
:param command: The command to execute.
:returns: A ``MessageStream`` to iterate over.
)docstring";


static const char* execute_async_doc = R"docstring(execute_async(command, on_message)
Execute the provided command and process responses on the client receive thread using the provided handler.
This method creates a ``Message`` based on the provided ``Command``, sends the ``Message`` to AMPS, and
invokes the provided handler to process messages returned in response to the command. Rather than providing
messages on the calling thread, the AMPS Python client runs the handler directly on the client receive thread.

When the provided handler is not ``None``, this function blocks until AMPS acknowledges that the command has
been processed. The results of the command after that acknowledgment are provided to the handler.


:type on_message: A function or other callable object.
:type command: AMPS.Command
:param command: The command to execute.
:param on_message: A handler for messages returned by this command execution.
:returns: The command ID assigned to the executed command.
)docstring";


static const char* get_unpersisted_count_doc = R"docstring(get_unpersisted_count()
Gets the count of unpersisted publishes.


:returns: The count of unpersisted publishes.
)docstring";


static const char* get_server_version_doc = R"docstring(get_server_version()
Gets the connected server's version as a numeric value.


:returns: The version converted to a number. For example, server version 3.8.1.7 would be 3080107.
)docstring";


static const char* get_server_version_info_doc = R"docstring(get_server_version_info()
Gets the connected server's version as a :class:`VersionInfo`.


:returns: The version in a :class:`VersionInfo`.
)docstring";


static const char* convert_version_to_number_doc = R"docstring(convert_version_to_number(version)
Converts the provided version string to a number using 2 digits for each dot.
A value such as 4.0.0.0 will become 4000000 while 3.8.1.7 will return 3080107.


:param version: The version string to convert.
:type version: str
:returns: The numeric value for the version string.
)docstring";


static const char* bookmark_subscribe_doc = R"docstring(bookmark_subscribe()

**Signatures**:

- ``Client.bookmark_subscribe(on_message, topic, bookmark, filter=None, sub_id=None, options=None, timeout=0)``
- ``Client.bookmark_subscribe(topic, bookmark, filter=None, sub_id=None, options=None, timeout=0)``

  Places a bookmark subscription with AMPS. Starts replay at the most recent message reported by the ``bookmark`` parameter.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``bookmark_subscribe`` command on a background
     thread and calls the message handler with individual messages from the transaction log replay (if any) and
     then cuts over to live messages that match the subscription.
  2. When no message handler is provided, this method returns a message stream that can be iterated on to process
     messages received from the transaction log replay (if any) and then cuts over to live messages that match
     the subscription.


:param on_message: The message handler to invoke with matching messages
                   (specified only in the case where async processing is used).
:type on_message: :class:`MessageHandler`
:param topic: The topic to subscribe to.
:type topic: str
:param bookmark: A bookmark identifier or one of the constants from
                 :class:`Bookmarks`.
:type bookmark: str
:param filter: The filter.
:type filter: str
:param sub_id: The subscription ID. You may optionally provide a
               subscription ID to ease recovery scenarios, instead of having the
               system automatically generate one for you.
               When used with the ``replace`` option, this is the subscription to
               be replaced.
               With a bookmark store, this is the subscription ID used for
               recovery. So, when using a persistent bookmark store, provide an explicit
               subscription ID that is consistent across application restarts.
:type sub_id: str
:param options: A comma separated string of options. Default is `None`.
:type options: str
:param timeout: The maximum time to wait for the client to receive and
                consume a processed ack for this subscription (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns a ``MessageStream`` containing the
          results of the command.

:raises: :exc:`SubscriptionAlreadyExistsException`,
         :exc:`BadFilterException`, :exc:`BadRegexTopicException`,
         :exc:`TimedOutException`, :exc:`DisconnectedException`.
)docstring";


static const char* close_doc = R"docstring(close()
Disconnect from the AMPS server.
)docstring";


static const char* connect_doc = R"docstring(connect(uri)
Connects to the AMPS instance through the provided URI.

       The URI is a string with the format:
          ``transport://userId:password@host:port/protocol``

       The components of the URI are as follows:
       
       * *transport* -- The network transport used for the connection.
       * *userId* -- If authentication is enabled, this is the unique user ID used to authenticate the connection.
       * *password* -- If authentication is enabled, this is the password used to authenticate the connection.
       * *host* -- The hostname or IP address of the host where AMPS is installed.
       * *port* -- The port to connect to the AMPS instance.
       * *protocol* -- The protocol used by this connection.

       .. note:: Authentication is optional. If the system is using the
         default authentication with AMPS (which grants access to all users
         regardless of ``userId`` or ``password``), you can omit the
         ``userId:password@`` string from the connect URI.


:param uri: The URI used to connect to AMPS.
:type uri: str
:raises: :class:`ConnectionException`
)docstring";


static const char* deltaPublish_doc = R"docstring(deltaPublish(topic,data)
This is a legacy method name for :meth:`delta_publish`.

 .. deprecated:: 3.2.0.0
  Use :func:`delta_publish` instead.
)docstring";


static const char* deltaSubscribe_doc = R"docstring(deltaSubscribe(on_message,topic,filter=None,options=0,timeout=0)
A legacy method name for :meth:`delta_subscribe`.

 .. deprecated:: 3.2.0.0
  Use :func:`delta_subscribe` instead.
)docstring";


static const char* delta_publish_doc = R"docstring(delta_publish(topic,data,expiration=None)
Delta publish a message to an AMPS topic.
This method does not wait for a response from the AMPS server.
To detect failure, install a failed write handler.
If the client was created with a persistent store on construction,
then the client will store before forwarding the message to AMPS.


:param topic: The topic to publish the data to.
:type topic: str
:param data: The data to publish to the topic.
:type data: str
:param expiration: Number of seconds until published messages should expire.
:type expiration: int

:returns: The sequence number assigned to this message by the publish store
          or 0 if there is no publish store and the server is assigning sequence numbers.

:raises: :exc:`DisconnectedException`
)docstring";


static const char* delta_subscribe_doc = R"docstring(delta_subscribe()

**Signatures**:

- ``Client.delta_subscribe(on_message, topic, filter=None, options=None, timeout=0, sub_id=None)``
- ``Client.delta_subscribe(topic, filter=None, options=None, timeout=0, sub_id=None)``

  Places a delta subscription with AMPS.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``delta_subscribe`` command on a background thread 
     and calls the message handler with individual messages that match the subscription and that contain the updated fields.
  2. When no message handler is provided, this method returns a message stream that can be iterated on to process 
     messages received that match the subscription and that contain the updated fields.


:param on_message: The message handler to invoke with matching messages
                   (specified only in the case where async processing
                   is used).
:type on_message: str
:param topic: The topic to subscribe to.
:type topic: str
:param filter: The filter.
:type filter: str
:param options: A comma separated list of values indicating additional
                processing options.
:type options: str
:param timeout: The maximum time to wait for the client to receive and
                consume the processed ack for this subscription
                (in milliseconds). ``0`` indicates to wait indefinitely.
:type timeout: int
:param sub_id: The subscription ID.  You may optionally provide a
               subscription ID to ease recovery scenarios, instead of having the
               system automatically generate one for you.
               When used with the ``replace`` option, this is the subscription to
               be replaced.
:type sub_id: str

:returns: The command identifier assigned to this command if a message handler was provided. 
          If no message handler was provided, returns a ``MessageStream`` containing the 
          results of the command.

:raises: :exc:`SubscriptionAlreadyExistsException`,
         :exc:`BadFilterException`, :exc:`BadRegexTopicException`,
         :exc:`TimedOutException`, :exc:`DisconnectedException`
)docstring";


static const char* disconnect_doc = R"docstring(disconnect()
Disconnects and closes any active connections.
)docstring";


static const char* getName_doc = R"docstring(getName()
A legacy method name for :meth:`get_name`.
)docstring";


static const char* get_name_doc = R"docstring(get_name()
Gets the name of the :class:`Client` object.

:returns: The :class:`Client` name.
)docstring";


static const char* get_name_hash_doc = R"docstring(get_name_hash()
Gets the string name hash of the :class:`Client` object.

:returns: The name hash string.
)docstring";


static const char* get_name_hash_value_doc = R"docstring(get_name_hash_value()
Gets the numeric name hash of the :class:`Client` object.


:returns: The name hash int.
)docstring";


static const char* setName_doc = R"docstring(setName(name)
A legacy method name for :meth:`set_name`.

 .. deprecated:: 3.2.0.0
  Use :func:`set_name` instead.
)docstring";


static const char* set_name_doc = R"docstring(set_name(name)
Sets the :class:`Client` name.


:param name: The :class:`Client` name.
)docstring";


static const char* get_logon_correlation_data_doc = R"docstring(get_logon_correlation_data()
Gets the data used to correlate the logon of this :class:`Client` to the server.


:returns: The logon correlation data.
)docstring";


static const char* set_logon_correlation_data_doc = R"docstring(set_logon_correlation_data(logon_correlation_data)
Sets the data used to correlate the logon of this Client in the server.


:param logon_correlation_data: The base64 data string to send with the logon.
)docstring";


static const char* logon_doc = R"docstring(logon(timeout=0,authenticator=AMPS.DefaultAuthenticator,options=None)
Logs into AMPS with the parameters provided in the :meth:`connect` method.


:param timeout: The maximum time to wait for the command to
                receive a processed ack from AMPS for the logon command
                (in milliseconds). ``0`` indicates to wait indefinitely.
:type timeout: int
:param authenticator: An `Authenticator` object used to negotiate logon.
:type authenticator: Authenticator
:param options: An options string to be passed to the server during logon, such as ``ack_conflation=100ms``.
:type options: string

:returns: The command identifier.

:raises: :exc:`ConnectionException`
)docstring";


static const char* name_doc = R"docstring(name()
The name of the :class:`Client` object.


:returns: The :class:`Client` name.
)docstring";


static const char* publish_doc = R"docstring(publish(topic,data,expiration=None)
Publish a message to an AMPS topic. This method does not wait for a response from the AMPS server.
To detect failure, install a failed write handler. If the client was created with a persistent store
on construction, then the client will store before forwarding the message to AMPS. If a :exc:`DisconnectedException`
occurs, the message is still stored in the publish store.


:param topic: The topic to publish to.
:type topic: str
:param data: The data to publish.
:type data: str
:param expiration: Number of seconds until published message should expire.
:type expiration: int

:returns: The sequence number assigned to this message by the publish store
          or 0 if there is no publish store and the server is assigning sequence numbers.

:raises: :exc:`DisconnectedException`
)docstring";



static const char* send_doc = R"docstring(send(message,message_handler=None,timeout=None)
Send a :class:`Message` to AMPS via the Transport used in the :class:`Client`.


:param message: The message to send.
:type message: :class:`Message`
:param message_handler: The message handler that will receive messages
                        for this command.
:type message_handler: :class:`MessageHandler`
:param timeout: The maximum time to wait for the client to receive and
                consume a processed ack for this command (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int

:returns: The command identifier assigned to this command, or `None` if
          one is not assigned.
)docstring";


static const char* add_message_handler_doc = R"docstring(add_message_handler(command_id,message_handler,acks,is_subscribe)
Add a message handler to the :class:`Client` to handle messages and the
requested acknowledgments sent in response to the given ``command_id``.


:param command_id: The command, query, or sub ID for messages and acks.
:type command_id: str
:param message_handler: The message handler that will receive messages
                        for the ``command_id``.
:type message_handler: MessageHandler
:param acks: The acknowledgments requested to go to the ``message_handler``.
:type acks: str
:param is_subscribe: If the ``message_handler`` is for a subscribe command.
:type is_subscribe: int
)docstring";


static const char* remove_message_handler_doc = R"docstring(remove_message_handler(command_id)
Remove a message handler from the :class:`Client`.


:param command_id: The command ID for the handler to remove.
:type command_id: str
)docstring";


static const char* setOnDisconnectHandler_doc = R"docstring(setOnDisconnectHandler(client_disconnect_handler)
A legacy method name for :meth:`set_disconnect_handler`.

 .. deprecated:: 3.2.0.0
  Use :func:`set_disconnect_handler` instead.
)docstring";


static const char* setDisconnectHandler_doc = R"docstring(setDisconnectHandler(client_disconnect_handler)
A legacy method name for :meth:`set_disconnect_handler`.

 .. deprecated:: 3.2.0.0
  Use :func:`set_disconnect_handler` instead.
)docstring";


static const char* setExceptionListener_doc = R"docstring(setExceptionListener(exception_listener)
A legacy method name for :meth:`set_exception_listener`.

 .. deprecated:: 3.2.0.0
  Use :func:`set_exception_listener` instead.
)docstring";


static const char* setUnhandledMessageHandler_doc = R"docstring(setUnhandledMessageHandler(message_handler)
A legacy method name for :meth:`set_last_chance_message_handler`.

 .. deprecated:: 3.2.0.0
  Use :func:`set_last_chance_message_handler` instead.
)docstring";


static const char* set_unhandled_message_handler_doc = R"docstring(set_unhandled_message_handler(message_handler)
A legacy method name for :meth:`set_last_chance_message_handler`.

 .. deprecated:: 4.0.0.0
  Use :func:`set_last_chance_message_handler` instead.
)docstring";


static const char* set_disconnect_handler_doc = R"docstring(set_disconnect_handler(client_disconnect_handler)
Sets the :class:`DisconnectHandler` used by the :class:`Client`. In the event that the `Client` is unintentionally 
disconnected from AMPS, the invoke method from the :class:`ClientDisconnectHandler` will be invoked.

 .. deprecated:: 5.3.5.0
  Use :class:`HAClient` instead to get automatic disconnect handling.


:param client_disconnect_handler: The disconnect handler.
:type client_disconnect_handler: :class:`DisconnectHandler`
)docstring";


static const char* set_exception_listener_doc = R"docstring(set_exception_listener(exception_listener)
Sets the exception listener instance used for communicating absorbed exceptions.


:param exception_listener: The exception listener instance to invoke for exceptions.
:type exception_listener: Exception
)docstring";


static const char* get_exception_listener_doc = R"docstring(get_exception_listener()
Gets the exception listener callable set on self.


:returns: The exception listener callable set on self, or None.
)docstring";


static const char* set_heartbeat_doc = R"docstring(set_heartbeat(interval_seconds, timeout_seconds=None)
Used to enable heartbeating between the client and the AMPS Server.  When a
:class:`Client` sends a heartbeat message to an AMPS instance, the AMPS
instance will send back an acknowledgment message.  From this point forward the
:class:`Client` and AMPS instance will each monitor that the other is still active.
AMPS sends heartbeat messages to the client at the specified interval.
If the :class:`Client` does not receive a heartbeat message within
the time interval specified in ``timeout_seconds``, then the :class:`Client`
will assume that the connection has ended, close the connection and
invoke the :exc:`DisconnectHandler`. Likewise, if the server
sends a heartbeat and does not receive a response within the timeout,
the server will consider the :class:`Client` to be nonresponsive and close
the connection.

Heartbeats are processed in the client receive thread. If you use
asynchronous message processing, your message handler must process
messages within the timeout interval, or risk being disconnected
by the server.


:param interval_seconds: The time between heartbeat messages being sent to AMPS.
:type interval_seconds: int
:param timeout_seconds: The maximum time to wait for AMPS to acknowledge the start of heartbeating (in seconds).
:type timeout_seconds: int
)docstring"; 


static const char* start_timer_doc = R"docstring(start_timer()
Used to start a timer on an AMPS Server for the client.

.. deprecated:: 5.3.2.0
)docstring";


static const char* stop_timer_doc = R"docstring(stop_timer(handler)
Used to stop a timer on an AMPS Server previously started for the client.

.. deprecated:: 5.3.2.0


:param handler: The handler to be invoked with the timer response.
)docstring";


static const char* set_last_chance_message_handler_doc = R"docstring(set_last_chance_message_handler(message_handler)
Sets the :class:`MessageHandler` instance called when no other incoming message handler matches.


:param message_handler: The message handler to invoke when no other incoming message handler matches.
:type message_handler: :class:`MessageHandler`
)docstring";


static const char* set_duplicate_message_handler_doc = R"docstring(set_duplicate_message_handler(message_handler)
Sets the :class:`MessageHandler` instance used for messages that arrive from AMPS that are deemed to be duplicates
of previous messages, according to the local bookmark store.


:param message_handler: The message handler to invoke for duplicate messages.
:type message_handler: MessageHandler
)docstring";


static const char* get_duplicate_message_handler_doc = R"docstring(get_duplicate_message_handler()
Gets the message handler object set with :meth:`set_duplicate_message_handler`.


:returns: The message handler object set with :meth:`set_duplicate_message_handler`.
)docstring";


static const char* sow_doc = R"docstring(sow()

**Signatures**:

- ``Client.sow(on_message, topic, filter=None, batch_size=10, timeout=0, top_n=None, order_by=None, bookmark=None, options=0)``
- ``Client.sow(topic, filter=None, batch_size=10, timeout=0, top_n=None, order_by=None, bookmark=None, options=0)``

  Executes a SOW query.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the SOW query on a background thread and calls the
     message handler with individual messages, including the ``group_begin`` and ``group_end`` messages, that indicate
     the beginning and end of the SOW results.
  2. When no message handler is provided, this method returns a message stream that can be iterated on to process
     messages received including the ``group_begin`` and ``group_end`` messages, that indicate the beginning and end of
     the SOW results.

For example::

  client = AMPS.Client("test_client")

  try:
      client.connect("tcp://127.0.0.1:9004/amps/fix")
      client.logon()
      for message in client.sow("MySowTopic"):
          print(message.get_data())
  finally:
      client.close()


:param on_message: The message handler to invoke with matching
                   messages (specified only in the case where async
                   processing is used).
:type on_message: :class:`MessageHandler`
:param topic: The topic to execute the SOW query against.
:type topic: str
:param filter: The filter.
:type filter: str
:param batch_size: The batching parameter to use for the results.
:type batch_size: int
:param timeout: The maximum time to wait for the client to receive and
                consume a processed ack for this command (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int
:param top_n: The maximum number of records to return from the SOW.
:type top_n: int
:param order_by: To have the records ordered by the server.
:type order_by: str
:param bookmark: The bookmark for historical query of the SOW.
:type bookmark: int
:param options: A comma separated list of values indicating additional
                processing options.
:type options: str

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns a ``MessageStream`` containing the
          results of the command.

:raises: :exc:`BadFilterException`, :exc:`BadRegexTopicException`,
         :exc:`TimedOutException`, :exc:`DisconnectedException`
)docstring";


static const char* sowAndDeltaSubscribe_doc = R"docstring(sowAndDeltaSubscribe(on_message,topic,filter=None,batch_size=1,oof_enabled=False,send_empties=False,options=0,timeout=0,top_n=None)
A legacy method name for :meth:`sow_and_delta_subscribe`.

 .. deprecated:: 3.2.0.0
  Use :func:`sow_and_delta_subscribe` instead.
)docstring";


static const char* sowAndSubscribe_doc = R"docstring(sowAndSubscribe(on_message,topic,filter,batch_size=1,oof_enabled=False,options=0,timeout=0,top_n=None)
A legacy method name for :meth:`sow_and_subscribe`.

 .. deprecated:: 3.2.0.0
  Use :func:`sow_and_subscribe` instead.
)docstring";


static const char* sowDelete_doc = R"docstring(sowDelete(on_message,topic,filter=None,timeout=0)
A legacy method name for :meth:`sow_delete`.

 .. deprecated:: 3.2.0.0
  Use :func:`sow_delete` instead.
)docstring";


static const char* sow_and_delta_subscribe_doc = R"docstring(sow_and_delta_subscribe()

**Signatures**:

- ``Client.sow_and_delta_subscribe(on_message, topic, filter=None, batch_size=1, oof_enabled=False, send_empties=False, timeout=0, top_n=None, order_by=None, options=None)``
- ``Client.sow_and_delta_subscribe(topic, filter=None, batch_size=1, oof_enabled=False, send_empties=False, timeout=0, top_n=None, order_by=None, options=None)``

  Executes a SOW query and places a delta subscription.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``sow_and_delta_subscribe`` command on a background
     thread and calls the message handler with individual messages received from the SOW query, including the
     ``group_begin`` and ``group_end`` messages, that indicate the beginning and end of the SOW results and then with
     messages received that match the subscription and that contain the updated fields.
  2. When no message handler is provided, this method returns a message stream that can be iterated on to process
     messages received from the SOW query, including the ``group_begin`` and ``group_end`` messages, that indicate the
     beginning and end of the SOW results and then processes messages received that match the subscription and that
     contain the updated fields.


:param on_message: The message handler to invoke with matching
                   messages (specified only in the case where async processing is used).
:type on_message: :class:`MessageHandler`
:param topic: The topic to execute the SOW query against.
:type topic: str
:param filter: The filter.
:type filter: str
:param batch_size: The batch sizing parameter to use for the results.
:type batch_size: int
:param oof_enabled: Specifies whether or not Out-of-Focus processing is enabled.
:type oof_enabled: boolean
:param send_empties: Specifies whether or not unchanged records are
                     received on the delta subscription.
:type send_empties: boolean
:param timeout: The maximum time to wait for the client to receive and
                consume the processed ack for this command (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int
:param top_n: The maximum number of records to return from the SOW.
:type top_n: int
:param order_by: To have the records ordered by the server.
:type order_by: str
:param options: A comma separated list of values indicating additional processing options.
:type options: str

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns a ``MessageStream`` containing the results
          of the command.

:raises: :exc:`SubscriptionAlreadyExistsException`,
         :exc:`BadFilterException`, :exc:`BadRegexTopicException`,
         :exc:`TimedOutException`, :exc:`DisconnectedException`
)docstring";


static const char* sow_and_subscribe_doc = R"docstring(sow_and_subscribe()

**Signatures**:

- ``Client.sow_and_subscribe(on_message, topic, filter=None, batch_size=1, oof_enabled=False, timeout=0, top_n=None, order_by=None, bookmark=None, options=None)``
- ``Client.sow_and_subscribe(topic, filter=None, batch_size=1, oof_enabled=False, timeout=0, top_n=None, order_by=None, bookmark=None, options=None)``

  Executes a SOW query and places a subscription.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``sow_and_subscribe`` command on a background thread
     and calls the message handler with individual messages received from the SOW query, including the ``group_begin``
     and ``group_end`` messages, that indicate the beginning and end of the SOW results and then with messages received
     that match the subscription.
  2. When no message handler is provided, this method returns a message stream that can be iterated on to process
     messages received from the SOW query, including the ``group_begin`` and ``group_end`` messages, that indicate the
     beginning and end of the SOW results and then processes messages received that match the subscription.


:param on_message: The message handler to invoke with matching
                   messages (specified only in the case where async processing is used).
:type on_message: :class:`MessageHandler`
:param topic: The topic to execute the SOW query against.
:type topic: str
:param filter: The filter.
:type filter: str
:param batch_size: The batching parameter to use for the results.
:type batch_size: int
:param oof_enabled: Specifies whether or not Out-of-Focus processing is enabled.
:type oof_enabled: boolean
:param timeout: The maximum time to wait for the client to receive and
                consume the processed ack for this command (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int
:param top_n: The maximum number of records to return from the SOW.
:type top_n: int
:param order_by: To have the records ordered by the server.
:type order_by: str
:param bookmark: The bookmark for historical query of the SOW.
:type bookmark: str
:param options: A comma separated list of values indicating additional processing options.
:type options: str

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns a ``MessageStream`` containing the results
          of the command.

:raises: :exc:`SubscriptionAlreadyExistsException`,
         :exc:`BadFilterException`, :exc:`BadRegexTopicException`,
         :exc:`TimedOutException`, :exc:`DisconnectedException`
)docstring";


static const char* sow_delete_doc = R"docstring(sow_delete()

**Signatures**:

- ``Client.sow_delete(on_message, topic, filter=None, timeout=0)``
- ``Client.sow_delete(topic, filter=None, timeout=0)``

  Executes a SOW delete with a filter.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``sow_delete`` command on a background thread and
     calls the message handler with the results of the delete.
  2. When no message handler is provided, this method returns an acknowledgment message with the result of the
     delete command.

For example, to delete all messages that match a filter::

  ...
  ackMessage = client.sow_delete("sow_topic","/status = 'obsolete'")
  print("%s: %s" % (ackMessage.get_ack_type(), ackMessage.get_status()))
  ...


:param on_message: The message handler to invoke with `stats` and `completed` acknowledgments
                   (specified only in the case where async processing is used).
:type  on_message: :exc:`MessageHandler`
:param topic: The topic to execute the SOW delete against.
:type  topic: str
:param filter: The filter. To delete all records, set a filter that is always true ('1=1').
:type  filter: str
:param timeout: The maximum time to wait for the client to receive and
                consume the processed ack for this command (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type  timeout: int

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns an acknowledgment.

:raises: :exc:`BadFilterException`, :exc:`BadRegexTopicException`,
         :exc:`TimedOutException`, :exc:`DisconnectedException`
)docstring";


static const char* sow_delete_by_keys_doc = R"docstring(sow_delete_by_keys()

**Signatures**:

- ``Client.sow_delete_by_keys(on_message, topic, keys, timeout=0)``
- ``Client.sow_delete_by_keys(topic, keys, timeout=0)``

  Executes a SOW delete using the provided SOW key(s) to determine the record(s) to delete.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``sow_delete_by_keys`` command on a background
     thread and calls the message handler with the results of the delete.
  2. When no message handler is provided, this method provides an acknowledgment message with the result of
     the delete command.


:param on_message: The message handler to invoke with `stats` and `completed` acknowledgments
                   (specified only in the case where async processing is used).
:type on_message: :exc:`MessageHandler`
:param topic: The topic to execute the SOW delete against.
:type topic: str
:param keys: A comma separated list of SOW keys to be deleted.
:type keys: str
:param timeout: The maximum time to wait for the client to receive and
                consume the processed ack for this command (in millseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns an acknowledgment.
)docstring";


static const char* sow_delete_by_data_doc = R"docstring(sow_delete_by_data()

**Signatures**:

- ``Client.sow_delete_by_data(on_message, topic, data, timeout=0)``
- ``Client.sow_delete_by_data(topic, data, timeout=0)``

  Executes a SOW delete using the provided message data to determine the SOW key of the record to delete.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``sow_delete_by_data`` command on a background
     thread and calls the message handler with the results of the delete.
  2. When no message handler is provided, this method provides an acknowledgment message with the result of
     the delete command.

For example, to efficiently delete a message that your program has received from AMPS::

  ...
  topic= aMessage.get_topic()
  data = aMessage.get_data()
  ackMessage = client.sow_delete_by_data(topic,data)
  print("%s: %s" % (ackMessage.get_ack_type(), ackMessage.get_status()))
  ...

In addition to deleting a message from AMPS, this method allows deletion of a message whose keys match one
that is already stored, for example::

  data = orders[orderId]
  ackMessage = client.sow_delete_by_data('orders', data)
  del orders[orderId]


:param on_message: The message handler to invoke with `stats` and `completed` acknowledgments
                   (specified only in the case where async processing is used).
:type on_message: :exc:`MessageHandler`
:param topic: The topic to execute the SOW delete against.
:type topic: str
:param data: A message whose keys match the message to be deleted in the server's SOW.
:type data: str
:param timeout: The maximum time to wait for the client to receive and
                consume the processed ack for this command (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns an acknowledgment.
)docstring";


static const char* subscribe_doc = R"docstring(subscribe()

**Signatures**:

- ``Client.subscribe(on_message, topic, filter=None, options=None, timeout=0, sub_id=None)``
- ``Client.subscribe(topic, filter=None, options=None, timeout=0, sub_id=None)``

  Places a subscription with AMPS.

  There are two ways to use this method:

  1. When a message handler is provided, this method submits the ``subscribe`` command on a background thread and
     calls the message handler with individual messages that match the subscription.
  2. When no message handler is provided, this method returns a message stream that can be iterated on to process
     messages received that match the subscription.


:param on_message: The message handler to invoke with matching
                   messages (specified only in the case where async processing is used).
:type on_message: str
:param topic: The topic to subscribe to.
:type topic: str
:param filter: The filter.
:type filter: str
:param options: A comma separated list of values indicating additional processing options.
:type options: str
:param timeout: The maximum time to wait for the client to receive and
                consume the processed ack for this command (in milliseconds).
                ``0`` indicates to wait indefinitely.
:type timeout: int
:param sub_id: The subscription ID. You may optionally provide a
               subscription ID to ease recovery scenarios, instead of having the
               system automatically generate one for you. When used with the ``replace``
               option, this is the subscription to be replaced.
:type sub_id: str

:returns: The command identifier assigned to this command if a message handler was provided.
          If no message handler was provided, returns a ``MessageStream`` containing the results
          of the command.

:raises: :exc:`SubscriptionAlreadyExistsException`,
         :exc:`BadFilterException`, :exc:`BadRegexTopicException`,
         :exc:`TimedOutException`, :exc:`DisconnectedException`
)docstring";


static const char* unsubscribe_doc = R"docstring(unsubscribe(sub_id=None)
Remove a subscription from AMPS.

    .. note::
      Using the keyword ``all`` with ``sub_id`` will remove all subscriptions to AMPS.


:param sub_id: The subscription ID to remove.
:type sub_id: str
)docstring";


static const char* get_uri_doc = R"docstring(get_uri()
Gets the URI string passed into the :class:`Client` during the :meth:`connect` invocation.


:returns: The URI string.
)docstring";


static const char* publish_flush_doc = R"docstring(publish_flush(timeout=0, ack_type=Message.AckType.ProcessedEnum)
Ensures that pending AMPS messages are sent and have been processed by the
AMPS server. When the client has a publish store configured, waits until
all messages that are in the store at the time the command is called have
been acknowledged by AMPS. Otherwise, issues a ``flush`` command
and waits for the server to acknowledge that command.

This method blocks until messages have been processed or
until the timeout expires, and is most useful when the application reaches
a point at which it is acceptable to block to ensure that messages are
delivered to the AMPS server. For example, an application might call
``publish_flush`` before exiting.

One thing to note is that if AMPS is unavailable (HA Client), ``publish_flush``
needs to wait for a connection to come back up, which may look like it's hanging.


:param timeout: The maximum time to wait for the messages to be acknowledged
                as persisted, or for the flush command to be acknowledged
                by AMPS (in milliseconds). ``0`` indicates to wait indefinitely.
:type timeout: int
:param ack_type: Whether the command should wait for a Processed or a
                 Persisted ack when sending the ``flush`` command.
:type ack_type: int
)docstring";


static const char* flush_doc = R"docstring(flush(timeout=0)
Another name for :meth:`publish_flush`.


:param timeout: The maximum time to wait for the messages to be acknowledged
                as persisted, or for the flush command to be acknowledged
                by AMPS (in milliseconds). ``0`` indicates to wait indefinitely.
:type timeout: int
)docstring";


static const char* set_publish_store_doc = R"docstring(set_publish_store(publish_store)
Sets a publish store on self.


:param publish_store: A :class:`PublishStore` or :class:`MemoryPublishStore` instance.
)docstring";


static const char* set_bookmark_store_doc = R"docstring(set_bookmark_store(bookmark_store)
Sets a bookmark store on self.


:param bookmark_store: A :class:`MMapBookmarkStore` or :class:`MemoryBookmarkStore` instance,
                      or a custom object that implements the required bookmark store methods.
)docstring";


static const char* set_failed_write_handler_doc = R"docstring(set_failed_write_handler(failedWriteHandler)
Sets a failed write handler on self.

For example, you might implement a function like::

 def PrintFailedWrites(message, reason):
     output = "Uh-oh, something went wrong writing to AMPS. (%s) " % reason
     if message is not None:
           output += "Topic: %s, Data snippet: %s..." % 
                   (message.get_topic(), message.get_data()[0:20])
     print(output)


:param failedWriteHandler: A callable object to be invoked when AMPS indicates that a published message is not
                           written. This could be because a duplicate message already exists in the transaction
                           log, this client is not entitled to publish to the topic, the message failed to parse,
                           or other similar reasons.
                           Parameters to this callable are an AMPS *message* when the client has a message saved
                           in the publish store, and a string that contains the *reason* the publish failed.
)docstring";


static const char* add_connection_state_listener_doc = R"docstring(add_connection_state_listener(listener_callable)
Sets a function to be called when this client connects or disconnects from AMPS.


:type listener_callable: A python function or other callable that takes a single value.
:param listener_callable: This function will be passed True if a connection is established, False if
                          a disconnect occurs. Notice that when a connection is established, the client
                          has not yet logged in or completed any recovery steps. The application should
                          not issue commands on the client until recovery is completed.
)docstring";


static const char* remove_connection_state_listener_doc = R"docstring(remove_connection_state_listener(listener_callable)
Removes a listener function previously supplied to :meth:`add_connection_state_listener`.


:type listener_callable: A python function or other callable that takes a single value.
:param listener_callable: The function or callable to be removed.
)docstring";


static const char* set_transport_filter_doc = R"docstring(set_transport_filter(transport_filter_callable)
Sets a function to be called when this client sends or receives data.


:type transport_filter_callable: A python function or other callable that takes two parameters: data and direction.
:param transport_filter_callable: This function is passed a string ('data') containing the raw bytes sent or received.
                                  The 'direction' parameter is False if the data is being sent to the server, or True
                                  if data is received from the server.
)docstring";


static const char* set_thread_created_callback_doc = R"docstring(set_thread_created_callback(thread_created_callable)
Sets a function to be called when this client creates a thread used to receive data from the server.


:type thread_created_callable: A python function or other callable that takes no parameters.
:param thread_created_callable: This function is called by the newly created thread.
)docstring";


static const char* ack_doc = R"docstring(ack(message,options=None) OR ack(topic,bookmark,options=None)
Acknowledges a message queue message.


:param message: An :class:`AMPS.Message` object to ack, OR
:param topic: The topic of the message to ack.
:param bookmark: The bookmark of the message to ack.
:param options: An optional string to include in the ack such as ``cancel``.
)docstring";


static const char* set_ack_batch_size_doc = R"docstring(set_ack_batch_size(batch_size)
Sets the batch size used for batching message queue ack messages.


:param batch_size: The number of ack messages to batch before sending.
)docstring";


static const char* get_ack_batch_size_doc = R"docstring(get_ack_batch_size()
Gets the current batch size used for batching message queue acknowledgment messages.


:returns: The current batch size used for batching message queue ack messages.
)docstring";


static const char* set_auto_ack_doc = R"docstring(set_auto_ack(enabled)
Enables or disables auto-acknowledgment of message queue messages.


:param enabled: True to enable auto-acknowledgment of message queue messages.
:type enabled: Boolean
)docstring";


static const char* get_auto_ack_doc = R"docstring(get_auto_ack()
Called to check if auto-acknowledgment of message queue messages is enabled.


:returns: True, if auto-acknowledgment of message queue messages is enabled.
)docstring";


static const char* get_ack_timeout_doc = R"docstring(get_ack_timeout()
Gets the current time (milliseconds) before queued acknowledgment messages are sent.


:returns: The current time (milliseconds) before queued ack messages are sent.
)docstring";


static const char* set_ack_timeout_doc = R"docstring(set_ack_timeout(timeout)
Sets the time before queued ack messages are sent.


:param timeout: The maximum amount of time to wait after adding the first message to an acknowledgment
                batch before sending the batch, in milliseconds. 0 indicates that the client will wait
                until the batch is full. A value of 0 is not recommended unless the batch size is set to 1.
)docstring";


static const char* set_retry_on_disconnect_doc = R"docstring(set_retry_on_disconnect(enabled)
Enables or disables automatic retry of a command to AMPS after a reconnect. This behavior is enabled by default.
       
       .. note:: Clients using a publish store will have all publish
         messages sent, regardless of this setting. Also, Clients with
         a subscription manager, including all HAClients, will have all
         subscribe calls placed.


:param enabled: False to disable automatic retry of commands to AMPS.
:type enabled: Boolean
)docstring";


static const char* get_retry_on_disconnect_doc = R"docstring(get_retry_on_disconnect()
Called to check if automatic retry of a command to AMPS after a reconnect is enabled.


:returns: True, if automatic retry of a command to AMPS after a reconnect is enabled.
)docstring";


static const char* set_default_max_depth_doc = R"docstring(set_default_max_depth(depth)
Sets a default maximum depth for all new ``MessageStream`` objects
that are returned from synchronous API calls such as :meth:`execute()`.


:param depth: The new depth to use. A depth of ``0`` means no max and is the default.
:type depth: int
)docstring";


static const char* get_default_max_depth_doc = R"docstring(get_default_max_depth()
Gets the maximum depth for any new ``MessageStream``.


:returns: The current maximum depth for any new ``MessageStream``. ``0`` is no maximum.
)docstring";


static const char* set_global_command_type_message_handler_doc = R"docstring(set_global_command_type_message_handler(command,message_handler)
Add a message handler to the :class:`Client` to handle messages from the
server with the specified command.


:param command: The command to send to the handler.
                Valid values are ``ack`` and ``heartbeat``.
:type command: str
:param message_handler: The message handler that will receive messages
                        of the command specified.
:type message_handler: :class:`MessageHandler`
)docstring";


static const char* get_error_on_publish_gap_doc = R"docstring(get_error_on_publish_gap()
Indicates whether :exc:`PublishStoreGapException` can be thrown by the client publish store if the
client logs onto a server that appears to be missing messages no longer held in the store.


:returns: True if :exc:`PublishStoreGapException` can be thrown, False otherwise.

)docstring";


static const char* set_error_on_publish_gap_doc = R"docstring(set_error_on_publish_gap(error_on_publish_gap)
Called to enable or disable throwing :exc:`PublishStoreGapException`.


:param error_on_publish_gap: If True, :exc:`PublishStoreGapException` can be thrown by the
                             client publish store if the client logs onto a server that
                             appears to be missing messages no longer held in the store.
:type error_on_publish_gap: Boolean
)docstring";

static const char* add_http_preflight_header_doc = R"docstring(add_http_preflight_header(header)
Called to add a header line to the HTTP preflight message sent via a proxy.


:param header: The full header line to append to the HTTP upgrade message.
:type header: string
)docstring";

static const char* add_http_preflight_header_key_value_doc = R"docstring(add_http_preflight_header_key_value(key, value)
Called to add key: value as a header line to the HTTP preflight message sent via a proxy.


:param key: The key in the header line to append to the HTTP upgrade message.
:type key: string
:param value: The value in the header line to append to the HTTP upgrade message.
:type value: string
)docstring";

static const char* clear_http_preflight_headers_doc = R"docstring(clear_http_preflight_headers()
Called to clear all HTTP header lines previously set for preflight.
)docstring";

static const char* set_publish_batching_doc = R"docstring(set_publish_batching(batchSize, batchTimeoutMillis)
Sets the max bytes to cache and max timeout in millis for caching delta_publish and publish commands.
Most useful when your message data is small compared to tcp packet size.


:param batchSize: The max number of bytes to cache before sending.
:type batchSize: unsigned long
:param batchTimeoutMillis: The max ms between sending batches.
:type batchTimeoutMillis: unsigned long
)docstring";
