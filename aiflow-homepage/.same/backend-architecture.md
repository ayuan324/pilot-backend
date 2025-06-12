# πlot Backend Architecture Plan

## 项目概述
基于用户的自然语言 Prompt 生成 AI Agent 工作流的后端系统，类似于 Dify 的可视化工作流构建平台。

## 技术架构

### 1. 后端技术栈
```
- **框架**: FastAPI (Python) - 高性能异步框架
- **数据库**: PostgreSQL + Redis
- **AI服务**: OpenRouter API / OpenAI API
- **消息队列**: Celery + Redis
- **容器化**: Docker + Docker Compose
- **部署**: Railway / Vercel / Supabase
```

### 2. 核心模块设计

#### 2.1 Prompt 解析与意图理解
```python
# prompt_analyzer.py
class PromptAnalyzer:
    def analyze_intent(self, prompt: str) -> WorkflowIntent
    def extract_entities(self, prompt: str) -> List[Entity]
    def suggest_workflow_structure(self, intent: WorkflowIntent) -> WorkflowBlueprint
```

#### 2.2 工作流生成引擎
```python
# workflow_generator.py
class WorkflowGenerator:
    def generate_workflow(self, blueprint: WorkflowBlueprint) -> Workflow
    def create_nodes(self, node_configs: List[NodeConfig]) -> List[Node]
    def connect_nodes(self, connections: List[Connection]) -> Graph
```

#### 2.3 Agent 节点系统
```python
# node_types.py
class NodeBase:
    - Input Node (用户输入)
    - LLM Node (大语言模型处理)
    - Condition Node (条件判断)
    - Loop Node (循环处理)
    - API Node (外部API调用)
    - Output Node (结果输出)
    - Knowledge Node (知识库查询)
    - Tool Node (工具调用)
```

### 3. 数据库设计

#### 3.1 核心表结构
```sql
-- 工作流表
CREATE TABLE workflows (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    user_id UUID,
    workflow_data JSONB,  -- 存储节点和连接信息
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 节点表
CREATE TABLE nodes (
    id UUID PRIMARY KEY,
    workflow_id UUID,
    node_type VARCHAR(100),
    config JSONB,
    position_x INTEGER,
    position_y INTEGER
);

-- 连接表
CREATE TABLE connections (
    id UUID PRIMARY KEY,
    workflow_id UUID,
    source_node_id UUID,
    target_node_id UUID,
    connection_type VARCHAR(50)
);

-- 执行历史表
CREATE TABLE execution_logs (
    id UUID PRIMARY KEY,
    workflow_id UUID,
    input_data JSONB,
    output_data JSONB,
    execution_time INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP
);
```

### 4. API 设计

#### 4.1 工作流生成 API
```python
# POST /api/workflows/generate
{
    "prompt": "创建一个客户支持聊天机器人",
    "user_preferences": {
        "complexity": "simple",
        "integrations": ["slack", "email"]
    }
}

# Response
{
    "workflow_id": "uuid",
    "workflow": {
        "nodes": [...],
        "connections": [...],
        "estimated_cost": 0.05,
        "execution_time": "~2s"
    }
}
```

#### 4.2 工作流执行 API
```python
# POST /api/workflows/{workflow_id}/execute
{
    "input_data": {
        "user_message": "我需要帮助"
    }
}

# Response (Stream)
{
    "execution_id": "uuid",
    "status": "running",
    "current_node": "node_1",
    "output": "正在处理您的请求..."
}
```

### 5. 前端集成方案

#### 5.1 下拉面板设计
```typescript
// WorkflowPanel.tsx
interface WorkflowPanelProps {
    isVisible: boolean;
    workflowData: Workflow;
    onNodeEdit: (nodeId: string, config: NodeConfig) => void;
    onExecute: (inputData: any) => void;
}

// 面板状态管理
const [panelState, setPanelState] = useState<'hidden' | 'generating' | 'editing' | 'executing'>('hidden');
```

#### 5.2 实时协作
```typescript
// 使用 WebSocket 实现实时更新
const ws = new WebSocket('/ws/workflow/{workflow_id}');
ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    updateWorkflowState(update);
};
```

### 6. 工作流模板系统

#### 6.1 预设模板
```python
WORKFLOW_TEMPLATES = {
    "customer_support": {
        "nodes": [
            {"type": "input", "config": {"input_type": "text"}},
            {"type": "llm", "config": {"model": "gpt-4", "temperature": 0.7}},
            {"type": "condition", "config": {"logic": "sentiment_analysis"}},
            {"type": "output", "config": {"format": "text"}}
        ]
    },
    "content_generation": {...},
    "data_analysis": {...}
}
```

#### 6.2 智能推荐
```python
class TemplateRecommender:
    def recommend_templates(self, prompt: str) -> List[Template]
    def suggest_optimizations(self, workflow: Workflow) -> List[Suggestion]
```

### 7. 执行引擎

#### 7.1 异步执行
```python
# workflow_executor.py
class WorkflowExecutor:
    async def execute_workflow(self, workflow: Workflow, input_data: dict):
        execution_context = ExecutionContext()
        for node in workflow.get_execution_order():
            result = await self.execute_node(node, execution_context)
            execution_context.update(result)
        return execution_context.get_final_output()
```

#### 7.2 错误处理与重试
```python
class ExecutionManager:
    def handle_node_failure(self, node: Node, error: Exception)
    def retry_with_backoff(self, node: Node, max_retries: int = 3)
    def fallback_strategy(self, node: Node, fallback_config: dict)
```

### 8. 监控与分析

#### 8.1 性能监控
- 工作流执行时间统计
- 节点成功率监控
- API 调用成本跟踪
- 用户使用模式分析

#### 8.2 优化建议
- 自动优化工作流结构
- 成本优化建议
- 性能瓶颈识别

## 开发阶段规划

### 阶段一：MVP (4-6周)
1. 基础 Prompt 解析
2. 简单工作流生成
3. 基本节点类型实现
4. 前端面板集成

### 阶段二：增强功能 (6-8周)
1. 复杂工作流支持
2. 模板系统
3. 实时执行监控
4. 用户管理系统

### 阶段三：高级特性 (8-10周)
1. 智能优化
2. 协作功能
3. 插件系统
4. 企业级功能

## 技术难点与解决方案

### 1. Prompt 到工作流的转换
- 使用大语言模型理解用户意图
- 建立意图到工作流的映射规则
- 训练专门的分类模型

### 2. 复杂工作流的可视化
- 使用 React Flow 或 D3.js
- 实现拖拽、连接、编辑功能
- 支持嵌套和子工作流

### 3. 实时执行与状态同步
- WebSocket 实时通信
- 状态机管理执行流程
- 错误恢复和断点续传

这个架构设计可以支持从简单的 MVP 到企业级的 AI 工作流平台的演进。您觉得哪个部分需要我详细展开说明？
