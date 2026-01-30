
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
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_system.system.command.command import Command, CommandStates
from holado.common.context.session_context import SessionContext
from holado_system.system.filesystem.file import File
import cryptography.x509
from cryptography.hazmat.primitives import serialization
from holado.common.handlers.undefined import default_value

logger = logging.getLogger(__name__)


class KeyManager(object):
    """
    Helper for key management.
    """
    
    @classmethod
    def __get_path_manager(cls):
        return SessionContext.instance().path_manager
    
    @classmethod
    def generate_new_self_signed_key_files(cls, public_key_path, private_key_path, openssl_args):
        cls.__get_path_manager().makedirs(public_key_path)
        cls.__get_path_manager().makedirs(private_key_path)
        
        cmd = f"openssl req -out '{public_key_path}' -keyout '{private_key_path}' {openssl_args}"
        command = Command(cmd, do_log_output=True, do_raise_on_stderr=False, executable="/bin/bash")
        command.start()
        command.join()
        
        if command.state is not CommandStates.Success:
            raise TechnicalException(f"Error while executing openssl command [{cmd}] : [{command.stderr}]")
    
    @classmethod
    def generate_new_self_signed_key_files_for_localhost(cls, public_key_path, private_key_path, algorithm='rsa:2048'):
        KeyManager.generate_new_self_signed_key_files(
            public_key_path, private_key_path, 
            f"-x509 -newkey {algorithm} -noenc -sha256 -subj '/CN=localhost' -extensions EXT \
              -config <( printf \"[dn]\nCN=localhost\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:localhost\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth\")"
            )
    
    @classmethod
    def load_pem_public_key(cls, data=None, file_path=None, is_x509=False, **kwargs):
        if file_path is not None:
            data = File.read_file_content(file_path, mode='rb')
        
        if is_x509:
            cert = cryptography.x509.load_pem_x509_certificate(data, **kwargs)
            res = cert.public_key()
        else:
            res = serialization.load_pem_public_key(data, **kwargs)
        
        return res
    
    @classmethod
    def load_pem_private_key(cls, data=None, file_path=None, **kwargs):
        if file_path is not None:
            data = File.read_file_content(file_path, mode='rb')
        
        password = kwargs.get('password', None)
        res = serialization.load_pem_private_key(data, password, **kwargs)
        
        return res
    
    @classmethod
    def convert_public_key_to_hex(cls, public_key, encoding=default_value, public_format=default_value):
        """Convert public in a portable hexadecimal format.
        Note: default encoding is DER, and default public_format is SubjectPublicKeyInfo. If they are not compatible with public_key, appropriate values must be specified.
        """
        if encoding is default_value:
            encoding = serialization.Encoding.DER
        if public_format is default_value:
            public_format = serialization.PublicFormat.SubjectPublicKeyInfo
        return public_key.public_bytes(encoding=encoding, format=public_format).hex()
    
    
    

