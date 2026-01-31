#!/usr/bin/python

#########################################################################
# AMPSUpdateForOOF

# This sample publishes messages to a SOW topic, then updates
# the message in a way that will cause AMPS to deliver OOF
# messages to the sample program that requests OOF notifications.

# The program flow is:
#
# * Connect to AMPS
# * Logon
# * Publish a message with expiration set
# * Publish a message to be deleted later
# * Publish a set of messages
# * Publish updates to some of those messages
# * Delete the message published to be deleted

# During this process, the sample program that receives OOF notifications
# will receive OOF messages for updates, for an expiration, and for a
# deleted message.

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

# deletedMessageAck
#
# This function receives the acknowledgement message that results from
# deleting a message from the SOW. For sample purposes, this program
# ignores the contents of the message.

def deletedMessageAck(message):
    pass


# main program
#
# Connect to AMPS, send a message with an expiration, and send a message that
# will be deleted. After that, send a set of messages and update the messages.
client = AMPS.Client("exampleSOWUpdater-%s" % os.getpid())

try:
    client.connect(uri_)
    client.logon()

    # Publish a message with the expiration set.
    m = client.allocate_message()
    m.set_expiration("1")
    m.set_command("publish")
    m.set_topic("messages-sow")
    m.set_data('{"messageNumber" :50000, "message" : "Here and then gone..."}')

    client.send(m)

    # Publish a message to be deleted later on.

    client.publish("messages-sow", \
                   '{"messageNumber":500,' + \
                      '"message":"I\'ve got a bad feeling about this..."}')

    # Publish two sets of messages, the first one to match
    # the subscriber filter, the next one to make messages no longer
    # match the subscriber filter.

    # The first set of messages is designed so that, if this is run
    # after the previous SOW example, the sample with OOF tracking
    # recieves an updated message.
 
    for number in range(0,10000,1250):
        client.publish("messages-sow",
                       '{"message":"Hello, you crazy world!"' +
                         ',"messageNumber":%i' % number +
                       ',"OptionalField":"true"}')


    # The second set of messages will cause OOF messages for the sample
    # that uses OOF tracking.

    for number in range(0,10000,1250): 
        client.publish("messages-sow",
                       '{"message":"Updated, world!"' +
                       ',"messageNumber":%i' % number+
                       ',"OptionalField":"ignore_me"}') 


    # Delete the message published earlier

    client.sow_delete(deletedMessageAck, "messages-sow", \
                         "/messageNumber = 500", 0)
    
except AMPS.AMPSException as e:
    sys.stderr.write(str(e) + "\n")

client.close()
