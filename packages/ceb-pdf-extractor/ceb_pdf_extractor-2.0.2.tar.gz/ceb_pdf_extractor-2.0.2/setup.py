#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup script for ceb-pdf-extractor package."""

import os
import sys
from setuptools import setup, find_packages

# 检查Python版本
if sys.version_info < (3, 7):
    sys.exit("Python 3.7 or higher is required.")


# 获取包版本
def get_version():
    """Get version from package __init__.py"""
    with open(os.path.join("ceb_pdf_extractor", "__init__.py"), "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                # __version__ = "2.0.2"
                return line.split("=")[1].strip().strip('"').strip("'")
    return "2.0.2"


# 读取README文件
def read_readme():
    """Read README file for long description."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "光大银行PDF对账单提取工具 - 支持五种不同版式的对账单提取"


# 读取requirements.txt
def read_requirements():
    """Read requirements from requirements.txt."""
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return ["PyMuPDF>=1.24.0", "openpyxl>=3.1.2"]


# 包信息
NAME = "ceb-pdf-extractor"
VERSION = get_version()
DESCRIPTION = "光大银行PDF对账单提取工具 - 支持五种不同版式的对账单提取"
LONG_DESCRIPTION = read_readme()
LONG_DESCRIPTION_CONTENT_TYPE = "text/markdown"
URL = "https://github.com/liangjingcheng/CEBBANK-statement-cleaning"
AUTHOR = "梁京成"
AUTHOR_EMAIL = "2046175864@qq.com"
LICENSE = "MIT"
PYTHON_REQUIRES = ">=3.7"
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Financial and Insurance Industry",
    "Intended Audience :: End Users/Desktop",
    "Intended Audience :: Developers",
    "Topic :: Office/Business :: Financial",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS :: MacOS X",
]
KEYWORDS = [
    "bank", "pdf", "extractor", "ceb", "excel",
    "光大银行", "对账单", "PDF解析", "表格提取",
    "financial", "document", "parser"
]
PROJECT_URLS = {
    "Homepage": "https://github.com/yourusername/ceb-pdf-extractor",
    "Documentation": "https://github.com/yourusername/ceb-pdf-extractor/wiki",
    "Bug Reports": "https://github.com/yourusername/ceb-pdf-extractor/issues",
    "Source Code": "https://github.com/yourusername/ceb-pdf-extractor",
    "Changelog": "https://github.com/yourusername/ceb-pdf-extractor/blob/main/CHANGELOG.md",
}

# 安装依赖
INSTALL_REQUIRES = read_requirements()

# 测试依赖（开发时使用）
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "mypy>=0.990",
        "twine>=4.0.0",
        "wheel>=0.37.0",
        "build>=0.9.0",
    ],
    "test": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
    ],
}

# 入口点（命令行工具）
ENTRY_POINTS = {
    "console_scripts": [
        "ceb-account-query=ceb_pdf_extractor.cli:account_query_main",
        "ceb-account-query-other=ceb_pdf_extractor.cli:account_query_other_main",
        "ceb-personal=ceb_pdf_extractor.cli:personal_main",
        "ceb-company=ceb_pdf_extractor.cli:company_main",
        "ceb-nowatermark=ceb_pdf_extractor.cli:nowatermark_main",
        "ceb-extractor=ceb_pdf_extractor.cli:main",
    ],
}

# 包数据文件
PACKAGE_DATA = {
    "ceb_pdf_extractor": [],  # 如果有数据文件可以在这里添加
}

setup(
    # 基本信息
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,

    # 作者信息
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,

    # 项目信息
    url=URL,
    project_urls=PROJECT_URLS,
    license=LICENSE,
    platforms="any",

    # 包配置
    packages=find_packages(include=["ceb_pdf_extractor", "ceb_pdf_extractor.*"]),
    package_dir={"ceb_pdf_extractor": "ceb_pdf_extractor"},
    include_package_data=True,
    package_data=PACKAGE_DATA,
    zip_safe=False,

    # 依赖
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,

    # 分类
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,

    # 入口点
    entry_points=ENTRY_POINTS,

    # 其他
    scripts=[],  # 如果有独立脚本可以在这里添加
    data_files=[],  # 如果有数据文件可以在这里添加

    # 配置
    options={
        "bdist_wheel": {
            "universal": False,  # 不是纯Python包（因为有二进制依赖）
        },
    },

    # 测试
    test_suite="tests",
    tests_require=EXTRAS_REQUIRE["test"],
)

if __name__ == "__main__":
    # 打印构建信息
    print(f"Building {NAME} version {VERSION}")
    print(f"Python {sys.version}")
    print(f"Platform: {sys.platform}")