
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
import ssl
from holado_core.common.tools.tools import Tools
from holado_json.ipc.json import set_object_attributes_with_json_dict
from holado_core.common.exceptions.technical_exception import TechnicalException
import os
import copy
from ssl import Purpose
from holado_system.system.command.command import Command, CommandStates
from holado.common.context.session_context import SessionContext
import json

logger = logging.getLogger(__name__)


class SslManager(object):
    """
    Helper for ssl module.
    
    It is implemented internally with standard library ssl.
    """
    
    @classmethod
    def __get_path_manager(cls):
        return SessionContext.instance().path_manager
    
    @classmethod
    def new_ssl_context(cls, server_side=False, ssl_kwargs=None, context_kwargs=None):
        res = None
        
        if ssl_kwargs is None:
            ssl_kwargs = {}
        kwargs = copy.copy(ssl_kwargs)
        
        try:
            activate_ssl = kwargs.pop('activate', True)
            if activate_ssl:
                if Tools.has_sub_kwargs(kwargs, 'create_default_context.'):
                    create_default_context_kwargs = Tools.pop_sub_kwargs(kwargs, 'create_default_context.')
                else:
                    create_default_context_kwargs = {}
                
                purpose = Purpose.CLIENT_AUTH if server_side else Purpose.SERVER_AUTH
                res = ssl.create_default_context(purpose=purpose, **create_default_context_kwargs)
                
                # res.set_default_verify_paths()
                
                if context_kwargs:
                    c_kwargs = copy.copy(context_kwargs)
                    
                    ciphers = c_kwargs.pop('ciphers', None)
                    if ciphers is not None:
                        if ciphers == 'OPENSSL_CIPHERS':
                            ciphers = SslManager.get_openssl_ciphers()
                            logger.debug(f"Using openssl ciphers: {ciphers}")
                        res.set_ciphers(ciphers)
                    if Tools.has_sub_kwargs(c_kwargs, 'load_cert_chain.'):
                        load_cert_chain_kwargs = Tools.pop_sub_kwargs(c_kwargs, 'load_cert_chain.')
                        res.load_cert_chain(**load_cert_chain_kwargs)
                    if Tools.has_sub_kwargs(c_kwargs, 'load_verify_locations.'):
                        load_verify_locations_kwargs = Tools.pop_sub_kwargs(c_kwargs, 'load_verify_locations.')
                        res.load_verify_locations(**load_verify_locations_kwargs)
                    
                    # Set context attributes with remaining c_kwargs
                    if len(c_kwargs) > 0:
                        set_object_attributes_with_json_dict(res, c_kwargs)
                
                logger.debug(f"Default verify paths: {ssl.get_default_verify_paths()})")
                dvp = ssl.get_default_verify_paths()
                if res.verify_mode != ssl.CERT_NONE and dvp.cafile is None and 'create_default_context.cafile' not in ssl_kwargs and 'load_verify_locations.cafile' not in context_kwargs:
                    msg_list = [f"No CA file is defined, it is not possible to verify certificates.",
                                f"Most common solutions:",
                                f"  - Configure to not verify certificates, by adding/setting in table: | 'ssl.context.verify_mode' | ssl.CERT_NONE |",
                                f"  - Be sure OpenSSL default CA file exists on system (configured path: '{dvp.openssl_cafile}'). Example of command (on Ubuntu): sudo ln -s /etc/ssl/certs/ca-certificates.crt {dvp.openssl_cafile}",
                                f"  - Configure a CA file at context creation, by adding/setting in table: | 'ssl.create_default_context.cafile' | <path to CA file> |",
                                f"  - Configure a CA file after context creation, by adding/setting in table: | 'ssl.context.load_verify_locations.cafile' | <path to CA file> |",
                                f"Note: step 'Given CACERTS_PATH = CA certs file path (from certifi package)' can be used to get the path to CA file coming with 'certifi' package that is supposed to be installed when using ssl module",
                                ]
                    raise TechnicalException("\n".join(msg_list))
                try:
                    logger.debug(f"Loaded CA certificates: {res.get_ca_certs()})")
                except NotImplementedError:
                    # Depending on environment, get_ca_certs can be not implemented (ex: python 3.10 and pip v25.1.1)
                    pass
                logger.debug(f"Loaded ciphers: {res.get_ciphers()})")
                
        except Exception as exc:
            msg = f"Failed to create SSL context with parameters ({ssl_kwargs}, {context_kwargs}): {exc}"
            logger.error(msg)
            raise TechnicalException(msg) from exc
        
        # Verify all kwargs were applied
        if len(kwargs) > 0:
            raise TechnicalException(f"Unmanaged ssl parameters: {kwargs}")
        
        return res
    
    @classmethod
    def get_openssl_ciphers(cls):
        import subprocess
        output = subprocess.run(["openssl", "ciphers"], capture_output=True).stdout
        output_str = output.decode("utf-8")
        return output_str.strip().split("\n")[0]
    
    @classmethod
    def get_default_certificates(cls):
        dvp = ssl.get_default_verify_paths()
        if not os.path.exists(dvp.cafile):
            raise TechnicalException(f"openssl CA file '{dvp.cafile}' doesn't exist. Example of resolution command (on Ubuntu): sudo ln -s /etc/ssl/certs/ca-certificates.crt {dvp.cafile}")
        return (dvp.cafile, dvp.capath)
    
    @classmethod
    def get_certifi_ca_certs_file_path(cls):
        import certifi
        return certifi.where()
    
    

