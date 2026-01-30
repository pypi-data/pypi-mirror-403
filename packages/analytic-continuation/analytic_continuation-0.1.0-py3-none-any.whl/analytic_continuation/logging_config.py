"""
Logging configuration for the analytic continuation pipeline.

Provides structured logging with optional SQLite persistence for recovery
and debugging long-running computations.
"""

import logging
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
import threading


class TaskStatus(str, Enum):
    """Status of a pipeline task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskProgress:
    """Progress information for a single task."""

    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class PipelineSession:
    """Represents a complete pipeline execution session."""

    session_id: str
    created_at: str
    expression: Optional[str] = None
    curve_data: Optional[Dict[str, Any]] = None
    zeros: List[Dict[str, float]] = field(default_factory=list)
    poles: List[Dict[str, float]] = field(default_factory=list)
    tasks: List[TaskProgress] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "expression": self.expression,
            "curve_data": self.curve_data,
            "zeros": self.zeros,
            "poles": self.poles,
            "tasks": [t.to_dict() for t in self.tasks],
            "result": self.result,
            "status": self.status.value,
        }


class PipelineLogger:
    """
    Logger for the analytic continuation pipeline.

    Provides:
    - Structured logging to console/file
    - SQLite persistence for session recovery
    - Progress tracking for UI updates
    """

    _instance: Optional["PipelineLogger"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        db_path: Optional[str] = None,
        log_level: int = logging.INFO,
        log_file: Optional[str] = None,
    ):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self.db_path = db_path or os.environ.get(
            "PIPELINE_DB_PATH", str(Path.home() / ".analytic_continuation" / "pipeline.db")
        )
        self.log_file = log_file

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Set up Python logger
        self.logger = logging.getLogger("analytic_continuation")
        self.logger.setLevel(log_level)

        # Console handler with colored output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

        # Initialize SQLite database
        self._init_db()

        # Current session tracking
        self._current_session: Optional[PipelineSession] = None
        self._progress_callbacks: List[callable] = []

    def _init_db(self):
        """Initialize SQLite database schema with migration support."""
        with self._get_db() as conn:
            # Create tables if they don't exist
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    expression TEXT,
                    curve_data TEXT,
                    zeros TEXT,
                    poles TEXT,
                    result TEXT,
                    status TEXT NOT NULL DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    error TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_task_logs_session 
                ON task_logs(session_id);
                
                CREATE TABLE IF NOT EXISTS computation_cache (
                    cache_key TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_cache_session
                ON computation_cache(session_id);
            """)

            # Run migrations for new columns
            self._migrate_db(conn)

    def _migrate_db(self, conn):
        """Run database migrations for schema updates."""
        # Check existing columns in sessions table
        cursor = conn.execute("PRAGMA table_info(sessions)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Add new columns if they don't exist
        migrations = [
            ("updated_at", "TEXT"),
            ("input_hash", "TEXT"),
            ("last_completed_stage", "TEXT"),
        ]

        for col_name, col_type in migrations:
            if col_name not in existing_columns:
                try:
                    conn.execute(f"ALTER TABLE sessions ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass  # Column might already exist

        # Create index on input_hash if it doesn't exist
        try:
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_input_hash
                ON sessions(input_hash)
            """)
        except sqlite3.OperationalError:
            pass

    @contextmanager
    def _get_db(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def register_progress_callback(self, callback: callable):
        """Register a callback for progress updates."""
        self._progress_callbacks.append(callback)

    def unregister_progress_callback(self, callback: callable):
        """Unregister a progress callback."""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    def _notify_progress(self, task: TaskProgress):
        """Notify all registered callbacks of progress update."""
        for callback in self._progress_callbacks:
            try:
                callback(task)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")

    @staticmethod
    def compute_input_hash(
        expression: Optional[str] = None,
        curve_data: Optional[Dict[str, Any]] = None,
        zeros: Optional[List[Dict[str, float]]] = None,
        poles: Optional[List[Dict[str, float]]] = None,
    ) -> str:
        """
        Compute a hash of the input parameters for session matching.

        This allows finding previous sessions with identical inputs
        for potential resumption.
        """
        import hashlib

        # Normalize and serialize inputs
        normalized = {
            "expression": expression or "",
            "curve_points": len(curve_data.get("controlPoints", [])) if curve_data else 0,
            "curve_closed": curve_data.get("closed", False) if curve_data else False,
            "zeros": sorted([(z.get("x", 0), z.get("y", 0)) for z in (zeros or [])]),
            "poles": sorted([(p.get("x", 0), p.get("y", 0)) for p in (poles or [])]),
        }

        # If we have curve data, include a hash of control points
        if curve_data and "controlPoints" in curve_data:
            pts = curve_data["controlPoints"]
            # Round to avoid floating point precision issues
            pt_tuples = [(round(p.get("x", 0), 6), round(p.get("y", 0), 6)) for p in pts]
            normalized["curve_hash"] = hash(tuple(pt_tuples))

        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def find_resumable_session(
        self,
        expression: Optional[str] = None,
        curve_data: Optional[Dict[str, Any]] = None,
        zeros: Optional[List[Dict[str, float]]] = None,
        poles: Optional[List[Dict[str, float]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a previous session with matching inputs that can be resumed.

        Returns session info including what stages were completed,
        or None if no matching session exists.
        """
        input_hash = self.compute_input_hash(expression, curve_data, zeros, poles)

        with self._get_db() as conn:
            # Find sessions with matching hash that have some progress
            row = conn.execute(
                """SELECT session_id, created_at, status, last_completed_stage, result
                   FROM sessions 
                   WHERE input_hash = ?
                   ORDER BY created_at DESC
                   LIMIT 1""",
                (input_hash,),
            ).fetchone()

            if not row:
                return None

            session_id = row["session_id"]

            # Get cached computations
            caches = conn.execute(
                "SELECT cache_key, stage FROM computation_cache WHERE session_id = ?", (session_id,)
            ).fetchall()

            return {
                "session_id": session_id,
                "created_at": row["created_at"],
                "status": row["status"],
                "last_completed_stage": row["last_completed_stage"],
                "has_result": row["result"] is not None,
                "cached_stages": [c["stage"] for c in caches],
                "input_hash": input_hash,
            }

    def start_session(
        self,
        expression: Optional[str] = None,
        curve_data: Optional[Dict[str, Any]] = None,
        zeros: Optional[List[Dict[str, float]]] = None,
        poles: Optional[List[Dict[str, float]]] = None,
    ) -> str:
        """Start a new pipeline session."""
        import uuid

        session_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        input_hash = self.compute_input_hash(expression, curve_data, zeros, poles)

        self._current_session = PipelineSession(
            session_id=session_id,
            created_at=now,
            expression=expression,
            curve_data=curve_data,
            zeros=zeros or [],
            poles=poles or [],
            tasks=[],
            status=TaskStatus.IN_PROGRESS,
        )

        # Persist to database
        with self._get_db() as conn:
            conn.execute(
                """INSERT INTO sessions 
                   (session_id, created_at, updated_at, expression, curve_data, zeros, poles, status, input_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    now,
                    now,
                    expression,
                    json.dumps(curve_data) if curve_data else None,
                    json.dumps(zeros or []),
                    json.dumps(poles or []),
                    TaskStatus.IN_PROGRESS.value,
                    input_hash,
                ),
            )

        self.logger.info(f"Started session {session_id} (hash: {input_hash})")
        return session_id

    def update_session_stage(self, stage: str, session_id: Optional[str] = None):
        """Update the last completed stage for a session."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if not sid:
            return

        now = datetime.utcnow().isoformat()
        with self._get_db() as conn:
            conn.execute(
                "UPDATE sessions SET last_completed_stage = ?, updated_at = ? WHERE session_id = ?",
                (stage, now, sid),
            )

    def get_session(self, session_id: str) -> Optional[PipelineSession]:
        """Retrieve a session by ID."""
        with self._get_db() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

            if not row:
                return None

            # Get tasks
            tasks_rows = conn.execute(
                "SELECT * FROM task_logs WHERE session_id = ? ORDER BY id", (session_id,)
            ).fetchall()

            tasks = [
                TaskProgress(
                    task_id=t["task_id"],
                    name=t["name"],
                    status=TaskStatus(t["status"]),
                    progress=t["progress"],
                    message=t["message"] or "",
                    started_at=t["started_at"],
                    completed_at=t["completed_at"],
                    error=t["error"],
                    metadata=json.loads(t["metadata"]) if t["metadata"] else {},
                )
                for t in tasks_rows
            ]

            return PipelineSession(
                session_id=row["session_id"],
                created_at=row["created_at"],
                expression=row["expression"],
                curve_data=json.loads(row["curve_data"]) if row["curve_data"] else None,
                zeros=json.loads(row["zeros"]) if row["zeros"] else [],
                poles=json.loads(row["poles"]) if row["poles"] else [],
                tasks=tasks,
                result=json.loads(row["result"]) if row["result"] else None,
                status=TaskStatus(row["status"]),
            )

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent sessions."""
        with self._get_db() as conn:
            rows = conn.execute(
                """SELECT session_id, created_at, expression, status 
                   FROM sessions ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def start_task(
        self,
        task_id: str,
        name: str,
        session_id: Optional[str] = None,
    ) -> TaskProgress:
        """Start tracking a new task."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if not sid:
            raise ValueError("No active session")

        now = datetime.utcnow().isoformat()
        task = TaskProgress(
            task_id=task_id,
            name=name,
            status=TaskStatus.IN_PROGRESS,
            started_at=now,
        )

        if self._current_session:
            self._current_session.tasks.append(task)

        # Persist
        with self._get_db() as conn:
            conn.execute(
                """INSERT INTO task_logs 
                   (session_id, task_id, name, status, started_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (sid, task_id, name, TaskStatus.IN_PROGRESS.value, now),
            )

        self.logger.info(f"[{sid}] Started task: {name}")
        self._notify_progress(task)
        return task

    def update_task(
        self,
        task_id: str,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ):
        """Update task progress."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if not sid:
            return

        # Find task in current session
        task = None
        if self._current_session:
            for t in self._current_session.tasks:
                if t.task_id == task_id:
                    task = t
                    break

        if task:
            if progress is not None:
                task.progress = progress
            if message is not None:
                task.message = message
            if metadata is not None:
                task.metadata.update(metadata)

        # Update database
        updates = []
        params = []
        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)
        if message is not None:
            updates.append("message = ?")
            params.append(message)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))

        if updates:
            params.extend([sid, task_id])
            with self._get_db() as conn:
                conn.execute(
                    f"""UPDATE task_logs SET {", ".join(updates)}
                       WHERE session_id = ? AND task_id = ?""",
                    params,
                )

        if task:
            self._notify_progress(task)
            if message:
                self.logger.debug(f"[{sid}] {task_id}: {message}")

    def complete_task(
        self,
        task_id: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ):
        """Mark a task as completed or failed."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if not sid:
            return

        now = datetime.utcnow().isoformat()
        status = TaskStatus.COMPLETED if success else TaskStatus.FAILED

        # Update in-memory
        task = None
        if self._current_session:
            for t in self._current_session.tasks:
                if t.task_id == task_id:
                    t.status = status
                    t.progress = 1.0 if success else t.progress
                    t.completed_at = now
                    t.error = error
                    if metadata:
                        t.metadata.update(metadata)
                    task = t
                    break

        # Persist
        with self._get_db() as conn:
            conn.execute(
                """UPDATE task_logs 
                   SET status = ?, progress = ?, completed_at = ?, error = ?, metadata = ?
                   WHERE session_id = ? AND task_id = ?""",
                (
                    status.value,
                    1.0 if success else (task.progress if task else 0.0),
                    now,
                    error,
                    json.dumps(metadata) if metadata else None,
                    sid,
                    task_id,
                ),
            )

        if success:
            self.logger.info(f"[{sid}] Completed task: {task_id}")
        else:
            self.logger.error(f"[{sid}] Failed task: {task_id} - {error}")

        if task:
            self._notify_progress(task)

    def cache_computation(
        self,
        cache_key: str,
        stage: str,
        data: Dict[str, Any],
        session_id: Optional[str] = None,
    ):
        """Cache intermediate computation results for recovery."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if not sid:
            return

        now = datetime.utcnow().isoformat()
        with self._get_db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO computation_cache
                   (cache_key, session_id, stage, data, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (cache_key, sid, stage, json.dumps(data), now),
            )

        self.logger.debug(f"[{sid}] Cached {stage} computation: {cache_key}")

    def get_cached_computation(
        self,
        cache_key: str,
        session_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached computation."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if not sid:
            return None

        with self._get_db() as conn:
            row = conn.execute(
                "SELECT data FROM computation_cache WHERE cache_key = ? AND session_id = ?",
                (cache_key, sid),
            ).fetchone()

            if row:
                return json.loads(row["data"])
        return None

    def end_session(
        self,
        success: bool = True,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """End the current session."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if not sid:
            return

        status = TaskStatus.COMPLETED if success else TaskStatus.FAILED

        if self._current_session:
            self._current_session.status = status
            self._current_session.result = result

        with self._get_db() as conn:
            conn.execute(
                "UPDATE sessions SET status = ?, result = ? WHERE session_id = ?",
                (status.value, json.dumps(result) if result else None, sid),
            )

        if success:
            self.logger.info(f"Session {sid} completed successfully")
        else:
            self.logger.error(f"Session {sid} failed: {error}")

        if self._current_session and self._current_session.session_id == sid:
            self._current_session = None

    def get_current_progress(self) -> Optional[Dict[str, Any]]:
        """Get current session progress for UI display."""
        if not self._current_session:
            return None
        return self._current_session.to_dict()

    # Convenience logging methods
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)


# Global logger instance
def get_logger() -> PipelineLogger:
    """Get the global pipeline logger instance."""
    return PipelineLogger()
