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
        previous_week_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect anomalies by comparing current week's data to previous week.
        """
        try:
            anomalies = {
                "detected_anomalies": [],
                "anomaly_score": 0,
                "severity_level": "normal",
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            if "error" in previous_week_stats:
                self.logger.warning("No previous week data available for anomaly detection")
                anomalies["warning"] = "Insufficient previous week data for comparison"
                return anomalies
            
            # Detect various types of anomalies by comparing weeks
            request_anomalies = self._detect_request_anomalies(current_stats, previous_week_stats)
            credit_anomalies = self._detect_credit_anomalies(current_stats, previous_week_stats)
            user_anomalies = self._detect_user_anomalies(current_stats, previous_week_stats)
            performance_anomalies = self._detect_performance_anomalies(current_stats, previous_week_stats)
            
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
                "comparison_period": {
                    "current_week": current_stats.get("report_period", {}),
                    "previous_week": previous_week_stats.get("report_period", {})
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
    
    
    def _detect_request_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        previous_week_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in request patterns by comparing current vs previous week."""
        anomalies = []
        current_gen_stats = current_stats.get("generation_stats", {})
        previous_gen_stats = previous_week_stats.get("generation_stats", {})
        
        current_requests = current_gen_stats.get("total_requests", 0)
        previous_requests = previous_gen_stats.get("total_requests", 0)
        
        # Total request spike detection
        if previous_requests > 0 and current_requests > (previous_requests * self.thresholds["total_request_spike_multiplier"]):
            spike_ratio = current_requests / previous_requests
            anomalies.append({
                "type": "request_spike",
                "severity": "high" if spike_ratio > 5 else "medium",
                "description": f"Total requests ({current_requests}) are {spike_ratio:.1f}x higher than previous week ({previous_requests})",
                "current_value": current_requests,
                "previous_value": previous_requests,
                "spike_ratio": round(spike_ratio, 2)
            })
        
        # Individual user request spike detection
        current_user_breakdown = current_stats.get("user_stats", {}).get("user_request_breakdown", {})
        previous_user_breakdown = previous_week_stats.get("user_stats", {}).get("user_request_breakdown", {})
        
        for user_id, current_count in current_user_breakdown.items():
            previous_count = previous_user_breakdown.get(user_id, 0)
            
            # Check for absolute spike threshold
            if current_count > self.thresholds["user_request_spike_threshold"]:
                # Also check if it's significantly higher than previous week
                if previous_count == 0 or current_count > (previous_count * 2):
                    anomalies.append({
                        "type": "user_request_spike",
                        "severity": "medium",
                        "description": f"User {user_id} made {current_count} requests (previous week: {previous_count})",
                        "user_id": user_id,
                        "current_value": current_count,
                        "previous_value": previous_count,
                        "threshold": self.thresholds["user_request_spike_threshold"]
                    })
        
        return anomalies
    
    def _detect_credit_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        previous_week_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in credit consumption by comparing current vs previous week."""
        anomalies = []
        current_credit_stats = current_stats.get("credit_stats", {})
        previous_credit_stats = previous_week_stats.get("credit_stats", {})
        
        current_credits = current_credit_stats.get("net_credits_consumed", 0)
        previous_credits = previous_credit_stats.get("net_credits_consumed", 0)
        
        # Credit consumption spike detection
        if previous_credits > 0 and current_credits > (previous_credits * self.thresholds["credit_consumption_spike_multiplier"]):
            spike_ratio = current_credits / previous_credits
            anomalies.append({
                "type": "credit_consumption_spike",
                "severity": "high" if spike_ratio > 5 else "medium",
                "description": f"Credit consumption ({current_credits}) is {spike_ratio:.1f}x higher than previous week ({previous_credits})",
                "current_value": current_credits,
                "previous_value": previous_credits,
                "spike_ratio": round(spike_ratio, 2)
            })
        
        # High refund rate detection compared to previous week
        current_deducted = current_credit_stats.get("total_credits_deducted", 0)
        current_refunded = current_credit_stats.get("total_credits_refunded", 0)
        previous_deducted = previous_credit_stats.get("total_credits_deducted", 0)
        previous_refunded = previous_credit_stats.get("total_credits_refunded", 0)
        
        if current_deducted > 0:
            current_refund_rate = current_refunded / current_deducted
            previous_refund_rate = previous_refunded / previous_deducted if previous_deducted > 0 else 0
            
            # Alert if current refund rate is high and significantly higher than previous week
            if current_refund_rate > 0.3 or (previous_refund_rate > 0 and current_refund_rate > (previous_refund_rate * 2)):
                anomalies.append({
                    "type": "high_refund_rate",
                    "severity": "medium",
                    "description": f"High refund rate of {current_refund_rate:.1%} (previous week: {previous_refund_rate:.1%})",
                    "current_refund_rate": round(current_refund_rate, 3),
                    "previous_refund_rate": round(previous_refund_rate, 3),
                    "current_refunded": current_refunded,
                    "current_deducted": current_deducted
                })
        
        return anomalies
    
    def _detect_user_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        previous_week_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in user behavior by comparing current vs previous week."""
        anomalies = []
        current_user_stats = current_stats.get("user_stats", {})
        previous_user_stats = previous_week_stats.get("user_stats", {})
        
        current_active_users = current_user_stats.get("active_users_count", 0)
        previous_active_users = previous_user_stats.get("active_users_count", 0)
        
        # User activity spike detection
        if previous_active_users > 0 and current_active_users > (previous_active_users + self.thresholds["new_user_spike_threshold"]):
            user_increase = current_active_users - previous_active_users
            anomalies.append({
                "type": "user_activity_spike",
                "severity": "low",
                "description": f"Active user count ({current_active_users}) increased by {user_increase} from previous week ({previous_active_users})",
                "current_value": current_active_users,
                "previous_value": previous_active_users,
                "increase": user_increase
            })
        
        # Detect new users (users active this week but not last week)
        current_users = set(current_user_stats.get("active_users", []))
        previous_users = set(previous_user_stats.get("active_users", []))
        new_users = current_users - previous_users
        
        if len(new_users) > self.thresholds["new_user_spike_threshold"]:
            anomalies.append({
                "type": "new_user_spike",
                "severity": "low",
                "description": f"{len(new_users)} new users this week (threshold: {self.thresholds['new_user_spike_threshold']})",
                "new_users_count": len(new_users),
                "threshold": self.thresholds["new_user_spike_threshold"],
                "new_users": list(new_users)[:10]  # Limit to first 10 for brevity
            })
        
        return anomalies
    
    def _detect_performance_anomalies(
        self, 
        current_stats: Dict[str, Any], 
        previous_week_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect performance-related anomalies by comparing current vs previous week."""
        anomalies = []
        current_gen_stats = current_stats.get("generation_stats", {})
        previous_gen_stats = previous_week_stats.get("generation_stats", {})
        
        current_failure_rate = current_gen_stats.get("failure_rate", 0) / 100  # Convert percentage to decimal
        previous_failure_rate = previous_gen_stats.get("failure_rate", 0) / 100
        
        # High failure rate detection (absolute threshold)
        if current_failure_rate > self.thresholds["failure_rate_threshold"]:
            anomalies.append({
                "type": "high_failure_rate",
                "severity": "high",
                "description": f"Failure rate of {current_failure_rate:.1%} exceeds threshold (previous week: {previous_failure_rate:.1%})",
                "current_failure_rate": round(current_failure_rate, 3),
                "previous_failure_rate": round(previous_failure_rate, 3),
                "threshold": self.thresholds["failure_rate_threshold"],
                "failed_requests": current_gen_stats.get("failed_requests", 0),
                "total_requests": current_gen_stats.get("total_requests", 0)
            })
        
        # Failure rate spike detection (relative to previous week)
        elif previous_failure_rate > 0 and current_failure_rate > (previous_failure_rate * 2):
            anomalies.append({
                "type": "failure_rate_spike",
                "severity": "medium",
                "description": f"Failure rate doubled from {previous_failure_rate:.1%} to {current_failure_rate:.1%}",
                "current_failure_rate": round(current_failure_rate, 3),
                "previous_failure_rate": round(previous_failure_rate, 3),
                "spike_ratio": round(current_failure_rate / previous_failure_rate, 2)
            })
        
        # Model performance comparison
        current_models = current_stats.get("model_performance", {})
        previous_models = previous_week_stats.get("model_performance", {})
        
        # Individual model analysis
        for model_name, current_model_stats in current_models.items():
            current_model_failure_rate = current_model_stats.get("failure_rate", 0) / 100
            previous_model_stats = previous_models.get(model_name, {})
            previous_model_failure_rate = previous_model_stats.get("failure_rate", 0) / 100
            
            # Critical model failure rate (>15%)
            if current_model_failure_rate > self.thresholds["critical_model_failure_rate"]:
                anomalies.append({
                    "type": "critical_model_failure_rate",
                    "severity": "high",
                    "description": f"Model {model_name} has critical failure rate of {current_model_failure_rate:.1%} (>{self.thresholds['critical_model_failure_rate']:.0%} threshold)",
                    "model": model_name,
                    "current_failure_rate": round(current_model_failure_rate, 3),
                    "previous_failure_rate": round(previous_model_failure_rate, 3),
                    "threshold": self.thresholds["critical_model_failure_rate"],
                    "failed_requests": current_model_stats.get("failed", 0),
                    "total_requests": current_model_stats.get("total_requests", 0)
                })
            
            # Model failure rate spike (2x increase from previous week)
            elif previous_model_failure_rate > 0 and current_model_failure_rate > (previous_model_failure_rate * self.thresholds["model_failure_spike_multiplier"]):
                anomalies.append({
                    "type": "model_failure_rate_spike",
                    "severity": "medium",
                    "description": f"Model {model_name} failure rate spiked from {previous_model_failure_rate:.1%} to {current_model_failure_rate:.1%}",
                    "model": model_name,
                    "current_failure_rate": round(current_model_failure_rate, 3),
                    "previous_failure_rate": round(previous_model_failure_rate, 3),
                    "spike_ratio": round(current_model_failure_rate / previous_model_failure_rate, 2)
                })
            
            # High model failure rate (absolute threshold - lower than critical)
            elif current_model_failure_rate > (self.thresholds["failure_rate_threshold"] * 1.5):
                anomalies.append({
                    "type": "model_performance_degradation",
                    "severity": "medium",
                    "description": f"Model {model_name} failure rate {current_model_failure_rate:.1%} exceeds threshold (previous: {previous_model_failure_rate:.1%})",
                    "model": model_name,
                    "current_failure_rate": round(current_model_failure_rate, 3),
                    "previous_failure_rate": round(previous_model_failure_rate, 3),
                    "failed_requests": current_model_stats.get("failed", 0),
                    "total_requests": current_model_stats.get("total_requests", 0)
                })
        
        # Cross-model comparison anomalies
        model_cross_comparison_anomalies = self._detect_cross_model_anomalies(current_models)
        anomalies.extend(model_cross_comparison_anomalies)
        
        return anomalies
    
    def _detect_cross_model_anomalies(self, current_models: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies by comparing performance between different models."""
        anomalies = []
        
        if len(current_models) < 2:
            return anomalies  # Need at least 2 models to compare
        
        # Get all models and their failure rates
        model_failure_rates = {}
        for model_name, model_stats in current_models.items():
            failure_rate = model_stats.get("failure_rate", 0) / 100
            total_requests = model_stats.get("total_requests", 0)
            
            # Only consider models with sufficient requests for meaningful comparison
            if total_requests >= self.thresholds["min_requests_for_model_comparison"]:
                model_failure_rates[model_name] = {
                    "failure_rate": failure_rate,
                    "total_requests": total_requests,
                    "failed_requests": model_stats.get("failed", 0)
                }
        
        if len(model_failure_rates) < 2:
            return anomalies
        
        # Find models with highest and lowest failure rates
        sorted_models = sorted(model_failure_rates.items(), key=lambda x: x[1]["failure_rate"])
        best_model = sorted_models[0]
        worst_model = sorted_models[-1]
        
        best_name, best_stats = best_model
        worst_name, worst_stats = worst_model
        
        # Check for significant performance gap between models
        best_rate = best_stats["failure_rate"]
        worst_rate = worst_stats["failure_rate"]
        
        # Anomaly if worst model has >5x higher failure rate than best model
        if best_rate > 0 and worst_rate > (best_rate * self.thresholds["model_performance_disparity_multiplier"]):
            ratio = worst_rate / best_rate
            anomalies.append({
                "type": "model_performance_disparity",
                "severity": "high",
                "description": f"Model {worst_name} failure rate ({worst_rate:.1%}) is {ratio:.1f}x higher than {best_name} ({best_rate:.1%})",
                "best_model": {
                    "name": best_name,
                    "failure_rate": round(best_rate, 3),
                    "total_requests": best_stats["total_requests"]
                },
                "worst_model": {
                    "name": worst_name,
                    "failure_rate": round(worst_rate, 3),
                    "total_requests": worst_stats["total_requests"]
                },
                "performance_ratio": round(ratio, 2)
            })
        
        # Check for any model significantly underperforming (>3x worse than average)
        if len(model_failure_rates) >= 2:
            avg_failure_rate = sum(stats["failure_rate"] for stats in model_failure_rates.values()) / len(model_failure_rates)
            
            for model_name, model_stats in model_failure_rates.items():
                model_failure_rate = model_stats["failure_rate"]
                
                if avg_failure_rate > 0 and model_failure_rate > (avg_failure_rate * self.thresholds["model_underperforming_multiplier"]):
                    anomalies.append({
                        "type": "model_underperforming",
                        "severity": "medium",
                        "description": f"Model {model_name} failure rate ({model_failure_rate:.1%}) is {model_failure_rate/avg_failure_rate:.1f}x higher than average ({avg_failure_rate:.1%})",
                        "model": model_name,
                        "model_failure_rate": round(model_failure_rate, 3),
                        "average_failure_rate": round(avg_failure_rate, 3),
                        "performance_ratio": round(model_failure_rate / avg_failure_rate, 2),
                        "total_requests": model_stats["total_requests"]
                    })
        
        # Check for models with suspiciously perfect performance (0% failure rate with many requests)
        for model_name, model_stats in model_failure_rates.items():
            if model_stats["failure_rate"] == 0 and model_stats["total_requests"] > self.thresholds["suspicious_perfect_performance_requests"]:
                # This might indicate data collection issues or the model isn't being properly tested
                anomalies.append({
                    "type": "suspicious_perfect_performance",
                    "severity": "low",
                    "description": f"Model {model_name} has 0% failure rate with {model_stats['total_requests']} requests - verify data collection",
                    "model": model_name,
                    "total_requests": model_stats["total_requests"],
                    "failure_rate": 0.0
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