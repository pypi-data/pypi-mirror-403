"""
配置参数模块

集中管理所有配置参数，便于维护和定制
"""

class Config:
    """配置类：可根据需要修改各项参数"""
    
    # 基础配置
    XML_DIR = 'xml'  # XML文件所在目录
    OUTPUT_FILE = '征信数据解析结果.csv'  # 默认输出文件名
    ENCODING = 'utf-8-sig'  # CSV编码格式
    
    # 报文有效性检测：必需字段列表
    REQUIRED_FIELDS = [
        './/PA01AR01',  # 报告时间
        './/PA01AI01',  # 报告编号
    ]
    
    # 可选但建议存在的字段
    OPTIONAL_FIELDS = [
        './/PA01BQ01',  # 姓名
        './/PA01BI01',  # 身份证号
        './/PB01AR01',  # 出生日期
    ]
    
    # 错误状态关键词
    ERROR_STATUS = ['FAILED', 'ERROR', 'INVALID']
    
    # 支持的时间格式
    SUPPORTED_TIME_FORMATS = [
        '%Y-%m-%dT%H:%M:%S',  # 标准格式
        '%Y-%m-%d %H:%M:%S',  # 空格分隔
        '%Y-%m-%d',           # 仅日期
    ]
    
    # 进度条配置
    PROGRESS_DESC = "处理进度"
    VALIDATION_DESC = "检测失效报文"
    
    # 输出格式配置
    MAX_DISPLAY_INVALID = 10  # 最多显示的失效文件数量
    SEPARATOR_LENGTH = 60     # 分隔线长度