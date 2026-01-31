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

#ifndef _MEMORYPUBLISHSTORE_H_
#define _MEMORYPUBLISHSTORE_H_

#include <amps/ampsplusplus.hpp>
#include <amps/BlockPublishStore.hpp>
#include <amps/MemoryStoreBuffer.hpp>

/// \file MemoryPublishStore.hpp
/// \brief Provides AMPS::MemoryPublishStore, a publish store that holds
/// messages in memory.

namespace AMPS
{
///
/// A StoreImpl implementation that uses MemoryStoreBuffer as its buffer to
/// hold published messages in memory. This store does not persist the
/// published messages, so this store cannot be used to guarantee message
/// publication if the application restarts.
  class MemoryPublishStore : public BlockPublishStore
  {
  public:
    ///
    /// Create a MemoryPublishStore with a specified initial capacity in bytes
    /// \param blockPerRealloc_ The number of blocks to grow by when capacity
    /// has been exceeded.
    /// \param errorOnPublishGap_ If true, PublishStoreGapException can be
    /// thrown by the store if the client logs onto a server that appears
    /// to be missing messages no longer held in the store.
    MemoryPublishStore(size_t blockPerRealloc_, bool errorOnPublishGap_ = false)
      : BlockPublishStore(new MemoryStoreBuffer(),
                          (amps_uint32_t)blockPerRealloc_,
                          false, errorOnPublishGap_)
      , _firstGapCheckDone(false)
    {
      // We always want to restart sequencing to avoid possible duplicate in
      // in the case where:
      // Client is up and publishing to A with sync replication to B
      // B goes down having persisted up to x in txn log where x < y
      // Client goes down after publishing y
      // Client comes back up and connects to A
      // Logon ack from A is for x because B is still down
      // If client started from x+1, all messages up to y would be duplicate
      // We cannot error on publish gap in this case, since a new
      //   MemoryPublishStore has no history.
      getLastPersisted();
    }

    ///
    /// Create a MemoryPublishStore with a specified initial capacity in bytes
    /// \param blockPerRealloc_ The number of blocks to grow by when capacity
    /// has been exceeded.
    /// \param blocksSize_ The size of each block, default is 2KB. Should be a
    ///        64-byte aligned value that is > 64 + expected message size.
    ///        Larger messages can span blocks but 1 block per message is most
    ///        efficient.
    /// \param errorOnPublishGap_ If true, PublishStoreGapException can be
    /// thrown by the store if the client logs onto a server that appears
    /// to be missing messages no longer held in the store.
    MemoryPublishStore(size_t blocksPerRealloc_, amps_uint32_t blockSize_,
                       bool errorOnPublishGap_ = false)
      : BlockPublishStore(new MemoryStoreBuffer(),
                          (amps_uint32_t)blocksPerRealloc_,
                          false, errorOnPublishGap_, blockSize_)
      , _firstGapCheckDone(false)
    {
      // We always want to restart sequencing to avoid possible duplicate in
      // in the case where:
      // Client is up and publishing to A with sync replication to B
      // B goes down having persisted up to x in txn log where x < y
      // Client goes down after publishing y
      // Client comes back up and connects to A
      // Logon ack from A is for x because B is still down
      // If client started from x+1, all messages up to y would be duplicate
      // We cannot error on publish gap in this case, since a new
      //   MemoryPublishStore has no history.
      getLastPersisted();
    }

    virtual void discardUpTo(amps_uint64_t index_)
    {
      BlockPublishStore::discardUpTo(index_);
      if (!_firstGapCheckDone)
      {
        _firstGapCheckDone = true;
      }
    }

    virtual bool getErrorOnPublishGap() const
    {
      return _firstGapCheckDone ? StoreImpl::getErrorOnPublishGap() : false;
    }

  private:
    bool _firstGapCheckDone;

  };//end MemoryPublishStore

}//end namespace AMPS

#endif //_MEMORYPUBLISHSTORE_H_

