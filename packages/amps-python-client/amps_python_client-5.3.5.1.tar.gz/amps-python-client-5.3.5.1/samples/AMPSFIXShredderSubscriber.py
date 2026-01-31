#!/usr/bin/python

#########################################################################
# AMPSFIXShredderSubscriber
#
# This sample subscribes to a topic and prints
# fix messages as they are received.

# The program flow is simple:
#
# * Connect to AMPS
# * Subscribe to a topic
# * Print the content of each fix message as it is received.
#
# This sample doesn't include error handling, high availability, or
# connection retry logic.
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
import os

uri_ = "tcp://127.0.0.1:9027/amps/fix"
client = AMPS.Client("ExampleFIXSubscriber-%s" % os.getpid())

try:
    client.connect(uri_)
    client.logon()

    # create the shredder for the message and subscribe to the topic
    shredder = AMPS.FIXShredder()
    messageStream = client.subscribe(topic="messages-sow", timeout=5000)

    # for each message in the subscription, shred it to a map and display
    # the values

    for message in messageStream:
      message_map = shredder.to_map(message.get_data_raw())

      # display the values of the message
      for key in message_map : 
          print (str(key) + " " + message_map[key])

except AMPS.AMPSException as e:
    sys.stderr.write(str(e) + "\n")

client.close()
