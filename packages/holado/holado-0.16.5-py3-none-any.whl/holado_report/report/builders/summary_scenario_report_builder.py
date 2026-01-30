
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
from holado_report.report.builders.report_builder import ReportBuilder
from holado_report.report.report_manager import ReportManager
from holado_python.common.tools.datetime import FORMAT_DATETIME_ISO, DateTime
from holado_system.system.filesystem.file import File
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_test.common.context.context_tools import ContextTools

logger = logging.getLogger(__name__)



class SummaryScenarioReportBuilder(ReportBuilder):
    def __init__(self, filepath, file_format='txt', exclude_statuses=None, exclude_categories=None, with_scenario_end_date=True, with_scenario_period=False, with_step_period=False, use_compact_format=True):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        self.__with_scenario_end_date = with_scenario_end_date
        self.__with_scenario_period = with_scenario_period
        self.__with_step_period = with_step_period
        self.__use_compact_format = use_compact_format
        
        if self.__file_format == 'txt':
            self.__file = File(filepath, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt')")
        
    def build(self):
        '''
        The file is built after each scenario
        '''
        pass
        
    def after_scenario(self, scenario, scenario_report=None):
        status_info = ReportManager.ScenarioTools.get_current_scenario_status_info(scenario)
        
        # Manage excluded scenario on status
        if self.__exclude_statuses and status_info.validation_status in self.__exclude_statuses:
            return
        
        self.__file_add_scenario(scenario, status_info)
            
    def after_all(self):
        self.__file.close()
        
    def __file_add_scenario(self, scenario, status_info):
        self.__open_file_if_needed()
        
        # Manage excluded scenario on category
        if status_info.validation_category:
            ind = status_info.validation_category.find(' (')
            category = status_info.validation_category[:ind] if ind > 0 else status_info.validation_category
            if self.__exclude_categories and category in self.__exclude_categories:
                return
        
        category_str = f" => {status_info.validation_category}" if status_info.validation_category else ""
        scenario_prefix_str = f"{ContextTools.format_context_period(status_info.scenario_context)} " if self.__with_scenario_period \
                              else f"{DateTime.datetime_2_str(status_info.scenario_context.end_datetime, FORMAT_DATETIME_ISO)} - " if self.__with_scenario_end_date else ""
        if status_info.step_failed:
            step_format_kwargs = {'step_context': status_info.step_context if self.__with_step_period else None,
                                  'dt_ref': status_info.scenario_context.start_datetime if self.__use_compact_format else None}
            self.__file.write(f"{scenario_prefix_str}{ReportManager.ScenarioTools.format_scenario_short_description(scenario)} - {ReportManager.StepTools.format_step_short_description(status_info.step_failed, status_info.step_failed_nb, has_failed=True, **step_format_kwargs)} - {status_info.validation_status}{category_str}\n")
        else:
            self.__file.write(f"{scenario_prefix_str}{ReportManager.ScenarioTools.format_scenario_short_description(scenario)} - {status_info.validation_status}{category_str}\n")
    
    def __open_file_if_needed(self):
        if not self.__file.is_open:
            self.__file.open()
    
