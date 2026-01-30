"""
Cron-like scheduler for ReplyFast.

Example usage:
    from replyfast import SignalClient
    from replyfast.scheduler import Scheduler

    client = SignalClient("./data")
    scheduler = Scheduler()

    # Schedule a message every day at 9:00 AM
    def send_morning_greeting(recipient, message):
        client.send_message_sync(recipient, message)

    scheduler.register(
        "0 9 * * *",  # cron syntax: minute hour day month weekday
        send_morning_greeting,
        args=("uuid-here", "Good morning!")
    )

    # Schedule every 5 minutes
    scheduler.register(
        "*/5 * * * *",
        lambda: print("Every 5 minutes")
    )

    # Start the scheduler (blocking)
    scheduler.run()

    # Or run in background
    scheduler.start()  # non-blocking
    # ... do other things ...
    scheduler.stop()
"""

import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional

try:
    from croniter import croniter
except ImportError:
    croniter = None


class ScheduledJob:
    """A scheduled job with cron expression."""

    def __init__(
        self,
        cron_expr: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
    ):
        if croniter is None:
            raise ImportError(
                "croniter is required for scheduling. "
                "Install it with: pip install croniter"
            )

        self.cron_expr = cron_expr
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.name = name or func.__name__
        self._cron = croniter(cron_expr, datetime.now())
        self.next_run: datetime = self._cron.get_next(datetime)
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.enabled = True

    def update_next_run(self):
        """Calculate the next run time."""
        self._cron = croniter(self.cron_expr, datetime.now())
        self.next_run = self._cron.get_next(datetime)

    def should_run(self) -> bool:
        """Check if the job should run now."""
        return self.enabled and datetime.now() >= self.next_run

    def run(self):
        """Execute the job."""
        try:
            self.func(*self.args, **self.kwargs)
            self.last_run = datetime.now()
            self.run_count += 1
        except Exception as e:
            print(f"[Scheduler] Error in job '{self.name}': {e}")
        finally:
            self.update_next_run()

    def __repr__(self):
        return (
            f"ScheduledJob(name='{self.name}', cron='{self.cron_expr}', "
            f"next_run={self.next_run}, run_count={self.run_count})"
        )


class Scheduler:
    """
    Cron-like scheduler for running functions at specified times.

    Cron expression format: "minute hour day month weekday"

    Examples:
        "0 9 * * *"     - Every day at 9:00 AM
        "*/5 * * * *"   - Every 5 minutes
        "0 */2 * * *"   - Every 2 hours
        "30 8 * * 1-5"  - 8:30 AM on weekdays
        "0 0 1 * *"     - First day of every month at midnight
    """

    def __init__(self, check_interval: float = 1.0):
        """
        Initialize the scheduler.

        Args:
            check_interval: How often to check for due jobs (in seconds)
        """
        self.jobs: list[ScheduledJob] = []
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def register(
        self,
        cron_expr: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
    ) -> ScheduledJob:
        """
        Register a function to run on a cron schedule.

        Args:
            cron_expr: Cron expression (e.g., "0 9 * * *" for 9 AM daily)
            func: Function to call
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            name: Optional name for the job (for logging/identification)

        Returns:
            The created ScheduledJob

        Cron expression format:
            ┌───────────── minute (0-59)
            │ ┌───────────── hour (0-23)
            │ │ ┌───────────── day of month (1-31)
            │ │ │ ┌───────────── month (1-12)
            │ │ │ │ ┌───────────── day of week (0-6, 0=Sunday)
            │ │ │ │ │
            * * * * *

        Examples:
            "*/5 * * * *"   - Every 5 minutes
            "0 9 * * *"     - Every day at 9:00 AM
            "0 9 * * 1"     - Every Monday at 9:00 AM
            "30 */2 * * *"  - Every 2 hours at minute 30
        """
        job = ScheduledJob(cron_expr, func, args, kwargs, name)
        with self._lock:
            self.jobs.append(job)
        return job

    def unregister(self, job: ScheduledJob) -> bool:
        """
        Remove a job from the scheduler.

        Args:
            job: The job to remove

        Returns:
            True if the job was found and removed
        """
        with self._lock:
            if job in self.jobs:
                self.jobs.remove(job)
                return True
            return False

    def clear(self):
        """Remove all scheduled jobs."""
        with self._lock:
            self.jobs.clear()

    def list_jobs(self) -> list[ScheduledJob]:
        """Get a list of all scheduled jobs."""
        with self._lock:
            return list(self.jobs)

    def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()
            with self._lock:
                jobs_to_run = [j for j in self.jobs if j.should_run()]

            for job in jobs_to_run:
                # Run each job in its own thread to avoid blocking
                threading.Thread(
                    target=job.run,
                    name=f"job-{job.name}",
                    daemon=True
                ).start()

            time.sleep(self.check_interval)

    def run(self):
        """
        Run the scheduler (blocking).

        This will block the current thread. Use start() for non-blocking.
        Press Ctrl+C to stop.
        """
        self._running = True
        print(f"[Scheduler] Started with {len(self.jobs)} job(s)")
        for job in self.jobs:
            print(f"  - {job.name}: next run at {job.next_run}")

        try:
            self._run_loop()
        except KeyboardInterrupt:
            print("\n[Scheduler] Stopped")
            self._running = False

    def start(self):
        """
        Start the scheduler in a background thread (non-blocking).

        Use stop() to stop the scheduler.
        """
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name="scheduler",
            daemon=True
        )
        self._thread.start()
        print(f"[Scheduler] Started in background with {len(self.jobs)} job(s)")

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        print("[Scheduler] Stopped")

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running


# Convenience function for simple use cases
_default_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """Get or create the default scheduler instance."""
    global _default_scheduler
    if _default_scheduler is None:
        _default_scheduler = Scheduler()
    return _default_scheduler


def schedule(
    cron_expr: str,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    name: Optional[str] = None,
):
    """
    Decorator to schedule a function with cron syntax.

    Example:
        @schedule("0 9 * * *")  # Every day at 9 AM
        def morning_task():
            print("Good morning!")

        # Start the scheduler
        from replyfast.scheduler import get_scheduler
        get_scheduler().start()
    """
    def decorator(func: Callable) -> Callable:
        get_scheduler().register(cron_expr, func, args, kwargs, name)
        return func
    return decorator
