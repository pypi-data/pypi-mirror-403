
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

from holado.common.handlers.undefined import to_be_defined
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_core.common.tools.tools import Tools

try:
    import xmltodict  # @UnresolvedImport
    with_xmltodict = True
except:
    with_xmltodict = False

try:
    from lxml import etree  # @UnresolvedImport
    with_lxml = True
except:
    with_lxml = False



class XML2Dict(object):
    """
    Manage conversion of XML <-> dict
    """
    
    
    @classmethod
    def parse(cls, content, force=False, **parse_kwargs):
        """ Parse content to dict, in libraries order and if available:
          - xmltodict,
          - lxml.
        If parse has failed and 'force' is True, a parse is tried with lxml (if available) in recovering mode, in case of XML files well-formed but with "invalid" characters
        """
        res = to_be_defined
        
        try:
            if with_xmltodict:
                kwargs = parse_kwargs['xmltodict'] if 'xmltodict' in parse_kwargs else {}
                res = cls.parse_with_xmltodict(content, **kwargs)
            elif with_lxml:
                kwargs = parse_kwargs['lxml'] if 'lxml' in parse_kwargs else {}
                res = cls.parse_with_lxml(content, **kwargs)
            else:
                raise TechnicalException(f"No XML library is available in (xmltodict, lxml)")
        except:
            # Parse with lxml in recovering mode, in case of XML files with "invalid" characters
            if force and with_lxml:
                kwargs = parse_kwargs['lxml'] if 'lxml' in parse_kwargs else {}
                kwargs['recover'] = True
                res = cls.parse_with_lxml(content, **kwargs)
            else:
                raise
        
        return res

    @classmethod
    def parse_with_xmltodict(cls, content, **parse_kwargs):
        return xmltodict.parse(content, **parse_kwargs)

    @classmethod
    def parse_with_lxml(cls, content, **parser_kwargs):
        parser = etree.XMLParser(**parser_kwargs)
        node = etree.fromstring(content, parser)
        return cls._lxml_node2dict(node)

    
    @classmethod
    def unparse(cls, data, pretty=True, indent=Tools.indent_string(4, ''), **unparse_kwargs):
        """ Unparse dict to string, in libraries order and if available:
          - xmltodict,
          - lxml.
        """
        res = to_be_defined
        
        if with_xmltodict:
            kwargs = unparse_kwargs['xmltodict'] if 'xmltodict' in unparse_kwargs else {}
            res = cls.unparse_with_xmltodict(data, pretty=pretty, indent=indent, **kwargs)
        elif with_lxml:
            kwargs = unparse_kwargs['lxml'] if 'lxml' in unparse_kwargs else {}
            res = cls.unparse_with_lxml(data, pretty=pretty, indent=indent, **kwargs)
        else:
            raise TechnicalException(f"No XML library is available in (xmltodict, lxml)")
        
        return res
    
    @classmethod
    def unparse_with_xmltodict(cls, data, pretty=True, indent=Tools.indent_string(4, ''), **unparse_kwargs):
        unparse_kwargs['pretty'] = pretty
        unparse_kwargs['indent'] = indent
        
        return xmltodict.unparse(data, **unparse_kwargs)

    @classmethod
    def unparse_with_lxml(cls, data, pretty=True, indent=Tools.indent_string(4, ''), **unparse_kwargs):
        """ Unparse dict with lxml.
        Warning: this method currently doesn't work since method _lxml_dict2node is not implemented.
        """
        unparse_kwargs['pretty_print'] = pretty
        
        node = cls._lxml_dict2node(data)
        res = etree.tostring(node, **unparse_kwargs)
        
        # By default 'tostring' return bytes whereas we expect a string
        if isinstance(res, bytes):
            res = res.encode('utf-8')
        # TODO: manage indent: with pretty=True, etree.tostring indent with 4 spaces -> replace each 4 space by indent value
        
        return res
    
    @classmethod
    def _lxml_node2dict(cls, node, attributes=True, add_node_name_as_key=True):
        """
        Convert a lxml.etree node tree into a dict.
        """
        result = {}
        if attributes:
            for item in node.attrib.items():
                key, result[key] = item
        
        for element in node.iterchildren():
            # Remove namespace prefix
            key = etree.QName(element).localname
    
            # Process element as tree element if the inner XML contains non-whitespace content
            if element.text and element.text.strip():
                value = element.text
            else:
                value = cls._lxml_node2dict(element, attributes=attributes, add_node_name_as_key=False)
            if key in result:
                if type(result[key]) is list:
                    result[key].append(value)
                else:
                    result[key] = [result[key], value]
            else:
                result[key] = value
        
        # Surround result by node name if requested 
        if add_node_name_as_key:
            name = etree.QName(node).localname
            res = {name:result}
        else:
            res = result
        
        return res

    @classmethod
    def _lxml_dict2node(cls, data, attributes=True):
        """
        Convert a dict into a lxml.etree node tree.
        """
        raise NotImplementedError()



