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
from holado_email.email.smtp_client import SMTPClient
from holado_core.common.exceptions.functional_exception import FunctionalException

logger = logging.getLogger(__name__)



def __get_scenario_context():
    return SessionContext.instance().get_scenario_context()

def __get_variable_manager():
    return __get_scenario_context().get_variable_manager()


@Step(r"(?P<var_name>{Variable}) = new SMTP client")
def step_impl(context, var_name):
    """ Create a SMTP client with standard library smtplib
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    table = BehaveStepTools.get_step_table(context)
    kwargs = ValueTableConverter.convert_name_value_table_2_dict(table)
    
    res = SMTPClient('ts_smtp_client', smtp_kwargs=kwargs)
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"send mail \(SMTP client: (?P<var_client>{Variable})\)")
def step_impl(context, var_client):
    client = StepTools.evaluate_variable_value(var_client)
    table = BehaveStepTools.get_step_table(context)
    kwargs = ValueTableConverter.convert_name_value_table_2_dict(table)
    
    send_errors = client.internal_client.sendmail(**kwargs)
    
    if send_errors:
        raise FunctionalException(f"Failed to send mail to some addresses: {send_errors}")

@Step(r"send message (?P<message>{Variable}) \(SMTP client: (?P<var_client>{Variable})\)")
def step_impl(context, message, var_client):
    message = StepTools.evaluate_variable_value(message)
    client = StepTools.evaluate_variable_value(var_client)
    table = BehaveStepTools.get_step_table(context)
    kwargs = ValueTableConverter.convert_name_value_table_2_dict(table)
    
    send_errors = client.internal_client.send_message(message, **kwargs)
    
    if send_errors:
        raise FunctionalException(f"Failed to send message to some addresses: {send_errors}")





