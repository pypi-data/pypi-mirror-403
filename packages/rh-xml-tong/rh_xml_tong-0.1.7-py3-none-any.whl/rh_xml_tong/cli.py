"""
命令行接口
"""

import argparse
import sys
import os
from pathlib import Path

from . import __version__
from .core import quick_process, get_invalid_files_report, get_processing_statistics


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description="rh-xml-tong - 人行XML征信数据处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  rh-xml-tong process xml/ output.csv          # 处理XML文件
  rh-xml-tong validate xml/                   # 验证XML文件
  rh-xml-tong stats xml/                      # 显示统计信息
  
更多信息请访问: https://github.com/yourusername/rh-xml-tong
        """
    )
    
    parser.add_argument('--version', action='version', version=f'rh-xml-tong {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # process命令
    process_parser = subparsers.add_parser('process', help='处理XML文件')
    process_parser.add_argument('xml_dir', help='XML文件目录')
    process_parser.add_argument('output_file', nargs='?', default='征信数据解析结果.csv', help='输出CSV文件路径')
    process_parser.add_argument('--no-progress', action='store_true', help='不显示进度条')
    process_parser.add_argument('--no-save', action='store_true', help='不保存CSV文件')
    
    # validate命令
    validate_parser = subparsers.add_parser('validate', help='验证XML文件')
    validate_parser.add_argument('xml_dir', help='XML文件目录')
    validate_parser.add_argument('--save-report', help='保存验证报告到指定文件')
    
    # stats命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.add_argument('xml_dir', help='XML文件目录')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == 'process':
            return handle_process(args)
        elif args.command == 'validate':
            return handle_validate(args)
        elif args.command == 'stats':
            return handle_stats(args)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        return 1
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1


def handle_process(args):
    """处理process命令"""
    if not os.path.exists(args.xml_dir):
        print(f"❌ 错误: 目录不存在 {args.xml_dir}")
        return 1
    
    print(f"🚀 开始处理 {args.xml_dir}")
    
    df, stats = quick_process(
        xml_dir=args.xml_dir,
        output_file=args.output_file if not args.no_save else None
    )
    
    if not df.empty:
        print(f"✅ 处理完成!")
        print(f"   成功处理: {stats['valid']} 个文件")
        print(f"   跳过失效: {stats['invalid']} 个文件")
        if not args.no_save:
            print(f"   输出文件: {args.output_file}")
    else:
        print("⚠️ 没有成功处理任何文件")
        return 1
    
    return 0


def handle_validate(args):
    """处理validate命令"""
    if not os.path.exists(args.xml_dir):
        print(f"❌ 错误: 目录不存在 {args.xml_dir}")
        return 1
    
    print(f"🔍 开始验证 {args.xml_dir}")
    
    df_invalid = get_invalid_files_report(args.xml_dir)
    
    if df_invalid.empty:
        print("✅ 所有XML文件均有效!")
    else:
        print(f"⚠️ 发现 {len(df_invalid)} 个失效文件:")
        print(df_invalid.to_string(index=False))
        
        if args.save_report:
            df_invalid.to_csv(args.save_report, index=False, encoding='utf-8-sig')
            print(f"📄 验证报告已保存到: {args.save_report}")
    
    return 0


def handle_stats(args):
    """处理stats命令"""
    if not os.path.exists(args.xml_dir):
        print(f"❌ 错误: 目录不存在 {args.xml_dir}")
        return 1
    
    print(f"📊 统计信息: {args.xml_dir}")
    print("="*50)
    
    stats = get_processing_statistics(args.xml_dir)
    
    if 'error' in stats:
        print(f"❌ {stats['error']}")
        return 1
    
    print(f"📁 总文件数: {stats['total_files']}")
    print(f"✅ 预计有效: {stats['estimated_valid']}")
    print(f"⚠️ 预计无效: {stats['estimated_invalid']}")
    print(f"📝 {stats['message']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())