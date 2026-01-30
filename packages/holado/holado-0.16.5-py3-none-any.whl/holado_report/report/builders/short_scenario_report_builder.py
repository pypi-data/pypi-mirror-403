
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
from holado_core.common.tools.tools import Tools
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_system.system.filesystem.file import File
from holado_test.common.context.context_tools import ContextTools

logger = logging.getLogger(__name__)



class ShortScenarioReportBuilder(ReportBuilder):
    def __init__(self, filepath, file_format='txt', exclude_statuses=None, exclude_categories=None, use_compact_format=True):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
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
        from holado_report.report.report_manager import ReportManager
        status_info = ReportManager.ScenarioTools.get_current_scenario_status_info(scenario)
        
        # Manage excluded scenarios
        if self.__exclude_statuses and status_info.validation_status in self.__exclude_statuses:
            return
        if status_info.validation_category is not None and self.__exclude_categories:
            ind = status_info.validation_category.find(' (')
            category = status_info.validation_category[:ind] if ind > 0 else status_info.validation_category
            if category in self.__exclude_categories:
                return
        
        self.__file_add_scenario(scenario, scenario_report, status_info)
        
    def after_all(self):
        # Manage file fail
        self.__file.close()
        
    def __file_add_scenario(self, scenario, scenario_report, status_info):
        from holado_report.report.report_manager import ReportManager
        
        self.__open_file_if_needed()
        
        msg_list = []
        category_str = f" => {status_info.validation_category}" if status_info.validation_category else ""
        if status_info.step_failed:
            msg_list.append(f"scenario in {ReportManager.ScenarioTools.format_scenario_short_description(scenario)} - {ReportManager.StepTools.format_step_short_description(status_info.step_failed, status_info.step_failed_nb, has_failed=True)} - {status_info.validation_status}{category_str}")
        else:
            msg_list.append(f"scenario in {ReportManager.ScenarioTools.format_scenario_short_description(scenario)} - {status_info.validation_status}{category_str}")
        msg_list.append(f"    Feature/Scenario: {scenario.feature.name}  =>  {scenario.name}")
        msg_list.append(f"    Report: {scenario_report.report_path}")
        msg_list.append(f"    Tags: -t " + " -t ".join(scenario.feature.tags + scenario.tags))
        
        if status_info.step_context and status_info.step_context.start_datetime is not None:
            msg_list.append(f"    Scenario/Step periods: {ContextTools.format_context_period(status_info.scenario_context, use_compact_format=self.__use_compact_format)} -> {ContextTools.format_context_period(status_info.step_context, dt_ref=status_info.scenario_context.start_datetime, use_compact_format=self.__use_compact_format)}")
        else:
            msg_list.append(f"    Scenario period: {ContextTools.format_context_period(status_info.scenario_context, use_compact_format=self.__use_compact_format)}")
        
        step_error_message = ReportManager.StepTools.get_step_error_message(status_info.step_failed)
        if step_error_message:
            if "\n" in step_error_message:
                msg_list.append(f"    Error message: ")
                msg_list.append(Tools.indent_string(8, step_error_message))
            else:
                msg_list.append(f"    Error message: {step_error_message}")
        
        if status_info.scenario_error is not None:
            if "\n" in status_info.scenario_error:
                msg_list.append(f"    Scenario error: ")
                msg_list.append(Tools.indent_string(8, status_info.scenario_error))
            else:
                msg_list.append(f"    Scenario error: {status_info.scenario_error}")
        
        msg_list.append(f"")
        msg_list.append(f"")
        
        self.__file.writelines(msg_list)
    
    def __open_file_if_needed(self):
        if not self.__file.is_open:
            self.__file.open()
    
