#!/usr/bin/python

#########################################################################
# CompositeMessageSubscriber
#
# Simple example to demonstrate subscribing to a composite message topic
# in AMPS.
#
# The program flow is simple:
#
# * Connect to AMPS, specifying composite json-binary messages as the
#   message type for the connection
# * Logon
# * Subscribe to the topic. As each message is received:
#   - Parse the message
#   - Print the contents of the message
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
import sys
import os

client = AMPS.HAClient("CompositeSubscriber-%s" % os.getpid() )

# Add URIs and connect the client.
sc = AMPS.DefaultServerChooser()
sc.add("tcp://127.0.0.1:9027/amps/composite-json-binary")
client.set_server_chooser(sc)

try:
  client.connect_and_logon()

  # Construct the parser to use
  parser = AMPS.CompositeMessageParser()

  # Subscribe and process messages
  for message in client.subscribe("messages", "/0/number % 3 == 0"):
     # parse the message and get the number of parts
     parts = parser.parse(message)  
     if parts != 2:
       print ("unknown message type")
       continue

     # Get the contents of the message 
     json = parser.get_part(0)
     theData = array.array('d')
     theData.fromstring(parser.get_field_at(1))

     # Print the message
     print ("Received message with %d parts." % parts)
     print (json)
     datastring = ""
     for d in theData:
        datastring += "%f " % d
     print (datastring)

except Exception as e:
  sys.stderr.write(str(e) + "\n")

client.close()
