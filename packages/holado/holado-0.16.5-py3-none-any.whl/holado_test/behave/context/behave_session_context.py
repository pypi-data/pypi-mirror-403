
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
from holado_core.common.tools.tools import Tools
from holado.common.context.session_context import SessionContext
import threading
from holado_test.test_config import TestConfig

logger = logging.getLogger(__name__)


class BehaveSessionContext(SessionContext):
    
    def __init__(self, name="Session"):
        super().__init__(name)
        
        self.__multitask_step_lock = threading.RLock()
    
    def before_all(self, behave_context):
        log_prefix = f"[Before session] "
        
        with self._multitask_lock:
            self.behave_manager.set_main_context(behave_context)
            self.report_manager.before_all()
        
        # Set variable with session context instance
        self.variable_manager.register_variable("SESSION_CONTEXT", self)
        
        logger.info(f"{log_prefix}Doing all post processes of a previous session if needed...")
        self.do_all_persisted_post_processes()
        
        # Abort execution if SUT is not operational
        # Note: it must be done after post processes, since a post process can restore SUT
        self.manage_execution_abort()
        
        
    def after_all(self):
        log_prefix = f"[After session] "
            
        # Post processes
        logger.info(f"{log_prefix}Post processing...")
        self.do_post_processes()
        
        with self._multitask_lock:
            self.report_manager.after_all()
            self.behave_manager.clear()

    def before_feature(self, feature):
        from holado_system.system.global_system import GlobalSystem
        from holado_helper.debug.memory.memory_profiler import MemoryProfiler
        from holado_test.common.context.feature_context import FeatureContext
        
        if self.behave_manager.is_execution_aborted():
            return
        
        log_prefix = f"[Before feature '{feature.name}'] "
        
        with self._multitask_lock:
            # Logs
            logger.info("="*150)
            logger.info(f"Feature [{feature.name}]")
            
            logger.info(f"{log_prefix}Begin")
            if self.has_feature_context(is_reference=True):
                from holado_core.common.exceptions.technical_exception import TechnicalException
                raise TechnicalException(f"{log_prefix}A feature context is already defined")
            
            GlobalSystem.log_resource_usage(prefix=log_prefix, level=logging.INFO, logger_=logger)
            if TestConfig.profile_memory_in_features and MemoryProfiler.is_tracker_available():
                MemoryProfiler.create_or_reset_tracker_of_objects_summary_changes("features summary")
                # MemoryProfiler.create_or_reset_tracker_of_objects_changes("features objects")
                
            # Feature context
            feature_context = FeatureContext(feature)
            self.__set_feature_context(feature_context)
            
            # Set variable with feature context instance
            self.variable_manager.register_variable("FEATURE_CONTEXT", feature_context)
            
            # Report
            try:
                self.report_manager.before_feature(feature_context, feature)
            except:
                logger.exception(f"{log_prefix}Error while updating report before feature")
            
            logger.info(f"{log_prefix}End")
        
    def after_feature(self, feature):
        from holado_system.system.global_system import GlobalSystem
        from holado_helper.debug.memory.memory_profiler import MemoryProfiler
        
        if self.behave_manager.is_execution_aborted():
            return
        
        log_prefix = f"[After feature '{feature.name}'] "
        
        with self._multitask_lock:
            logger.info(f"{log_prefix}Begin")
            if not self.has_feature_context(is_reference=True):
                from holado_core.common.exceptions.technical_exception import TechnicalException
                raise TechnicalException(f"{log_prefix}No feature context is defined")
            
            if TestConfig.profile_memory_in_features and MemoryProfiler.is_tracker_available():
                MemoryProfiler.log_tracker_diff(name="features summary", prefix=log_prefix, level=logging.INFO, logger_=logger)  # @UndefinedVariable
                # MemoryProfiler.log_tracker_diff(name="features objects", prefix="[After feature] ", level=logging.INFO, logger_=logger)  # @UndefinedVariable
            GlobalSystem.log_resource_usage(prefix=log_prefix, level=logging.INFO, logger_=logger)
            
            # End feature context
            self.get_feature_context().end()
            
            # Report
            try:
                self.report_manager.after_feature(feature)
            except:
                logger.exception(f"{log_prefix}Error while updating report after feature")
            
            if Tools.do_log(logger, logging.DEBUG):
                logger.debug(f"{log_prefix}Deleting feature context")
            self.__delete_feature_context()
            
            logger.info(f"{log_prefix}End")
            logger.info(f"Finished feature [{feature.name}]")
        
    def has_feature_context(self, is_reference=None, do_log=False):
        return self.multitask_manager.has_feature_context(is_reference=is_reference, do_log=do_log)
    
    def get_feature_context(self):
        return self.multitask_manager.get_feature_context()
    
    def __set_feature_context(self, feature_context):
        return self.multitask_manager.set_feature_context(feature_context)
    
    def __delete_feature_context(self):
        return self.multitask_manager.delete_feature_context()
    
    def before_scenario(self, scenario):
        from holado_system.system.global_system import GlobalSystem
        from holado_helper.debug.memory.memory_profiler import MemoryProfiler
        from holado_test.common.context.scenario_context import ScenarioContext
        
        if self.behave_manager.is_execution_aborted():
            return
        
        log_prefix = f"[Before scenario '{scenario.name}'] "
        
        with self._multitask_lock:
            logger.info("-"*150)
            logger.info(f"Scenario [{scenario.name}]")
            
            logger.info(f"{log_prefix}Begin")
            if not self.has_feature_context(is_reference=True):
                from holado_core.common.exceptions.technical_exception import TechnicalException
                raise TechnicalException(f"{log_prefix}No feature context is defined")
            
            # Create and initialize ScenarioContext
            scenario_context = ScenarioContext(scenario)
            self.get_feature_context().add_scenario(scenario_context)
            
            # Report: create scenario report
            try:
                self.report_manager.before_scenario(scenario_context, scenario)
            except:
                logger.exception(f"{log_prefix}Error while updating report before scenario")
            
            # Set variable with scenario context instance
            # Note: must be after scenario report creation
            self.get_scenario_context().get_variable_manager().register_variable("SCENARIO_CONTEXT", self.get_scenario_context())
            
            # Behave context
            try:
                self.behave_manager.before_scenario()
            except:
                logger.exception(f"{log_prefix}Error while updating behave context before scenario")
            
            GlobalSystem.log_resource_usage(log_prefix, level=logging.INFO, logger_=logger)
            if TestConfig.profile_memory_in_scenarios and MemoryProfiler.is_tracker_available():
                MemoryProfiler.create_or_reset_tracker_of_objects_summary_changes("scenarios summary")
                # MemoryProfiler.create_or_reset_tracker_of_objects_changes("scenarios objects")
        
            logger.info(f"{log_prefix}Doing previous scenario post processes if needed...")
            self.get_scenario_context().do_persisted_post_processes()
            
            logger.info(f"{log_prefix}End")
            logger.info(f"Start scenario [{scenario.name}]")
        
    def get_SUT_status(self):
        """ Return if SUT is operational and error message
        Override it in a subclass to activate this feature.
        """
        return True, None
    
    def manage_execution_abort(self, scenario=None):
        """ Manage cases execution must be aborted for outside reasons.
        It uses the return of get_SUT_status to abort if SUT is not operational.
        """
        if TestConfig.manage_execution_abort:
            is_sut_ok, sut_error = self.get_SUT_status()
            if not is_sut_ok:
                if scenario:
                    scenario.sut_failed = True
                    scenario.sut_error = sut_error
                self.abort_execution(reason=f"SUT is not operational: {sut_error}")
    
    def abort_execution(self, reason):
        """ Abort execution.
        """
        self.behave_manager.abort_execution(reason=reason)
        
        # Logs
        logger.print(f"ABORT EXECUTION: {reason}")
        print(f"ABORT EXECUTION: {reason}")
        
        # Create abort report
        self.report_manager.report_abort(reason)
    
    def after_scenario(self, scenario):
        from holado_core.common.exceptions.technical_exception import TechnicalException
        from holado_system.system.global_system import GlobalSystem
        from holado_helper.debug.memory.memory_profiler import MemoryProfiler
        
        if self.behave_manager.is_execution_aborted():
            return
        
        log_prefix = f"[After scenario '{scenario.name}'] "
        
        with self._multitask_lock:
            # End scenario
            if not self.has_feature_context(is_reference=True):
                raise TechnicalException(f"{log_prefix}No feature context is defined")
            if not self.has_scenario_context(is_reference=True):
                raise TechnicalException(f"{log_prefix}No scenario context is defined")
            self.get_scenario_context().end()
            
            # Process actions at scenario end
            try:
                self.after_scenario_end(scenario)
            except:
                logger.exception(f"{log_prefix}Error while processing actions after scenario end")
            
            # Process after scenario
            logger.info(f"{log_prefix}Begin")
            # logger.printf"++++++++++++ scenario: {Tools.represent_object(scenario)}")
            
            logger.info(f"{log_prefix}Resource usage:")
            if TestConfig.profile_memory_in_scenarios and MemoryProfiler.is_tracker_available():
                MemoryProfiler.log_tracker_diff(name="scenarios summary", prefix=log_prefix, level=logging.INFO, logger_=logger)  # @UndefinedVariable
                # MemoryProfiler.log_tracker_diff(name="scenarios objects", prefix="[After scenario] ", level=logging.INFO, logger_=logger)  # @UndefinedVariable
            GlobalSystem.log_resource_usage(prefix=log_prefix, level=logging.INFO, logger_=logger)
            
            # Post processes
            logger.info(f"{log_prefix}Post processing...")
            self.get_scenario_context().scope_manager.reset_scope_level()
            self.get_scenario_context().do_post_processes()
            
            # Abort execution if SUT has fall not operational during scenario
            # Note: it must be done after post processes (a post process can restore SUT) and before reports generation (to manage status 'Failed in SUT' in reports)
            self.manage_execution_abort(scenario)
            
            # Report
            logger.info(f"{log_prefix}Generating reports...")
            try:
                self.report_manager.after_scenario(scenario)
            except:
                logger.exception(f"{log_prefix}Error while updating report after scenario")
            
            # Delete scenario context
            logger.info(f"{log_prefix}Deleting scenario context...")
            # if Tools.do_log(logger, logging.DEBUG):
            #     logger.debug("Deleting context of scenario [{}]".format(scenario.name))
            self.__delete_scenario_context()
            
            # Remove all threads
            logger.info(f"{log_prefix}Interrupting and unregistering all threads...")
            # if Tools.do_log(logger, logging.DEBUG):
            #     logger.debug("Interrupting and unregistering all threads for scenario [{}]".format(scenario.name))
            #TODO: For case of multiple scenarios launched in parallel, interrupt only threads related to current scenario (scenario launched by this thread)
            self.threads_manager.interrupt_all_threads(scope="Scenario")
            self.threads_manager.unregister_all_threads(scope="Scenario", keep_alive=False)
            
            logger.info(f"{log_prefix}End")
            logger.info(f"Finished scenario [{scenario.name}]")
    
    def after_scenario_end(self, scenario):
        from holado_test.behave.scenario.behave_step_tools import BehaveStepTools
        from holado_test.common.context.context_tools import ContextTools
        from holado_test.behave.scenario.behave_scenario_tools import BehaveScenarioTools
        
        # Log error on failing scenario
        status_info = BehaveScenarioTools.get_current_scenario_status_info(scenario)
        has_failed = status_info.validation_status != "Passed"
        if has_failed:
            msg_list = []
            category_str = f" => {status_info.validation_category}" if status_info.validation_category else ""
            msg_list.append(f"Scenario {status_info.validation_status}{category_str}: {ContextTools.format_context_period(status_info.scenario_context)} {BehaveScenarioTools.format_scenario_short_description(scenario)} - {BehaveStepTools.format_step_short_description(status_info.step_failed, status_info.step_failed_nb, step_context=status_info.step_context, dt_ref=status_info.scenario_context.start_datetime, has_failed=has_failed)}")
            step_error_message = BehaveStepTools.get_step_error_message(status_info.step_failed)
            if step_error_message:
                msg_list.append(step_error_message)
            msg = "\n".join(msg_list)
            logger.error(msg)
    
    def has_scenario_context(self, is_reference=None):
        return self.has_feature_context(is_reference=is_reference) and self.get_feature_context().has_scenario
    
    def get_scenario_context(self):
        return self.get_feature_context().current_scenario
    
    def __delete_scenario_context(self):
        self.get_scenario_context().delete_object()
        
    def before_step(self, step):
        log_prefix = f"[Before step '{step}'] "
        
        with self.__multitask_step_lock:
            from holado_test.behave.context.behave_step_context import BehaveStepContext
            from holado_core.common.exceptions.technical_exception import TechnicalException
            
            if not self.has_feature_context(is_reference=None):
                # Look again but do logs before raising exception
                self.has_feature_context(is_reference=None, do_log=True)
                raise TechnicalException(f"{log_prefix}No feature context is defined (step: {step})")
            if not self.has_scenario_context(is_reference=None):
                raise TechnicalException(f"{log_prefix}No scenario context is defined (step: {step})")
            scenario_context = self.get_scenario_context()
            
            # Manage step context
            step_context = BehaveStepContext(step)
            scenario_context.scope_manager.set_step_context(step_context)
            
            # Update scenario context
            step_level = scenario_context.scope_manager.scope_level("steps")
            if step_level == 0:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"{log_prefix}Add step {step_context} in scenario {scenario_context}")
                scenario_context.add_step(step_context)
            
            # Manage scope in define
            if scenario_context.block_manager.is_in_define \
                    and (scenario_context.block_manager.is_in_sub_define         # needed to add in define the "end define" steps of sub-define \
                         or step.name not in ["end for", "end while", "end function"]):     # needed to not add in define the "end define" steps of current define
                from holado_test.behave.behave import format_step
                step_str = format_step(step)
                scenario_context.block_manager.scope_in_define.add_steps(step_str)
                
                # Set step status
                step_context.status = "defined"
            
            # Report
            try:
                self.report_manager.before_step(step_context, step, step_level)
            except:
                logger.exception(f"{log_prefix}Error while updating report before step")
    
    def after_step(self, step, has_started=True):
        """Process after step
        @param step: step instance
        @param has_started: if False, the step is added but without execution. 
            It is usually True and before_step was called before, except for undefined and skipped steps.
        """
        log_prefix = f"[After step '{step}'] "
        
        with self.__multitask_step_lock:
            from holado_test.common.context.step_context import StepContext
            from holado_core.common.exceptions.technical_exception import TechnicalException
            
            if not self.has_feature_context(is_reference=None):
                raise TechnicalException(f"{log_prefix}No feature context is defined (step: {step})")
            if not self.has_scenario_context(is_reference=None):
                raise TechnicalException(f"{log_prefix}No scenario context is defined (step: {step})")
            scenario_context = self.get_scenario_context()
            
            # Manage step context
            if has_started:
                step_context = scenario_context.scope_manager.get_step_context()
                step_context.end()
                if step_context.status is None:
                    step_context.status = step.status.name
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"{log_prefix}Ended step {step_context} in scenario {scenario_context}")
            else:
                # Manage step context
                step_context = StepContext(step, do_start=False)
                scenario_context.scope_manager.set_step_context(step_context)
                
                # Update scenario context
                step_level = scenario_context.scope_manager.scope_level("steps")
                if step_level == 0:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"{log_prefix}Add step {step_context} in scenario {scenario_context}")
                    scenario_context.add_step(step_context)
                
                # Process before step in reports
                try:
                    self.report_manager.before_step(step_context, step, step_level)
                except:
                    logger.exception(f"{log_prefix}Error while updating report before step for unstarted step")
            
            # Report
            try:
                step_level = scenario_context.scope_manager.scope_level("steps")
                self.report_manager.after_step(step_context, step, step_level)
            except:
                logger.exception(f"{log_prefix}Error while updating report after step")
    
    def has_step_context(self):
        return self.has_feature_context() and self.get_feature_context().has_scenario and self.get_scenario_context().has_step()
    
    def get_step_context(self):
        return self.get_scenario_context().get_current_step()
        



