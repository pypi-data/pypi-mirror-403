
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
import weakref
from holado_system.system.filesystem.file import File
from holado_core.common.exceptions.technical_exception import TechnicalException

logger = logging.getLogger(__name__)



class ExecutionHistoricSummaryReportBuilder(ReportBuilder):
    def __init__(self, execution_historic, filepath):
        self.__execution_historic_weakref = weakref.ref(execution_historic)
        self.__filepath = filepath

    @property
    def __execution_historic(self):
        return self.__execution_historic_weakref()

    def build(self):
        features = {}
        scenarios = {}
        for eh_feat in self.__execution_historic:
            status_name = eh_feat.feature.status.name
            if status_name not in features:
                features[status_name] = 0
            features[status_name] += 1
            
            for eh_sce in eh_feat.scenarios:
                status_name = eh_sce.status_info.validation_status
                # status_name = eh_sce[0].status.name.lower()
                if status_name not in scenarios:
                    scenarios[status_name] = 0
                scenarios[status_name] += 1
            
        with open(self.__filepath, "wt") as feh:
            feh.write("features: " + ", ".join([f"{v} {k}" for k, v in dict(sorted(features.items())).items()]) + "\n")
            feh.write("scenarios: " + ", ".join([f"{v} {k}" for k, v in dict(sorted(scenarios.items())).items()]) + "\n")
        
    
class SummaryReportBuilder(ReportBuilder):
    def __init__(self, filepath, file_format='txt', with_features=True, exclude_statuses=None, exclude_categories=None):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        self.__with_features = with_features
        
        if self.__file_format == 'txt':
            self.__file = File(filepath, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt')")
        
        self.__features = {}
        self.__scenarios = {}

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
        
        if status_info.validation_status not in self.__scenarios:
            self.__scenarios[status_info.validation_status] = 0
        self.__scenarios[status_info.validation_status] += 1
        
        self.__update_file()
    
    def after_feature(self, feature, feature_report=None):
        status_name = feature.status.name
        if status_name not in self.__features:
            self.__features[status_name] = 0
        self.__features[status_name] += 1
        
        self.__update_file()
    
    def __update_file(self):
        with self.__file as fout:
            if self.__with_features:
                fout.write("features: " + ", ".join([f"{v} {k}" for k, v in dict(sorted(self.__features.items())).items()]) + "\n")
            fout.write("scenarios: " + ", ".join([f"{v} {k}" for k, v in dict(sorted(self.__scenarios.items())).items()]) + "\n")
    
    
    
    
