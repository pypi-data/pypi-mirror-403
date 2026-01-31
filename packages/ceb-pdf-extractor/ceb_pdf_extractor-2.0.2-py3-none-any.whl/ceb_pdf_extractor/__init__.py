"""
光大银行PDF对账单提取工具包

提供五种PDF提取器：
1. PDFTableExtractor_AccountQuery - 处理账户交易明细查询PDF（从"借贷"开始）
2. PDFTableExtractor_AccountQuery_other - 处理账户交易明细查询PDF（从"交易对方名"开始）
3. PDFTableExtractor_Personal - 处理个人版对账单PDF
4. PDFTableExtractor_Company - 处理公司版对账单PDF
5. PDFTableExtractor_NoWatermark - 处理无水印版对账单PDF

版本: 2.0.2
作者: 梁京成
许可证: MIT
"""

__version__ = "2.0.2"
__author__ = "梁京成"
__email__ = "2046175864@qq.com"
__license__ = "MIT"
__description__ = "光大银行PDF对账单提取工具 - 支持五种不同版式的对账单提取"
__url__ = "https://github.com/liangjingcheng/CEBBANK-statement-cleaning"

# 导入所有提取器类
from .account_query import PDFTableExtractor_AccountQuery
from .account_query_other import PDFTableExtractor_AccountQuery_other
from .personal import PDFTableExtractor_Personal
from .company import PDFTableExtractor_Company
from .nowatermark import PDFTableExtractor_NoWatermark

# 导入便捷函数
from .account_query import process_pdf_to_multiple_excel, process_pdf_to_single_excel
from .account_query_other import process_pdf_to_multiple_excel as process_pdf_to_multiple_excel_other
from .account_query_other import process_pdf_to_single_excel as process_pdf_to_single_excel_other

# 导入工具函数
from .cli import detect_pdf_type, create_extractor, process_multiple_files

# 定义包的公开API
__all__ = [
    # 核心类
    "PDFTableExtractor_AccountQuery",
    "PDFTableExtractor_AccountQuery_other",
    "PDFTableExtractor_Personal",
    "PDFTableExtractor_Company",
    "PDFTableExtractor_NoWatermark",

    # 便捷函数
    "process_pdf_to_multiple_excel",
    "process_pdf_to_single_excel",
    "process_pdf_to_multiple_excel_other",
    "process_pdf_to_single_excel_other",

    # 工具函数
    "detect_pdf_type",
    "create_extractor",
    "process_multiple_files",

    # 元数据
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
    "__url__",
]

# 可选：包初始化代码
def get_version():
    """获取包版本信息"""
    return __version__

def get_author_info():
    """获取作者信息"""
    return {
        "author": __author__,
        "email": __email__,
        "url": __url__
    }

def print_info():
    """打印包信息"""
    info = f"""
光大银行PDF对账单提取工具
版本: {__version__}
作者: {__author__} ({__email__})
描述: {__description__}
GitHub: {__url__}
许可证: {__license__}

支持的提取器类型:
1. PDFTableExtractor_AccountQuery - 账户交易明细查询PDF（从"借贷"开始）
2. PDFTableExtractor_AccountQuery_other - 账户交易明细查询PDF（从"交易对方名"开始）
3. PDFTableExtractor_Personal - 个人版对账单PDF
4. PDFTableExtractor_Company - 公司版对账单PDF
5. PDFTableExtractor_NoWatermark - 无水印版对账单PDF

使用示例:
    from ceb_pdf_extractor import PDFTableExtractor_AccountQuery, PDFTableExtractor_Personal
    
    # 处理账户查询PDF
    extractor = PDFTableExtractor_AccountQuery("path/to/file.pdf", output_mode="multiple")
    result = extractor.process()
    
    # 处理个人版PDF
    extractor = PDFTableExtractor_Personal("path/to/file.pdf", export_type="split")
    result = extractor.process()
    """
    print(info)

# 可选：添加包级别的配置
DEFAULT_CONFIG = {
    "account_query": {
        "target_font": "FangSong",
        "target_size": 10.0,
        "size_tolerance": 0.2,
        "row_tolerance": 13.359375,
        "col_tolerance": 30.0,
    },
    "account_query_other": {
        "target_font": "FangSong",
        "target_size": 10.0,
        "size_tolerance": 0.2,
        "row_tolerance": 13.359375,
        "col_tolerance": 30.0,
    },
    "personal": {
        "target_size": 6.0,
        "size_tolerance": 0.2,
        "row_tolerance": 5.0,
        "col_tolerance": 30.0,
    },
    "company": {
        "target_size": 6.0,
        "size_tolerance": 0.2,
        "row_tolerance": 5.0,
        "col_tolerance": 30.0,
    },
    "nowatermark": {
        "target_size": 6.0,
        "size_tolerance": 0.2,
        "row_tolerance": 5.0,
        "col_tolerance": 30.0,
    }
}

# 可选：验证环境
def check_environment():
    """检查运行环境是否满足要求"""
    import sys

    requirements = {
        "Python版本": f">=3.7 (当前: {sys.version.split()[0]})",
        "PyMuPDF": ">=1.23.0",
        "openpyxl": ">=3.1.0"
    }

    print("环境检查:")
    print("-" * 40)

    # 检查Python版本
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 7:
        print(f"✅ Python版本: {sys.version.split()[0]}")
    else:
        print(f"❌ Python版本: {sys.version.split()[0]} (需要 >=3.7)")

    # 检查依赖包
    try:
        import fitz
        print(f"✅ PyMuPDF: {fitz.__doc__.split()[1] if fitz.__doc__ else '已安装'}")
    except ImportError:
        print("❌ PyMuPDF: 未安装")

    try:
        import openpyxl
        print(f"✅ openpyxl: {openpyxl.__version__}")
    except ImportError:
        print("❌ openpyxl: 未安装")

    print("-" * 40)