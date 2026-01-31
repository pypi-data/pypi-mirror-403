"""Unified Memory Interface for Empathy Framework

Provides a single API for both short-term (Redis) and long-term (persistent) memory,
with automatic pattern promotion and environment-aware storage backend selection.

Usage:
    from empathy_os.memory import UnifiedMemory

    memory = UnifiedMemory(
        user_id="agent@company.com",
        environment="production",  # or "staging", "development"
    )

    # Short-term operations
    memory.stash("working_data", {"key": "value"})
    data = memory.retrieve("working_data")

    # Long-term operations
    result = memory.persist_pattern(content, pattern_type="algorithm")
    pattern = memory.recall_pattern(pattern_id)

    # Pattern promotion
    memory.promote_pattern(staged_pattern_id)

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

import heapq
import json
import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

from .claude_memory import ClaudeMemoryConfig
from .config import get_redis_memory
from .file_session import FileSessionConfig, FileSessionMemory
from .long_term import Classification, LongTermMemory, SecureMemDocsIntegration
from .redis_bootstrap import RedisStartMethod, RedisStatus, ensure_redis
from .short_term import (
    AccessTier,
    AgentCredentials,
    RedisShortTermMemory,
    StagedPattern,
    TTLStrategy,
)

logger = structlog.get_logger(__name__)


class Environment(Enum):
    """Deployment environment for storage configuration."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class MemoryConfig:
    """Configuration for unified memory system."""

    # Environment
    environment: Environment = Environment.DEVELOPMENT

    # File-first architecture settings (always available)
    file_session_enabled: bool = True  # Use file-based session as primary
    file_session_dir: str = ".empathy"  # Directory for file-based storage

    # Short-term memory settings (Redis - optional enhancement)
    redis_url: str | None = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_mock: bool = False
    redis_auto_start: bool = False  # Changed to False - file-first by default
    redis_required: bool = False  # If True, fail without Redis
    default_ttl_seconds: int = 3600  # 1 hour

    # Long-term memory settings
    storage_dir: str = "./memdocs_storage"
    encryption_enabled: bool = True

    # Claude memory settings
    claude_memory_enabled: bool = True
    load_enterprise_memory: bool = True
    load_project_memory: bool = True
    load_user_memory: bool = True

    # Pattern promotion settings
    auto_promote_threshold: float = 0.8  # Confidence threshold for auto-promotion

    # Compact state auto-generation
    auto_generate_compact_state: bool = True
    compact_state_path: str = ".claude/compact-state.md"

    @classmethod
    def from_environment(cls) -> "MemoryConfig":
        """Create configuration from environment variables.

        Environment Variables:
            EMPATHY_ENV: Environment (development/staging/production)
            EMPATHY_FILE_SESSION: Enable file-based session (true/false, default: true)
            EMPATHY_FILE_SESSION_DIR: Directory for file-based storage
            REDIS_URL: Redis connection URL
            EMPATHY_REDIS_MOCK: Use mock Redis (true/false)
            EMPATHY_REDIS_AUTO_START: Auto-start Redis (true/false, default: false)
            EMPATHY_REDIS_REQUIRED: Fail without Redis (true/false, default: false)
            EMPATHY_STORAGE_DIR: Long-term storage directory
            EMPATHY_ENCRYPTION: Enable encryption (true/false)
        """
        env_str = os.getenv("EMPATHY_ENV", "development").lower()
        environment = (
            Environment(env_str)
            if env_str in [e.value for e in Environment]
            else Environment.DEVELOPMENT
        )

        return cls(
            environment=environment,
            # File-first settings (always available)
            file_session_enabled=os.getenv("EMPATHY_FILE_SESSION", "true").lower() == "true",
            file_session_dir=os.getenv("EMPATHY_FILE_SESSION_DIR", ".empathy"),
            # Redis settings (optional)
            redis_url=os.getenv("REDIS_URL"),
            redis_host=os.getenv("EMPATHY_REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("EMPATHY_REDIS_PORT", "6379")),
            redis_mock=os.getenv("EMPATHY_REDIS_MOCK", "").lower() == "true",
            redis_auto_start=os.getenv("EMPATHY_REDIS_AUTO_START", "false").lower() == "true",
            redis_required=os.getenv("EMPATHY_REDIS_REQUIRED", "false").lower() == "true",
            # Long-term storage
            storage_dir=os.getenv("EMPATHY_STORAGE_DIR", "./memdocs_storage"),
            encryption_enabled=os.getenv("EMPATHY_ENCRYPTION", "true").lower() == "true",
            claude_memory_enabled=os.getenv("EMPATHY_CLAUDE_MEMORY", "true").lower() == "true",
            # Compact state
            auto_generate_compact_state=os.getenv("EMPATHY_AUTO_COMPACT_STATE", "true").lower()
            == "true",
            compact_state_path=os.getenv("EMPATHY_COMPACT_STATE_PATH", ".claude/compact-state.md"),
        )


@dataclass
class UnifiedMemory:
    """Unified interface for short-term and long-term memory.

    Provides:
    - Short-term memory (Redis): Fast, TTL-based working memory
    - Long-term memory (Persistent): Cross-session pattern storage
    - Pattern promotion: Move validated patterns from short to long-term
    - Environment-aware configuration: Auto-detect storage backends
    """

    user_id: str
    config: MemoryConfig = field(default_factory=MemoryConfig.from_environment)
    access_tier: AccessTier = AccessTier.CONTRIBUTOR

    # Internal state
    _file_session: FileSessionMemory | None = field(default=None, init=False)  # Primary storage
    _short_term: RedisShortTermMemory | None = field(default=None, init=False)  # Optional Redis
    _long_term: SecureMemDocsIntegration | None = field(default=None, init=False)
    _simple_long_term: LongTermMemory | None = field(default=None, init=False)
    _redis_status: RedisStatus | None = field(default=None, init=False)
    _initialized: bool = field(default=False, init=False)
    # LRU cache for pattern lookups (pattern_id -> pattern_data)
    _pattern_cache: dict[str, dict[str, Any]] = field(default_factory=dict, init=False)
    _pattern_cache_max_size: int = field(default=100, init=False)

    def __post_init__(self):
        """Initialize memory backends based on configuration."""
        self._initialize_backends()

    def _initialize_backends(self):
        """Initialize short-term and long-term memory backends.

        File-First Architecture:
        1. FileSessionMemory is always initialized (primary storage)
        2. Redis is optional (for real-time features like pub/sub)
        3. Falls back gracefully when Redis is unavailable
        """
        if self._initialized:
            return

        # Initialize file-based session memory (PRIMARY - always available)
        if self.config.file_session_enabled:
            try:
                file_config = FileSessionConfig(base_dir=self.config.file_session_dir)
                self._file_session = FileSessionMemory(
                    user_id=self.user_id,
                    config=file_config,
                )
                logger.info(
                    "file_session_memory_initialized",
                    base_dir=self.config.file_session_dir,
                    session_id=self._file_session._state.session_id,
                )
            except Exception as e:
                logger.error("file_session_memory_failed", error=str(e))
                self._file_session = None

        # Initialize Redis short-term memory (OPTIONAL - for real-time features)
        try:
            if self.config.redis_mock:
                self._short_term = RedisShortTermMemory(use_mock=True)
                self._redis_status = RedisStatus(
                    available=False,
                    method=RedisStartMethod.MOCK,
                    message="Mock mode explicitly enabled",
                )
            elif self.config.redis_url:
                self._short_term = get_redis_memory(url=self.config.redis_url)
                self._redis_status = RedisStatus(
                    available=True,
                    method=RedisStartMethod.ALREADY_RUNNING,
                    message="Connected via REDIS_URL",
                )
            # Use auto-start if enabled
            elif self.config.redis_auto_start:
                self._redis_status = ensure_redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    auto_start=True,
                    verbose=True,
                )
                if self._redis_status.available:
                    self._short_term = RedisShortTermMemory(
                        host=self.config.redis_host,
                        port=self.config.redis_port,
                        use_mock=False,
                    )
                else:
                    # File session is primary, so Redis mock is not needed
                    self._short_term = None
                    self._redis_status = RedisStatus(
                        available=False,
                        method=RedisStartMethod.MOCK,
                        message="Redis unavailable, using file-based storage",
                    )
            else:
                # Try to connect to existing Redis
                try:
                    self._short_term = get_redis_memory()
                    if self._short_term.is_connected():
                        self._redis_status = RedisStatus(
                            available=True,
                            method=RedisStartMethod.ALREADY_RUNNING,
                            message="Connected to existing Redis",
                        )
                    else:
                        self._short_term = None
                        self._redis_status = RedisStatus(
                            available=False,
                            method=RedisStartMethod.MOCK,
                            message="Redis not available, using file-based storage",
                        )
                except Exception:
                    self._short_term = None
                    self._redis_status = RedisStatus(
                        available=False,
                        method=RedisStartMethod.MOCK,
                        message="Redis not available, using file-based storage",
                    )

            logger.info(
                "short_term_memory_initialized",
                redis_available=self._redis_status.available if self._redis_status else False,
                file_session_available=self._file_session is not None,
                redis_method=self._redis_status.method.value if self._redis_status else "none",
                environment=self.config.environment.value,
            )

            # Fail if Redis is required but not available
            if self.config.redis_required and not (
                self._redis_status and self._redis_status.available
            ):
                raise RuntimeError("Redis is required but not available")

        except RuntimeError:
            raise  # Re-raise required Redis error
        except Exception as e:
            logger.warning("redis_initialization_failed", error=str(e))
            self._short_term = None
            self._redis_status = RedisStatus(
                available=False,
                method=RedisStartMethod.MOCK,
                message=f"Failed to initialize: {e}",
            )

        # Initialize long-term memory (SecureMemDocs)
        try:
            claude_config = ClaudeMemoryConfig(
                enabled=self.config.claude_memory_enabled,
                load_enterprise=self.config.load_enterprise_memory,
                load_project=self.config.load_project_memory,
                load_user=self.config.load_user_memory,
            )
            self._long_term = SecureMemDocsIntegration(
                claude_memory_config=claude_config,
                storage_dir=self.config.storage_dir,
                enable_encryption=self.config.encryption_enabled,
            )

            logger.info(
                "long_term_memory_initialized",
                storage_dir=self.config.storage_dir,
                encryption=self.config.encryption_enabled,
            )
        except Exception as e:
            logger.error("long_term_memory_failed", error=str(e))
            self._long_term = None

        # Initialize simple long-term memory (for testing and simple use cases)
        try:
            self._simple_long_term = LongTermMemory(storage_path=self.config.storage_dir)
            logger.debug("simple_long_term_memory_initialized")
        except Exception as e:
            logger.error("simple_long_term_memory_failed", error=str(e))
            self._simple_long_term = None

        self._initialized = True

    @property
    def credentials(self) -> AgentCredentials:
        """Get agent credentials for short-term memory operations."""
        return AgentCredentials(agent_id=self.user_id, tier=self.access_tier)

    def get_backend_status(self) -> dict[str, Any]:
        """Get the current status of all memory backends.

        Returns a structured dict suitable for health checks, debugging,
        and dashboard display. Can be serialized to JSON.

        Returns:
            dict with keys:
                - environment: Current environment (development/staging/production)
                - short_term: Status of Redis-based short-term memory
                - long_term: Status of persistent long-term memory
                - initialized: Whether backends have been initialized

        Example:
            >>> memory = UnifiedMemory(user_id="agent")
            >>> status = memory.get_backend_status()
            >>> print(status["short_term"]["available"])
            True

        """
        short_term_status: dict[str, Any] = {
            "available": False,
            "mock": True,
            "method": "unknown",
            "message": "Not initialized",
        }

        if self._redis_status:
            short_term_status = {
                "available": self._redis_status.available,
                "mock": not self._redis_status.available
                or self._redis_status.method == RedisStartMethod.MOCK,
                "method": self._redis_status.method.value,
                "message": self._redis_status.message,
            }

        long_term_status: dict[str, Any] = {
            "available": self._long_term is not None,
            "storage_dir": self.config.storage_dir,
            "encryption_enabled": self.config.encryption_enabled,
        }

        return {
            "environment": self.config.environment.value,
            "initialized": self._initialized,
            "short_term": short_term_status,
            "long_term": long_term_status,
        }

    # =========================================================================
    # SHORT-TERM MEMORY OPERATIONS
    # =========================================================================

    def stash(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        """Store data in working memory with TTL.

        Uses file-based session as primary storage, with optional Redis for
        real-time features. Data is persisted to disk automatically.

        Args:
            key: Storage key
            value: Data to store (must be JSON-serializable)
            ttl_seconds: Time-to-live in seconds (default from config)

        Returns:
            True if stored successfully

        """
        ttl = ttl_seconds or self.config.default_ttl_seconds

        # Primary: File session memory (always available)
        if self._file_session:
            self._file_session.stash(key, value, ttl=ttl)

        # Optional: Redis for real-time sync
        if self._short_term and self._redis_status and self._redis_status.available:
            # Map ttl_seconds to TTLStrategy
            ttl_strategy = TTLStrategy.WORKING_RESULTS
            if ttl_seconds is not None:
                if ttl_seconds <= TTLStrategy.COORDINATION.value:
                    ttl_strategy = TTLStrategy.COORDINATION
                elif ttl_seconds <= TTLStrategy.SESSION.value:
                    ttl_strategy = TTLStrategy.SESSION
                elif ttl_seconds <= TTLStrategy.WORKING_RESULTS.value:
                    ttl_strategy = TTLStrategy.WORKING_RESULTS
                elif ttl_seconds <= TTLStrategy.STAGED_PATTERNS.value:
                    ttl_strategy = TTLStrategy.STAGED_PATTERNS
                else:
                    ttl_strategy = TTLStrategy.CONFLICT_CONTEXT

            try:
                self._short_term.stash(key, value, self.credentials, ttl_strategy)
            except Exception as e:
                logger.debug("redis_stash_failed", key=key, error=str(e))

        # Return True if at least one backend succeeded
        return self._file_session is not None

    def retrieve(self, key: str) -> Any | None:
        """Retrieve data from working memory.

        Checks Redis first (if available) for faster access, then falls back
        to file-based session storage.

        Args:
            key: Storage key

        Returns:
            Stored data or None if not found

        """
        # Try Redis first (faster, if available)
        if self._short_term and self._redis_status and self._redis_status.available:
            try:
                result = self._short_term.retrieve(key, self.credentials)
                if result is not None:
                    return result
            except Exception as e:
                logger.debug("redis_retrieve_failed", key=key, error=str(e))

        # Fall back to file session (primary storage)
        if self._file_session:
            return self._file_session.retrieve(key)

        return None

    def stage_pattern(
        self,
        pattern_data: dict[str, Any],
        pattern_type: str = "general",
        ttl_hours: int = 24,
    ) -> str | None:
        """Stage a pattern for validation before long-term storage.

        Args:
            pattern_data: Pattern content and metadata
            pattern_type: Type of pattern (algorithm, protocol, etc.)
            ttl_hours: Hours before staged pattern expires (not used in current impl)

        Returns:
            Staged pattern ID or None if failed

        """
        if not self._short_term:
            logger.warning("short_term_memory_unavailable")
            return None

        # Create a StagedPattern object from the pattern_data dict
        pattern_id = f"staged_{uuid.uuid4().hex[:12]}"
        staged_pattern = StagedPattern(
            pattern_id=pattern_id,
            agent_id=self.user_id,
            pattern_type=pattern_type,
            name=pattern_data.get("name", f"Pattern {pattern_id[:8]}"),
            description=pattern_data.get("description", ""),
            code=pattern_data.get("code"),
            context=pattern_data.get("context", {}),
            confidence=pattern_data.get("confidence", 0.5),
            staged_at=datetime.now(),
            interests=pattern_data.get("interests", []),
        )
        # Store content in context if provided
        if "content" in pattern_data:
            staged_pattern.context["content"] = pattern_data["content"]

        success = self._short_term.stage_pattern(staged_pattern, self.credentials)
        return pattern_id if success else None

    def get_staged_patterns(self) -> list[dict]:
        """Get all staged patterns awaiting validation.

        Returns:
            List of staged patterns with metadata

        """
        if not self._short_term:
            return []

        staged_list = self._short_term.list_staged_patterns(self.credentials)
        return [p.to_dict() for p in staged_list]

    # =========================================================================
    # LONG-TERM MEMORY OPERATIONS
    # =========================================================================

    def persist_pattern(
        self,
        content: str,
        pattern_type: str,
        classification: Classification | str | None = None,
        auto_classify: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Store a pattern in long-term memory with security controls.

        Args:
            content: Pattern content
            pattern_type: Type of pattern (algorithm, protocol, etc.)
            classification: Security classification (PUBLIC/INTERNAL/SENSITIVE)
            auto_classify: Auto-detect classification from content
            metadata: Additional metadata to store

        Returns:
            Storage result with pattern_id and classification, or None if failed

        """
        if not self._long_term:
            logger.error("long_term_memory_unavailable")
            return None

        try:
            # Convert string classification to enum if needed
            explicit_class = None
            if classification is not None:
                if isinstance(classification, str):
                    explicit_class = Classification[classification.upper()]
                else:
                    explicit_class = classification

            result = self._long_term.store_pattern(
                content=content,
                pattern_type=pattern_type,
                user_id=self.user_id,
                explicit_classification=explicit_class,
                auto_classify=auto_classify,
                custom_metadata=metadata,
            )
            logger.info(
                "pattern_persisted",
                pattern_id=result.get("pattern_id"),
                classification=result.get("classification"),
            )
            return result
        except Exception as e:
            logger.error("persist_pattern_failed", error=str(e))
            return None

    def _cache_pattern(self, pattern_id: str, pattern: dict[str, Any]) -> None:
        """Add pattern to LRU cache, evicting oldest if at capacity."""
        # Simple LRU: remove oldest entry if at max size
        if len(self._pattern_cache) >= self._pattern_cache_max_size:
            # Remove first (oldest) item
            oldest_key = next(iter(self._pattern_cache))
            del self._pattern_cache[oldest_key]

        self._pattern_cache[pattern_id] = pattern

    def recall_pattern(
        self,
        pattern_id: str,
        check_permissions: bool = True,
        use_cache: bool = True,
    ) -> dict[str, Any] | None:
        """Retrieve a pattern from long-term memory.

        Uses LRU cache for frequently accessed patterns to reduce I/O.

        Args:
            pattern_id: ID of pattern to retrieve
            check_permissions: Verify user has access to pattern
            use_cache: Whether to use/update the pattern cache (default: True)

        Returns:
            Pattern data with content and metadata, or None if not found

        """
        if not self._long_term:
            logger.error("long_term_memory_unavailable")
            return None

        # Check cache first (if enabled)
        if use_cache and pattern_id in self._pattern_cache:
            logger.debug("pattern_cache_hit", pattern_id=pattern_id)
            return self._pattern_cache[pattern_id]

        try:
            pattern = self._long_term.retrieve_pattern(
                pattern_id=pattern_id,
                user_id=self.user_id,
                check_permissions=check_permissions,
            )

            # Cache the result (if enabled and pattern found)
            if use_cache and pattern:
                self._cache_pattern(pattern_id, pattern)

            return pattern
        except Exception as e:
            logger.error("recall_pattern_failed", pattern_id=pattern_id, error=str(e))
            return None

    def clear_pattern_cache(self) -> int:
        """Clear the pattern lookup cache.

        Returns:
            Number of entries cleared
        """
        count = len(self._pattern_cache)
        self._pattern_cache.clear()
        logger.debug("pattern_cache_cleared", entries=count)
        return count

    def _score_pattern(
        self,
        pattern: dict[str, Any],
        query_lower: str,
        query_words: list[str],
    ) -> float:
        """Calculate relevance score for a pattern.

        Args:
            pattern: Pattern data dictionary
            query_lower: Lowercase query string
            query_words: Pre-split query words (length >= 3)

        Returns:
            Relevance score (0.0 if no match)
        """
        if not query_lower:
            return 1.0  # No query - all patterns have equal score

        content = str(pattern.get("content", "")).lower()
        metadata_str = str(pattern.get("metadata", {})).lower()

        score = 0.0

        # Exact phrase match in content (highest score)
        if query_lower in content:
            score += 10.0

        # Keyword matching (medium score)
        for word in query_words:
            if word in content:
                score += 2.0
            if word in metadata_str:
                score += 1.0

        return score

    def _filter_and_score_patterns(
        self,
        query: str | None,
        pattern_type: str | None,
        classification: Classification | None,
    ) -> Iterator[tuple[float, dict[str, Any]]]:
        """Generator that filters and scores patterns.

        Memory-efficient: yields (score, pattern) tuples one at a time.
        Use with heapq.nlargest() for efficient top-N selection.

        Args:
            query: Search query (case-insensitive)
            pattern_type: Filter by pattern type
            classification: Filter by classification level

        Yields:
            Tuples of (score, pattern) for matching patterns
        """
        query_lower = query.lower() if query else ""
        query_words = [w for w in query_lower.split() if len(w) >= 3] if query else []

        for pattern in self._iter_all_patterns():
            # Apply filters
            if pattern_type and pattern.get("pattern_type") != pattern_type:
                continue

            if classification:
                pattern_class = pattern.get("classification")
                if isinstance(classification, Classification):
                    if pattern_class != classification.value:
                        continue
                elif pattern_class != classification:
                    continue

            # Calculate relevance score
            score = self._score_pattern(pattern, query_lower, query_words)

            # Skip if no matches found (when query is provided)
            if query and score == 0.0:
                continue

            yield (score, pattern)

    def search_patterns(
        self,
        query: str | None = None,
        pattern_type: str | None = None,
        classification: Classification | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search patterns in long-term memory with keyword matching and relevance scoring.

        Implements keyword-based search with:
        1. Full-text search in pattern content and metadata
        2. Filter by pattern_type and classification
        3. Relevance scoring (exact matches rank higher)
        4. Results sorted by relevance

        Memory-efficient: Uses generators and heapq.nlargest() to avoid
        loading all patterns into memory. Only keeps top N results.

        Args:
            query: Text to search for in pattern content (case-insensitive)
            pattern_type: Filter by pattern type (e.g., "meta_workflow_execution")
            classification: Filter by classification level
            limit: Maximum results to return

        Returns:
            List of matching patterns with metadata, sorted by relevance

        Example:
            >>> patterns = memory.search_patterns(
            ...     query="successful workflows",
            ...     pattern_type="meta_workflow_execution",
            ...     limit=5
            ... )
        """
        if not self._long_term:
            logger.debug("long_term_memory_unavailable")
            return []

        try:
            # Use heapq.nlargest for memory-efficient top-N selection
            # This avoids loading all patterns into memory at once
            scored_patterns = heapq.nlargest(
                limit,
                self._filter_and_score_patterns(query, pattern_type, classification),
                key=lambda x: x[0],
            )

            # Return patterns without scores
            return [pattern for _, pattern in scored_patterns]

        except Exception as e:
            logger.error("pattern_search_failed", error=str(e))
            return []

    def _get_storage_dir(self) -> Path | None:
        """Get the storage directory from long-term memory backend.

        Returns:
            Path to storage directory, or None if unavailable.
        """
        if not self._long_term:
            return None

        # Try different ways to access storage directory
        if hasattr(self._long_term, "storage_dir"):
            return Path(self._long_term.storage_dir)
        elif hasattr(self._long_term, "storage"):
            if hasattr(self._long_term.storage, "storage_dir"):
                return Path(self._long_term.storage.storage_dir)
        elif hasattr(self._long_term, "_storage"):
            if hasattr(self._long_term._storage, "storage_dir"):
                return Path(self._long_term._storage.storage_dir)

        return None

    def _iter_all_patterns(self) -> Iterator[dict[str, Any]]:
        """Iterate over all patterns from long-term memory storage.

        Memory-efficient generator that yields patterns one at a time,
        avoiding loading all patterns into memory simultaneously.

        Yields:
            Pattern data dictionaries

        Note:
            This is O(1) memory vs O(n) for _get_all_patterns().
            Use this for large datasets or when streaming is acceptable.
        """
        storage_dir = self._get_storage_dir()
        if not storage_dir:
            logger.warning("cannot_access_storage_directory")
            return

        if not storage_dir.exists():
            return

        # Yield patterns one at a time (memory-efficient)
        for pattern_file in storage_dir.rglob("*.json"):
            try:
                with pattern_file.open("r", encoding="utf-8") as f:
                    yield json.load(f)
            except json.JSONDecodeError as e:
                logger.debug("pattern_json_decode_failed", file=str(pattern_file), error=str(e))
                continue
            except Exception as e:
                logger.debug("pattern_load_failed", file=str(pattern_file), error=str(e))
                continue

    def _get_all_patterns(self) -> list[dict[str, Any]]:
        """Get all patterns from long-term memory storage.

        Scans the storage directory for pattern files and loads them.
        This is a helper method for search_patterns().

        In production with large datasets, this should be replaced with:
        - Database queries with indexes
        - Full-text search engine (Elasticsearch, etc.)
        - Vector embeddings for semantic search

        Returns:
            List of all stored patterns

        Note:
            This performs a full scan and is O(n) memory. For large datasets,
            use _iter_all_patterns() generator instead.
        """
        try:
            patterns = list(self._iter_all_patterns())
            logger.debug("patterns_loaded", count=len(patterns))
            return patterns
        except Exception as e:
            logger.error("get_all_patterns_failed", error=str(e))
            return []

    # =========================================================================
    # PATTERN PROMOTION (SHORT-TERM → LONG-TERM)
    # =========================================================================

    def promote_pattern(
        self,
        staged_pattern_id: str,
        classification: Classification | str | None = None,
        auto_classify: bool = True,
    ) -> dict[str, Any] | None:
        """Promote a staged pattern from short-term to long-term memory.

        Args:
            staged_pattern_id: ID of staged pattern to promote
            classification: Override classification (or auto-detect)
            auto_classify: Auto-detect classification from content

        Returns:
            Long-term storage result, or None if failed

        """
        if not self._short_term or not self._long_term:
            logger.error("memory_backends_unavailable")
            return None

        # Retrieve staged pattern
        staged_patterns = self.get_staged_patterns()
        staged = next(
            (p for p in staged_patterns if p.get("pattern_id") == staged_pattern_id),
            None,
        )

        if not staged:
            logger.warning("staged_pattern_not_found", pattern_id=staged_pattern_id)
            return None

        # Persist to long-term storage
        # Content is stored in context dict by stage_pattern
        context = staged.get("context", {})
        content = context.get("content", "") or staged.get("description", "")
        result = self.persist_pattern(
            content=content,
            pattern_type=staged.get("pattern_type", "general"),
            classification=classification,
            auto_classify=auto_classify,
            metadata=context,
        )

        if result:
            # Remove from staging (use promote_pattern which handles deletion)
            try:
                self._short_term.promote_pattern(staged_pattern_id, self.credentials)
            except PermissionError:
                # If we can't promote (delete from staging), just log it
                logger.warning("could_not_remove_from_staging", pattern_id=staged_pattern_id)
            logger.info(
                "pattern_promoted",
                staged_id=staged_pattern_id,
                long_term_id=result.get("pattern_id"),
            )

        return result

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    @property
    def has_short_term(self) -> bool:
        """Check if short-term memory is available."""
        return self._short_term is not None

    @property
    def has_long_term(self) -> bool:
        """Check if long-term memory is available."""
        return self._long_term is not None

    @property
    def redis_status(self) -> RedisStatus | None:
        """Get Redis connection status."""
        return self._redis_status

    @property
    def using_real_redis(self) -> bool:
        """Check if using real Redis (not mock)."""
        return (
            self._redis_status is not None
            and self._redis_status.available
            and self._redis_status.method != RedisStartMethod.MOCK
        )

    @property
    def short_term(self) -> RedisShortTermMemory:
        """Get short-term memory backend for direct access (testing).

        Returns:
            RedisShortTermMemory instance

        Raises:
            RuntimeError: If short-term memory is not initialized

        """
        if self._short_term is None:
            raise RuntimeError("Short-term memory not initialized")
        return self._short_term

    @property
    def long_term(self) -> LongTermMemory:
        """Get simple long-term memory backend for direct access (testing).

        Returns:
            LongTermMemory instance

        Raises:
            RuntimeError: If long-term memory is not initialized

        Note:
            For production use with security features (PII scrubbing, encryption),
            use persist_pattern() and recall_pattern() methods instead.

        """
        if self._simple_long_term is None:
            raise RuntimeError("Long-term memory not initialized")
        return self._simple_long_term

    def health_check(self) -> dict[str, Any]:
        """Check health of memory backends.

        Returns:
            Status of each memory backend

        """
        redis_info: dict[str, Any] = {
            "available": self.has_short_term,
            "mock_mode": not self.using_real_redis,
        }
        if self._redis_status:
            redis_info["method"] = self._redis_status.method.value
            redis_info["host"] = self._redis_status.host
            redis_info["port"] = self._redis_status.port

        return {
            "file_session": {
                "available": self._file_session is not None,
                "session_id": self._file_session._state.session_id if self._file_session else None,
                "base_dir": self.config.file_session_dir,
            },
            "short_term": redis_info,
            "long_term": {
                "available": self.has_long_term,
                "storage_dir": self.config.storage_dir,
                "encryption": self.config.encryption_enabled,
            },
            "environment": self.config.environment.value,
        }

    # =========================================================================
    # CAPABILITY DETECTION (File-First Architecture)
    # =========================================================================

    @property
    def has_file_session(self) -> bool:
        """Check if file-based session memory is available (always True if enabled)."""
        return self._file_session is not None

    @property
    def file_session(self) -> FileSessionMemory:
        """Get file session memory backend for direct access.

        Returns:
            FileSessionMemory instance

        Raises:
            RuntimeError: If file session memory is not initialized
        """
        if self._file_session is None:
            raise RuntimeError("File session memory not initialized")
        return self._file_session

    def supports_realtime(self) -> bool:
        """Check if real-time features are available (requires Redis).

        Real-time features include:
        - Pub/Sub messaging between agents
        - Cross-session coordination
        - Distributed task queues

        Returns:
            True if Redis is available and connected
        """
        return self.using_real_redis

    def supports_distributed(self) -> bool:
        """Check if distributed features are available (requires Redis).

        Distributed features include:
        - Multi-process coordination
        - Cross-session state sharing
        - Agent discovery

        Returns:
            True if Redis is available and connected
        """
        return self.using_real_redis

    def supports_persistence(self) -> bool:
        """Check if persistence is available (always True with file-first).

        Returns:
            True if file session or long-term memory is available
        """
        return self._file_session is not None or self._long_term is not None

    def get_capabilities(self) -> dict[str, bool]:
        """Get a summary of available memory capabilities.

        Returns:
            Dictionary mapping capability names to availability
        """
        return {
            "file_session": self.has_file_session,
            "redis": self.using_real_redis,
            "long_term": self.has_long_term,
            "persistence": self.supports_persistence(),
            "realtime": self.supports_realtime(),
            "distributed": self.supports_distributed(),
            "encryption": self.config.encryption_enabled and self.has_long_term,
        }

    # =========================================================================
    # COMPACT STATE GENERATION
    # =========================================================================

    def generate_compact_state(self) -> str:
        """Generate SBAR-format compact state from current session.

        Creates a human-readable summary of the current session state,
        suitable for Claude Code's .claude/compact-state.md file.

        Returns:
            Markdown-formatted compact state string
        """
        from datetime import datetime

        lines = [
            "# Compact State - Session Handoff",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ]

        # Add session info
        if self._file_session:
            session = self._file_session._state
            lines.extend(
                [
                    f"**Session ID:** {session.session_id}",
                    f"**User ID:** {session.user_id}",
                    "",
                ]
            )

        lines.extend(
            [
                "## SBAR Handoff",
                "",
                "### Situation",
            ]
        )

        # Get context from file session
        context = {}
        if self._file_session:
            context = self._file_session.get_all_context()

        situation = context.get("situation", "Session in progress.")
        background = context.get("background", "No background information recorded.")
        assessment = context.get("assessment", "No assessment recorded.")
        recommendation = context.get("recommendation", "Continue with current task.")

        lines.extend(
            [
                situation,
                "",
                "### Background",
                background,
                "",
                "### Assessment",
                assessment,
                "",
                "### Recommendation",
                recommendation,
                "",
            ]
        )

        # Add working memory summary
        if self._file_session:
            working_keys = list(self._file_session._state.working_memory.keys())
            if working_keys:
                lines.extend(
                    [
                        "## Working Memory",
                        "",
                        f"**Active keys:** {len(working_keys)}",
                        "",
                    ]
                )
                for key in working_keys[:10]:  # Show max 10
                    lines.append(f"- `{key}`")
                if len(working_keys) > 10:
                    lines.append(f"- ... and {len(working_keys) - 10} more")
                lines.append("")

        # Add staged patterns summary
        if self._file_session:
            staged = list(self._file_session._state.staged_patterns.values())
            if staged:
                lines.extend(
                    [
                        "## Staged Patterns",
                        "",
                        f"**Pending validation:** {len(staged)}",
                        "",
                    ]
                )
                for pattern in staged[:5]:  # Show max 5
                    lines.append(
                        f"- {pattern.name} ({pattern.pattern_type}, conf: {pattern.confidence:.2f})"
                    )
                if len(staged) > 5:
                    lines.append(f"- ... and {len(staged) - 5} more")
                lines.append("")

        # Add capabilities
        caps = self.get_capabilities()
        lines.extend(
            [
                "## Capabilities",
                "",
                f"- File session: {'Yes' if caps['file_session'] else 'No'}",
                f"- Redis: {'Yes' if caps['redis'] else 'No'}",
                f"- Long-term memory: {'Yes' if caps['long_term'] else 'No'}",
                f"- Real-time sync: {'Yes' if caps['realtime'] else 'No'}",
                "",
            ]
        )

        return "\n".join(lines)

    def export_to_claude_md(self, path: str | None = None) -> Path:
        """Export current session state to Claude Code's compact-state.md.

        Args:
            path: Path to write to (defaults to config.compact_state_path)

        Returns:
            Path where state was written
        """
        from empathy_os.config import _validate_file_path

        path = path or self.config.compact_state_path
        validated_path = _validate_file_path(path)

        # Ensure parent directory exists
        validated_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate and write compact state
        content = self.generate_compact_state()
        validated_path.write_text(content, encoding="utf-8")

        logger.info("compact_state_exported", path=str(validated_path))
        return validated_path

    def set_handoff(
        self,
        situation: str,
        background: str,
        assessment: str,
        recommendation: str,
        **extra_context,
    ) -> None:
        """Set SBAR handoff context for session continuity.

        This data is used by generate_compact_state() and export_to_claude_md().

        Args:
            situation: Current situation summary
            background: Relevant background information
            assessment: Assessment of progress/state
            recommendation: Recommended next steps
            **extra_context: Additional context key-value pairs
        """
        if not self._file_session:
            logger.warning("file_session_not_available")
            return

        self._file_session.set_context("situation", situation)
        self._file_session.set_context("background", background)
        self._file_session.set_context("assessment", assessment)
        self._file_session.set_context("recommendation", recommendation)

        for key, value in extra_context.items():
            self._file_session.set_context(key, value)

        # Auto-export if configured
        if self.config.auto_generate_compact_state:
            self.export_to_claude_md()

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def save(self) -> None:
        """Explicitly save all memory state."""
        if self._file_session:
            self._file_session.save()
        logger.debug("memory_saved")

    def close(self) -> None:
        """Close all memory backends and save state."""
        if self._file_session:
            self._file_session.close()

        if self._short_term and hasattr(self._short_term, "close"):
            self._short_term.close()

        logger.info("unified_memory_closed")

    def __enter__(self) -> "UnifiedMemory":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
