"""Service layer for weekly reporting functionality."""

import logging
from typing import Dict, Any
from repositories import ReportRepository


class ReportService:
    """Service for generating weekly usage and credit consumption reports."""
    
    def __init__(self):
        """Initialize report service."""
        self.report_repository = ReportRepository()
        self.logger = logging.getLogger(__name__)
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive weekly usage report.
        
        Returns:
            Dict containing report status and statistics
        """
        try:
            self.logger.info("Starting weekly report generation")
            
            # Get weekly statistics
            weekly_stats = self.report_repository.get_weekly_usage_stats()
            
            if "error" in weekly_stats:
                self.logger.error(f"Failed to generate weekly stats: {weekly_stats['error']}")
                return {
                    "reportStatus": "failed",
                    "error": weekly_stats["error"],
                    "error_type": weekly_stats.get("error_type", "system")
                }
            
            # Save report to database
            save_success = self.report_repository.save_weekly_report(weekly_stats)
            
            if not save_success:
                self.logger.warning("Report generated but failed to save to database")
                return {
                    "reportStatus": "partial_success",
                    "message": "Report generated but not saved to database",
                    "report_data": weekly_stats
                }
            
            self.logger.info("Weekly report generated and saved successfully")
            
            return {
                "reportStatus": "success",
                "report_data": weekly_stats,
                "summary": self._generate_report_summary(weekly_stats)
            }
            
        except Exception as e:
            error_msg = f"Weekly report generation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "reportStatus": "failed",
                "error": error_msg,
                "error_type": "system"
            }
    
    def _generate_report_summary(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a concise summary of the weekly report.
        
        Args:
            stats: Full weekly statistics
            
        Returns:
            Dict containing key metrics summary
        """
        try:
            generation_stats = stats.get("generation_stats", {})
            credit_stats = stats.get("credit_stats", {})
            user_stats = stats.get("user_stats", {})
            
            return {
                "total_requests": generation_stats.get("total_requests", 0),
                "success_rate": generation_stats.get("success_rate", 0),
                "active_users": user_stats.get("active_users_count", 0),
                "credits_consumed": credit_stats.get("net_credits_consumed", 0),
                "most_popular_style": self._get_most_popular_item(
                    generation_stats.get("style_breakdown", {})
                ),
                "most_popular_size": self._get_most_popular_item(
                    generation_stats.get("size_breakdown", {})
                ),
                "report_period": stats.get("report_period", {})
            }
        except Exception:
            return {"error": "Failed to generate summary"}
    
    def _get_most_popular_item(self, breakdown: Dict[str, int]) -> str:
        """Get the most popular item from a breakdown dictionary."""
        if not breakdown:
            return "none"
        
        return max(breakdown.items(), key=lambda x: x[1])[0] if breakdown else "none"