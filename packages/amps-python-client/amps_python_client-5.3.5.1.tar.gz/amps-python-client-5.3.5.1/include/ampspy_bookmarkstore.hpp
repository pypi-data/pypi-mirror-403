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
#ifndef _AMPSPY_BOOKMARKSTORE_HPP_
#define _AMPSPY_BOOKMARKSTORE_HPP_

#include <amps/Message.hpp>
#include <amps/util.hpp>

namespace ampspy
{
  namespace bookmarkstore
  {
    class wrapper : public AMPS::BookmarkStoreImpl
    {
    public:
      wrapper(PyObject* object_);
      virtual ~wrapper(void);
      size_t log(AMPS::Message& message_);
      void discard(const AMPS::Message::Field& subId_,
                   size_t bookmarkSeqNo_);
      void discard(const AMPS::Message& message_);
      AMPS::Message::Field getMostRecent(const AMPS::Message::Field& subId_);
      bool isDiscarded(AMPS::Message& message_);
      void purge(void);
      void purge(const AMPS::Message::Field& subId_);
      size_t getOldestBookmarkSeq(const AMPS::Message::Field& subId_);
      void persisted(const AMPS::Message::Field& subId_,
                     const AMPS::Message::Field& bookmark_);

      AMPS::Message::Field persisted(const AMPS::Message::Field& subId_, size_t bookmark_);

      void setServerVersion(const AMPS::VersionInfo& version_);
      void setServerVersion(size_t version_);

    protected:
      PyObject* _pImpl;
    };
  }
}

#endif // _AMPSPY_BOOKMARKSTORE_HPP_
