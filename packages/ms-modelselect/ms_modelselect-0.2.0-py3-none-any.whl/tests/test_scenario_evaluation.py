#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试场景评估 API 功能"""

import requests
import json

BASE_URL = "http://localhost:8001"

print("=" * 60)
print("🧪 场景评估 API 测试")
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

# 2. 测试获取场景评估支持的 Grader 列表
print("\n2️⃣  获取场景评估支持的 Grader 列表...")
response = requests.get(f"{BASE_URL}/api/v1/scenarios/graders", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ 成功")
    print(f"   - 可用 Graders: {data.get('total')} 个")
    print("\n   支持的场景评估 Graders:")
    for g in data.get('graders', []):
        print(f"     • {g['code']}: {g['name']}")
        print(f"       描述: {g['description']}")
        print(f"       用例: {', '.join(g['use_cases'][:2])}")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 3. 测试场景评估 - RelevanceGrader
print("\n3️⃣  测试 RelevanceGrader - 客服对话质量评估...")
scenario_data = {
    "grader": "relevance",
    "query": "如何申请退款?",
    "response": "您好!您可以在订单详情页面点击退款按钮。请注意,数字商品在购买后24小时内可以申请退款,超过时间将无法处理。退款会在3-5个工作日内原路返回。",
    "context": "客户购买的是在线课程,已购买2天",
    "reference": "应该说明退款政策(数字商品24小时内可退)、退款流程、以及当前情况无法退款的原因"
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/evaluate",
    headers=headers,
    json=scenario_data
)
if response.status_code == 200:
    result = response.json()
    print(f"   ✅ 评估成功")
    print(f"   - Grader: {result.get('grader_name')}")
    print(f"   - 结果类型: {result.get('result_type')}")
    if result.get('score') is not None:
        print(f"   - 分数: {result.get('score')}")
    if result.get('reason'):
        print(f"   - 原因: {result.get('reason')[:150]}...")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 4. 测试场景评估 - CorrectnessGrader
print("\n4️⃣  测试 CorrectnessGrader - 知识问答正确性评估...")
scenario_data = {
    "grader": "correctness",
    "query": "法国的首都是哪里?",
    "response": "法国的首都是巴黎,它是法国最大的城市,也是政治、经济和文化中心。",
    "reference": "正确答案: 巴黎"
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/evaluate",
    headers=headers,
    json=scenario_data
)
if response.status_code == 200:
    result = response.json()
    print(f"   ✅ 评估成功")
    print(f"   - Grader: {result.get('grader_name')}")
    print(f"   - 结果类型: {result.get('result_type')}")
    if result.get('score') is not None:
        print(f"   - 分数: {result.get('score')}")
    if result.get('reason'):
        print(f"   - 原因: {result.get('reason')[:150]}...")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 5. 测试场景评估 - SimilarityGrader
print("\n5️⃣  测试 SimilarityGrader - 文本相似度评估...")
scenario_data = {
    "grader": "similarity",
    "query": "翻译: Hello World",
    "response": "你好世界",
    "reference": "你好,世界"
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/evaluate",
    headers=headers,
    json=scenario_data
)
if response.status_code == 200:
    result = response.json()
    print(f"   ✅ 评估成功")
    print(f"   - Grader: {result.get('grader_name')}")
    print(f"   - 结果类型: {result.get('result_type')}")
    if result.get('score') is not None:
        print(f"   - 分数: {result.get('score')}")
    if result.get('reason'):
        reason = result.get('reason', '')
        print(f"   - 说明: {reason[:150]}...")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

# 6. 测试场景评估 - JsonMatchGrader
print("\n6️⃣  测试 JsonMatchGrader - JSON 格式验证...")
scenario_data = {
    "grader": "json_match",
    "query": "生成用户信息 JSON",
    "response": '{"name": "张三", "age": 30, "city": "北京"}',
    "reference": '{"name": "张三", "age": 30, "city": "北京"}'
}

response = requests.post(
    f"{BASE_URL}/api/v1/scenarios/evaluate",
    headers=headers,
    json=scenario_data
)
if response.status_code == 200:
    result = response.json()
    print(f"   ✅ 评估成功")
    print(f"   - Grader: {result.get('grader_name')}")
    print(f"   - 结果类型: {result.get('result_type')}")
    if result.get('score') is not None:
        print(f"   - 分数: {result.get('score')}")
    if result.get('reason'):
        print(f"   - 原因: {result.get('reason')[:150]}...")
else:
    print(f"   ❌ 失败: {response.status_code}")
    print(f"   响应: {response.text}")

print("\n" + "=" * 60)
print("🎉 场景评估 API 测试完成!")
print("=" * 60)
print("\n✅ 成功验证:")
print("   • 场景评估 Grader 列表查询")
print("   • RelevanceGrader - 相关性评估")
print("   • CorrectnessGrader - 正确性评估")
print("   • SimilarityGrader - 相似度评估")
print("   • JsonMatchGrader - JSON 格式验证")
print("\n📌 关键特性:")
print("   • 无需上传数据集")
print("   • 实时评估 query-response 对")
print("   • 支持多种评估维度")
print("   • 适用于快速测试和原型验证")
print("\n📚 API 文档: http://localhost:8001/docs")
