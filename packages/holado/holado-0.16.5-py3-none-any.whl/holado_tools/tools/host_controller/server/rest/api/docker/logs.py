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

from flask.views import MethodView
from holado.common.context.session_context import SessionContext
from holado_docker.sdk.docker.container_logs import DockerContainersLogsSaver,\
    PrettyTableDockerContainerLogsSaver, JsonDockerContainerLogsSaver,\
    CsvDockerContainerLogsSaver
import logging
from holado.common.handlers.undefined import default_value


logger = logging.getLogger(__name__)


def _get_session_context():
    return SessionContext.instance()


class SaveView(MethodView):
    
    def put(self, body: dict):
        logger.info(f"Saving container logs with parameters: {body}")
        try:
            destination_path = body['destination_path']
            file_format = body.get('file_format', 'JSON')
            container_include_patterns = body.get('container_include_patterns', None)
            container_exclude_patterns = body.get('container_exclude_patterns', None)
            with_timestamps = body.get('with_timestamps', True)
            timestamps_field_name = body.get('timestamps_field_name', default_value if with_timestamps else None)
            field_include_patterns = body.get('field_include_patterns', None)
            field_exclude_patterns = body.get('field_exclude_patterns', None)
            field_include_others_name = body.get('field_include_others_name', default_value)
            since = body.get('since', None)
            until = body.get('until', None)
            
            if file_format == 'CSV':
                container_saver = CsvDockerContainerLogsSaver(timestamps_field_name, field_include_patterns, field_exclude_patterns, field_include_others_name)
            elif file_format == 'JSON':
                container_saver = JsonDockerContainerLogsSaver(timestamps_field_name, field_include_patterns, field_exclude_patterns, field_include_others_name)
            elif file_format == 'PrettyTable':
                container_saver = PrettyTableDockerContainerLogsSaver(timestamps_field_name, field_include_patterns, field_exclude_patterns, field_include_others_name)
            else:
                return f"Unexpected file format '{file_format}' (possible formats: 'CSV', 'JSON', 'PrettyTable')", 406
            
            saver = DockerContainersLogsSaver(_get_session_context().docker_client, 
                                              container_logs_saver = container_saver,
                                              include_patterns=container_include_patterns,
                                              exclude_patterns=container_exclude_patterns)
            res = saver.save_containers_logs(destination_path, timestamps=with_timestamps, since=since, until=until)
            
            return res
        except Exception as exc:
            logger.exception(f"Failed to save logs (parameters: {body})")
            return str(exc), 500

    
