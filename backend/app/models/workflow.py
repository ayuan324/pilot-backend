"""
Workflow data models for πlot
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class NodeType(str, Enum):
    """Available node types in the workflow (based on Dify architecture)"""
    # Core nodes
    START = "start"
    END = "end"
    
    # LLM nodes
    LLM = "llm"
    CHAT = "chat"
    
    # Logic nodes
    CONDITION = "condition"
    IF_ELSE = "if-else"
    
    # Data processing
    CODE = "code"
    TEMPLATE_TRANSFORM = "template-transform"
    VARIABLE_ASSIGNER = "variable-assigner"
    
    # External integration
    HTTP_REQUEST = "http-request"
    TOOL = "tool"
    
    # Knowledge & RAG
    KNOWLEDGE_RETRIEVAL = "knowledge-retrieval"
    DOC_EXTRACTOR = "doc-extractor"
    
    # Flow control
    LOOP = "loop"
    ITERATION = "iteration"
    
    # Input/Output
    PARAMETER_EXTRACTOR = "parameter-extractor"
    ANSWER = "answer"


class NodePosition(BaseModel):
    """Node position in the workflow canvas"""
    x: float
    y: float


class NodeConfig(BaseModel):
    """Enhanced configuration for different node types (Dify-inspired)"""
    # Common configs
    title: Optional[str] = None
    desc: Optional[str] = None
    
    # LLM Node configs
    model: Optional[str] = "gpt-3.5-turbo"
    prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    top_p: Optional[float] = 1.0
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    
    # Chat node specific
    memory: Optional[Dict[str, Any]] = None
    conversation_variables: Optional[List[str]] = None
    
    # Condition Node configs
    conditions: Optional[List[Dict[str, Any]]] = None
    logical_operator: Optional[str] = "and"  # and, or
    
    # Code Node configs
    code: Optional[str] = None
    code_language: Optional[str] = "python3"
    dependencies: Optional[List[str]] = None
    
    # HTTP Request configs
    method: Optional[str] = "GET"
    url: Optional[str] = None
    authorization: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = 30
    
    # Template Transform configs
    template: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    
    # Knowledge Retrieval configs
    dataset_ids: Optional[List[str]] = None
    query_variable: Optional[str] = None
    retrieval_mode: Optional[str] = "semantic"  # semantic, full_text, hybrid
    top_k: Optional[int] = 3
    score_threshold: Optional[float] = 0.5
    
    # Tool configs
    provider_id: Optional[str] = None
    provider_type: Optional[str] = None
    provider_name: Optional[str] = None
    tool_name: Optional[str] = None
    tool_parameters: Optional[Dict[str, Any]] = None
    
    # Loop configs
    iterator_selector: Optional[List[str]] = None
    output_selector: Optional[List[str]] = None
    output_type: Optional[str] = "array"  # array, object
    
    # Variable Assigner configs
    variable_assignments: Optional[List[Dict[str, Any]]] = None
    
    # Doc Extractor configs
    file_types: Optional[List[str]] = None
    extract_settings: Optional[Dict[str, Any]] = None


class NodeHandle(BaseModel):
    """Input/Output handle for nodes (Dify-style)"""
    id: str
    type: str = "source"  # source, target
    position: str = "right"  # left, right, top, bottom
    data_type: str = "string"  # string, number, object, array, file
    required: bool = False


class WorkflowVariable(BaseModel):
    """Workflow variable definition"""
    variable: str
    label: str
    type: str = "string"  # string, number, select, paragraph, file
    required: bool = False
    max_length: Optional[int] = None
    default: Optional[str] = None
    options: Optional[List[str]] = None  # for select type
    description: Optional[str] = None


class Node(BaseModel):
    """Enhanced workflow node model (Dify-compatible)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    position: NodePosition
    data: NodeConfig = Field(default_factory=NodeConfig)
    
    # Node connections
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    
    # UI properties
    selected: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    
    # Metadata
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    def get_input_variables(self) -> List[str]:
        """Extract input variables from node configuration"""
        variables = []
        if self.data.prompt:
            # Extract variables from prompt template (format: {{variable_name}})
            import re
            variables.extend(re.findall(r'\{\{(\w+)\}\}', self.data.prompt))
        if self.data.template:
            import re
            variables.extend(re.findall(r'\{\{(\w+)\}\}', self.data.template))
        return list(set(variables))

    def get_output_variables(self) -> List[str]:
        """Get output variables for this node type"""
        output_map = {
            NodeType.START: ["sys.query", "sys.files"],
            NodeType.LLM: ["text"],
            NodeType.CHAT: ["text"],
            NodeType.CODE: ["result"],
            NodeType.HTTP_REQUEST: ["body", "status_code", "headers"],
            NodeType.KNOWLEDGE_RETRIEVAL: ["result"],
            NodeType.CONDITION: ["result"],
            NodeType.TEMPLATE_TRANSFORM: ["output"],
            NodeType.DOC_EXTRACTOR: ["text"],
            NodeType.TOOL: ["result"],
        }
        return output_map.get(self.type, ["output"])


class Edge(BaseModel):
    """Connection between nodes (React Flow compatible)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # source node id
    target: str  # target node id
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    type: str = "default"  # default, step, smoothstep, straight
    animated: bool = False
    label: Optional[str] = None
    style: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class WorkflowBase(BaseModel):
    """Base workflow model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    variables: List[WorkflowVariable] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False

    @validator('nodes')
    def validate_nodes(cls, v):
        """Validate that workflow has at least a start node"""
        if not v:
            return v

        start_nodes = [node for node in v if node.type == NodeType.START]
        if not start_nodes:
            raise ValueError("Workflow must have at least one START node")

        return v

    @validator('edges')
    def validate_edges(cls, v, values):
        """Validate that edges reference existing nodes"""
        if not v or 'nodes' not in values:
            return v

        node_ids = {node.id for node in values['nodes']}

        for edge in v:
            if edge.source not in node_ids:
                raise ValueError(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids:
                raise ValueError(f"Edge target '{edge.target}' not found in nodes")

        return v

    def get_workflow_variables(self) -> List[str]:
        """Extract all variables used in the workflow"""
        all_variables = set()
        for node in self.nodes:
            all_variables.update(node.get_input_variables())
        return list(all_variables)


class WorkflowCreate(WorkflowBase):
    """Model for creating a new workflow"""
    pass


class WorkflowUpdate(BaseModel):
    """Model for updating a workflow"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    nodes: Optional[List[Node]] = None
    edges: Optional[List[Edge]] = None
    variables: Optional[List[WorkflowVariable]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class Workflow(WorkflowBase):
    """Complete workflow model with database fields"""
    id: str
    user_id: str
    status: str = "draft"  # draft, published, archived
    version: int = 1
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0


class WorkflowInDB(Workflow):
    """Workflow model as stored in database"""
    pass


class WorkflowTemplate(BaseModel):
    """Workflow template model"""
    id: str
    name: str
    description: str
    category: str
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    estimated_time: str = "5 minutes"
    workflow: WorkflowBase
    tags: List[str] = Field(default_factory=list)
    icon: Optional[str] = None
    preview_image: Optional[str] = None


# Enhanced workflow templates with Dify-style nodes
WORKFLOW_TEMPLATES = {
    "simple_chatbot": WorkflowTemplate(
        id="simple_chatbot",
        name="Simple Chatbot",
        description="A basic conversational AI that responds to user messages with context awareness",
        category="conversational",
        difficulty="beginner",
        estimated_time="2 minutes",
        workflow=WorkflowBase(
            name="Simple Chatbot",
            description="Basic conversational AI workflow with memory",
            nodes=[
                Node(
                    id="start",
                    type=NodeType.START,
                    position=NodePosition(x=100, y=200),
                    data=NodeConfig(
                        title="Start",
                        desc="User input entry point"
                    )
                ),
                Node(
                    id="chat",
                    type=NodeType.CHAT,
                    position=NodePosition(x=400, y=200),
                    data=NodeConfig(
                        title="AI Chat",
                        desc="Conversational AI response",
                        model="gpt-3.5-turbo",
                        prompt="You are a helpful assistant. Please respond to the user's message in a friendly and informative way.\n\nUser: {{sys.query}}",
                        temperature=0.7,
                        max_tokens=500,
                        memory={"type": "conversation_summary", "max_tokens": 2000}
                    )
                ),
                Node(
                    id="answer",
                    type=NodeType.ANSWER,
                    position=NodePosition(x=700, y=200),
                    data=NodeConfig(
                        title="Answer",
                        desc="Final response to user"
                    )
                )
            ],
            edges=[
                Edge(source="start", target="chat"),
                Edge(source="chat", target="answer")
            ],
            variables=[
                WorkflowVariable(
                    variable="sys.query",
                    label="User Input",
                    type="paragraph",
                    required=True,
                    description="The user's message or question"
                )
            ]
        ),
        tags=["chatbot", "conversational", "beginner"],
        icon="💬"
    ),

    "content_generator": WorkflowTemplate(
        id="content_generator",
        name="AI Content Generator",
        description="Generate high-quality articles and blog posts from topics with structured approach",
        category="content",
        difficulty="intermediate",
        estimated_time="5 minutes",
        workflow=WorkflowBase(
            name="AI Content Generator",
            description="Multi-step content generation with outline and writing phases",
            nodes=[
                Node(
                    id="start",
                    type=NodeType.START,
                    position=NodePosition(x=100, y=200),
                    data=NodeConfig(
                        title="Topic Input",
                        desc="Enter the topic for content generation"
                    )
                ),
                Node(
                    id="outline_generator",
                    type=NodeType.LLM,
                    position=NodePosition(x=400, y=200),
                    data=NodeConfig(
                        title="Outline Generator",
                        desc="Create a structured outline for the content",
                        model="gpt-4",
                        prompt="""Create a detailed outline for an article about: {{topic}}

Please provide:
1. A compelling title
2. Introduction points
3. 3-5 main sections with subsections
4. Conclusion points
5. Key takeaways

Format as a structured outline with clear headings.""",
                        temperature=0.6,
                        max_tokens=800
                    )
                ),
                Node(
                    id="content_writer",
                    type=NodeType.LLM,
                    position=NodePosition(x=700, y=200),
                    data=NodeConfig(
                        title="Content Writer",
                        desc="Write the full article based on the outline",
                        model="gpt-4",
                        prompt="""Based on the following outline, write a comprehensive, engaging article:

{{outline_generator.text}}

Requirements:
- Write in a professional yet accessible tone
- Include specific examples and insights
- Ensure smooth transitions between sections
- Aim for 800-1200 words
- Include a strong introduction and conclusion""",
                        temperature=0.7,
                        max_tokens=2000
                    )
                ),
                Node(
                    id="answer",
                    type=NodeType.ANSWER,
                    position=NodePosition(x=1000, y=200),
                    data=NodeConfig(
                        title="Final Article",
                        desc="The completed article ready for publication"
                    )
                )
            ],
            edges=[
                Edge(source="start", target="outline_generator"),
                Edge(source="outline_generator", target="content_writer"),
                Edge(source="content_writer", target="answer")
            ],
            variables=[
                WorkflowVariable(
                    variable="topic",
                    label="Article Topic",
                    type="paragraph",
                    required=True,
                    description="The main topic or subject for the article"
                )
            ]
        ),
        tags=["content", "writing", "articles", "intermediate"],
        icon="✍️"
    ),

    "data_analyzer": WorkflowTemplate(
        id="data_analyzer",
        name="Data Analysis Assistant",
        description="Analyze data files and generate insights with visualizations",
        category="analysis",
        difficulty="advanced",
        estimated_time="10 minutes",
        workflow=WorkflowBase(
            name="Data Analysis Assistant",
            description="Upload data files and get AI-powered analysis and insights",
            nodes=[
                Node(
                    id="start",
                    type=NodeType.START,
                    position=NodePosition(x=100, y=200),
                    data=NodeConfig(
                        title="File Upload",
                        desc="Upload your data file (CSV, Excel, etc.)"
                    )
                ),
                Node(
                    id="doc_extractor",
                    type=NodeType.DOC_EXTRACTOR,
                    position=NodePosition(x=400, y=200),
                    data=NodeConfig(
                        title="Data Extractor",
                        desc="Extract and parse data from uploaded file",
                        file_types=["csv", "xlsx", "json"],
                        extract_settings={"parse_headers": True, "max_rows": 1000}
                    )
                ),
                Node(
                    id="data_analyzer",
                    type=NodeType.CODE,
                    position=NodePosition(x=700, y=200),
                    data=NodeConfig(
                        title="Data Analysis",
                        desc="Analyze the data and generate statistics",
                        code_language="python3",
                        code="""
import pandas as pd
import json

# Parse the extracted data
data_text = "{{doc_extractor.text}}"
try:
    # Try to parse as CSV
    from io import StringIO
    df = pd.read_csv(StringIO(data_text))
    
    # Generate basic statistics
    analysis = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "numeric_summary": df.describe().to_dict() if len(df.select_dtypes(include='number').columns) > 0 else {},
        "sample_data": df.head().to_dict('records')
    }
    
    result = json.dumps(analysis, indent=2, default=str)
except Exception as e:
    result = f"Error analyzing data: {str(e)}"
""",
                        dependencies=["pandas"]
                    )
                ),
                Node(
                    id="insight_generator",
                    type=NodeType.LLM,
                    position=NodePosition(x=1000, y=200),
                    data=NodeConfig(
                        title="Insight Generator",
                        desc="Generate insights and recommendations from the analysis",
                        model="gpt-4",
                        prompt="""Based on the following data analysis results, provide insights and recommendations:

{{data_analyzer.result}}

Please provide:
1. Key findings and patterns
2. Data quality assessment
3. Interesting insights or anomalies
4. Recommendations for further analysis
5. Potential business implications

Format your response in a clear, structured manner.""",
                        temperature=0.6,
                        max_tokens=1000
                    )
                ),
                Node(
                    id="answer",
                    type=NodeType.ANSWER,
                    position=NodePosition(x=1300, y=200),
                    data=NodeConfig(
                        title="Analysis Report",
                        desc="Complete data analysis report with insights"
                    )
                )
            ],
            edges=[
                Edge(source="start", target="doc_extractor"),
                Edge(source="doc_extractor", target="data_analyzer"),
                Edge(source="data_analyzer", target="insight_generator"),
                Edge(source="insight_generator", target="answer")
            ],
            variables=[
                WorkflowVariable(
                    variable="sys.files",
                    label="Data File",
                    type="file",
                    required=True,
                    description="Upload your data file for analysis"
                )
            ]
        ),
        tags=["data", "analysis", "insights", "advanced"],
        icon="📊"
    )
}
