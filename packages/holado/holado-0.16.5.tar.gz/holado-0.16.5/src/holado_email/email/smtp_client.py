
#################################################
# HolAdo (Holistic Automation do)
#
# (C) Copyright 2023 by Eric Klumpp
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# The Software is provided “as is”, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the Software.
#################################################

import logging
from holado_core.common.tools.tools import Tools
from holado.common.handlers.object import DeleteableObject
import smtplib

logger = logging.getLogger(__name__)


class SMTPClient(DeleteableObject):

    def __init__(self, name, smtp_kwargs):
        super().__init__(name)
        
        self.__client = smtplib.SMTP(**smtp_kwargs)
    
    def _delete_object(self):
        if Tools.do_log(logger, logging.DEBUG):
            logger.debug(f"[{self.name}] Deleting SMTP client...")
        self.close()
        if Tools.do_log(logger, logging.DEBUG):
            logger.debug(f"[{self.name}] Finished to delete SMTP client")
    
    @property    
    def internal_client(self) -> smtplib.SMTP:
        return self.__client
    
    @property    
    def is_connected(self):
        return self.__client.sock is not None
    
    def close(self):
        if self.is_connected:
            self.__client.quit()




