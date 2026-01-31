#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    :2026/1/28 16:12
# @Author  : Divine
# @Site    :
# @File    :main.py
# @Software: PyCharm
#
# import requests
# from threading import Thread
#
# device_id = settings.DEVICE_ID
#
#
# class Node:
#     # 注册节点的 URL
#     register_node_url = settings.REGISTER_NODE_URL
#
#     def __init__(self):
#         # 注册节点
#         self.register_node()
#         # 创建消费者
#         self.consumer = MQConsumer()
#
#     def register_node(self):
#         """注册节点"""
#         print("--------------开始注册执行设备-----------------")
#         # 发送请求，注册设备
#         response = requests.post(self.register_node_url, json=settings.DEVICE)
#         if response.status_code == 201:
#             print(response.text)
#             db = db_client.DB()
#             username = db.get_user_name_by_user_id(device_id)
#             print(f'执行用户【{username}】的设备id:【{device_id}】已经上线')
#         else:
#             print(f'用户设备{device_id}注册失败！错误信息：{response.text}')
#             # 退出程序
#             sys.exit(0)
#         # print('设备注册结果：', response.text)
#
#     def start(self):
#         """启动节点"""
#         # 发布节点状态
#         redis_pub.publish_status(device_id, '在线')
#         # 发布节点屏幕画面
#         Thread(target=redis_pub.publish_screen, args=(device_id,)).start()
#         # 启动消费者
#         self.consumer.main()
#
#     def stop(self):
#         """关闭节点"""
#         # 关闭 RabbitMQ 连接
#         self.consumer.stop()
#         # 设置节点状态为已停止
#         redis_pub.publish_status(device_id, '离线')
#         # 清理设备执行日志
#         redis_pub.clear_history(device_id)
#         # 关闭 Redis 连接
#         redis_pub.close()
#         # 修改数据库中节点状态为离线
#         db = db_client.DB()
#         db.execute(sql="UPDATE device SET status = '离线' WHERE id = %s", args=device_id)
#         print("-------------节点关闭，清理资源完毕-----------------")
#         # 退出程序
#         sys.exit(0)
#
#     def handle_exit(self, signum, frame):
#         """处理节点退出信号并执行清理"""
#         print(f"收到退出信号{signum}，开始清理...")
#         # 停止节点
#         self.stop()
#
#     def get_user_name(self):
#         """获取用户名"""
#         db = db_client.DB()
#         username = db.get_user_name().get('username')
#         db.close()
#         return username
#
#
# def main():
#     node = Node()
#     # 绑定信号处理函数，确保节点能退出
#     signal.signal(signal.SIGTERM, node.handle_exit)
#     signal.signal(signal.SIGINT, node.handle_exit)
#     # 启动节点并开始任务监听
#     node.start()
#
#
#
# if __name__ == '__main__':
#     main()

if __name__ == '__main__':
    cases_list = [
        {
            "name": "用户登录_正常账号密码登录成功",
            "description": "验证使用正确账号密码调用登录接口时，返回200且响应体包含token及userInfo.userId为整数",
            "interface": "/api/users/login",
            "preconditions": [],
            "request": {
                "interface_id": "login",
                "method": "POST",
                "url": "/user/login",
                "base_url": "${{base_url}}",
                "headers": {
                    "Content-Type": "application/json"
                },
                "params": {},
                "body": {
                    "username": "${{username}}",
                    "password": "${{password}}"
                },
                "files": {},
                "setup_script": "username = \"admin\"\npassword = \"123456\"\ntest.save_test_env_variables(\"username\", username)\ntest.save_test_env_variables(\"password\", password)",
                "teardown_script": "import json\n# 假设response已经是字典格式\nif isinstance(response, dict):\n    if 'access_token' in response:\n        access_token = response['access_token']\n        test.save_test_env_variables('access_token', access_token)\n        print(f'已保存access_token1111: {access_token[:20]}...')\n    else:\n        print('响应中未找到access_token字段')\n        print(f'响应内容: {response}')\nelif hasattr(response, 'text'):\n    # 如果是requests.Response对象\n    try:\n        response_data = json.loads(response.text)\n        if 'access_token' in response_data:\n            access_token = response_data['access_token']\n            test.save_test_env_variables('access_token', access_token)\n            print(f'已保存access_token2222: {access_token[:20]}...')\n    except:\n        print(f'无法解析响应: {response.text}')\nelse:\n    print(f'未知的响应类型: {type(response)}')"
            },
            "assertions": {
                "response": [
                    {
                        "type": "http_code",
                        "field": "http_code",
                        "expected": 200
                    }
                ]
            },
            "state": "可用"
        },
        {
            "name": "/user/profile",
            "description": "/user/profile",
            "interface": "/user/profile",
            "preconditions": [],
            "request": {
                "interface_id": "/user/profile",
                "method": "GET",
                "url": "/user/profile",
                "base_url": "${{base_url}}",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer ${{access_token}}"
                },
                "params": {},
                "body": {
                },
                "files": {},
                "setup_script": "access_token='access_token'\ntest.get_test_env_variables('access_token')",
                "teardown_script": ""
            },
            "assertions": {
                "response": [
                    {
                        "type": "http_code",
                        "field": "http_code",
                        "expected": 200
                    }
                ]
            },
            "state": "可用"
        }
    ]
    db = [{
        "name": "ai_test",
        "type": "mysql",
        "config": {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "root",
            "password": "123456",
            "database": "ai_test"
        }
    }]
    run_case(test_env_global={"base_url": "http://127.0.0.1:8080"}, db_config=db, suite_data=cases_list)