#!/usr/bin/python

#########################################################################
# AMPSPublishForReplay

# This sample publishes messages to a topic in AMPS that
# maintains a transaction log.

# The program flow is simple:
#
# * Connect to AMPS
# * Logon
# * Publish 1000 messages at a time to the "messages-history" topic. Each
#   message published has a unique orderId. The program waits one second
#   between sets of 1000 messages.
#
# The "messages-history" topic is configured in config/sample.xml
# to maintain a transaction log.
#
# This sample doesn't include error handling, high availability, or
# connection retry logic.
#
#########################################################################
##
## Copyright (c) 2010-2025 60East Technologies Inc., All Rights Reserved.
##
## This computer software is owned by 60East Technologies Inc. and is
## protected by U.S. copyright laws and other laws and by international
## treaties.  This computer software is furnished by 60East Technologies
## Inc. pursuant to a written license agreement and may be used, copied,
## transmitted, and stored only in accordance with the terms of such
## license agreement and with the inclusion of the above copyright notice.
## This computer software or any other copies thereof may not be provided
## or otherwise made available to any other person.
##
## U.S. Government Restricted Rights.  This computer software: (a) was
## developed at private expense and is in all respects the proprietary
## information of 60East Technologies Inc.; (b) was not developed with
## government funds; (c) is a trade secret of 60East Technologies Inc.
## for all purposes of the Freedom of Information Act; and (d) is a
## commercial item and thus, pursuant to Section 12.212 of the Federal
## Acquisition Regulations (FAR) and DFAR Supplement Section 227.7202,
## Government's use, duplication or disclosure of the computer software
## is subject to the restrictions set forth by 60East Technologies Inc..
##
########################################################################

import AMPS
import sys
import time
import os


uri_ = "tcp://127.0.0.1:9027/amps/json"

try:
    client = AMPS.Client("replayPublisher-%s"% os.getpid())
    client.connect(uri_)
    client.logon()

    orderId = 1

    loop_count = 0

    while loop_count < 100:
      for i in range(1,10):
        message = '{"orderId"=%d' % orderId + \
                  ' "symbol"="IBM", "size"=1000, "price"=190.01}'

        client.publish("messages-history", message)
        orderId += 1
 
      time.sleep(1)
      loop_count += 1
      print("Published %s messages to messages-history" % (loop_count * 10 ))

except AMPS.AMPSException as e:
    sys.stderr.write(str(e) + "\n")

client.publish_flush(2000)
client.close()
