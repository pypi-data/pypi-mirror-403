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

from AMPS import DefaultAuthenticator, DisconnectedException
import random

class RandomServerChooser:

  def __init__(self, seed = None):
     self.servers = []
     self.current_server = None
     self.random = random.Random(seed)
     self.authenticator = DefaultAuthenticator()

  def add(self, server):
     self.servers.append(server)

  def get_current_uri(self):
     if len(self.servers) == 0:
        return None

     if self.current_server == None:
        self.set_current_server()
 
     return self.current_server

  def next(self):
     self.set_current_server()  

  def get_current_authenticator(self):
    return self.authenticator

  def report_failure(self, exception, info):
    if ( (type(exception) is DisconnectedException) == False):
       self.next() 

  def report_success(self, info):
      pass

  def set_current_server(self):
     if len(self.servers) == 0:
        return None

     self.current_server = self.random.choice(self.servers) 
