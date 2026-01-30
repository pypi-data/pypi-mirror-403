
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

logger = logging.getLogger(__name__)


class ScenarioStatusInfo(object):
    validation_category = None
    validation_status = None
    step_failed = None
    step_failed_nb = None
    scenario_context = None
    step_context = None
    scenario_error = None
    
    def __init__(self, category, status, step_failed, step_nb, scenario_context, step_context, scenario_error):
        self.validation_category = category
        self.validation_status = status
        self.step_failed = step_failed
        self.step_failed_nb = step_nb
        self.scenario_context = scenario_context
        self.step_context = step_context
        self.scenario_error = scenario_error


#TODO: make it a service in SessionContext
class ScenarioTools(object):
    
    _scenario_status_info_by_uid = {}
    
    @staticmethod
    def _get_scenario_context():
        return SessionContext.instance().get_scenario_context()

    @classmethod
    def _get_test_server_client(cls):
        return SessionContext.instance().test_server_client
    


    @classmethod
    def get_scenario_uid(cls, scenario):
        raise NotImplementedError()
    
    @classmethod
    def format_scenario_short_description(cls, scenario):
        raise NotImplementedError()
        
    #TODO: Remove the dependence to current scenario with _get_scenario_context, and find the scenario context in context history, 
    @classmethod
    def get_current_scenario_status_info(cls, scenario):
        return cls.get_scenario_status_info(scenario, cls._get_scenario_context())
        
    @classmethod
    def get_scenario_status_info(cls, scenario, scenario_context):
        scenario_uid = cls.get_scenario_uid(scenario)
        if scenario_uid not in cls._scenario_status_info_by_uid:
            info = cls._build_scenario_status_info(scenario, scenario_context)
            cls._scenario_status_info_by_uid[scenario_uid] = info
        return cls._scenario_status_info_by_uid[scenario_uid]
    
    @classmethod
    def _build_scenario_status_info(cls, scenario, scenario_context):
        step_failed, step_nb = cls.get_step_failed_info(scenario)
        
        # Define scenario status
        status = cls.compute_validation_status(scenario, scenario_context, step_failed)
        
        # Define scenario category
        category = cls.compute_validation_category(scenario, status)
        
        scenario_error = None
        if hasattr(scenario, "sut_error"):
            scenario_error = scenario.sut_error
        
        return ScenarioStatusInfo(category, status, step_failed, step_nb, 
                                  scenario_context,
                                  scenario_context.get_step(step_nb-1) if step_nb is not None else None,
                                  scenario_error)

    @classmethod
    def get_step_failed_info(cls, scenario):
        raise NotImplementedError()


    @classmethod
    def compute_validation_status(cls, scenario, scenario_context):
        raise NotImplementedError()
        
    @classmethod
    def compute_validation_category(cls, scenario, status):
        if not cls._get_test_server_client().is_available:
            return None
        
        res = None
        
        # Get scenario execution statuses
        scenario_name = cls.format_scenario_short_description(scenario)
        sce_hist = cls._get_test_server_client().get_scenario_history(scenario_name=scenario_name, size=29)
        statuses = [s['status'] for s in reversed(sce_hist[0]['statuses'])] if sce_hist else []
        statuses.append(status)
        
        # Get scenario status sequences
        passed_sequences = []
        is_failed_relevant = None
        for status in statuses:
            if status == 'Passed':
                passed = True
            elif status.startswith("Failed"):
                passed = False
                if status == "Failed":
                    is_failed_relevant = True
                elif is_failed_relevant is None:
                    is_failed_relevant = False
            else:
                continue
            
            if len(passed_sequences) == 0 or passed != passed_sequences[-1][0]:
                passed_sequences.append([passed, 1])
            else:
                passed_sequences[-1][1] += 1
        
        # Compute category
        if passed_sequences:
            nb_exec = sum([x[1] for x in passed_sequences])
            last_passed, last_nb_times = passed_sequences[-1]
            if len(passed_sequences) == 1:
                if last_passed:
                    res = f'Always Success ({last_nb_times})'
                elif is_failed_relevant:
                    res = f'Always Failed ({last_nb_times})'
                else:
                    res = f'Always Not Relevant ({last_nb_times})'
            elif last_passed and len(passed_sequences) in [2, 3]:
                res = f'Fixed ({last_nb_times} success / {nb_exec})'
            elif len(passed_sequences) > 2:
                nb_fail = sum([x[1] for x in passed_sequences if not x[0]])
                if is_failed_relevant:
                    res = f'Random ({nb_fail} fails / {nb_exec})'
                else:
                    res = f'Random but Not Relevant ({nb_fail} fails / {nb_exec})'
            elif not last_passed:
                if last_nb_times == 1:
                    if is_failed_relevant:
                        res = f'Newly Failed ({last_nb_times} fails / {nb_exec})'
                    else:
                        res = f'Newly Failed but Not Relevant ({last_nb_times} fails / {nb_exec})'
                else:
                    if is_failed_relevant:
                        res = f'Regression ({last_nb_times} fails / {nb_exec})'
                    else:
                        res = f'Regression but Not Relevant ({last_nb_times} fails / {nb_exec})'
            else:
                res = f'Unknown (unmanaged sequence: {passed_sequences})'
        
        logger.debug(f"Category of scenario '{scenario}': {res}  (computed from last statuses: {statuses})")
        return res



