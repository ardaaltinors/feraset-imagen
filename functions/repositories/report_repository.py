"""Repository for weekly report data aggregation."""

from typing import Dict, List, Any
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from core import Config


class ReportRepository(BaseRepository):
    """Repository for generating usage and credit consumption reports."""
    
    def __init__(self):
        """Initialize report repository."""
        super().__init__(Config.get_collection_name("reports"))
    
    def get_weekly_usage_stats(self) -> Dict[str, Any]:
        """
        Aggregate weekly usage statistics.
        """
        try:
            # Calculate date range for the past week
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Get generation requests from the past week
            generation_requests = self._get_weekly_generation_requests(start_date, end_date)
            
            # Get user transactions from the past week
            user_transactions = self._get_weekly_transactions(start_date, end_date)
            
            # Calculate statistics
            stats = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generation_stats": self._calculate_generation_stats(generation_requests),
                "credit_stats": self._calculate_credit_stats(user_transactions),
                "user_stats": self._calculate_user_stats(generation_requests, user_transactions),
                "model_performance": self._calculate_model_performance(generation_requests)
            }
            
            return stats
            
        except Exception as e:
            return {
                "error": f"Failed to generate weekly stats: {str(e)}",
                "error_type": "system"
            }
    
    def _get_weekly_generation_requests(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get generation requests from the past week."""
        try:
            generation_collection = self.db.collection(Config.get_collection_name("generation_requests"))
            docs = (
                generation_collection
                .where("created_at", ">=", start_date)
                .where("created_at", "<=", end_date)
                .stream()
            )
            
            requests = []
            for doc in docs:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                requests.append(request_data)
            
            return requests
        except Exception:
            return []
    
    def _get_weekly_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get all user transactions from the past week."""
        try:
            transactions = []
            users_collection = self.db.collection(Config.get_collection_name("users"))
            
            # Get all users
            user_docs = users_collection.stream()
            
            for user_doc in user_docs:
                user_id = user_doc.id
                
                # Get transactions for this user
                transaction_docs = (
                    users_collection
                    .document(user_id)
                    .collection("transactions")
                    .where("timestamp", ">=", start_date)
                    .where("timestamp", "<=", end_date)
                    .stream()
                )
                
                for trans_doc in transaction_docs:
                    transaction_data = trans_doc.to_dict()
                    transaction_data["id"] = trans_doc.id
                    transactions.append(transaction_data)
            
            return transactions
        except Exception:
            return []
    
    def _calculate_generation_stats(self, generation_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate generation request statistics."""
        total_requests = len(generation_requests)
        completed_requests = len([r for r in generation_requests if r.get("status") == "completed"])
        failed_requests = len([r for r in generation_requests if r.get("status") == "failed"])
        pending_requests = len([r for r in generation_requests if r.get("status") in ["pending", "processing"]])
        
        # Style breakdown
        style_breakdown = {}
        for request in generation_requests:
            style = request.get("style", "unknown")
            style_breakdown[style] = style_breakdown.get(style, 0) + 1
        
        # Size breakdown
        size_breakdown = {}
        for request in generation_requests:
            size = request.get("size", "unknown")
            size_breakdown[size] = size_breakdown.get(size, 0) + 1
        
        return {
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "failed_requests": failed_requests,
            "pending_requests": pending_requests,
            "success_rate": round((completed_requests / total_requests * 100), 2) if total_requests > 0 else 0,
            "failure_rate": round((failed_requests / total_requests * 100), 2) if total_requests > 0 else 0,
            "style_breakdown": style_breakdown,
            "size_breakdown": size_breakdown
        }
    
    def _calculate_credit_stats(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate credit consumption statistics."""
        total_credits_deducted = sum(
            t.get("credits", 0) for t in transactions if t.get("type") == "deduction"
        )
        total_credits_refunded = sum(
            t.get("credits", 0) for t in transactions if t.get("type") == "refund"
        )
        net_credits_consumed = total_credits_deducted - total_credits_refunded
        
        total_transactions = len(transactions)
        deduction_transactions = len([t for t in transactions if t.get("type") == "deduction"])
        refund_transactions = len([t for t in transactions if t.get("type") == "refund"])
        
        return {
            "total_credits_deducted": total_credits_deducted,
            "total_credits_refunded": total_credits_refunded,
            "net_credits_consumed": net_credits_consumed,
            "total_transactions": total_transactions,
            "deduction_transactions": deduction_transactions,
            "refund_transactions": refund_transactions,
            "average_credits_per_request": round(
                (total_credits_deducted / deduction_transactions), 2
            ) if deduction_transactions > 0 else 0
        }
    
    def _calculate_user_stats(self, generation_requests: List[Dict[str, Any]], transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate user activity statistics."""
        active_users = set()
        
        # Users who made generation requests
        for request in generation_requests:
            user_id = request.get("user_id")
            if user_id:
                active_users.add(user_id)
        
        # Users who had transactions
        for transaction in transactions:
            user_id = transaction.get("user_id")
            if user_id:
                active_users.add(user_id)
        
        # User request breakdown
        user_request_breakdown = {}
        for request in generation_requests:
            user_id = request.get("user_id", "unknown")
            user_request_breakdown[user_id] = user_request_breakdown.get(user_id, 0) + 1
        
        return {
            "active_users_count": len(active_users),
            "active_users": list(active_users),
            "user_request_breakdown": user_request_breakdown,
            "average_requests_per_user": round(
                (len(generation_requests) / len(active_users)), 2
            ) if len(active_users) > 0 else 0
        }
    
    def _calculate_model_performance(self, generation_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate AI model performance statistics."""
        model_stats = {}
        
        for request in generation_requests:
            model = request.get("model", "unknown")
            status = request.get("status", "unknown")
            
            if model not in model_stats:
                model_stats[model] = {
                    "total_requests": 0,
                    "completed": 0,
                    "failed": 0,
                    "success_rate": 0,
                    "failure_rate": 0
                }
            
            model_stats[model]["total_requests"] += 1
            
            if status == "completed":
                model_stats[model]["completed"] += 1
            elif status == "failed":
                model_stats[model]["failed"] += 1
        
        # Calculate rates
        for model, stats in model_stats.items():
            total = stats["total_requests"]
            if total > 0:
                stats["success_rate"] = round((stats["completed"] / total * 100), 2)
                stats["failure_rate"] = round((stats["failed"] / total * 100), 2)
        
        return model_stats
    
    def get_historical_reports(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Get historical weekly reports for anomaly detection comparison.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            docs = (
                self.db.collection(Config.get_collection_name("reports"))
                .where("report_type", "==", "weekly")
                .where("generated_at", ">=", cutoff_date)
                .order_by("generated_at", direction="DESCENDING")
                .limit(10)  # Limit to last 10 reports
                .stream()
            )
            
            reports = []
            for doc in docs:
                report_data = doc.to_dict()
                report_data["id"] = doc.id
                reports.append(report_data)
            
            return reports
        except Exception:
            return []
    
    def save_weekly_report(self, report_data: Dict[str, Any]) -> bool:
        """
        Save weekly report to database.
        """
        try:
            report_id = f"weekly_report_{datetime.now().strftime('%Y_%m_%d')}"
            report_data["id"] = report_id
            report_data["generated_at"] = datetime.now()
            report_data["report_type"] = "weekly"
            
            self.create(report_id, report_data)
            return True
        except Exception:
            return False