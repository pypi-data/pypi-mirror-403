# -*- coding: utf-8 -*-

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


from holado_test.scenario.step_tools import StepTools
from holado.common.context.session_context import SessionContext
from holado_test.behave.behave import *  # @UnusedWildImport
import logging
from holado_test.behave.scenario.behave_step_tools import BehaveStepTools
from holado_value.common.tables.converters.value_table_converter import ValueTableConverter
from holado_email.test_tools.mailhog.mailhog_client import MailHogClient

logger = logging.getLogger(__name__)



def __get_scenario_context():
    return SessionContext.instance().get_scenario_context()

def __get_variable_manager():
    return __get_scenario_context().get_variable_manager()


@Step(r"(?P<var_name>{Variable}) = new MailHog client")
def step_impl(context, var_name):
    """ Create a MailHog client with package mailhog (https://pypi.org/project/mailhog/)
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    table = BehaveStepTools.get_step_table(context)
    kwargs = ValueTableConverter.convert_name_value_table_2_dict(table)
    
    res = MailHogClient.new_client(**kwargs)
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"(?P<var_name>{Variable}) = get number of emails \(MailHog client: (?P<var_client>{Variable})\)")
def step_impl(context, var_name, var_client):
    var_name = StepTools.evaluate_variable_name(var_name)
    client = StepTools.evaluate_variable_value(var_client)
    
    res = client.get_number_of_messages()
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"(?P<var_name>{Variable}) = get emails \(MailHog client: (?P<var_client>{Variable})\)")
def step_impl(context, var_name, var_client):
    var_name = StepTools.evaluate_variable_name(var_name)
    client = StepTools.evaluate_variable_value(var_client)
    table = BehaveStepTools.get_step_table(context)
    kwargs = ValueTableConverter.convert_name_value_table_2_dict(table)
    
    res = client.get_messages(**kwargs)
    
    __get_variable_manager().register_variable(var_name, res)
    


