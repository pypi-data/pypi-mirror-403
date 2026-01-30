# Copyright (c) 2024 Plug and Play Robotics (Suzhou) Co., Ltd.
# This software is licensed under the MPL-2.0 license.
# See the LICENSE file for details.

from .franka_desk_api import FrankDeskApi, create_franka_api_from_args
from .config_manager import config_manager

def init_config(overwrite: bool = False) -> None:
    """
    Initialize user configuration files
    
    Args:
        overwrite: Whether to overwrite existing configuration files
    """
    config_manager.copy_default_configs(overwrite)
    print(f"Configuration files initialized to: {config_manager.get_user_config_dir()}")

__all__ = ['FrankDeskApi', 'create_franka_api_from_args', 'config_manager', 'init_config']