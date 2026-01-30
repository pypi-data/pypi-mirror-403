"""
Progress tracking for the analytic continuation pipeline.

Provides real-time progress updates via Server-Sent Events (SSE)
and progress state management for UI display.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, AsyncGenerator
import asyncio
import json
from datetime import datetime
from enum import Enum

from .logging_config import TaskStatus, TaskProgress, PipelineLogger, get_logger


# Pipeline stages for the analytic continuation workflow
PIPELINE_STAGES = [
    ("precheck", "Pre-Check Contour", "Quick validation of curve topology"),
    ("validate_input", "Validate Input", "Checking curve and function validity"),
    ("load_curve", "Load Curve", "Loading and preprocessing Jordan curve"),
    ("fit_laurent", "Fit Laurent Map", "Fitting Laurent series to curve"),
    (
        "analyze_complexity",
        "Analyze Complexity",
        "Computing Cesàro/Whewell forms for cost estimation",
    ),
    ("check_holomorphic", "Check Holomorphic", "Verifying function is holomorphic on annulus"),
    ("prepare_render", "Prepare Render", "Extracting coefficients for rendering"),
    ("render", "Render", "Generating domain coloring visualization"),
]


@dataclass
class StageInfo:
    """Information about a pipeline stage."""

    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    message: str = ""
    substeps_total: int = 0
    substeps_done: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "substeps_total": self.substeps_total,
            "substeps_done": self.substeps_done,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class ProgressTracker:
    """
    Tracks progress through the analytic continuation pipeline.

    Provides:
    - Stage-by-stage progress tracking
    - Real-time updates via callbacks or SSE
    - Checklist-style UI output
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.logger = get_logger()
        self.stages: Dict[str, StageInfo] = {}
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

        # Initialize stages
        for stage_id, name, desc in PIPELINE_STAGES:
            self.stages[stage_id] = StageInfo(
                id=stage_id,
                name=name,
                description=desc,
            )

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to progress updates via SSE."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)

        try:
            # Send initial state
            yield self._format_sse_event("init", self.get_state())

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
        finally:
            self._subscribers.remove(queue)

    def _format_sse_event(self, event_type: str, data: Any) -> str:
        """Format data as SSE event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    async def _broadcast(self, event_type: str, data: Any):
        """Broadcast update to all subscribers."""
        event = self._format_sse_event(event_type, data)
        for queue in self._subscribers:
            await queue.put(event)

    def get_state(self) -> Dict[str, Any]:
        """Get current progress state for UI."""
        stages_list = []
        overall_progress = 0.0
        total_weight = len(self.stages)

        for stage_id, _, _ in PIPELINE_STAGES:
            stage = self.stages[stage_id]
            stages_list.append(stage.to_dict())

            if stage.status == TaskStatus.COMPLETED:
                overall_progress += 1.0
            elif stage.status == TaskStatus.IN_PROGRESS:
                overall_progress += stage.progress

        return {
            "session_id": self.session_id,
            "overall_progress": overall_progress / total_weight if total_weight > 0 else 0.0,
            "stages": stages_list,
            "current_stage": self._get_current_stage_id(),
        }

    def _get_current_stage_id(self) -> Optional[str]:
        """Get the ID of the currently running stage."""
        for stage_id, _, _ in PIPELINE_STAGES:
            stage = self.stages[stage_id]
            if stage.status == TaskStatus.IN_PROGRESS:
                return stage_id
        return None

    async def start_stage(
        self,
        stage_id: str,
        substeps_total: int = 0,
        message: str = "",
    ):
        """Start a pipeline stage."""
        if stage_id not in self.stages:
            return

        stage = self.stages[stage_id]
        stage.status = TaskStatus.IN_PROGRESS
        stage.started_at = datetime.utcnow().isoformat()
        stage.substeps_total = substeps_total
        stage.substeps_done = 0
        stage.message = message or stage.description
        stage.progress = 0.0

        # Log to pipeline logger
        if self.session_id:
            self.logger.start_task(stage_id, stage.name, self.session_id)

        await self._broadcast(
            "stage_start",
            {
                "stage_id": stage_id,
                "stage": stage.to_dict(),
                "overall": self.get_state(),
            },
        )

    async def update_stage(
        self,
        stage_id: str,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        substeps_done: Optional[int] = None,
    ):
        """Update stage progress."""
        if stage_id not in self.stages:
            return

        stage = self.stages[stage_id]

        if progress is not None:
            stage.progress = min(1.0, max(0.0, progress))
        if message is not None:
            stage.message = message
        if substeps_done is not None:
            stage.substeps_done = substeps_done
            if stage.substeps_total > 0:
                stage.progress = substeps_done / stage.substeps_total

        # Log update
        if self.session_id:
            self.logger.update_task(
                stage_id,
                progress=stage.progress,
                message=stage.message,
                session_id=self.session_id,
            )

        await self._broadcast(
            "stage_update",
            {
                "stage_id": stage_id,
                "stage": stage.to_dict(),
                "overall": self.get_state(),
            },
        )

    async def complete_stage(
        self,
        stage_id: str,
        success: bool = True,
        error: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """Complete a pipeline stage."""
        if stage_id not in self.stages:
            return

        stage = self.stages[stage_id]
        stage.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        stage.completed_at = datetime.utcnow().isoformat()
        stage.progress = 1.0 if success else stage.progress
        stage.error = error
        if message:
            stage.message = message

        # Log completion
        if self.session_id:
            self.logger.complete_task(
                stage_id,
                success=success,
                error=error,
                session_id=self.session_id,
            )

        await self._broadcast(
            "stage_complete",
            {
                "stage_id": stage_id,
                "success": success,
                "stage": stage.to_dict(),
                "overall": self.get_state(),
            },
        )

    async def skip_stage(self, stage_id: str, reason: str = ""):
        """Skip a stage (e.g., when using cached results)."""
        if stage_id not in self.stages:
            return

        stage = self.stages[stage_id]
        stage.status = TaskStatus.SKIPPED
        stage.message = reason or "Skipped"
        stage.progress = 1.0

        await self._broadcast(
            "stage_skip",
            {
                "stage_id": stage_id,
                "reason": reason,
                "stage": stage.to_dict(),
                "overall": self.get_state(),
            },
        )

    def sync_start_stage(self, stage_id: str, substeps_total: int = 0, message: str = ""):
        """Synchronous version of start_stage for non-async contexts."""
        if stage_id not in self.stages:
            return

        stage = self.stages[stage_id]
        stage.status = TaskStatus.IN_PROGRESS
        stage.started_at = datetime.utcnow().isoformat()
        stage.substeps_total = substeps_total
        stage.substeps_done = 0
        stage.message = message or stage.description
        stage.progress = 0.0

        if self.session_id:
            self.logger.start_task(stage_id, stage.name, self.session_id)

    def sync_update_stage(
        self,
        stage_id: str,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        substeps_done: Optional[int] = None,
    ):
        """Synchronous version of update_stage."""
        if stage_id not in self.stages:
            return

        stage = self.stages[stage_id]

        if progress is not None:
            stage.progress = min(1.0, max(0.0, progress))
        if message is not None:
            stage.message = message
        if substeps_done is not None:
            stage.substeps_done = substeps_done
            if stage.substeps_total > 0:
                stage.progress = substeps_done / stage.substeps_total

        if self.session_id:
            self.logger.update_task(
                stage_id,
                progress=stage.progress,
                message=stage.message,
                session_id=self.session_id,
            )

    def sync_complete_stage(
        self,
        stage_id: str,
        success: bool = True,
        error: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """Synchronous version of complete_stage."""
        if stage_id not in self.stages:
            return

        stage = self.stages[stage_id]
        stage.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        stage.completed_at = datetime.utcnow().isoformat()
        stage.progress = 1.0 if success else stage.progress
        stage.error = error
        if message:
            stage.message = message

        if self.session_id:
            self.logger.complete_task(
                stage_id,
                success=success,
                error=error,
                session_id=self.session_id,
            )


def format_cli_progress(tracker: ProgressTracker) -> str:
    """
    Format progress as CLI-style checklist output.

    Example output:
    ┌─────────────────────────────────────────────────┐
    │ Analytic Continuation Pipeline                   │
    ├─────────────────────────────────────────────────┤
    │ ✓ Validate Input          [████████████] 100%   │
    │ ✓ Load Curve              [████████████] 100%   │
    │ ● Fit Laurent Map         [████████░░░░]  67%   │
    │   Fitting N=24...                               │
    │ ○ Check Holomorphic       [░░░░░░░░░░░░]   0%   │
    │ ○ Prepare Render          [░░░░░░░░░░░░]   0%   │
    │ ○ Render                  [░░░░░░░░░░░░]   0%   │
    └─────────────────────────────────────────────────┘
    """
    lines = []
    width = 55

    lines.append("┌" + "─" * (width - 2) + "┐")
    lines.append("│" + " Analytic Continuation Pipeline".ljust(width - 2) + "│")
    lines.append("├" + "─" * (width - 2) + "┤")

    for stage_id, _, _ in PIPELINE_STAGES:
        stage = tracker.stages[stage_id]

        # Status icon
        if stage.status == TaskStatus.COMPLETED:
            icon = "✓"
        elif stage.status == TaskStatus.FAILED:
            icon = "✗"
        elif stage.status == TaskStatus.IN_PROGRESS:
            icon = "●"
        elif stage.status == TaskStatus.SKIPPED:
            icon = "○"
        else:
            icon = "○"

        # Progress bar
        bar_width = 12
        filled = int(stage.progress * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        pct = f"{int(stage.progress * 100):3d}%"

        # Stage name (truncated if needed)
        name = stage.name[:20].ljust(20)

        line = f"│ {icon} {name} [{bar}] {pct}   │"
        lines.append(line)

        # Show message for in-progress stage
        if stage.status == TaskStatus.IN_PROGRESS and stage.message:
            msg = stage.message[: width - 6]
            lines.append("│   " + msg.ljust(width - 5) + "│")
        elif stage.status == TaskStatus.FAILED and stage.error:
            err = f"Error: {stage.error}"[: width - 6]
            lines.append("│   " + err.ljust(width - 5) + "│")

    lines.append("└" + "─" * (width - 2) + "┘")

    return "\n".join(lines)
