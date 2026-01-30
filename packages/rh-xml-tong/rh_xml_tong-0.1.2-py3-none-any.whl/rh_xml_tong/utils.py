"""
工具函数模块

提供XML处理、数据转换等通用工具函数
"""

from typing import Dict, Any
import json


def element_to_dict(element) -> Dict[str, Any]:
    """
    递归将XML元素转换为字典
    相同标签多次出现时自动转换为列表
    
    参数:
        element: XML元素节点
    
    返回:
        Dict: 转换后的字典
    """
    result = {}
    for child in element:
        if len(child) == 0:  # 叶子节点
            result[child.tag] = child.text
        else:  # 有子节点
            child_dict = element_to_dict(child)
            if child.tag in result:
                # 标签已存在，转换为列表
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
    return result


def safe_get_text(element) -> str:
    """
    安全获取XML元素的文本内容
    
    参数:
        element: XML元素或None
    
    返回:
        str: 文本内容，如果元素为None或无文本则返回空字符串
    """
    if element is None:
        return ""
    return element.text if element.text is not None else ""


def extract_date_from_datetime(datetime_str: str) -> str:
    """
    从完整时间字符串中提取日期部分
    
    参数:
        datetime_str: 时间字符串，如 "2024-09-10T09:05:47"
    
    返回:
        str: 日期部分，如 "2024-09-10"
    """
    if not datetime_str:
        return ""
    return datetime_str.split('T')[0]


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    
    参数:
        size_bytes: 文件大小（字节）
    
    返回:
        str: 格式化的大小字符串
    """
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f}TB"


def create_summary_report(stats: Dict[str, Any]) -> str:
    """
    创建处理结果摘要报告
    
    参数:
        stats: 统计信息字典
    
    返回:
        str: 格式化的摘要报告
    """
    report = []
    report.append("="*60)
    report.append("📊 处理结果摘要")
    report.append("="*60)
    report.append(f"📁 总文件数: {stats.get('total', 0)}")
    report.append(f"✅ 成功处理: {stats.get('valid', 0)} 个")
    report.append(f"⚠️  跳过失效: {stats.get('invalid', 0)} 个")
    report.append(f"❌ 解析失败: {stats.get('parse_error', 0)} 个")
    
    if stats.get('total', 0) > 0:
        success_rate = stats.get('valid', 0) / stats.get('total', 1) * 100
        report.append(f"📈 成功率: {success_rate:.1f}%")
    
    return "\n".join(report)


def validate_output_path(output_path: str) -> bool:
    """
    验证输出路径是否有效
    
    参数:
        output_path: 输出文件路径
    
    返回:
        bool: 路径是否有效
    """
    import os
    
    # 检查目录是否存在
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except:
            return False
    
    # 检查文件扩展名
    if not output_path.lower().endswith('.csv'):
        return False
    
    return True


def convert_dict_to_json_string(data_dict: Dict, ensure_ascii: bool = False) -> str:
    """
    将字典转换为JSON字符串
    
    参数:
        data_dict: 要转换的字典
        ensure_ascii: 是否确保ASCII编码
    
    返回:
        str: JSON字符串
    """
    return json.dumps(data_dict, ensure_ascii=ensure_ascii, indent=None, separators=(',', ':'))


def print_processing_header(xml_dir: str, file_count: int):
    """
    打印处理开始的标题信息
    
    参数:
        xml_dir: XML目录
        file_count: 文件数量
    """
    print("="*60)
    print("📂 开始处理XML征信数据")
    print("="*60)
    print(f"📁 XML目录: {xml_dir}")
    print(f"📄 发现文件: {file_count} 个")
    print("="*60 + "\n")


def print_invalid_files_summary(invalid_files: list, max_display: int = 10):
    """
    打印失效文件摘要
    
    参数:
        invalid_files: 失效文件列表
        max_display: 最多显示的文件数量
    """
    if not invalid_files:
        return
        
    print(f"\n📋 失效文件详情 (显示前{max_display}个):")
    for item in invalid_files[:max_display]:
        print(f"   - {item['file']}: {item['reason']}")
    
    if len(invalid_files) > max_display:
        print(f"   ... 还有 {len(invalid_files) - max_display} 个失效文件")