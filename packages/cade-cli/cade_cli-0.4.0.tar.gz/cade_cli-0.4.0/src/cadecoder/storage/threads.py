"""Thread storage system for CadeCoder.

This module provides persistent storage for chat threads and messages.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from ulid import ulid

from cadecoder.core.config import get_config
from cadecoder.core.errors import StorageError
from cadecoder.core.logging import log
from cadecoder.core.names import generate_unique_thread_name

# --- Message Models ---


class ToolCallInfo(BaseModel):
    """Tool call information."""

    call_id: str
    tool_name: str
    tool_type: str = "function"
    parameters: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int | None = None
    status: str | None = None
    error_message: str | None = None

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Custom dump that converts datetime to ISO format."""
        data = super().model_dump(**kwargs)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


class ModelInfo(BaseModel):
    """Model information for a message."""

    provider: str
    model_name: str
    model_version: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class Message(BaseModel):
    """Message model."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: str = Field(alias="id")
    thread_id: str
    role: str
    content: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)
    responding_tool_call_id: str | None = None
    model_info: ModelInfo | None = None
    parent_message_id: str | None = None
    conversation_turn: int | None = None

    def model_dump_db(self) -> dict[str, Any]:
        """Prepare model for DB storage."""
        dump = self.model_dump(by_alias=True)
        dump["timestamp"] = dump["timestamp"].isoformat()
        dump["tool_calls_json"] = json.dumps([tc.model_dump() for tc in self.tool_calls])
        dump.pop("tool_calls", None)

        if self.model_info:
            dump["model_info_json"] = json.dumps(self.model_info.model_dump())
        else:
            dump["model_info_json"] = None
        dump.pop("model_info", None)

        dump["conversation_id"] = dump.pop("thread_id")
        dump["tool_call_id"] = self.responding_tool_call_id
        dump.pop("responding_tool_call_id", None)

        return dump

    @classmethod
    def model_validate_db(cls, data: dict[str, Any]) -> "Message":
        """Validate data coming from DB."""
        db_data = data.copy()
        db_data["thread_id"] = db_data.pop("conversation_id")
        db_data["responding_tool_call_id"] = db_data.pop("tool_call_id", None)

        tool_calls_json = db_data.pop("tool_calls_json", None)
        if tool_calls_json:
            tool_calls_data = json.loads(tool_calls_json)
            db_data["tool_calls"] = [ToolCallInfo.model_validate(tc) for tc in tool_calls_data]
        else:
            db_data["tool_calls"] = []

        model_info_json = db_data.pop("model_info_json", None)
        if model_info_json:
            db_data["model_info"] = ModelInfo.model_validate(json.loads(model_info_json))

        db_data["timestamp"] = datetime.fromisoformat(db_data["timestamp"])

        return cls.model_validate(db_data)


class Thread(BaseModel):
    """Thread model."""

    model_config = ConfigDict(populate_by_name=True)

    thread_id: str = Field(alias="id")
    name: str | None = None
    git_branch: str | None = None
    model: str = Field(default="unknown")
    user_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_modified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_dump_db(self) -> dict[str, Any]:
        dump = self.model_dump(by_alias=True)
        dump["created_at"] = dump["created_at"].isoformat()
        dump["last_modified_at"] = dump["last_modified_at"].isoformat()
        dump["tags_json"] = json.dumps(dump.pop("tags", []))
        dump["metadata_json"] = json.dumps(dump.pop("metadata", {}))
        return dump

    @classmethod
    def model_validate_db(cls, data: dict[str, Any]) -> "Thread":
        db_data = data.copy()
        db_data["created_at"] = datetime.fromisoformat(db_data["created_at"])
        db_data["last_modified_at"] = datetime.fromisoformat(db_data["last_modified_at"])

        tags_json = db_data.pop("tags_json", None)
        if tags_json:
            db_data["tags"] = json.loads(tags_json)

        metadata_json = db_data.pop("metadata_json", None)
        if metadata_json:
            db_data["metadata"] = json.loads(metadata_json)

        if "model" not in db_data:
            db_data["model"] = "unknown"
        if "user_id" not in db_data:
            db_data["user_id"] = None

        return cls.model_validate(db_data)


# --- Storage Interfaces ---

T = TypeVar("T")


class BaseThreadHistory(ABC):
    """Abstract base class for chat thread history storage."""

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Adds a message to the history."""
        raise NotImplementedError

    @abstractmethod
    def get_messages(self, thread_id: str) -> list[Message]:
        """Retrieves all messages for a given thread."""
        raise NotImplementedError

    @abstractmethod
    def get_thread(self, thread_id: str) -> Thread | None:
        """Retrieves thread metadata."""
        raise NotImplementedError

    @abstractmethod
    def list_threads(self) -> list[Thread]:
        """Lists all stored threads."""
        raise NotImplementedError

    @abstractmethod
    def create_thread(
        self,
        name: str | None = None,
        git_branch: str | None = None,
        model: str = "unknown",
        user_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Thread:
        """Creates a new thread."""
        raise NotImplementedError

    @abstractmethod
    def delete_thread(self, thread_id: str) -> None:
        """Deletes a thread and its messages."""
        raise NotImplementedError

    @abstractmethod
    def update_thread_timestamp(self, thread_id: str) -> None:
        """Updates the last modified timestamp of a thread."""
        raise NotImplementedError


# --- SQLite Implementation ---

DEFAULT_DB_NAME = "cadecoder_history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    name TEXT,
    git_branch TEXT,
    model TEXT DEFAULT 'unknown',
    user_id TEXT,
    created_at TEXT NOT NULL,
    last_modified_at TEXT NOT NULL,
    tags_json TEXT DEFAULT '[]',
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    timestamp TEXT NOT NULL,
    tool_calls_json TEXT DEFAULT '[]',
    tool_call_id TEXT,
    model_info_json TEXT,
    parent_message_id TEXT,
    conversation_turn INTEGER,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_last_modified ON conversations(last_modified_at);
"""


def get_db_path() -> Path:
    """Determines the path for the SQLite database using config."""
    try:
        app_directory = get_config().ensure_app_dir()
        base_path = Path(app_directory)
    except Exception as e:
        log.error(f"Failed to get or ensure app directory from config: {e}")
        raise StorageError(f"Could not determine storage directory: {e}") from e

    return base_path / DEFAULT_DB_NAME


class SqliteThreadHistory(BaseThreadHistory):
    """SQLite-based chat thread history implementation."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else get_db_path()
        self._conn: sqlite3.Connection | None = None
        self._connect()
        self._initialize_db()
        log.info(f"Initialized SQLite thread history at {self.db_path}")

    def _connect(self):
        """Establish SQLite connection."""
        if self._conn is not None:
            return
        try:
            self._conn = sqlite3.connect(
                self.db_path, isolation_level=None, check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
            log.debug(f"Connected to SQLite database: {self.db_path}")
        except sqlite3.Error as e:
            log.error(f"Error connecting to SQLite database: {e}")
            raise StorageError(f"Failed to connect to database: {e}") from e

    def _initialize_db(self):
        """Create database schema."""
        if not self._conn:
            self._connect()

        try:
            self._conn.executescript(SCHEMA)
            log.debug("Database schema initialized.")
        except Exception as e:
            log.error(f"Error initializing database schema: {e}")
            raise StorageError(f"Failed to initialize database schema: {e}") from e

    def _execute(self, query: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        """Executes a SQL query with error handling."""
        if not self._conn:
            raise StorageError("Database connection is not available.")
        try:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            log.error(f"SQLite error: {e}")
            raise StorageError(f"Database error: {e}") from e

    def close(self):
        """Closes the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            log.debug("Closed SQLite database connection.")

    def add_message(self, message: Message) -> None:
        """Adds a message to the database."""
        if not self.get_thread(message.thread_id):
            raise StorageError(f"Cannot add message to non-existent thread: {message.thread_id}")

        if not message.message_id:
            message.message_id = str(ulid()).lower()

        msg_data = message.model_dump_db()
        query = """
            INSERT INTO messages (
                id, conversation_id, role, content, timestamp,
                tool_calls_json, tool_call_id, model_info_json,
                parent_message_id, conversation_turn
            )
            VALUES (
                :id, :conversation_id, :role, :content, :timestamp,
                :tool_calls_json, :tool_call_id, :model_info_json,
                :parent_message_id, :conversation_turn
            )
        """
        try:
            self._execute(query, msg_data)
            self.update_thread_timestamp(message.thread_id)
            log.debug(f"Added message {message.message_id} to thread {message.thread_id}")
        except Exception as e:
            log.error(f"Failed to add message: {e}")
            raise

    def get_messages(self, thread_id: str) -> list[Message]:
        """Retrieves all messages for a thread, ordered by timestamp."""
        query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC"
        cursor = self._execute(query, (thread_id,))
        rows = cursor.fetchall()
        cursor.close()
        return [Message.model_validate_db(dict(row)) for row in rows]

    def get_thread(self, thread_id: str) -> Thread | None:
        """Retrieves thread metadata."""
        query = "SELECT * FROM conversations WHERE id = ?"
        cursor = self._execute(query, (thread_id,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return Thread.model_validate_db(dict(row))
        return None

    def list_threads(self) -> list[Thread]:
        """Lists all threads, ordered by last modified."""
        query = "SELECT * FROM conversations ORDER BY last_modified_at DESC"
        cursor = self._execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return [Thread.model_validate_db(dict(row)) for row in rows]

    def create_thread(
        self,
        name: str | None = None,
        git_branch: str | None = None,
        model: str = "unknown",
        user_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Thread:
        """Creates a new thread record.

        If no name is provided, generates a Docker-style name like 'happy_panda'.
        """
        # Auto-generate name if not provided
        if not name:
            existing_names = {t.name for t in self.list_threads() if t.name}
            name = generate_unique_thread_name(existing_names)

        thread = Thread(
            id=str(ulid()).lower(),
            name=name,
            git_branch=git_branch,
            model=model,
            user_id=user_id,
            tags=tags or [],
            metadata=metadata or {},
        )

        thread_data = thread.model_dump_db()
        query = """
            INSERT INTO conversations (
                id, name, git_branch, model, user_id,
                created_at, last_modified_at, tags_json, metadata_json
            )
            VALUES (
                :id, :name, :git_branch, :model, :user_id,
                :created_at, :last_modified_at, :tags_json, :metadata_json
            )
        """
        try:
            self._execute(query, thread_data)
            log.info(f"Created thread: {thread.thread_id}")
            return thread
        except sqlite3.IntegrityError:
            log.error(f"Failed to create thread: {thread.thread_id}")
            raise StorageError(f"Thread ID collision for {thread.thread_id}")

    def delete_thread(self, thread_id: str) -> None:
        """Deletes a thread and its associated messages."""
        if not self.get_thread(thread_id):
            log.warning(f"Attempted to delete non-existent thread: {thread_id}")
            return

        # Delete messages first
        self._execute("DELETE FROM messages WHERE conversation_id = ?", (thread_id,))
        # Delete thread
        cursor = self._execute("DELETE FROM conversations WHERE id = ?", (thread_id,))
        if cursor.rowcount > 0:
            log.info(f"Deleted thread {thread_id} and its messages.")
        cursor.close()

    def update_thread_timestamp(self, thread_id: str) -> None:
        """Updates the last modified timestamp."""
        now_iso = datetime.now(UTC).isoformat()
        query = "UPDATE conversations SET last_modified_at = ? WHERE id = ?"
        cursor = self._execute(query, (now_iso, thread_id))
        cursor.close()

    def find_thread_by_name_and_branch(self, name: str, git_branch: str) -> Thread | None:
        """Find a thread by name and git branch."""
        query = "SELECT * FROM conversations WHERE name = ? AND git_branch = ?"
        cursor = self._execute(query, (name, git_branch))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return Thread.model_validate_db(dict(row))
        return None

    def find_thread_by_name(self, name: str) -> Thread | None:
        """Find the most recent thread with a given name.

        Args:
            name: Thread name (e.g., 'happy_panda')

        Returns:
            Most recent thread with that name, or None if not found.
        """
        query = "SELECT * FROM conversations WHERE name = ? ORDER BY last_modified_at DESC LIMIT 1"
        cursor = self._execute(query, (name,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return Thread.model_validate_db(dict(row))
        return None

    def update_thread_git_branch(self, thread_id: str, git_branch: str) -> None:
        """Updates the git branch of a thread."""
        query = "UPDATE conversations SET git_branch = ? WHERE id = ?"
        cursor = self._execute(query, (git_branch, thread_id))
        if cursor.rowcount == 0:
            raise StorageError(f"Thread {thread_id} not found.")
        cursor.close()
        self.update_thread_timestamp(thread_id)

    def update_thread_model(self, thread_id: str, model: str) -> None:
        """Updates the AI model of a thread."""
        query = "UPDATE conversations SET model = ? WHERE id = ?"
        cursor = self._execute(query, (model, thread_id))
        if cursor.rowcount == 0:
            raise StorageError(f"Thread {thread_id} not found.")
        cursor.close()
        self.update_thread_timestamp(thread_id)

    def update_thread_user_id(self, thread_id: str, user_id: str) -> None:
        """Updates the user ID of a thread."""
        query = "UPDATE conversations SET user_id = ? WHERE id = ?"
        cursor = self._execute(query, (user_id, thread_id))
        if cursor.rowcount == 0:
            raise StorageError(f"Thread {thread_id} not found.")
        cursor.close()
        self.update_thread_timestamp(thread_id)


# --- Helper / Factory ---

_thread_history_instance: BaseThreadHistory | None = None


@lru_cache(maxsize=1)
def get_thread_history() -> BaseThreadHistory:
    """Gets the chat thread history instance (singleton pattern)."""
    log.debug("Initializing thread history instance...")

    try:
        get_config().ensure_app_dir()
        instance = SqliteThreadHistory()
    except StorageError as e:
        log.error(f"Failed to initialize SQLite history: {e}")
        raise
    except Exception as e:
        log.exception("Unexpected error initializing thread history")
        raise StorageError(f"Failed to initialize thread history: {e}") from e

    return instance
