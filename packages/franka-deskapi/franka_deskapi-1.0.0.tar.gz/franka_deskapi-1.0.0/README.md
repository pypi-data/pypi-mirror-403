# Franka Desk API
![alt text](./blob/PNPRobotics.jpg)
一个由[集智联机器人（苏州）有限公司（ Plug and Play Robotics (Suzhou) Co., Ltd.）](#公司信息)基于 Franka Desk API 开发的 Python 工具，提供Franka机器人Desk界面的部分功能，如关节、重启、解锁抱闸、切换模式、激活FCI等，便于用户在终端中直接管理Franka机器人的运行状态。


## 安装

### 从 PyPI 安装（推荐）

```bash
pip install franka-deskapi
```

### 从源码安装

```bash
git clone https://github.com/chengyk-pnprobotics/FrankaDeskApi.git
cd FrankaDeskApi
pip install .
```

## 配置管理

### 初始化用户配置

安装包后，首先需要初始化用户配置文件：

```bash
# 方法1: 使用命令行工具
franka-desk-api-config init_config

# 方法2: 使用Python模块
python -m deskapi init_config

# 方法3: 在Python代码中初始化
from deskapi import init_config
init_config()
```

配置文件将自动复制到 `~/.frankadeskapi/` 目录，方便用户修改。

### 配置文件位置

- **默认配置**: 包内配置文件 (`deskapi/desk_api_cfg/`)
- **用户配置**: `~/.frankadeskapi/` (优先使用)

### 管理配置

```bash
# 列出所有可用的机器人配置
franka-desk-api-config list_robots

# 显示配置目录
franka-desk-api-config show_config_dir
```

### 自定义配置目录

可以通过环境变量或参数指定自定义配置目录：

```bash
# 使用环境变量
export FRANKA_DESK_API_CONFIG_DIR=/path/to/your/configs

# 使用命令行参数
python your_script.py --config-dir /path/to/your/configs

## 快速开始

### 基本连接测试

```python
from deskapi import create_franka_api_from_args

# 创建 API 实例
franka_api, args = create_franka_api_from_args("测试 Franka 机器人连接")

with franka_api:
    # 获取系统状态
    status = franka_api.get_system_status()
    print("系统状态:", status)
    
    # 获取系统状态信息
    state = franka_api.get_system_state()
    print("系统信息:", state)
```

### 完整的机器人启动流程

```python
from deskapi import create_franka_api_from_args

if __name__ == "__main__":
    franka_api, args = create_franka_api_from_args("启动 Franka 机器人")
    
    with franka_api:
        # 获取控制权限
        franka_api.take_control()
        
        # 获取配置信息
        config = franka_api.get_configuration()
        print(config)
        
        # 解锁刹车
        franka_api.unlock_brakes()
        
        # 设置为执行模式
        franka_api.set_mode_execution()
        
        # 启用 FCI
        franka_api.enable_fci()
        
        # 释放控制权限
        franka_api.release_control()
```

## 重要功能说明

### 强制获取控制权限

**关键特性：使用 `force=True` 参数强制获取控制权限**

在某些情况下，机器人可能已被其他用户或进程控制。此时可以使用 `force=True` 参数强制获取控制权限：

```python
from deskapi import create_franka_api_from_args

franka_api, args = create_franka_api_from_args("强制控制机器人")

with franka_api:
    # 强制获取控制权限（即使机器人已被其他用户控制）
    franka_api.take_control(force=True)
    
    # 执行需要控制权限的操作
    franka_api.unlock_brakes()
    franka_api.set_mode_execution()
    
    # 操作完成后释放控制
    franka_api.release_control()
```

**⚠️ 安全警告：**
- `force=True` 会强制中断其他用户的控制会话
- 仅在紧急情况或确定需要强制控制时使用
- 在生产环境中谨慎使用此功能

### 常用操作示例

#### 1. 机器人关机

```python
from deskapi import create_franka_api_from_args

franka_api, args = create_franka_api_from_args("关闭 Franka 机器人")

with franka_api:
    franka_api.take_control()
    franka_api.shutdown()
    print("机器人关机已启动")
```

#### 2. 解锁刹车

```python
from deskapi import create_franka_api_from_args

franka_api, args = create_franka_api_from_args("解锁 Franka 机器人刹车")

with franka_api:
    franka_api.take_control()
    franka_api.unlock_brakes()
    print("刹车已解锁")
```

#### 3. 设置为编程模式

```python
from deskapi import create_franka_api_from_args

franka_api, args = create_franka_api_from_args("设置 Franka 机器人为编程模式")

with franka_api:
    franka_api.take_control()
    franka_api.set_mode_programming()
    franka_api.release_control()
```

#### 4. 打包姿势移动

```python
from deskapi import create_franka_api_from_args

franka_api, args = create_franka_api_from_args("移动 Franka 机器人到打包姿势")

with franka_api:
    franka_api.take_control()
    franka_api.unlock_brakes()
    franka_api.set_mode_execution()
    franka_api.move_to_pack_pose()
    franka_api.shutdown()
```

## 命令行参数

库支持通过命令行参数配置机器人连接：

```bash
# 基本用法
python your_script.py --robot robot1

# 指定配置文件
python your_script.py --config /path/to/custom_config.yaml --robot robot2

# 查看帮助
python your_script.py --help
```

### 配置文件示例

创建 `cfg.yaml` 文件：

```yaml
default_robot: robot1

robots:
  robot1:
    host: "192.168.0.100"
    user: "franka"
    password: "franka123"
  
  robot2:
    host: "192.168.0.101" 
    user: "franka"
    password: "franka123"
```

## API 方法参考

### 控制相关方法
- `take_control(force=False)` - 获取控制权限
- `release_control()` - 释放控制权限
- `has_control()` - 检查是否拥有控制权限

### 模式设置方法
- `set_mode_execution()` - 设置为执行模式
- `set_mode_programming()` - 设置为编程模式

### 运动控制方法
- `unlock_brakes()` - 解锁刹车
- `lock_brakes()` - 锁定刹车
- `move_to_pack_pose()` - 移动到打包姿势

### 系统管理方法
- `shutdown()` - 关闭机器人
- `reboot()` - 重启机器人
- `enable_fci()` - 启用 FCI

## 公司信息
- **公司**: 集智联机器人（苏州）有限公司（ Plug and Play Robotics (Suzhou) Co., Ltd.）
- **网站**: https://www.pnprobotics.com
- **邮箱**: chengyk@pnprobotics.com

## 许可证

本项目基于 MPL-2.0 许可证。详见 [LICENSE](LICENSE) 文件。


## 贡献

欢迎提交 Issue 和 Pull Request！请确保代码符合项目的代码风格和质量标准。

---

*Franka 和 Franka Panda 是 Franka Emika GmbH 的注册商标。本项目是独立的第三方实现。*