"""
Workflow execution models for πlot
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class ExecutionStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class NodeExecutionStatus(str, Enum):
    """Individual node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionEventType(str, Enum):
    """Types of execution events"""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_SKIPPED = "node_skipped"
    VARIABLE_UPDATED = "variable_updated"
    LOG_MESSAGE = "log_message"
    PROGRESS_UPDATE = "progress_update"


class ExecutionEvent(BaseModel):
    """Real-time execution event"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    type: ExecutionEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    node_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0


class NodeExecutionLog(BaseModel):
    """Log entry for individual node execution"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    node_id: str
    node_type: str
    node_name: str
    status: NodeExecutionStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None

    @property
    def duration_ms(self) -> Optional[int]:
        """Calculate execution duration in milliseconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


class WorkflowExecutionBase(BaseModel):
    """Base workflow execution model"""
    workflow_id: str
    user_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    total_tokens_used: Optional[int] = None
    total_cost: Optional[float] = None
    execution_context: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """Model for creating a new workflow execution"""
    pass


class WorkflowExecution(WorkflowExecutionBase):
    """Complete workflow execution model"""
    id: str
    output_data: Optional[Dict[str, Any]] = None
    node_logs: List[NodeExecutionLog] = Field(default_factory=list)
    events: List[ExecutionEvent] = Field(default_factory=list)
    progress: float = 0.0  # 0.0 to 1.0
    current_node_id: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[int]:
        """Calculate total execution duration in milliseconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running"""
        return self.status == ExecutionStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)"""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    def add_event(self, event_type: ExecutionEventType, **kwargs) -> ExecutionEvent:
        """Add a new execution event"""
        event = ExecutionEvent(
            execution_id=self.id,
            type=event_type,
            **kwargs
        )
        self.events.append(event)
        return event

    def add_node_log(self, node_log: NodeExecutionLog):
        """Add a node execution log"""
        self.node_logs.append(node_log)

        # Update current node
        if node_log.status == NodeExecutionStatus.RUNNING:
            self.current_node_id = node_log.node_id
        elif node_log.status in [NodeExecutionStatus.COMPLETED, NodeExecutionStatus.FAILED]:
            self.current_node_id = None

    def update_progress(self, progress: float):
        """Update execution progress"""
        self.progress = max(0.0, min(1.0, progress))
        self.add_event(
            ExecutionEventType.PROGRESS_UPDATE,
            progress=self.progress,
            message=f"Progress: {self.progress * 100:.1f}%"
        )


class WorkflowExecutionInDB(WorkflowExecution):
    """Workflow execution model as stored in database"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExecutionRequest(BaseModel):
    """Request model for executing a workflow"""
    input_data: Dict[str, Any] = Field(default_factory=dict)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Execution options
    timeout_seconds: Optional[int] = 300  # 5 minutes default
    max_retries: int = 0
    retry_delay_seconds: int = 1

    # Debugging options
    debug_mode: bool = False
    save_intermediate_results: bool = True


class ExecutionResponse(BaseModel):
    """Response model for workflow execution"""
    execution_id: str
    status: ExecutionStatus
    message: str = "Execution started"
    estimated_duration_ms: Optional[int] = None


class ExecutionStats(BaseModel):
    """Statistics for workflow executions"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration_ms: Optional[float] = None
    total_tokens_used: Optional[int] = None
    total_cost: Optional[float] = None
    success_rate: float = 0.0

    @property
    def failure_rate(self) -> float:
        return 1.0 - self.success_rate


class ExecutionSummary(BaseModel):
    """Summary of a workflow execution"""
    id: str
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    success: bool = False
