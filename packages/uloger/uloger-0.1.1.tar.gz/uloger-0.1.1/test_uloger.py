#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试uloger模块的导入和使用
"""

import os
import sys

# 获取父目录路径（项目根目录）
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加父目录到Python路径，确保可以导入uloger
sys.path.insert(0, parent_dir)

try:
    # 测试基本导入
    from uloger import logger, logging
    print("✅ 成功导入 logger")
    print("✅ 成功导入 logging 模块")
    print(f"   确认logging是标准模块: {'logging' in sys.modules}")
    
    # 测试简化函数导入
    from uloger import log_info, log_debug, log_warning, log_error, log_critical, log_exception
    print("✅ 成功导入所有简化函数")
    
    # 测试ULoger类导入
    from uloger import ULoger
    print("✅ 成功导入 ULoger 类")
    
    # 测试日志功能
    logger.info("这是一条测试信息日志")
    logger.debug("这是一条测试调试日志")
    logger.warning("这是一条测试警告日志")
    print("✅ 成功使用 logger 记录日志")
    
    # 测试简化函数
    log_info("这是一条使用简化函数的测试信息日志")
    log_debug("这是一条使用简化函数的测试调试日志")
    print("✅ 成功使用简化函数记录日志")
    
    # 测试自定义配置
    custom_config = {
        "log_dir": "test_logs",
        "log_file_name": "test_{date}.log",
        "log_backup_count": 5
    }
    custom_logger = ULoger(custom_config).get_logger()
    custom_logger.info("这是一条使用自定义配置的测试日志")
    print("✅ 成功使用自定义配置创建日志记录器")
    
    print("\n🎉 所有测试通过！uloger模块可以正常使用。")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 测试过程中发生错误: {e}")
    sys.exit(1)