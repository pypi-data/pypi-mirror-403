
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

from holado_core.common.tools.tools import Tools
import logging
from holado_report.report.builders.report_builder import ReportBuilder
from holado_xml.xml.stream_xml_file import StreamXMLFile
from holado_system.system.filesystem.file import File
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_test.common.context.context_tools import ContextTools

logger = logging.getLogger(__name__)



class DetailedScenarioReportBuilder(ReportBuilder):
    """ Detailed scenario report
    It is dedicated to have a convenient compromise between completeness and shortness.
    
    Notes: XML version of this report is mandatory by test-server as it uses CampaignManager that needs it in its campaign import process.
           For this import process, all periods must be in uncompact format, thus this format is forced in XML format management.
    """
    def __init__(self, filepath, file_format='xml', exclude_statuses=None, exclude_categories=None):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        
        if self.__file_format == 'xml':
            self.__file = StreamXMLFile(filepath, mode='wt')
        elif self.__file_format == 'txt':
            self.__file = File(filepath, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt', 'xml')")
        
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
        # Manage file
        self.__file.close()
        
    def __file_add_scenario(self, scenario, scenario_report, status_info):
        if self.__file_format == 'xml':
            self.__file_add_scenario_xml(scenario, scenario_report, status_info)
        else:
            self.__file_add_scenario_txt(scenario, scenario_report, status_info)
        
    def __file_add_scenario_xml(self, scenario, scenario_report, status_info):
        from holado_report.report.report_manager import ReportManager
        
        self.__open_file_if_needed()
        
        data = {
            'scenario': {
                'file': ReportManager.ScenarioTools.format_scenario_short_description(scenario),
                'feature': scenario.feature.name,
                'scenario': scenario.name,
                'scenario_period': ContextTools.format_context_period(status_info.scenario_context, use_compact_format=False),
                'report': scenario_report.report_path,
                'tags': "-t " + " -t ".join(scenario.feature.tags + scenario.tags),
                }
            }
        if status_info.validation_category:
            data['scenario']['validation_category'] = status_info.validation_category
        data['scenario']['validation_status'] = status_info.validation_status
        
        failure_data = {}
        if status_info.step_failed is not None:
            failure_data['step_number'] = status_info.step_failed_nb
            failure_data['step_line'] = status_info.step_failed.line
            if status_info.step_context and status_info.step_context.start_datetime is not None:
                failure_data['step_period'] = ContextTools.format_context_period(status_info.step_context, use_compact_format=False)

            step_descr = ReportManager.StepTools.get_step_description(status_info.step_failed)
            if "\n" in step_descr:
                failure_data['step'] = "\n" + Tools.indent_string(12, step_descr) + Tools.indent_string(8, "\n")
            else:
                failure_data['step'] = step_descr
                
            step_error_message = ReportManager.StepTools.get_step_error_message(status_info.step_failed)
            if step_error_message:
                if "\n" in step_error_message:
                    failure_data['error_message'] = "\n" + Tools.indent_string(12, step_error_message) + Tools.indent_string(8, "\n")
                else:
                    failure_data['error_message'] = step_error_message
            
            step_error = ReportManager.StepTools.get_step_error(status_info.step_failed)
            if step_error and step_error != step_error_message:
                if "\n" in step_error:
                    failure_data['error'] = "\n" + Tools.indent_string(12, step_error) + Tools.indent_string(8, "\n")
                else:
                    failure_data['error'] = step_error
                    
        if status_info.scenario_error:
            if "\n" in status_info.scenario_error:
                failure_data['scenario_error'] = "\n" + Tools.indent_string(12, status_info.scenario_error) + Tools.indent_string(8, "\n")
            else:
                failure_data['scenario_error'] = status_info.scenario_error
                
        if failure_data:
            data['scenario']['failure'] = failure_data
        elif status_info.validation_status != 'Passed':
            data['scenario']['failure'] = "No step failed, it has probably failed on a missing step implementation"
            
        self.__file.write_element_dict(data, pretty=True, indent=Tools.indent_string(4, ''))
        # Add 2 empty lines for more readability
        self.__file.internal_file.writelines(['', ''])
        
    def __file_add_scenario_txt(self, scenario, scenario_report, status_info):
        from holado_report.report.report_manager import ReportManager
        
        self.__open_file_if_needed()
        
        msg_list = [f"{scenario.filename} - l.{scenario.line}"]
        msg_list.append(f"    Feature: {scenario.feature.name}")
        msg_list.append(f"    Scenario: {scenario.name}")
        msg_list.append(f"    Report: {scenario_report.report_path}")
        msg_list.append(f"    Scenario period: {ContextTools.format_context_period(status_info.scenario_context)}")
        msg_list.append(f"    Tags: -t " + " -t ".join(scenario.feature.tags + scenario.tags))
        if status_info.validation_category:
            msg_list.append(f"    Validation category: {status_info.validation_category}")
        msg_list.append(f"    Validation status: {status_info.validation_status}")
        if status_info.step_failed is not None or status_info.scenario_error:
            msg_list.append(f"    Failure:")
            if status_info.step_failed is not None:
                msg_list.append(f"        Step number-line: {status_info.step_failed_nb} - l.{status_info.step_failed.line}")
                if status_info.step_context and status_info.step_context.start_datetime is not None:
                    msg_list.append(f"        Step period: {ContextTools.format_context_period(status_info.step_context)}")
                step_descr = ReportManager.StepTools.get_step_description(status_info.step_failed)
                if "\n" in step_descr:
                    msg_list.append(f"        Step:")
                    msg_list.append(Tools.indent_string(12, step_descr))
                else:
                    msg_list.append(f"        Step: {step_descr}")
                    
                step_error = ReportManager.StepTools.get_step_error(status_info.step_failed)
                if step_error:
                    if "\n" in step_error:
                        msg_list.append(f"        Error:")
                        msg_list.append(Tools.indent_string(12, step_error))
                    else:
                        msg_list.append(f"        Error: {step_error}")
            
            if status_info.scenario_error:
                if "\n" in status_info.scenario_error:
                    msg_list.append(f"        Scenario error:")
                    msg_list.append(Tools.indent_string(12, status_info.scenario_error))
                else:
                    msg_list.append(f"        Scenario error: {status_info.scenario_error}")
        else:
            msg_list.append(f"    Failure: No step failed, it has probably failed on a missing step implementation")
        msg_list.append(f"")
        msg_list.append(f"")
            
        self.__file.writelines(msg_list)
    
    def __open_file_if_needed(self):
        if not self.__file.is_open:
            self.__file.open()
    
    
