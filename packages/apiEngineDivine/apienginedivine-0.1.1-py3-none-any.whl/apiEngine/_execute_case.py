#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    :2026/1/28 10:34
# @Author  : Divine
# @Site    :
# @File    :_execute_case.py
# @Software: PyCharm

import time
from typing import List
from apiEngine.core._database_client import DBClient
from apiEngine.core._test_result import TestResult
from apiEngine.core._basecase import BaseTestCase
import traceback


class TestExecutor:
    """用例执行器"""

    def __init__(self, test_env_global: dict, db_config: list):
        # 保存所有用例执行的结果
        self.results: List[TestResult] = []
        self.summary = {
            "total": 0,  # 统计用例总数
            "success": 0,  # 统计用例成功数
            "fail": 0,  # 统计用例失败数
            "error": 0,  # 统计用例错误数
            "skip": 0,  # 统计用例跳过数
            "duration": 0,  # 用例总执行时长
        }
        self.test_env_global = test_env_global
        # 对数据库连接进行初始化
        self.db = DBClient(db_config)

    def _execute_test_case(self, case_data: dict) -> TestResult:
        """执行单条用例，并收集执行的结果"""
        case_name = case_data.get("name")
        case_id = case_data.get("id")
        # 创建一个执行结果记录器
        result = TestResult(case_name, case_id)
        # 判断用例是否需要跳过执行
        if case_data.get("skip"):
            result.status = "skip"
            result.add_info_log(f"【跳过用例】：{case_name}")
            return result
        # 记录开始执行的时间
        result.start_time = time.time()
        result.add_info_log(f"【开始执行用例】：{case_name}")
        try:
            # 编写用例执行的逻辑
            case_run = BaseTestCase(case_data, result, self.test_env_global, self.db)
            case_run._run()
        except AssertionError as e:
            # 修改用例执行的状态为失败
            result.status = "failed"
            # 记录用例执行的错误信息
            result.error_message = str(e)
            # 获取异常的堆栈信息
            result.traceback = traceback.format_exc()
            result.add_error_log(f"用例{case_name}断言失败，错误信息为：{e}")
        except Exception as e:
            # 说明用例执行过程中出现了错误
            result.status = "error"
            # 记录用例执行的错误信息
            result.error_message = str(e)
            # 获取异常的堆栈信息
            result.traceback = traceback.format_exc()
            result.add_error_log(f"用例{case_name}执行出现错误！，错误信息为：{e}")
        else:
            result.status = "success"
            result.add_info_log(f"【执行通过】：用例{case_name}")
        # 获取执行结束的时间戳
        result.end_time = time.time()
        # 计算执行的时长
        result.duration = result.end_time - result.start_time
        new_api_requests_info = []
        for api_request in result.api_requests_info:
            new_api_requests_info.append({
                "response_body": api_request.response_body,
                "url": api_request.url,
                "method": api_request.method,
                "headers": api_request.headers,
                "params": api_request.params,
                "body": api_request.body,
                "case_id": api_request.case_id,
                "status_code": api_request.status_code,
            })
        result.api_requests_info = new_api_requests_info
        # 返回用例执行的结果
        return result

    def _execute_test_suite(self, suite_data: dict):
        """执行测试套件"""
        # 获取当前时间戳
        start_time = time.time()
        # 记录套件中的用例总数
        self.summary['total'] = len(suite_data.get("cases_list"))
        # 遍历测试套件中所有的测试用例
        for case_data in suite_data.get("cases_list"):
            # 执行遍历出来的用例
            result = self._execute_test_case(case_data)
            # 保存执行结果
            self.results.append(result)
            # 判断执行的状态信息
            if result.status == "success":
                self.summary['success'] += 1
            elif result.status == "failed":
                self.summary['fail'] += 1
            elif result.status == "error":
                self.summary['error'] += 1
            elif result.status == "skip":
                self.summary['skip'] += 1
        end_time = time.time()
        # 获取执行完的时间戳
        self.summary['duration'] = end_time - start_time

        # 获取执行完的数据，进行返回
        return {
            "results": self.results,
            "summary": self.summary
        }

    def _execute_test_task(self, task_data: dict):
        """执行测试任务的方法
        Args:
            task_data (dict): 测试任务数据，包含任务信息和套件列表
                格式: {
                    "id": 任务ID,
                    "task_name": "任务名称",
                    "description": "任务描述",
                    "type": "api",
                    "suites_list": [
                        {
                            "id": 套件ID,
                            "suite_name": "套件名称",
                            "cases_list": [用例数据列表]
                        }
                    ]
                }
        Returns:
            dict: 任务执行结果，包含所有套件的执行结果和统计信息
        """
        # 获取任务开始时间
        task_start_time = time.time()

        # 初始化任务级别的统计信息
        task_summary = {
            "total_suites": 0,
            "total_cases": 0,
            "success_cases": 0,
            "failed_cases": 0,
            "error_cases": 0,
            "skip_cases": 0,
            "duration": 0,
        }

        # 存储所有套件的执行结果
        suite_results = []

        # 获取任务中的套件列表
        suites_list = task_data.get("suites_list", [])
        task_summary["total_suites"] = len(suites_list)

        # 遍历执行任务中的每个套件
        for suite_data in suites_list:
            # 重置执行器状态，为每个套件创建新的结果收集器
            self.results = []
            self.summary = {
                "total": 0,
                "success": 0,
                "fail": 0,
                "error": 0,
                "skip": 0,
                "duration": 0,
            }

            # 执行当前套件
            suite_result = self._execute_test_suite(suite_data)

            # 将套件信息添加到结果中
            suite_result["suite_id"] = suite_data.get("id")
            suite_result["suite_name"] = suite_data.get("suite_name")

            # 保存套件执行结果
            suite_results.append(suite_result)

            # 累计任务级别的统计信息
            task_summary["total_cases"] += suite_result["summary"]["total"]
            task_summary["success_cases"] += suite_result["summary"]["success"]
            task_summary["failed_cases"] += suite_result["summary"]["fail"]
            task_summary["error_cases"] += suite_result["summary"]["error"]
            task_summary["skip_cases"] += suite_result["summary"]["skip"]

        # 计算任务总执行时长
        task_end_time = time.time()
        task_summary["duration"] = task_end_time - task_start_time

        # 返回任务执行结果
        return {
            "task_id": task_data.get("id"),
            "task_name": task_data.get("task_name"),
            "task_summary": task_summary,
            "suite_results": suite_results
        }


if __name__ == '__main__':
    pass
