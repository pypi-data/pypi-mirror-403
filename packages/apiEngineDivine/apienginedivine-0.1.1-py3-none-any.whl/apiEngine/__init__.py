#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    :2025/12/10 9:26
# @Author  : Divine
# @Site    :
# @File    :__init__.py.py
# @Software: PyCharm
"""
Copyright [2026] [copyright Divine]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# my_api_engine/__init__.py
# my_api_engine/__init__.py
from ._execute_case import TestExecutor


# 对外唯一暴露的公开方法
def run_case(test_env_global: dict, db_config: list, suite_data: dict):
    """
    对外公开的 API 调用方法
    :param params: dict，API 请求参数（需包含 api_key）
    :return: dict，处理后的响应结果
    """
    # 可在此处添加参数预处理、异常封装等，进一步隔离核心逻辑
    try:
        run_case = TestExecutor(test_env_global=test_env_global, db_config=db_config)._execute_test_suite(
            suite_data=suite_data)
        return run_case
    except Exception as e:
        return {"code": 500, "error": str(e)}


# 关键：控制 from my_api_engine import * 时只导出 call_api
__all__ = ["run_case"]


