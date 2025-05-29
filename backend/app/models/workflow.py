"""
Workflow data models for πlot
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class NodeType(str, Enum):
    """Available node types in the workflow"""
    START = "start"
    LLM = "llm"
    PROMPT_TEMPLATE = "prompt_template"
    CONDITION = "condition"
    CODE = "code"
    HTTP_REQUEST = "http"
    VARIABLE = "variable"
    OUTPUT = "output"
    LOOP = "loop"
    KNOWLEDGE_RETRIEVAL = "knowledge"
    TOOL_CALL = "tool"


class NodePosition(BaseModel):
    """Node position on the canvas"""
    x: float
    y: float


class NodeConfig(BaseModel):
    """Configuration for different node types"""
    # Common configs
    name: Optional[str] = None
    description: Optional[str] = None

    # LLM Node configs
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    prompt_template: Optional[str] = None
    system_message: Optional[str] = None

    # Condition Node configs
    condition_logic: Optional[str] = None
    condition_type: Optional[str] = "simple"  # simple, expression, ai

    # HTTP Request configs
    method: Optional[str] = "GET"
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = {}
    body: Optional[Dict[str, Any]] = {}

    # Code Node configs
    code: Optional[str] = None
    language: Optional[str] = "python"

    # Variable Node configs
    variable_name: Optional[str] = None
    variable_value: Optional[Union[str, int, float, bool, Dict, List]] = None
    variable_type: Optional[str] = "string"

    # Output Node configs
    output_format: Optional[str] = "text"
    output_template: Optional[str] = None

    # Loop Node configs
    loop_type: Optional[str] = "for"  # for, while, foreach
    loop_condition: Optional[str] = None
    max_iterations: Optional[int] = 10

    # Knowledge Retrieval configs
    knowledge_base_id: Optional[str] = None
    query_type: Optional[str] = "semantic"  # semantic, keyword, hybrid
    top_k: Optional[int] = 3

    # Tool Call configs
    tool_name: Optional[str] = None
    tool_parameters: Optional[Dict[str, Any]] = {}


class NodeHandle(BaseModel):
    """Input/Output handle for nodes"""
    id: str
    type: str = "default"  # default, condition_true, condition_false
    label: Optional[str] = None
    data_type: Optional[str] = "any"  # any, string, number, boolean, object, array


class Node(BaseModel):
    """Workflow node model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    position: NodePosition
    config: NodeConfig = Field(default_factory=NodeConfig)
    inputs: List[NodeHandle] = Field(default_factory=list)
    outputs: List[NodeHandle] = Field(default_factory=list)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context) -> None:
        """Ensure nodes have default input/output handles after model creation"""
        if not self.inputs:
            if self.type != NodeType.START:
                self.inputs = [NodeHandle(id="input", label="Input")]
        
        if not self.outputs:
            if self.type != NodeType.OUTPUT:
                if self.type == NodeType.CONDITION:
                    self.outputs = [
                        NodeHandle(id="true", type="condition_true", label="True"),
                        NodeHandle(id="false", type="condition_false", label="False")
                    ]
                else:
                    self.outputs = [NodeHandle(id="output", label="Output")]


class Edge(BaseModel):
    """Connection between nodes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # source node id
    target: str  # target node id
    source_handle: str = "output"
    target_handle: str = "input"
    label: Optional[str] = None
    animated: bool = False
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class WorkflowVariable(BaseModel):
    """Global workflow variable"""
    name: str
    value: Union[str, int, float, bool, Dict, List, None] = None
    type: str = "string"
    description: Optional[str] = None
    is_input: bool = False
    is_output: bool = False


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
    """Complete workflow model with metadata"""
    id: str
    user_id: str
    status: str = "draft"  # draft, published, archived
    version: int = 1
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0

    class Config:
        from_attributes = True


class WorkflowInDB(Workflow):
    """Workflow model as stored in database"""
    pass


# Workflow Templates for quick start
class WorkflowTemplate(BaseModel):
    """Pre-built workflow template"""
    id: str
    name: str
    description: str
    category: str
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    estimated_time: Optional[str] = None
    workflow: WorkflowBase
    preview_image: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


# Standard workflow templates
WORKFLOW_TEMPLATES = {
    "simple_chatbot": WorkflowTemplate(
        id="simple_chatbot",
        name="Simple Chatbot",
        description="A basic chatbot that responds to user messages",
        category="conversational",
        difficulty="beginner",
        estimated_time="2 minutes",
        workflow=WorkflowBase(
            name="Simple Chatbot",
            description="Basic conversational AI workflow",
            nodes=[
                Node(
                    id="start",
                    type=NodeType.START,
                    position=NodePosition(x=100, y=100),
                    config=NodeConfig(name="User Input"),
                    outputs=[NodeHandle(id="output", label="User Message")]
                ),
                Node(
                    id="llm",
                    type=NodeType.LLM,
                    position=NodePosition(x=300, y=100),
                    config=NodeConfig(
                        name="AI Response",
                        model="gpt-3.5-turbo",
                        temperature=0.7,
                        prompt_template="You are a helpful assistant. Respond to the user's message: {input}"
                    )
                ),
                Node(
                    id="output",
                    type=NodeType.OUTPUT,
                    position=NodePosition(x=500, y=100),
                    config=NodeConfig(name="Bot Response"),
                    inputs=[NodeHandle(id="input", label="Response")]
                )
            ],
            edges=[
                Edge(source="start", target="llm"),
                Edge(source="llm", target="output")
            ],
            variables=[
                WorkflowVariable(name="input", type="string", is_input=True),
                WorkflowVariable(name="output", type="string", is_output=True)
            ]
        ),
        tags=["chatbot", "conversational", "beginner"]
    ),

    "content_generator": WorkflowTemplate(
        id="content_generator",
        name="Content Generator",
        description="Generate blog posts or articles from a topic",
        category="content",
        difficulty="intermediate",
        estimated_time="5 minutes",
        workflow=WorkflowBase(
            name="Content Generator",
            description="AI-powered content generation workflow",
            nodes=[
                Node(
                    id="start",
                    type=NodeType.START,
                    position=NodePosition(x=100, y=100),
                    config=NodeConfig(name="Topic Input")
                ),
                Node(
                    id="outline",
                    type=NodeType.LLM,
                    position=NodePosition(x=300, y=100),
                    config=NodeConfig(
                        name="Generate Outline",
                        prompt_template="Create a detailed outline for an article about: {input}"
                    )
                ),
                Node(
                    id="content",
                    type=NodeType.LLM,
                    position=NodePosition(x=500, y=100),
                    config=NodeConfig(
                        name="Write Content",
                        prompt_template="Write a comprehensive article based on this outline: {outline}"
                    )
                ),
                Node(
                    id="output",
                    type=NodeType.OUTPUT,
                    position=NodePosition(x=700, y=100),
                    config=NodeConfig(name="Final Article")
                )
            ],
            edges=[
                Edge(source="start", target="outline"),
                Edge(source="outline", target="content"),
                Edge(source="content", target="output")
            ]
        ),
        tags=["content", "writing", "articles", "intermediate"]
    )
}
