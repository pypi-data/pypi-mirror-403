
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
from holado.common.context.session_context import SessionContext
from holado.common.handlers.undefined import default

logger = logging.getLogger(__name__)


class CryptoManager(object):
    """
    Helper for cryptography management.
    """
    
    @classmethod
    def __get_path_manager(cls):
        return SessionContext.instance().path_manager
    
    @classmethod
    def encrypt_data_with_key(cls, data, key, data_padding_char=b'\x00', padding=default):
        """ Encrypt data with given asymmetric public key.
        Note: default padding is OAEP with sha256. If it doesn't match the key, padding parameter must be specified.
        """
        return cls._crypt_data_with_key(data, key.key_size, key.encrypt, data_padding_char, padding)
    
    @classmethod
    def decrypt_data_with_key(cls, data, key, data_padding_char=b'\x00', padding=default):
        """ Decrypt data with given asymmetric private key.
        Note: default padding is OAEP with sha256. If it doesn't match the key, padding parameter must be specified.
        """
        return cls._crypt_data_with_key(data, key.key_size, key.decrypt, data_padding_char, padding)

    @classmethod
    def _crypt_data_with_key(cls, data, key_size, key_method, data_padding_char=b'\x00', padding=default):
        """ Decrypt data with given asymmetric private key.
        Note: default padding is OAEP with sha256. If it doesn't match the key, padding parameter must be specified.
        """
        if padding is default:
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes
            padding = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        
        # Decrypt data
        res = b''
        key_nb_bytes = key_size // 8
        for i in range(0, len(data), key_nb_bytes):
            cur_data = data[i*key_nb_bytes:(i+1)*key_nb_bytes]
            cur_len = len(cur_data)
            if cur_len < key_nb_bytes:
                cur_data += data_padding_char * (key_nb_bytes - cur_len)
            cur_res = key_method(cur_data, padding=padding)
            if cur_len < key_nb_bytes:
                cur_res = cur_res[:cur_len]
            res += cur_res
        
        return res

    @classmethod
    def cipher_data(cls, data, cipher=None, **cipher_kwargs):
        """ Cipher data with given symmetric cipher.
        """
        if cipher is None:
            cipher = cls.new_cipher(**cipher_kwargs)
        encryptor = cipher.encryptor()
        res = encryptor.update(data) + encryptor.finalize()
        return res

    @classmethod
    def decipher_data(cls, data, cipher=None, **cipher_kwargs):
        """ Decipher data with given symmetric cipher.
        """
        if cipher is None:
            cipher = cls.new_cipher(**cipher_kwargs)
        decryptor = cipher.decryptor()
        res = decryptor.update(data) + decryptor.finalize()
        return res
        

    @classmethod
    def new_cipher(cls, algorithm=None, mode=default, algorithm_name=None, algorithm_key=None, **kwargs):
        """ Create cipher with given symmetric algorithm.
        Note: default mode is CBC with initial vector composed of as many zeros as needed by algorithm.
        """
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        
        if algorithm is None and algorithm_name is not None:
            if hasattr(algorithms, algorithm_name):
                algorithm = getattr(algorithms, algorithm_name)(algorithm_key)
            else:
                raise TechnicalException(f"Algorithm '{algorithm_name}' is not managed")
        if mode is default:
            mode = modes.CBC(b'\x00' * (algorithm.block_size // 8))
        
        return Cipher(algorithm, mode, **kwargs)
        
        
