# Copyright (c) 2024 Plug and Play Robotics (Suzhou) Co., Ltd.
# This software is licensed under the MPL-2.0 license.
# See the LICENSE file for details.



import yaml
from typing import Dict, Any
import os

def load_convenience_methods():
    """Load convenience methods configuration"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "desk_api_cfg", "api_cfg", "methods.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('convenience_methods', {})
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Failed to load convenience methods config: {e}")
        return {}

def add_convenience_methods_to_class(cls):
    """Add convenience methods to FrankaAPI class"""
    methods_config = load_convenience_methods()
    
    for method_name, api_name in methods_config.items():
        def create_method(input_api_name):
            def method(self, *args, **kwargs):
                return self.call_api(input_api_name, *args, **kwargs)
            return method
        
        if api_name == "offline_software_update":
            def offline_software_update(self, file_path: str = None, binary_data: bytes = None):
                if file_path is not None:
                    return self.call_api("offline_software_update", file_path=file_path)
                elif binary_data is not None:
                    return self.call_api("offline_software_update", body=binary_data)
                else:
                    raise ValueError("Must provide file_path or binary_data parameter")
            setattr(cls, method_name, offline_software_update)
        
        elif api_name == "change_operating_mode":
            def change_operating_mode(self, mode: str = "Execution"):
                return self.call_api("change_operating_mode", mode=mode)
            setattr(cls, method_name, change_operating_mode)
        
        elif api_name == "start_arm_motion":
            def start_arm_motion(self, mode: str = "MoveToPackPose"):
                return self.call_api("start_arm_motion", mode=mode)
            setattr(cls, method_name, start_arm_motion)
        
        elif method_name == "change_mode_execution":
            def change_mode_execution(self):
                return self.call_api("change_operating_mode", mode="Execution")
            setattr(cls, method_name, change_mode_execution)
        
        elif method_name == "move_to_pack_pose":
            def move_to_pack_pose(self):
                return self.call_api("start_arm_motion", mode="MoveToPackPose")
            setattr(cls, method_name, move_to_pack_pose)
        
        elif method_name == "activate_fci":
            def activate_fci(self):
                result = self.call_api("activate_fci")
                input("Press Enter to quit and release control...")
                return result
            setattr(cls, method_name, activate_fci)
        elif method_name == "enable_fci":
            def enable_fci(self):
                result = self.call_api("enable_fci")
                input("Press Enter to quit and release control...")
                return result
            setattr(cls, method_name, enable_fci)
        
        else:
            setattr(cls, method_name, create_method(api_name))
    
    return cls