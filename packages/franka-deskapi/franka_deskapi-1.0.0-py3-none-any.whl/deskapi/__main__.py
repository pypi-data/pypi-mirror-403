# Copyright (c) 2024 Plug and Play Robotics (Suzhou) Co., Ltd.
# This software is licensed under the MPL-2.0 license.
# See the LICENSE file for details.

import argparse
from .config_manager import config_manager

def main():
    parser = argparse.ArgumentParser(description="Franka Desk API Configuration Management Tool")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    init_parser = subparsers.add_parser('init_config', help='Initialize user configuration files')
    init_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing configuration files')
    
    list_parser = subparsers.add_parser('list_robots', help='List all available robot configurations')
    
    dir_parser = subparsers.add_parser('show_config_dir', help='Show configuration directory path')
    
    args = parser.parse_args()
    
    if args.command == 'init_config':
        config_manager.copy_default_configs(args.overwrite)
        print(f"Configuration files initialized to: {config_manager.get_user_config_dir()}")
        
    elif args.command == 'list_robots':
        robots = config_manager.list_available_robots()
        if robots:
            print("Available robot configurations:")
            for robot in robots:
                print(f"  - {robot}")
        else:
            print("No robot configurations found")
            
    elif args.command == 'show_config_dir':
        print(f"User configuration directory: {config_manager.get_user_config_dir()}")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()