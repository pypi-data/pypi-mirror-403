#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 ModelSelect 集成"""

import requests
import json

BASE_URL = "http://localhost:8001"

print("🧪 测试 ModelSelect 集成\n")

# 1. 登录
print("1️⃣ 管理员登录...")
login_data = {
    "email": "zhizhengyang@aliyun.com",
    "password": "yzz620987."
}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get("access_token")
    print(f"   ✅ 登录成功")
else:
    print(f"   ❌ 登录失败: {response.status_code}")
    exit(1)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 2. 测试获取 Grader 列表
print("\n2️⃣ 获取支持的 Grader 列表...")
response = requests.get(f"{BASE_URL}/api/v1/graders", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ 成功")
    print(f"   - ModelSelect 可用: {data.get('modelselect_available')}")
    print(f"   - Grader 数量: {data.get('total')}")
    print("\n   支持的 Graders:")
    for grader in data.get('graders', []):
        print(f"     • {grader['code']}: {grader.get('name', 'N/A')}")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 3. 测试获取特定 Grader 信息
print("\n3️⃣ 获取 Relevance Grader 信息...")
response = requests.get(f"{BASE_URL}/api/v1/graders/relevance", headers=headers)
if response.status_code == 200:
    info = response.json()
    print(f"   ✅ 成功")
    print(f"   - 类名: {info.get('class_name')}")
    print(f"   - 模块: {info.get('module')}")
else:
    print(f"   ❌ 失败: {response.status_code}")

# 4. 测试创建评估任务
print("\n4️⃣ 创建评估任务...")
task_data = {
    "name": "测试任务",
    "description": "测试 ModelSelect 集成",
    "config": {
        "grader": "relevance",
        "grader_config": {},
        "dataset": [
            {
                "question": "什么是AI?",
                "answer": "人工智能是计算机科学的一个分支",
                "reference": "AI是指人工智能"
            }
        ]
    },
    "auto_execute": False  # 不自动执行
}

response = requests.post(f"{BASE_URL}/api/v1/tasks", headers=headers, json=task_data)
if response.status_code == 200:
    task = response.json()
    task_id = task.get('id')
    print(f"   ✅ 任务创建成功")
    print(f"   - 任务ID: {task_id}")
    print(f"   - 任务名: {task.get('name')}")
    print(f"   - 状态: {task.get('status')}")

    # 5. 手动执行任务
    print(f"\n5️⃣ 手动执行任务...")
    response = requests.post(f"{BASE_URL}/api/v1/tasks/{task_id}/execute", headers=headers)
    if response.status_code == 200:
        print(f"   ✅ 任务已提交执行")
        print(f"   等待3秒后查看结果...")
        import time
        time.sleep(3)

        # 6. 查询任务状态
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}", headers=headers)
        if response.status_code == 200:
            task = response.json()
            print(f"   - 任务状态: {task.get('status')}")
            print(f"   - 进度: {task.get('progress')}%")
            if task.get('error_message'):
                print(f"   - 错误: {task.get('error_message')}")

        # 7. 查询结果
        print(f"\n6️⃣ 查询评估结果...")
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}/results", headers=headers)
        if response.status_code == 200:
            results = response.json()
            if isinstance(results, list) and len(results) > 0:
                print(f"   ✅ 获取到 {len(results)} 条结果")
                for idx, result in enumerate(results[:3]):  # 只显示前3条
                    print(f"\n   样本 {idx + 1}:")
                    print(f"     - Grader: {result.get('grader_name')}")
                    print(f"     - 类型: {result.get('result_type')}")
                    if result.get('score') is not None:
                        print(f"     - 分数: {result.get('score')}")
                    if result.get('reason'):
                        print(f"     - 原因: {result.get('reason')[:100]}...")
            else:
                print(f"   ⚠️  暂无结果 (可能还在处理中)")
        else:
            print(f"   ❌ 查询失败: {response.status_code}")

    else:
        print(f"   ❌ 执行失败: {response.status_code}")
        print(f"   响应: {response.text}")
else:
    print(f"   ❌ 创建失败: {response.status_code}")
    print(f"   响应: {response.text}")

print("\n" + "="*60)
print("ModelSelect 集成测试完成")
print("="*60)
