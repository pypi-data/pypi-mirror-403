
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

from holado.common.handlers.object import DeleteableObject
import os
from typing import AnyStr, List
from holado_python.standard_library.typing import Typing
from holado_core.common.exceptions.technical_exception import TechnicalException
import copy


class File(DeleteableObject):
    """
    Manage a file
    """

    def __init__(self, path, auto_flush=True, do_open=False, **open_kwargs):
        """ Manage a file
        @param path: file path
        @param do_open: if file must be open during this file initialization
        @param open_kwargs: arguments to open method
        """
        super().__init__(f"file '{path}'")

        self.__path = path
        self.__auto_flush = auto_flush
        self.__file = None
        self.__open_kwargs = open_kwargs
        if do_open:
            self.open()

    def _delete_object(self):
        self.close()
    
    def __enter__(self):
        if not self.is_open:
            self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @property
    def path(self):
        return self.__path

    @property
    def internal_file(self):
        return self.__file
    
    @property
    def is_open(self):
        return self.__file is not None

    def open(self, **kwargs):
        if self.is_open:
            raise TechnicalException(f"File '{self.path}' is already opened")
        open_kwargs = copy.copy(self.__open_kwargs)
        if kwargs:
            open_kwargs.update(kwargs)
        
        self.__file = open(self.__path, **open_kwargs)

    def close(self):
        if self.__file:
            self.__file.close()
            self.__file = None

    def write(self, data):
        res = self.internal_file.write(data)
        if self.__auto_flush:
            self.internal_file.flush()
        return res

    def writelines(self, lines, add_line_sep=True):
        for line in lines:
            self.internal_file.write(line)
            if add_line_sep and not line.endswith(os.linesep):
                self.internal_file.write(os.linesep)
        if self.__auto_flush:
            self.internal_file.flush()

    def read(self, n: int = -1) -> AnyStr:
        return self.internal_file.read(n)

    def readline(self, limit: int = -1) -> AnyStr:
        return self.internal_file.readline(limit)

    def readlines(self, hint: int = -1, strip_newline=False) -> List[AnyStr]:
        res = self.internal_file.readlines(hint)
        if strip_newline:
            res = [l.strip('\n') for l in res]
        return res



    @classmethod
    def read_file_content(cls, path, **open_kwargs):
        with File(path, **open_kwargs) as file:
            res = file.read()
        return res

    @classmethod
    def read_file_content_in_base64(cls, path, **open_kwargs):
        import base64
        
        # Force to read file in binary mode
        open_kwargs['mode'] = 'rb'
        
        with File(path, **open_kwargs) as fin:
            content = fin.read()
        res = base64.b64encode(content)
        
        return res

    @classmethod
    def read_file_content_in_hexadecimal(cls, path, **open_kwargs):
        # Force to read file in binary mode
        open_kwargs['mode'] = 'rb'
        
        with File(path, **open_kwargs) as fin:
            content = fin.read()
        res = content.hex()
        
        return res

    @classmethod
    def write_file_with_content(cls, path, content):
        if isinstance(content, str):
            with File(path, mode='wt') as fout:
                fout.write(content)
        elif isinstance(content, bytes):
            with File(path, mode='wb') as fout:
                fout.write(content)
        else:
            raise TechnicalException(f"Unexpected content type {Typing.get_object_class_fullname(content)} (allowed types: str, bytes)")




