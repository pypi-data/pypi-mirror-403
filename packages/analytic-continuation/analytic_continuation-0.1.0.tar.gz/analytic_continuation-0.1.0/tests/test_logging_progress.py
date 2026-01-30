"""Tests for logging and progress tracking functionality."""

import pytest
import os
import tempfile
from pathlib import Path

from analytic_continuation.logging_config import (
    PipelineLogger,
    TaskStatus,
    TaskProgress,
    PipelineSession,
)
from analytic_continuation.progress import (
    ProgressTracker,
    StageInfo,
    PIPELINE_STAGES,
    format_cli_progress,
)


class TestPipelineLogger:
    """Test the PipelineLogger class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_pipeline.db")
            # Reset singleton for testing
            PipelineLogger._instance = None
            yield db_path

    def test_start_session(self, temp_db):
        """Test starting a new session."""
        logger = PipelineLogger(db_path=temp_db)
        session_id = logger.start_session(
            expression="z^2",
            zeros=[{"x": 0, "y": 0}],
            poles=[{"x": 1, "y": 0}],
        )

        assert session_id is not None
        assert len(session_id) == 8

    def test_get_session(self, temp_db):
        """Test retrieving a session."""
        logger = PipelineLogger(db_path=temp_db)
        session_id = logger.start_session(expression="sin(z)/z")

        session = logger.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id
        assert session.expression == "sin(z)/z"
        assert session.status == TaskStatus.IN_PROGRESS

    def test_task_lifecycle(self, temp_db):
        """Test starting, updating, and completing a task."""
        logger = PipelineLogger(db_path=temp_db)
        session_id = logger.start_session()

        # Start task
        task = logger.start_task("fit_laurent", "Fit Laurent Map", session_id)
        assert task.status == TaskStatus.IN_PROGRESS

        # Update task
        logger.update_task("fit_laurent", progress=0.5, message="Fitting N=12")

        # Complete task
        logger.complete_task("fit_laurent", success=True, metadata={"N": 12})

        # Verify
        session = logger.get_session(session_id)
        assert len(session.tasks) == 1
        assert session.tasks[0].status == TaskStatus.COMPLETED

    def test_cache_computation(self, temp_db):
        """Test caching and retrieving computation data."""
        logger = PipelineLogger(db_path=temp_db)
        session_id = logger.start_session()

        # Cache some data
        data = {"N": 12, "coeffs": [1.0, 2.0, 3.0]}
        logger.cache_computation("laurent_map", "fit", data, session_id)

        # Retrieve
        cached = logger.get_cached_computation("laurent_map", session_id)
        assert cached == data

    def test_list_sessions(self, temp_db):
        """Test listing sessions."""
        logger = PipelineLogger(db_path=temp_db)

        # Create multiple sessions
        logger.start_session(expression="z^2")
        logger.start_session(expression="z^3")
        logger.start_session(expression="sin(z)")

        sessions = logger.list_sessions(limit=10)
        assert len(sessions) == 3

    def test_end_session(self, temp_db):
        """Test ending a session."""
        logger = PipelineLogger(db_path=temp_db)
        session_id = logger.start_session()

        logger.end_session(
            session_id=session_id,
            success=True,
            result={"ok": True},
        )

        session = logger.get_session(session_id)
        assert session.status == TaskStatus.COMPLETED
        assert session.result == {"ok": True}


class TestProgressTracker:
    """Test the ProgressTracker class."""

    def test_initial_state(self):
        """Test initial progress state."""
        tracker = ProgressTracker()
        state = tracker.get_state()

        assert state["overall_progress"] == 0.0
        assert len(state["stages"]) == len(PIPELINE_STAGES)

        for stage in state["stages"]:
            assert stage["status"] == "pending"
            assert stage["progress"] == 0.0

    def test_sync_stage_lifecycle(self):
        """Test synchronous stage operations."""
        tracker = ProgressTracker()

        # Start stage
        tracker.sync_start_stage("validate_input", message="Validating")
        state = tracker.get_state()

        assert state["current_stage"] == "validate_input"
        validate_stage = next(s for s in state["stages"] if s["id"] == "validate_input")
        assert validate_stage["status"] == "in_progress"

        # Update stage
        tracker.sync_update_stage("validate_input", progress=0.5, message="Half done")

        # Complete stage
        tracker.sync_complete_stage("validate_input", success=True)

        state = tracker.get_state()
        validate_stage = next(s for s in state["stages"] if s["id"] == "validate_input")
        assert validate_stage["status"] == "completed"
        assert validate_stage["progress"] == 1.0

    def test_overall_progress(self):
        """Test overall progress calculation."""
        tracker = ProgressTracker()
        num_stages = len(PIPELINE_STAGES)

        # Complete first stage
        tracker.sync_start_stage("validate_input")
        tracker.sync_complete_stage("validate_input")

        state = tracker.get_state()
        expected = 1.0 / num_stages
        assert abs(state["overall_progress"] - expected) < 0.01

    def test_failed_stage(self):
        """Test failing a stage."""
        tracker = ProgressTracker()

        tracker.sync_start_stage("fit_laurent")
        tracker.sync_complete_stage("fit_laurent", success=False, error="Curve too short")

        state = tracker.get_state()
        fit_stage = next(s for s in state["stages"] if s["id"] == "fit_laurent")
        assert fit_stage["status"] == "failed"
        assert fit_stage["error"] == "Curve too short"


class TestCliProgress:
    """Test CLI progress formatting."""

    def test_format_cli_progress(self):
        """Test CLI progress output format."""
        tracker = ProgressTracker()

        # Complete some stages
        tracker.sync_start_stage("validate_input")
        tracker.sync_complete_stage("validate_input")
        tracker.sync_start_stage("load_curve")
        tracker.sync_complete_stage("load_curve")
        tracker.sync_start_stage("fit_laurent", message="Fitting N=24...")
        tracker.sync_update_stage("fit_laurent", progress=0.67)

        output = format_cli_progress(tracker)

        # Should contain box drawing characters
        assert "┌" in output
        assert "└" in output

        # Should show completed items with checkmark
        assert "✓" in output

        # Should show progress bar
        assert "█" in output
        assert "░" in output

        # Should show current message
        assert "Fitting N=24" in output

    def test_format_with_error(self):
        """Test CLI progress with failed stage."""
        tracker = ProgressTracker()

        tracker.sync_start_stage("validate_input")
        tracker.sync_complete_stage("validate_input", success=False, error="Invalid curve")

        output = format_cli_progress(tracker)

        # Should show error icon
        assert "✗" in output

        # Should show error message
        assert "Invalid curve" in output


class TestTaskProgress:
    """Test TaskProgress dataclass."""

    def test_to_dict(self):
        """Test TaskProgress serialization."""
        task = TaskProgress(
            task_id="test",
            name="Test Task",
            status=TaskStatus.IN_PROGRESS,
            progress=0.5,
            message="Working...",
        )

        d = task.to_dict()
        assert d["task_id"] == "test"
        assert d["status"] == "in_progress"
        assert d["progress"] == 0.5


class TestStageInfo:
    """Test StageInfo dataclass."""

    def test_to_dict(self):
        """Test StageInfo serialization."""
        stage = StageInfo(
            id="fit_laurent",
            name="Fit Laurent Map",
            description="Fitting Laurent series",
            status=TaskStatus.COMPLETED,
            progress=1.0,
            substeps_total=10,
            substeps_done=10,
        )

        d = stage.to_dict()
        assert d["id"] == "fit_laurent"
        assert d["status"] == "completed"
        assert d["substeps_total"] == 10
