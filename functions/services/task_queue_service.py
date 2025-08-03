"""Service for managing Cloud Tasks queue operations."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from core import Config

# Try to import Cloud Tasks, fallback to mock for emulator
try:
    from google.cloud import tasks_v2
    from google.protobuf import timestamp_pb2
    CLOUD_TASKS_AVAILABLE = True
except ImportError:
    # Fallback for development/emulator
    CLOUD_TASKS_AVAILABLE = False
    tasks_v2 = None
    timestamp_pb2 = None


class TaskQueueService:
    """Service for managing asynchronous task processing with Cloud Tasks."""
    
    def __init__(self):
        """Initialize task queue service."""
        self.logger = logging.getLogger(__name__)
        self.project_id = Config.PROJECT_ID
        self.location = "us-central1"  # Firebase Functions default region
        self.queue_name = "image-generation-queue"
        
        # Check if we're in emulator mode (project_id is demo-project or no credentials)
        is_emulator = (
            self.project_id == "demo-project" or 
            not self._has_credentials()
        )
        
        if CLOUD_TASKS_AVAILABLE and not is_emulator:
            try:
                self.client = tasks_v2.CloudTasksClient()
                # Construct the fully qualified queue name
                self.parent = self.client.queue_path(
                    self.project_id, self.location, self.queue_name
                )
                self.logger.info("Cloud Tasks client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Cloud Tasks initialization failed: {str(e)}, using fallback mode")
                self.client = None
                self.parent = None
        else:
            self.logger.warning("Using fallback mode for emulator or missing credentials")
            self.client = None
            self.parent = None
    
    def enqueue_generation_task(
        self, 
        generation_request_id: str,
        task_payload: Dict[str, Any],
        priority: str = "normal",
        delay_seconds: int = 0
    ) -> bool:
        """
        Enqueue an image generation task to Cloud Tasks.
        """
        if not CLOUD_TASKS_AVAILABLE or not self.client:
            # Fallback for emulator - simulate immediate processing
            self.logger.info(f"Emulator mode: Simulating task queue for generation {generation_request_id}")
            return self._simulate_emulator_task(generation_request_id, task_payload)
        
        try:
            # Create the task
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": self._get_worker_function_url(),
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "body": json.dumps(task_payload).encode(),
                }
            }
            
            # Add schedule time if delay is specified
            if delay_seconds > 0:
                # Create a timestamp for the scheduled time
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(datetime.utcnow() + timedelta(seconds=delay_seconds))
                task["schedule_time"] = timestamp
            
            # Enqueue the task
            response = self.client.create_task(
                request={"parent": self.parent, "task": task}
            )
            
            self.logger.info(f"Task {response.name} enqueued for generation {generation_request_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to enqueue task for generation {generation_request_id}: {str(e)}"
            self.logger.error(error_msg)
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get current queue statistics.
        """
        if not CLOUD_TASKS_AVAILABLE or not self.client:
            return {
                "queue_name": self.queue_name,
                "state": "EMULATOR_MODE",
                "retry_config": Config.TASK_QUEUE_CONFIG["retry_config"],
                "rate_limits": Config.TASK_QUEUE_CONFIG["rate_limits"]
            }
        
        try:
            # Get queue information
            queue = self.client.get_queue(name=self.parent)
            
            # Get queue statistics (approximate)
            stats = {
                "queue_name": self.queue_name,
                "state": queue.state.name if queue.state else "UNKNOWN",
                "retry_config": {
                    "max_attempts": queue.retry_config.max_attempts if queue.retry_config else None,
                    "min_backoff": queue.retry_config.min_backoff.seconds if queue.retry_config and queue.retry_config.min_backoff else None,
                    "max_backoff": queue.retry_config.max_backoff.seconds if queue.retry_config and queue.retry_config.max_backoff else None,
                },
                "rate_limits": {
                    "max_concurrent_dispatches": queue.rate_limits.max_concurrent_dispatches if queue.rate_limits else None,
                    "max_dispatches_per_second": queue.rate_limits.max_dispatches_per_second if queue.rate_limits else None,
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get queue stats: {str(e)}")
            return {"error": str(e)}
    
    def _get_worker_function_url(self) -> str:
        return Config.get_worker_function_url("processImageGeneration")
    
    def _generate_task_name(self, generation_request_id: str) -> str:
        """Generate a unique task name."""
        # Task names must be unique and URL-safe
        return f"generation-task-{generation_request_id.replace('_', '-')}"
    
    def estimate_completion_time(self, queue_position: int = None) -> Optional[datetime]:
        """
        Estimate when a task will complete based on queue position.
        """
        try:
            # Base processing time per task (estimate)
            avg_processing_time_seconds = 60  # 1 minute average
            
            # If queue position is known, calculate based on position
            if queue_position is not None:
                estimated_seconds = queue_position * avg_processing_time_seconds
            else:
                # Default estimate if position unknown
                estimated_seconds = avg_processing_time_seconds * 2
            
            return datetime.now() + timedelta(seconds=estimated_seconds)
            
        except Exception:
            return None
    
    def _simulate_emulator_task(self, generation_request_id: str, task_payload: Dict[str, Any]) -> bool:
        """
        Simulate task processing in emulator mode.
        
        In emulator mode, we can't use Cloud Tasks, so we just log the task
        and return True to simulate successful queueing. The actual processing
        would be handled by the background worker endpoint.
        """
        try:
            self.logger.info(f"Emulator mode: Task queued for generation {generation_request_id}")
            self.logger.info(f"Task payload: {json.dumps(task_payload, indent=2)}")
            
            # In emulator mode, we simulate successful queueing
            # The actual processing would be handled by calling the processImageGeneration endpoint
            return True
                
        except Exception as e:
            self.logger.error(f"Emulator task simulation failed: {str(e)}")
            return False
    
    def _has_credentials(self) -> bool:
        """Check if Google Cloud credentials are available."""
        try:
            import google.auth
            google.auth.default()
            return True
        except Exception:
            return False