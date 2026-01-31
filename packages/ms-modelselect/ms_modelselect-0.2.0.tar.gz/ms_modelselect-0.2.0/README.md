<div align="center">

<img src="./docs/images/logo.svg" alt="ModelSelect Logo" width="500">

<br/>

<h3>
  <em>模型智选，评测先行：让 AI 选型更简单</em>
</h3>

<p>
  🌟 <em>If you find ModelSelect helpful, please give us a <b>Star</b>!</em> 🌟
</p>

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue?logo=python)](https://pypi.org/project/ms-modelselect/)
[![PyPI](https://img.shields.io/badge/pypi-v0.3.0-blue?logo=pypi)](https://pypi.org/project/ms-modelselect/)
[![Documentation](https://img.shields.io/badge/docs-online-blue?logo=readthedocs&logoColor=white)](https://github.com/modelselect/modelselect)

[📖 Documentation](https://github.com/modelselect/modelselect) | [🤝 Contributing](https://github.com/modelselect/modelselect) | [中文](./README_zh.md)

</div>




ModelSelect (模选) 是一个**开源的 AI 模型评测框架**，专为**AI 应用**（如 AI 智能体、聊天机器人、大语言模型）的**质量评估**和**持续优化**而设计。

> 在实践中，卓越的应用取决于可信赖的评测工作流：收集测试数据 → 定义评分标准 → 规模化运行评测 → 分析薄弱环节 → 快速迭代优化。

ModelSelect 提供**开箱即用的评分器(Grader)**，并支持生成**场景特定的评分标准**，使这一工作流**更简单**、**更专业**、**易于集成**到您的工作流中。同时，它还能将评分结果转换为**奖励信号**，帮助您**微调**和优化应用。

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [News](#news)
- [Installation](#-installation)
- [Quickstart](#-quickstart)
- [API Service](#-api-service)
- [Contributing](#-contributing)
- [Community](#-community)
- [Citation](#-citation)
---

## ✨ Key Features

### 📦 系统化且质量保障的 Grader 库

访问 **50+ 生产级评分器**，涵盖全面的分类体系，经过严格验证确保可靠性能。

<table>
<tr>
<td width="33%" valign="top">

#### 🎯 通用能力

**聚焦:** 语义质量、功能正确性、结构合规性

**核心评分器:**
- `Relevance` - 语义相关性评分
- `Similarity` - 文本相似度测量
- `Syntax Check` - 代码语法验证
- `JSON Match` - 结构合规性检查

</td>
<td width="33%" valign="top">

#### 🤖 智能体评估

**聚焦:** 智能体生命周期、工具调用、记忆、计划可行性、轨迹质量

**核心评分器:**
- `Tool Selection` - 工具选择准确性
- `Memory` - 上下文保持能力
- `Plan` - 策略可行性
- `Trajectory` - 路径优化

</td>
<td width="33%" valign="top">

#### 🖼️ 多模态评估

**聚焦:** 图文一致性、视觉生成质量、图像有用性

**核心评分器:**
- `Image Coherence` - 视觉-文本对齐
- `Text-to-Image` - 生成质量
- `Image Helpfulness` - 图像贡献度

</td>
</tr>
</table>

- 🌐 **多场景覆盖:** 广泛支持 Agent、文本、代码、数学和多模态任务等多种领域
- 🔄 ** holistic 智能体评估:** 不仅评估最终结果，还评估整个生命周期——包括轨迹、记忆、反思和工具使用
- ✅ **质量保证:** 每个评分器都附带基准数据集和 pytest 集成验证

### 🛠️ 灵活的评分器构建方式

选择适合您需求的构建方式：
* **定制化:** 需求明确但没有现成评分器？如果有明确的规则或逻辑，使用 Python 接口或 Prompt 模板快速定义自己的评分器
* **零样本评分标准生成:** 不确定使用什么标准，且没有标注数据？只需提供任务描述和可选的示例查询——LLM 将自动生成评估评分标准
* **数据驱动的评分标准生成:** 需求模糊，但有一些示例？使用 GraderGenerator 从标注数据中自动总结评估评分标准，并生成基于 LLM 的评分器
* **训练评判模型:** 数据量大且需要最佳性能？使用我们的训练流程训练专用的评判模型

### 🌐 SaaS API 服务

ModelSelect 提供完整的 SaaS API 服务，支持：
- ✅ **多租户管理**: 支持多租户隔离，每个租户独立配置
- ✅ **用户管理**: 完整的用户认证、授权和权限管理
- ✅ **评估任务**: 创建、管理和执行 AI 应用评估任务
- ✅ **场景评估**: 无需上传数据集，直接评估单个 query-response 对
- ✅ **API Key 管理**: 支持 API Key 创建和管理
- ✅ **结果分析**: 评估结果的存储、查询和统计分析

---

## News

- **2025-01-29** - ModelSelect v0.3.0 发布 - 全新品牌升级！从 OpenJudge 分支并扩展更多模型评测能力，新增 SaaS API 服务和多租户支持

---

## 📥 Installation

```bash
pip install ms-modelselect
```

安装 SaaS 服务依赖：
```bash
pip install "ms-modelselect[saas]"
```

---

## 🚀 Quickstart

### 简单示例

评估单个响应的简单示例：

```python
import asyncio
from modelselect.models import OpenAIChatModel
from modelselect.graders.common.relevance import RelevanceGrader

async def main():
    # 1️⃣ 创建模型客户端
    model = OpenAIChatModel(model="qwen3-32b")
    # 2️⃣ 初始化评分器
    grader = RelevanceGrader(model=model)
    # 3️⃣ 准备数据
    data = {
        "query": "What is machine learning?",
        "response": "Machine learning is a subset of AI that enables computers to learn from data.",
    }
    # 4️⃣ 评估
    result = await grader.aevaluate(**data)
    print(f"Score: {result.score}")   # Score: 4
    print(f"Reason: {result.reason}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🌐 API Service

ModelSelect 提供完整的 SaaS API 服务，支持多租户、用户管理、评估任务管理和场景评估。

### 快速启动

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d
```

### API 端点

| 模块 | 端点 | 功能 |
|------|------|------|
| 认证 | `POST /api/v1/auth/login` | 用户登录 |
| 认证 | `POST /api/v1/auth/register` | 用户注册 |
| 用户 | `GET /api/v1/users/me` | 获取当前用户 |
| API Key | `POST /api/v1/api-keys` | 创建 API Key |
| 任务 | `POST /api/v1/tasks` | 创建评估任务 |
| 任务 | `GET /api/v1/tasks` | 获取任务列表 |
| 场景 | `POST /api/v1/scenarios/evaluate` | 场景评估 |
| 场景 | `POST /api/v1/scenarios/batch-evaluate` | 批量场景评估 |

更多 API 文档请访问：`http://localhost:8000/docs`

---

## 🤝 Contributing

我们欢迎各种形式的贡献！请查看我们的[贡献指南](https://github.com/modelselect/modelselect)。

## 📜 License

本项目基于 Apache 2.0 许可证开源。

---

**ModelSelect Team** - 让 AI 模型选型更简单 🚀
