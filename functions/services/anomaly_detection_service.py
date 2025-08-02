"""Service for detecting anomalies in usage patterns."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from core import Config


class AnomalyDetectionService:
    """Service for detecting unusual usage spikes and patterns."""
    
    def __init__(self):
        """Initialize anomaly detection service."""
        self.logger = logging.getLogger(__name__)
        self.thresholds = Config.ANOMALY_DETECTION
    
    def detect_anomalies(
        self, 
        current_stats: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect anomalies in current week's data compared to historical patterns.
        
        Args:
            current_stats: Current week's statistics
            historical_data: Historical weekly reports for comparison
            
        Returns:
            Dict containing anomaly detection results
        """
        try:
            anomalies = {
                "detected_anomalies": [],
                "anomaly_score": 0,
                "severity_level": "normal",
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            if not historical_data:
                self.logger.warning("No historical data available for anomaly detection")
                anomalies["warning"] = "Insufficient historical data for comparison"
                return anomalies
            
            # Calculate historical averages
            historical_averages = self._calculate_historical_averages(historical_data)
            
            # Detect various types of anomalies
            request_anomalies = self._detect_request_anomalies(current_stats, historical_averages)
            credit_anomalies = self._detect_credit_anomalies(current_stats, historical_averages)
            user_anomalies = self._detect_user_anomalies(current_stats, historical_averages)
            performance_anomalies = self._detect_performance_anomalies(current_stats, historical_averages)
            
            # Combine all anomalies
            all_anomalies = request_anomalies + credit_anomalies + user_anomalies + performance_anomalies
            
            # Calculate overall anomaly score and severity
            anomaly_score = self._calculate_anomaly_score(all_anomalies)
            severity_level = self._determine_severity_level(anomaly_score)
            
            anomalies.update({
                "detected_anomalies": all_anomalies,
                "anomaly_score": round(anomaly_score, 2),
                "severity_level": severity_level,
                "total_anomalies": len(all_anomalies),
                "historical_comparison": {
                    "periods_analyzed": len(historical_data),
                    "baseline_period": f"{self.thresholds['historical_days']} days"
                }
            })
            
            self.logger.info(f"Anomaly detection completed: {len(all_anomalies)} anomalies detected, severity: {severity_level}")
            
            return anomalies
            
        except Exception as e:
            error_msg = f"Anomaly detection failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "detected_anomalies": [],
                "anomaly_score": 0,
                "severity_level": "error",
                "error": error_msg,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _calculate_historical_averages(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate averages from historical data."""
        if not historical_data:
            return {}
        
        total_requests = sum(
            report.get("generation_stats", {}).get("total_requests", 0) 
            for report in historical_data
        )
        total_credits = sum(
            report.get("credit_stats", {}).get("net_credits_consumed", 0) 
            for report in historical_data
        )
        total_users = sum(
            report.get("user_stats", {}).get("active_users_count", 0) 
            for report in historical_data
        )
        total_failures = sum(
            report.get("generation_stats", {}).get("failed_requests", 0) 
            for report in historical_data
        )
        
        periods = len(historical_data)
        
        return {
            "avg_requests": total_requests / periods if periods > 0 else 0,
            "avg_credits": total_credits / periods if periods > 0 else 0,
            "avg_active_users": total_users / periods if periods > 0 else 0,
            "avg_failure_rate": (total_failures / total_requests) if total_requests > 0 else 0,
            "periods": periods
        }
    
    def _detect_request_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        historical_averages: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in request patterns."""
        anomalies = []
        generation_stats = current_stats.get("generation_stats", {})
        current_requests = generation_stats.get("total_requests", 0)
        avg_requests = historical_averages.get("avg_requests", 0)
        
        # Total request spike detection
        if avg_requests > 0 and current_requests > (avg_requests * self.thresholds["total_request_spike_multiplier"]):
            spike_ratio = current_requests / avg_requests
            anomalies.append({
                "type": "request_spike",
                "severity": "high" if spike_ratio > 5 else "medium",
                "description": f"Total requests ({current_requests}) are {spike_ratio:.1f}x higher than historical average ({avg_requests:.1f})",
                "current_value": current_requests,
                "historical_average": round(avg_requests, 1),
                "spike_ratio": round(spike_ratio, 2)
            })
        
        # Individual user request spike detection
        user_breakdown = current_stats.get("user_stats", {}).get("user_request_breakdown", {})
        for user_id, request_count in user_breakdown.items():
            if request_count > self.thresholds["user_request_spike_threshold"]:
                anomalies.append({
                    "type": "user_request_spike",
                    "severity": "medium",
                    "description": f"User {user_id} made {request_count} requests (above threshold of {self.thresholds['user_request_spike_threshold']})",
                    "user_id": user_id,
                    "current_value": request_count,
                    "threshold": self.thresholds["user_request_spike_threshold"]
                })
        
        return anomalies
    
    def _detect_credit_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        historical_averages: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in credit consumption."""
        anomalies = []
        credit_stats = current_stats.get("credit_stats", {})
        current_credits = credit_stats.get("net_credits_consumed", 0)
        avg_credits = historical_averages.get("avg_credits", 0)
        
        # Credit consumption spike detection
        if avg_credits > 0 and current_credits > (avg_credits * self.thresholds["credit_consumption_spike_multiplier"]):
            spike_ratio = current_credits / avg_credits
            anomalies.append({
                "type": "credit_consumption_spike",
                "severity": "high" if spike_ratio > 5 else "medium",
                "description": f"Credit consumption ({current_credits}) is {spike_ratio:.1f}x higher than historical average ({avg_credits:.1f})",
                "current_value": current_credits,
                "historical_average": round(avg_credits, 1),
                "spike_ratio": round(spike_ratio, 2)
            })
        
        # High refund rate detection
        total_deducted = credit_stats.get("total_credits_deducted", 0)
        total_refunded = credit_stats.get("total_credits_refunded", 0)
        if total_deducted > 0:
            refund_rate = total_refunded / total_deducted
            if refund_rate > 0.3:  # 30% refund rate threshold
                anomalies.append({
                    "type": "high_refund_rate",
                    "severity": "medium",
                    "description": f"High refund rate of {refund_rate:.1%} indicates potential system issues",
                    "refund_rate": round(refund_rate, 3),
                    "total_refunded": total_refunded,
                    "total_deducted": total_deducted
                })
        
        return anomalies
    
    def _detect_user_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        historical_averages: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in user behavior."""
        anomalies = []
        user_stats = current_stats.get("user_stats", {})
        current_active_users = user_stats.get("active_users_count", 0)
        avg_active_users = historical_averages.get("avg_active_users", 0)
        
        # New user spike detection (simplified - would need user creation tracking)
        if avg_active_users > 0 and current_active_users > (avg_active_users + self.thresholds["new_user_spike_threshold"]):
            user_increase = current_active_users - avg_active_users
            anomalies.append({
                "type": "user_activity_spike",
                "severity": "low",
                "description": f"Active user count ({current_active_users}) increased by {user_increase} from average ({avg_active_users:.1f})",
                "current_value": current_active_users,
                "historical_average": round(avg_active_users, 1),
                "increase": round(user_increase, 1)
            })
        
        return anomalies
    
    def _detect_performance_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        historical_averages: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Detect performance-related anomalies."""
        anomalies = []
        generation_stats = current_stats.get("generation_stats", {})
        current_failure_rate = generation_stats.get("failure_rate", 0) / 100  # Convert percentage to decimal
        historical_failure_rate = historical_averages.get("avg_failure_rate", 0)
        
        # High failure rate detection
        if current_failure_rate > self.thresholds["failure_rate_threshold"]:
            anomalies.append({
                "type": "high_failure_rate",
                "severity": "high",
                "description": f"Failure rate of {current_failure_rate:.1%} exceeds threshold of {self.thresholds['failure_rate_threshold']:.1%}",
                "current_value": round(current_failure_rate, 3),
                "threshold": self.thresholds["failure_rate_threshold"],
                "failed_requests": generation_stats.get("failed_requests", 0),
                "total_requests": generation_stats.get("total_requests", 0)
            })
        
        # Model performance anomalies
        model_performance = current_stats.get("model_performance", {})
        for model_name, model_stats in model_performance.items():
            model_failure_rate = model_stats.get("failure_rate", 0) / 100
            if model_failure_rate > (self.thresholds["failure_rate_threshold"] * 1.5):  # 1.5x threshold for individual models
                anomalies.append({
                    "type": "model_performance_degradation",
                    "severity": "medium",
                    "description": f"Model {model_name} has high failure rate of {model_failure_rate:.1%}",
                    "model": model_name,
                    "failure_rate": round(model_failure_rate, 3),
                    "failed_requests": model_stats.get("failed", 0),
                    "total_requests": model_stats.get("total_requests", 0)
                })
        
        return anomalies
    
    def _calculate_anomaly_score(self, anomalies: List[Dict[str, Any]]) -> float:
        """Calculate overall anomaly score based on detected anomalies."""
        if not anomalies:
            return 0.0
        
        severity_weights = {
            "low": 1.0,
            "medium": 2.5,
            "high": 5.0
        }
        
        total_score = sum(
            severity_weights.get(anomaly.get("severity", "low"), 1.0) 
            for anomaly in anomalies
        )
        
        return total_score
    
    def _determine_severity_level(self, anomaly_score: float) -> str:
        """Determine overall severity level based on anomaly score."""
        if anomaly_score >= 10:
            return "critical"
        elif anomaly_score >= 5:
            return "high"
        elif anomaly_score >= 2:
            return "medium"
        elif anomaly_score > 0:
            return "low"
        else:
            return "normal"