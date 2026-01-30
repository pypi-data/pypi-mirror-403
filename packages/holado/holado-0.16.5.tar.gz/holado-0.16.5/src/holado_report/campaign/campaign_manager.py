
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
from holado_core.common.resource.table_data_manager import TableDataManager
from holado_python.common.tools.datetime import DateTime, TIMEZONE_LOCAL,\
    DurationUnit
import os
from holado_system.system.filesystem.file import File
import re
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado.holado_config import Config
from holado_xml.xml.stream_xml_file import StreamXMLFile
import json
from holado_core.common.tools.tools import Tools
import sys
from holado_python.common.enums import ArithmeticOperator
from datetime import datetime


logger = logging.getLogger(__name__)



class CampaignManager(object):
    """ Manage all campaigns
    """
    
    def __init__(self, db_name="campaigns"):
        super().__init__()
        
        self.__db_name = db_name
        self.__resource_manager = None
        
        self.__campaigns_table_manager = TableDataManager('campaign', 'campaigns', self.__get_campaigns_table_sql_create(), db_name=self.__db_name)
        self.__campaign_scenarios_table_manager = TableDataManager('campaign scenario', 'campaign_scenarios', self.__get_campaign_scenarios_table_sql_create(), db_name=self.__db_name)
    
    def initialize(self, resource_manager):
        self.__resource_manager = resource_manager
        
        self.__campaigns_table_manager.initialize(resource_manager)
        self.__campaigns_table_manager.ensure_db_exists()
        self.__campaign_scenarios_table_manager.initialize(resource_manager)
        self.__campaign_scenarios_table_manager.ensure_db_exists()
    
    def __get_db_client(self):
        return self.__resource_manager.get_db_client(self.__db_name)
    
    def __get_campaigns_table_sql_create(self):
        return """CREATE TABLE campaigns (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                report_path TEXT NOT NULL,
                updated_at TEXT
            )"""

    def __get_campaign_scenarios_table_sql_create(self):
        return """CREATE TABLE campaign_scenarios (
                id INTEGER PRIMARY KEY,
                campaign_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                report_path TEXT,
                status TEXT,
                status_at TEXT,
                details TEXT
            )"""

    def update_stored_campaigns(self):
        """ Update stored reports in DB with new campaigns
        """
        # Get report paths of campaigns to import
        dt_last_camp = self.__get_last_campaign_updated_datetime()
        dt_ref = DateTime.apply_delta_on_datetime(dt_last_camp, ArithmeticOperator.Addition, 1, DurationUnit.Microsecond) if dt_last_camp else None
        report_paths = self.__get_campaigns_report_paths(since_datetime=dt_ref)
        
        # Sort reports in time order
        report_paths = sorted(report_paths, key=lambda p: os.path.getmtime(os.path.join(p, Config.campaign_manager_import_report_name)))  # @UndefinedVariable
        logger.info(f"reports to import: {report_paths}", msg_size_limit=None)
        
        # Import reports
        for report_path in report_paths:
            self.import_campaign_reports(report_path)
    
    def __get_campaigns_report_paths(self, since_datetime):
        reports_path = SessionContext.instance().path_manager.get_reports_path(name="test_runner", with_application_group=False)
        file_paths = SessionContext.instance().path_manager.find_files(reports_path, 
                                                                       subdir_relative_path=Config.campaign_manager_import_report_name,  # @UndefinedVariable
                                                                       since_datetime=since_datetime)
        return [os.path.dirname(p) for p in file_paths]
    
    def __get_last_campaign_updated_datetime(self):
        """ From stored campaigns, return the datetime of the last updated campaign
        """
        client = self.__get_db_client()
        
        query_str = f'''
            SELECT updated_at
            FROM campaigns
            WHERE updated_at is not NULL
            ORDER BY updated_at DESC 
            LIMIT 1
        '''
        res_dict_list = client.execute(query_str, result_as_dict_list=True, as_generator=False)
        
        updated_dt_str = res_dict_list[0]['updated_at'] if res_dict_list else None
        updated_dt = DateTime.str_2_datetime(updated_dt_str, tz=TIMEZONE_LOCAL) if updated_dt_str else None
        return updated_dt
        
    def __get_campaign_updated_datetime(self, camp_id):
        data = self.__campaigns_table_manager.get_data(filter_data={'id':camp_id})
        if data is not None and DateTime.is_str_datetime(data['updated_at']):
            return DateTime.str_2_datetime(data['updated_at'], tz=TIMEZONE_LOCAL)
        else:
            return None
        
    def __update_campaign_updated_datetime(self, camp_id, updated_datetime):
        updated_dt_str = updated_datetime
        if isinstance(updated_dt_str, datetime):
            updated_dt_str = DateTime.datetime_2_str(updated_dt_str)
        self.__campaigns_table_manager.update_data({'updated_at':updated_dt_str}, filter_data={'id':camp_id})
        
    # def __get_last_campaign_scenario_status_datetime(self):
    #     """ From stored campaigns, return the datetime of the last scenario with an execution status
    #     """
    #     client = self.__get_db_client()
    #
    #     query_str = f'''
    #         SELECT status_at
    #         FROM campaign_scenarios
    #         ORDER BY status_at DESC 
    #         LIMIT 1
    #     '''
    #     res_dict_list = client.execute(query_str, result_as_dict_list=True, as_generator=False)
    #
    #     status_dt_str = res_dict_list[0]['status_at'] if res_dict_list else None
    #     status_dt = DateTime.str_2_datetime(status_dt_str, tz=TIMEZONE_LOCAL) if status_dt_str else None
    #     return status_dt
        
    def import_campaign_reports(self, report_path):
        """ Import reports of a campaign
        @param report_path Path to the campaign report
        """
        logger.info(f"Import campaign report '{report_path}'")
        
        # Add campaign
        camp_name = os.path.basename(report_path)
        camp_id = self.add_campaign_if_needed(camp_name, report_path)
        
        # Import scenario status if needed
        if self.__do_campaign_needs_import(report_path, camp_id):
            updated_dt = None
            
            # Import information from 'report_detailed_scenario.xml'
            try:
                updated_dt = self.__import_campaign_report_detailed_scenario(report_path, camp_id)
            except Exception as exc:
                if not 'No such file or directory' in str(exc):
                    logger.error(f"Failed to import campaign report '{report_path}' from '{Config.campaign_manager_import_report_name}': {Tools.represent_exception(exc)}")  # @UndefinedVariable
                    sys.exit(1)
                else:
                    logger.debug(f"Failed to import campaign report '{report_path}' from '{Config.campaign_manager_import_report_name}': {str(exc)}")  # @UndefinedVariable
            else:
                logger.debug(f"Imported campaign report '{report_path}' from '{Config.campaign_manager_import_report_name}'")  # @UndefinedVariable
            
            # Try to import information from 'report_summary_scenario_all.txt'
            if updated_dt is None:
                try:
                    updated_dt = self.__import_campaign_report_summary_scenario_all(report_path, camp_id)
                except:
                    raise TechnicalException(f"Failed to import campaign report '{report_path}'")
                else:
                    logger.debug(f"Imported campaign report '{report_path}' from 'report_summary_scenario_all.txt'")
            
            # Update campaign updated datetime
            self.__update_campaign_updated_datetime(camp_id, updated_dt)
    
    def get_scenario_history(self, scenario_name=None, size=None):
        client = self.__get_db_client()
        placeholder = client._get_sql_placeholder()
        
        # Get data from DB
        where_clause = ""
        where_data = []
        if scenario_name is not None:
            where_clause = f"where name = {placeholder}"
            where_data.append(scenario_name)
        
        query_str = f'''
            SELECT *
            FROM campaign_scenarios
            {where_clause}
            ORDER BY name, status_at DESC 
        '''
        camp_scenarios_gen = client.execute(query_str, *where_data, result_as_dict_list=True, as_generator=True)
        
        # Build result
        res = []
        cur_scenario_name = None
        cur_scenario_statuses = None
        for cs in camp_scenarios_gen:
            # Manage new scenario
            if cur_scenario_name is None or cur_scenario_name != cs['name']:
                cur_scenario_statuses = []
                cur_scenario_name = cs['name']
                res.append({'name':cur_scenario_name, 'statuses':cur_scenario_statuses})
            
            # Add campaign info for this scenario execution if size limit is not reached
            if size is None or len(cur_scenario_statuses) < size:
                cur_scenario_statuses.append({'at':cs['status_at'], 'status':cs['status']})
            
        return res
        
    def add_campaign_if_needed(self, name, report_path):
        filter_data = {'report_path': report_path}
        if not self.__campaigns_table_manager.has_data(filter_data):
            self.__campaigns_table_manager.add_data(filter_data, {'name': name})
        camp = self.__campaigns_table_manager.get_data(filter_data)
        return camp['id']
    
    def update_or_add_campaign_scenario(self, campaign_id, name, *, report_path=None, status=None, status_at_str=None, details=None):
        filter_data = {'campaign_id': campaign_id, 'name': name}
        data = {}
        if report_path is not None:
            data['report_path'] = report_path
        if status is not None:
            data['status'] = status
        if status_at_str is not None:
            data['status_at'] = status_at_str
        if details is not None:
            data['details'] = details
        
        self.__campaign_scenarios_table_manager.update_or_add_data(filter_data, data)
        # camp_sce = self.__campaign_scenarios_table_manager.get_data(filter_data)
        # return camp_sce['id']
    
    def __do_campaign_needs_import(self, report_path, camp_id):
        stored_dt = self.__get_campaign_updated_datetime(camp_id)
        if stored_dt is None:
            return True
        
        file_path = os.path.join(report_path, Config.campaign_manager_import_report_name)  # @UndefinedVariable
        if not os.path.exists(file_path):
            return True
        
        file_dt = DateTime.timestamp_to_datetime(os.path.getmtime(file_path))
        return file_dt > stored_dt
    
    def __get_campaign_status_at_by_scenario(self, camp_id):
        res = {}
        
        filter_data = {'campaign_id':camp_id}
        for data in self.__campaign_scenarios_table_manager.get_datas(filter_data, as_generator=True):
            res[data['name']] = data['status_at']
        
        return res
    
    def __import_campaign_report_detailed_scenario(self, report_path, camp_id):
        filepath = os.path.join(report_path, Config.campaign_manager_import_report_name)  # @UndefinedVariable
        if not os.path.exists(filepath):
            return None
        
        status_at_by_scenario = self.__get_campaign_status_at_by_scenario(camp_id)
        
        # Note: get file modified datetime just before reading it, so that modified datetime is not outdated and elements will be missed on next import 
        file_modified_dt = DateTime.timestamp_to_datetime(os.path.getmtime(filepath))
        with StreamXMLFile(filepath) as fin:
            scenarios = fin.read_elements_as_dict_list(force=True)      # 'force' is True to be able to read XML files with "invalid" UTF-8 characters.
        if Tools.do_log(logger, logging.TRACE):  # @UndefinedVariable
            logger.trace(f"Elements read in '{filepath}':\n{scenarios}")
        
        regex_period = re.compile(r"^\[(.+) - ([^\]]+)\]$")
        for scenario_index, scenario in enumerate(scenarios):
            if 'scenario' not in scenario:
                raise TechnicalException(f"Unexpected structure of {scenario_index+1}'th scenario: {scenario}")
            scenario = scenario['scenario']
            
            name = scenario['file']
            
            m = regex_period.match(scenario['scenario_period'])
            if m:
                status_at_str = m.group(2)
                # If report is done with dates in compact format, end datetime in period is not a valid datetime, use begin datetime instead
                if not DateTime.is_str_datetime(status_at_str[:10], '%Y-%m-%d'):
                    status_at_str = m.group(1)
            else:
                raise TechnicalException(f"Failed to import report of scenario '{name}' in campaign report file '{filepath}'")
            
            if name in status_at_by_scenario and status_at_str == status_at_by_scenario[name]:
                # Scenario result is already stored
                continue
            
            scenario_report_path = scenario['report']
            status = scenario['validation_status']
            details = json.dumps( {k:scenario[k] for k in scenario.keys() if k not in ['file', 'scenario_period', 'report', 'validation_status']} )
            
            self.update_or_add_campaign_scenario(camp_id, name, report_path=scenario_report_path, status=status, status_at_str=status_at_str, details=details)
        
        return file_modified_dt
        
    def __import_campaign_report_summary_scenario_all(self, report_path, camp_id):
        file_path = os.path.join(report_path, 'report_summary_scenario_all.txt')
        if not os.path.exists(file_path):
            return None
        
        # Note: get file modified datetime just before reading it, so that modified datetime is not outdated and elements will be missed on next import 
        file_modified_dt = DateTime.timestamp_to_datetime(os.path.getmtime(file_path))
        lines = File(file_path, do_open=True, mode='rt').readlines(strip_newline=True)
        
        regex_line_period = re.compile(r"^\[(.+) - ([^\]]+)\] (.+?)(?: - .+)? - (.*)$")
        regex_line_time = re.compile(r"^(.+?) - (.+?)(?: - .+)? - (.+)$")
        regex_status = re.compile(r"^(.*?)(?: \(.*\)| => .*)?$")
        
        for line in lines:
            m = regex_line_period.match(line)
            if m:
                status_at_str = m.group(2)
                # If report is done with dates in compact format, end datetime in period is not a valid datetime, use begin datetime instead
                if not DateTime.is_str_datetime(status_at_str[:10], '%Y-%m-%d'):
                    status_at_str = m.group(1)
                scenario_name = m.group(3)
                status_info = m.group(4)
            else:
                m = regex_line_time.match(line)
                if not m:
                    raise TechnicalException(f"Unexpected line format in {file_path}: [{line}]")
                status_at_str = m.group(1)
                scenario_name = m.group(2)
                status_info = m.group(3)
            
            m = regex_status.match(status_info)
            status = m.group(1)
            
            self.update_or_add_campaign_scenario(camp_id, scenario_name, status=status, status_at_str=status_at_str)
        
        return file_modified_dt


