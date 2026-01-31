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

static const char* memorypublishstore_class_doc = R"docstring(MemoryPublishStore
A publish store that keeps messages in memory. This class is the
default publish store for a Python HAClient. The HAClient manages
storing messages in the publish store, replaying messages to the
server after failover, and removing messages from the store. With
this publish store, an application typically checks to be sure
that the publish store is empty (that is, all messages have been
persisted in the AMPS server) before exiting.

**Constructor Arguments:**


:param blocksPerRealloc: The number of blocks to add to the memory used by the store whenever it needs to grow. Optional, default is 10000.
:type blocksPerRealloc: unsigned long
:param errorOnPublishGap: If True, a PublishStoreGapException can be thrown by the store if the client logs onto a server that appears to be missing messages no longer held in the store. Optional, default is False.
:type errorOnPublishGap: Boolean
:param blockSize: The size (in bytes) for each block in which messages are stored. Optional, default is 2048.
:type blockSize: unsigned long
)docstring";

static const char*  store_doc  = R"docstring(store(message)
Store the provided message into the publish store. Returns the sequence number that should be assigned to the message.


:param message: The message to put into the store.
:type message: AMPS.Message
)docstring";

static const char*  discard_up_to_doc  = R"docstring(discard_up_to(sequence)
Discard all messages in the publish store with a sequence number less than or equal to the provided argument.


:param sequence: The highest sequence number to discard.
:type sequence: unsigned long
)docstring";

static const char*  replay_doc  = R"docstring(replay(handler)
Replays all messages currently in the publish store via the provided message handler.

:param handler: The message handler to call with each message.
)docstring";

static const char*  replay_single_doc  = R"docstring(replay_single(handler, sequence)
Replays the message with the given sequence number if it is currently in the publish store via the provided message handler.


:param handler: The message handler to call with each message.
:param sequence: The sequence number of the message to replay.
:type sequence: unsigned long
)docstring";

static const char*  get_unpersisted_count_doc  = R"docstring(get_unpersisted_count()
Returns the number of messages published which have not been ACK'ed by the server.
)docstring";

static const char*  get_lowest_unpersisted_doc  = R"docstring(get_lowest_unpersisted()
Returns the sequence number of the oldest message in the publish store.
)docstring";

static const char*  get_last_persisted_doc  = R"docstring(get_last_persisted()
Returns the sequence number of last message ACK'ed by the server.
)docstring";

static const char*  set_resize_handler_doc  = R"docstring(set_resize_handler()
Sets the object to call when the store needs to resize.
)docstring";

static const char*  get_error_on_publish_gap_doc  = R"docstring(get_error_on_publish_gap()
Indicates whether :exc:`PublishStoreGapException` can be thrown
by the client publish store if the client logs onto a server that appears to be missing messages no longer held in the store.


:returns: True if :exc:`PublishStoreGapException` can be thrown False otherwise.
)docstring";

static const char*  set_error_on_publish_gap_doc  = R"docstring(set_error_on_publish_gap(error_on_publish_gap)
Called to enable or disable throwing :exc:`PublishStoreGapException`.


:param error_on_publish_gap: If True :exc:`PublishStoreGapException` can be thrown by the client publish store if the client logs onto a server that appears to be missing messages no longer held in the store.
:type error_on_publish_gap: Boolean
)docstring";
