"""
Agent Orchestrator for AiCippy.

Coordinates multiple specialized agents to complete complex tasks
with parallel execution, dependency resolution, and result merging.

This module provides:
- Multi-agent task orchestration
- Parallel execution with concurrency limits
- Task decomposition and dependency resolution
- Bedrock model invocation with circuit breaker pattern
- Progress tracking and result aggregation
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Final

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn

from aicippy.agents.models import (
    AGENT_SYSTEM_PROMPTS,
    AgentConfig,
    AgentResponse,
    AgentRun,
    AgentStatus,
    AgentTask,
    AgentType,
    TokenUsage,
)
from aicippy.config import get_settings
from aicippy.exceptions import (
    AgentExecutionError,
    AgentSpawnError,
    AgentTimeoutError,
    ContextExceededError,
    ErrorContext,
    ModelInvocationError,
    ModelRateLimitedError,
)
from aicippy.types import JsonDict, SessionId
from aicippy.utils.correlation import CorrelationContext, get_correlation_id
from aicippy.utils.logging import get_logger
from aicippy.utils.retry import CircuitBreaker, CircuitBreakerOpenError, async_retry

if TYPE_CHECKING:
    from types import TracebackType

logger = get_logger(__name__)

# ============================================================================
# Constants
# ============================================================================

DEFAULT_MAX_AGENTS: Final[int] = 3
MAX_TASK_DECOMPOSITION_DEPTH: Final[int] = 3
BEDROCK_READ_TIMEOUT: Final[int] = 120
BEDROCK_CONNECT_TIMEOUT: Final[int] = 10
BEDROCK_MAX_RETRIES: Final[int] = 3


# ============================================================================
# Data Classes
# ============================================================================


@dataclass(slots=True)
class AgentInstance:
    """
    Running agent instance with state tracking.

    Attributes:
        id: Unique agent identifier.
        agent_type: Type of specialized agent.
        config: Agent configuration.
        status: Current execution status.
        current_task: Currently executing task.
        total_tokens: Cumulative token usage.
        started_at: Instance creation timestamp.
        last_activity: Last activity timestamp.
    """

    id: str
    agent_type: AgentType
    config: AgentConfig
    status: AgentStatus = AgentStatus.IDLE
    current_task: AgentTask | None = None
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)

    def add_tokens(self, usage: TokenUsage) -> None:
        """Add token usage to cumulative total."""
        self.total_tokens = self.total_tokens + usage
        self.update_activity()


# ============================================================================
# Orchestrator
# ============================================================================


class AgentOrchestrator:
    """
    Multi-agent orchestrator for complex task execution.

    Coordinates specialized agents, manages parallel execution,
    handles dependencies, and merges results with comprehensive
    error handling and observability.

    Features:
    - Parallel agent execution up to configurable limit
    - Task decomposition with dependency resolution
    - Circuit breaker pattern for Bedrock API
    - Structured logging with correlation IDs
    - Graceful error recovery

    Example:
        >>> orchestrator = AgentOrchestrator(model_id="opus", max_agents=5)
        >>> response = await orchestrator.chat("Explain AWS Lambda")
        >>> print(response.content)

    Example with progress:
        >>> from rich.console import Console
        >>> console = Console()
        >>> response = await orchestrator.run_task_with_progress(
        ...     "Deploy a serverless API",
        ...     console,
        ... )
    """

    __slots__ = (
        "_settings",
        "_model_id",
        "_max_agents",
        "_session_id",
        "_agents",
        "_task_queue",
        "_completed_tasks",
        "_lock",
        "_circuit_breaker",
        "_bedrock_client",
    )

    def __init__(
        self,
        model_id: str | None = None,
        max_agents: int = DEFAULT_MAX_AGENTS,
        session_id: str | None = None,
    ) -> None:
        """
        Initialize the orchestrator.

        Args:
            model_id: Bedrock model ID to use. Defaults to configured default.
            max_agents: Maximum number of parallel agents (capped by settings).
            session_id: Session identifier for tracking. Auto-generated if not provided.

        Raises:
            ValueError: If max_agents is less than 1.
        """
        if max_agents < 1:
            raise ValueError("max_agents must be at least 1")

        self._settings = get_settings()
        self._model_id = model_id or self._settings.get_model_id()
        self._max_agents = min(max_agents, self._settings.max_parallel_agents)
        self._session_id = SessionId(session_id or str(uuid.uuid4()))

        # Agent management
        self._agents: dict[str, AgentInstance] = {}
        self._task_queue: asyncio.Queue[AgentTask] = asyncio.Queue()
        self._completed_tasks: dict[str, AgentResponse] = {}
        self._lock = asyncio.Lock()

        # Circuit breaker for Bedrock API
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
            half_open_requests=3,
        )

        # Bedrock client (lazy initialization)
        self._bedrock_client: Any = None

        logger.info(
            "orchestrator_initialized",
            model_id=self._model_id,
            max_agents=self._max_agents,
            session_id=self._session_id,
        )

    @property
    def session_id(self) -> SessionId:
        """Get the session identifier."""
        return self._session_id

    @property
    def model_id(self) -> str:
        """Get the current model ID."""
        return self._model_id

    @property
    def max_agents(self) -> int:
        """Get the maximum number of parallel agents."""
        return self._max_agents

    @property
    def active_agent_count(self) -> int:
        """Get the number of currently active agents."""
        return len(self._agents)

    def _get_bedrock_client(self) -> Any:
        """
        Get or create Bedrock runtime client with optimized configuration.

        Returns:
            Configured boto3 Bedrock runtime client.
        """
        if self._bedrock_client is None:
            config = Config(
                retries={
                    "max_attempts": BEDROCK_MAX_RETRIES,
                    "mode": "adaptive",
                },
                read_timeout=BEDROCK_READ_TIMEOUT,
                connect_timeout=BEDROCK_CONNECT_TIMEOUT,
            )

            session_kwargs: dict[str, Any] = {
                "region_name": self._settings.aws_region,
            }
            if self._settings.aws_profile:
                session_kwargs["profile_name"] = self._settings.aws_profile

            session = boto3.Session(**session_kwargs)
            self._bedrock_client = session.client(
                "bedrock-runtime",
                config=config,
            )

        return self._bedrock_client

    async def chat(self, message: str) -> AgentResponse:
        """
        Process a chat message and return response.

        Args:
            message: User message to process.

        Returns:
            AgentResponse with the assistant's reply.

        Note:
            This method handles errors gracefully and returns an error
            response rather than raising exceptions for operational failures.
        """
        if not message or not message.strip():
            return AgentResponse.error_response(
                "Empty message provided",
                AgentType.ORCHESTRATOR,
            )

        correlation_id = get_correlation_id()
        logger.info(
            "chat_started",
            message_length=len(message),
            model=self._model_id,
            correlation_id=correlation_id,
        )

        try:
            response = await self._invoke_model(
                message=message,
                system_prompt=AGENT_SYSTEM_PROMPTS[AgentType.ORCHESTRATOR],
            )

            logger.info(
                "chat_completed",
                input_tokens=response.usage.input_tokens if response.usage else 0,
                output_tokens=response.usage.output_tokens if response.usage else 0,
                correlation_id=correlation_id,
            )

            return response

        except CircuitBreakerOpenError as e:
            logger.warning(
                "chat_circuit_breaker_open",
                error=str(e),
                correlation_id=correlation_id,
            )
            return AgentResponse.error_response(
                "Service temporarily unavailable. Please retry shortly.",
                AgentType.ORCHESTRATOR,
            )

        except (ModelInvocationError, ModelRateLimitedError) as e:
            logger.warning(
                "chat_model_error",
                error=str(e),
                error_code=e.code.name,
                correlation_id=correlation_id,
            )
            return AgentResponse.error_response(str(e), AgentType.ORCHESTRATOR)

        except Exception as e:
            logger.exception(
                "chat_failed",
                error=str(e),
                correlation_id=correlation_id,
            )
            return AgentResponse.error_response(
                f"Unexpected error: {e}",
                AgentType.ORCHESTRATOR,
            )

    async def run_task_with_progress(
        self,
        task: str,
        console: Console,
    ) -> AgentResponse:
        """
        Execute a task with progress display.

        Args:
            task: Task description to execute.
            console: Rich console for progress display.

        Returns:
            AgentResponse with combined results from all agents.

        Note:
            Complex tasks are automatically decomposed into subtasks
            and executed in parallel where dependencies allow.
        """
        if not task or not task.strip():
            return AgentResponse.error_response(
                "Empty task provided",
                AgentType.ORCHESTRATOR,
            )

        correlation_id = get_correlation_id()
        logger.info(
            "task_started",
            task=task[:100],
            max_agents=self._max_agents,
            correlation_id=correlation_id,
        )

        try:
            # Analyze task and create subtasks
            subtasks = await self._analyze_and_decompose(task)

            if not subtasks:
                # Simple task - process directly
                logger.debug(
                    "task_simple_execution",
                    correlation_id=correlation_id,
                )
                return await self.chat(task)

            logger.info(
                "task_decomposed",
                subtask_count=len(subtasks),
                correlation_id=correlation_id,
            )

            # Create progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
                transient=True,
            ) as progress:
                # Add progress tasks for each subtask
                progress_tasks: dict[str, TaskID] = {}
                for subtask in subtasks:
                    task_id = progress.add_task(
                        f"[cyan]{subtask.agent_type.value}[/cyan]: {subtask.description[:50]}",
                        total=100,
                    )
                    progress_tasks[subtask.id] = task_id

                # Execute subtasks with parallelism
                results = await self._execute_subtasks(
                    subtasks,
                    lambda task_id, pct: progress.update(
                        progress_tasks.get(task_id, TaskID(0)),
                        completed=pct,
                    ),
                )

            # Merge results
            merged = self._merge_results(results)

            logger.info(
                "task_completed",
                subtask_count=len(subtasks),
                successful=sum(1 for r in results.values() if not r.is_error),
                failed=sum(1 for r in results.values() if r.is_error),
                correlation_id=correlation_id,
            )

            return merged

        except Exception as e:
            logger.exception(
                "task_failed",
                error=str(e),
                correlation_id=correlation_id,
            )
            return AgentResponse.error_response(
                f"Task execution failed: {e}",
                AgentType.ORCHESTRATOR,
            )

    async def _analyze_and_decompose(self, task: str) -> list[AgentTask]:
        """
        Analyze a task and decompose into subtasks for parallel execution.

        Args:
            task: Task description to analyze.

        Returns:
            List of subtasks. Empty list if task is simple.
        """
        analysis_prompt = f"""Analyze this task and determine if it should be decomposed into subtasks
for parallel agent execution. If the task is simple, return an empty list.
If complex, identify the subtasks and which specialized agent should handle each.

Available agent types:
- infra-core: AWS CDK, IAM, VPC, security
- bedrock-ai: Bedrock agents, knowledge bases
- api-gateway: WebSocket, Lambda authorizers
- cognito-auth: User pools, authentication
- cli-core: Python CLI, Typer, Rich
- mcp-bridges: Tool connectors
- knowledge-ingest: Feed crawling, indexing
- observability: CloudWatch, logging
- email-notify: SES, notifications
- cicd-deploy: GitHub Actions, deployment

Task: {task}

Respond with a JSON array of subtasks, each with:
- description: Brief task description
- agent_type: One of the agent types above
- priority: 0-10 (higher = more important)
- dependencies: Array of other subtask indices that must complete first

Example response for a complex task:
[
  {{"description": "Create VPC and networking", "agent_type": "infra-core", "priority": 10, "dependencies": []}},
  {{"description": "Setup DynamoDB tables", "agent_type": "infra-core", "priority": 8, "dependencies": [0]}}
]

For a simple task, respond with: []
"""

        try:
            response = await self._invoke_model(
                message=analysis_prompt,
                system_prompt="You are a task analysis assistant. Respond only with valid JSON.",
            )

            # Parse JSON response
            content = response.content.strip()

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            content = content.strip()

            try:
                subtask_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(
                    "task_decomposition_json_error",
                    error=str(e),
                    content_preview=content[:200],
                )
                return []

            if not subtask_data or not isinstance(subtask_data, list):
                return []

            # Convert to AgentTask objects with validation
            subtasks: list[AgentTask] = []
            for i, data in enumerate(subtask_data):
                if not isinstance(data, dict):
                    continue

                description = data.get("description", "")
                agent_type_str = data.get("agent_type", "")

                if not description or not agent_type_str:
                    continue

                try:
                    agent_type = AgentType.from_string(agent_type_str)
                except (ValueError, KeyError):
                    logger.warning(
                        "task_decomposition_invalid_agent_type",
                        agent_type=agent_type_str,
                    )
                    continue

                task_id = str(uuid.uuid4())
                dependencies = []

                # Resolve dependency indices to task IDs
                for dep_idx in data.get("dependencies", []):
                    if isinstance(dep_idx, int) and 0 <= dep_idx < len(subtasks):
                        dependencies.append(subtasks[dep_idx].id)

                subtasks.append(
                    AgentTask(
                        id=task_id,
                        description=description,
                        agent_type=agent_type,
                        priority=min(10, max(0, int(data.get("priority", 5)))),
                        dependencies=dependencies,
                    )
                )

            return subtasks

        except Exception as e:
            logger.warning(
                "task_decomposition_failed",
                error=str(e),
            )
            return []

    async def _execute_subtasks(
        self,
        subtasks: Sequence[AgentTask],
        progress_callback: Callable[[str, int], None],
    ) -> dict[str, AgentResponse]:
        """
        Execute subtasks with parallel execution and dependency handling.

        Args:
            subtasks: List of subtasks to execute.
            progress_callback: Callback for progress updates (task_id, percentage).

        Returns:
            Dictionary mapping task IDs to responses.
        """
        results: dict[str, AgentResponse] = {}
        pending: dict[str, AgentTask] = {task.id: task for task in subtasks}
        running: dict[str, asyncio.Task[AgentResponse]] = {}

        while pending or running:
            # Find tasks that can be started (all dependencies completed)
            ready = [
                task
                for task in pending.values()
                if all(dep in results for dep in task.dependencies)
            ]

            # Sort by priority (higher first) and start tasks up to max_agents
            ready.sort(key=lambda t: t.priority, reverse=True)

            for task in ready:
                if len(running) >= self._max_agents:
                    break

                # Start task execution
                del pending[task.id]
                progress_callback(task.id, 10)

                async_task = asyncio.create_task(
                    self._execute_single_task(task, results, progress_callback),
                    name=f"agent-{task.agent_type.value}-{task.id[:8]}",
                )
                running[task.id] = async_task

            if running:
                # Wait for at least one task to complete
                done, _ = await asyncio.wait(
                    running.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Process completed tasks
                for completed_task in done:
                    # Find which task completed
                    completed_id: str | None = None
                    for tid, t in running.items():
                        if t is completed_task:
                            completed_id = tid
                            break

                    if completed_id:
                        try:
                            results[completed_id] = completed_task.result()
                        except Exception as e:
                            logger.warning(
                                "subtask_exception",
                                task_id=completed_id,
                                error=str(e),
                            )
                            results[completed_id] = AgentResponse.error_response(
                                str(e),
                                AgentType.ORCHESTRATOR,
                            )

                        del running[completed_id]
                        progress_callback(completed_id, 100)

            # Small delay to prevent tight loop
            await asyncio.sleep(0.05)

        return results

    async def _execute_single_task(
        self,
        task: AgentTask,
        completed_results: dict[str, AgentResponse],
        progress_callback: Callable[[str, int], None],
    ) -> AgentResponse:
        """
        Execute a single subtask with context from dependencies.

        Args:
            task: Task to execute.
            completed_results: Results from completed dependent tasks.
            progress_callback: Progress update callback.

        Returns:
            AgentResponse from task execution.
        """
        correlation_id = get_correlation_id()
        progress_callback(task.id, 20)

        # Build context from dependencies
        context_parts: list[str] = []
        for dep_id in task.dependencies:
            if dep_id in completed_results:
                dep_result = completed_results[dep_id]
                if not dep_result.is_error:
                    # Truncate long results to prevent context overflow
                    content_preview = dep_result.content[:1000]
                    if len(dep_result.content) > 1000:
                        content_preview += "... [truncated]"
                    context_parts.append(f"Previous result: {content_preview}")

        context = "\n\n".join(context_parts) if context_parts else ""
        progress_callback(task.id, 40)

        # Get system prompt for this agent type
        system_prompt = AGENT_SYSTEM_PROMPTS.get(
            task.agent_type,
            AGENT_SYSTEM_PROMPTS[AgentType.ORCHESTRATOR],
        )

        # Build message with context
        message_parts = [f"Execute this task:\n{task.description}"]
        if context:
            message_parts.append(f"\nContext from previous tasks:\n{context}")
        message_parts.append(
            "\nProvide a detailed response with your analysis and any code, "
            "configurations, or recommendations needed to complete this task."
        )

        message = "\n".join(message_parts)
        progress_callback(task.id, 60)

        # Execute with the specialized agent
        try:
            response = await self._invoke_model(
                message=message,
                system_prompt=system_prompt,
            )

            response.agent_type = task.agent_type
            response.task_id = task.id

            progress_callback(task.id, 90)

            logger.debug(
                "subtask_completed",
                task_id=task.id,
                agent_type=task.agent_type.value,
                correlation_id=correlation_id,
            )

            return response

        except Exception as e:
            logger.warning(
                "subtask_failed",
                task_id=task.id,
                agent_type=task.agent_type.value,
                error=str(e),
                correlation_id=correlation_id,
            )
            return AgentResponse.error_response(str(e), task.agent_type)

    def _merge_results(
        self,
        results: dict[str, AgentResponse],
    ) -> AgentResponse:
        """
        Merge results from multiple agents into a single response.

        Args:
            results: Dictionary of task results.

        Returns:
            Merged AgentResponse with combined content and usage.
        """
        if not results:
            return AgentResponse(content="No results to merge.")

        # Combine content by agent type
        content_parts: list[str] = []
        total_usage = TokenUsage()
        all_artifacts: list[dict[str, Any]] = []
        error_count = 0

        for task_id, response in results.items():
            agent_label = response.agent_type.value if response.agent_type else "unknown"

            if response.is_error:
                error_count += 1
                content_parts.append(f"## {agent_label} (Error)\n{response.error}")
            else:
                content_parts.append(f"## {agent_label}\n{response.content}")

            if response.usage:
                total_usage = total_usage + response.usage

            all_artifacts.extend(response.artifacts)

        merged_content = "\n\n---\n\n".join(content_parts)

        # Add summary header if there were errors
        if error_count > 0:
            header = f"**Note:** {error_count} of {len(results)} tasks encountered errors.\n\n"
            merged_content = header + merged_content

        return AgentResponse(
            content=merged_content,
            agent_type=AgentType.ORCHESTRATOR,
            usage=total_usage,
            artifacts=all_artifacts,
        )

    @async_retry(max_attempts=3, min_wait=1.0, max_wait=10.0)
    async def _invoke_model(
        self,
        message: str,
        system_prompt: str,
    ) -> AgentResponse:
        """
        Invoke Bedrock model with retry logic and circuit breaker.

        Args:
            message: User message to send.
            system_prompt: System prompt for the model.

        Returns:
            AgentResponse with model output.

        Raises:
            ModelInvocationError: If model invocation fails.
            ModelRateLimitedError: If rate limited.
            CircuitBreakerOpenError: If circuit breaker is open.
        """
        correlation_id = get_correlation_id()
        client = self._get_bedrock_client()

        # Build request body based on model
        body: dict[str, Any]
        if "claude" in self._model_id.lower():
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": message}],
            }
        elif "llama" in self._model_id.lower():
            body = {
                "prompt": f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{message}<|end|>\n<|assistant|>",
                "max_gen_len": 4096,
                "temperature": 0.7,
            }
        else:
            # Default format for other models
            body = {
                "prompt": f"{system_prompt}\n\nHuman: {message}\n\nAssistant:",
                "max_tokens": 4096,
            }

        # Async invoke function for circuit breaker
        async def invoke() -> dict[str, Any]:
            loop = asyncio.get_running_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: client.invoke_model(
                        modelId=self._model_id,
                        body=json.dumps(body),
                        contentType="application/json",
                        accept="application/json",
                    ),
                )
                return json.loads(response["body"].read())
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                error_message = e.response.get("Error", {}).get("Message", str(e))

                if error_code == "ThrottlingException":
                    raise ModelRateLimitedError(
                        model_id=self._model_id,
                        context=ErrorContext(
                            correlation_id=correlation_id,
                            operation="model_invocation",
                        ),
                    ) from e
                elif error_code == "ValidationException" and "context" in error_message.lower():
                    raise ContextExceededError(
                        model_id=self._model_id,
                        tokens_used=0,  # Unknown
                        max_tokens=200000,
                        context=ErrorContext(
                            correlation_id=correlation_id,
                            operation="model_invocation",
                        ),
                    ) from e
                else:
                    raise ModelInvocationError(
                        model_id=self._model_id,
                        message=error_message,
                        context=ErrorContext(
                            correlation_id=correlation_id,
                            operation="model_invocation",
                            details={"error_code": error_code},
                        ),
                    ) from e
            except BotoCoreError as e:
                raise ModelInvocationError(
                    model_id=self._model_id,
                    message=str(e),
                    context=ErrorContext(
                        correlation_id=correlation_id,
                        operation="model_invocation",
                    ),
                ) from e

        # Execute through circuit breaker
        try:
            result = await self._circuit_breaker.call(invoke)
        except CircuitBreakerOpenError:
            logger.warning(
                "circuit_breaker_open",
                model=self._model_id,
                correlation_id=correlation_id,
            )
            raise
        except (ModelInvocationError, ModelRateLimitedError, ContextExceededError):
            raise
        except Exception as e:
            logger.error(
                "model_invocation_failed",
                error=str(e),
                model=self._model_id,
                correlation_id=correlation_id,
            )
            raise ModelInvocationError(
                model_id=self._model_id,
                message=str(e),
                context=ErrorContext(
                    correlation_id=correlation_id,
                    operation="model_invocation",
                ),
            ) from e

        # Parse response based on model
        if "claude" in self._model_id.lower():
            content = result.get("content", [{}])[0].get("text", "")
            usage = TokenUsage(
                input_tokens=result.get("usage", {}).get("input_tokens", 0),
                output_tokens=result.get("usage", {}).get("output_tokens", 0),
            )
        elif "llama" in self._model_id.lower():
            content = result.get("generation", "")
            usage = TokenUsage(
                input_tokens=result.get("prompt_token_count", 0),
                output_tokens=result.get("generation_token_count", 0),
            )
        else:
            content = result.get("completion", result.get("generated_text", ""))
            usage = TokenUsage()

        return AgentResponse(
            content=content,
            usage=usage,
        )

    async def close(self) -> None:
        """Clean up orchestrator resources."""
        self._agents.clear()
        self._completed_tasks.clear()

        # Clear task queue
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.debug("orchestrator_closed", session_id=self._session_id)

    async def __aenter__(self) -> "AgentOrchestrator":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit with cleanup."""
        await self.close()
