
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
from holado_rest.api.rest.rest_client import RestClient
from holado.common.handlers.undefined import undefined_argument, undefined_value, default,\
    default_value
import os
from holado_core.common.tools.converters.converter import Converter
from holado_rest.api.rest.rest_manager import RestManager
from holado_core.common.handlers.wait import WaitFuncResult
from datetime import datetime
from holado_python.common.tools.datetime import DateTime

logger = logging.getLogger(__name__)


class HostControllerClient(RestClient):
    
    @classmethod
    def new_client(cls, use_localhost=undefined_argument, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = None
        if 'url' not in kwargs:
            if use_localhost is undefined_argument:
                env_use = os.getenv("HOLADO_USE_LOCALHOST", False)
                use_localhost = Converter.is_boolean(env_use) and Converter.to_boolean(env_use)
            
            url = os.getenv("HOLADO_HOST_CONTROLLER_URL", undefined_value)
            if url is undefined_value:
                scheme = kwargs.get('scheme', undefined_value)
                if scheme is undefined_value:
                    scheme = os.getenv("HOLADO_HOST_CONTROLLER_SCHEME", "http")
                host = kwargs.get('host', undefined_value)
                if host is undefined_value:
                    host = "localhost" if use_localhost else os.getenv("HOLADO_HOST_CONTROLLER_HOST", "holado_host_controller")
                port = kwargs.get('port', undefined_value)
                if port is undefined_value:
                    if use_localhost:
                        port = os.getenv("HOLADO_HOST_CONTROLLER_HOSTPORT", 51231)
                    else:
                        port = os.getenv("HOLADO_HOST_CONTROLLER_PORT", 51231)
                
                if port is None:
                    url = f"{scheme}://{host}"
                else:
                    url = f"{scheme}://{host}:{port}"
            kwargs['url'] = url
        
        manager = RestManager(default_client_class=HostControllerClient)
        res = manager.new_client(**kwargs)
        
        return res

    
    def __init__(self, name, url, headers=None):
        super().__init__(name, url, headers)
    
    
    # Monitoring of host-controller
    
    def is_healthy(self):
        try:
            response = self.get(f"health")
            return response.status_code == 200
        except:
            return False
    
    def wait_is_healthy(self, timeout_sec=300, do_raise_on_timeout=True):
        logger.info(f"Waiting for host-controller ({self.url}) to be healthy...")
        wait_context = WaitFuncResult(f"wait host-controller is healthy", self.is_healthy)
        wait_context.with_timeout(timeout_sec) \
                    .with_raise_on_timeout(do_raise_on_timeout) \
                    .with_process_in_thread(False) \
                    .redo_until(True)
        try:
            wait_context.execute()
        except Exception as exc:
            logger.error(f"Error while waiting for host-controller ({self.url}) to be healthy: {str(exc)}")
            raise
        else:
            logger.info(f"host-controller ({self.url}) is healthy")
    
    
    # Common features
    
    def get_environment_variable_value(self, var_name):
        data = [var_name]
        response = self.get(f"os/env", json=data)
        return self.response_result(response, status_ok=[200])
    
    def get_directory_filenames(self, path, extension='.yml'):
        data = {'path':path, 'extension':extension}
        response = self.get(f"os/ls", json=data)
        return self.response_result(response, status_ok=[200])
    
    
    # Manage containers
    
    def get_containers_status(self, all_=False):
        if all_:
            response = self.get("docker/container?all=true")
        else:
            response = self.get("docker/container")
        return self.response_result(response, status_ok=[200,204])
    
    def get_container_info(self, name, all_=False):
        """Get container info
        @return container info if found, else None
        """
        if all_:
            response = self.get(f"docker/container/{name}?all=true")
        else:
            response = self.get(f"docker/container/{name}")
        return self.response_result(response, status_ok=[200,204], result_on_statuses={204:None, default:None})
    
    def get_container_status(self, name, all_=False):
        """Get container status
        @return container status if found, else None
        """
        if all_:
            response = self.get(f"docker/container/{name}/status?all=true")
        else:
            response = self.get(f"docker/container/{name}/status")
        return self.response_result(response, status_ok=[200,204], result_on_statuses={204:None, default:None})
    
    def get_container_health_status(self, name, all_=False):
        """Get container health status
        @return container health status if found, else None
        """
        if all_:
            response = self.get(f"docker/container/{name}/health_status?all=true")
        else:
            response = self.get(f"docker/container/{name}/health_status")
        return self.response_result(response, status_ok=[200,204], result_on_statuses={204:None, default:None})
    
    def restart_container(self, name, wait_started=True, timeout=default_value, start_if_gone=False):
        response = self.put(f"docker/container/{name}/restart?wait_started={'true' if wait_started else 'false'}{f'&timeout={timeout}' if timeout is not default_value else ''}")
        if start_if_gone and response.status_code == 410:
            return self.start_container(name)
        else:
            return self.response_result(response, status_ok=[200,204])
    
    def start_container(self, name, wait_started=True, timeout=default_value):
        response = self.put(f"docker/container/{name}/start?wait_started={'true' if wait_started else 'false'}{f'&timeout={timeout}' if timeout is not default_value else ''}")
        return self.response_result(response, status_ok=[200,204])
    
    def stop_container(self, name, wait_stopped=True, timeout=default_value, raise_if_gone=True):
        response = self.put(f"docker/container/{name}/stop?wait_stopped={'true' if wait_stopped else 'false'}{f'&timeout={timeout}' if timeout is not default_value else ''}")
        if not raise_if_gone and response.status_code == 410:
            return None
        else:
            return self.response_result(response, status_ok=[200,204])
    
    def wait_container(self, name, timeout=default_value, raise_if_gone=True):
        response = self.put(f"docker/container/{name}/wait{f'?timeout={timeout}' if timeout is not default_value else ''}")
        if not raise_if_gone and response.status_code == 410:
            return None
        else:
            return self.response_result(response, status_ok=[200,204])
    
    def await_container_is_started(self, name, timeout=default_value):
        if isinstance(timeout, int):
            response = self.put(f"docker/container/{name}/await_started?timeout={timeout}")
        else:
            response = self.put(f"docker/container/{name}/await_started")
        return self.response_result(response, status_ok=[200,204])
    
    def await_container_status(self, name, status='running', timeout=default_value):
        if isinstance(timeout, int):
            response = self.put(f"docker/container/{name}/await_status?status={status}&timeout={timeout}")
        else:
            response = self.put(f"docker/container/{name}/await_status?status={status}")
        return self.response_result(response, status_ok=[200,204])
    
    def await_container_health_status(self, name, status='healthy', timeout=default_value):
        if isinstance(timeout, int):
            response = self.put(f"docker/container/{name}/await_health_status?status={status}&timeout={timeout}")
        else:
            response = self.put(f"docker/container/{name}/await_health_status?status={status}")
        return self.response_result(response, status_ok=[200,204])
    
    
    # Manage logs
    
    def get_container_logs(self, name, with_timestamps=True, since=undefined_argument, until=undefined_argument):
        data = {}
        if with_timestamps is not None:
            data['with_timestamps'] = with_timestamps
        if since not in [undefined_argument, None]:
            if isinstance(since, datetime):
                since = DateTime.datetime_2_str(since)
            data['since'] = since
        if until not in [undefined_argument, None]:
            if isinstance(until, datetime):
                until = DateTime.datetime_2_str(until)
            data['until'] = until
        
        response = self.get(f"docker/logs/{name}", json=data)
        return self.response_result(response, status_ok=[200,204], result_on_statuses={204:[], default:None})
    
    def save_containers_logs(self, destination_path, file_format=default_value,
                  container_include_patterns=undefined_argument, container_exclude_patterns=undefined_argument,
                  field_include_patterns=undefined_argument, field_exclude_patterns=undefined_argument, field_include_others_name=default_value, 
                  with_timestamps=True, timestamps_field_name=default_value, since=undefined_argument, until=undefined_argument):
        data = {'destination_path':destination_path}
        if file_format not in [default_value, None]:
            data['file_format'] = file_format
        if container_include_patterns not in [undefined_argument, None]:
            data['container_include_patterns'] = container_include_patterns
        if container_exclude_patterns not in [undefined_argument, None]:
            data['container_exclude_patterns'] = container_exclude_patterns
        if field_include_patterns not in [undefined_argument, None]:
            data['field_include_patterns'] = field_include_patterns
        if field_exclude_patterns not in [undefined_argument, None]:
            data['field_exclude_patterns'] = field_exclude_patterns
        if field_include_others_name not in [default_value, None]:
            data['field_include_others_name'] = field_include_others_name
        if with_timestamps is not None:
            data['with_timestamps'] = with_timestamps
        if timestamps_field_name and timestamps_field_name is not default_value:
            data['timestamps_field_name'] = timestamps_field_name
        if since not in [undefined_argument, None]:
            if isinstance(since, datetime):
                since = DateTime.datetime_2_str(since)
            data['since'] = since
        if until not in [undefined_argument, None]:
            if isinstance(until, datetime):
                until = DateTime.datetime_2_str(until)
            data['until'] = until
        
        response = self.put(f"docker/logs/save", json=data)
        return self.response_result(response, status_ok=[200,204], result_on_statuses={204:None, default:None})
    
    
    # Manage configuration
    
    def get_yaml_file_content(self, file_path, field_keys=None):
        data = {'file_path': file_path}
        if field_keys:
            data['field_keys'] = field_keys
        response = self.get(f"config/yaml_file", json=data)
        return self.response_result(response, status_ok=[200,204])
    
    def update_yaml_file(self, file_path, text, with_backup=True, backup_extension='.ha_bak'):
        data = {
            'file_path': file_path,
            'yaml_string': text,
            'with_backup': with_backup,
            'backup_extension': backup_extension
            }
        response = self.patch(f"config/yaml_file", json=data)
        return self.response_result(response, status_ok=[200,204])
    
    def restore_yaml_file(self, file_path, backup_extension='.ha_bak'):
        data = {
            'action': 'restore',
            'file_path': file_path,
            'backup_extension': backup_extension
            }
        response = self.put(f"config/yaml_file", json=data)
        return self.response_result(response, status_ok=[200,204])
    
    
    
