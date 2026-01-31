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

static const char* memorybookmarkstore_class_doc = R"docstring(MemoryBookmarkStore(adapter)
A bookmark store that maintains information about the recovery
point for bookmark subscriptions in memory.

When the bookmark store is set on a Client or HAClient,
the AMPS client library manages adding subscriptions to the
store and tracking bookmarks as they arrive. The AMPS HAClient
uses the bookmark store on failover to recover bookmark subscriptions
at the appropriate point.

For a bookmark subscription, an application must discard messages
when they have been processed. The other methods on this class
are not typically called by the application during normal use.

A ``RecoveryPointAdapter`` may optionally be specified when created
to add something such as storage in a SOW using :class:`SOWRecoveryPointAdapter`
to prevent any message loss if the client application dies.


:param adapter: A ``RecoveryPointAdapter`` object that provides
                additional storage capabilities, such as 
                :class:`SOWRecoveryPointAdapter`.
                Default is None. *Optional*.
)docstring";
