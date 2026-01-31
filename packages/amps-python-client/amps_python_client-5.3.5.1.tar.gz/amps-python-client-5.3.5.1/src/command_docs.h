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


#define COMMAND_SETTER_BOILERPLATE "\n\nNot all headers are processed by AMPS for all commands. See the *AMPS Command Reference* for which headers are used by AMPS for a specific command.\n\n:param value: The new value to set for the header.\n\n:returns: This command."


static const char* command_class_doc = R"docstring(Command(command_name)
``AMPS.Command`` represents a single message (or *command*) sent to the
AMPS server. The class provides methods for headers that are used
for commands to the server. Applications typically use this class
to create outgoing requests to AMPS. The responses to requests,
whether acknowledgments or messages that contain data, are
returned as instances of the :class:`AMPS.Message` class.

The :class:`AMPS.Client` provides named convenience methods that support
a subset of the options available via a Command. For most applications,
the recommended approach is to use the ``publish()`` methods for sending
data to AMPS (unless the application needs to set options not
available through that method) and use the Command class for queries,
subscriptions, and to remove data.

To use the Command class to run a command on the server, you create the
Command, set options as described in the *Command Cookbook* in the
*AMPS Command Reference*, and then use :func:`AMPS.Client.execute_async()`
to process messages asynchronously,or :func:`AMPS.Client.execute()`
to process messages synchronously.

**Constructor Arguments:**


:param command_name: The name of the command to send to the server. 
                     For example, ``sow``, ``sow_and_subscribe`` or ``publish``.
)docstring";


static const char* reset_doc = R"docstring(reset(command)
Resets this command with a new Command type and re-initializes all other fields.


:param command: A string indicating the AMPS command.
)docstring";


static const char* set_sow_key_doc = R"docstring(set_sow_key(value)
Sets the SOW key for this command. This is useful for ``publish`` commands.

For a ``publish`` command, sets the SOW key for a message when the SOW
is configured so that the publisher is responsible for determining and
providing the SOW key. This option is ignored on a ``publish`` when
the topic is configured with a ``Key`` field in the SOW file.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_sow_keys_doc = R"docstring(set_sow_keys(value)
The SOW keys for a command are a comma-separated list
of the keys that AMPS assigns to SOW messages. The SOW key for a
message is available through the :meth:`Message.get_sow_key` method on a message.

For a ``sow_delete`` command, this list indicates the set of messages to be deleted.

For a query or subscription, this list indicates the set of messages to
include in the query or subscription.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_command_id_doc = R"docstring(set_command_id(value)
Sets the value of the *command_id* header. This header, set by the client,
is used to identify responses to the command and correlate later messages
and commands. For example, the client sets a command ID on a subscription
request to AMPS, and can later use that command ID to unsubscribe. The
command ID is returned on ack messages in response to the command. The AMPS
FAQ has details on the relationship between command ID, subscription ID, and
query ID.

If not set, the AMPS Client will automatically fill in a ``command_id``
when the client needs one to be present (for example, when the client
needs a ``processed`` acknowledgment to be able to tell if a
``subscribe`` command succeeded or failed).


:param value: The new value for this header.
:returns: This command.
)docstring";


static const char* set_topic_doc = R"docstring(set_topic(value)
Sets the value of the topic header, which specifies the topic that
the command applies to. For a ``publish`` command, this field is
interpreted as the literal topic to publish to. For commands such as
``sow`` or ``subscribe``, the topic is interpreted as a literal topic
unless there are regular expression characters present in the topic
name. For those commands, if regular expression characters are present,
the command will be interpreted as applying to all topics with names
that match the regular expression.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_filter_doc = R"docstring(set_filter(value)
Sets the value of the filter header.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_order_by_doc = R"docstring(set_order_by(value)
Sets the value of the order by header. This header is only used for SOW query results,
and must contain one or more XPath identifiers and an optional ``ASC`` or ``DESC`` order
specifier (for example, ``/orderTimestamp DESC``).
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_sub_id_doc = R"docstring(set_sub_id(value)
Sets the subscription ID of self.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_query_id_doc = R"docstring(set_query_id(value)
Sets the query ID of self.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_bookmark_doc = R"docstring(set_bookmark(value)
Sets the value of the bookmark header. For a subscription, this identifies the point in the
transaction log at which to begin the replay. For a ``sow_delete`` (queue acknowledgment), this
indicates the message or messages to acknowledge. For a query on a SOW topic with ``History``
configured, this indicates the point at which to query the topic. Setting the bookmark on a
publish message has no effect.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_correlation_id_doc = R"docstring(set_correlation_id(value)
Sets the value of the correlation ID header. The AMPS server does not process or interpret 
this value; however, the value must contain only characters that are valid in Base64 encoding 
for the server to be guaranteed to process the Command.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_options_doc = R"docstring(set_options(value)
Sets the value of the options header. The options available, and how
AMPS interprets the options, depend on the command being sent. The
:class:`AMPS.Message.Options` class contains constants and helper
methods for building an options string. See the *AMPS Command Reference*
for details on the options available for a given command.


:param value: The value to set.
:returns: This command.
)docstring";


static const char* add_ack_type_doc = R"docstring(add_ack_type(value)
Adds an ack type to this command, in addition to any other ack types
that have been previously set or that will be set by the Client.


:param value: The ack type to add.
:returns: This command.
)docstring";


static const char* set_ack_type_doc = R"docstring(set_ack_type(value)
Sets the ack type for this command, replacing any other ack types
that have been previously set or that will be set by the Client.


:param value: The ack type to set.
:returns: This command.
)docstring";


static const char* set_ack_type_enum_doc = R"docstring(set_ack_type_enum(value)
Sets the ack type enum for this command, replacing any other ack type enums
that have been previously set or that will be set by the Client.


:param value: The ack type enum to set.
:returns: This command.
)docstring";


static const char* get_ack_type_doc = R"docstring(get_ack_type()
Gets the ack type for this command.


:returns: The ack type as a string.
)docstring";


static const char* get_ack_type_enum_doc = R"docstring(get_ack_type_enum()
Gets the ack type enum for this command.


:returns: The ack type as an enum.
)docstring";


static const char* set_data_doc = R"docstring(set_data(value)
Sets the data for this command. This is used for ``publish`` commands and for ``sow_delete`` commands.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_timeout_doc = R"docstring(set_timeout(value)
Sets the amount of time that the Client will wait for a ``processed``
acknowledgment from the server to be received and consumed before
abandoning the request; this option is *only* used by the Client and is not
sent to the server. The acknowledgment is processed on the client receive thread.
This option is expressed in milliseconds, where a value of ``0`` means to wait
indefinitely.


:param value: The value to set.
:returns: This command.
)docstring";


static const char* set_top_n_doc = R"docstring(set_top_n(value)
Sets the top N header of this command. Although AMPS accepts a top N value in the header
of a command, most AMPS applications pass the value in the ``top_n`` option for clarity.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_batch_size_doc = R"docstring(set_batch_size(value)
Sets the batch size header, which is used to control the number of records that AMPS will 
send in each batch when returning the results of a SOW query. See the *AMPS User Guide* for 
details on SOW query batches.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_expiration_doc = R"docstring(set_expiration(value)
Sets the expiration of self. For a publish to a SOW topic or queue, this sets the number of 
seconds the message will be active before expiring.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* set_sequence_doc = R"docstring(set_sequence(value)
Sets the sequence of self for ``publish``, ``delta_publish``, or ``sow_delete`` commands. A publish store 
on the client may replace this value.
)docstring"
COMMAND_SETTER_BOILERPLATE;


static const char* get_sequence_doc = R"docstring(get_sequence()
Gets the sequence of self for ``publish``, ``delta_publish``, or ``sow_delete`` commands.
This can be checked after calling ``execute`` or ``executeAsync`` to query the sequence
number that was used, if any.


:returns: The sequence number used in the last ``publish``, ``delta_publish``, or ``sow_delete`` command.
)docstring";
