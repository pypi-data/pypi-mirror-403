from setuptools import setup, find_packages
import os

# 动态获取版本
try:
    from setuptools_scm import get_version
    version = get_version()
except Exception:
    # 如果无法获取Git版本，则尝试从__init__.py或其他地方获取
    version = "unknown"

# 获取当前目录
current_dir = os.path.abspath(os.path.dirname(__file__))

# 从README.md读取描述信息（如果存在）
try:
    with open(os.path.join(current_dir, 'README.md'), 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "一个灵活的Python日志辅助模块"

setup(
    name="uloger",
    version=version,
    description="一个灵活的Python日志辅助模块",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="pymod",
    author_email="pymod@example.com",
    url="https://gitcode.com/pymod/uloger",  # 项目地址
    # 使用find_packages()自动找到所有包
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires='>=3.6',
    install_requires=[],
    setup_requires=["setuptools_scm"],
)
