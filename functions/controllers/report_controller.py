"""Controller for weekly report endpoints."""

import json
import logging
from firebase_functions import https_fn, scheduler_fn
from services import ReportService


class ReportController:
    """Controller for handling weekly report HTTP requests."""
    
    def __init__(self):
        """Initialize report controller."""
        self.report_service = ReportService()
        self.logger = logging.getLogger(__name__)
    
    
    def generate_weekly_report(self, event: scheduler_fn.ScheduledEvent) -> None:
        """
        Generate weekly report triggered by scheduler.
        
        Args:
            event: The scheduler event that triggered this function
        """
        try:
            self.logger.info("Processing scheduled weekly report")
            
            # Generate the weekly report
            result = self.report_service.generate_weekly_report()
            
            # Log the result
            if result.get("reportStatus") == "success":
                self.logger.info("Weekly report generated successfully")
            else:
                self.logger.error(f"Weekly report failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            error_msg = f"Scheduled weekly report error: {str(e)}"
            self.logger.error(error_msg)
            raise