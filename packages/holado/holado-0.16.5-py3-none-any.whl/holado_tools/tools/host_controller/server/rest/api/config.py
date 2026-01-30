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

from flask.views import MethodView
from holado.common.context.session_context import SessionContext
from holado_yaml.yaml.yaml_manager import YAMLManager
import logging

logger = logging.getLogger(__name__)


def _get_session_context():
    return SessionContext.instance()


class YamlFileView(MethodView):
    
    def get(self, body: dict):
        file_path = body.get('file_path')
        field_keys = body.get('field_keys')
        
        try:
            data = YAMLManager.load_file(file_path)
            
            res = data
            if field_keys:
                current_keys = []
                for key in field_keys:
                    if not isinstance(res, dict):
                        return f"Field '{'.'.join(current_keys)}' is not an object in YAML file '{file_path}'", 400
                    
                    current_keys.append(key)
                    if key not in res:
                        return f"Field '{'.'.join(current_keys)}' doesn't exist in YAML file '{file_path}'", 400
                    
                    res = res[key]
            
            return res
        except Exception as exc:
            logger.exception(f"Failed to get content of YAML file '{file_path}'")
            return str(exc), 500

    def patch(self, body: dict):
        file_path = body.get('file_path')
        
        try:
            yaml_string = body['yaml_string']
            with_backup = body['with_backup']
            backup_extension = body['backup_extension']
            
            data = YAMLManager.load_string(yaml_string)
            res = YAMLManager.update_file(file_path, data, with_backup=with_backup, backup_extension=backup_extension)
            
            return res
        except Exception as exc:
            logger.exception(f"Failed to update content of YAML file '{file_path}'")
            return str(exc), 500

    def put(self, body: list):
        file_path = body.get('file_path')
        
        try:
            action = body['action']
            backup_extension = body['backup_extension']
            
            if action == 'restore':
                res = YAMLManager.restore_file(file_path, backup_extension=backup_extension)
            else:
                return f"Unmanaged action '{action}'", 400
                
            return res
        except Exception as exc:
            logger.exception(f"Failed to restore content of YAML file '{file_path}'")
            return str(exc), 500





