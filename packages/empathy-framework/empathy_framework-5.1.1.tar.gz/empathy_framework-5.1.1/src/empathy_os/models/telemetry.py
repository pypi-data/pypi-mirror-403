"""Structured Telemetry for Multi-Model Workflows

Provides normalized schemas for tracking LLM calls and workflow runs:
- LLMCallRecord: Per-call metrics (model, tokens, cost, latency)
- WorkflowRunRecord: Per-workflow metrics (stages, total cost, duration)
- TelemetryBackend: Abstract interface for telemetry storage
- TelemetryStore: JSONL file-based backend (default)
- Analytics helpers for cost analysis and optimization

Tier 1 Automation Monitoring:
- TaskRoutingRecord: Task routing decisions and outcomes
- TestExecutionRecord: Test execution results and coverage
- CoverageRecord: Test coverage metrics and trends
- AgentAssignmentRecord: Agent assignments for simple tasks

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import heapq
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class LLMCallRecord:
    """Record of a single LLM API call.

    Captures all relevant metrics for cost tracking, performance analysis,
    and debugging.
    """

    # Identification
    call_id: str
    timestamp: str  # ISO format

    # Context
    workflow_name: str | None = None
    step_name: str | None = None
    user_id: str | None = None
    session_id: str | None = None

    # Task routing
    task_type: str = "unknown"
    provider: str = "anthropic"
    tier: str = "capable"
    model_id: str = ""

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0

    # Cost (in USD)
    estimated_cost: float = 0.0
    actual_cost: float | None = None

    # Performance
    latency_ms: int = 0

    # Fallback and resilience tracking
    fallback_used: bool = False
    fallback_chain: list[str] = field(default_factory=list)
    original_provider: str | None = None
    original_model: str | None = None
    retry_count: int = 0  # Number of retries before success
    circuit_breaker_state: str | None = None  # "closed", "open", "half-open"

    # Error tracking
    success: bool = True
    error_type: str | None = None
    error_message: str | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMCallRecord":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class WorkflowStageRecord:
    """Record of a single workflow stage execution."""

    stage_name: str
    tier: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    success: bool = True
    skipped: bool = False
    skip_reason: str | None = None
    error: str | None = None


@dataclass
class WorkflowRunRecord:
    """Record of a complete workflow execution.

    Aggregates stage-level metrics and provides workflow-level analytics.
    """

    # Identification
    run_id: str
    workflow_name: str
    started_at: str  # ISO format
    completed_at: str | None = None

    # Context
    user_id: str | None = None
    session_id: str | None = None

    # Stages
    stages: list[WorkflowStageRecord] = field(default_factory=list)

    # Aggregated metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    baseline_cost: float = 0.0  # If all stages used premium
    savings: float = 0.0
    savings_percent: float = 0.0

    # Performance
    total_duration_ms: int = 0

    # Status
    success: bool = True
    error: str | None = None

    # Provider usage
    providers_used: list[str] = field(default_factory=list)
    tiers_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["stages"] = [asdict(s) for s in self.stages]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowRunRecord":
        """Create from dictionary."""
        stages = [WorkflowStageRecord(**s) for s in data.pop("stages", [])]
        return cls(stages=stages, **data)


@dataclass
class TaskRoutingRecord:
    """Record of task routing decision for Tier 1 automation.

    Tracks which agent/workflow handles each task, routing strategy,
    and execution outcome for automation monitoring.
    """

    # Identification (required)
    routing_id: str
    timestamp: str  # ISO format

    # Task context (required)
    task_description: str
    task_type: str  # "code_review", "test_gen", "bug_fix", "refactor", etc.
    task_complexity: str  # "simple", "moderate", "complex"

    # Routing decision (required)
    assigned_agent: str  # "test_gen_workflow", "code_review_workflow", etc.
    assigned_tier: str  # "cheap", "capable", "premium"
    routing_strategy: str  # "rule_based", "ml_predicted", "manual_override"

    # Optional fields with defaults
    task_dependencies: list[str] = field(default_factory=list)  # Task IDs this depends on
    confidence_score: float = 1.0  # 0.0-1.0 for ML predictions

    # Execution tracking
    status: str = "pending"  # "pending", "running", "completed", "failed"
    started_at: str | None = None
    completed_at: str | None = None

    # Outcome
    success: bool = False
    quality_score: float | None = None  # 0.0-1.0 if applicable
    retry_count: int = 0
    error_type: str | None = None
    error_message: str | None = None

    # Cost tracking
    estimated_cost: float = 0.0
    actual_cost: float | None = None

    # Metadata
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskRoutingRecord":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TestExecutionRecord:
    """Record of test execution for Tier 1 QA automation.

    Tracks test execution results, coverage metrics, and failure details
    for quality assurance monitoring.
    """

    # Identification (required)
    execution_id: str
    timestamp: str  # ISO format

    # Test context (required)
    test_suite: str  # "unit", "integration", "e2e", "all"

    # Optional fields with defaults
    test_files: list[str] = field(default_factory=list)  # Specific test files executed
    triggered_by: str = "manual"  # "workflow", "manual", "ci", "pre_commit"

    # Execution details
    command: str = ""
    working_directory: str = ""
    duration_seconds: float = 0.0

    # Results
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0

    # Coverage (if available)
    coverage_percentage: float | None = None
    coverage_report_path: str | None = None

    # Failures
    failed_tests: list[dict[str, Any]] = field(
        default_factory=list
    )  # [{name, file, error, traceback}]

    # Status
    success: bool = False  # True if all tests passed
    exit_code: int = 0

    # Metadata
    workflow_id: str | None = None  # Link to workflow that triggered this
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestExecutionRecord":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CoverageRecord:
    """Record of test coverage metrics for Tier 1 QA monitoring.

    Tracks coverage percentage, trends, and critical gaps for
    continuous quality improvement.
    """

    # Identification (required)
    record_id: str
    timestamp: str  # ISO format

    # Coverage metrics (required)
    overall_percentage: float
    lines_total: int
    lines_covered: int

    # Optional fields with defaults
    branches_total: int = 0
    branches_covered: int = 0

    # File-level breakdown
    files_total: int = 0
    files_well_covered: int = 0  # >= 80%
    files_critical: int = 0  # < 50%
    untested_files: list[str] = field(default_factory=list)

    # Critical gaps
    critical_gaps: list[dict[str, Any]] = field(
        default_factory=list
    )  # [{file, coverage, priority}]

    # Trend data
    previous_percentage: float | None = None
    trend: str | None = None  # "improving", "declining", "stable"

    # Source
    coverage_format: str = "xml"  # "xml", "json", "lcov"
    coverage_file: str = ""

    # Metadata
    workflow_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoverageRecord":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AgentAssignmentRecord:
    """Record of agent assignment for simple tasks (Tier 1).

    Tracks task assignments to agents/workflows with clear specs
    and no complex dependencies for automation monitoring.
    """

    # Identification (required)
    assignment_id: str
    timestamp: str  # ISO format

    # Task details (required)
    task_id: str
    task_title: str
    task_description: str

    # Assignment (required)
    assigned_agent: str  # Agent/workflow name

    # Optional fields with defaults
    task_spec_clarity: float = 0.0  # 0.0-1.0, higher = clearer spec
    assignment_reason: str = ""  # Why this agent was chosen
    estimated_duration_hours: float = 0.0

    # Criteria checks
    has_clear_spec: bool = False
    has_dependencies: bool = False
    requires_human_review: bool = False
    automated_eligible: bool = False  # True for Tier 1

    # Execution tracking
    status: str = "assigned"  # "assigned", "in_progress", "completed", "blocked"
    started_at: str | None = None
    completed_at: str | None = None
    actual_duration_hours: float | None = None

    # Outcome
    success: bool = False
    quality_check_passed: bool = False
    human_review_required: bool = False

    # Metadata
    workflow_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentAssignmentRecord":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FileTestRecord:
    """Record of test execution for a specific source file.

    Tracks when tests for an individual file were last run, results,
    and coverage - enabling per-file test status tracking.

    This complements TestExecutionRecord (suite-level) by providing
    granular file-level test tracking for better test maintenance.
    """

    # Identification (required)
    file_path: str  # Source file path (relative to project root)
    timestamp: str  # ISO format - when tests were run

    # Test results (required)
    last_test_result: str  # "passed", "failed", "error", "skipped", "no_tests"
    test_count: int  # Number of tests for this file

    # Detailed results with defaults
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0

    # Timing
    duration_seconds: float = 0.0

    # Coverage for this file (if available)
    coverage_percent: float | None = None
    lines_total: int = 0
    lines_covered: int = 0

    # Test file info
    test_file_path: str | None = None  # Associated test file

    # Failure details (if any)
    failed_tests: list[dict[str, Any]] = field(default_factory=list)

    # Staleness tracking
    source_modified_at: str | None = None  # When source file was last modified
    tests_modified_at: str | None = None  # When test file was last modified
    is_stale: bool = False  # Tests haven't been run since source changed

    # Link to execution
    execution_id: str | None = None  # Link to TestExecutionRecord
    workflow_id: str | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileTestRecord":
        """Create from dictionary."""
        return cls(**data)

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.last_test_result == "passed" and self.failed == 0 and self.errors == 0


@runtime_checkable
class TelemetryBackend(Protocol):
    """Protocol for telemetry storage backends.

    Implementations can store telemetry data in different backends:
    - JSONL files (default, via TelemetryStore)
    - Database (PostgreSQL, SQLite, etc.)
    - Cloud services (DataDog, New Relic, etc.)
    - Custom backends

    Supports both core telemetry (LLM calls, workflows) and Tier 1
    automation monitoring (task routing, tests, coverage, assignments).

    Example implementing a custom backend:
        >>> class DatabaseBackend:
        ...     def log_call(self, record: LLMCallRecord) -> None:
        ...         # Insert into database
        ...         pass
        ...
        ...     def log_workflow(self, record: WorkflowRunRecord) -> None:
        ...         # Insert into database
        ...         pass
        ...
        ...     def get_calls(self, since=None, workflow_name=None, limit=1000):
        ...         # Query database
        ...         return []
        ...
        ...     def get_workflows(self, since=None, workflow_name=None, limit=100):
        ...         # Query database
        ...         return []
    """

    def log_call(self, record: LLMCallRecord) -> None:
        """Log an LLM call record."""
        ...

    def log_workflow(self, record: WorkflowRunRecord) -> None:
        """Log a workflow run record."""
        ...

    def get_calls(
        self,
        since: datetime | None = None,
        workflow_name: str | None = None,
        limit: int = 1000,
    ) -> list[LLMCallRecord]:
        """Get LLM call records with optional filters."""
        ...

    def get_workflows(
        self,
        since: datetime | None = None,
        workflow_name: str | None = None,
        limit: int = 100,
    ) -> list[WorkflowRunRecord]:
        """Get workflow run records with optional filters."""
        ...

    # Tier 1 automation monitoring methods
    def log_task_routing(self, record: TaskRoutingRecord) -> None:
        """Log a task routing decision."""
        ...

    def log_test_execution(self, record: TestExecutionRecord) -> None:
        """Log a test execution."""
        ...

    def log_coverage(self, record: CoverageRecord) -> None:
        """Log coverage metrics."""
        ...

    def log_agent_assignment(self, record: AgentAssignmentRecord) -> None:
        """Log an agent assignment."""
        ...

    def get_task_routings(
        self,
        since: datetime | None = None,
        status: str | None = None,
        limit: int = 1000,
    ) -> list[TaskRoutingRecord]:
        """Get task routing records with optional filters."""
        ...

    def get_test_executions(
        self,
        since: datetime | None = None,
        success_only: bool = False,
        limit: int = 100,
    ) -> list[TestExecutionRecord]:
        """Get test execution records with optional filters."""
        ...

    def get_coverage_history(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[CoverageRecord]:
        """Get coverage history records."""
        ...

    def get_agent_assignments(
        self,
        since: datetime | None = None,
        automated_only: bool = True,
        limit: int = 1000,
    ) -> list[AgentAssignmentRecord]:
        """Get agent assignment records with optional filters."""
        ...

    # Per-file test tracking methods
    def log_file_test(self, record: "FileTestRecord") -> None:
        """Log a per-file test execution record."""
        ...

    def get_file_tests(
        self,
        file_path: str | None = None,
        since: datetime | None = None,
        result_filter: str | None = None,
        limit: int = 1000,
    ) -> list["FileTestRecord"]:
        """Get per-file test records with optional filters."""
        ...

    def get_latest_file_test(self, file_path: str) -> "FileTestRecord | None":
        """Get the most recent test record for a specific file."""
        ...


def _parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO format timestamp, handling 'Z' suffix for Python 3.10 compatibility.

    Args:
        timestamp_str: ISO format timestamp string, possibly with 'Z' suffix

    Returns:
        Parsed datetime object (timezone-naive UTC)
    """
    # Python 3.10's fromisoformat() doesn't handle 'Z' suffix
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1]

    dt = datetime.fromisoformat(timestamp_str)

    # Convert to naive UTC if timezone-aware
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    return dt


class TelemetryStore:
    """JSONL file-based telemetry backend (default implementation).

    Stores records in JSONL format for easy streaming and analysis.
    Implements the TelemetryBackend protocol.

    Supports both core telemetry and Tier 1 automation monitoring.
    """

    def __init__(self, storage_dir: str = ".empathy"):
        """Initialize telemetry store.

        Args:
            storage_dir: Directory for telemetry files

        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Core telemetry files
        self.calls_file = self.storage_dir / "llm_calls.jsonl"
        self.workflows_file = self.storage_dir / "workflow_runs.jsonl"

        # Tier 1 automation monitoring files
        self.task_routing_file = self.storage_dir / "task_routing.jsonl"
        self.test_executions_file = self.storage_dir / "test_executions.jsonl"
        self.coverage_history_file = self.storage_dir / "coverage_history.jsonl"
        self.agent_assignments_file = self.storage_dir / "agent_assignments.jsonl"

        # Per-file test tracking
        self.file_tests_file = self.storage_dir / "file_tests.jsonl"

    def log_call(self, record: LLMCallRecord) -> None:
        """Log an LLM call record."""
        with open(self.calls_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def log_workflow(self, record: WorkflowRunRecord) -> None:
        """Log a workflow run record."""
        with open(self.workflows_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def get_calls(
        self,
        since: datetime | None = None,
        workflow_name: str | None = None,
        limit: int = 1000,
    ) -> list[LLMCallRecord]:
        """Get LLM call records.

        Args:
            since: Only return records after this time
            workflow_name: Filter by workflow name
            limit: Maximum records to return

        Returns:
            List of LLMCallRecord

        """
        records: list[LLMCallRecord] = []
        if not self.calls_file.exists():
            return records

        with open(self.calls_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    record = LLMCallRecord.from_dict(data)

                    # Apply filters
                    if since:
                        record_time = _parse_timestamp(record.timestamp)
                        if record_time < since:
                            continue

                    if workflow_name and record.workflow_name != workflow_name:
                        continue

                    records.append(record)

                    if len(records) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        return records

    def get_workflows(
        self,
        since: datetime | None = None,
        workflow_name: str | None = None,
        limit: int = 100,
    ) -> list[WorkflowRunRecord]:
        """Get workflow run records.

        Args:
            since: Only return records after this time
            workflow_name: Filter by workflow name
            limit: Maximum records to return

        Returns:
            List of WorkflowRunRecord

        """
        records: list[WorkflowRunRecord] = []
        if not self.workflows_file.exists():
            return records

        with open(self.workflows_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    record = WorkflowRunRecord.from_dict(data)

                    # Apply filters
                    if since:
                        record_time = _parse_timestamp(record.started_at)
                        if record_time < since:
                            continue

                    if workflow_name and record.workflow_name != workflow_name:
                        continue

                    records.append(record)

                    if len(records) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        return records

    # Tier 1 automation monitoring methods

    def log_task_routing(self, record: TaskRoutingRecord) -> None:
        """Log a task routing decision."""
        with open(self.task_routing_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def log_test_execution(self, record: TestExecutionRecord) -> None:
        """Log a test execution."""
        with open(self.test_executions_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def log_coverage(self, record: CoverageRecord) -> None:
        """Log coverage metrics."""
        with open(self.coverage_history_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def log_agent_assignment(self, record: AgentAssignmentRecord) -> None:
        """Log an agent assignment."""
        with open(self.agent_assignments_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def get_task_routings(
        self,
        since: datetime | None = None,
        status: str | None = None,
        limit: int = 1000,
    ) -> list[TaskRoutingRecord]:
        """Get task routing records.

        Args:
            since: Only return records after this time
            status: Filter by status (pending, running, completed, failed)
            limit: Maximum records to return

        Returns:
            List of TaskRoutingRecord

        """
        records: list[TaskRoutingRecord] = []
        if not self.task_routing_file.exists():
            return records

        with open(self.task_routing_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    record = TaskRoutingRecord.from_dict(data)

                    # Apply filters
                    if since:
                        record_time = _parse_timestamp(record.timestamp)
                        if record_time < since:
                            continue

                    if status and record.status != status:
                        continue

                    records.append(record)

                    if len(records) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        return records

    def get_test_executions(
        self,
        since: datetime | None = None,
        success_only: bool = False,
        limit: int = 100,
    ) -> list[TestExecutionRecord]:
        """Get test execution records.

        Args:
            since: Only return records after this time
            success_only: Only return successful test runs
            limit: Maximum records to return

        Returns:
            List of TestExecutionRecord

        """
        records: list[TestExecutionRecord] = []
        if not self.test_executions_file.exists():
            return records

        with open(self.test_executions_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    record = TestExecutionRecord.from_dict(data)

                    # Apply filters
                    if since:
                        record_time = _parse_timestamp(record.timestamp)
                        if record_time < since:
                            continue

                    if success_only and not record.success:
                        continue

                    records.append(record)

                    if len(records) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        return records

    def get_coverage_history(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[CoverageRecord]:
        """Get coverage history records.

        Args:
            since: Only return records after this time
            limit: Maximum records to return

        Returns:
            List of CoverageRecord

        """
        records: list[CoverageRecord] = []
        if not self.coverage_history_file.exists():
            return records

        with open(self.coverage_history_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    record = CoverageRecord.from_dict(data)

                    # Apply filters
                    if since:
                        record_time = _parse_timestamp(record.timestamp)
                        if record_time < since:
                            continue

                    records.append(record)

                    if len(records) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        return records

    def get_agent_assignments(
        self,
        since: datetime | None = None,
        automated_only: bool = True,
        limit: int = 1000,
    ) -> list[AgentAssignmentRecord]:
        """Get agent assignment records.

        Args:
            since: Only return records after this time
            automated_only: Only return assignments eligible for Tier 1 automation
            limit: Maximum records to return

        Returns:
            List of AgentAssignmentRecord

        """
        records: list[AgentAssignmentRecord] = []
        if not self.agent_assignments_file.exists():
            return records

        with open(self.agent_assignments_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    record = AgentAssignmentRecord.from_dict(data)

                    # Apply filters
                    if since:
                        record_time = _parse_timestamp(record.timestamp)
                        if record_time < since:
                            continue

                    if automated_only and not record.automated_eligible:
                        continue

                    records.append(record)

                    if len(records) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        return records

    # Per-file test tracking methods

    def log_file_test(self, record: "FileTestRecord") -> None:
        """Log a per-file test execution record.

        Args:
            record: FileTestRecord to log
        """
        with open(self.file_tests_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def get_file_tests(
        self,
        file_path: str | None = None,
        since: datetime | None = None,
        result_filter: str | None = None,
        limit: int = 1000,
    ) -> list["FileTestRecord"]:
        """Get per-file test records with optional filters.

        Args:
            file_path: Filter by specific file path
            since: Only return records after this time
            result_filter: Filter by result (passed, failed, error, skipped, no_tests)
            limit: Maximum records to return

        Returns:
            List of FileTestRecord
        """
        records: list[FileTestRecord] = []
        if not self.file_tests_file.exists():
            return records

        with open(self.file_tests_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    record = FileTestRecord.from_dict(data)

                    # Apply filters
                    if file_path and record.file_path != file_path:
                        continue

                    if since:
                        record_time = _parse_timestamp(record.timestamp)
                        if record_time < since:
                            continue

                    if result_filter and record.last_test_result != result_filter:
                        continue

                    records.append(record)

                    if len(records) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        return records

    def get_latest_file_test(self, file_path: str) -> "FileTestRecord | None":
        """Get the most recent test record for a specific file.

        Args:
            file_path: Path to the source file

        Returns:
            Most recent FileTestRecord or None if not found
        """
        records = self.get_file_tests(file_path=file_path, limit=10000)
        if not records:
            return None

        # Return the most recent record (last one since we read in chronological order)
        return records[-1]

    def get_files_needing_tests(
        self,
        stale_only: bool = False,
        failed_only: bool = False,
    ) -> list["FileTestRecord"]:
        """Get files that need test attention.

        Args:
            stale_only: Only return files with stale tests
            failed_only: Only return files with failed tests

        Returns:
            List of FileTestRecord for files needing attention
        """
        all_records = self.get_file_tests(limit=100000)

        # Get latest record per file
        latest_by_file: dict[str, FileTestRecord] = {}
        for record in all_records:
            existing = latest_by_file.get(record.file_path)
            if existing is None:
                latest_by_file[record.file_path] = record
            else:
                # Keep the more recent one
                if record.timestamp > existing.timestamp:
                    latest_by_file[record.file_path] = record

        # Filter based on criteria
        results = []
        for record in latest_by_file.values():
            if stale_only and not record.is_stale:
                continue
            if failed_only and record.last_test_result not in ("failed", "error"):
                continue
            if not stale_only and not failed_only:
                # Return all files needing attention (stale OR failed OR no_tests)
                if (
                    record.last_test_result not in ("failed", "error", "no_tests")
                    and not record.is_stale
                ):
                    continue
            results.append(record)

        return results


class TelemetryAnalytics:
    """Analytics helpers for telemetry data.

    Provides insights into cost optimization, provider usage, and performance.
    """

    def __init__(self, store: TelemetryStore | None = None):
        """Initialize analytics.

        Args:
            store: TelemetryStore to analyze (creates default if None)

        """
        self.store = store or TelemetryStore()

    def top_expensive_workflows(
        self,
        n: int = 10,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get the most expensive workflows.

        Args:
            n: Number of workflows to return
            since: Only consider workflows after this time

        Returns:
            List of dicts with workflow_name, total_cost, run_count

        """
        workflows = self.store.get_workflows(since=since, limit=10000)

        # Aggregate by workflow name
        costs: dict[str, dict[str, Any]] = {}
        for wf in workflows:
            if wf.workflow_name not in costs:
                costs[wf.workflow_name] = {
                    "workflow_name": wf.workflow_name,
                    "total_cost": 0.0,
                    "run_count": 0,
                    "total_savings": 0.0,
                    "avg_duration_ms": 0,
                }
            costs[wf.workflow_name]["total_cost"] += wf.total_cost
            costs[wf.workflow_name]["run_count"] += 1
            costs[wf.workflow_name]["total_savings"] += wf.savings

        # Calculate averages and sort
        result = list(costs.values())
        for item in result:
            if item["run_count"] > 0:
                item["avg_cost"] = item["total_cost"] / item["run_count"]

        result.sort(key=lambda x: x["total_cost"], reverse=True)
        return result[:n]

    def provider_usage_summary(
        self,
        since: datetime | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Get usage summary by provider.

        Args:
            since: Only consider calls after this time

        Returns:
            Dict mapping provider to usage stats

        """
        calls = self.store.get_calls(since=since, limit=100000)

        summary: dict[str, dict[str, Any]] = {}
        for call in calls:
            if call.provider not in summary:
                summary[call.provider] = {
                    "call_count": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "error_count": 0,
                    "avg_latency_ms": 0,
                    "by_tier": {"cheap": 0, "capable": 0, "premium": 0},
                }

            s = summary[call.provider]
            s["call_count"] += 1
            s["total_tokens"] += call.input_tokens + call.output_tokens
            s["total_cost"] += call.estimated_cost
            if not call.success:
                s["error_count"] += 1
            if call.tier in s["by_tier"]:
                s["by_tier"][call.tier] += 1

        # Calculate averages
        for _provider, stats in summary.items():
            if stats["call_count"] > 0:
                stats["avg_cost"] = stats["total_cost"] / stats["call_count"]

        return summary

    def tier_distribution(
        self,
        since: datetime | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Get call distribution by tier.

        Args:
            since: Only consider calls after this time

        Returns:
            Dict mapping tier to stats

        """
        calls = self.store.get_calls(since=since, limit=100000)

        dist: dict[str, dict[str, Any]] = {
            "cheap": {"count": 0, "cost": 0.0, "tokens": 0},
            "capable": {"count": 0, "cost": 0.0, "tokens": 0},
            "premium": {"count": 0, "cost": 0.0, "tokens": 0},
        }

        for call in calls:
            if call.tier in dist:
                dist[call.tier]["count"] += 1
                dist[call.tier]["cost"] += call.estimated_cost
                dist[call.tier]["tokens"] += call.input_tokens + call.output_tokens

        total_calls = sum(d["count"] for d in dist.values())
        for _tier, stats in dist.items():
            stats["percent"] = (stats["count"] / total_calls * 100) if total_calls > 0 else 0

        return dist

    def fallback_stats(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get fallback usage statistics.

        Args:
            since: Only consider calls after this time

        Returns:
            Dict with fallback stats

        """
        calls = self.store.get_calls(since=since, limit=100000)

        total = len(calls)
        fallback_count = sum(1 for c in calls if c.fallback_used)
        error_count = sum(1 for c in calls if not c.success)

        # Count by original provider
        by_provider: dict[str, int] = {}
        for call in calls:
            if call.fallback_used and call.original_provider:
                by_provider[call.original_provider] = by_provider.get(call.original_provider, 0) + 1

        return {
            "total_calls": total,
            "fallback_count": fallback_count,
            "fallback_percent": (fallback_count / total * 100) if total > 0 else 0,
            "error_count": error_count,
            "error_rate": (error_count / total * 100) if total > 0 else 0,
            "by_original_provider": by_provider,
        }

    def sonnet_opus_fallback_analysis(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Analyze Sonnet 4.5 → Opus 4.5 fallback performance and cost savings.

        Tracks:
        - How often Sonnet 4.5 succeeds vs needs Opus fallback
        - Cost savings from using Sonnet instead of always using Opus
        - Success rates by model

        Args:
            since: Only consider calls after this time

        Returns:
            Dict with fallback analysis and cost savings
        """
        calls = self.store.get_calls(since=since, limit=100000)

        # Filter for Anthropic calls (Sonnet/Opus)
        anthropic_calls = [
            c
            for c in calls
            if c.provider == "anthropic"
            and c.model_id in ["claude-sonnet-4-5", "claude-opus-4-5-20251101"]
        ]

        if not anthropic_calls:
            return {
                "total_calls": 0,
                "sonnet_attempts": 0,
                "sonnet_successes": 0,
                "opus_fallbacks": 0,
                "success_rate_sonnet": 0.0,
                "fallback_rate": 0.0,
                "actual_cost": 0.0,
                "always_opus_cost": 0.0,
                "savings": 0.0,
                "savings_percent": 0.0,
            }

        total = len(anthropic_calls)

        # Count Sonnet attempts and successes
        sonnet_calls = [c for c in anthropic_calls if c.model_id == "claude-sonnet-4-5"]
        sonnet_successes = sum(1 for c in sonnet_calls if c.success)

        # Count Opus fallbacks (calls with fallback_used and ended up on Opus)
        opus_fallbacks = sum(
            1
            for c in anthropic_calls
            if c.model_id == "claude-opus-4-5-20251101" and c.fallback_used
        )

        # Calculate costs
        actual_cost = sum(c.estimated_cost for c in anthropic_calls)

        # Calculate what it would cost if everything used Opus
        opus_input_cost = 15.00 / 1_000_000  # per token
        opus_output_cost = 75.00 / 1_000_000  # per token
        always_opus_cost = sum(
            (c.input_tokens * opus_input_cost) + (c.output_tokens * opus_output_cost)
            for c in anthropic_calls
        )

        savings = always_opus_cost - actual_cost
        savings_percent = (savings / always_opus_cost * 100) if always_opus_cost > 0 else 0

        return {
            "total_calls": total,
            "sonnet_attempts": len(sonnet_calls),
            "sonnet_successes": sonnet_successes,
            "opus_fallbacks": opus_fallbacks,
            "success_rate_sonnet": (
                (sonnet_successes / len(sonnet_calls) * 100) if sonnet_calls else 0.0
            ),
            "fallback_rate": (opus_fallbacks / total * 100) if total > 0 else 0.0,
            "actual_cost": actual_cost,
            "always_opus_cost": always_opus_cost,
            "savings": savings,
            "savings_percent": savings_percent,
            "avg_cost_per_call": actual_cost / total if total > 0 else 0.0,
            "avg_opus_cost_per_call": always_opus_cost / total if total > 0 else 0.0,
        }

    def cost_savings_report(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Generate cost savings report.

        Args:
            since: Only consider workflows after this time

        Returns:
            Dict with savings analysis

        """
        workflows = self.store.get_workflows(since=since, limit=10000)

        total_cost = sum(wf.total_cost for wf in workflows)
        total_baseline = sum(wf.baseline_cost for wf in workflows)
        total_savings = sum(wf.savings for wf in workflows)

        return {
            "workflow_count": len(workflows),
            "total_actual_cost": total_cost,
            "total_baseline_cost": total_baseline,
            "total_savings": total_savings,
            "savings_percent": (
                (total_savings / total_baseline * 100) if total_baseline > 0 else 0
            ),
            "avg_cost_per_workflow": total_cost / len(workflows) if workflows else 0,
        }

    # Tier 1 automation monitoring analytics

    def task_routing_accuracy(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Analyze task routing accuracy.

        Args:
            since: Only consider routings after this time

        Returns:
            Dict with routing accuracy metrics by task type and strategy

        """
        routings = self.store.get_task_routings(since=since, limit=10000)

        if not routings:
            return {
                "total_tasks": 0,
                "successful_routing": 0,
                "accuracy_rate": 0.0,
                "avg_confidence": 0.0,
                "by_task_type": {},
                "by_strategy": {},
            }

        total = len(routings)
        successful = sum(1 for r in routings if r.success)
        total_confidence = sum(r.confidence_score for r in routings)

        # Aggregate by task type
        by_type: dict[str, dict[str, int | float]] = {}
        for r in routings:
            if r.task_type not in by_type:
                by_type[r.task_type] = {"total": 0, "success": 0}
            by_type[r.task_type]["total"] += 1
            if r.success:
                by_type[r.task_type]["success"] += 1

        # Calculate rates
        for _task_type, stats in by_type.items():
            stats["rate"] = stats["success"] / stats["total"] if stats["total"] > 0 else 0.0

        # Aggregate by strategy
        by_strategy: dict[str, dict[str, int]] = {}
        for r in routings:
            if r.routing_strategy not in by_strategy:
                by_strategy[r.routing_strategy] = {"total": 0, "success": 0}
            by_strategy[r.routing_strategy]["total"] += 1
            if r.success:
                by_strategy[r.routing_strategy]["success"] += 1

        return {
            "total_tasks": total,
            "successful_routing": successful,
            "accuracy_rate": successful / total if total > 0 else 0.0,
            "avg_confidence": total_confidence / total if total > 0 else 0.0,
            "by_task_type": by_type,
            "by_strategy": by_strategy,
        }

    def test_execution_trends(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Analyze test execution trends.

        Args:
            since: Only consider executions after this time

        Returns:
            Dict with test execution metrics and trends

        """
        executions = self.store.get_test_executions(since=since, limit=1000)

        if not executions:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": 0.0,
                "total_tests_run": 0,
                "total_failures": 0,
                "coverage_trend": "stable",
                "most_failing_tests": [],
            }

        total_execs = len(executions)
        successful_execs = sum(1 for e in executions if e.success)
        total_duration = sum(e.duration_seconds for e in executions)
        total_tests = sum(e.total_tests for e in executions)
        total_failures = sum(e.failed for e in executions)

        # Find most failing tests
        failure_counts: dict[str, int] = {}
        for exec_rec in executions:
            for test in exec_rec.failed_tests:
                test_name = test.get("name", "unknown")
                failure_counts[test_name] = failure_counts.get(test_name, 0) + 1

        most_failing = [
            {"name": name, "failures": count}
            for name, count in heapq.nlargest(10, failure_counts.items(), key=lambda x: x[1])
        ]

        return {
            "total_executions": total_execs,
            "success_rate": successful_execs / total_execs if total_execs > 0 else 0.0,
            "avg_duration_seconds": total_duration / total_execs if total_execs > 0 else 0.0,
            "total_tests_run": total_tests,
            "total_failures": total_failures,
            "coverage_trend": "stable",  # Will be computed from coverage_progress
            "most_failing_tests": most_failing,
        }

    def coverage_progress(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Track coverage progress over time.

        Args:
            since: Only consider coverage records after this time

        Returns:
            Dict with coverage metrics and trends

        """
        records = self.store.get_coverage_history(since=since, limit=1000)

        if not records:
            return {
                "current_coverage": 0.0,
                "previous_coverage": 0.0,
                "change": 0.0,
                "trend": "no_data",
                "coverage_history": [],
                "files_improved": 0,
                "files_declined": 0,
                "critical_gaps_count": 0,
            }

        # Latest and first records
        latest = records[-1]
        first = records[0]
        current_coverage = latest.overall_percentage

        # Calculate trend by comparing first to last
        if len(records) == 1:
            # Single record - no trend analysis possible
            prev_coverage = 0.0
            change = 0.0
            trend = "stable"
        else:
            # Multiple records - compare first to last
            prev_coverage = first.overall_percentage
            change = current_coverage - prev_coverage

            # Determine trend based on change
            if change > 1.0:
                trend = "improving"
            elif change < -1.0:
                trend = "declining"
            else:
                trend = "stable"

        # Build coverage history from records
        coverage_history = [
            {
                "timestamp": r.timestamp,
                "coverage": r.overall_percentage,
                "trend": r.trend,
            }
            for r in records
        ]

        return {
            "current_coverage": current_coverage,
            "previous_coverage": prev_coverage,
            "change": change,
            "trend": trend,
            "coverage_history": coverage_history,
            "files_improved": 0,  # Would need file-level history
            "files_declined": 0,  # Would need file-level history
            "critical_gaps_count": len(latest.critical_gaps),
        }

    def agent_performance(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Analyze agent/workflow performance.

        Args:
            since: Only consider assignments after this time

        Returns:
            Dict with agent performance metrics

        """
        assignments = self.store.get_agent_assignments(
            since=since, automated_only=False, limit=10000
        )

        if not assignments:
            return {
                "total_assignments": 0,
                "by_agent": {},
                "automation_rate": 0.0,
                "human_review_rate": 0.0,
            }

        # Aggregate by agent
        by_agent: dict[str, dict[str, Any]] = {}
        total_assignments = len(assignments)
        total_automated = 0
        total_human_review = 0

        for assignment in assignments:
            agent = assignment.assigned_agent
            if agent not in by_agent:
                by_agent[agent] = {
                    "assignments": 0,
                    "completed": 0,
                    "successful": 0,
                    "success_rate": 0.0,
                    "avg_duration_hours": 0.0,
                    "quality_score_avg": 0.0,
                    "total_duration": 0.0,
                    "quality_scores": [],
                }

            stats = by_agent[agent]
            stats["assignments"] += 1
            if assignment.status == "completed":
                stats["completed"] += 1
                if assignment.actual_duration_hours is not None:
                    stats["total_duration"] += assignment.actual_duration_hours

            # Track successful assignments (not just completed)
            if assignment.success:
                stats["successful"] += 1

            if assignment.automated_eligible:
                total_automated += 1
            if assignment.human_review_required:
                total_human_review += 1

        # Calculate averages
        for _agent, stats in by_agent.items():
            if stats["assignments"] > 0:
                stats["success_rate"] = stats["successful"] / stats["assignments"]
            if stats["completed"] > 0:
                stats["avg_duration_hours"] = stats["total_duration"] / stats["completed"]

            # Remove helper fields
            del stats["total_duration"]
            del stats["quality_scores"]
            del stats["successful"]  # Remove helper field, keep success_rate

        return {
            "total_assignments": total_assignments,
            "by_agent": by_agent,
            "automation_rate": (
                total_automated / total_assignments if total_assignments > 0 else 0.0
            ),
            "human_review_rate": (
                total_human_review / total_assignments if total_assignments > 0 else 0.0
            ),
        }

    def tier1_summary(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Comprehensive Tier 1 automation summary.

        Args:
            since: Only consider records after this time

        Returns:
            Dict combining all Tier 1 metrics

        """
        return {
            "task_routing": self.task_routing_accuracy(since),
            "test_execution": self.test_execution_trends(since),
            "coverage": self.coverage_progress(since),
            "agent_performance": self.agent_performance(since),
            "cost_savings": self.cost_savings_report(since),
        }


# Singleton for global telemetry
_telemetry_store: TelemetryStore | None = None


def get_telemetry_store(storage_dir: str = ".empathy") -> TelemetryStore:
    """Get or create the global telemetry store."""
    global _telemetry_store
    if _telemetry_store is None:
        _telemetry_store = TelemetryStore(storage_dir)
    return _telemetry_store


def log_llm_call(record: LLMCallRecord) -> None:
    """Convenience function to log an LLM call."""
    get_telemetry_store().log_call(record)


def log_workflow_run(record: WorkflowRunRecord) -> None:
    """Convenience function to log a workflow run."""
    get_telemetry_store().log_workflow(record)
