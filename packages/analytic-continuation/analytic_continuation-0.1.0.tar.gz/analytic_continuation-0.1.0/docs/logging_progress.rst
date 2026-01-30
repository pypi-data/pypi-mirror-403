Logging and Progress Tracking
=============================

The logging and progress modules provide infrastructure for tracking pipeline execution,
reporting progress, and structured logging.

Pipeline Logger
---------------

.. autoclass:: analytic_continuation.PipelineLogger
   :members:
   :special-members: __init__

The pipeline logger provides structured logging for each stage:

.. code-block:: python

   from analytic_continuation import PipelineLogger, get_logger

   # Get a logger instance
   logger = get_logger("my_pipeline")

   # Log stage start
   logger.stage_start("stage_3_laurent_fit")

   # Log progress
   logger.progress("Fitting with N=16", progress=0.5)

   # Log stage completion
   logger.stage_complete("stage_3_laurent_fit", success=True)

.. autofunction:: analytic_continuation.get_logger

Task Status
-----------

.. autoclass:: analytic_continuation.TaskStatus
   :members:

.. autoclass:: analytic_continuation.TaskProgress
   :members:

Track individual task progress:

.. code-block:: python

   from analytic_continuation import TaskStatus, TaskProgress

   # Create task progress
   task = TaskProgress(
       name="Laurent Fitting",
       status=TaskStatus.RUNNING,
       progress=0.0,
       message="Starting...",
   )

   # Update progress
   task.progress = 0.75
   task.message = "Checking quality metrics"

   # Mark complete
   task.status = TaskStatus.COMPLETED
   task.progress = 1.0

Pipeline Session
----------------

.. autoclass:: analytic_continuation.PipelineSession
   :members:

Manages a complete pipeline execution session:

.. code-block:: python

   from analytic_continuation import PipelineSession

   # Create a new session
   session = PipelineSession()

   # Start a stage
   session.start_stage("preprocessing")

   # Record metrics
   session.record_metric("curve_points", 500)
   session.record_metric("estimated_complexity", "medium")

   # Complete stage
   session.complete_stage("preprocessing", success=True)

   # Get session summary
   summary = session.get_summary()

Progress Tracker
----------------

.. autoclass:: analytic_continuation.ProgressTracker
   :members:

High-level progress tracking across pipeline stages:

.. code-block:: python

   from analytic_continuation import ProgressTracker, PIPELINE_STAGES

   # Create tracker
   tracker = ProgressTracker()

   # Track each stage
   for stage in PIPELINE_STAGES:
       tracker.start_stage(stage.name)
       # ... do work ...
       tracker.complete_stage(stage.name)

   # Get overall progress
   print(f"Overall progress: {tracker.overall_progress * 100:.1f}%")

Stage Information
-----------------

.. autoclass:: analytic_continuation.StageInfo
   :members:

.. autodata:: analytic_continuation.PIPELINE_STAGES

Predefined pipeline stages:

.. code-block:: python

   from analytic_continuation import PIPELINE_STAGES

   for stage in PIPELINE_STAGES:
       print(f"Stage {stage.index}: {stage.name}")
       print(f"  Description: {stage.description}")
       print(f"  Weight: {stage.weight}")

CLI Progress Formatting
-----------------------

.. autofunction:: analytic_continuation.format_cli_progress

Format progress for command-line display:

.. code-block:: python

   from analytic_continuation import format_cli_progress, ProgressTracker

   tracker = ProgressTracker()
   tracker.start_stage("stage_3_laurent_fit")
   tracker.update_progress(0.5)

   # Get formatted output
   output = format_cli_progress(tracker)
   print(output)

   # Output example:
   # [===========         ] 55% Stage 3: Laurent Map Fitting

Integration Example
-------------------

Complete example integrating logging and progress:

.. code-block:: python

   from analytic_continuation import (
       PipelineLogger,
       ProgressTracker,
       PipelineSession,
       PIPELINE_STAGES,
       format_cli_progress,
       fit_laurent_map,
       SplineExport,
   )

   # Set up infrastructure
   logger = PipelineLogger("analytic_continuation")
   tracker = ProgressTracker()
   session = PipelineSession()

   def run_pipeline(export: SplineExport):
       # Stage 3: Laurent Fitting
       stage = PIPELINE_STAGES[2]  # Stage 3
       tracker.start_stage(stage.name)
       session.start_stage(stage.name)
       logger.stage_start(stage.name)

       try:
           result = fit_laurent_map(export)

           if result.ok:
               session.record_metric("laurent_N", result.laurent_map.N)
               session.record_metric("fit_max_err", result.fit_max_err)
               tracker.complete_stage(stage.name)
               session.complete_stage(stage.name, success=True)
               logger.stage_complete(stage.name, success=True)
           else:
               tracker.fail_stage(stage.name, result.failure_reason)
               session.complete_stage(stage.name, success=False)
               logger.stage_complete(stage.name, success=False)

       except Exception as e:
           logger.error(f"Stage failed with exception: {e}")
           tracker.fail_stage(stage.name, str(e))
           session.complete_stage(stage.name, success=False)
           raise

       # Print progress
       print(format_cli_progress(tracker))

       return result

Callback-based Progress
-----------------------

For long-running operations, use callbacks:

.. code-block:: python

   def progress_callback(stage: str, progress: float, message: str):
       tracker.update_progress(progress)
       print(format_cli_progress(tracker), end='\r')

   # Pass callback to fitting function (if supported)
   result = fit_laurent_map(export, progress_callback=progress_callback)
