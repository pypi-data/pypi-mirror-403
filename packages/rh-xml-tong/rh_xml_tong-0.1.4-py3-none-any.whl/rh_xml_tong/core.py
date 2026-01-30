"""
核心处理模块

提供XML征信数据的解析、批量处理等核心功能
"""

import pandas as pd
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List, Optional, Tuple

from .config import Config
from .validator import validate_xml_content
from .utils import (
    element_to_dict, 
    safe_get_text, 
    extract_date_from_datetime,
    convert_dict_to_json_string,
    print_processing_header,
    print_invalid_files_summary,
    create_summary_report,
    validate_output_path
)


def parse_single_xml(file_path: str, xml_dir: str = Config.XML_DIR) -> Optional[Dict]:
    """
    解析单个XML文件（已通过有效性检测）
    
    参数:
        file_path: XML文件名
        xml_dir: XML文件所在目录
    
    返回:
        Dict: 解析后的数据字典，失败返回None
    """
    file_name = os.path.splitext(file_path)[0]
    full_path = os.path.join(xml_dir, file_path)
    
    try:
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        # 提取基本信息
        report_no = root.find('.//PA01AI01')
        name = root.find('.//PA01BQ01')
        report_time = root.find('.//PA01AR01')
        
        report_time_str = safe_get_text(report_time)
        time_modified = extract_date_from_datetime(report_time_str)
        
        # 将整个Document转换为JSON
        document = element_to_dict(root)
        content_str = convert_dict_to_json_string({'Document': document})
        
        return {
            '用户id': file_name,
            '报告编号': safe_get_text(report_no),
            '姓名': safe_get_text(name),
            '报告时间': report_time_str,
            '报文内容': content_str,
            '报告时间修改': time_modified
        }
        
    except Exception as e:
        print(f"解析{file_path}时出错: {str(e)}")
        return None


def process_all_xml_files(
    xml_dir: str = Config.XML_DIR,
    output_file: str = Config.OUTPUT_FILE,
    save_csv: bool = True,
    show_progress: bool = True,
    validate_output: bool = True
) -> Tuple[pd.DataFrame, Dict]:
    """
    批量处理所有XML文件，自动检测并跳过失效报文
    
    参数:
        xml_dir: XML文件所在目录
        output_file: 输出CSV文件名
        save_csv: 是否保存为CSV文件
        show_progress: 是否显示进度条
        validate_output: 是否验证输出路径
    
    返回:
        Tuple[DataFrame, Dict]: (结果DataFrame, 处理统计信息)
    """
    # 验证输入参数
    if not os.path.exists(xml_dir):
        raise FileNotFoundError(f"XML目录不存在: {xml_dir}")
    
    if validate_output and save_csv:
        if not validate_output_path(output_file):
            raise ValueError(f"输出路径无效: {output_file}")
    
    # 获取所有XML文件
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
    
    if not xml_files:
        print(f"⚠️ 在目录 {xml_dir} 中未找到任何XML文件")
        return pd.DataFrame(), {
            'total': 0, 'valid': 0, 'invalid': 0, 'parse_error': 0, 'invalid_files': []
        }
    
    print_processing_header(xml_dir, len(xml_files))
    
    # 统计信息
    stats = {
        'total': len(xml_files),
        'valid': 0,
        'invalid': 0,
        'parse_error': 0,
        'invalid_files': [],  # 记录失效文件详情
    }
    
    all_data = []
    iterator = tqdm(xml_files, desc=Config.PROGRESS_DESC) if show_progress else xml_files
    
    for xml_file in iterator:
        # 第一步：检测报文有效性
        is_valid, reason = validate_xml_content(xml_file, xml_dir)
        
        if not is_valid:
            stats['invalid'] += 1
            stats['invalid_files'].append({
                'file': xml_file,
                'reason': reason
            })
            continue
        
        # 第二步：解析有效的XML文件
        result = parse_single_xml(xml_file, xml_dir)
        
        if result:
            all_data.append(result)
            stats['valid'] += 1
        else:
            stats['parse_error'] += 1
    
    # 创建DataFrame
    df_result = pd.DataFrame(all_data)
    
    # 打印统计信息
    print(create_summary_report(stats))
    
    # 显示失效文件详情
    if stats['invalid_files']:
        print_invalid_files_summary(stats['invalid_files'], Config.MAX_DISPLAY_INVALID)
    
    # 保存CSV
    if save_csv and not df_result.empty:
        try:
            df_result.to_csv(output_file, index=False, encoding=Config.ENCODING)
            print(f"\n💾 数据已保存到: {output_file}")
            print(f"   共 {len(df_result)} 条记录")
        except Exception as e:
            print(f"❌ 保存文件失败: {str(e)}")
    
    return df_result, stats


def quick_process(xml_dir: str = 'xml', output_file: str = '征信数据解析结果.csv') -> Tuple[pd.DataFrame, Dict]:
    """
    快捷处理函数 - 一行代码完成所有处理
    
    使用示例:
        df, stats = quick_process('xml', '输出文件.csv')
    
    参数:
        xml_dir: XML文件所在目录
        output_file: 输出CSV文件名
    
    返回:
        Tuple[DataFrame, Dict]: (结果DataFrame, 处理统计信息)
    """
    return process_all_xml_files(xml_dir, output_file)


def get_invalid_files_report(xml_dir: str = Config.XML_DIR) -> pd.DataFrame:
    """
    单独检测并返回所有失效文件的详细报告
    
    参数:
        xml_dir: XML文件所在目录
    
    返回:
        DataFrame: 包含失效文件名和失效原因的报告
    """
    if not os.path.exists(xml_dir):
        print(f"⚠️ 目录不存在: {xml_dir}")
        return pd.DataFrame(columns=['文件名', '失效原因'])
    
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
    
    if not xml_files:
        print(f"⚠️ 在目录 {xml_dir} 中未找到任何XML文件")
        return pd.DataFrame(columns=['文件名', '失效原因'])
    
    invalid_report = []
    
    for xml_file in tqdm(xml_files, desc=Config.VALIDATION_DESC):
        is_valid, reason = validate_xml_content(xml_file, xml_dir)
        if not is_valid:
            invalid_report.append({
                '文件名': xml_file,
                '失效原因': reason
            })
    
    df_invalid = pd.DataFrame(invalid_report)
    
    if df_invalid.empty:
        print("✅ 所有XML文件均有效！")
    else:
        print(f"🔍 发现 {len(df_invalid)} 个失效文件")
    
    return df_invalid


def process_single_file(file_path: str, xml_dir: str = Config.XML_DIR) -> Optional[Dict]:
    """
    处理单个XML文件（包含验证和解析）
    
    参数:
        file_path: XML文件名
        xml_dir: XML文件所在目录
    
    返回:
        Dict: 处理结果，包含数据和状态信息
    """
    # 验证文件
    is_valid, reason = validate_xml_content(file_path, xml_dir)
    
    if not is_valid:
        return {
            'status': 'invalid',
            'reason': reason,
            'data': None
        }
    
    # 解析文件
    data = parse_single_xml(file_path, xml_dir)
    
    if data is None:
        return {
            'status': 'parse_error',
            'reason': '解析失败',
            'data': None
        }
    
    return {
        'status': 'success',
        'reason': '处理成功',
        'data': data
    }


def get_processing_statistics(xml_dir: str = Config.XML_DIR) -> Dict:
    """
    获取目录处理统计信息（不执行实际处理）
    
    参数:
        xml_dir: XML文件所在目录
    
    返回:
        Dict: 统计信息
    """
    if not os.path.exists(xml_dir):
        return {'error': f'目录不存在: {xml_dir}'}
    
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
    
    if not xml_files:
        return {
            'total_files': 0,
            'estimated_valid': 0,
            'estimated_invalid': 0,
            'message': '未找到XML文件'
        }
    
    # 快速检测前10个文件以估算比例
    sample_size = min(10, len(xml_files))
    valid_count = 0
    
    for i in range(sample_size):
        is_valid, _ = validate_xml_content(xml_files[i], xml_dir)
        if is_valid:
            valid_count += 1
    
    valid_ratio = valid_count / sample_size
    total_files = len(xml_files)
    
    return {
        'total_files': total_files,
        'estimated_valid': int(total_files * valid_ratio),
        'estimated_invalid': int(total_files * (1 - valid_ratio)),
        'sample_size': sample_size,
        'message': f'基于{sample_size}个样本文件的估算'
    }