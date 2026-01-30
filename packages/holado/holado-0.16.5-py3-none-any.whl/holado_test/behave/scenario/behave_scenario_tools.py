
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
from holado_test.scenario.scenario_tools import ScenarioStatusInfo,\
    ScenarioTools



logger = logging.getLogger(__name__)


class BehaveScenarioTools(ScenarioTools):
    """
    Gives usefull tools for scenarios.
    """
    

    @classmethod
    def get_scenario_uid(cls, scenario):
        return f"{scenario.filename} at l.{scenario.line}"
    
    @classmethod
    def format_scenario_short_description(cls, scenario):
        return f"{scenario.filename} at l.{scenario.line}"
    
    @classmethod
    def compute_validation_status(cls, scenario, scenario_context, step_failed):
        if step_failed is not None and hasattr(scenario_context, "is_in_preconditions") and scenario_context.is_in_preconditions:
            return "Failed in Preconditions"
        elif step_failed is not None and step_failed.keyword == "Given":
            return "Failed in Given"
        elif step_failed is not None or scenario.status.has_failed():
            return "Failed"
        elif hasattr(scenario, 'sut_failed') and scenario.sut_failed:
            return "Failed in SUT"
        else:
            return scenario.status.name.capitalize()
        
    @classmethod
    def get_step_failed_info(cls, scenario):
        res_step, res_step_number = None, None
        for ind, step in enumerate(scenario.steps):
            if step.status.has_failed():
                res_step, res_step_number = step, ind+1
                break
        return res_step, res_step_number
    


