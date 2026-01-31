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

static const char* fixshredder_class_doc = R"docstring(FIXShredder(separator=chr(1))
Convenience class for easily processing FIX strings. This class provides
functionality to parse FIX messages and convert them into Python dictionaries
for easy manipulation and analysis.

**Constructor Arguments:**


:param separator: The delimiter to expect between FIX fields. Defaults to chr(1) if no
                  delimiter is provided.
)docstring";

static const char* to_map_doc = R"docstring(to_map(message)
Parse the provided FIX message and return a map that contains the
fields in the message.


:param message: The FIX message to parse.
)docstring";
