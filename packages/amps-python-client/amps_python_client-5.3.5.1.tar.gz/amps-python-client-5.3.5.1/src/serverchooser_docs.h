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

static const char* serverchooser_class_doc = R"docstring(
A simple server chooser that keeps a list of AMPS instances and
Authenticators, and advances to the next one when failure occurs.

To use the ``DefaultServerChooser``, you add the URIs for the server to
choose from, then set the server for the ``HAClient`` as shown below::

        client = AMPS.HAClient("showchooser")
        chooser = AMPS.DefaultServerChooser()
        chooser.add("tcp://server:9005/amps/nvfix")
        chooser.add("tcp://server-two:9005/amps/nvfix")
        client.set_server_chooser(chooser)
        client.connect_and_logon()

You can add any number of URIs to the ``DefaultServerChooser``.
)docstring";
