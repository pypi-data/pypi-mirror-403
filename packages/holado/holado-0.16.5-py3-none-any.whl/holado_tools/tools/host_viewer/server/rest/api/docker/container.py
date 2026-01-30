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
from holado.common.handlers.undefined import default_value
import logging


logger = logging.getLogger(__name__)


def _get_session_context():
    return SessionContext.instance()


class StatusView(MethodView):
    
    def get(self, name, all_=False):
        try:
            cont = _get_session_context().docker_client.get_container(name, all_=all_, reset_if_removed=False)
            if cont:
                return cont.status
            else:
                return
        except Exception as exc:
            logger.exception(f"Failed to get status of container '{name}'")
            return str(exc), 500

class HealthStatusView(MethodView):
    
    def get(self, name, all_=False):
        try:
            cont = _get_session_context().docker_client.get_container(name, all_=all_, reset_if_removed=False)
            if cont:
                return cont.health_status
            else:
                return
        except Exception as exc:
            logger.exception(f"Failed to get health status of container '{name}'")
            return str(exc), 500




class AwaitStartedView(MethodView):
    
    def put(self, name, timeout=default_value):
        try:
            _get_session_context().docker_client.await_container_exists(name, timeout=timeout)
            return _get_session_context().docker_client.get_container(name).await_started(timeout=timeout)()
        except Exception as exc:
            logger.exception(f"Failed to await container '{name}' is started")
            return str(exc), 500
    
class AwaitStatusView(MethodView):
    
    def put(self, name, status, timeout=default_value):
        try:
            _get_session_context().docker_client.await_container_exists(name, timeout=timeout)
            return _get_session_context().docker_client.get_container(name).await_status(status, timeout=timeout)()
        except Exception as exc:
            logger.exception(f"Failed to await container '{name}' has status '{status}'")
            return str(exc), 500
    
class AwaitHealthStatusView(MethodView):
    
    def put(self, name, status, timeout=default_value):
        try:
            _get_session_context().docker_client.await_container_exists(name, timeout=timeout)
            return _get_session_context().docker_client.get_container(name).await_health_status(status, timeout=timeout)()
        except Exception as exc:
            logger.exception(f"Failed to await container '{name}' has health status '{status}'")
            return str(exc), 500




