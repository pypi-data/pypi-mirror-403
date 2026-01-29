"""Concurrency policy handler for enforcing run concurrency rules."""

from typing import TYPE_CHECKING, Optional

from task_framework.logging import logger
from task_framework.models.schedule import ConcurrencyPolicy, Run, RunState, Schedule

if TYPE_CHECKING:
    from task_framework.interfaces.database import Database
    from task_framework.services.artifact_service import ArtifactService
    from task_framework.services.thread_service import ThreadService


class ConcurrencyPolicyHandler:
    """Handler for enforcing concurrency policies."""

    def __init__(
        self,
        database: "Database",
        artifact_service: Optional["ArtifactService"] = None,
        thread_service: Optional["ThreadService"] = None,
    ) -> None:
        """Initialize ConcurrencyPolicyHandler.
        
        Args:
            database: Database implementation
            artifact_service: Optional ArtifactService for deleting artifacts
            thread_service: Optional ThreadService for stopping threads
        """
        self.database = database
        self.artifact_service = artifact_service
        self.thread_service = thread_service

    async def check_and_enforce(
        self,
        schedule: Schedule,
        new_run: Run,
    ) -> bool:
        """Check concurrency policy and enforce if needed.
        
        Args:
            schedule: Schedule instance
            new_run: New run to be created
            
        Returns:
            True if run should proceed, False if run should be skipped
        """
        policy = schedule.concurrency_policy
        
        if policy == ConcurrencyPolicy.ALLOW:
            # No checking, proceed directly
            return True
        
        elif policy == ConcurrencyPolicy.FORBID:
            # Check if previous run is still running
            if await self._has_running_run(schedule.id):
                # Skip new run
                await self._enforce_forbid(new_run)
                return False
            # No running run, proceed
            return True
        
        elif policy == ConcurrencyPolicy.REPLACE:
            # Check if previous run is still running
            running_run = await self._get_running_run(schedule.id)
            if running_run:
                # Stop previous run and delete artifacts
                await self._enforce_replace(running_run)
            # Always proceed with new run
            return True
        
        else:
            # Unknown policy, log warning and proceed
            logger.warning(
                "schedule.run.concurrency.unknown_policy",
                schedule_id=schedule.id,
                policy=policy.value if hasattr(policy, 'value') else str(policy),
            )
            return True

    async def _has_running_run(self, schedule_id: str) -> bool:
        """Check if schedule has a running run.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            True if running run exists, False otherwise
        """
        running_run = await self.database.get_running_run_by_schedule(schedule_id)
        return running_run is not None

    async def _get_running_run(self, schedule_id: str) -> Optional[Run]:
        """Get the currently running run for a schedule.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Running Run instance if found, None otherwise
        """
        return await self.database.get_running_run_by_schedule(schedule_id)

    async def _enforce_forbid(self, run: Run) -> None:
        """Enforce forbid policy by skipping the run.
        
        Args:
            run: Run instance to skip
        """
        run.state = RunState.SKIPPED
        run.finished_at = run.created_at  # Set finished_at to created_at for skipped runs
        await self.database.update_run(run)
        
        # Logging
        logger.info(
            "schedule.run.skipped",
            schedule_id=run.schedule_id,
            run_id=run.run_id,
            reason="forbid_policy_conflict",
        )

    async def _enforce_replace(self, previous_run: Run) -> None:
        """Enforce replace policy by stopping previous run and deleting artifacts.
        
        Args:
            previous_run: Previous run instance to stop
        """
        # Stop previous run
        previous_run.state = RunState.STOPPED
        from datetime import datetime, timezone
        
        previous_run.finished_at = datetime.now(timezone.utc)
        await self.database.update_run(previous_run)
        
        # Stop threads synchronously
        if self.thread_service:
            for thread_id in previous_run.threads:
                try:
                    thread = await self.database.get_thread(thread_id)
                    if thread:
                        # Handle both enum and string values (due to use_enum_values=True)
                        thread_state = thread.state.value if hasattr(thread.state, 'value') else str(thread.state)
                        if thread_state in ["queued", "running"]:
                            await self.thread_service.stop_thread(
                                thread_id=thread_id,
                                user_id=None,
                                app_id=None,
                                is_admin=False,
                            )
                except Exception as e:
                    logger.warning(
                        "schedule.run.replace.thread_stop_failed",
                        schedule_id=previous_run.schedule_id,
                        run_id=previous_run.run_id,
                        thread_id=thread_id,
                        error=str(e),
                    )
        
        # Delete artifacts synchronously
        if self.artifact_service:
            for thread_id in previous_run.threads:
                try:
                    artifacts = await self.database.get_thread_artifacts(thread_id)
                    for artifact in artifacts:
                        await self.artifact_service.delete_artifact(
                            artifact_id=artifact.id,
                            user_id=None,
                            app_id=None,
                            is_admin=False,
                        )
                except Exception as e:
                    logger.warning(
                        "schedule.run.replace.artifact_delete_failed",
                        schedule_id=previous_run.schedule_id,
                        run_id=previous_run.run_id,
                        thread_id=thread_id,
                        error=str(e),
                    )
        
        # Logging
        logger.info(
            "schedule.run.replaced",
            schedule_id=previous_run.schedule_id,
            previous_run_id=previous_run.run_id,
            reason="replace_policy",
        )

