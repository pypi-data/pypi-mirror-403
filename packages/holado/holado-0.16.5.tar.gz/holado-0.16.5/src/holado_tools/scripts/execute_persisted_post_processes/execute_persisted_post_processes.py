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

# Uncomment next lines to insert holado sources when using a clone of holado project rather than holado package 
# from initialize_holado import insert_holado_source_paths  # @UnresolvedImport
# insert_holado_source_paths()

# Initialize HolAdo
from holado import initialize_for_script
initialize_for_script(TSessionContext=None, use_holado_logger=True, logging_config_file_path=None,
                      log_level=logging.WARNING, log_time_in_utc=None, log_on_console=True, log_in_file=False,
                      config_kwargs={'application_group':'configuration'},
                      garbage_collector_periodicity=None)

# Script content
from holado.common.context.session_context import SessionContext
from holado_core.common.resource.persisted_method_to_call_manager import PersistedMethodToCallManager
from holado.common.handlers.undefined import any_value

persisted_method_to_call_manager = PersistedMethodToCallManager(scope_name=any_value)
persisted_method_to_call_manager.initialize(SessionContext.instance().resource_manager, SessionContext.instance().expression_evaluator)
if persisted_method_to_call_manager.does_persistent_db_exist():
    persisted_method_to_call_manager.call_functions_and_methods(use="post_process")


