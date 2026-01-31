"""Types for Claude Agent SDK integration"""

from typing import Any

from pydantic import BaseModel, Field


class CodeFile(BaseModel):
    """A code file ready to be written to sandbox"""

    code_block_id: str
    filename: str  # e.g., "github_fetcher.py"
    source: str  # Full source code
    entrypoint: str  # Function to call
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    language: str
    dependencies: list[str] = Field(default_factory=list)
    verdict_score: float
    thumbs_up: int
    thumbs_down: int
    similarity_score: float = 0.0  # Pinecone semantic similarity (0-1)
    combined_score: float = 0.0  # Combined score: similarity * 0.6 + verdict * 0.4


class GetCodeFilesResponse(BaseModel):
    """Response with code files for a task"""

    files: list[CodeFile]
    task: str
    total_found: int
    add_to_llm_prompt: str = ""  # Pre-formatted string to append to LLM system prompt
