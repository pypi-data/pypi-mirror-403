
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
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado.common.handlers.object import DeleteableObject
from holado_multitask.multithreading.functionthreaded import FunctionThreaded
from holado_python.common.tools.datetime import DateTime
import json
from holado_json.filesystem.stream_json_file import StreamJSONFile
import re
from holado.common.context.session_context import SessionContext
import os
from datetime import datetime
import copy
from holado_system.system.filesystem.file import File
from holado.common.handlers.undefined import is_undefined, default_value
import time

logger = logging.getLogger(__name__)


def _get_timestamps_field_name(input_field_name):
    if input_field_name is None:
        return None
    elif is_undefined(input_field_name):
        return 'time'
    else:
        return input_field_name

def _get_include_others_name(input_include_others_name):
    if input_include_others_name is None:
        return None
    elif is_undefined(input_include_others_name):
        return '[others]'
    else:
        return input_include_others_name


class DockerContainerLogsFollower(DeleteableObject):
    """Generic follower of logs of a container
    """
    def __init__(self, docker_container):
        super.__init__(self, docker_container.container.name)
        self.__docker_container = docker_container
        self.__logs = []
        self.__logs_stream = None
        self.__thread = None
    
    def _delete_object(self):
        self.close()
    
    def close(self):
        if self.__logs_stream is not None:
            self.__logs_stream.close()
            self.__thread.join()
            
            self.__logs_stream = None
            self.__thread = None
    
    def follow_logs(self, stdout=True, stderr=True, tail='all', since=None):
        """Follow logs from Docker Engine
        """
        if isinstance(since, str):
            since = DateTime.str_2_datetime(since)
        
        if self.__logs_stream is not None:
            raise TechnicalException(f"Logs of container '{self.name}' are already followed")
        self.__logs_stream = self.__docker_container.container.logs(stdout=stdout, stderr=stderr, tail=tail, since=since, stream=True, timestamps=True)
        
        self.__thread = FunctionThreaded(self.__read_stream, name=f"follow logs of container '{self.__docker_container.container.name}'", register_thread=False)
        self.__thread.interrupt_function = self.__logs_stream.close
        self.__thread.start()
    
    def __read_stream(self):
        for log in self.__logs_stream:
            self.__logs.append( (log['time'], log['steam'] == 'stdout', self.__docker_container._get_log_from_log_bytes(log['log'])) )
    
    def reset(self):
        self.__logs.clear()
    
    def get_logs(self, stdout=True, stderr=True, timestamps=False, tail='all', since=None, until=None, wait_before_s=0.1):
        if wait_before_s is not None:
            time.sleep(wait_before_s)
        
        if since is not None and isinstance(since, datetime):
            since = DateTime.datetime_2_str(since)
        if until is not None and isinstance(until, datetime):
            until = DateTime.datetime_2_str(until)
        
        res = []
        for log in self.__logs:
            if log[1] and not stdout or not log[1] and not stderr:
                continue
            if since is not None and log[0] < since:
                continue
            if until is not None and log[0] >= until:
                continue
            
            if timestamps:
                res.append( (log[0], log[2]) )
            else:
                res.append(log[2])
        
        if tail != 'all':
            if not isinstance(tail, int) or tail < 0:
                raise TechnicalException(f"Argument 'tail' can be 'all' or a positive integer")
            res = res[-tail:]
        
        return res




class DockerContainerLogsFormatter(object):
    """Base class for formatters of container logs.
    """
    def __init__(self, include_patterns=None, exclude_patterns=None, include_others_name=default_value):
        """ Constructor
        @param include_patterns: patterns of log fields to include
        @param exclude_patterns: patterns of log fields to exclude
        @param include_others_name: if defined, all fields not included and not excluded are grouped in this field name (used only if include_patterns is defined)
        """
        self.__include_patterns = {p if isinstance(p, re.Pattern) else re.compile(p):pinfo for p, pinfo in include_patterns.items()} if include_patterns is not None else None
        self.__exclude_patterns = [ep if isinstance(ep, re.Pattern) else re.compile(ep) for ep in exclude_patterns] if exclude_patterns is not None else None
        self.__include_others_name = _get_include_others_name(include_others_name)
    
    def _filter_json_log_fields(self, log_dict):
        if self.__include_patterns is None and self.__exclude_patterns is None:
            # No filters are defined
            return log_dict
        
        res = {}
        log = copy.copy(log_dict)
        
        # Manage included fields and remove them from source copy
        if self.__include_patterns is not None:
            for pat, pat_info in self.__include_patterns.items():
                for key in list(log.keys()):
                    if pat.match(key):
                        name = pat_info['replace'] if 'replace' in pat_info else key
                        res[name] = log.pop(key)
        
        # Manage excluded fields and remove them from source copy
        if self.__exclude_patterns is not None:
            for pat in self.__exclude_patterns:
                for key in list(log.keys()):
                    if pat.match(key):
                        del log[key]
        
        # Manage remaining fields of source copy
        if log:
            if self.__include_patterns is not None:
                if self.__include_others_name is not None:
                    # Include remaining fields in surrounding field self.__include_others_name
                    res[self.__include_others_name] = log
            else:
                # Remaining fields are the result
                res = log
        
        return res
    
    def format_logs(self, logs, with_timestamps=False):
        raise NotImplementedError()

class JsonDockerContainerLogsFormatter(DockerContainerLogsFormatter):
    """Formatter of container logs in JSON format.
    """
    def __init__(self, timestamps_field_name=default_value, include_patterns=None, exclude_patterns=None, include_others_name=None):
        """ Constructor
        @param timestamps_field_name: field name of timestamps if they are added to logs
        @param include_patterns: patterns of log fields to include
        @param exclude_patterns: patterns of log fields to exclude
        @param include_others_name: if defined, all fields not included and not excluded are grouped in this field name (used only if include_patterns is defined)
        """
        super().__init__(include_patterns, exclude_patterns, include_others_name)
        self.__timestamps_field_name = _get_timestamps_field_name(timestamps_field_name)
    
    def format_logs(self, logs, with_timestamps=False):
        if with_timestamps and self.__timestamps_field_name is None:
            raise TechnicalException("Timestamps field name must defined to include docker timestamps")
        
        res = []
        
        for log in logs:
            ts = None
            if with_timestamps:
                ts, log = log[0], log[1]
            
            res_log = {}
            
            # Begin by timestamp so that it is the first dict element
            if ts is not None:
                res_log[self.__timestamps_field_name] = ts
            
            # Add log as JSON format
            try:
                log_dict = json.loads(log)
            except:
                # In some circumstances (ex: container is in panic), logs can be in another format even if configured in json format
                log_dict = {'log':log}
            res_log.update(self._filter_json_log_fields(log_dict))
            
            res.append(res_log)
        
        return res




class DockerContainerLogsSaver(object):
    """Base class for savers of docker container logs.
    """
    def __init__(self, timestamps_field_name=default_value, include_patterns=None, exclude_patterns=None, include_others_name=default_value, formatter=None):
        """ Constructor
        @param formatter: logs formatter
        """
        self.__timestamps_field_name = _get_timestamps_field_name(timestamps_field_name)
        self.__include_patterns = {p if isinstance(p, re.Pattern) else re.compile(p):pinfo for p, pinfo in include_patterns.items()} if include_patterns is not None else None
        self.__exclude_patterns = [ep if isinstance(ep, re.Pattern) else re.compile(ep) for ep in exclude_patterns] if exclude_patterns is not None else None
        self.__include_others_name = _get_include_others_name(include_others_name)
        self.__formatter = formatter
        
        if self.__formatter is None:
            self.__formatter = JsonDockerContainerLogsFormatter(timestamps_field_name=timestamps_field_name, include_patterns=include_patterns, exclude_patterns=exclude_patterns, include_others_name=include_others_name)
    
    def get_logs(self, docker_container, stdout=True, stderr=True, timestamps=True, tail='all', since=None, until=None, wait_before_s=0.1):
        return docker_container.get_logs(stdout=stdout, stderr=stderr, timestamps=timestamps, tail=tail, since=since, until=until, wait_before_s=wait_before_s, formatter=self.__formatter)
        
    def save_logs(self, docker_container, full_file_name, stdout=True, stderr=True, timestamps=True, tail='all', since=None, until=None):
        """ Save logs of a container.
        @return: number of logs saved
        """
        raise NotImplementedError()
    
    def _define_field_names_for_logs(self, logs):
        res = []
        
        # Get all field names from logs
        names = list(set().union(*logs))
        
        # Sort by included fields
        if self.__timestamps_field_name and self.__timestamps_field_name in names:
            res.append(self.__timestamps_field_name)
            names.remove(self.__timestamps_field_name)
        if self.__include_patterns:
            for ip, ip_info in self.__include_patterns.items():
                i = 0
                while i < len(names):
                    if ip_info and 'replace' in ip_info:
                        if names[i] == ip_info['replace']:
                            res.append(names.pop(i))
                            continue
                    elif ip.match(names[i]):
                        res.append(names.pop(i))
                        continue
                    
                    # else increment counter
                    i += 1
        
        # Add remaining names in alphabetical order
        if names:
            res.extend(sorted(names))
        
        return res
    
    def _get_log_fields_values(self, field_names, log, missing_field_value=''):
        res = []
        
        for name in field_names:
            if name in log:
                res.append(log[name])
            else:
                res.append(missing_field_value)
        
        return res
    

class JsonDockerContainerLogsSaver(DockerContainerLogsSaver):
    """Saver of docker container logs in a stream JSON file.
    """
    def __init__(self, timestamps_field_name=default_value, include_patterns=None, exclude_patterns=None, include_others_name=default_value, formatter=None, **dumps_kwargs):
        """ Constructor
        @param timestamps_field_name: field name of timestamps if they are added to logs
        @param include_patterns: patterns of log fields to include
        @param exclude_patterns: patterns of log fields to exclude
        @param include_others_name: if defined, all fields not included and not excluded are grouped in this field name (used only if include_patterns is defined)
        @param formatter: formatter to use (if defined, previous fields are omitted)
        @param dumps_kwargs: all additional kwargs are used as json.dumps additional parameters
        """
        super().__init__(timestamps_field_name=timestamps_field_name, include_patterns=include_patterns, exclude_patterns=exclude_patterns, include_others_name=include_others_name, formatter=formatter)
        self.__dumps_kwargs = dumps_kwargs
        
    def save_logs(self, docker_container, full_file_name, stdout=True, stderr=True, timestamps=True, tail='all', since=None, until=None, wait_before_s=0.1):
        res = None
        
        file_path = f"{full_file_name}.json"
        SessionContext.instance().path_manager.makedirs(file_path)
        
        logs = self.get_logs(docker_container, stdout=stdout, stderr=stderr, timestamps=timestamps, tail=tail, since=since, until=until, wait_before_s=wait_before_s)
        if logs:
            with StreamJSONFile(file_path, mode='wt') as fout:
                fout.write_elements_json_object_list(logs, **self.__dumps_kwargs)
            res = len(logs)
            logger.info(f"Saved {res} logs for container '{docker_container.container.name}' in file '{file_path}'")
        
        return res

class PrettyTableDockerContainerLogsSaver(DockerContainerLogsSaver):
    """Saver of docker container logs in a pretty table file.
    """
    def __init__(self, timestamps_field_name=default_value, include_patterns=None, exclude_patterns=None, include_others_name=default_value, formatter=None, **prettytable_kwargs):
        """ Constructor
        @param timestamps_field_name: field name of timestamps if they are added to logs
        @param include_patterns: patterns of log fields to include
        @param exclude_patterns: patterns of log fields to exclude
        @param include_others_name: if defined, all fields not included and not excluded are grouped in this field name (used only if include_patterns is defined)
        @param formatter: formatter to use (if defined, previous fields are omitted)
        @param prettytable_kwargs: all additional kwargs are used as PrettyTable constructor parameters
        """
        super().__init__(timestamps_field_name=timestamps_field_name, include_patterns=include_patterns, exclude_patterns=exclude_patterns, include_others_name=include_others_name, formatter=formatter)
        self.__prettytable_kwargs = prettytable_kwargs
        
    def save_logs(self, docker_container, full_file_name, stdout=True, stderr=True, timestamps=True, tail='all', since=None, until=None, wait_before_s=0.1):
        import prettytable
        from prettytable.prettytable import PrettyTable, TableStyle
        
        res = None
        
        file_path = f"{full_file_name}.txt"
        SessionContext.instance().path_manager.makedirs(file_path)
        
        logs = self.get_logs(docker_container, stdout=stdout, stderr=stderr, timestamps=timestamps, tail=tail, since=since, until=until, wait_before_s=wait_before_s)
        
        if logs:
            # Build table
            table = PrettyTable(**self.__prettytable_kwargs)
            table.field_names = self._define_field_names_for_logs(logs)
            for log in logs:
                table.add_row(self._get_log_fields_values(table.field_names, log))
            
            # Output table as string
            table.set_style(TableStyle.ORGMODE)
            table.align = 'l'
            table.hrules = prettytable.NONE
            table_str = table.get_string()
            
            with File(file_path, mode='wt') as fout:
                fout.write(table_str)
                fout.write('\n')
            
            res = len(logs)
            logger.info(f"Saved {res} logs for container '{docker_container.container.name}' in file '{file_path}'")
        
        return res

class CsvDockerContainerLogsSaver(DockerContainerLogsSaver):
    """Saver of docker container logs in a CSV file.
    """
    def __init__(self, timestamps_field_name=default_value, include_patterns=None, exclude_patterns=None, include_others_name=default_value, formatter=None, **csv_kwargs):
        """ Constructor
        @param timestamps_field_name: field name of timestamps if they are added to logs
        @param include_patterns: patterns of log fields to include
        @param exclude_patterns: patterns of log fields to exclude
        @param include_others_name: if defined, all fields not included and not excluded are grouped in this field name (used only if include_patterns is defined)
        @param formatter: formatter to use (if defined, previous fields are omitted)
        @param csv_kwargs: all additional kwargs are used as csv.DictWriter additional parameters
        """
        super().__init__(timestamps_field_name=timestamps_field_name, include_patterns=include_patterns, exclude_patterns=exclude_patterns, include_others_name=include_others_name, formatter=formatter)
        self.__csv_kwargs = csv_kwargs
        
    def __get_log_row(self, field_names, log):
        res = []
        
        for name in field_names:
            if name in log:
                res.append(log[name])
            else:
                res.append('')
        
        return res
    
    def save_logs(self, docker_container, full_file_name, stdout=True, stderr=True, timestamps=True, tail='all', since=None, until=None, wait_before_s=0.1):
        import csv
        
        res = None
        
        file_path = f"{full_file_name}.csv"
        SessionContext.instance().path_manager.makedirs(file_path)
        
        logs = self.get_logs(docker_container, stdout=stdout, stderr=stderr, timestamps=timestamps, tail=tail, since=since, until=until, wait_before_s=wait_before_s)
        
        if logs:
            field_names = self._define_field_names_for_logs(logs)
            
            with File(file_path, mode='wt') as fout:
                dw = csv.DictWriter(fout, fieldnames=field_names, **self.__csv_kwargs)
                
                dw.writeheader()
                for log in logs:
                    dw.writerow(log)
            
            res = len(logs)
            logger.info(f"Saved {res} logs for container '{docker_container.container.name}' in file '{file_path}'")
        
        return res



class DockerContainersLogsSaver():
    """Saver of logs for a group of containers
    """
    def __init__(self, docker_client, container_logs_saver=default_value, include_patterns=None, exclude_patterns=None):
        self.__docker_client = docker_client
        self.__container_logs_saver = container_logs_saver if container_logs_saver is not default_value else JsonDockerContainerLogsSaver()
        self.__include_patterns = [ip if isinstance(ip, re.Pattern) else re.compile(ip) for ip in include_patterns] if include_patterns is not None else None
        self.__exclude_patterns = [ep if isinstance(ep, re.Pattern) else re.compile(ep) for ep in exclude_patterns] if exclude_patterns is not None else None
        
    def save_containers_logs(self, destination_path, stdout=True, stderr=True, timestamps=True, tail='all', since=None, until=None, wait_before_s=0.1):
        """ Save containers logs
        @return: number of containers for which logs have been saved
        """
        res = 0
        has_waited = False  # Manage to wait only on first container
        
        names = self.__docker_client.get_container_names(in_list=True, all_=True, sparse=True, include_patterns=self.__include_patterns, exclude_patterns=self.__exclude_patterns)
        for name in names:
            container = self.__docker_client.get_container(name, all_=True, reset_if_removed=False)
            full_file_name = os.path.join(destination_path, name)
            nb_logs = self.__container_logs_saver.save_logs(container, full_file_name, stdout=stdout, stderr=stderr, timestamps=timestamps, tail=tail, since=since, until=until, wait_before_s=wait_before_s if not has_waited else None)
            has_waited = True
            
            if nb_logs is not None:
                res += 1
        
        return res

