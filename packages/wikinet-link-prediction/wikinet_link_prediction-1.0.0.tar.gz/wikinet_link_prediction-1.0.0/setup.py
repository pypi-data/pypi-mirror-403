#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README内容
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# 读取requirements.txt
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# 获取版本号
def get_version():
    version_file = os.path.join('.', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '1.0.0'

setup(
    name='wikinet_link_prediction',
    version=get_version(),
    author='inneedloveBu',
    author_email='indeedlove@foxmail.com',
    description='WikiLinks Graph Neural Network for Link Prediction',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/inneedloveBu/wikinet-link-prediction',
    
    # 包发现
    packages=find_packages(include=['wikinet', 'wikinet.*']),
    include_package_data=True,
    
    # 依赖
    install_requires=requirements,
    
    # 可选依赖（额外功能）
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'visualization': [
            'seaborn>=0.12.0',
            'plotly>=5.14.0',
            'networkx>=3.0',
        ],
        'gpu': [
            'torch>=2.0.0',
            'torch-geometric>=2.3.0',
        ]
    },
    
    # Python版本要求
    python_requires='>=3.8',
    
    # 分类信息
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    
    # 关键词
    keywords=['gnn', 'graph-neural-networks', 'link-prediction', 'machine-learning', 'pytorch'],
    
    # 项目URLs
    project_urls={
        'Bug Reports': 'https://github.com/inneedloveBu/wikinet-link-prediction/issues',
        'Source': 'https://github.com/inneedloveBu/wikinet-link-prediction',
        'Documentation': 'https://github.com/inneedloveBu/wikinet-link-prediction/wiki',
    },
    
    # 入口点（命令行工具）
    entry_points={
        'console_scripts': [
            'wikinet-train=wikinet.cli:train_command',
            'wikinet-evaluate=wikinet.cli:evaluate_command',
            'wikinet-predict=wikinet.cli:predict_command',
            'wikinet-visualize=wikinet.cli:visualize_command',
        ],
    },
    
    # 许可证
    license='MIT',
)