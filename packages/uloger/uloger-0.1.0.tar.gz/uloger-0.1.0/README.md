# uloger

一个灵活的Python日志辅助模块，提供简单易用的日志功能。

## 功能特点

- 支持控制台和文件日志同时输出
- 自动创建日志目录，支持自定义日志文件路径
- 支持日志轮转（按时间或大小）
- 支持日志备份压缩
- 兼容PyInstaller打包环境
- 简单易用的API接口

## 安装方法

### 使用pip从Git仓库安装

```bash
pip install uloger
```
### 使用pip从Git仓库更新

```bash
pip install uloger
```

### 使用uv从Git仓库安装

```bash
uv add uloger
```

### 使用uv从Git仓库更新

```
uv sync --upgrade-package uloger
```



### 使用pip从本地安装

```bash
# 进入项目目录
cd path/to/uloger
# 安装模块
pip install -e .
```

### 使用uv从本地安装

```bash
# 进入项目目录
cd path/to/uloger
# 安装模块
uv add -e .
```

## 使用示例

### 基本用法

```python
from uloger import logger

# 使用日志记录器
logger.info("这是一条信息日志")
logger.debug("这是一条调试日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")
logger.critical("这是一条严重错误日志")

try:
    1/0
except Exception:
    logger.exception("发生了异常")
```

### 使用简化函数

```python
from uloger import log_info, log_debug, log_warning, log_error, log_critical, log_exception

# 使用简化的日志函数
log_info("这是一条信息日志")
log_debug("这是一条调试日志")
log_warning("这是一条警告日志")
log_error("这是一条错误日志")
log_critical("这是一条严重错误日志")

try:
    1/0
except Exception:
    log_exception("发生了异常")
```

### 自定义配置

```python
from uloger import uloger

# 创建自定义配置的日志记录器
config = {
    "log_dir": "my_logs",  # 自定义日志目录
    "log_file_name": "my_app_{date}.log",  # 自定义日志文件名
    "console_log_level": "INFO",  # 控制台日志级别
    "file_log_level": "DEBUG",  # 文件日志级别
    "log_backup_count": 30,  # 日志备份数量
    "log_rotation_when": "D",  # 按天轮转
    "log_rotation_interval": 1,  # 轮转间隔
    "compress_backups": True,  # 压缩备份日志
    "enable_signal_handler": False  # 不启用信号处理器
}

# 创建自定义日志记录器实例
custom_logger = uloger(config).get_logger()

# 使用自定义日志记录器
custom_logger.info("这是使用自定义配置的日志")
```

## 配置选项

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| log_dir | str | "logs" | 日志目录名称 |
| log_file_name | str | "app_{date}.log" | 日志文件名，{date}会被替换为当前日期 |
| log_formatter_console | str | "%(asctime)s - %(levelname)s - %(message)s" | 控制台日志格式 |
| log_formatter_file | str | "%(asctime)s - %(levelname)s - <%(funcName)s> - %(message)s" | 文件日志格式 |
| log_backup_count | int | 180 | 日志文件最多保留的备份数量 |
| console_log_level | int/str | logging.INFO | 控制台日志级别 |
| file_log_level | int/str | logging.DEBUG | 文件日志级别 |
| log_rotation_when | str | "D" | 日志轮转时间单位（S:秒, M:分, H:时, D:天, W0-W6:星期几） |
| log_rotation_interval | int | 1 | 日志轮转间隔 |
| log_max_bytes | int/None | None | 单个日志文件最大字节数，None表示不限制 |
| compress_backups | bool | False | 是否压缩备份日志 |
| logger_name | str | "app_logger" | 日志记录器名称 |
| enable_signal_handler | bool | True | 是否启用信号处理器 |

## 注意事项

- 日志默认保存在程序运行目录下的logs文件夹中
- 如果使用PyInstaller打包程序，日志功能仍然可以正常工作
- 支持Windows、Linux和macOS平台

