
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
from holado_system.system.filesystem.file import File
import json
from holado.common.context.session_context import SessionContext


def __get_path_manager():
    return SessionContext.instance().path_manager


class JSONFile(DeleteableObject):
    """
    Manage a JSON file
    """

    def __init__(self, path, auto_flush=True, do_open=False, **open_kwargs):
        super().__init__(f"JSON file '{path}'")

        self.__file = File(path, auto_flush=auto_flush, do_open=do_open, **open_kwargs)

    def __enter__(self):
        self.__file.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__file.__exit__(exc_type, exc_val, exc_tb)
    
    @property
    def path(self):
        return self.__file.path

    @property
    def internal_file(self):
        return self.__file
    
    @property
    def is_open(self):
        return self.__file.is_open

    def open(self, **kwargs):
        self.__file.open(**kwargs)

    def close(self):
        self.__file.close()

    def read_as_json_object(self, **loads_kwargs):
        with self.__file as fin:
            content = fin.read()
        return json.loads(content, **loads_kwargs)

    def write_json_object(self, data, indent=4, **dumps_kwargs):
        dumps_kwargs['indent'] = indent
        
        content = json.dumps(data, **dumps_kwargs)
        with self.__file as fout:
            fout.write(content)



    @classmethod
    def read_json_file_content_as_json_object(cls, path, open_kwargs=None, loads_kwargs=None):
        open_kwargs = open_kwargs if open_kwargs is not None else {}
        loads_kwargs = loads_kwargs if loads_kwargs is not None else {}
        
        file = JSONFile(path, **open_kwargs)
        return file.read_as_json_object(**loads_kwargs)

    @classmethod
    def write_json_file_with_json_object(cls, path, data, open_kwargs=None, dumps_kwargs=None):
        open_kwargs = open_kwargs if open_kwargs is not None else {}
        dumps_kwargs = dumps_kwargs if dumps_kwargs is not None else {}
        
        __get_path_manager().makedirs(path)
        
        file = JSONFile(path, **open_kwargs)
        file.write_json_object(data, **dumps_kwargs)
        return file




