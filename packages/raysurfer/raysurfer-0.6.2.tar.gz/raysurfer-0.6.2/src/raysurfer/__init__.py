"""
RaySurfer Python SDK - Drop-in replacement for Claude Agent SDK with caching.

Simply swap your import and rename your client:

    # Before
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    client = ClaudeSDKClient(options)
    await client.query("task")

    # After
    from raysurfer import RaysurferClient
    from claude_agent_sdk import ClaudeAgentOptions
    client = RaysurferClient(options)
    await client.query("task")

Options come directly from claude_agent_sdk - no Raysurfer-specific options needed.
Set RAYSURFER_API_KEY to enable caching.
"""

# Main client
# Direct API clients (for advanced use cases)
from raysurfer._version import __version__  # noqa: E402
from raysurfer.client import AsyncRaySurfer, RaySurfer

# Exceptions
from raysurfer.exceptions import (
    APIError,
    AuthenticationError,
    CacheUnavailableError,
    RateLimitError,
    RaySurferError,
    ValidationError,
)

# Re-export Claude Agent SDK types for convenience (use these directly)
from raysurfer.sdk_client import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    Message,
    RaysurferClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

# Types for direct API usage
from raysurfer.sdk_types import CodeFile, GetCodeFilesResponse
from raysurfer.types import (
    AgentReview,
    AgentVerdict,
    BestMatch,
    CodeBlock,
    ExecutionIO,
    ExecutionRecord,
    ExecutionState,
    FewShotExample,
    FileWritten,
    SubmitExecutionResultResponse,
    TaskPattern,
)

__all__ = [
    # Main client
    "RaysurferClient",
    # Re-exported from Claude Agent SDK (use these directly)
    "ClaudeAgentOptions",
    "AgentDefinition",
    "HookMatcher",
    "Message",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "TextBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    # Direct API clients
    "RaySurfer",
    "AsyncRaySurfer",
    # Types
    "AgentReview",
    "AgentVerdict",
    "BestMatch",
    "CodeBlock",
    "CodeFile",
    "ExecutionIO",
    "ExecutionRecord",
    "ExecutionState",
    "FewShotExample",
    "FileWritten",
    "GetCodeFilesResponse",
    "SubmitExecutionResultResponse",
    "TaskPattern",
    # Exceptions
    "RaySurferError",
    "APIError",
    "AuthenticationError",
    "CacheUnavailableError",
    "RateLimitError",
    "ValidationError",
    # Version
    "__version__",
]
