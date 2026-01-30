"""
XML报文验证模块

提供各种XML征信报文的有效性检测功能
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Tuple

from .config import Config


def validate_xml_content(file_path: str, xml_dir: str = Config.XML_DIR) -> Tuple[bool, str]:
    """
    检测XML报文是否有效
    
    参数:
        file_path: XML文件名
        xml_dir: XML文件所在目录
    
    返回:
        Tuple[bool, str]: (是否有效, 失效原因)
    """
    full_path = os.path.join(xml_dir, file_path)
    
    # 检查1: 文件是否存在
    if not os.path.exists(full_path):
        return False, "文件不存在"
    
    # 检查2: 文件是否为空
    if os.path.getsize(full_path) == 0:
        return False, "文件为空"
    
    try:
        # 检查3: XML是否可以正常解析
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        # 检查4: 根节点是否存在
        if root is None:
            return False, "XML根节点为空"
        
        # 检查5: 必需字段是否存在且有值
        for field_xpath in Config.REQUIRED_FIELDS:
            element = root.find(field_xpath)
            if element is None:
                return False, f"缺少必需字段: {field_xpath}"
            if element.text is None or element.text.strip() == '':
                return False, f"必需字段为空: {field_xpath}"
        
        # 检查6: 检测报文内容是否为错误/失效状态
        # 检查是否有错误码标签
        error_code = root.find('.//ErrorCode')
        if error_code is not None and error_code.text:
            return False, f"报文包含错误码: {error_code.text}"
        
        # 检查是否有失败状态标识
        status = root.find('.//Status')
        if status is not None and status.text in Config.ERROR_STATUS:
            return False, f"报文状态异常: {status.text}"
        
        # 检查7: 验证报告时间格式是否正确
        report_time = root.find('.//PA01AR01')
        if report_time is not None and report_time.text:
            if not _validate_time_format(report_time.text):
                return False, f"报告时间格式无效: {report_time.text}"
        
        return True, "有效"
        
    except ET.ParseError as e:
        return False, f"XML解析错误: {str(e)}"
    except Exception as e:
        return False, f"未知错误: {str(e)}"


def _validate_time_format(time_str: str) -> bool:
    """
    验证时间格式是否正确
    
    参数:
        time_str: 时间字符串
    
    返回:
        bool: 格式是否有效
    """
    # 提取日期部分
    date_part = time_str.split('T')[0] if 'T' in time_str else time_str
    
    for fmt in Config.SUPPORTED_TIME_FORMATS:
        try:
            if fmt == '%Y-%m-%d':
                datetime.strptime(date_part, fmt)
                return True
            else:
                datetime.strptime(time_str, fmt)
                return True
        except ValueError:
            continue
    
    return False


def validate_xml_structure(xml_root) -> Tuple[bool, str]:
    """
    验证XML结构是否符合征信报文标准
    
    参数:
        xml_root: XML根节点
    
    返回:
        Tuple[bool, str]: (是否有效, 检验结果说明)
    """
    # 检查基本结构
    if xml_root.tag != 'Document':
        return False, f"根节点应为Document，实际为: {xml_root.tag}"
    
    # 检查是否包含个人信息部分
    personal_info = xml_root.find('.//PA01')
    if personal_info is None:
        return False, "缺少个人基本信息部分(PA01)"
    
    return True, "XML结构有效"


def get_validation_summary(xml_dir: str = Config.XML_DIR) -> dict:
    """
    获取目录下所有XML文件的验证摘要
    
    参数:
        xml_dir: XML文件所在目录
    
    返回:
        dict: 验证摘要统计
    """
    if not os.path.exists(xml_dir):
        return {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'error_rate': 0.0,
            'common_errors': []
        }
    
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
    
    valid_count = 0
    error_reasons = []
    
    for xml_file in xml_files:
        is_valid, reason = validate_xml_content(xml_file, xml_dir)
        if is_valid:
            valid_count += 1
        else:
            error_reasons.append(reason)
    
    # 统计常见错误
    from collections import Counter
    common_errors = Counter(error_reasons).most_common(5)
    
    total = len(xml_files)
    invalid_count = total - valid_count
    
    return {
        'total': total,
        'valid': valid_count,
        'invalid': invalid_count,
        'error_rate': (invalid_count / total * 100) if total > 0 else 0,
        'common_errors': common_errors
    }