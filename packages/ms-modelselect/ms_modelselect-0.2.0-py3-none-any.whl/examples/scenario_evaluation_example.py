#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
场景评估 API 使用示例

演示如何使用 ModelSelect SaaS 的场景评估 API 进行快速评估,
无需上传完整数据集。
"""

import requests
import json
from typing import Dict, Any


class ScenarioEvaluationClient:
    """场景评估客户端"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.access_token = None

    def login(self, email: str, password: str) -> bool:
        """登录获取访问令牌"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
            return True
        return False

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def list_graders(self) -> Dict[str, Any]:
        """获取支持的 Grader 列表"""
        response = requests.get(
            f"{self.base_url}/api/v1/scenarios/graders",
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else None

    def evaluate_relevance(
        self,
        query: str,
        response: str,
        context: str = None,
        reference: str = None
    ) -> Dict[str, Any]:
        """评估响应与查询的相关性

        适用场景:
        - 客服对话质量评估
        - 搜索结果相关性评估
        - 问答系统评估
        """
        return requests.post(
            f"{self.base_url}/api/v1/scenarios/evaluate",
            headers=self.get_headers(),
            json={
                "grader": "relevance",
                "query": query,
                "response": response,
                "context": context,
                "reference": reference
            }
        ).json()

    def evaluate_correctness(
        self,
        query: str,
        response: str,
        reference: str = None
    ) -> Dict[str, Any]:
        """评估响应的正确性

        适用场景:
        - 知识问答正确性评估
        - 代码实现正确性评估
        - 事实核查
        """
        return requests.post(
            f"{self.base_url}/api/v1/scenarios/evaluate",
            headers=self.get_headers(),
            json={
                "grader": "correctness",
                "query": query,
                "response": response,
                "reference": reference
            }
        ).json()

    def evaluate_similarity(
        self,
        response: str,
        reference: str,
        query: str = None
    ) -> Dict[str, Any]:
        """评估文本相似度 (使用 BLEU 等指标)

        适用场景:
        - 翻译质量评估
        - 文本生成评估
        - 摘要质量评估
        """
        return requests.post(
            f"{self.base_url}/api/v1/scenarios/evaluate",
            headers=self.get_headers(),
            json={
                "grader": "similarity",
                "query": query,
                "response": response,
                "reference": reference
            }
        ).json()

    def evaluate_json_match(
        self,
        response: str,
        reference: str
    ) -> Dict[str, Any]:
        """验证 JSON 格式和字段匹配

        适用场景:
        - API 响应格式验证
        - 结构化数据生成评估
        - 配置文件格式检查
        """
        return requests.post(
            f"{self.base_url}/api/v1/scenarios/evaluate",
            headers=self.get_headers(),
            json={
                "grader": "json_match",
                "query": "JSON validation",
                "response": response,
                "reference": reference
            }
        ).json()

    def batch_evaluate(
        self,
        grader: str,
        scenarios: list,
        grader_config: dict = None
    ) -> Dict[str, Any]:
        """批量评估多个场景

        Args:
            grader: 评估器名称
            scenarios: 场景列表,每个场景包含 query, response 等字段
            grader_config: 评估器配置 (可选)

        Returns:
            批量评估结果
        """
        if grader_config is None:
            grader_config = {}

        return requests.post(
            f"{self.base_url}/api/v1/scenarios/batch-evaluate",
            headers=self.get_headers(),
            json={
                "grader": grader,
                "scenarios": scenarios,
                "grader_config": grader_config
            }
        ).json()


def main():
    """使用示例"""

    # 初始化客户端
    client = ScenarioEvaluationClient()

    # 登录
    print("🔐 登录中...")
    if not client.login("zhizhengyang@aliyun.com", "yzz620987."):
        print("❌ 登录失败")
        return
    print("✅ 登录成功\n")

    # 示例 1: 客服对话质量评估
    print("=" * 60)
    print("📞 示例 1: 客服对话质量评估 (Relevance)")
    print("=" * 60)
    result = client.evaluate_relevance(
        query="如何申请退款?",
        response="您好!您可以在订单详情页面点击退款按钮。请注意,数字商品在购买后24小时内可以申请退款,超过时间将无法处理。",
        context="客户购买的是在线课程",
        reference="应该说明退款政策、操作流程以及数字商品的特殊规定"
    )
    print(f"评估结果: {result.get('reason', 'N/A')}")
    print(f"评分: {result.get('score') or result.get('rank')}\n")

    # 示例 2: 知识问答正确性评估
    print("=" * 60)
    print("💡 示例 2: 知识问答正确性评估 (Correctness)")
    print("=" * 60)
    result = client.evaluate_correctness(
        query="Python 中什么是列表推导式?",
        response="列表推导式是 Python 中创建列表的简洁方式,语法为 [expression for item in iterable if condition],它可以替代传统的 for 循环和 map/filter 函数。",
        reference="正确答案应包含语法格式、使用场景和示例"
    )
    print(f"评估结果: {result.get('reason', 'N/A')}")
    print(f"评分: {result.get('score') or result.get('rank')}\n")

    # 示例 3: 翻译质量评估
    print("=" * 60)
    print("🌐 示例 3: 翻译质量评估 (Similarity)")
    print("=" * 60)
    result = client.evaluate_similarity(
        query="翻译: Hello, World!",
        response="你好,世界!",
        reference="你好,世界!"
    )
    print(f"相似度分数: {result.get('score')}")
    print(f"说明: {result.get('reason', 'N/A')}\n")

    # 示例 4: API JSON 响应验证
    print("=" * 60)
    print("🔧 示例 4: API JSON 响应验证 (JsonMatch)")
    print("=" * 60)
    result = client.evaluate_json_match(
        response='{"name": "张三", "age": 30, "city": "北京"}',
        reference='{"name": "张三", "age": 30, "city": "北京"}'
    )
    print(f"匹配分数: {result.get('score')}")
    print(f"说明: {result.get('reason', 'N/A')}\n")

    # 示例 5: 批量客服对话质量评估
    print("=" * 60)
    print("📊 示例 5: 批量客服对话质量评估")
    print("=" * 60)
    scenarios = [
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
    result = client.batch_evaluate("relevance", scenarios)
    print(f"总数: {result['total_count']}")
    print(f"成功: {result['success_count']}")
    print(f"失败: {result['failed_count']}")
    print("\n批量评估结果:")
    for idx, eval_result in enumerate(result['results']):
        print(f"场景 {idx + 1}:")
        print(f"  评分: {eval_result.get('score') or eval_result.get('rank')}")
        print(f"  原因: {eval_result.get('reason', 'N/A')[:80]}...")
    print()

    # 示例 6: 批量知识问答评估
    print("=" * 60)
    print("📚 示例 6: 批量知识问答评估")
    print("=" * 60)
    qa_scenarios = [
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
    result = client.batch_evaluate("correctness", qa_scenarios)
    print(f"总数: {result['total_count']}")
    print(f"成功: {result['success_count']}")
    print(f"失败: {result['failed_count']}")
    print("\n批量评估结果:")
    for idx, eval_result in enumerate(result['results']):
        print(f"问题 {idx + 1}:")
        print(f"  评分: {eval_result.get('score') or eval_result.get('rank')}")
    print()

    print("=" * 60)
    print("✅ 所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
