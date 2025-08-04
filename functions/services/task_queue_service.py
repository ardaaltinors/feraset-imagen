"""Service for managing Cloud Tasks queue operations."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from core import Config
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2


class TaskQueueService:
    """Service for managing asynchronous task processing with Cloud Tasks."""
    
    def __init__(self):
        """Initialize task queue service."""
        self.logger = logging.getLogger(__name__)
        self.project_id = Config.PROJECT_ID
        self.location = Config.REGION
        self.queue_name = "image-generation-queue"
        
        self.is_emulator = Config.is_emulator()
        
        if self.is_emulator:
            self.logger.info("Task queue service initialized for emulator mode (HTTP-based)")
        else:
            # prod configuration
            try:
                self.logger.info("Initializing Cloud Tasks client for production")
                self.client = tasks_v2.CloudTasksClient()
                
                self.parent = self.client.queue_path(
                    self.project_id, self.location, self.queue_name
                )
                self.logger.info(f"Cloud Tasks client initialized for production, queue path: {self.parent}")
                
            except Exception as e:
                self.logger.error(f"Cloud Tasks initialization failed: {str(e)}", exc_info=True)
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
        if self.is_emulator:
            # In emulator mode, directly call the worker function via HTTP
            return self._enqueue_emulator_task(generation_request_id, task_payload, delay_seconds)
        
        if not self.client:
            self.logger.error(f"Cloud Tasks client not available for generation {generation_request_id}")
            return False
        
        try:
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
            
            self.logger.info(f"Task {response.name} enqueued for generation {generation_request_id} (production)")
            return True
            
        except Exception as e:
            error_msg = f"Failed to enqueue task for generation {generation_request_id}: {str(e)}"
            self.logger.error(error_msg)
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get current queue statistics.
        """
        if not self.client:
            return {
                "queue_name": self.queue_name,
                "state": "CLIENT_UNAVAILABLE",
                "mode": "emulator" if self.is_emulator else "production",
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
                "mode": "emulator" if self.is_emulator else "production",
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
    
    
    
    def _enqueue_emulator_task(self, generation_request_id: str, task_payload: Dict[str, Any], delay_seconds: int) -> bool:
        """
        Enqueue task in emulator mode by directly calling the worker function.
        
        In Firebase emulator, task queue functions are exposed as HTTP endpoints.
        """
        try:
            import requests
            import threading
            import time
            
            # Get the worker function URL
            url = self._get_worker_function_url()
            
            def execute_task():
                """Execute the task after delay."""
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
                
                try:
                    response = requests.post(
                        url,
                        json=task_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        self.logger.info(f"Emulator task completed for generation {generation_request_id}")
                    else:
                        self.logger.error(f"Emulator task failed for generation {generation_request_id}: {response.status_code}")
                        
                except Exception as e:
                    self.logger.error(f"Error executing emulator task for generation {generation_request_id}: {str(e)}")
            
            # Execute task in background thread to simulate async behavior
            thread = threading.Thread(target=execute_task, daemon=True)
            thread.start()
            
            self.logger.info(f"Task enqueued for generation {generation_request_id} (emulator mode, delay: {delay_seconds}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enqueue emulator task for generation {generation_request_id}: {str(e)}")
            return False
    
