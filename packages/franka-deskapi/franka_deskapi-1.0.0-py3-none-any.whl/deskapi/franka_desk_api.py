# Copyright (c) 2024 Plug and Play Robotics (Suzhou) Co., Ltd.
# This software is licensed under the MPL-2.0 license.
# See the LICENSE file for details.


import base64
import hashlib
import http.client
import json
import ssl
import time
import urllib.parse
import os
import yaml
from http.client import HTTPSConnection, HTTPResponse
from typing import Dict, Optional, Any, Literal
from typing import Tuple
import argparse
from .config_manager import config_manager

def load_api_config():
    """Load API configuration from file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "desk_api_cfg", "api_cfg", "api_cfg.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('api_config', {})
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Failed to load API config: {e}")
        return {}

API_CONFIG = load_api_config()

class FrankDeskApiError(Exception):
    pass

class FrankaAPIError(FrankDeskApiError):
    def __init__(
        self,
        target: str,
        http_code: int,
        http_reason: str,
        headers: Dict[str, str],
        message: str,
    ):
        super().__init__(
            f"Franka API returned error {http_code} ({http_reason}) when accessing end-point {target}: {message}"
        )
        self.target = target
        self.http_code = http_code
        self.headers = headers
        self.message = message

class TakeControlTimeoutError(FrankDeskApiError):
    pass



class FrankDeskApi:
    def __init__(self, hostname: str, username: str, password: str):
        self.__hostname = hostname
        self.__username = username
        self.__password = password

        self.__client = None
        self.__token = None
        self.__control_token = None
        self.__control_token_id = None

    def _load_robot_config(self, config_section: str = None):
        """Load robot configuration from file"""
        try:
            config_data = config_manager.load_config("config.yaml")
            
            if not config_data:
                raise FileNotFoundError("No configuration found in robot_config.yaml")
            
            if config_section:
                if config_section in config_data:
                    return config_data[config_section]
                else:
                    raise KeyError(f"Configuration section '{config_section}' not found in robot_config.yaml")
            else:
                first_key = next(iter(config_data))
                return config_data[first_key]
                    
        except FileNotFoundError:
            raise FileNotFoundError("robot_config.yaml file not found")
        except KeyError as e:
            raise KeyError(f"Configuration loading failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load robot configuration: {e}")

    @staticmethod
    def __encode_password(user: str, password: str) -> str:
        bs = ",".join(
            [
                str(b)
                for b in hashlib.sha256(
                    (password + "#" + user + "@franka").encode("utf-8")
                ).digest()
            ]
        )
        return base64.encodebytes(bs.encode("utf-8")).decode("utf-8")

    def __get_basic_auth_header(self) -> str:
        credentials = f"{self.__username}:{self.__password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

    def __get_basic_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.__get_basic_auth_header()
        }
    
    def _send_api_request(
        self,
        target: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        method: Literal["GET", "POST", "DELETE","PATCH", "PUT"] = "POST",
    ):
        _headers = {"Cookie": f"authorization={self.__token}"}
        if headers is not None:
            _headers.update(headers)
        
        try:
            self.__client.request(method, target, headers=_headers, body=body)
            res: HTTPResponse = self.__client.getresponse()
            success_codes = [200]
            if method in ["POST", "PATCH", "PUT"]:
                success_codes.append(204)  
            
            response_data = res.read()
            
            if res.getcode() not in success_codes:
                try:
                    error_message = response_data.decode("utf-8")
                except UnicodeDecodeError:
                    error_message = f"Binary response data (size: {len(response_data)} bytes)"
                
                raise FrankaAPIError(
                    target,
                    res.getcode(),
                    res.reason,
                    dict(res.headers),
                    error_message,
                )
            
            if res.getcode() == 200:
                return response_data
            else:  
                return None
        except http.client.CannotSendRequest:
            raise
        except Exception as ex:
            try:
                if hasattr(self.__client, '_HTTPConnection__response') and self.__client._HTTPConnection__response:
                    self.__client._HTTPConnection__response.read()
            except:
                pass
            raise ex

    def send_api_request(
        self,
        target: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        method: Literal["GET", "POST", "DELETE"] = "POST",
    ):
        last_error = None
        for i in range(3):
            try:
                return self._send_api_request(target, headers, body, method)
            except (http.client.RemoteDisconnected, http.client.CannotSendRequest) as ex:
                if isinstance(ex, http.client.CannotSendRequest):
                    self.__reset_connection()
                last_error = ex
        raise last_error

    def __reset_connection(self):
        """Reset the HTTP connection to a clean state"""
        if hasattr(self, '__client') and self.__client:
            try:
                self.__client.close()
            except:
                pass
            self.__client = HTTPSConnection(
                self.__hostname, timeout=30.0, context=ssl._create_unverified_context()
            )
            self.__client.connect()
            if self.__token:
                _headers = {"Cookie": f"authorization={self.__token}"}
                self.__client.request("GET", "/admin/api/system-status", headers=_headers)
                res = self.__client.getresponse()
                res.read()  

    def send_control_api_request(
        self,
        target: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        method: Literal["GET", "POST", "DELETE"] = "POST",
    ):
        if headers is None:
            headers = {}
        self.__check_control_token()
        _headers = {"X-Control-Token": self.__control_token}
        _headers.update(headers)
        return self.send_api_request(target, headers=_headers, method=method, body=body)

    def open(self, timeout: float = 30.0):
        if self.is_open:
            raise RuntimeError("Session is already open.")
        self.__client = HTTPSConnection(
            self.__hostname, timeout=timeout, context=ssl._create_unverified_context()
        )
        self.__client.connect()
        payload = json.dumps(
            {
                "login": self.__username,
                "password": self.__encode_password(self.__username, self.__password),
            }
        )
        self.__token = self.send_api_request(
            "/admin/api/login",
            headers={"content-type": "application/json"},
            body=payload,
        ).decode("utf-8")
        return self

    def close(self):
        if not self.is_open:
            raise RuntimeError("Session is not open.")
        if self.__control_token is not None:
            self.release_control()
        self.__token = None
        self.__client.close()

    def __enter__(self):
        return self.open()

    def __exit__(self, type, value, traceback):
        self.close()

    def __check_control_token(self):
        if self.__control_token is None:
            raise RuntimeError(
                "Client does not have control. Call take_control() first."
            )

    def take_control(self, wait_timeout: float = 30.0, force: bool = False):
        if not self.has_control():
            res = self.send_api_request(
                f"/admin/api/control-token/request{'?force' if force else ''}",
                headers={"content-type": "application/json"},
                body=json.dumps({"requestedBy": self.__username}),
            )
            if force:
                print(
                    "Forcibly taking control: "
                    f"Please physically take control by pressing the top button on the FR3 within {wait_timeout}s!"
                )
            response_dict = json.loads(res)
            self.__control_token = response_dict["token"]
            self.__control_token_id = response_dict["id"]
            start = time.time()
            has_control = self.has_control()
            while time.time() - start < wait_timeout and not has_control:
                time.sleep(max(0.0, min(1.0, wait_timeout - (time.time() - start))))
                has_control = self.has_control()
            if not has_control:
                raise TakeControlTimeoutError(
                    f"Timed out waiting for control to be granted after {wait_timeout}s."
                )

    def release_control(self):
        if self.__control_token is not None:
            self.send_control_api_request(
                "/admin/api/control-token",
                headers={"content-type": "application/json"},
                method="DELETE",
                body=json.dumps({"token": self.__control_token}),
            )
            self.__control_token = None
            self.__control_token_id = None

    def has_control(self):
        if self.__control_token_id is not None:
            status = self.get_system_status()
            active_token = status["controlToken"]["activeToken"]
            return (
                active_token is not None
                and active_token["id"] == self.__control_token_id
            )
        return False

    def call_api(self, api_name: str, **kwargs):
        """Unified API calling method"""
        if api_name not in API_CONFIG:
            raise ValueError(f"Unknown API: {api_name}")
        
        config = API_CONFIG[api_name]
        endpoint = config["endpoint"]
        method = config["method"]
        headers = config.get("headers", {}).copy()
        api_timeout = config.get("timeout")
        original_timeout = None

        if api_timeout is not None:
            original_timeout = self.__client.timeout
            self.__client.timeout = api_timeout
        
        if config.get("needs_auth", False):
            headers.update(self.__get_basic_auth_headers())
        
        if api_name == "enable_fci":
            body = self._build_enable_fci_body()
        elif api_name == "change_operating_mode":
            mode = kwargs.get('mode', 'Execution')
            body = json.dumps({"desiredOperatingMode": mode})
        elif api_name == "start_arm_motion":
            motion_type = kwargs.get('mode', 'MoveToPackPose')
            body = json.dumps({"type": motion_type})
        elif api_name == "offline_software_update":
            file_path = kwargs.get('file_path')
            if not file_path:
                raise ValueError("offline_software_update requires file_path parameter")
            
            with open(file_path, "rb") as f:
                body = f.read()
            headers["content-type"] = "application/octet-stream"
        
        else:
            if config.get("load_config_from_file", False):
                config_data = kwargs.get('config_data')
                if config_data is None:
                    config_section = config.get("load_config_from_file")
                    if isinstance(config_section, str) and config_section != "true":
                        config_data = self._load_robot_config(config_section)
                    else:
                        config_data = self._load_robot_config()
                if api_name == "add_userConfiguration": 
                    self._validate_admin_user_presence(config_data)
                
                body = json.dumps(config_data)
            else:
                body = kwargs.get('body')           
                if 'file_path' in kwargs:
                    with open(kwargs['file_path'], "rb") as f:
                        body = f.read()
                    headers["content-type"] = "application/octet-stream"
        try:    
            if config.get("needs_control", False):
                response = self.send_control_api_request(
                    endpoint, headers=headers, body=body, method=method
                )
            else:
                response = self.send_api_request(
                    endpoint, headers=headers, body=body, method=method
                )
            
            if config.get("save_file", False) and response:
                return self._handle_file_save(response, config)
            
            return self._handle_standard_response(response, config)
    
        finally:
            if original_timeout is not None:
                self.__client.timeout = original_timeout
    
    def _validate_admin_user_presence(self, config_data):
        if not config_data:
            raise ValueError("Configuration data is empty")
        if 'userConfiguration' not in config_data:
            raise ValueError("Configuration data is missing userConfiguration field")  
        
        user_config = config_data['userConfiguration']
        if 'users' not in user_config:
            raise ValueError("userConfiguration is missing users field")  
        
        users = user_config['users']
        if not isinstance(users, list):
            raise ValueError("users field must be a list of users")
        has_admin = False
        for user in users:
            if isinstance(user, dict) and user.get('role') == 'Admin':
                has_admin = True
                break 
        if not has_admin:
            print("Invalid user configuration: Account must contain Admin user")
            raise ValueError("User configuration must contain at least one Admin user")
        print("User configuration validation passed: Contains Admin user")
    
    
    def _build_enable_fci_body(self):
        """Build special body for enable_fci"""
        token_encoded = base64.b64encode(self.__control_token.encode('ascii'))
        token_quoted = urllib.parse.quote(token_encoded)
        return f"token={token_quoted}"
    
    def _handle_standard_response(self, response, config):
        """Handle standard response"""
        if not response:
            return None
            
        response_type = config.get("response_type", "none")
        if response_type == "json":
            return json.loads(response.decode("utf-8"))
        elif response_type == "text":
            return response.decode("utf-8")
        elif response_type == "binary":
            return response
        else:
            return None
    
    def _handle_file_save(self, response, config):
        """Handle file saving logic"""
        import datetime
        
        try:
            system_state = self.get_system_state()
            control_serial = system_state.get('controlSerialNumber', 'unknown-unknown')
        except:
            control_serial = 'unknown-unknown'
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
        filename_template = config.get("filename_template", "data-{controlSerialNumber}-{timestamp}.log")
        filename = filename_template.format(
            controlSerialNumber=control_serial,
            timestamp=current_time
        )
        
        with open(filename, "wb") as f:
            f.write(response)
        
        return f"Data saved to file: {filename}, size: {len(response)} bytes"

    @property
    def client(self) -> HTTPSConnection:
        return self.__client

    @property
    def token(self) -> str:
        return self.__token

    @property
    def is_open(self) -> bool:
        return self.__token is not None
       

def create_franka_api_from_args(description: str = "Franka robot operation") -> Tuple[FrankDeskApi, argparse.Namespace]:
    """
    Create FrankDeskApi instance from command line arguments
    
    Args:
        description: Description for the argument parser
        
    Returns:
        Tuple of (FrankDeskApi instance, parsed arguments)
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--robot", type=str, help="Robot name to use from config file")
    parser.add_argument("--config-dir", type=str, help="Custom config directory path")
    args = parser.parse_args()
    
    if args.config_dir:
        config_path = Path(args.config_dir) / "robot.yaml"
    else:
        config_path = config_manager.get_config_path("robot.yaml")
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        print("Please run 'python -m deskapi init_config' to initialize configuration files")
        raise

    if args.robot:
        robot_name = args.robot
    else:
        robot_name = config.get('default_robot', 'fci')
    
    robot_config = config['robots'][robot_name]
    if not robot_config:
        available_robots = list(config.get('robots', {}).keys())
        raise ValueError(f"Robot configuration '{robot_name}' not found. Available robots: {available_robots}")
    host = robot_config['host']
    user = robot_config['user']
    password = robot_config['password']
    
    return FrankDeskApi(host, user, password), args
from .convenience_methods import add_convenience_methods_to_class
FrankDeskApi = add_convenience_methods_to_class(FrankDeskApi)