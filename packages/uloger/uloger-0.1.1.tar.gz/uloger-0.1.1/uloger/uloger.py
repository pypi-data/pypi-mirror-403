
try:
    from importlib.metadata import version
except ImportError:
    # Python < 3.8
    from importlib_metadata import version

__version__ = version("uloger")

import signal
import sys
import logging
import os
import datetime
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import pathlib
import zipfile
from typing import Optional, Dict, Any, Union, Callable


class ULoger:
    """
    日志辅助类，提供灵活的日志配置和记录功能
    """

    # 默认配置
    DEFAULT_CONFIG = {
        "log_dir": "logs",
        "log_file_name": "app_{date}.log",
        "log_formatter_console": "%(asctime)s - %(levelname)s - %(message)s",
        "log_formatter_file": "%(asctime)s - %(levelname)s - <%(funcName)s> - %(message)s",
        "log_backup_count": 180,  # 日志文件最多保留180个备份
        "console_log_level": logging.INFO,
        "file_log_level": logging.DEBUG,
        "log_rotation_when": "D",  # 按天轮转
        "log_rotation_interval": 1,  # 轮转间隔
        "log_max_bytes": None,  # 单个日志文件最大字节数，None表示不限制
        "compress_backups": False,  # 是否压缩备份日志
        "logger_name": "app_logger",
        "enable_signal_handler": True,  # 是否启用信号处理器
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志处理器

        Args:
            config: 日志配置字典，可覆盖默认配置
        """
        # 合并配置
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

        # 验证配置
        self._validate_config()

        # 获取程序运行目录
        self.program_directory = self._get_app_dir()

        # 初始化日志记录器
        self.logger = self._setup_logger()

        # 根据配置决定是否注册信号处理
        if self.config.get("enable_signal_handler", True):
            self._register_signal_handler()

    def _get_app_dir(self) -> str:
        """
        获取程序根目录
        - 源码运行：返回 main.py 所在目录
        - PyInstaller / Nuitka 打包：返回 exe 所在目录
        """
        if "__compiled__" in globals():
            # Nuitka：argv[0] 保存的是原始 exe 路径
            return os.path.dirname(os.path.abspath(sys.argv[0]))

        # PyInstaller / 普通 exe
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))

        # 源码运行
        main_module = sys.modules.get("__main__")
        if main_module and hasattr(main_module, "__file__") and main_module.__file__:
            return os.path.dirname(os.path.abspath(main_module.__file__))

        # 如果无法确定主模块目录（例如作为模块导入时），使用当前模块的目录
        return os.path.dirname(os.path.abspath(__file__))

    def _register_signal_handler(self) -> None:
        """
        注册信号处理程序
        """

        def handle_interrupt(signal_num, frame):
            """处理程序中断信号（如Ctrl+C）"""
            print("按下了Ctrl+C！")
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, handle_interrupt)
        except Exception as e:
            # 信号处理失败时使用标准错误输出，因为logger可能不可用
            print(f"注册信号处理程序失败: {e}", file=sys.stderr)

    def _create_log_dir(self, log_dir: str) -> str:
        """
        确保日志目录存在，如果不存在则创建

        Args:
            log_dir: 日志目录名称

        Returns:
            str: 日志目录的绝对路径
        """
        try:
            log_dir_path = os.path.join(self.program_directory, log_dir)
            pathlib.Path(log_dir_path).mkdir(parents=True, exist_ok=True)
            return log_dir_path
        except Exception as e:
            # 使用标准logging记录错误，因为此时logger可能尚未创建
            import sys
            print(f"创建日志目录失败: {e}", file=sys.stderr)
            # 如果创建失败，使用系统临时目录
            temp_dir = os.path.join(os.getenv("TEMP", os.getcwd()), "app_logs")
            pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)
            return temp_dir

    def _setup_logger(self) -> logging.Logger:
        """
        设置并返回日志记录器

        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(self.config["logger_name"])
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # 防止日志传播到父记录器

        # 清空现有处理器，避免重复添加
        if logger.handlers:
            logger.handlers.clear()

        try:
            # 控制台日志处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.config["console_log_level"])
            console_formatter = logging.Formatter(
                self.config["log_formatter_console"])
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # 文件日志处理器
            log_dir_path = self._create_log_dir(self.config["log_dir"])

            # 生成带日期的日志文件名
            today = datetime.date.today().strftime("%Y-%m-%d")
            log_file_name = self.config["log_file_name"].format(date=today)
            log_file_path = os.path.join(log_dir_path, log_file_name)

            # 根据配置选择合适的日志处理器
            if self.config["log_max_bytes"]:
                # 大小和时间双轮转
                file_handler_kwargs = {
                    "filename": log_file_path,
                    "encoding": "utf-8",
                    "maxBytes": self.config["log_max_bytes"],
                    "backupCount": self.config["log_backup_count"],
                }
                file_handler = RotatingFileHandler(**file_handler_kwargs)
            else:
                # 仅时间轮转
                file_handler_kwargs = {
                    "filename": log_file_path,
                    "encoding": "utf-8",
                    "when": self.config["log_rotation_when"],
                    "interval": self.config["log_rotation_interval"],
                    "backupCount": self.config["log_backup_count"],
                }
                file_handler = TimedRotatingFileHandler(**file_handler_kwargs)

            # 如果启用了备份压缩，添加自定义的后缀名生成器
            if self.config["compress_backups"]:
                original_namer = file_handler.namer
                file_handler.namer = lambda name: self._namer_with_compression(
                    name, original_namer
                )

                # 为TimedRotatingFileHandler添加自定义的清理函数
                if hasattr(file_handler, 'rotator'):
                    original_rotator = file_handler.rotator
                    file_handler.rotator = lambda source, dest: self._rotator_with_compression(
                        source, dest, original_rotator
                    )

            file_handler.setLevel(self.config["file_log_level"])
            file_formatter = logging.Formatter(
                self.config["log_formatter_file"])
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        except Exception as e:
            # 此时logger已建立，可以使用它记录错误
            logger.error(f"设置日志处理器失败: {e}")

        return logger

    def _namer_with_compression(self, name: str, original_namer: Optional[Callable] = None) -> str:
        """
        自定义的日志文件命名器，用于压缩备份日志

        Args:
            name: 原始日志文件名
            original_namer: 原始的命名器函数

        Returns:
            str: 处理后的日志文件名
        """
        # 使用原始命名器生成新名称
        if original_namer:
            new_name = original_namer(name)
        else:
            new_name = name + ".1"

        # 如果文件存在且不是压缩文件，则压缩
        if os.path.exists(name) and not name.endswith(".zip"):
            try:
                zip_name = new_name + ".zip"
                # 确保目标目录存在
                zip_dir = os.path.dirname(zip_name)
                os.makedirs(zip_dir, exist_ok=True)

                with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(name, os.path.basename(name))
                os.remove(name)  # 删除原文件
                return zip_name
            except Exception as e:
                # 记录压缩失败的信息，但继续使用原始命名
                # 不在此处使用logger，因为可能还在日志轮转过程中
                print(f"压缩日志文件失败: {e}", file=sys.stderr)
                # 压缩失败，使用原始命名
                if os.path.exists(name):
                    os.rename(name, new_name)

        return new_name

    def _rotator_with_compression(self, source: str, dest: str, original_rotator: Optional[Callable] = None) -> None:
        """
        带压缩功能的日志轮转器

        Args:
            source: 源文件路径
            dest: 目标文件路径
            original_rotator: 原始轮转器函数
        """
        # 先执行原始轮转操作（如果有）
        if original_rotator:
            original_rotator(source, dest)
        else:
            # 如果没有原始轮转器，手动移动文件
            if os.path.exists(source):
                os.rename(source, dest)

        # 压缩轮转后的文件
        if self.config["compress_backups"] and os.path.exists(dest) and not dest.endswith(".zip"):
            try:
                zip_dest = dest + ".zip"

                with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(dest, os.path.basename(dest))

                # 删除原始轮转文件
                os.remove(dest)
            except Exception as e:
                # 压缩失败不影响正常的轮转操作
                print(f"压缩轮转日志失败: {e}", file=sys.stderr)

    def _validate_config(self) -> None:
        """
        验证配置参数的有效性
        """
        # 验证日志级别
        console_level = self.config.get("console_log_level", logging.INFO)
        file_level = self.config.get("file_log_level", logging.DEBUG)

        # 尝试转换字符串形式的日志级别
        if isinstance(console_level, str):
            self.config["console_log_level"] = self._get_log_level_from_string(
                console_level)
        elif not isinstance(console_level, int):
            raise ValueError(f"Invalid console log level: {console_level}")

        if isinstance(file_level, str):
            self.config["file_log_level"] = self._get_log_level_from_string(
                file_level)
        elif not isinstance(file_level, int):
            raise ValueError(f"Invalid file log level: {file_level}")

        # 验证日志轮转参数
        rotation_when = self.config.get("log_rotation_when", "D")
        if rotation_when not in ["S", "M", "H", "D", "W0", "W1", "W2", "W3", "W4", "W5", "W6"]:
            raise ValueError(f"Invalid log rotation when: {rotation_when}")

        # 验证其他数值参数
        backup_count = self.config.get("log_backup_count", 180)
        if not isinstance(backup_count, int) or backup_count < 0:
            raise ValueError(f"Invalid log backup count: {backup_count}")

        interval = self.config.get("log_rotation_interval", 1)
        if not isinstance(interval, int) or interval <= 0:
            raise ValueError(f"Invalid log rotation interval: {interval}")

        max_bytes = self.config.get("log_max_bytes", None)
        if max_bytes is not None and (not isinstance(max_bytes, int) or max_bytes <= 0):
            raise ValueError(f"Invalid log max bytes: {max_bytes}")

    def _get_log_level_from_string(self, level_str: str) -> int:
        """
        将字符串形式的日志级别转换为对应的整数值

        Args:
            level_str: 字符串形式的日志级别

        Returns:
            int: 对应的日志级别整数值
        """
        level_map = {
            "NOTSET": logging.NOTSET,
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "WARN": logging.WARN,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
            "FATAL": logging.FATAL,
        }

        upper_level = level_str.upper()
        if upper_level in level_map:
            return level_map[upper_level]
        else:
            raise ValueError(f"Unknown log level string: {level_str}")

    def get_logger(self) -> logging.Logger:
        """
        获取日志记录器实例

        Returns:
            logging.Logger: 日志记录器实例
        """
        return self.logger

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新日志配置并重新初始化日志记录器

        Args:
            config: 要更新的配置字典
        """
        self.config.update(config)
        self.logger = self._setup_logger()

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录信息日志"""
        self.logger.info(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录错误日志"""
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录调试日志"""
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录警告日志"""
        self.logger.warning(msg, *args, **kwargs)

    def exception(self, msg: str = "发生异常", *args: Any, **kwargs: Any) -> None:
        """记录异常信息"""
        self.logger.exception(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录严重错误日志"""
        self.logger.critical(msg, *args, **kwargs)

    def log(self, level: Union[int, str], msg: str, *args: Any, **kwargs: Any) -> None:
        """记录指定级别的日志"""
        self.logger.log(level, msg, *args, **kwargs)


# 创建全局日志实例
log_helper = ULoger()
logger = log_helper.logger


# 简化访问方式
def log_info(msg: str, *args: Any, **kwargs: Any) -> None:
    """记录信息日志"""
    log_helper.info(msg, *args, **kwargs)


def log_error(msg: str, *args: Any, **kwargs: Any) -> None:
    """记录错误日志"""
    log_helper.error(msg, *args, **kwargs)


def log_debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """记录调试日志"""
    log_helper.debug(msg, *args, **kwargs)


def log_warning(msg: str, *args: Any, **kwargs: Any) -> None:
    """记录警告日志"""
    log_helper.warning(msg, *args, **kwargs)


def log_exception(msg: str = "发生异常", *args: Any, **kwargs: Any) -> None:
    """记录异常信息"""
    log_helper.exception(msg, *args, **kwargs)


def log_critical(msg: str, *args: Any, **kwargs: Any) -> None:
    """记录严重错误日志"""
    log_helper.critical(msg, *args, **kwargs)
