"""Helper utilities for thread state metric updates."""

from task_framework.logging import logger
from task_framework.metrics import threads_current
from task_framework.thread_state import ThreadState


def update_thread_state_gauge(previous_state: ThreadState | str, new_state: ThreadState | str) -> None:
    """Update threads_current gauge when thread state transitions.
    
    Decrements the previous state's gauge and increments the new state's gauge.
    This ensures accurate counts of threads in each state.
    
    Args:
        previous_state: Previous thread state (enum or string)
        new_state: New thread state (enum or string)
    """
    try:
        # Convert to string values for metric labels
        prev_state_value = previous_state.value if hasattr(previous_state, "value") else str(previous_state)
        new_state_value = new_state.value if hasattr(new_state, "value") else str(new_state)
        
        # Only update if state actually changed
        if prev_state_value != new_state_value:
            # Decrement previous state gauge (if it exists and is > 0)
            try:
                threads_current.labels(state=prev_state_value).dec()
            except Exception:
                # Ignore if gauge cannot be decremented (e.g., already zero or doesn't exist)
                pass
            
            # Increment new state gauge
            threads_current.labels(state=new_state_value).inc()
    except Exception as e:
        # Log but don't fail on metric update errors
        logger.exception("metrics.update_thread_state_gauge_failed", error=str(e))


async def restore_thread_metrics_from_db(database) -> None:
    """Restore thread metrics from database on server startup.
    
    Queries the database for current thread counts by state and restores
    the threads_current gauge values. This ensures metrics persist across
    server restarts.
    
    Args:
        database: Database interface instance
    """
    try:
        from task_framework.metrics import threads_current, threads_total
        from task_framework.thread_state import ThreadState
        
        # Query all threads from database
        all_threads = []
        try:
            # Try to get all threads (may need to query without filters)
            filter_dict = {}
            all_threads = await database.query_threads(filter_dict)
        except Exception:
            # If query_threads doesn't work without filters, try alternative approach
            # Some DB implementations may need different query methods
            logger.warning("metrics.restore.could_not_query_all_threads", error="query_threads may require filters")
            return
        
        # Count threads by state
        state_counts: dict[str, int] = {}
        total_created = 0
        
        for thread in all_threads:
            state_value = thread.state.value if hasattr(thread.state, "value") else str(thread.state)
            state_counts[state_value] = state_counts.get(state_value, 0) + 1
            total_created += 1
        
        # Restore threads_current gauge for each state
        for state_value, count in state_counts.items():
            try:
                threads_current.labels(state=state_value).set(count)
            except Exception as e:
                logger.warning(
                    "metrics.restore.gauge_set_failed",
                    state=state_value,
                    count=count,
                    error=str(e)
                )
        
        # Restore threads_total counter (set initial value based on total created)
        # Note: Prometheus counters are cumulative, so we set the initial value
        # by incrementing from zero to the current total
        if total_created > 0:
            # Get all possible states to ensure counters exist
            all_states = [ThreadState.QUEUED, ThreadState.RUNNING, ThreadState.SUCCEEDED, 
                         ThreadState.FAILED, ThreadState.STOPPED, ThreadState.TIMEOUT, ThreadState.EXPIRED]
            
            # For each state, increment counter by the count of threads in that state
            for state in all_states:
                state_value = state.value if hasattr(state, "value") else str(state)
                count = state_counts.get(state_value, 0)
                if count > 0:
                    try:
                        # Increment counter to restore cumulative value
                        # Note: This assumes threads_total represents "total threads that reached this state"
                        # If semantics differ, adjust accordingly
                        threads_total.labels(state=state_value).inc(count)
                    except Exception as e:
                        logger.warning(
                            "metrics.restore.counter_inc_failed",
                            state=state_value,
                            count=count,
                            error=str(e)
                        )
        
        logger.info(
            "metrics.restored_from_db",
            total_threads=total_created,
            state_counts=state_counts
        )
    except Exception as e:
        # Log error but don't fail startup if metrics restoration fails
        logger.exception("metrics.restore.failed", error=str(e))

