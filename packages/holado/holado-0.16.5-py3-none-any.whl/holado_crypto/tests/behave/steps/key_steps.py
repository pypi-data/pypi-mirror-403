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


from holado.common.context.session_context import SessionContext
from holado_test.behave.behave import *  # @UnusedWildImport
import logging
from holado_test.behave.scenario.behave_step_tools import BehaveStepTools
from holado_value.common.tables.converters.value_table_converter import ValueTableConverter
from holado_crypto.crypto.key import KeyManager
from holado_test.scenario.step_tools import StepTools

logger = logging.getLogger(__name__)


def __get_scenario_context():
    return SessionContext.instance().get_scenario_context()

def __get_text_interpreter():
    return __get_scenario_context().get_text_interpreter()

def __get_variable_manager():
    return __get_scenario_context().get_variable_manager()



@Given(r"generate new self-signed key files for localhost")
def step_impl(context):
    """Generate public and private keys for a localhost use.
    """
    table = BehaveStepTools.convert_step_table_2_value_table_with_header(context.table)
    kwargs = ValueTableConverter.convert_name_value_table_2_dict(table)

    KeyManager.generate_new_self_signed_key_files_for_localhost(**kwargs)

@Given(r"(?P<var_name>{Variable}) = public key for (?:(?P<is_x509_str>X509) )?PEM file (?P<file_path>{Str})")
def step_impl(context, var_name, is_x509_str, file_path):
    """Get public key instance.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    is_x509 = is_x509_str is not None
    file_path = StepTools.evaluate_scenario_parameter(file_path)
    
    res = KeyManager.load_pem_public_key(file_path=file_path, is_x509=is_x509)
    
    __get_variable_manager().register_variable(var_name, res)

@Given(r"(?P<var_name>{Variable}) = private key for PEM file (?P<file_path>{Str})")
def step_impl(context, var_name, file_path):
    """Get private key instance.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    file_path = StepTools.evaluate_scenario_parameter(file_path)
    
    res = KeyManager.load_pem_private_key(file_path=file_path)
    
    __get_variable_manager().register_variable(var_name, res)

@Given(r"(?P<var_name>{Variable}) = convert public key (?P<pub_key>{Variable}) to hexadecimal")
def step_impl(context, var_name, pub_key):
    """Return path to default cert file.
    Note: It uses ssl.get_default_verify_paths method.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    key = StepTools.evaluate_variable_value(pub_key)
    
    res = KeyManager.convert_public_key_to_hex(key)
    
    __get_variable_manager().register_variable(var_name, res)


