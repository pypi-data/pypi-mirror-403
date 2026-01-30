from builtins import super
import logging
from holado_test.common.context.test_session_context import BehaveSessionContext

logger = logging.getLogger(__name__)


class TSSessionContext(BehaveSessionContext):
    
    def __init__(self):
        super().__init__("TSSession")
        
    def configure(self, session_kwargs=None):
        logger.info("Configuring TSSessionContext")
        
        super().configure(session_kwargs)
        
        # Override default registered modules
         
        from common.tools.path_manager import TSPathManager  # @UnresolvedImport
        self.services.register_service_type("path_manager", TSPathManager,
                            lambda m: m.initialize(),
                            raise_if_exist=False )
        
        
        # Register new modules
        
        from config.config_manager import TSConfigManager  # @UnresolvedImport
        self.services.register_service_type("config_manager", TSConfigManager,
                            lambda m: m.initialize(lambda: self.path_manager) )
        
        
    def initialize(self, session_kwargs=None):
        if session_kwargs is None:
            session_kwargs = {}
        raise_if_not_exist = session_kwargs.get("raise_if_not_exist", True)
        
        # Call default initialization
        super().initialize(session_kwargs)
        
        # Initialize testing solution
        
        
        
        
