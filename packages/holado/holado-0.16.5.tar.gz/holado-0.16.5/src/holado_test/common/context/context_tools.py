
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

from holado.common.context.session_context import SessionContext
import logging
import re
from holado_core.common.exceptions.functional_exception import FunctionalException
from holado_scripting.common.tools.variable_manager import VariableManager
from holado_core.common.tools.tools import Tools
from holado_value.common.tables.value_table import ValueTable
from holado_value.common.tables.value_table_with_header import ValueTableWithHeader
from holado_core.common.tables.table_with_header import TableWithHeader
from holado_value.common.tables.converters.value_table_converter import ValueTableConverter
from holado_core.common.tables.table import Table
from holado_core.common.tables.table_row import TableRow
from holado_core.common.tables.table_cell import TableCell
from holado_value.common.tables.value_table_row import ValueTableRow
from holado_value.common.tables.value_table_cell import ValueTableCell
from holado_value.common.tools.value_types import ValueTypes
from holado_value.common.tables.comparators.table_2_value_table_with_header_comparator import Table2ValueTable_WithHeaderComparator
from holado_value.common.tables.comparators.table_2_value_table_comparator import Table2ValueTable_Comparator
from holado_core.common.tables.table_manager import TableManager
from holado_scripting.common.tools.evaluate_parameters import EvaluateParameters
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado.holado_config import Config
from holado_python.standard_library.typing import Typing
from holado_value.common.tables.value_table_manager import ValueTableManager
from holado_python.common.tools.datetime import DateTime, FORMAT_DATETIME_ISO,\
    FORMAT_TIME_ISO
from holado.common.handlers.undefined import default_value

logger = logging.getLogger(__name__)


#TODO: make it a service in SessionContext
class ContextTools(object):
    
    @classmethod
    def format_context_period(cls, context, format_precision_nsec=None, dt_ref=None, use_compact_format=default_value):
        dt_start, dt_end = context.start_datetime, context.end_datetime
        
        # Prepare format of start datetime
        if format_precision_nsec is not None:
            dt_start = DateTime.truncate_datetime(dt_start, precision_nanoseconds=format_precision_nsec)
        dt_format_start = cls.get_datetime_format_compared_to_reference(dt_start, dt_ref, use_compact_format=use_compact_format)
        
        # Prepare format of end datetime
        if dt_end is not None:
            if format_precision_nsec is not None:
                dt_end = DateTime.truncate_datetime(dt_end, precision_nanoseconds=format_precision_nsec)
            dt_format_end = cls.get_datetime_format_compared_to_reference(dt_end, dt_start, use_compact_format=use_compact_format)
            if len(dt_format_end) > len(dt_format_start):
                dt_format_start = dt_format_end
        else:
            dt_format_end = None
        
        # Format datetimes
        start_txt = DateTime.datetime_2_str(dt_start, dt_format=dt_format_start)
        end_txt = DateTime.datetime_2_str(dt_end, dt_format=dt_format_end) if dt_end is not None else ''
        
        # Truncate formatted datetimes if needed
        if format_precision_nsec is not None:
            trunc_len = len(f'{int(format_precision_nsec)}') - 4
            if trunc_len > 0:
                start_txt = start_txt[:-trunc_len-1]+'Z' if start_txt.endswith('Z') else start_txt[:-trunc_len]
                if len(end_txt) > 0:
                    end_txt = end_txt[:-trunc_len-1]+'Z' if end_txt.endswith('Z') else end_txt[:-trunc_len]
        
        return f"[{start_txt} - {end_txt}]"
    
    @classmethod
    def get_datetime_format_compared_to_reference(cls, dt, dt_ref=None, use_compact_format=default_value):
        if use_compact_format is default_value:
            use_compact_format = Config.report_compact_datetime_period  # @UndefinedVariable
        
        if dt_ref is None:
            return FORMAT_DATETIME_ISO
        
        if not use_compact_format or dt.date() != dt_ref.date():
            return FORMAT_DATETIME_ISO
        elif dt.hour != dt_ref.hour:
            return FORMAT_TIME_ISO
        elif dt.minute != dt_ref.minute:
            return '%M:%S.%f'
        elif dt.second != dt_ref.second:
            return '%S.%f'
        else:
            return '.%f'
    




