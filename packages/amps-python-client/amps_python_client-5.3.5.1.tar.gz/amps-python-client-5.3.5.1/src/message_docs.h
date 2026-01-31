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


// Boilerplate is used in both generic documentation (for seldom used /
// specialized fields) and in expanded documentation (for frequently used
// or potentially confusing fields).

#define SETTER_BOILERPLATE(x) "\n\nNot all headers are processed by AMPS for all commands. See the *AMPS Command Reference* for which headers are used by AMPS for a specific command.\n\n:param value: The new value for ``" #x "``.\n\n:returns: This message."

#define GETTER_BOILERPLATE(x) "\n\nNot all headers are populated by AMPS for all commands. See the *AMPS Command Reference* for which headers are returned by AMPS in response to a specific command\n\n:returns: The value of ``" #x "`` on this message."

// Helper macros to expand the boilerplate macros within strings
#define EXPAND_SETTER_BOILERPLATE(x) "Sets the value of " #x " for this message." SETTER_BOILERPLATE(x)
#define EXPAND_GETTER_BOILERPLATE(x) "Gets the value of " #x " for this message." GETTER_BOILERPLATE(x)

// Standard documentation simply sets up the generic documentation

#define STANDARD_GETTER_DOC(x) "Gets the value of ``" #x "`` for this message." GETTER_BOILERPLATE(x)

#define STANDARD_SETTER_DOC(x) "Sets the value of ``" #x "`` for this message." SETTER_BOILERPLATE(x)


#define STANDARD_DOC(x,y) static const char* set_##x ##_docs = STANDARD_SETTER_DOC(x); \
  static const char* get_##x ##_docs = STANDARD_GETTER_DOC(x);


/////////////////////////////////////////////////
// Documentation strings follow
//
// For fields that have not seemed to be confusing,
// we use the boilerplate docs.
/////////////////////////////////////////////////

static const char* amps_message_class_docs = R"docstring(
:class:`AMPS.Message` represents a single message sent to or received from the
AMPS server. The class provides methods for every header that can be
present, whether or not that header will be populated or used in a
particular context.

Applications typically use an :class:`AMPS.Command` to create outgoing
requests to AMPS, and receive instances of :class:`AMPS.Message` in
response.

The *AMPS Command Reference* provides details on which headers are used
by AMPS and which will be populated on messages received from AMPS,
depending on the command the :class:`AMPS.Message` responds to, the options
and headers set on that command, and the type of the response message.

:class:`AMPS.Message` has been designed to minimize unnecessary memory
allocation. Copying a Message does not copy the underlying content
of the message. When the AMPS client provides a Message to a
``MessageHandler`` function, the data in that Message is a region
in the buffer that the AMPS client uses to read from the socket. If your
application will use the Message after the ``MessageHandler`` returns,
you should use the :func:`__deepcopy__()` function to
copy the underlying data as well as the Message, since in this case the
AMPS client will reuse the underlying buffer once the ``MessageHandler``
returns. See the *AMPS Python Developer Guide* section on asynchronous
message processing for more details.

If your application has the need to bypass most of the :class:`AMPS.Client`
infrastructure for some reason when sending commands to AMPS, the
:class:`AMPS.Message` / :func:`AMPS.Client.send()` interface provides the
flexibility to do so. In return, your application must provide
functionality that is normally provided automatically by the
:class:`AMPS.Client` (for example, tracking subscriptions for failover,
recording the message in the publish store and managing success or
failure of the publish, and so on). Although this functionality is
available for flexibility, it is rarely needed in practice. 60East
recommends using :class:`AMPS.Command` objects with
:func:`AMPS.Client.execute()` and
:func:`AMPS.Client.execute_async()` for sending commands to AMPS.
)docstring";


static const char* commands_class_doc = R"docstring(
This class provides special values for AMPS Commands.

Each command string is available as a member:

e.g., ``Commands.SOWAndSubscribe`` is ``"sow_and_subscribe"``

Each command also has an Enum version that is returned by ``get_command_enum``:

e.g., ``Commands.PublishEnum = 1``
)docstring";


static const char* acktypes_class_doc = R"docstring(
This class provides special values for AMPS ack commands.

Each ack type string is available as a member:

e.g., ``AckTypes.Persisted`` is ``"persisted"``

Each ack type also has an Enum version used for ``Command.set_ack_type_enum``:

e.g., ``command.set_ack_type_enum(AckTypes.Processed | AckTypes.Completed)``
)docstring";


// BatchSize

static const char* set_batch_size_docs = R"docstring(
Sets the value of the *BatchSize* header, which is used to control the number of
records that AMPS will send in a batch when returning the results of a SOW query.
See the *AMPS User Guide* for details on SOW query batches.
)docstring" SETTER_BOILERPLATE(batch_size);


static const char* get_batch_size_docs = R"docstring(
Gets the value of the *BatchSize* header.
)docstring" GETTER_BOILERPLATE(batch_size);

// Bookmark

static const char* set_bookmark_docs = R"docstring(
Sets the value of the *Bookmark* header. For a subscription, this identifies the point in the
transaction log at which to begin the replay. For a ``sow_delete`` (queue acknowledgment), this
indicates the message or messages to acknowledge. For a query on a SOW topic with ``History``
configured, this indicates the point at which to query the topic. Setting the bookmark on a publish
message has no effect.
)docstring" SETTER_BOILERPLATE(bookmark);


static const char* get_bookmark_docs = R"docstring(
Gets the value of the *Bookmark* header. For messages returned from AMPS, this is an opaque
identifier that AMPS can use to locate the message in the transaction log, and is returned
on messages that are produced from the transaction log (for example, messages delivered from
queues or returned in response to a bookmark subscribe command).
)docstring" GETTER_BOILERPLATE(bookmark);

// ClientName

static const char* set_client_name_docs = R"docstring(
Sets the value of the *ClientName* header. In a ``logon`` command, this header sets the client
name for the connection.
)docstring" SETTER_BOILERPLATE(client_name);


static const char* get_client_name_docs = STANDARD_GETTER_DOC(client_name);

// Command

static const char* set_command_docs = R"docstring(
Sets the value of the *Command* header. Every message sent to AMPS is required to have a *Command*
header set, which specifies how the message is to be intrepreted. It is an error to send a message
to AMPS without setting this field. See the *AMPS Command Reference* for details on the values that
AMPS accepts for this header, how those commands are interpreted, and what headers and options can
be set for a given command.

.. NOTE::

    If you are building a command to be sent to AMPS, using the :class:`AMPS.Command` class rather than
    :class:`Message` is recommended for most purposes.


:param value: The new value for the Command.
)docstring";


static const char* get_command_docs = R"docstring(
Gets the value of the *Command* header, which specifies what type of message this is. Every message
from AMPS has the Command header set, and should interpret the message based on the Command. See the
*AMPS Command Reference* for details on what Command values will be returned in response to a given
command to AMPS, what header fields are provided on Messages with a given Command value, and how an
application should interpret those header fields.


:returns: The value of the Command set on this message.
)docstring";

// CorrelationId

static const char* get_correlation_id_docs = R"docstring(
Gets the value of the *correlation_id* header. The correlation ID is a unique identifier provided
by the publisher when a command is sent to AMPS. The AMPS server does not process or interpret
this value; it is returned verbatim and provided to subscribers of the message without interpreting
or changing the identifier.
)docstring" GETTER_BOILERPLATE(correlation_id);


static const char* set_correlation_id_docs = R"docstring(
Sets the value of the *correlation_id* header. The correlation ID is a unique identifier provided
by the publisher of a message. AMPS provides the identifier to subscribers of the message without
interpreting or changing the identifier. The correlation ID must contain only characters valid in
base-64 encoding to guarantee that the server processes the message correctly. Base-64 encoding
uses a subset of characters, typically consisting of uppercase letters (A-Z), lowercase letters
(a-z), digits (0-9), and two additional characters, usually '+' and '/'.
)docstring" SETTER_BOILERPLATE(correlation_id);

// MessageType

static const char* set_message_type_docs = R"docstring(
Sets the value of the *message_type* header. This header is used during logon to set the message
type for the connection when a message type is provided in the connection URI. It is ignored for
other commands.
)docstring" SETTER_BOILERPLATE(message_type);


static const char* get_message_type_docs = STANDARD_GETTER_DOC(message_type);

// SowKey

static const char* set_sow_key_docs = R"docstring(
Sets the value of the *sow_key* header. When publishing a message to a topic in the State of the
World (SOW) that is configured to require the publisher to set an explicit key (rather than having AMPS
calculate the key based on the message contents), the publisher uses this header to set the key to
be used.
)docstring" SETTER_BOILERPLATE(sow_key);


static const char* get_sow_key_docs = R"docstring(
Gets the value of the *sow_key* header. When a message is returned from a Topic in the State of the
World (SOW), this header provides the key that the AMPS server uses to identify the message.
)docstring" GETTER_BOILERPLATE(sow_key);

// SowKeys

static const char* set_sow_keys_docs = R"docstring(
Sets the value of the *sow_keys* header. This header contains a comma-delimited list of identifiers
representing the set of ``SowKeys`` this message applies to. This can be useful for commands that
operate on multiple SOW records, such as a ``sow_delete`` that specifies a set of keys to remove. The
``SowKey`` is a unique key used to identify a SOW record within AMPS. For messages received from a
SOW, AMPS provides the SOW key on each message.
)docstring" SETTER_BOILERPLATE(sow_key);

static const char* get_sow_keys_docs = STANDARD_GETTER_DOC(sow_keys);

// Timestamp

static const char* get_timestamp_docs = R"docstring(
Gets the value of the *timestamp* header. When the ``timestamp`` option is specified on a command,
the ``publish`` and ``sow`` messages returned will include the time at which the AMPS server
processed the message, formatted as an ISO-8601 string.
)docstring" GETTER_BOILERPLATE(timestamp);

static const char* set_timestamp_docs = R"docstring(
Sets the value of the *timestamp* header. The timestamp is set by AMPS at the time it processes
the message and is available for the AMPS Client to use when constructing a message. No commands
to the AMPS server use this header.
)docstring" SETTER_BOILERPLATE(timestamp);

// CommandId

static const char* set_command_id_docs = R"docstring(
Sets the value of the *command_id* header. This header, set by the client, is used to identify
responses to the command and correlate later messages and commands. For example, the client sets
a command ID on a subscription request to AMPS, and can later use that command ID to unsubscribe.
The command ID is returned on ack messages in response to the command. The AMPS FAQ has details on
the relationship between command ID, subscription ID, and query ID.

If not set, the AMPS Client will automatically fill in a ``command_id`` when the client needs one
to be present (for example, when the client needs a ``processed`` acknowledgment to be able to tell
if a ``subscribe`` command succeeded or failed).
)docstring" GETTER_BOILERPLATE(command_id);

static const char* get_command_id_docs = STANDARD_GETTER_DOC(command_id);

// Expiration

static const char* set_expiration_docs = R"docstring(
Sets the value of the *expiration* header. The expiration is used on a publish command to set the lifetime
of a message. For the lifetime to be processed by AMPS, the message must be published to a SOW topic or
queue that supports message expiration. See the *AMPS User Guide* for details.
)docstring" SETTER_BOILERPLATE(expiration);

static const char* get_expiration_docs = STANDARD_GETTER_DOC(expiration);

STANDARD_DOC(ack_type, AckType)
STANDARD_DOC(filter, Filter)
STANDARD_DOC(group_seq_no, GroupSeqNo)
STANDARD_DOC(heartbeat, Heartbeat)
STANDARD_DOC(lease_period, LeasePeriod)
STANDARD_DOC(matches, Matches)
STANDARD_DOC(message_size, MessageSize)
STANDARD_DOC(options, Options)
STANDARD_DOC(order_by, OrderBy)
STANDARD_DOC(password, Password)
STANDARD_DOC(query_id, QueryId)
STANDARD_DOC(reason, Reason)
STANDARD_DOC(records_inserted, RecordsInserted)
STANDARD_DOC(records_returned, RecordsReturned)
STANDARD_DOC(records_updated, RecordsUpdated)
STANDARD_DOC(sequence, Sequence)
STANDARD_DOC(sow_deleted, SowDeleted)
STANDARD_DOC(status, Status)
STANDARD_DOC(sub_id, SubId)
STANDARD_DOC(sub_ids, SubIds)
STANDARD_DOC(timeout_interval, TimeoutInterval)
STANDARD_DOC(top_n, TopN)
STANDARD_DOC(topic, Topic)
STANDARD_DOC(topic_matches, TopicMatches)
STANDARD_DOC(user_id, UserId)
STANDARD_DOC(version, Version)
STANDARD_DOC(data, Data)


// Doc strings for Message.Options class

#define OPTIONS_REFERENCE " See the *AMPS Command Reference* and *AMPS User Guide* for details.\n\n"

#define OPTIONS_CONSTANT_DOC(x) "Adds the ``" #x "`` option to the current set of options." \
  OPTIONS_REFERENCE


static const char* amps_message_options_class_docs = R"docstring(
:class:`AMPS.Message.Options` is a class that provides
convenience methods for constructing an options string for use in a command
to AMPS. This class is intended to help in formatting the options. It does not
validate the values provided, that the options apply to any particular command,
or that the options have a particular result. The AMPS Python client (and the
AMPS server itself) accept options as a string, so there is no requirement
to use this class to format options.

.. code-block:: python

   cmd = AMPS.Command("sow_and_subscribe").set_topic("my_cool_topic")
             .set_options(str(AMPS.Message.Options().set_OOF().set_conflation("5s")))

.. NOTE::

    Not every option applies to every command. See the *AMPS User Guide* and *AMPS Command
    Reference* for details on what options are available on a given command, and what
    effect the option has.
)docstring";


static const char* amps_message_options_maxbacklog_docs = R"docstring(set_max_backlog(value)
Sets the ``max_backlog`` option, which defines the maximum number of unacknowledged queue
messages that a subscription is willing to accept at a given time. (The actual number of messages
allowed will be either this setting, or the per subscription maximum set for the queue, whichever
is smaller).

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The maximum backlog for the subscription.
)docstring";


static const char* amps_message_options_conflation_docs = R"docstring(set_conflation(value)
Sets the ``conflation`` option as a time interval such as
``250ms`` or ``1m``.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The conflation interval to set.
)docstring";


static const char* amps_message_options_conflation_key_docs  = R"docstring(set_conflation_key(value)
Sets the ``conflation_key`` for a subscription, as one or more XPath identifiers to use
to determine which messages are identical and should be conflated.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The key or keys for the command to conflate on.
)docstring";


static const char* amps_message_options_top_n_docs = R"docstring(set_top_n(value)
Sets the ``top_n`` value for a command.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The ``top_n`` value, as an integer.
)docstring";


static const char* amps_message_options_rate_docs = R"docstring(set_rate(value)
Sets the ``rate`` option, which optionally controls the maximum rate at which
a transaction log replay will produce messages.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The rate value as a message number, number of data bytes, or multiplier
              of the original message rate.
)docstring";


static const char* amps_message_options_rate_max_gap_docs = R"docstring(set_rate_max_gap(value)
Sets the ``rate_max_gap`` option, which controls the amount of time AMPS will go without
producing a message from a transaction log replay when the ``rate`` option is specified.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The maximum gap as an interval (such as ``30s``).
)docstring";


static const char* amps_message_options_skip_n_docs = R"docstring(set_skip_n(value)
Sets the ``skip_n`` value for a command.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The ``skip_n`` value as an integer.
)docstring";


static const char* amps_message_options_projection_docs = R"docstring(set_projection(value)
Sets the ``projection`` option, which defines the fields produced by an
aggregated subscription or aggregated query.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The projection definition for the command.
)docstring";


static const char* amps_message_options_grouping_docs = R"docstring(set_grouping(value)
Sets the ``grouping`` option, which defines how to group messages from the
original topic into result messages in an aggregated subscription or aggregated query.

See the *AMPS Command Reference* and *AMPS User Guide* for details.


:param value: The grouping definition for the command.
)docstring";


static const char* amps_message_options_bookmark_not_found_docs = R"docstring(set_bookmark_not_found(action)
Set the option for the action to take if the requested bookmark to
start the subscription is not found.


:param action: Can be one of "now", "epoch", or "fail".
)docstring";


static const char* amps_message_options_bookmark_not_found_now_docs = R"docstring(set_bookmark_not_found_now()
Set the option for the action to take if the requested bookmark to
start the subscription is not found to start at NOW instead.
)docstring";


static const char* amps_message_options_bookmark_not_found_epoch_docs = R"docstring(set_bookmark_not_found_epoch()
Set the option for the action to take if the requested bookmark to
start the subscription is not found to start at EPOCH instead.
)docstring";


static const char* amps_message_options_bookmark_not_found_fail_docs = R"docstring(set_bookmark_not_found_fail()
Set the option for the action to take if the requested bookmark to
start the subscription is not found to fail the command.
)docstring";
