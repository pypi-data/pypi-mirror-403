
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

from builtins import super
import logging
import os.path
from holado.common.context.context import Context
import threading
from holado.common.handlers.enums import ObjectStates
from holado.holado_config import Config
import importlib


logger = logging

def initialize_logger():
    global logger
    logger = logging.getLogger(__name__)


class SessionContext(Context):
    TSessionContext = None
    
    # Singleton management
    __instance = None
    __is_resetting_instance = False
    
    @staticmethod
    def instance() -> TSessionContext:
        # Note: If session context istance is under reset, consider it is already None
        if SessionContext.__is_resetting_instance:
            return None
        
        if SessionContext.__instance is None:
            # If needed, import session context module, and replace TSessionContext string by its class type
            if isinstance(SessionContext.TSessionContext, str):
                module_name, class_type = SessionContext.TSessionContext.rsplit('.', maxsplit=1)
                module = importlib.import_module(module_name)
                SessionContext.TSessionContext = getattr(module, class_type)
            
            # Create instance
            SessionContext.__instance = SessionContext.TSessionContext()
            logger.debug(f"Created session context of type {SessionContext.TSessionContext}")
            # logging.log(45, f"Created session context of type {SessionContext.TSessionContext}")
            # import traceback
            # logging.log(45, "".join(traceback.format_list(traceback.extract_stack())))
        return SessionContext.__instance
    
    @staticmethod
    def has_instance() -> bool:
        if SessionContext.__is_resetting_instance:
            return False
        else:
            return SessionContext.__instance is not None
    
    @staticmethod
    def _reset_instance():
        if SessionContext.__instance is not None:
            logger.debug(f"Resetting session context")
            SessionContext.__is_resetting_instance = True
            SessionContext.__instance = None
            SessionContext.__is_resetting_instance = False
            logger.debug(f"Reset of session context")
    
    def __init__(self, name="Session"):
        super().__init__(name, with_post_process=True)
        
        self.__with_session_path = None
        
        from holado.common.context.service_manager import ServiceManager
        self.__service_manager = ServiceManager(type(self))
        
        # Manage multitasking
        self.__multitask_lock = threading.RLock()
        
    def __del__(self):
        # Note: Override Object.__del__ since it supposes that SessionContext is initialized, whereas SessionContext is deleting
        try:
            if self.object_state in [ObjectStates.Deleting, ObjectStates.Deleted]:
                return
            
            self.delete_object()
        except Exception as exc:
            if "Python is likely shutting down" in str(exc):
                # Simply return
                return
            else:
                raise exc
    
    @property
    def _multitask_lock(self):
        return self.__multitask_lock
    
    def _delete_object(self):
        # if Tools.do_log(logger, logging.DEBUG):
        #     logger.debug("Interrupting and unregistering all threads for scenario [{}]".format(scenario.name))
        if self.has_threads_manager:
            logger.info(f"Delete session context - Interrupting and unregistering all threads...")
            self.threads_manager.interrupt_all_threads(scope="Session")
            self.threads_manager.unregister_all_threads(scope="Session", keep_alive=False)
        
        # Delete session context
        logger.info(f"Delete session context - Deleting context objects...")
        super()._delete_object()
        
    def configure(self, session_kwargs=None):
        """
        Override this method to configure the session context before new session creation.
        It is usually used to register new services.
        """
        if session_kwargs is None:
            session_kwargs = {}
            
        self.__with_session_path = session_kwargs.get("with_session_path", True)
        
        # Create this thread context
        self.multitask_manager.get_thread_context()
    
    def initialize(self, session_kwargs=None):
        """
        Override this method to initialize the session context after its configuration and new session creation.
        """
        pass
        
    @property
    def services(self):
        return self.__service_manager
    
    @property
    def with_session_path(self):
        return self.__with_session_path
    
    def get_object_getter_eval_string(self, obj, raise_not_found=True):
        from holado_python.standard_library.typing import Typing
        
        name = self.get_object_name(obj)
        if name is not None:
            if self.__service_manager.has_service(name):
                return f"{Typing.get_object_class_fullname(self)}.instance().{name}"
            else:
                return f"{Typing.get_object_class_fullname(self)}.instance().get_object('{name}')"
        
        if raise_not_found:
            from holado_core.common.exceptions.element_exception import ElementNotFoundException
            raise ElementNotFoundException(f"[{self.name}] Failed to find object of id {id(obj)}")
        else:
            return None

    def new_session(self, session_kwargs=None):
        from holado_python.common.tools.datetime import DateTime
        
        # Report session
        report_path = None
        if self.with_session_path:
            # Create new report path for this session
            name = "session_{}".format(DateTime.now(tz=Config.report_timezone).strftime("%Y-%m-%d_%H-%M-%S"))  # @UndefinedVariable
            report_path = self.path_manager.get_reports_path(name)
            logger.info(f"Reports location: {report_path}")
            print(f"Reports location: {report_path}")
        self.report_manager.new_session(report_path)
            
        # Logging configuration
        if self.with_session_path and SessionContext.instance().log_manager.in_file:
            log_filename = os.path.join(report_path, "logs", "report.log")
            self.path_manager.makedirs(log_filename)
            SessionContext.instance().log_manager.set_root_log_file(log_filename)
            SessionContext.instance().log_manager.set_config()
    


SessionContext.TSessionContext = SessionContext


