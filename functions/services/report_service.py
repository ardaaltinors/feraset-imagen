"""Service layer for weekly reporting functionality."""

import logging
from typing import Dict, Any
from repositories import ReportRepository
from .anomaly_detection_service import AnomalyDetectionService
from core import Config


class ReportService:
    """Service for generating weekly usage and credit consumption reports."""
    
    def __init__(self):
        """Initialize report service."""
        self.report_repository = ReportRepository()
        self.anomaly_detection_service = AnomalyDetectionService()
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
            
            # Get historical data for anomaly detection
            historical_reports = self.report_repository.get_historical_reports(
                days_back=Config.ANOMALY_DETECTION["historical_days"]
            )
            
            # Perform anomaly detection
            anomaly_analysis = self.anomaly_detection_service.detect_anomalies(
                current_stats=weekly_stats,
                historical_data=historical_reports
            )
            
            # Add anomaly analysis to weekly stats
            weekly_stats["anomaly_analysis"] = anomaly_analysis
            
            # Save report to database
            save_success = self.report_repository.save_weekly_report(weekly_stats)
            
            if not save_success:
                self.logger.warning("Report generated but failed to save to database")
                return {
                    "reportStatus": "partial_success",
                    "message": "Report generated but not saved to database",
                    "report_data": weekly_stats
                }
            
            # Log anomaly detection results
            anomaly_count = len(anomaly_analysis.get("detected_anomalies", []))
            severity = anomaly_analysis.get("severity_level", "normal")
            
            if anomaly_count > 0:
                self.logger.warning(f"Anomaly detection: {anomaly_count} anomalies detected with severity: {severity}")
            else:
                self.logger.info("Anomaly detection: No anomalies detected")
            
            self.logger.info("Weekly report generated and saved successfully")
            
            return {
                "reportStatus": "success",
                "report_data": weekly_stats,
                "summary": self._generate_report_summary(weekly_stats),
                "anomaly_summary": self._generate_anomaly_summary(anomaly_analysis)
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
    
    def _generate_anomaly_summary(self, anomaly_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a concise summary of anomaly detection results.
        """
        try:
            anomalies = anomaly_analysis.get("detected_anomalies", [])
            
            # Count anomalies by type and severity
            type_counts = {}
            severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            
            for anomaly in anomalies:
                anomaly_type = anomaly.get("type", "unknown")
                severity = anomaly.get("severity", "low")
                
                type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Get most critical anomalies
            critical_anomalies = [
                a for a in anomalies 
                if a.get("severity") in ["high", "critical"]
            ]
            
            return {
                "total_anomalies": len(anomalies),
                "severity_level": anomaly_analysis.get("severity_level", "normal"),
                "anomaly_score": anomaly_analysis.get("anomaly_score", 0),
                "severity_breakdown": {k: v for k, v in severity_counts.items() if v > 0},
                "type_breakdown": type_counts,
                "critical_anomalies_count": len(critical_anomalies),
                "requires_attention": len(critical_anomalies) > 0 or anomaly_analysis.get("severity_level") in ["high", "critical"],
                "analysis_timestamp": anomaly_analysis.get("analysis_timestamp")
            }
        except Exception:
            return {"error": "Failed to generate anomaly summary"}