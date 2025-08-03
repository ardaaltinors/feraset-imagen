"""Controller for weekly report endpoints."""

import json
import logging
from firebase_functions import https_fn
from services import ReportService


class ReportController:
    """Controller for handling weekly report HTTP requests."""
    
    def __init__(self):
        """Initialize report controller."""
        self.report_service = ReportService()
        self.logger = logging.getLogger(__name__)
    
    def schedule_weekly_report(self, req: https_fn.Request) -> https_fn.Response:
        """
        Generate weekly usage and credit consumption report.
        
        This endpoint is designed to be triggered by a scheduler.
        """
        try:
            self.logger.info("Processing scheduled weekly report request")
            
            # Generate the weekly report
            result = self.report_service.generate_weekly_report()
            
            # Determine HTTP status code based on report status
            if result.get("reportStatus") == "success":
                status_code = 200
            elif result.get("reportStatus") == "partial_success":
                status_code = 207  # Multi-Status
            else:
                status_code = 500
            
            # Log the result
            if result.get("reportStatus") == "success":
                self.logger.info("Weekly report generated successfully")
            else:
                self.logger.error(f"Weekly report failed: {result.get('error', 'Unknown error')}")
            
            return https_fn.Response(
                response=json.dumps(result, default=str),
                status=status_code,
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            error_msg = f"Weekly report controller error: {str(e)}"
            self.logger.error(error_msg)
            
            error_response = {
                "reportStatus": "failed",
                "error": error_msg,
                "error_type": "controller"
            }
            
            return https_fn.Response(
                response=json.dumps(error_response),
                status=500,
                headers={"Content-Type": "application/json"}
            )