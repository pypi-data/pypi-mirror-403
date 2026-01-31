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

static const char* class_doc = R"docstring(HAClient(name, publish_store=None, bookmark_store=None, no_store=False)
AMPS ``HAClient`` Object used for highly-available client connections. Derives from :class:`Client`.

An example of a Python client publishing a JSON message using the ``HAClient`` is listed below::

    client = AMPS.HAClient("test_client")

    chooser = AMPS.DefaultServerChooser()
    chooser.add("tcp://127.0.0.1:9004/amps/json")
    client.set_server_chooser(chooser)

    try:
      client.connect_and_logon()
      client.publish("topic_name",'{"a":1,"b":"2"}')
    finally:
      client.close()

**Constructor Arguments:**


:param name: The unique name for this client. AMPS does not enforce
             specific restrictions on the character set used, however some protocols
             (for example, XML) may not allow specific characters. 60East recommends
             that the client name be meaningful, short, human readable, and avoid
             using control characters, newline characters, or square brackets.
:param publish_store: An optional file name for the client's local publish store. If not supplied, a memory-backed publish store is used.
:param bookmark_store: An optional file name for the client's local bookmark store. If not supplied, a memory-backed bookmark store is used.
:param no_store: Pass ``no_store=True`` to indicate that a memory bookmark and/or publish store should not be used.
)docstring";


static const char* connect_and_logon_doc = R"docstring(
Connects and logs on using the ``ServerChooser`` you've supplied via :meth:`set_server_chooser`. Will continue
attempting to connect and logon to each URI returned by the ``ServerChooser`` until the connection succeeds or
the ``ServerChooser`` returns an empty URI.
)docstring";


static const char* haclient_connect_doc = R"docstring(
Not used in the ``HAClient``; call :meth:`connect_and_logon` to connect and log on to AMPS once a server chooser is set.
)docstring";


static const char* discard_doc = R"docstring(discard(message)
Discards a message from the local bookmark store.


:param message: An ``AMPS.Message`` instance that was received from a bookmark subscription.
:type message: AMPS.Message
)docstring";


static const char* prune_store_doc = R"docstring(prune_store(tmp_file_name)
Prunes the local bookmark store. If it's file-based, it will remove unnecessary entries from the file.


:param tmp_file_name: Optional file name to use for temporary storage during prune operation.
:type tmp_file_name: string
)docstring";


static const char* get_most_recent_doc = R"docstring(get_most_recent(sub_id)
Gets the most recent bookmark from the local bookmark store for the given subscription ID.


:param sub_id: The subscription ID for which to retrieve the most recent bookmark.
:type sub_id: string
)docstring";


static const char* set_server_chooser_doc = R"docstring(set_server_chooser(serverChooser)
Sets a server chooser on self.


:param serverChooser: A ``ServerChooser`` instance, such as a :class:`DefaultServerChooser`.
:type serverChooser: ServerChooser
)docstring";


static const char* get_server_chooser_doc = R"docstring(get_server_chooser()
Gets self's server chooser and returns it.
)docstring";


static const char* set_logon_options_doc = R"docstring(set_logon_options(options)
Sets a logon options on self.


:param options: An options string to be passed to the server during logon, such as ``ack_conflation=100ms``.
:type options: string
)docstring";


static const char* get_logon_options_doc = R"docstring(get_logon_options()
Gets self's logon options string and returns it.
)docstring";


static const char* set_timeout_doc = R"docstring(set_timeout(timeout)
Sets the timeout, in milliseconds, used when sending a logon command to the server.
Default value is 10000 (10 seconds).


:param timeout: The number of milliseconds to wait for a server response to logon. ``0`` indicates no timeout.
)docstring";


static const char* set_reconnect_delay_doc = R"docstring(set_reconnect_delay(reconnect_delay)
Sets the delay in milliseconds used when reconnecting, after a disconnect occurs. Calling this method
creates and installs a new :class:`FixedDelayStrategy` in this client.
Default value is 200 (0.2 seconds).


:param reconnect_delay: The number of milliseconds to wait before reconnecting, after a disconnect occurs.
)docstring";


static const char* set_reconnect_delay_strategy_doc = R"docstring(set_reconnect_delay_strategy(reconnect_delay_strategy)
Sets the reconnect delay strategy object used to control delay behavior
when connecting and reconnecting to servers.


:param reconnect_delay_strategy: The reconnect delay strategy object to use when connecting
                                 and reconnecting to AMPS instances. The object must have
                                 the following two methods defined:

                                    ``get_connect_wait_duration(uri)``:
                                      *uri* - A string containing the next URI AMPS will connect with.
                                      *Returns* an integer representing the time in milliseconds to wait
                                      before connecting to that URI.

                                    ``reset()``:
                                      Resets the state of self after a successful connection.
)docstring";


static const char* get_reconnect_delay_strategy_doc = R"docstring(get_reconnect_delay_strategy()
Returns the reconnect delay strategy object used to control delay behavior
when connecting and reconnecting to servers.


:returns: The reconnect delay strategy object.
)docstring";


static const char* get_default_resubscription_timeout_doc = R"docstring(get_default_resubscription_timeout()
Gets the default timeout, in milliseconds, used when attempting to resubscribe
each subscription after a re-connect.
)docstring";


static const char* set_default_resubscription_timeout_doc = R"docstring(set_default_resubscription_timeout(timeout)
Sets the default timeout, in milliseconds, used when attempting to resubscribe
each subscription after a re-connect.
Default value is ``0`` (no timeout).


:param timeout: The number of milliseconds to wait for a server response. ``0`` indicates no timeout.
)docstring";


static const char* get_resubscription_timeout_doc = R"docstring(get_resubscription_timeout()
Gets the timeout, in milliseconds, used when attempting to resubscribe each
subscription after a re-connect.
)docstring";


static const char* set_resubscription_timeout_doc = R"docstring(set_resubscription_timeout(timeout)
Sets the timeout, in milliseconds, used when attempting to resubscribe each
subscription after a re-connect. 

Default value is ``0`` (no timeout), but can be changed using :meth:`set_default_resubscription_timeout`.


:param timeout: The number of milliseconds to wait for a server response. ``0`` indicates no timeout.
)docstring";


static const char* set_failed_resubscribe_handler_doc = R"docstring(set_failed_resubscribe_handler(handler)
Sets the handler that is called if a resubscribe after failover, fails to complete successfully.
The subscribe Message, requested ack types, and exception are passed to the handler. The handler
should return False to force a new attempt at ``connect_and_logon`` or True to ignore the failure and
remove the subscription from the subscription manager.


:param handler: The callable handler to invoke.
)docstring";

