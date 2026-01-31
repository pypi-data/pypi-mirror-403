#!/usr/bin/python

#########################################################################
# AMPSSOWConsoleSubscriber
#
# This sample runs a SOW query and receives the results. The sample prints
# each message as it is received.
#
# The program flow is simple:
#
# * Connect to AMPS
# * Execute a SOW command, which runs a query for the current values in
#   the topic.
# * Print the content of each message as it is received
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
import time
import os

uri_ = "tcp://127.0.0.1:9027/amps/json"

try:
    client = AMPS.Client("exampleSOWQuery-%s" % os.getpid())
    client.connect(uri_)
    client.logon()

    # Query the current state of the messages-sow topic
    # for any messages where the messageNumber field is
    # less than 10.

    # The loop exits when all of matching messages are
    # retrieved.
        
    for message in client.sow(topic="messages-sow",
                              filter="/messageNumber < 10"):
       if (message.get_command() == message.Command.GroupBegin):
           print("Receiving messages from the SOW.")
           continue

       if (message.get_command() == message.Command.GroupEnd):
           print("Done receiving messages from the SOW.")
           continue

       print(message.get_data())

except AMPS.AMPSException as e:
    sys.stderr.write(str(e) + "\n")
