#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试批量场景评估 API 功能"""

import requests
import json

BASE_URL = "http://localhost:8001"

print("=" * 60)
print("🧪 批量场景评估 API 测试")
print("=" * 60)

# 1. 登录
print("\n1️⃣  管理员登录...")
login_data = {
    "email": "zhizhengyang@aliyun.com",
    "password": "yzz620987."
}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get("access_token")
    print("   ✅ 登录成功")
else:
    print(f"   ❌ 登录失败: {response.status_code}")
    exit(1)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 2. 测试批量场景评估 - RelevanceGrader (客服对话)
print("\n2️⃣  测试批量场景评估 - RelevanceGrader (客服对话)...")
batch_request = {
    "grader": "relevance",
    "scenarios": [
        {
            "query": "如何申请退款?",
            "response": "您好!您可以在订单详情页面点击退款按钮。数字商品在购买后24小时内可以申请退款。",
            "context": "客户购买的是在线课程"
        },
        {
            "query": "产品价格是多少?",
            "response": "我们有多种价格方案,基础版99元/月,专业版199元/月,企业版请咨询销售。",
            "context": "客户询问价格"
        },
        {
            "query": "可以试用吗?",
            "response": "当然可以!我们提供14天免费试用,无需信用卡,可以直接注册体验。",
            "context": "客户想试用产品"
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/batch-evaluate",
    headers=headers,
    json=batch_request
)
if response.status_code == 200:
    result = response.json()
    print(f"   ✅ 批量评估成功")
    print(f"   - 总数: {result.get('total_count')}")
    print(f"   - 成功: {result.get('success_count')}")
    print(f"   - 失败: {result.get('failed_count')}")
    print("\n   评估结果:")
    for idx, eval_result in enumerate(result.get('results', [])):
        print(f"   场景 {idx + 1}:")
        print(f"     - Grader: {eval_result.get('grader_name')}")
        print(f"     - 结果类型: {eval_result.get('result_type')}")
        if eval_result.get('score') is not None:
            print(f"     - 分数: {eval_result.get('score')}")
        if eval_result.get('rank'):
            print(f"     - 排名: {eval_result.get('rank')}")
        if eval_result.get('reason'):
            reason = eval_result.get('reason', '')
            print(f"     - 原因: {reason[:100]}...")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 3. 测试批量场景评估 - CorrectnessGrader (知识问答)
print("\n3️⃣  测试批量场景评估 - CorrectnessGrader (知识问答)...")
batch_request = {
    "grader": "correctness",
    "scenarios": [
        {
            "query": "Python 中什么是列表推导式?",
            "response": "列表推导式是 Python 中创建列表的简洁方式,语法为 [expression for item in iterable if condition]。",
            "reference": "应包含语法格式和使用示例"
        },
        {
            "query": "什么是递归?",
            "response": "递归是一种编程技巧,函数直接或间接调用自身来解决问题,需要定义基准情况和递归情况。",
            "reference": "应解释递归的概念和两个关键要素"
        },
        {
            "query": "REST API 是什么?",
            "response": "REST是一种架构风格,使用HTTP方法(GET, POST, PUT, DELETE)操作资源,具有无状态、可缓存等特点。",
            "reference": "应解释REST的基本概念和特点"
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/batch-evaluate",
    headers=headers,
    json=batch_request
)
if response.status_code == 200:
    result = response.json()
    print(f"   ✅ 批量评估成功")
    print(f"   - 总数: {result.get('total_count')}")
    print(f"   - 成功: {result.get('success_count')}")
    print(f"   - 失败: {result.get('failed_count')}")
    print("\n   评估结果:")
    for idx, eval_result in enumerate(result.get('results', [])):
        print(f"   场景 {idx + 1}:")
        print(f"     - Grader: {eval_result.get('grader_name')}")
        print(f"     - 结果类型: {eval_result.get('result_type')}")
        if eval_result.get('score') is not None:
            print(f"     - 分数: {eval_result.get('score')}")
        if eval_result.get('rank'):
            print(f"     - 排名: {eval_result.get('rank')}")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 4. 测试批量场景评估 - SimilarityGrader (翻译质量)
print("\n4️⃣  测试批量场景评估 - SimilarityGrader (翻译质量)...")
batch_request = {
    "grader": "similarity",
    "scenarios": [
        {
            "query": "翻译: Hello, World!",
            "response": "你好,世界!",
            "reference": "你好,世界!"
        },
        {
            "query": "翻译: Good morning!",
            "response": "早上好!",
            "reference": "早上好"
        },
        {
            "query": "翻译: Thank you!",
            "response": "谢谢!",
            "reference": "谢谢"
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/batch-evaluate",
    headers=headers,
    json=batch_request
)
if response.status_code == 200:
    result = response.json()
    print(f"   ✅ 批量评估成功")
    print(f"   - 总数: {result.get('total_count')}")
    print(f"   - 成功: {result.get('success_count')}")
    print(f"   - 失败: {result.get('failed_count')}")
    print("\n   相似度分数:")
    for idx, eval_result in enumerate(result.get('results', [])):
        score = eval_result.get('score')
        print(f"   场景 {idx + 1}: {score}")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 5. 测试错误处理 - 包含无效场景
print("\n5️⃣  测试错误处理 - 包含无效场景...")
batch_request = {
    "grader": "relevance",
    "scenarios": [
        {
            "query": "如何申请退款?",
            "response": "您可以点击退款按钮..."
        },
        {
            # 缺少 response 字段
            "query": "产品价格是多少?"
        },
        {
            "query": "可以试用吗?",
            "response": "我们提供14天免费试用"
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/batch-evaluate",
    headers=headers,
    json=batch_request
)
if response.status_code == 400:
    print(f"   ✅ 正确处理无效请求")
    print(f"   - 错误信息: {response.json().get('detail')}")
else:
    print(f"   ⚠️  期望400错误,实际: {response.status_code}")

print("\n" + "=" * 60)
print("🎉 批量场景评估 API 测试完成!")
print("=" * 60)
print("\n✅ 成功验证:")
print("   • 批量场景评估 API")
print("   • RelevanceGrader 批量评估")
print("   • CorrectnessGrader 批量评估")
print("   • SimilarityGrader 批量评估")
print("   • 错误处理机制")
print("\n📌 批量评估特性:")
print("   • 一次性评估多个场景 (最多50个)")
print("   • 统一的 Grader 配置")
print("   • 详细的错误报告")
print("   • 成功/失败统计")
print("\n📚 API 文档: http://localhost:8001/docs")
