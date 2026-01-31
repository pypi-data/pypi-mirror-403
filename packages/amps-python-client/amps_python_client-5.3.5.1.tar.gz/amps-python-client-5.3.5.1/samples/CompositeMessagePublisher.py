#!/usr/bin/python

#########################################################################
# CompositeMessagePublisher 
#
# Simple example to demonstrate publish a composite message to a topic
# in AMPS.
#
# The program flow is simple:
#
# * Connect to AMPS, using the transport configured for composite json-binary
#   messages
# * Logon
# * Construct binary data for the message. For demonstration purposes,
#   the sample uses the same binary data for each message.
# * Publish a set of messages to AMPS. For each message:
#   - Construct a josn part that the subscriber can filter on
#   - Construct a composite message payload
#   - Publish the message.
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
import array
import os

client = AMPS.HAClient("CompositePublisher-%s" % os.getpid())

sc = AMPS.DefaultServerChooser()
sc.add("tcp://127.0.0.1:9027/amps/composite-json-binary")

client.set_server_chooser(sc)
client.connect_and_logon()

theData = array.array('d')
theData.append(1.0)

for d in range(1, 50):
   if (d <= 1):
       theData.append(float(1))
       continue
   theData.append(float(d + theData[d-2]) )

for count in range(1,10):
    # Construct a JSON part
    json='{"binary_type":"double", "size":%d, "number":%d,' \
            % (len(theData), count) + \
           '"message":"Hi, world!"}' 

    # Createa  builder and add the parts
    builder=AMPS.CompositeMessageBuilder()
    builder.append(json)
    builder.append(theData.tostring())

    # Send the message
    client.publish("messages", builder.get_data())

client.publish_flush(2000)
client.close()
