#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    :2026/1/28 16:17
# @Author  : Divine
# @Site    :
# @File    :setup.py.py
# @Software: PyCharm
import setuptools

# 核心修改：读取文件时指定 encoding='utf-8'
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="apiEngineDivine",  # 替换为实际项目名
    version="0.1.1",   # 替换为实际版本号
    author="Divine",  # 替换为实际作者名
    author_email="294491521@qq.com",
    description="this is a api engine",
    long_description=long_description,  # 使用上面读取的内容
    long_description_content_type="text/markdown",  # 建议添加这行，指定md格式
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",  # 对应Apache 2.0协议
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',  # 根据项目需求调整Python版本
    install_requires=[
        "requests>=2.31.0",  # 示例：HTTP 请求库（>=指定最低版本）
        "jmespath>=0.10.0",  # 示例：数据校验库（支持 >=2.0 的所有版本）
        "jsonpath>=0.82.2",  # 示例：如果你的引擎基于 FastAPI（可选，根据实际需求）
        "Faker>=38.2.0",  # 示例：ASGI 服务器（用于运行 API，可选）
        "PyMySQL>= 1.1.2"  # 示例：ASGI 服务器（用于运行 API，可选）
    ]
)
