"""
Task Scheduler Module

This module provides advanced scheduling capabilities for SNMP data collection tasks.
It supports cron-like scheduling, task prioritization, bulk operations, and resource management.

Features:
- Cron expression parsing and scheduling
- Task priority management
- Concurrent task execution with resource limits
- Bulk operation optimization
- Task dependency management
- Retry logic and error handling
- Performance monitoring and metrics
- Resource pooling and connection management
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import heapq
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("croniter not available, cron scheduling disabled")

from ..utils.data_structures import CollectionTask, CollectionResult
from ..collectors.olt_collector import OLTCollector, OLTCollectionConfig
from ..storage.database_converter import DatabaseManager

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ScheduledTask:
    """Scheduled task with execution metadata."""
    task: CollectionTask
    next_run: datetime
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    last_run: Optional[datetime] = None
    last_result: Optional[CollectionResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    average_duration: float = 0.0
    total_duration: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None

    def __lt__(self, other):
        """For priority queue ordering."""
        return self.next_run < other.next_run


@dataclass
class TaskExecution:
    """Task execution context."""
    scheduled_task: ScheduledTask
    start_time: datetime
    executor_id: str
    execution_id: str


class ResourcePool:
    """Resource pool for managing concurrent task execution."""

    def __init__(self, max_concurrent_tasks: int = 10, max_connections: int = 50):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.connection_pool = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.total_connections_created = 0

    async def acquire_connection(self, connection_factory: Callable):
        """Acquire a connection from the pool."""
        try:
            # Try to get existing connection
            connection = self.connection_pool.get_nowait()
            return connection
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            if self.active_connections < self.max_connections:
                connection = await connection_factory()
                self.active_connections += 1
                self.total_connections_created += 1
                return connection
            else:
                # Wait for available connection
                return await self.connection_pool.get()

    async def release_connection(self, connection):
        """Release a connection back to the pool."""
        try:
            self.connection_pool.put_nowait(connection)
        except asyncio.QueueFull:
            # Pool is full, close the connection
            if hasattr(connection, 'close'):
                await connection.close()
            self.active_connections -= 1

    async def acquire_execution_slot(self):
        """Acquire a task execution slot."""
        await self.semaphore.acquire()

    def release_execution_slot(self):
        """Release a task execution slot."""
        self.semaphore.release()


class TaskScheduler:
    """Advanced task scheduler for SNMP data collection."""

    def __init__(self,
                 max_concurrent_tasks: int = 10,
                 max_connections: int = 50,
                 task_timeout: int = 300,
                 retry_delay: int = 60,
                 enable_metrics: bool = True):
        """
        Initialize the task scheduler.

        Args:
            max_concurrent_tasks: Maximum concurrent task executions
            max_connections: Maximum database connections
            task_timeout: Default task timeout in seconds
            retry_delay: Delay between retries in seconds
            enable_metrics: Enable performance metrics collection
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_timeout = task_timeout
        self.retry_delay = retry_delay
        self.enable_metrics = enable_metrics

        # Resource management
        self.resource_pool = ResourcePool(max_concurrent_tasks, max_connections)

        # Task management
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[ScheduledTask] = []
        self.running_tasks: Dict[str, TaskExecution] = {}
        self.task_dependencies: Dict[str, List[str]] = {}

        # Execution tracking
        self.execution_history: List[CollectionResult] = []
        self.performance_metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_execution_time': 0.0,
            'queue_depth': 0,
            'active_tasks': 0,
            'resource_utilization': 0.0
        }

        # Scheduler state
        self.running = False
        self.scheduler_task = None

        # Collectors cache
        self.collectors: Dict[str, OLTCollector] = {}

        logger.info(f"Task scheduler initialized: max_concurrent={max_concurrent_tasks}, max_connections={max_connections}")

    async def start(self):
        """Start the task scheduler."""
        if self.running:
            logger.warning("Task scheduler is already running")
            return

        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task scheduler started")

    async def stop(self):
        """Stop the task scheduler."""
        if not self.running:
            return

        self.running = False

        # Cancel scheduler task
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        # Wait for running tasks to complete or timeout
        if self.running_tasks:
            logger.info(f"Waiting for {len(self.running_tasks)} running tasks to complete...")
            await asyncio.sleep(5)  # Give tasks time to complete

        # Cleanup collectors
        for collector in self.collectors.values():
            try:
                await collector.cleanup()
            except:
                pass
        self.collectors.clear()

        logger.info("Task scheduler stopped")

    async def add_task(self,
                      task: CollectionTask,
                      schedule: Optional[str] = None,
                      dependencies: Optional[List[str]] = None) -> bool:
        """
        Add a task to the scheduler.

        Args:
            task: Collection task to schedule
            schedule: Cron expression for recurring tasks
            dependencies: List of task IDs this task depends on

        Returns:
            True if task was added successfully
        """
        try:
            # Calculate next run time
            if schedule:
                if not CRONITER_AVAILABLE:
                    logger.error("croniter not available, cannot schedule recurring tasks")
                    return False

                cron = croniter(schedule, datetime.now())
                next_run = cron.get_next(datetime)
            else:
                # Run immediately
                next_run = datetime.now()

            # Create scheduled task
            scheduled_task = ScheduledTask(
                task=task,
                next_run=next_run,
                max_retries=task.parameters.get('max_retries', 3)
            )

            # Add to scheduled tasks
            self.scheduled_tasks[task.task_id] = scheduled_task

            # Add to priority queue
            heapq.heappush(self.task_queue, scheduled_task)

            # Store dependencies
            if dependencies:
                self.task_dependencies[task.task_id] = dependencies

            logger.info(f"Added task {task.task_id} ({task.task_type}), next run: {next_run}")
            return True

        except Exception as e:
            logger.error(f"Failed to add task {task.task_id}: {e}")
            return False

    async def remove_task(self, task_id: str) -> bool:
        """Remove a task from the scheduler."""
        try:
            if task_id in self.scheduled_tasks:
                scheduled_task = self.scheduled_tasks[task_id]
                scheduled_task.status = TaskStatus.CANCELLED

                # Remove from scheduled tasks
                del self.scheduled_tasks[task_id]

                # Remove from dependencies
                self.task_dependencies.pop(task_id, None)

                logger.info(f"Removed task {task_id}")
                return True
            else:
                logger.warning(f"Task {task_id} not found")
                return False

        except Exception as e:
            logger.error(f"Failed to remove task {task_id}: {e}")
            return False

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Scheduler loop started")

        while self.running:
            try:
                # Process ready tasks
                await self._process_ready_tasks()

                # Clean up completed tasks
                await self._cleanup_completed_tasks()

                # Update metrics
                if self.enable_metrics:
                    await self._update_metrics()

                # Wait before next iteration
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)

        logger.info("Scheduler loop ended")

    async def _process_ready_tasks(self):
        """Process tasks that are ready to run."""
        current_time = datetime.now()
        tasks_to_run = []

        # Find ready tasks
        while self.task_queue and self.task_queue[0].next_run <= current_time:
            task = heapq.heappop(self.task_queue)

            # Check if task is still valid
            if (task.task.task_id in self.scheduled_tasks and
                task.status == TaskStatus.PENDING):

                # Check dependencies
                if await self._check_dependencies(task.task.task_id):
                    tasks_to_run.append(task)
                else:
                    # Reschedule task for later
                    task.next_run = current_time + timedelta(minutes=1)
                    heapq.heappush(self.task_queue, task)

        # Execute ready tasks
        for task in tasks_to_run:
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                # Re-queue task if we're at capacity
                task.next_run = current_time + timedelta(seconds=10)
                heapq.heappush(self.task_queue, task)
                continue

            # Start task execution
            asyncio.create_task(self._execute_task(task))

    async def _check_dependencies(self, task_id: str) -> bool:
        """Check if task dependencies are satisfied."""
        dependencies = self.task_dependencies.get(task_id, [])

        for dep_id in dependencies:
            if dep_id in self.scheduled_tasks:
                dep_task = self.scheduled_tasks[dep_id]
                if dep_task.status not in [TaskStatus.COMPLETED]:
                    return False

        return True

    async def _execute_task(self, scheduled_task: ScheduledTask):
        """Execute a scheduled task."""
        task_id = scheduled_task.task.task_id
        execution_id = f"{task_id}_{int(time.time())}"

        try:
            # Update task status
            scheduled_task.status = TaskStatus.RUNNING
            scheduled_task.last_run = datetime.now()
            scheduled_task.execution_count += 1

            # Create execution context
            execution = TaskExecution(
                scheduled_task=scheduled_task,
                start_time=datetime.now(),
                executor_id="scheduler",
                execution_id=execution_id
            )
            self.running_tasks[task_id] = execution

            logger.info(f"Executing task {task_id} (execution #{scheduled_task.execution_count})")

            # Acquire resources
            await self.resource_pool.acquire_execution_slot()

            # Execute task with timeout
            result = await asyncio.wait_for(
                self._run_collection_task(scheduled_task.task),
                timeout=self.task_timeout
            )

            # Process result
            await self._process_task_result(scheduled_task, result)

        except asyncio.TimeoutError:
            error_msg = f"Task {task_id} timed out after {self.task_timeout}s"
            logger.error(error_msg)
            await self._handle_task_failure(scheduled_task, error_msg)

        except Exception as e:
            error_msg = f"Task {task_id} failed: {str(e)}"
            logger.error(error_msg)
            await self._handle_task_failure(scheduled_task, error_msg)

        finally:
            # Release resources
            self.resource_pool.release_execution_slot()

            # Remove from running tasks
            self.running_tasks.pop(task_id, None)

    async def _run_collection_task(self, task: CollectionTask) -> CollectionResult:
        """Run a collection task."""
        start_time = datetime.now()

        try:
            # Get or create collector
            collector = await self._get_collector(task)

            if not collector:
                raise Exception(f"Failed to get collector for device {task.device_id}")

            # Execute task based on type
            if task.task_type == "discovery":
                # Run device discovery
                olt_data = await collector.collect_all_data()
                data_collected = {"olt_data": olt_data}

            elif task.task_type == "monitoring":
                # Run monitoring collection
                olt_data = await collector.collect_all_data()
                data_collected = {"olt_data": olt_data}

            elif task.task_type == "bulk_collection":
                # Run bulk collection
                data_collected = await self._run_bulk_collection(task, collector)

            else:
                raise Exception(f"Unknown task type: {task.task_type}")

            # Create successful result
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return CollectionResult(
                task_id=task.task_id,
                device_id=task.device_id,
                success=True,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                data_collected=data_collected,
                metrics_collected=len(data_collected),
                records_stored=len(data_collected)
            )

        except Exception as e:
            # Create failed result
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return CollectionResult(
                task_id=task.task_id,
                device_id=task.device_id,
                success=False,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                errors=[str(e)]
            )

    async def _get_collector(self, task: CollectionTask) -> Optional[OLTCollector]:
        """Get or create a collector for the task."""
        device_id = task.device_id

        if device_id not in self.collectors:
            # Create collector from task parameters
            config_dict = task.parameters.get('collector_config', {})
            config = OLTCollectionConfig(**config_dict)

            collector = OLTCollector(config)

            if await collector.initialize():
                self.collectors[device_id] = collector
            else:
                logger.error(f"Failed to initialize collector for {device_id}")
                return None

        return self.collectors[device_id]

    async def _run_bulk_collection(self, task: CollectionTask, collector: OLTCollector) -> Dict[str, Any]:
        """Run bulk collection operations."""
        try:
            # Get bulk collection parameters
            bulk_config = task.parameters.get('bulk_config', {})
            collection_types = bulk_config.get('collection_types', ['olt', 'onus', 'ports'])

            results = {}

            # Collect each type of data
            for collection_type in collection_types:
                if collection_type == 'olt':
                    olt_data = await collector.collect_all_data()
                    results['olt'] = olt_data

                elif collection_type == 'onus':
                    # Collect ONU data specifically
                    onus = await collector._collect_onu_data()
                    results['onus'] = onus

                elif collection_type == 'ports':
                    # Collect port data specifically
                    ports = await collector._collect_port_data()
                    results['ports'] = ports

            return results

        except Exception as e:
            logger.error(f"Bulk collection failed: {e}")
            raise

    async def _process_task_result(self, scheduled_task: ScheduledTask, result: CollectionResult):
        """Process task execution result."""
        try:
            # Update scheduled task
            scheduled_task.last_result = result
            scheduled_task.total_duration += result.duration
            scheduled_task.average_duration = scheduled_task.total_duration / scheduled_task.execution_count

            if result.success:
                # Task completed successfully
                scheduled_task.status = TaskStatus.COMPLETED
                self.performance_metrics['completed_tasks'] += 1

                # Add to execution history
                self.execution_history.append(result)

                # Keep history size manageable
                if len(self.execution_history) > 1000:
                    self.execution_history = self.execution_history[-500:]

                logger.info(f"Task {scheduled_task.task.task_id} completed successfully in {result.duration:.2f}s")

                # Schedule next run if it's a recurring task
                if scheduled_task.task.schedule:
                    await self._schedule_next_run(scheduled_task)
                else:
                    # Remove one-time task
                    self.scheduled_tasks.pop(scheduled_task.task.task_id, None)

            else:
                # Task failed
                await self._handle_task_failure(scheduled_task, "; ".join(result.errors))

        except Exception as e:
            logger.error(f"Error processing task result: {e}")

    async def _handle_task_failure(self, scheduled_task: ScheduledTask, error_msg: str):
        """Handle task execution failure."""
        scheduled_task.status = TaskStatus.FAILED
        scheduled_task.error_count += 1
        scheduled_task.last_error = error_msg

        self.performance_metrics['failed_tasks'] += 1

        # Retry logic
        if scheduled_task.retry_count < scheduled_task.max_retries:
            scheduled_task.retry_count += 1
            scheduled_task.status = TaskStatus.RETRYING

            # Schedule retry with exponential backoff
            retry_delay = self.retry_delay * (2 ** scheduled_task.retry_count)
            scheduled_task.next_run = datetime.now() + timedelta(seconds=retry_delay)

            heapq.heappush(self.task_queue, scheduled_task)

            logger.info(f"Task {scheduled_task.task.task_id} will retry in {retry_delay}s (attempt {scheduled_task.retry_count + 1}/{scheduled_task.max_retries})")
        else:
            logger.error(f"Task {scheduled_task.task.task_id} failed permanently after {scheduled_task.max_retries} retries: {error_msg}")

            # Remove failed task
            self.scheduled_tasks.pop(scheduled_task.task.task_id, None)

    async def _schedule_next_run(self, scheduled_task: ScheduledTask):
        """Schedule next run for a recurring task."""
        try:
            if CRONITER_AVAILABLE and scheduled_task.task.schedule:
                cron = croniter(scheduled_task.task.schedule, datetime.now())
                scheduled_task.next_run = cron.get_next(datetime)
                scheduled_task.status = TaskStatus.PENDING

                heapq.heappush(self.task_queue, scheduled_task)

                logger.debug(f"Scheduled next run for task {scheduled_task.task.task_id}: {scheduled_task.next_run}")

        except Exception as e:
            logger.error(f"Error scheduling next run: {e}")

    async def _cleanup_completed_tasks(self):
        """Clean up completed and old tasks."""
        try:
            # Remove tasks that haven't run in a long time
            cutoff_time = datetime.now() - timedelta(hours=24)

            tasks_to_remove = []
            for task_id, scheduled_task in self.scheduled_tasks.items():
                if (scheduled_task.status == TaskStatus.COMPLETED and
                    scheduled_task.last_run and
                    scheduled_task.last_run < cutoff_time):
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                del self.scheduled_tasks[task_id]
                logger.debug(f"Cleaned up old task {task_id}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _update_metrics(self):
        """Update performance metrics."""
        try:
            self.performance_metrics['total_tasks'] = len(self.scheduled_tasks)
            self.performance_metrics['queue_depth'] = len(self.task_queue)
            self.performance_metrics['active_tasks'] = len(self.running_tasks)
            self.performance_metrics['resource_utilization'] = len(self.running_tasks) / self.max_concurrent_tasks

            # Calculate average execution time
            if self.execution_history:
                total_time = sum(r.duration for r in self.execution_history[-100:])
                self.performance_metrics['average_execution_time'] = total_time / min(len(self.execution_history), 100)

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler performance metrics."""
        metrics = self.performance_metrics.copy()
        metrics.update({
            'running_tasks': list(self.running_tasks.keys()),
            'collectors_cached': len(self.collectors),
            'connections_created': self.resource_pool.total_connections_created,
            'active_connections': self.resource_pool.active_connections,
        })
        return metrics

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        if task_id in self.scheduled_tasks:
            scheduled_task = self.scheduled_tasks[task_id]
            return {
                'task_id': task_id,
                'status': scheduled_task.status.value,
                'next_run': scheduled_task.next_run.isoformat(),
                'last_run': scheduled_task.last_run.isoformat() if scheduled_task.last_run else None,
                'execution_count': scheduled_task.execution_count,
                'retry_count': scheduled_task.retry_count,
                'error_count': scheduled_task.error_count,
                'average_duration': scheduled_task.average_duration,
                'last_error': scheduled_task.last_error
            }
        return None

    async def export_schedule(self, file_path: str):
        """Export current schedule to file."""
        try:
            schedule_data = {
                'export_time': datetime.now().isoformat(),
                'tasks': []
            }

            for task_id, scheduled_task in self.scheduled_tasks.items():
                task_data = {
                    'task': scheduled_task.task.__dict__,
                    'next_run': scheduled_task.next_run.isoformat(),
                    'status': scheduled_task.status.value,
                    'execution_count': scheduled_task.execution_count,
                    'retry_count': scheduled_task.retry_count
                }
                schedule_data['tasks'].append(task_data)

            with open(file_path, 'w') as f:
                json.dump(schedule_data, f, indent=2, default=str)

            logger.info(f"Schedule exported to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export schedule: {e}")

    async def import_schedule(self, file_path: str) -> int:
        """Import schedule from file."""
        try:
            with open(file_path, 'r') as f:
                schedule_data = json.load(f)

            imported_count = 0

            for task_data in schedule_data.get('tasks', []):
                try:
                    # Recreate task
                    task_dict = task_data['task']
                    task = CollectionTask(**task_dict)

                    # Add to scheduler
                    if await self.add_task(task):
                        imported_count += 1

                except Exception as e:
                    logger.error(f"Failed to import task: {e}")

            logger.info(f"Imported {imported_count} tasks from {file_path}")
            return imported_count

        except Exception as e:
            logger.error(f"Failed to import schedule: {e}")
            return 0