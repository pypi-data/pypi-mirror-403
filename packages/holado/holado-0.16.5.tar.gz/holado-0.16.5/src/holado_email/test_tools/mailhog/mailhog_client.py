
#################################################
# HolAdo (Holistic Automation do)
#
# (C) Copyright 2021-2025 by Eric Klumpp
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# The Software is provided “as is”, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the Software.
#################################################

import logging
from holado_rest.api.rest.rest_client import RestClient
from holado.common.handlers.undefined import undefined_argument, default
from holado_rest.api.rest.rest_manager import RestManager
import email.parser
import email.policy

logger = logging.getLogger(__name__)


class MailHogClient(RestClient):
    
    @classmethod
    def new_client(cls, use_localhost=undefined_argument, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = None
        if 'url' not in kwargs:
            scheme = kwargs.get('scheme', "http")
            host = kwargs.get('host', 'localhost')
            port = kwargs.get('port', 8025)
            
            if port is None:
                url = f"{scheme}://{host}"
            else:
                url = f"{scheme}://{host}:{port}"
            kwargs['url'] = url
        
        manager = RestManager(default_client_class=MailHogClient)
        res = manager.new_client(**kwargs)
        
        return res

    
    def __init__(self, name, url, headers=None):
        super().__init__(name, url, headers)
        self.__policy = email.policy.default
    
    
    def get_number_of_messages(self):
        response = self.get(f"api/v2/messages")
        result = self.response_result(response, status_ok=[200])
        return result['total']
    
    def get_messages(self, start=0, limit=50):
        response = self.get(f"api/v1/messages", path_parameters={'start':start, 'limit':limit})
        result = self.response_result(response, status_ok=[200])
        
        parser = email.parser.Parser(policy=self.__policy)
        
        res = []
        for item in result:
            mail = parser.parsestr(item["Raw"]["Data"])
            mail["From"] = item["Raw"]["From"]
            mail["To"] = item["Raw"]["To"]
            res.append(mail)
        
        return res
    
    
    
    
    
