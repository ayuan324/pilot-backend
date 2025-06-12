# πlot MVP 实现计划

## 技术栈确认
- **前端**: Next.js + React Flow + shadcn/ui + TailwindCSS
- **后端**: FastAPI + Python
- **用户管理**: Clerk
- **数据库**: Supabase (PostgreSQL)
- **大模型**: OpenRouter API + LiteLLM
- **监控**: Sentry
- **部署**: Vercel (前端) + Railway/Render (后端)

## MVP 核心功能

### 1. 工作流引擎 (参考 Dify)

#### 1.1 节点系统设计
```python
# 基础节点类型
class NodeType(Enum):
    START = "start"           # 开始节点
    LLM = "llm"              # 大语言模型节点
    PROMPT_TEMPLATE = "prompt_template"  # 提示词模板
    CONDITION = "condition"   # 条件判断
    CODE = "code"            # 代码执行
    HTTP_REQUEST = "http"     # HTTP 请求
    VARIABLE = "variable"     # 变量设置
    OUTPUT = "output"        # 输出节点

# 节点配置结构
class NodeConfig(BaseModel):
    id: str
    type: NodeType
    name: str
    description: str
    position: Dict[str, float]  # x, y coordinates
    config: Dict[str, Any]      # 节点特定配置
    inputs: List[str]           # 输入变量
    outputs: List[str]          # 输出变量
```

#### 1.2 工作流数据结构
```python
class Workflow(BaseModel):
    id: str
    name: str
    description: str
    user_id: str
    nodes: List[NodeConfig]
    edges: List[Edge]
    variables: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class Edge(BaseModel):
    id: str
    source: str      # source node id
    target: str      # target node id
    source_handle: str  # output handle
    target_handle: str  # input handle
```

#### 1.3 前端可视化编辑器
```typescript
// WorkflowEditor.tsx - 基于 React Flow
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge
} from 'reactflow';

const WorkflowEditor = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // 自定义节点组件
  const nodeTypes = {
    llm: LLMNode,
    condition: ConditionNode,
    http: HttpNode,
    // ... 其他节点类型
  };

  // 节点配置浮窗
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => setSelectedNode(node)}
      >
        <Controls />
        <Background />
      </ReactFlow>

      {/* 节点配置浮窗 */}
      {selectedNode && (
        <NodeConfigPanel
          node={selectedNode}
          onSave={updateNodeConfig}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
};
```

#### 1.4 节点配置面板
```typescript
// NodeConfigPanel.tsx
const NodeConfigPanel = ({ node, onSave, onClose }) => {
  const [config, setConfig] = useState(node.data.config);

  // 根据节点类型渲染不同的配置表单
  const renderConfigForm = () => {
    switch (node.type) {
      case 'llm':
        return <LLMConfigForm config={config} onChange={setConfig} />;
      case 'condition':
        return <ConditionConfigForm config={config} onChange={setConfig} />;
      case 'http':
        return <HttpConfigForm config={config} onChange={setConfig} />;
      default:
        return <div>暂不支持此节点类型的配置</div>;
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>配置 {node.data.label}</DialogTitle>
        </DialogHeader>
        {renderConfigForm()}
        <DialogFooter>
          <Button onClick={() => onSave(node.id, config)}>保存</Button>
          <Button variant="outline" onClick={onClose}>取消</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

### 2. 后端工作流执行引擎

#### 2.1 执行器核心
```python
# workflow_executor.py
class WorkflowExecutor:
    def __init__(self):
        self.litellm_client = LiteLLMClient()
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: str
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """执行工作流并实时返回状态"""

        # 1. 获取工作流配置
        workflow = await self.get_workflow(workflow_id)

        # 2. 创建执行上下文
        context = ExecutionContext(
            workflow_id=workflow_id,
            user_id=user_id,
            variables=input_data
        )

        # 3. 验证工作流
        if not self.validate_workflow(workflow):
            yield ExecutionEvent(type="error", message="工作流配置无效")
            return

        # 4. 执行节点
        execution_order = self.get_execution_order(workflow)

        for node in execution_order:
            yield ExecutionEvent(
                type="node_start",
                node_id=node.id,
                message=f"开始执行节点: {node.name}"
            )

            try:
                result = await self.execute_node(node, context)
                context.update_variables(result)

                yield ExecutionEvent(
                    type="node_complete",
                    node_id=node.id,
                    data=result,
                    message=f"节点执行完成: {node.name}"
                )

            except Exception as e:
                yield ExecutionEvent(
                    type="node_error",
                    node_id=node.id,
                    error=str(e),
                    message=f"节点执行失败: {node.name}"
                )
                break

        yield ExecutionEvent(
            type="workflow_complete",
            data=context.get_final_output(),
            message="工作流执行完成"
        )

    async def execute_node(self, node: NodeConfig, context: ExecutionContext):
        """执行单个节点"""
        if node.type == NodeType.LLM:
            return await self.execute_llm_node(node, context)
        elif node.type == NodeType.CONDITION:
            return await self.execute_condition_node(node, context)
        elif node.type == NodeType.HTTP_REQUEST:
            return await self.execute_http_node(node, context)
        # ... 其他节点类型

    async def execute_llm_node(self, node: NodeConfig, context: ExecutionContext):
        """执行 LLM 节点"""
        config = node.config

        # 构建提示词
        prompt = self.build_prompt(config.get("prompt_template", ""), context)

        # 调用 LLM
        response = await self.litellm_client.completion(
            model=config.get("model", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1000)
        )

        return {
            "output": response.choices[0].message.content,
            "usage": response.usage.dict() if response.usage else None
        }
```

#### 2.2 实时状态跟踪
```python
# websocket_manager.py
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def broadcast_execution_event(self, user_id: str, event: ExecutionEvent):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(event.dict())

# FastAPI WebSocket 端点
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # 保持连接
            await websocket.receive_text()
    except WebSocketDisconnect:
        del manager.active_connections[user_id]

# 执行工作流的 API
@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: ExecutionRequest,
    current_user = Depends(get_current_user)
):
    # 启动异步执行
    task = asyncio.create_task(
        execute_workflow_with_events(workflow_id, request.input_data, current_user.id)
    )

    return {"execution_id": str(uuid4()), "status": "started"}

async def execute_workflow_with_events(workflow_id: str, input_data: dict, user_id: str):
    """执行工作流并发送实时事件"""
    executor = WorkflowExecutor()

    async for event in executor.execute_workflow(workflow_id, input_data, user_id):
        await manager.broadcast_execution_event(user_id, event)
```

### 3. Prompt 解析 (MVP 简化版)

#### 3.1 意图识别
```python
# prompt_analyzer.py
class PromptAnalyzer:
    def __init__(self):
        self.litellm_client = LiteLLMClient()

    async def analyze_prompt(self, prompt: str) -> WorkflowBlueprint:
        """分析用户提示并生成工作流蓝图"""

        # 使用 LLM 分析意图
        analysis_prompt = f"""
        分析以下用户需求，提取关键信息并生成工作流结构：

        用户需求: "{prompt}"

        请返回 JSON 格式的分析结果：
        {{
            "intent": "客服助手/内容生成/数据分析/其他",
            "entities": ["关键实体1", "关键实体2"],
            "complexity": "simple/medium/complex",
            "suggested_nodes": [
                {{
                    "type": "start",
                    "name": "开始",
                    "description": "工作流开始点"
                }},
                {{
                    "type": "llm",
                    "name": "AI 处理",
                    "description": "使用 AI 处理用户输入",
                    "config": {{
                        "model": "gpt-3.5-turbo",
                        "prompt_template": "处理用户请求: {{{{input}}}}"
                    }}
                }},
                {{
                    "type": "output",
                    "name": "输出结果",
                    "description": "返回处理结果"
                }}
            ],
            "suggested_connections": [
                {{"source": "start", "target": "llm"}},
                {{"source": "llm", "target": "output"}}
            ]
        }}
        """

        response = await self.litellm_client.completion(
            model="gpt-4",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3
        )

        try:
            result = json.loads(response.choices[0].message.content)
            return WorkflowBlueprint(**result)
        except json.JSONDecodeError:
            # 降级处理
            return self.create_default_workflow(prompt)

    def create_default_workflow(self, prompt: str) -> WorkflowBlueprint:
        """创建默认的简单工作流"""
        return WorkflowBlueprint(
            intent="其他",
            entities=[],
            complexity="simple",
            suggested_nodes=[
                NodeBlueprint(type="start", name="开始"),
                NodeBlueprint(
                    type="llm",
                    name="AI 处理",
                    config={"prompt_template": f"处理以下请求: {prompt}\n\n用户输入: {{{{input}}}}"}
                ),
                NodeBlueprint(type="output", name="输出结果")
            ],
            suggested_connections=[
                {"source": "start", "target": "llm"},
                {"source": "llm", "target": "output"}
            ]
        )
```

#### 3.2 工作流模板
```python
# workflow_templates.py
WORKFLOW_TEMPLATES = {
    "客服助手": {
        "nodes": [
            {"type": "start", "name": "用户输入"},
            {"type": "llm", "name": "意图识别", "config": {"prompt_template": "分析用户意图: {{input}}"}},
            {"type": "condition", "name": "判断类型", "config": {"condition": "intent == 'complaint'"}},
            {"type": "llm", "name": "生成回复", "config": {"prompt_template": "友好回复用户: {{input}}"}},
            {"type": "output", "name": "返回答案"}
        ],
        "connections": [
            {"source": "start", "target": "意图识别"},
            {"source": "意图识别", "target": "判断类型"},
            {"source": "判断类型", "target": "生成回复"},
            {"source": "生成回复", "target": "output"}
        ]
    },

    "内容生成": {
        "nodes": [
            {"type": "start", "name": "内容主题"},
            {"type": "llm", "name": "大纲生成", "config": {"prompt_template": "为主题生成大纲: {{input}}"}},
            {"type": "llm", "name": "内容撰写", "config": {"prompt_template": "根据大纲撰写文章: {{outline}}"}},
            {"type": "output", "name": "输出文章"}
        ]
    }
}
```

### 4. 数据库设计 (Supabase)

```sql
-- 工作流表
CREATE TABLE workflows (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id TEXT NOT NULL, -- Clerk user ID
    workflow_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 执行历史
CREATE TABLE workflow_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id),
    user_id TEXT NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_log JSONB
);

-- 节点执行日志
CREATE TABLE node_execution_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    execution_id UUID REFERENCES workflow_executions(id),
    node_id VARCHAR(255) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- 启用 RLS (Row Level Security)
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;

-- RLS 策略
CREATE POLICY "Users can only access their own workflows" ON workflows
    FOR ALL USING (auth.jwt() ->> 'sub' = user_id);
```

### 5. 前端集成

#### 5.1 下拉面板实现
```typescript
// WorkflowPanel.tsx
const WorkflowPanel = ({ isVisible, workflow, onClose }) => {
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [executionLogs, setExecutionLogs] = useState<ExecutionEvent[]>([]);

  // WebSocket 连接
  useEffect(() => {
    if (isVisible) {
      const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);

      ws.onmessage = (event) => {
        const executionEvent = JSON.parse(event.data);
        setExecutionLogs(prev => [...prev, executionEvent]);

        if (executionEvent.type === 'workflow_complete') {
          setExecutionStatus('completed');
        } else if (executionEvent.type === 'error') {
          setExecutionStatus('error');
        }
      };

      return () => ws.close();
    }
  }, [isVisible, userId]);

  return (
    <div className={`fixed inset-x-0 top-0 h-full bg-white transform transition-transform duration-300 ease-in-out z-50 ${
      isVisible ? 'translate-y-0' : '-translate-y-full'
    }`}>
      <div className="h-full flex flex-col">
        {/* 面板头部 */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">AI 工作流编辑器</h2>
          <Button variant="ghost" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* 工作流编辑区域 */}
        <div className="flex-1 flex">
          <div className="flex-1 relative">
            <WorkflowEditor workflow={workflow} onChange={updateWorkflow} />
          </div>

          {/* 右侧面板 */}
          <div className="w-80 border-l bg-gray-50">
            <Tabs defaultValue="properties">
              <TabsList className="w-full">
                <TabsTrigger value="properties">属性</TabsTrigger>
                <TabsTrigger value="execution">执行</TabsTrigger>
              </TabsList>

              <TabsContent value="properties" className="p-4">
                <NodePropertiesPanel selectedNode={selectedNode} />
              </TabsContent>

              <TabsContent value="execution" className="p-4">
                <ExecutionPanel
                  status={executionStatus}
                  logs={executionLogs}
                  onExecute={executeWorkflow}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};
```

## 开发顺序

### Week 1-2: 基础架构
1. FastAPI 后端搭建 + Clerk 集成
2. Supabase 数据库设计和连接
3. 基础工作流数据模型

### Week 3-4: 工作流引擎
1. 节点执行器实现
2. WebSocket 实时通信
3. 基础节点类型 (Start, LLM, Output)

### Week 5-6: 前端编辑器
1. React Flow 集成
2. 可视化工作流编辑
3. 节点配置面板

### Week 7-8: Prompt 解析 + 整合
1. LLM 意图分析
2. 自动工作流生成
3. 系统集成测试

您希望我先从哪个模块开始具体实现代码？
