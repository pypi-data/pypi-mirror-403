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
import logging
from holado_docker.sdk.docker.container_logs import JsonDockerContainerLogsFormatter

logger = logging.getLogger(__name__)



def _get_session_context():
    return SessionContext.instance()

class ContainerView(MethodView):
    
    def get(self, name=None, all_=False, limit=100):
        try:
            _get_session_context().docker_client.update_containers(all_=all_)
            if name is not None:
                if not _get_session_context().docker_client.has_container(name, in_list=False, all_=all_, reset_if_removed=False):
                    if all_:
                        return f"Container '{name}' doesn't exist", 406
                    else:
                        return f"Container '{name}' is not running (try with '?all=true' to get information on existing but not running containers)", 406
                
                cont = _get_session_context().docker_client.get_container(name, all_=all_)
                res = cont.information
            else:
                names = _get_session_context().docker_client.get_container_names(in_list=False, all_=all_)
                res = [{'name':n, 'status':_get_session_context().docker_client.get_container(n, all_=all_).status} for n in names]
            return res
        except Exception as exc:
            if name is not None:
                msg = f"Failed to get information of container '{name}'"
            else:
                msg = f"Failed to get information of all containers"
            logger.exception(msg)
            return str(exc), 500

class LogsView(MethodView):
    
    def get(self, name, body: dict):
        try:
            with_timestamps = body.get('with_timestamps', True)
            since = body.get('since', None)
            until = body.get('until', None)
            
            container = _get_session_context().docker_client.get_container(name, all_=True, reset_if_removed=False)
            res = container.get_logs(timestamps=with_timestamps, since=since, until=until, 
                                     formatter=JsonDockerContainerLogsFormatter())
            
            return res
        except Exception as exc:
            logger.exception(f"Failed to get logs of container '{name}'")
            return str(exc), 500
