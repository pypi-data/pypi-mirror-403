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
from holado_crypto.crypto.crypto import CryptoManager

logger = logging.getLogger(__name__)


def __get_scenario_context():
    return SessionContext.instance().get_scenario_context()

def __get_text_interpreter():
    return __get_scenario_context().get_text_interpreter()

def __get_variable_manager():
    return __get_scenario_context().get_variable_manager()



@Step(r"(?P<var_name>{Variable}) = encrypt (?P<data>{Str}) with public key (?P<public_key>{Str})")
def step_impl(context, var_name, data, public_key):
    """ Encrypt data with a public key.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    data = StepTools.evaluate_scenario_parameter(data)
    public_key = StepTools.evaluate_scenario_parameter(public_key)
    
    res = CryptoManager.encrypt_data_with_key(data, public_key)
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"(?P<var_name>{Variable}) = decrypt (?P<data>{Bytes}) with private key (?P<private_key>{Str})")
def step_impl(context, var_name, data, private_key):
    """ Decrypt data with a private key.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    data = StepTools.evaluate_scenario_parameter(data)
    private_key = StepTools.evaluate_scenario_parameter(private_key)
    
    res = CryptoManager.decrypt_data_with_key(data, private_key)
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"(?P<var_name>{Variable}) = encrypt (?P<data>{Bytes}) with public key (?P<public_key>{Str})")
def step_impl(context, var_name, data, public_key):
    """ Encrypt data with a public key.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    data = StepTools.evaluate_scenario_parameter(data)
    public_key = StepTools.evaluate_scenario_parameter(public_key)
    
    res = CryptoManager.cipher_data(data, public_key)
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"(?P<var_name>{Variable}) = new cipher \(algorithm: (?P<algorithm>{Str}) ; key: (?P<key>{Bytes})\)")
def step_impl(context, var_name, algorithm, key):
    """ Create new cipher instance.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    algorithm = StepTools.evaluate_scenario_parameter(algorithm)
    key = StepTools.evaluate_scenario_parameter(key)
    
    res = CryptoManager.new_cipher(algorithm_name=algorithm, algorithm_key=key)
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"(?P<var_name>{Variable}) = cipher (?P<data>{Bytes}) \(cipher: (?P<cipher>{Variable})\)")
def step_impl(context, var_name, data, cipher):
    """ Cipher data with a cipher instance.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    data = StepTools.evaluate_scenario_parameter(data)
    cipher = StepTools.evaluate_scenario_parameter(cipher)
    
    res = CryptoManager.cipher_data(data, cipher)
    
    __get_variable_manager().register_variable(var_name, res)

@Step(r"(?P<var_name>{Variable}) = decipher (?P<data>{Bytes}) \(cipher: (?P<cipher>{Variable})\)")
def step_impl(context, var_name, data, cipher):
    """ Decipher data with a cipher instance.
    """
    var_name = StepTools.evaluate_variable_name(var_name)
    data = StepTools.evaluate_scenario_parameter(data)
    cipher = StepTools.evaluate_scenario_parameter(cipher)
    
    res = CryptoManager.decipher_data(data, cipher)
    
    __get_variable_manager().register_variable(var_name, res)



