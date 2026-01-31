"""RaySurfer SDK types - mirrors the backend API types"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionState(str, Enum):
    """Technical execution outcome - NOT a quality judgment"""

    COMPLETED = "completed"
    ERRORED = "errored"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class AgentVerdict(str, Enum):
    """Agent's judgment on whether an execution was useful"""

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    PENDING = "pending"


class SnipsDesired(str, Enum):
    """Scope of private snippets for retrieval"""

    COMPANY = "company"  # Organization-level snippets (Team or Enterprise tier)
    CLIENT = "client"  # Client workspace snippets (Enterprise tier only)


class CodeBlock(BaseModel):
    """A stored code block with metadata for semantic retrieval"""

    id: str
    name: str
    description: str
    source: str
    entrypoint: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    language: str
    language_version: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    example_queries: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExecutionIO(BaseModel):
    """Stores the actual input/output data"""

    input_data: dict[str, Any]
    input_hash: str = ""
    output_data: Any = None
    output_hash: str = ""
    output_type: str = "unknown"


class AgentReview(BaseModel):
    """Agent's assessment of whether an execution was useful"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    verdict: AgentVerdict
    reasoning: str
    what_worked: list[str] = Field(default_factory=list)
    what_didnt_work: list[str] = Field(default_factory=list)
    output_was_useful: bool
    output_was_correct: bool
    output_was_complete: bool
    error_was_appropriate: bool | None = None
    would_use_again: bool
    suggested_improvements: list[str] = Field(default_factory=list)
    required_workaround: bool = False
    workaround_description: str | None = None


class ExecutionRecord(BaseModel):
    """Full execution trace"""

    id: str
    code_block_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_state: ExecutionState
    duration_ms: int
    error_message: str | None = None
    error_type: str | None = None
    io: ExecutionIO
    triggering_task: str
    retrieval_score: float = 0.0
    verdict: AgentVerdict = AgentVerdict.PENDING
    review: AgentReview | None = None


class BestMatch(BaseModel):
    """The best matching code block with full scoring"""

    code_block: CodeBlock
    combined_score: float
    vector_score: float
    verdict_score: float
    error_resilience: float
    thumbs_up: int
    thumbs_down: int


class AlternativeCandidate(BaseModel):
    """An alternative candidate code block"""

    code_block_id: str
    name: str
    combined_score: float
    reason: str


class FewShotExample(BaseModel):
    """A few-shot example for code generation"""

    task: str
    input_sample: dict[str, Any]
    output_sample: Any
    code_snippet: str


class TaskPattern(BaseModel):
    """A proven task→code mapping"""

    task_pattern: str
    code_block_id: str
    code_block_name: str
    thumbs_up: int
    thumbs_down: int
    verdict_score: float
    error_resilience: float
    last_thumbs_up: datetime | None = None
    last_thumbs_down: datetime | None = None


# Response types
class StoreCodeBlockResponse(BaseModel):
    success: bool
    code_block_id: str
    embedding_id: str
    message: str


class StoreExecutionResponse(BaseModel):
    success: bool
    execution_id: str
    pattern_updated: bool
    message: str


class RetrieveCodeBlockResponse(BaseModel):
    code_blocks: list["CodeBlockMatch"]
    total_found: int


class CodeBlockMatch(BaseModel):
    code_block: CodeBlock
    score: float
    verdict_score: float
    thumbs_up: int
    thumbs_down: int
    recent_executions: list[ExecutionRecord] = Field(default_factory=list)


class RetrieveBestResponse(BaseModel):
    best_match: BestMatch | None
    alternative_candidates: list[AlternativeCandidate]
    retrieval_confidence: str


class FileWritten(BaseModel):
    """A file written during agent execution"""

    path: str
    content: str


class SubmitExecutionResultRequest(BaseModel):
    """Raw execution result - backend handles all processing"""

    task: str
    files_written: list[FileWritten]
    succeeded: bool


class SubmitExecutionResultResponse(BaseModel):
    """Response from submitting execution result"""

    success: bool
    code_blocks_stored: int
    message: str


# Auto Review API
class AutoReviewResponse(BaseModel):
    """Response with auto-generated review"""

    success: bool
    execution_id: str
    review: AgentReview
    message: str


# Retrieve Executions API
class RetrieveExecutionsResponse(BaseModel):
    """Response with executions"""

    executions: list[ExecutionRecord]
    total_found: int
