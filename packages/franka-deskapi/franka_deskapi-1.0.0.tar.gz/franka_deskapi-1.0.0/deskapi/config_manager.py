# Copyright (c) 2024 Plug and Play Robotics (Suzhou) Co., Ltd.
# This software is licensed under the MPL-2.0 license.
# See the LICENSE file for details.

import shutil
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from importlib.resources import files as resource_files
    IMPORTLIB_AVAILABLE = True
except ImportError:
    try:
        from importlib_resources import files as resource_files
        IMPORTLIB_AVAILABLE = True
    except ImportError:
        IMPORTLIB_AVAILABLE = False

class ConfigManager:
    """Manage configuration files with support for user home directory configuration"""
    
    def __init__(self):
        self.user_config_dir = Path.home() / ".frankadeskapi"
        self.user_config_dir.mkdir(exist_ok=True)
        self.package_config_dir = self._get_package_config_dir()
    
    def _get_package_config_dir(self) -> Path:

        if IMPORTLIB_AVAILABLE:
            try:
                config_resource = resource_files('deskapi') / 'desk_api_cfg'
                if config_resource.is_dir():
                    return Path(str(config_resource))
            except Exception:
                pass  
        current_dir = Path(__file__).parent
        config_path = current_dir / "desk_api_cfg"
        if config_path.exists():
            return config_path
        return current_dir
    
    def get_config_path(self, filename: str, use_user_config: bool = True) -> Path:
        """
        Get configuration file path, prioritize user configuration
        
        Args:
            filename: Configuration file name
            use_user_config: Whether to prioritize user configuration
            
        Returns:
            Configuration file path
        """
        user_path = self.user_config_dir / filename
        package_path = self.package_config_dir / filename
        if use_user_config and user_path.exists():
            return user_path
        else:
            return package_path
    
    def copy_default_configs(self, overwrite: bool = False) -> None:
        """
        Copy default configuration files to user directory
        
        Args:
            overwrite: Whether to overwrite existing files
        """
        config_files = ["config.yaml", "robot.yaml"]
        
        for filename in config_files:
            source_path = self.package_config_dir / filename
            target_path = self.user_config_dir / filename
            
            if source_path.exists():
                if not target_path.exists() or overwrite:
                    shutil.copy2(source_path, target_path)
                    print(f"Copied {filename} to user configuration directory")
                    print(f"Source: {source_path}")
                    print(f"Target: {target_path}")
                else:
                    print(f"User configuration file {filename} already exists, skipping copy")
            else:
                print(f"Warning: Default configuration file {filename} does not exist at {source_path}")
                print("Available files in package config directory:")
                if self.package_config_dir.exists():
                    for file in self.package_config_dir.iterdir():
                        print(f"  - {file.name}")
    
    def load_config(self, filename: str, use_user_config: bool = True) -> Dict[str, Any]:
        """
        Load configuration file
        
        Args:
            filename: Configuration file name
            use_user_config: Whether to prioritize user configuration
            
        Returns:
            Configuration dictionary
        """
        config_path = self.get_config_path(filename, use_user_config)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Configuration file not found: {config_path}")
            return {}
        except Exception as e:
            print(f"Failed to load configuration file {config_path}: {e}")
            return {}
    
    def save_config(self, filename: str, config_data: Dict[str, Any]) -> None:
        """
        Save configuration file to user directory
        
        Args:
            filename: Configuration file name
            config_data: Configuration data
        """
        target_path = self.user_config_dir / filename
        
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            print(f"Configuration file saved to: {target_path}")
        except Exception as e:
            print(f"Failed to save configuration file {target_path}: {e}")
    
    def get_robot_config(self, robot_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get robot configuration
        
        Args:
            robot_name: Robot name, if None use default robot
            
        Returns:
            Robot configuration dictionary
        """
        robot_config = self.load_config("robot.yaml")
        
        if not robot_config:
            return {}
        
        if robot_name:
            return robot_config.get("robots", {}).get(robot_name, {})
        else:
            default_robot = robot_config.get("default_robot")
            if default_robot:
                return robot_config.get("robots", {}).get(default_robot, {})
            else:
                robots = robot_config.get("robots", {})
                if robots:
                    return next(iter(robots.values()))
                else:
                    return {}
    
    def list_available_robots(self) -> list:
        """List all available robot configurations"""
        robot_config = self.load_config("robot.yaml")
        return list(robot_config.get("robots", {}).keys())
    
    def get_user_config_dir(self) -> Path:
        """Get user configuration directory path"""
        return self.user_config_dir

config_manager = ConfigManager()