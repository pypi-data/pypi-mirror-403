"""
rh_xml_tong - 人行XML征信数据处理库

一个专门用于解析和处理中国人民银行XML格式征信数据的Python库。
支持批量处理、自动验证、智能错误处理等功能。

作者: Tong
版本: 0.1.4
"""

__version__ = "0.1.7"
__author__ = "Tong"
__email__ = "litong0923@gmail.com"
__description__ = "专业的中国人民银行XML征信数据处理工具库，支持批量处理、智能验证、错误检测，工作日常用到，因此封装为库！"

# 导出主要功能
from .core import (
    process_all_xml_files,
    quick_process,
    parse_single_xml,
    get_invalid_files_report
)
from .validator import validate_xml_content
from .utils import element_to_dict
from .config import Config

__all__ = [
    'process_all_xml_files',
    'quick_process',
    'parse_single_xml', 
    'get_invalid_files_report',
    'validate_xml_content',
    'element_to_dict',
    'Config'
]
