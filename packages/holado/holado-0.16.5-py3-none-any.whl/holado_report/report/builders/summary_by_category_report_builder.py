
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
from holado_system.system.filesystem.file import File
from holado_core.common.exceptions.technical_exception import TechnicalException

logger = logging.getLogger(__name__)



class SummaryByCategoryReportBuilder(ReportBuilder):
    def __init__(self, filepath, file_format='txt', exclude_statuses=None, exclude_categories=None):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        
        if self.__file_format == 'txt':
            self.__file = File(filepath, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt')")
        
        self.__counter_by_category = {}
        self.__categories_order = [
                'Newly Failed',
                'Regression',
                'Always Failed',
                'Random',
                'Newly Failed but Not Relevant',
                'Regression but Not Relevant',
                'Always Not Relevant',
                'Random but Not Relevant',
                'Always Success',
                'Fixed',
                'Unknown'
            ]
        
    def build(self):
        '''
        The file is built after each scenario
        '''
        pass
        
    def after_scenario(self, scenario, scenario_report=None):
        from holado_report.report.report_manager import ReportManager
        status_info = ReportManager.ScenarioTools.get_current_scenario_status_info(scenario)
        if status_info.validation_category is not None:
            ind = status_info.validation_category.find(' (')
            category = status_info.validation_category[:ind] if ind > 0 else status_info.validation_category
        else:
            category = None
        
        # Manage excluded scenarios
        if self.__exclude_statuses and status_info.validation_status in self.__exclude_statuses:
            return
        if category is not None and self.__exclude_categories and category in self.__exclude_categories:
            return
        
        if category is not None:
            if category not in self.__counter_by_category:
                self.__counter_by_category[category] = 0
            self.__counter_by_category[category] += 1
            
            # Update categories order with unexpected category
            if category not in self.__categories_order:
                self.__categories_order.append(category)
            
            self.__update_file()
        
    def __update_file(self):
        list_by_group = {
            'Success': [(k,self.__counter_by_category[k]) for k in self.__categories_order 
                        if k in self.__counter_by_category and k in ['Always Success', 'Fixed']],
            'Failed': [(k,self.__counter_by_category[k]) for k in self.__categories_order 
                       if k in self.__counter_by_category and k in ['Newly Failed', 'Regression', 'Always Failed', 'Random']],
            'Not Relevant': [(k,self.__counter_by_category[k]) for k in self.__categories_order 
                             if k in self.__counter_by_category and k in ['Newly Failed but Not Relevant', 'Regression but Not Relevant', 'Always Not Relevant', 'Random but Not Relevant']]
            }
        others_list = [(k,v) for k,v in self.__counter_by_category.items() 
                       if k not in ['Always Success', 'Fixed', 'Newly Failed', 'Regression', 'Always Failed', 'Random', 'Newly Failed but Not Relevant', 'Regression but Not Relevant', 'Always Not Relevant', 'Random but Not Relevant']]
        
        lines = []
        for group_name, group_list in list_by_group.items():
            if group_list:
                lines.append(f"{group_name:>12s}: {sum([x[1] for x in group_list]):5d}  ({' ; '.join([f'{x[0]}: {x[1]}' for x in group_list])})")
            else:
                lines.append(f"{group_name:>12s}: {0:5d}")
        if others_list:
            lines.append(f"{'Others':>12s}: {sum([x[1] for x in others_list]):5d}  ({' ; '.join([f'{x[0]}: {x[1]}' for x in others_list])})")

        with self.__file as fout:
            fout.writelines(lines)
        
        
