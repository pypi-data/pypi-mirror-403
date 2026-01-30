
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
import re
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_core.common.tools.tools import Tools
from holado.common.context.session_context import SessionContext
from holado_xml.xml.xml_2_dict import XML2Dict


def __get_path_manager():
    return SessionContext.instance().path_manager


class StreamXMLFile(DeleteableObject):
    """
    Manage a stream XML file.
    
    A stream XML file is a file with many root elements that are valid XML.
    It is useful for example to process workflows of data formatted in XML.
    An example in HolAdo is the test report DetailedScenarioReportBuilder with an XML file, 
    which adds in a single file a new scenario XML report after each scenario.
    """

    def __init__(self, path, auto_flush=True, do_open=False, **open_kwargs):
        super().__init__(f"stream XML file '{path}'")

        self.__file = File(path, auto_flush=auto_flush, do_open=do_open, **open_kwargs)
        self.__current_line = None
        self.__current_pos = None

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

    def read_element_as_dict(self, **parse_kwargs):
        # Extract lines of next element
        lines = []
        root_tag = None
        regex_tag_start = re.compile(r"<(?!/)([^ >]+)>")
        regex_tag_end = re.compile(r"</([^ >]+)>")
        level = 0
        is_found = False
        current_element_line = ""
        while not is_found:
            # Read next file line if needed
            if self.__current_line is None:
                line = self.__file.readline()
                if not line:
                    break
                self.__current_line = line
                self.__current_pos = 0
                current_element_line = ""
            
            # Find next tag
            m_start = regex_tag_start.search(self.__current_line, pos=self.__current_pos)
            m_end = regex_tag_end.search(self.__current_line, pos=self.__current_pos)
            #print(f"{root_tag=} ; {level=}  #  {m_start=} ; {m_end=}  #  {self.__current_pos=} in {self.__current_line=}")
            is_start = m_start is not None and (m_end is None or m_start.start() < m_end.start())
            is_end = m_end is not None and (m_start is None or m_end.start() < m_start.start())
            if is_start:
                current_end = m_start.end()
                if root_tag is None:
                    root_tag = m_start.group(1)
                else:
                    level += 1
            elif is_end:
                current_end = m_end.end()
                if level > 0:
                    level -= 1
                elif m_end.group(1) == root_tag:
                    root_tag = None
                    is_found = True
                else:
                    raise TechnicalException(f"Failed to read next element from stream XML file '{self.path}' at position {self.__file.tell()}: got root end element tag '{m_end.group(1)}' that doesn't match previous root start element tag '{root_tag}'")
            else:
                current_end = len(self.__current_line)
            
            # Append in current element line the text until tag
            current_element_line += self.__current_line[self.__current_pos:current_end]
            self.__current_pos = current_end
            
            # Add element line and reset current line
            if self.__current_pos >= len(self.__current_line) or is_found:
                lines.append(current_element_line)
                if self.__current_pos >= len(self.__current_line):
                    self.__current_line = None
        
        # Check error cases
        if root_tag is not None:
            raise TechnicalException(f"Failed to read next element from stream XML file '{self.path}': end of file is reached whereas a root end element tag '{root_tag}' is still expected")
        
        # Manage when end of file is reached without new element
        content = ''.join(lines).strip()
        if len(content) == 0:
            return None
        
        # Parse element as dict
        # print(f"Parsing:\n--------------------------------\n{content}\n--------------------------------")
        return XML2Dict.parse(content, **parse_kwargs)
    
    def read_elements_as_dict_list(self, **parse_kwargs):
        res = []
        while True:
            element = self.read_element_as_dict(**parse_kwargs)
            if element is not None:
                res.append(element)
            else:
                break
        return res
    
    def write_element_dict(self, data, pretty=True, indent=Tools.indent_string(4, ''), **unparse_kwargs):
        content = XML2Dict.unparse(data, pretty=pretty, indent=indent, **unparse_kwargs)
        self.__file.write(content)
        if pretty:
            self.__file.write('\n')
    
    def write_elements_dict_list(self, data_list, pretty=True, indent=Tools.indent_string(4, ''), **unparse_kwargs):
        for data in data_list:
            self.write_element_dict(data, pretty=pretty, indent=indent, **unparse_kwargs)


    @classmethod
    def read_stream_xml_file_content_as_dict_list(cls, path, open_kwargs=None, parse_kwargs=None):
        open_kwargs = open_kwargs if open_kwargs is not None else {}
        parse_kwargs = parse_kwargs if parse_kwargs is not None else {}
        
        file = StreamXMLFile(path, **open_kwargs)
        return file.read_elements_as_dict_list(**parse_kwargs)

    @classmethod
    def write_stream_xml_file_with_dict_list(cls, path, data_list, open_kwargs=None, unparse_kwargs=None):
        open_kwargs = open_kwargs if open_kwargs is not None else {}
        unparse_kwargs = unparse_kwargs if unparse_kwargs is not None else {}
        
        __get_path_manager().makedirs(path)
        
        file = StreamXMLFile(path, **open_kwargs)
        file.write_elements_dict_list(data_list, **unparse_kwargs)
        return file




