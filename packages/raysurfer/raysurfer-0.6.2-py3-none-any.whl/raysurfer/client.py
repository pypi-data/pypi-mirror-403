"""RaySurfer SDK client"""

import asyncio
import logging
from typing import Any

import httpx

from raysurfer._version import __version__
from raysurfer.exceptions import (
    APIError,
    AuthenticationError,
    CacheUnavailableError,
    RateLimitError,
)
from raysurfer.sdk_types import CodeFile, GetCodeFilesResponse
from raysurfer.types import (
    AgentReview,
    AgentVerdict,
    AlternativeCandidate,
    AutoReviewResponse,
    BestMatch,
    CodeBlock,
    CodeBlockMatch,
    ExecutionIO,
    ExecutionRecord,
    ExecutionState,
    FewShotExample,
    FileWritten,
    RetrieveBestResponse,
    RetrieveCodeBlockResponse,
    RetrieveExecutionsResponse,
    SnipsDesired,
    StoreCodeBlockResponse,
    StoreExecutionResponse,
    SubmitExecutionResultResponse,
    TaskPattern,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.raysurfer.com"

# Maximum number of retry attempts for transient failures
MAX_RETRIES = 3
# Base delay in seconds for exponential backoff
RETRY_BASE_DELAY = 0.5
# HTTP status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class AsyncRaySurfer:
    """Async client for RaySurfer API"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        organization_id: str | None = None,
        workspace_id: str | None = None,
        snips_desired: SnipsDesired | str | None = None,
        namespace: str | None = None,
    ):
        """
        Initialize the RaySurfer async client.

        Args:
            api_key: RaySurfer API key (or set RAYSURFER_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            organization_id: Optional organization ID for dedicated namespace (team/enterprise)
            workspace_id: Optional workspace ID for client-specific namespace (enterprise only)
            snips_desired: Scope of private snippets - "company" (Team/Enterprise) or "client" (Enterprise only)
            namespace: Custom namespace for code storage/retrieval (overrides org-based namespacing)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.organization_id = organization_id
        self.workspace_id = workspace_id
        self.namespace = namespace
        # Convert string to SnipsDesired if needed
        if isinstance(snips_desired, str):
            self.snips_desired = SnipsDesired(snips_desired) if snips_desired else None
        else:
            self.snips_desired = snips_desired
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            # Add organization/workspace headers for namespace routing
            if self.organization_id:
                headers["X-Raysurfer-Org-Id"] = self.organization_id
            if self.workspace_id:
                headers["X-Raysurfer-Workspace-Id"] = self.workspace_id
            # Add snippet retrieval scope headers
            if self.snips_desired:
                headers["X-Raysurfer-Snips-Desired"] = self.snips_desired.value
            # Custom namespace override
            if self.namespace:
                headers["X-Raysurfer-Namespace"] = self.namespace
            # SDK version for tracking
            headers["X-Raysurfer-SDK-Version"] = f"python/{__version__}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncRaySurfer":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        client = await self._get_client()
        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.request(method, path, **kwargs)

                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else RETRY_BASE_DELAY * (2 ** attempt)
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Rate limited, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(delay)
                        continue
                    raise RateLimitError(retry_after=delay)
                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_BASE_DELAY * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(delay)
                        continue
                if response.status_code >= 400:
                    raise APIError(response.text, status_code=response.status_code)

                return response.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"Network error: {e}, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    continue
                raise CacheUnavailableError(f"Failed to connect after {MAX_RETRIES} attempts: {e}") from e

        # Should not reach here, but just in case
        raise CacheUnavailableError(f"Request failed after {MAX_RETRIES} attempts") from last_exception

    # =========================================================================
    # Store API
    # =========================================================================

    async def store_code_block(
        self,
        name: str,
        source: str,
        entrypoint: str,
        language: str,
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        language_version: str | None = None,
        dependencies: list[str] | None = None,
        tags: list[str] | None = None,
        capabilities: list[str] | None = None,
        example_queries: list[str] | None = None,
    ) -> StoreCodeBlockResponse:
        """Store a new code block"""
        data = {
            "name": name,
            "description": description,
            "source": source,
            "entrypoint": entrypoint,
            "language": language,
            "input_schema": input_schema or {},
            "output_schema": output_schema or {},
            "language_version": language_version,
            "dependencies": dependencies or [],
            "tags": tags or [],
            "capabilities": capabilities or [],
            "example_queries": example_queries,
        }
        result = await self._request("POST", "/api/store/code-block", json=data)
        return StoreCodeBlockResponse(**result)

    async def store_execution(
        self,
        code_block_id: str,
        triggering_task: str,
        input_data: dict[str, Any],
        output_data: Any,
        execution_state: ExecutionState = ExecutionState.COMPLETED,
        duration_ms: int = 0,
        error_message: str | None = None,
        error_type: str | None = None,
        verdict: AgentVerdict | None = None,
        review: AgentReview | None = None,
    ) -> StoreExecutionResponse:
        """Store an execution record"""
        io = ExecutionIO(
            input_data=input_data,
            output_data=output_data,
            output_type=type(output_data).__name__,
        )
        data = {
            "code_block_id": code_block_id,
            "triggering_task": triggering_task,
            "io": io.model_dump(),
            "execution_state": execution_state.value,
            "duration_ms": duration_ms,
            "error_message": error_message,
            "error_type": error_type,
            "verdict": verdict.value if verdict else None,
            "review": review.model_dump() if review else None,
        }
        result = await self._request("POST", "/api/store/execution", json=data)
        return StoreExecutionResponse(**result)

    async def upload_new_code_snips(
        self,
        task: str,
        files_written: list[FileWritten],
        succeeded: bool,
        auto_vote: bool = True,
        execution_logs: str | None = None,
    ) -> SubmitExecutionResultResponse:
        """
        Upload new code snippets from an execution.

        This is the simplified API for agent integrations. Just send:
        - The task that was executed
        - Files that were written during execution
        - Whether the task succeeded
        - Whether to auto-vote on stored blocks (default: True)
        - Captured execution logs for vote context

        Backend handles: entrypoint detection, tag extraction, language detection,
        deduplication, quality checks, and storage.
        """
        data: dict[str, Any] = {
            "task": task,
            "files_written": [f.model_dump() for f in files_written],
            "succeeded": succeeded,
            "auto_vote": auto_vote,
        }
        if execution_logs is not None:
            data["execution_logs"] = execution_logs
        result = await self._request("POST", "/api/store/execution-result", json=data)
        return SubmitExecutionResultResponse(**result)

    # =========================================================================
    # Retrieve API
    # =========================================================================

    async def get_code_snips(
        self,
        task: str,
        top_k: int = 10,
        min_verdict_score: float = 0.0,
    ) -> RetrieveCodeBlockResponse:
        """
        Get cached code snippets for a task.

        Searches for code blocks by task description using semantic search.
        """
        data = {
            "task": task,
            "top_k": top_k,
            "min_verdict_score": min_verdict_score,
        }
        result = await self._request("POST", "/api/retrieve/code-blocks", json=data)

        code_blocks = [
            CodeBlockMatch(
                code_block=CodeBlock(**cb["code_block"]),
                score=cb["score"],
                verdict_score=cb["verdict_score"],
                thumbs_up=cb["thumbs_up"],
                thumbs_down=cb["thumbs_down"],
                recent_executions=cb.get("recent_executions", []),
            )
            for cb in result["code_blocks"]
        ]
        return RetrieveCodeBlockResponse(
            code_blocks=code_blocks,
            total_found=result["total_found"],
        )

    async def retrieve_best(
        self,
        task: str,
        top_k: int = 10,
        min_verdict_score: float = 0.0,
    ) -> RetrieveBestResponse:
        """Get the single best code block for a task using verdict-aware scoring"""
        data = {
            "task": task,
            "top_k": top_k,
            "min_verdict_score": min_verdict_score,
        }
        result = await self._request("POST", "/api/retrieve/best-for-task", json=data)

        best_match = None
        if result.get("best_match"):
            bm = result["best_match"]
            best_match = BestMatch(
                code_block=CodeBlock(**bm["code_block"]),
                combined_score=bm["combined_score"],
                vector_score=bm["vector_score"],
                verdict_score=bm["verdict_score"],
                error_resilience=bm["error_resilience"],
                thumbs_up=bm["thumbs_up"],
                thumbs_down=bm["thumbs_down"],
            )

        alternatives = [AlternativeCandidate(**alt) for alt in result.get("alternative_candidates", [])]

        return RetrieveBestResponse(
            best_match=best_match,
            alternative_candidates=alternatives,
            retrieval_confidence=result["retrieval_confidence"],
        )

    async def get_few_shot_examples(
        self,
        task: str,
        k: int = 3,
    ) -> list[FewShotExample]:
        """Retrieve few-shot examples for code generation"""
        data = {"task": task, "k": k}
        result = await self._request("POST", "/api/retrieve/few-shot-examples", json=data)
        return [FewShotExample(**ex) for ex in result["examples"]]

    async def get_task_patterns(
        self,
        task: str | None = None,
        code_block_id: str | None = None,
        min_thumbs_up: int = 0,
        top_k: int = 20,
    ) -> list[TaskPattern]:
        """Retrieve proven task->code mappings"""
        data = {
            "task": task,
            "code_block_id": code_block_id,
            "min_thumbs_up": min_thumbs_up,
            "top_k": top_k,
        }
        result = await self._request("POST", "/api/retrieve/task-patterns", json=data)
        return [TaskPattern(**p) for p in result["patterns"]]

    async def get_code_files(
        self,
        task: str,
        top_k: int = 5,
        min_verdict_score: float = 0.3,
        prefer_complete: bool = True,
        cache_dir: str = ".raysurfer_code",
    ) -> GetCodeFilesResponse:
        """
        Get code files for a task, ready to download to sandbox.

        Returns code blocks with full source code, optimized for:
        - High verdict scores (proven to work)
        - More complete implementations (prefer longer source)
        - Task relevance (semantic similarity)

        Args:
            task: Task description for semantic search
            top_k: Maximum number of files to return
            min_verdict_score: Minimum quality score (0-1)
            prefer_complete: Whether to prefer longer/more complete implementations
            cache_dir: Directory path where files will be written (default: .raysurfer_code).
                      Used to generate full paths in add_to_llm_prompt.
        """
        data = {
            "task": task,
            "top_k": top_k,
            "min_verdict_score": min_verdict_score,
            "prefer_complete": prefer_complete,
        }
        result = await self._request("POST", "/api/retrieve/code-files", json=data)
        files = [CodeFile(**f) for f in result["files"]]

        # Generate the add_to_llm_prompt string
        add_to_llm_prompt = self._format_llm_prompt(files, cache_dir)

        return GetCodeFilesResponse(
            files=files,
            task=result["task"],
            total_found=result["total_found"],
            add_to_llm_prompt=add_to_llm_prompt,
        )

    def _format_llm_prompt(self, files: list[CodeFile], cache_dir: str | None = None) -> str:
        """Format a prompt string listing all retrieved code files."""
        if not files:
            return ""

        lines = [
            "\n\n## IMPORTANT: Pre-validated Code Files Available\n",
            "The following validated code has been retrieved from the cache. "
            "Use these files directly instead of regenerating code.\n",
        ]

        for f in files:
            if cache_dir:
                import os
                full_path = os.path.join(cache_dir, f.filename)
                lines.append(f"\n### `{f.filename}` -> `{full_path}`")
            else:
                lines.append(f"\n### `{f.filename}`")
            lines.append(f"- **Description**: {f.description}")
            lines.append(f"- **Language**: {f.language}")
            lines.append(f"- **Entrypoint**: `{f.entrypoint}`")
            lines.append(f"- **Confidence**: {f.verdict_score:.0%}")
            if f.dependencies:
                lines.append(f"- **Dependencies**: {', '.join(f.dependencies)}")

        lines.append("\n\n**Instructions**:")
        lines.append("1. Read the cached file(s) before writing new code")
        lines.append("2. Use the cached code as your starting point")
        lines.append("3. Only modify if the task requires specific changes")
        lines.append("4. Do not regenerate code that already exists\n")

        return "\n".join(lines)

    async def vote_code_snip(
        self,
        task: str,
        code_block_id: str,
        code_block_name: str,
        code_block_description: str,
        succeeded: bool,
    ) -> dict[str, Any]:
        """
        Vote on whether a cached code snippet was useful.

        This triggers background voting to assess whether the cached code
        actually helped complete the task successfully.
        """
        data = {
            "task": task,
            "code_block_id": code_block_id,
            "code_block_name": code_block_name,
            "code_block_description": code_block_description,
            "succeeded": succeeded,
        }
        return await self._request("POST", "/api/store/cache-usage", json=data)

    # =========================================================================
    # Auto Review API
    # =========================================================================

    async def auto_review(
        self,
        execution_id: str,
        triggering_task: str,
        execution_state: ExecutionState,
        input_data: dict[str, Any],
        output_data: Any,
        code_block_name: str,
        code_block_description: str,
        error_message: str | None = None,
    ) -> AutoReviewResponse:
        """
        Get an auto-generated review using Claude Opus 4.5.
        Useful for programmatically reviewing execution results.
        """
        data = {
            "execution_id": execution_id,
            "triggering_task": triggering_task,
            "execution_state": execution_state.value,
            "input_data": input_data,
            "output_data": output_data,
            "code_block_name": code_block_name,
            "code_block_description": code_block_description,
            "error_message": error_message,
        }
        result = await self._request("POST", "/api/store/auto-review", json=data)
        return AutoReviewResponse(
            success=result["success"],
            execution_id=result["execution_id"],
            review=AgentReview(**result["review"]),
            message=result["message"],
        )

    async def get_executions(
        self,
        code_block_id: str | None = None,
        task: str | None = None,
        verdict: AgentVerdict | None = None,
        limit: int = 20,
    ) -> RetrieveExecutionsResponse:
        """Retrieve execution records by code block ID, task, or verdict."""
        data = {
            "code_block_id": code_block_id,
            "task": task,
            "verdict": verdict.value if verdict else None,
            "limit": limit,
        }
        result = await self._request("POST", "/api/retrieve/executions", json=data)
        executions = [ExecutionRecord(**ex) for ex in result["executions"]]
        return RetrieveExecutionsResponse(
            executions=executions,
            total_found=result["total_found"],
        )


class RaySurfer:
    """Sync client for RaySurfer API"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        organization_id: str | None = None,
        workspace_id: str | None = None,
        snips_desired: SnipsDesired | str | None = None,
        namespace: str | None = None,
    ):
        """
        Initialize the RaySurfer sync client.

        Args:
            api_key: RaySurfer API key (or set RAYSURFER_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            organization_id: Optional organization ID for dedicated namespace (team/enterprise)
            workspace_id: Optional workspace ID for client-specific namespace (enterprise only)
            snips_desired: Scope of private snippets - "company" (Team/Enterprise) or "client" (Enterprise only)
            namespace: Custom namespace for code storage/retrieval (overrides org-based namespacing)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.organization_id = organization_id
        self.workspace_id = workspace_id
        self.namespace = namespace
        # Convert string to SnipsDesired if needed
        if isinstance(snips_desired, str):
            self.snips_desired = SnipsDesired(snips_desired) if snips_desired else None
        else:
            self.snips_desired = snips_desired
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            # Add organization/workspace headers for namespace routing
            if self.organization_id:
                headers["X-Raysurfer-Org-Id"] = self.organization_id
            if self.workspace_id:
                headers["X-Raysurfer-Workspace-Id"] = self.workspace_id
            # Add snippet retrieval scope headers
            if self.snips_desired:
                headers["X-Raysurfer-Snips-Desired"] = self.snips_desired.value
            # Custom namespace override
            if self.namespace:
                headers["X-Raysurfer-Namespace"] = self.namespace
            # SDK version for tracking
            headers["X-Raysurfer-SDK-Version"] = f"python/{__version__}"
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "RaySurfer":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        import time as _time

        client = self._get_client()
        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = client.request(method, path, **kwargs)

                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else RETRY_BASE_DELAY * (2 ** attempt)
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Rate limited, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        _time.sleep(delay)
                        continue
                    raise RateLimitError(retry_after=delay)
                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_BASE_DELAY * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        _time.sleep(delay)
                        continue
                if response.status_code >= 400:
                    raise APIError(response.text, status_code=response.status_code)

                return response.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"Network error: {e}, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    _time.sleep(delay)
                    continue
                raise CacheUnavailableError(f"Failed to connect after {MAX_RETRIES} attempts: {e}") from e

        # Should not reach here, but just in case
        raise CacheUnavailableError(f"Request failed after {MAX_RETRIES} attempts") from last_exception

    # =========================================================================
    # Store API
    # =========================================================================

    def store_code_block(
        self,
        name: str,
        source: str,
        entrypoint: str,
        language: str,
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        language_version: str | None = None,
        dependencies: list[str] | None = None,
        tags: list[str] | None = None,
        capabilities: list[str] | None = None,
        example_queries: list[str] | None = None,
    ) -> StoreCodeBlockResponse:
        """Store a new code block"""
        data = {
            "name": name,
            "description": description,
            "source": source,
            "entrypoint": entrypoint,
            "language": language,
            "input_schema": input_schema or {},
            "output_schema": output_schema or {},
            "language_version": language_version,
            "dependencies": dependencies or [],
            "tags": tags or [],
            "capabilities": capabilities or [],
            "example_queries": example_queries,
        }
        result = self._request("POST", "/api/store/code-block", json=data)
        return StoreCodeBlockResponse(**result)

    def store_execution(
        self,
        code_block_id: str,
        triggering_task: str,
        input_data: dict[str, Any],
        output_data: Any,
        execution_state: ExecutionState = ExecutionState.COMPLETED,
        duration_ms: int = 0,
        error_message: str | None = None,
        error_type: str | None = None,
        verdict: AgentVerdict | None = None,
        review: AgentReview | None = None,
    ) -> StoreExecutionResponse:
        """Store an execution record"""
        io = ExecutionIO(
            input_data=input_data,
            output_data=output_data,
            output_type=type(output_data).__name__,
        )
        data = {
            "code_block_id": code_block_id,
            "triggering_task": triggering_task,
            "io": io.model_dump(),
            "execution_state": execution_state.value,
            "duration_ms": duration_ms,
            "error_message": error_message,
            "error_type": error_type,
            "verdict": verdict.value if verdict else None,
            "review": review.model_dump() if review else None,
        }
        result = self._request("POST", "/api/store/execution", json=data)
        return StoreExecutionResponse(**result)

    def upload_new_code_snips(
        self,
        task: str,
        files_written: list[FileWritten],
        succeeded: bool,
        auto_vote: bool = True,
        execution_logs: str | None = None,
    ) -> SubmitExecutionResultResponse:
        """
        Upload new code snippets from an execution.

        This is the simplified API for agent integrations. Just send:
        - The task that was executed
        - Files that were written during execution
        - Whether the task succeeded
        - Whether to auto-vote on stored blocks (default: True)
        - Captured execution logs for vote context

        Backend handles: entrypoint detection, tag extraction, language detection,
        deduplication, quality checks, and storage.
        """
        data: dict[str, Any] = {
            "task": task,
            "files_written": [f.model_dump() for f in files_written],
            "succeeded": succeeded,
            "auto_vote": auto_vote,
        }
        if execution_logs is not None:
            data["execution_logs"] = execution_logs
        result = self._request("POST", "/api/store/execution-result", json=data)
        return SubmitExecutionResultResponse(**result)

    # =========================================================================
    # Retrieve API
    # =========================================================================

    def get_code_snips(
        self,
        task: str,
        top_k: int = 10,
        min_verdict_score: float = 0.0,
    ) -> RetrieveCodeBlockResponse:
        """
        Get cached code snippets for a task.

        Searches for code blocks by task description using semantic search.
        """
        data = {
            "task": task,
            "top_k": top_k,
            "min_verdict_score": min_verdict_score,
        }
        result = self._request("POST", "/api/retrieve/code-blocks", json=data)

        code_blocks = [
            CodeBlockMatch(
                code_block=CodeBlock(**cb["code_block"]),
                score=cb["score"],
                verdict_score=cb["verdict_score"],
                thumbs_up=cb["thumbs_up"],
                thumbs_down=cb["thumbs_down"],
                recent_executions=cb.get("recent_executions", []),
            )
            for cb in result["code_blocks"]
        ]
        return RetrieveCodeBlockResponse(
            code_blocks=code_blocks,
            total_found=result["total_found"],
        )

    def retrieve_best(
        self,
        task: str,
        top_k: int = 10,
        min_verdict_score: float = 0.0,
    ) -> RetrieveBestResponse:
        """Get the single best code block for a task using verdict-aware scoring"""
        data = {
            "task": task,
            "top_k": top_k,
            "min_verdict_score": min_verdict_score,
        }
        result = self._request("POST", "/api/retrieve/best-for-task", json=data)

        best_match = None
        if result.get("best_match"):
            bm = result["best_match"]
            best_match = BestMatch(
                code_block=CodeBlock(**bm["code_block"]),
                combined_score=bm["combined_score"],
                vector_score=bm["vector_score"],
                verdict_score=bm["verdict_score"],
                error_resilience=bm["error_resilience"],
                thumbs_up=bm["thumbs_up"],
                thumbs_down=bm["thumbs_down"],
            )

        alternatives = [AlternativeCandidate(**alt) for alt in result.get("alternative_candidates", [])]

        return RetrieveBestResponse(
            best_match=best_match,
            alternative_candidates=alternatives,
            retrieval_confidence=result["retrieval_confidence"],
        )

    def get_few_shot_examples(
        self,
        task: str,
        k: int = 3,
    ) -> list[FewShotExample]:
        """Retrieve few-shot examples for code generation"""
        data = {"task": task, "k": k}
        result = self._request("POST", "/api/retrieve/few-shot-examples", json=data)
        return [FewShotExample(**ex) for ex in result["examples"]]

    def get_task_patterns(
        self,
        task: str | None = None,
        code_block_id: str | None = None,
        min_thumbs_up: int = 0,
        top_k: int = 20,
    ) -> list[TaskPattern]:
        """Retrieve proven task->code mappings"""
        data = {
            "task": task,
            "code_block_id": code_block_id,
            "min_thumbs_up": min_thumbs_up,
            "top_k": top_k,
        }
        result = self._request("POST", "/api/retrieve/task-patterns", json=data)
        return [TaskPattern(**p) for p in result["patterns"]]

    def get_code_files(
        self,
        task: str,
        top_k: int = 5,
        min_verdict_score: float = 0.3,
        prefer_complete: bool = True,
        cache_dir: str = ".raysurfer_code",
    ) -> GetCodeFilesResponse:
        """
        Get code files for a task, ready to download to sandbox.

        Returns code blocks with full source code, optimized for:
        - High verdict scores (proven to work)
        - More complete implementations (prefer longer source)
        - Task relevance (semantic similarity)

        Args:
            task: Task description for semantic search
            top_k: Maximum number of files to return
            min_verdict_score: Minimum quality score (0-1)
            prefer_complete: Whether to prefer longer/more complete implementations
            cache_dir: Directory path where files will be written (default: .raysurfer_code).
                      Used to generate full paths in add_to_llm_prompt.
        """
        data = {
            "task": task,
            "top_k": top_k,
            "min_verdict_score": min_verdict_score,
            "prefer_complete": prefer_complete,
        }
        result = self._request("POST", "/api/retrieve/code-files", json=data)
        files = [CodeFile(**f) for f in result["files"]]

        # Generate the add_to_llm_prompt string
        add_to_llm_prompt = self._format_llm_prompt(files, cache_dir)

        return GetCodeFilesResponse(
            files=files,
            task=result["task"],
            total_found=result["total_found"],
            add_to_llm_prompt=add_to_llm_prompt,
        )

    def _format_llm_prompt(self, files: list[CodeFile], cache_dir: str | None = None) -> str:
        """Format a prompt string listing all retrieved code files."""
        if not files:
            return ""

        lines = [
            "\n\n## IMPORTANT: Pre-validated Code Files Available\n",
            "The following validated code has been retrieved from the cache. "
            "Use these files directly instead of regenerating code.\n",
        ]

        for f in files:
            if cache_dir:
                import os
                full_path = os.path.join(cache_dir, f.filename)
                lines.append(f"\n### `{f.filename}` -> `{full_path}`")
            else:
                lines.append(f"\n### `{f.filename}`")
            lines.append(f"- **Description**: {f.description}")
            lines.append(f"- **Language**: {f.language}")
            lines.append(f"- **Entrypoint**: `{f.entrypoint}`")
            lines.append(f"- **Confidence**: {f.verdict_score:.0%}")
            if f.dependencies:
                lines.append(f"- **Dependencies**: {', '.join(f.dependencies)}")

        lines.append("\n\n**Instructions**:")
        lines.append("1. Read the cached file(s) before writing new code")
        lines.append("2. Use the cached code as your starting point")
        lines.append("3. Only modify if the task requires specific changes")
        lines.append("4. Do not regenerate code that already exists\n")

        return "\n".join(lines)

    def vote_code_snip(
        self,
        task: str,
        code_block_id: str,
        code_block_name: str,
        code_block_description: str,
        succeeded: bool,
    ) -> dict[str, Any]:
        """
        Vote on whether a cached code snippet was useful.

        This triggers background voting to assess whether the cached code
        actually helped complete the task successfully.
        """
        data = {
            "task": task,
            "code_block_id": code_block_id,
            "code_block_name": code_block_name,
            "code_block_description": code_block_description,
            "succeeded": succeeded,
        }
        return self._request("POST", "/api/store/cache-usage", json=data)

    # =========================================================================
    # Auto Review API
    # =========================================================================

    def auto_review(
        self,
        execution_id: str,
        triggering_task: str,
        execution_state: ExecutionState,
        input_data: dict[str, Any],
        output_data: Any,
        code_block_name: str,
        code_block_description: str,
        error_message: str | None = None,
    ) -> AutoReviewResponse:
        """
        Get an auto-generated review using Claude Opus 4.5.
        Useful for programmatically reviewing execution results.
        """
        data = {
            "execution_id": execution_id,
            "triggering_task": triggering_task,
            "execution_state": execution_state.value,
            "input_data": input_data,
            "output_data": output_data,
            "code_block_name": code_block_name,
            "code_block_description": code_block_description,
            "error_message": error_message,
        }
        result = self._request("POST", "/api/store/auto-review", json=data)
        return AutoReviewResponse(
            success=result["success"],
            execution_id=result["execution_id"],
            review=AgentReview(**result["review"]),
            message=result["message"],
        )

    def get_executions(
        self,
        code_block_id: str | None = None,
        task: str | None = None,
        verdict: AgentVerdict | None = None,
        limit: int = 20,
    ) -> RetrieveExecutionsResponse:
        """Retrieve execution records by code block ID, task, or verdict."""
        data = {
            "code_block_id": code_block_id,
            "task": task,
            "verdict": verdict.value if verdict else None,
            "limit": limit,
        }
        result = self._request("POST", "/api/retrieve/executions", json=data)
        executions = [ExecutionRecord(**ex) for ex in result["executions"]]
        return RetrieveExecutionsResponse(
            executions=executions,
            total_found=result["total_found"],
        )
