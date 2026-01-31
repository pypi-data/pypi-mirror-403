#!/usr/bin/python

#########################################################################
# AMPSSubscribeForReplay

# This sample subscribes to a topic in AMPS that maintains a transaction
# log, and requests replay from the transaction log.
#
# The program flow is simple:
#
# * Connect to AMPS
# * Logon
# * Request replay from the "messages-history" topic from the last
#   message received.
#
# To understand this program, start with the subscribe method of the
# bookmark_subscriber.
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

client = AMPS.HAClient("exampleSubscriberWithReplay-%s" % os.getpid())

message_count = 0

# Handler for received messages.
#
# Prints the received message to the console and 
# discards the message from the bookmark store.

def onMessagePrinter(message):
    global message_count
    message_count += 1
    print (message.get_data_raw())

    # Discard the message. This tells the bookmark store that the
    # message has been processed, and does not need to be requested
    # again.
    client.discard(message)

    # After 10 messages, exit the program
    if (message_count >= 10):
       exit(0)

# onExceptionHandler
#
# Receives any exceptions thrown by the message processor. For demonstration
# purposes, the handler prints the exception and continues.

def onExceptionHandler(e):
    sys.stderr.write(str(e) + "\n")

# Main section of the program.

try:

    # Create a server chooser. For demonstration purposes, only include
    # the URI to the sample AMPS instance.
    
    chooser = AMPS.DefaultServerChooser()
    chooser.add(uri_)
    client.set_server_chooser(chooser) 

    # Create file-backed bookmark store, using "bookmarks" as the file
    # name. 

    bookmarks = AMPS.MMapBookmarkStore("bookmarks")
    client.set_bookmark_store(bookmarks)

    # Set the exception listener.

    client.set_exception_listener(onExceptionHandler)

    # The client is now prepared for use. Connect and logon.

    client.connect_and_logon()


    # Enter the subscription. This statement requests all
    # messages that have not been previously processed on
    # the "messages-history" topic.

    client.bookmark_subscribe(onMessagePrinter, \
                              "messages-history", \
                              client.Bookmarks.MOST_RECENT)

    # All of the work happens on a background thread. Sleep on
    # the main thread.

    # Loop until the background thread receives 10 messages,
    # or until the program begins exiting (and message_count is destroyed).
    while message_count != None and message_count<10:
        time.sleep(.5)
    exit() 

except AMPS.AMPSException as e:
    sys.stderr.write(str(e) + "\n")

client.close()
