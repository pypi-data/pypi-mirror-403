#!/usr/bin/python

#########################################################################
# AMPSSOWandSubscribeWithOOF
#
# This sample runs a SOW query and enters an atomic subscription
# at the same time. The sample receives the results from the query, then
# receives new messages published to the topic. The sample requests OOF
# notifications when a message which previously matched the subscription
# no longer matches the subscription.
#
# The sample prints each message as it is received, and also indicates
# where the SOW query begins and ends. For demonstration purposes, the
# sample also shows the command value of each message. For messages
# received as part of the SOW query, the command is "sow". For messages
# received from the subscription, the command is "publish". For messages
# that no longer match, the command is "oof".

# The program flow is:
#
# * Connect to AMPS
# * Execute a SOW and Subscribe command, which runs a query and
#   subscribes to the topic in a single atomic operation
# * Print the content of each message as it is received
#   - For SOW results or published messages, print the message data
#   - For group_begin and group_end messages, print an informative message
#   - For OOF messages, print the reason for the OOF and the message which
#     no longer matches
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


# main program
#
# Create a client, connect to the server, query the SOW,
# and then wait for the callback function to process messages.
client = AMPS.Client("exampleSOWandSubscribeQueryWithOOF-%s"% os.getpid())

try:
    client.connect(uri_)
    client.logon()
   
    # Query for messages in the messages-sow topic.

    # When messages are received, AMPS will invoke the
    # handleMessage function, providing the message and
    # as a parameter.

    # Because oof_enabled is true, AMPS will provide
    # an OOF message when a message that had previously matched the filter
    # no longer matches the filter.
 
    for message in client.sow_and_subscribe(topic="messages-sow",
                filter="/messageNumber % 10  = 0 " +
                "AND (/OptionalField IS NULL OR /OptionalField <> 'ignore_me')",
                oof_enabled="true"):

      if (message.get_command() == message.Command.OOF):
          print("Received an OOF.")
          print("   " + message.get_reason() + " : %s" %  message.get_data_raw())
          continue

      if (message.get_command() == message.Command.GroupBegin):
          print("Receiving messages from the SOW.")
          continue

      if (message.get_command() == message.Command.GroupEnd):
          print("Done receiving messages from the SOW.")

      print(message.get_data_raw())


except AMPS.AMPSException as e:
    sys.stderr.write(str(e) + "\n")

client.close()
