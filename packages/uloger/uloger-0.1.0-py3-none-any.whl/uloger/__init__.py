# 导入标准logging模块，方便用户直接从uloger导入使用
import logging

# 从uloger.py导入logger，使得可以直接通过from uloger import logger导入
from .uloger import __version__
from .uloger import logger
from .uloger import log_helper
from .uloger import uloger
from .uloger import log_info, log_error, log_debug, log_warning, log_exception, log_critical

# 导出所有公共接口
__all__ = [
    '__version__',  # 版本信息
    'logging',  # 添加logging模块到导出列表
    'logger',
    'log_helper',
    'uloger',
    'log_info',
    'log_error',
    'log_debug',
    'log_warning',
    'log_exception',
    'log_critical'
]
