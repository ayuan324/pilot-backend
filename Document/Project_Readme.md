# Dify 替代方案：基于 Streamlit 和 OpenRouter 的低代码 AI 工作流构建平台

## 项目概述

随着LLM能力爆发，越来越多企业与个人希望快速构建AI应用。然而现有智能体构建平台（如Dify、Langflow）虽然功能强大，却仍需理解Prompt编写、数据流连接等概念，对普通非程序人员仍不友好。

**现有产品**

Dify 提供了工作流构建与Prompt可视化工具，Langflow 强调组件丰富与自定义性，Flowise追求轻量化体验。然而，它们普遍存在**上手门槛高、调试流程复杂、缺少引导与模块市场**等问题，严重影响非专业用户的体验。

**我们的改进思路**

我们致力于打造一款“ **傻瓜式构建AI智能体** ”平台，强调 **自然语言驱动的工作流搭建、预设模版和可视化提示** ，使产品经理、教师、销售人员等非技术用户也能快速搭建AI应用。核心亮点包括：

* **自然语言生成工作流结构草图** （基于任务描述自动搭建流程）
* **Prompt模版库与任务意图建议** （降低提示编写门槛）
* **流程市场与插件机制** （促进复用与社区共享）


## 技术架构

### 前端 (Streamlit)

* 提供直观的可视化界面
* 提供自然语言到工作流的转换
* 可视化工作流编辑器
* 模板库和组件市场

### 后端

* Python FastAPI 服务
* OpenRouter API 集成（用于访问多种 LLM 模型）
* 工作流存储和管理系统

### 数据存储

* 暂时不需要

## 核心功能模块

### 1. 自然语言工作流生成器

### 2. 可视化工作流编辑器

* 拖放式组件
* 节点连接管理
* 工作流验证
* 实时预览

### 3. Prompt 模板管理

* 预设模板库
* 自定义模板创建
* 版本控制
* 性能分析

### OpenRouter 集成

OpenRouter 将作为 API 调用的中间层，提供以下功能：

```python
def call_openrouter_api(model, prompt, temperature=0.7):
    """调用 OpenRouter API 访问不同的 LLM 模型"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
  
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates workflow structures."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
  
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )
  
    return response.json()
```

## 开发路线

### 阶段一：MVP（最小可行产品）

1. 基础 Streamlit 界面
2. OpenRouter API 集成
3. 简单工作流生成功能
4. 基本工作流编辑器

### 阶段二：功能增强

1. 完整的可视化编辑器
2. 模板库和组件系统
3. 一键部署功能
4. 用户认证和权限管理

### 阶段三：社区和市场

1. 工作流市场
2. 社区共享功能
3. 评分和评论系统
4. API 集成扩展
