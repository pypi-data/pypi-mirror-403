
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
import os
from holado_system.system.command.command import Command, CommandStates
from holado.common.context.session_context import SessionContext
import json
from holado_system.system.filesystem.file import File

logger = logging.getLogger(__name__)


class TcpbinManager(object):
    """
    Helper for tcpbin.com usage.
    """
    
    @classmethod
    def __get_path_manager(cls):
        return SessionContext.instance().path_manager
    
    @classmethod
    def get_client_certificates(cls):
        base_path = cls.__get_path_manager().get_local_resources_path('certificates')
        certfile_path = os.path.join(base_path, 'tcpbin.crt')
        keyfile_path = os.path.join(base_path, 'tcpbin.key')
        
        cls.ensure_tcpbin_certificates_are_valid(certfile_path, keyfile_path)
        
        return (certfile_path, keyfile_path)
    
    @classmethod
    def get_CAs(cls):
        base_path = cls.__get_path_manager().get_local_resources_path('certificates')
        ca_certfile_path = os.path.join(base_path, 'rootCACert.pem')
        ca_keyfile_path = os.path.join(base_path, 'rootCAKey.pem')
        
        cls.extract_tcpbin_ca_files(ca_certfile_path, ca_keyfile_path)
        
        return (ca_certfile_path, ca_keyfile_path)
    
    @classmethod
    def ensure_tcpbin_certificates_are_valid(cls, public_key_path, private_key_path, duration_seconds=600):
        cls.__get_path_manager().makedirs(public_key_path)
        cls.__get_path_manager().makedirs(private_key_path)
        
        # Verify if certificate has expired
        do_generate_certificates = True
        if os.path.exists(public_key_path):
            cmd = f"openssl x509 -checkend {duration_seconds} -noout -in '{public_key_path}'"
            command = Command(cmd, do_log_output=True, do_raise_on_stderr=False, executable="/bin/bash")
            command.start()
            command.join()
            if command.state is CommandStates.Success:
                do_generate_certificates = False
            elif command.return_code == 1:
                do_generate_certificates = True
            else:
                raise TechnicalException(f"Error while executing openssl command [{cmd}]: error code={command.return_code} ; stdout: [{command.stdout}] ; stderr: [{command.stderr}]")
        
        # Generate new certificates if needed
        if do_generate_certificates:
            cmd = f"curl -s https://tcpbin.com/api/client-cert"
            command = Command(cmd, do_log_output=True, do_raise_on_stderr=False, executable="/bin/bash")
            command.start()
            command.join()
            if command.state is not CommandStates.Success:
                raise TechnicalException(f"Error while executing command [{cmd}] : [{command.stderr}]")
            
            data = json.loads(command.stdout)
            File.write_file_with_content(public_key_path, data['cert'])
            File.write_file_with_content(private_key_path, data['key'])
    
    @classmethod
    def extract_tcpbin_ca_files(cls, ca_certfile_path, ca_keyfile_path):
        if not cls.__get_path_manager().check_file_exists(ca_certfile_path, raise_exception=False):
            cmd = f"curl -s https://tcpbin.com/rootCACert.pem"
            command = Command(cmd, do_log_output=True, do_raise_on_stderr=True, executable="/bin/bash")
            command.start()
            command.join()
            File.write_file_with_content(ca_certfile_path, command.stdout)
        
        if not cls.__get_path_manager().check_file_exists(ca_keyfile_path, raise_exception=False):
            cmd = f"curl -s https://tcpbin.com/rootCAKey.pem"
            command = Command(cmd, do_log_output=True, do_raise_on_stderr=True, executable="/bin/bash")
            command.start()
            command.join()
            File.write_file_with_content(ca_keyfile_path, command.stdout)
        




