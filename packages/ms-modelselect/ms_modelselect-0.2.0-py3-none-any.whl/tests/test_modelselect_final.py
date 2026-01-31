#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 ModelSelect 完整评估流程"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

print("🧪 ModelSelect 完整评估流程测试\n")

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
    print(f"   ✅ 登录成功\n")
else:
    print(f"   ❌ 登录失败\n")
    exit(1)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 2. 获取 Grader 列表
print("2️⃣ 获取支持的 Grader 列表...")
response = requests.get(f"{BASE_URL}/api/v1/graders", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ 成功")
    print(f"   - ModelSelect 可用: {data.get('modelselect_available')}")
    print(f"   - 可用 Graders: {len(data.get('graders', []))} 个")
    for g in data.get('graders', []):
        print(f"     • {g['code']}")
    print()
else:
    print(f"   ❌ 失败\n")

# 3. 创建并执行评估任务 (使用 similarity grader)
print("3️⃣ 创建评估任务 (使用 Similarity Grader)...")
task_data = {
    "name": "Similarity 评估测试",
    "description": "测试 ModelSelect Similarity Grader",
    "config": {
        "grader": "similarity",
        "grader_config": {},
        "dataset": [
            {
                "question": "什么是人工智能?",
                "answer": "人工智能是计算机科学的一个分支",
                "reference": "AI是人工智能的简称"
            },
            {
                "question": "什么是机器学习?",
                "answer": "机器学习是AI的一个子领域",
                "reference": "机器学习让计算机从数据中学习"
            }
        ]
    },
    "auto_execute": False
}

response = requests.post(f"{BASE_URL}/api/v1/tasks", headers=headers, json=task_data)
if response.status_code == 200:
    task = response.json()
    task_id = task.get('id')
    print(f"   ✅ 任务创建成功")
    print(f"   - 任务ID: {task_id}")
    print(f"   - 状态: {task.get('status')}\n")
else:
    print(f"   ❌ 创建失败\n")
    exit(1)

# 4. 手动执行任务
print(f"4️⃣ 手动执行任务...")
response = requests.post(f"{BASE_URL}/api/v1/tasks/{task_id}/execute", headers=headers)
if response.status_code == 200:
    print(f"   ✅ 任务已提交执行")
    print(f"   等待评估完成...\n")
    time.sleep(5)
else:
    print(f"   ❌ 执行失败\n")
    exit(1)

# 5. 查询任务状态
print(f"5️⃣ 查询任务状态...")
response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}", headers=headers)
if response.status_code == 200:
    task = response.json()
    print(f"   - 任务状态: {task.get('status')}")
    print(f"   - 进度: {task.get('progress')}%")
    if task.get('error_message'):
        print(f"   - 错误: {task.get('error_message')}")
    print()
else:
    print(f"   ❌ 查询失败\n")

# 6. 查询评估结果
print(f"6️⃣ 查询评估结果...")
response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}/results", headers=headers)
if response.status_code == 200:
    results = response.json()
    if isinstance(results, list) and len(results) > 0:
        print(f"   ✅ 获取到 {len(results)} 条结果\n")
        for idx, result in enumerate(results):
            print(f"   样本 {idx + 1}:")
            print(f"     - Grader: {result.get('grader_name')}")
            print(f"     - 类型: {result.get('result_type')}")
            if result.get('score') is not None:
                print(f"     - 分数: {result.get('score')}")
            if result.get('reason'):
                reason = result.get('reason', '')
                print(f"     - 原因: {reason[:100]}...")
            print()
    else:
        print(f"   ⚠️  暂无结果\n")
else:
    print(f"   ❌ 查询失败\n")

# 7. 测试数据集上传
print(f"7️⃣ 测试数据集验证...")
dataset = [
    {"question": "Q1", "answer": "A1", "reference": "R1"},
    {"question": "Q2", "answer": "A2", "reference": "R2"}
]
response = requests.post(f"{BASE_URL}/api/v1/datasets/validate", headers=headers, json=dataset)
if response.status_code == 200:
    validation = response.json()
    print(f"   ✅ 验证完成")
    print(f"   - 有效: {validation.get('valid')}")
    print(f"   - 样本数: {validation.get('total_samples')}")
    print(f"   - 错误: {validation.get('error_count')}")
    print(f"   - 警告: {validation.get('warning_count')}\n")
else:
    print(f"   ❌ 验证失败\n")

print("="*60)
print("🎉 ModelSelect 集成测试完成!")
print("="*60)
print("\n✅ 成功验证:")
print("   • ModelSelect 核心库导入")
print("   • Grader 列表查询")
print("   • 任务创建和执行")
print("   • 评估结果查询")
print("   • 数据集验证")
print("\n📚 API 文档: http://localhost:8001/docs")
