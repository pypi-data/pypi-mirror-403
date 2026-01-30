"""
rh_xml_tong 安装配置文件
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    return "人行XML征信数据处理库"

# 读取版本号
def read_version():
    init_path = os.path.join(os.path.dirname(__file__), "rh_xml_tong", "__init__.py")
    with open(init_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="rh-xml-tong",
    version=read_version(),
    author="Tong",
    author_email="litong0923@gmail.com",
    description="专业的中国人民银行XML征信数据处理工具库，支持批量处理、智能验证、错误检测，工作日常用到，因此封装为库！",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://tongblog-61e.pages.dev/",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/rh-xml-tong/issues",
        "Documentation": "https://github.com/yourusername/rh-xml-tong/wiki",
        "Source Code": "https://github.com/yourusername/rh-xml-tong",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "tqdm>=4.50.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "twine>=3.0",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords="xml credit finance parser 征信 解析 人民银行 风控 金融",
    license="MIT",
    entry_points={
        "console_scripts": [
            "rh-xml-tong=rh_xml_tong.cli:main",
        ],
    },
)