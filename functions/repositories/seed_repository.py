"""Repository for seeding database with initial data."""

from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any
import random
import uuid
from .base_repository import BaseRepository
from schemas import StyleModel, ColorModel, SizeModel, UserModel, GenerationStatus, AIModel, TransactionType
from core import Config


class SeedRepository(BaseRepository):
    """Repository for database seeding operations."""
    
    def __init__(self):
        """Initialize seed repository."""
        super().__init__("seed")  # Not used, but required by base class
    
    def get_validated_styles(self) -> List[Tuple[str, StyleModel]]:
        """Get predefined image styles with validation."""
        styles_data = [
            ("realistic", {
                "display_name": "Realistic",
                "description": "Photorealistic images with natural lighting",
                "sort_order": 1
            }),
            ("anime", {
                "display_name": "Anime", 
                "description": "Japanese animation style artwork",
                "sort_order": 2
            }),
            ("oil_painting", {
                "display_name": "Oil Painting",
                "description": "Traditional oil painting technique", 
                "sort_order": 3
            }),
            ("sketch", {
                "display_name": "Sketch",
                "description": "Hand-drawn pencil sketch style",
                "sort_order": 4
            }),
            ("cyberpunk", {
                "display_name": "Cyberpunk",
                "description": "Futuristic neon-lit cyberpunk aesthetic",
                "sort_order": 5
            }),
            ("watercolor", {
                "display_name": "Watercolor",
                "description": "Soft watercolor painting technique",
                "sort_order": 6
            })
        ]
        
        return [(style_id, StyleModel(**data)) for style_id, data in styles_data]
    
    def get_validated_colors(self) -> List[Tuple[str, ColorModel]]:
        """Get predefined color palettes with validation."""
        colors_data = [
            ("vibrant", {
                "display_name": "Vibrant",
                "description": "Bold and saturated colors",
                "hex_examples": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
                "sort_order": 1
            }),
            ("monochrome", {
                "display_name": "Monochrome",
                "description": "Black and white tones", 
                "hex_examples": ["#000000", "#808080", "#FFFFFF"],
                "sort_order": 2
            }),
            ("pastel", {
                "display_name": "Pastel",
                "description": "Soft and muted colors",
                "hex_examples": ["#FFB3BA", "#BAFFC9", "#BAE1FF"],
                "sort_order": 3
            }),
            ("neon", {
                "display_name": "Neon", 
                "description": "Electric glowing colors",
                "hex_examples": ["#39FF14", "#FF073A", "#00FFFF"],
                "sort_order": 4
            }),
            ("vintage", {
                "display_name": "Vintage",
                "description": "Warm retro color palette",
                "hex_examples": ["#D2B48C", "#CD853F", "#8B4513"],
                "sort_order": 5
            })
        ]
        
        return [(color_id, ColorModel(**data)) for color_id, data in colors_data]
    
    def get_validated_sizes(self) -> List[Tuple[str, SizeModel]]:
        """Get predefined image sizes with validation."""
        sizes_data = [
            ("512x512", {
                "width": 512,
                "height": 512,
                "aspect_ratio": "1:1",
                "display_name": "Square (512×512)",
                "description": "Perfect for avatars and social media",
                "credit_cost": 1,
                "sort_order": 1
            }),
            ("1024x1024", {
                "width": 1024,
                "height": 1024,
                "aspect_ratio": "1:1", 
                "display_name": "Large Square (1024×1024)",
                "description": "High resolution square images",
                "credit_cost": 3,
                "sort_order": 2
            }),
            ("1024x1792", {
                "width": 1024,
                "height": 1792,
                "aspect_ratio": "9:16",
                "display_name": "Portrait (1024×1792)",
                "description": "Vertical format for portraits",
                "credit_cost": 4,
                "sort_order": 3
            })
        ]
        
        return [(size_id, SizeModel(**data)) for size_id, data in sizes_data]
    
    def get_validated_users(self) -> List[Tuple[str, UserModel]]:
        """Get realistic test user data with validation."""
        current_time = datetime.now()
        users_data = [
            ("arda", {
                "name": "Arda Altinors",
                "email": "arda@altinors.com", 
                "current_credits": 500,
                "total_images_generated": 47,
                "created_at": current_time - timedelta(days=25),
                "updated_at": current_time - timedelta(hours=2),
                "last_login": current_time - timedelta(hours=2)
            }),
            ("havanur", {
                "name": "Havanur Koc",
                "email": "havanur@example.com",
                "current_credits": 5,
                "total_images_generated": 23,
                "created_at": current_time - timedelta(days=20),
                "updated_at": current_time - timedelta(days=1),
                "last_login": current_time - timedelta(days=1)
            }),
            ("alex_designer", {
                "name": "Alex Thompson",
                "email": "alex.thompson@designstudio.com",
                "current_credits": 8,
                "total_images_generated": 156,
                "created_at": current_time - timedelta(days=45),
                "updated_at": current_time - timedelta(hours=6),
                "last_login": current_time - timedelta(hours=6)
            }),
            ("sarah_artist", {
                "name": "Sarah Kim",
                "email": "sarah.kim@artcollective.org",
                "current_credits": 42,
                "total_images_generated": 89,
                "created_at": current_time - timedelta(days=30),
                "updated_at": current_time - timedelta(hours=12),
                "last_login": current_time - timedelta(hours=12)
            }),
            ("mike_creative", {
                "name": "Mike Johnson",
                "email": "mike.j@creativeworks.io",
                "current_credits": 3,
                "total_images_generated": 234,
                "created_at": current_time - timedelta(days=60),
                "updated_at": current_time - timedelta(days=3),
                "last_login": current_time - timedelta(days=3)
            }),
            ("emma_photo", {
                "name": "Emma Rodriguez",
                "email": "emma.r@photomagic.com",
                "current_credits": 67,
                "total_images_generated": 78,
                "created_at": current_time - timedelta(days=35),
                "updated_at": current_time - timedelta(hours=18),
                "last_login": current_time - timedelta(hours=18)
            }),
            ("david_dev", {
                "name": "David Chen",
                "email": "david.chen@techstartup.dev",
                "current_credits": 12,
                "total_images_generated": 45,
                "created_at": current_time - timedelta(days=15),
                "updated_at": current_time - timedelta(hours=4),
                "last_login": current_time - timedelta(hours=4)
            }),
            ("lisa_marketing", {
                "name": "Lisa Wilson",
                "email": "lisa.wilson@marketingpro.com",
                "current_credits": 28,
                "total_images_generated": 167,
                "created_at": current_time - timedelta(days=40),
                "updated_at": current_time - timedelta(hours=8),
                "last_login": current_time - timedelta(hours=8)
            }),
            # New users for current week to trigger user activity spike
            ("bot_spammer", {
                "name": "Bot Spammer",
                "email": "bot@spamservice.net",
                "current_credits": 200,
                "total_images_generated": 150,
                "created_at": current_time - timedelta(days=2),
                "updated_at": current_time - timedelta(hours=1),
                "last_login": current_time - timedelta(hours=1)
            }),
            ("new_enterprise", {
                "name": "Enterprise Client",
                "email": "admin@bigcorp.com",
                "current_credits": 1000,
                "total_images_generated": 85,
                "created_at": current_time - timedelta(days=3),
                "updated_at": current_time - timedelta(hours=3),
                "last_login": current_time - timedelta(hours=3)
            }),
            ("promo_user1", {
                "name": "Promo User One",
                "email": "promo1@campaign.com",
                "current_credits": 50,
                "total_images_generated": 25,
                "created_at": current_time - timedelta(days=4),
                "updated_at": current_time - timedelta(days=1),
                "last_login": current_time - timedelta(days=1)
            }),
            ("promo_user2", {
                "name": "Promo User Two",
                "email": "promo2@campaign.com",
                "current_credits": 45,
                "total_images_generated": 30,
                "created_at": current_time - timedelta(days=4),
                "updated_at": current_time - timedelta(days=1),
                "last_login": current_time - timedelta(days=1)
            }),
            ("viral_marketer", {
                "name": "Viral Marketer",
                "email": "viral@socialmedia.com",
                "current_credits": 15,
                "total_images_generated": 120,
                "created_at": current_time - timedelta(days=5),
                "updated_at": current_time - timedelta(hours=2),
                "last_login": current_time - timedelta(hours=2)
            })
        ]
        
        return [(user_id, UserModel(**data)) for user_id, data in users_data]
    
    def get_historical_generation_requests(self) -> List[Dict[str, Any]]:
        """Generate realistic historical generation requests for the last 3 weeks."""
        requests = []
        current_time = datetime.now()
        
        # Available options
        user_ids = ["arda", "havanur", "alex_designer", "sarah_artist", "mike_creative", 
                   "emma_photo", "david_dev", "lisa_marketing", "bot_spammer", 
                   "new_enterprise", "promo_user1", "promo_user2", "viral_marketer"]
        styles = ["realistic", "anime", "oil_painting", "sketch", "cyberpunk", "watercolor"]
        colors = ["vibrant", "monochrome", "pastel", "neon", "vintage"]
        sizes = ["512x512", "1024x1024", "1024x1792"]
        models = [AIModel.MODEL_A.value, AIModel.MODEL_B.value]
        
        # Size to credit mapping
        size_credits = {"512x512": 1, "1024x1024": 3, "1024x1792": 4}
        
        prompts = [
            "A serene mountain landscape at sunset",
            "Portrait of a futuristic robot",
            "Abstract geometric patterns",
            "A cozy coffee shop interior",
            "Fantasy dragon in a mystical forest",
            "Modern architecture building",
            "Vintage car on a country road",
            "Space station floating in cosmos",
            "Underwater coral reef scene",
            "Medieval castle on a hill",
            "City skyline at night",
            "Tropical beach paradise",
            "Steampunk mechanical device",
            "Elegant flower bouquet",
            "Post-apocalyptic wasteland"
        ]
        
        # Generate requests for each week with different patterns
        for week in range(4):  # Now including current week (week 0)
            if week == 0:  # Current week - ANOMALY WEEK
                # Skip current week generation here, we'll handle it separately
                continue
                
            week_start = current_time - timedelta(weeks=week)
            
            # Historical weeks pattern:
            # Week 1 (1 week ago): Normal activity - 25-30 requests
            # Week 2 (2 weeks ago): Low activity - 15-20 requests  
            # Week 3 (3 weeks ago): Low activity - 18-22 requests
            if week == 1:  # 1 week ago - normal
                num_requests = random.randint(25, 30)
                failure_rate = 0.05  # 5% failure rate
            elif week == 2:  # 2 weeks ago - low
                num_requests = random.randint(15, 20)
                failure_rate = 0.04  # 4% failure rate
            else:  # 3 weeks ago - low activity
                num_requests = random.randint(18, 22)
                failure_rate = 0.03  # 3% failure rate
            
            for i in range(num_requests):
                # Random timestamp within the week
                days_offset = random.uniform(0, 7)
                hours_offset = random.uniform(0, 24)
                request_time = week_start + timedelta(days=days_offset, hours=hours_offset)
                
                # Random request data
                user_id = random.choice(user_ids)
                style = random.choice(styles)
                color = random.choice(colors)
                size = random.choice(sizes)
                model = random.choice(models)
                prompt = random.choice(prompts)
                credits_deducted = size_credits[size]
                
                # Determine if request should fail
                should_fail = random.random() < failure_rate
                
                generation_id = str(uuid.uuid4())
                
                request_data = {
                    "id": generation_id,
                    "user_id": user_id,
                    "model": model,
                    "style": style,
                    "color": color,
                    "size": size,
                    "prompt": prompt,
                    "status": GenerationStatus.FAILED.value if should_fail else GenerationStatus.COMPLETED.value,
                    "credits_deducted": credits_deducted,
                    "created_at": request_time,
                    "updated_at": request_time + timedelta(seconds=random.randint(30, 300)),
                    "completed_at": request_time + timedelta(seconds=random.randint(30, 300))
                }
                
                if should_fail:
                    request_data["error_message"] = random.choice([
                        "Model timeout error",
                        "Content policy violation",
                        "Generation service unavailable",
                        "Invalid prompt parameters"
                    ])
                    request_data["image_url"] = None
                else:
                    request_data["image_url"] = f"https://storage.googleapis.com/feraset-images/{generation_id}.jpg"
                    request_data["error_message"] = None
                
                requests.append(request_data)
        
        # CURRENT WEEK - Generate anomalous patterns
        current_week_start = current_time - timedelta(days=current_time.weekday())
        
        # 1. Total request spike (2.5x multiplier) - average was ~20, so we need 50+
        # 2. Individual user spike (bot_spammer will make 15+ requests)
        # 3. High failure rate (Model B will have 20%+ failure rate)
        # 4. Credit consumption spike (3x multiplier) - lots of large images
        # 5. New user activity spike (5 new users this week)
        
        # Bot spammer making excessive requests (triggers user_request_spike)
        for i in range(18):  # 18 requests from single user
            days_offset = random.uniform(0, min(7, (current_time - current_week_start).days))
            request_time = current_week_start + timedelta(days=days_offset)
            
            # Bot prefers large, expensive images
            size = random.choice(["1024x1024", "1024x1792", "1024x1792"])  # More expensive sizes
            generation_id = str(uuid.uuid4())
            
            request_data = {
                "id": generation_id,
                "user_id": "bot_spammer",
                "model": AIModel.MODEL_B.value,  # Using Model B more
                "style": random.choice(styles),
                "color": random.choice(colors),
                "size": size,
                "prompt": "Generate spam content for marketing campaign",
                "credits_deducted": size_credits[size],
                "status": GenerationStatus.FAILED.value if random.random() < 0.25 else GenerationStatus.COMPLETED.value,
                "created_at": request_time,
                "updated_at": request_time + timedelta(seconds=random.randint(30, 120)),
                "completed_at": request_time + timedelta(seconds=random.randint(30, 120))
            }
            
            if request_data["status"] == GenerationStatus.FAILED.value:
                request_data["error_message"] = "Content policy violation - spam detected"
                request_data["image_url"] = None
            else:
                request_data["image_url"] = f"https://storage.googleapis.com/feraset-images/{generation_id}.jpg"
                request_data["error_message"] = None
                
            requests.append(request_data)
        
        # Enterprise client bulk generation (credit consumption spike)
        for i in range(25):  # 25 high-cost requests
            days_offset = random.uniform(0, min(7, (current_time - current_week_start).days))
            request_time = current_week_start + timedelta(days=days_offset)
            
            # Enterprise mostly uses expensive sizes
            size = "1024x1792" if i < 15 else "1024x1024"  # Mostly 4-credit images
            generation_id = str(uuid.uuid4())
            
            request_data = {
                "id": generation_id,
                "user_id": "new_enterprise",
                "model": AIModel.MODEL_A.value,
                "style": "realistic",  # Enterprise prefers realistic
                "color": random.choice(["vibrant", "monochrome"]),
                "size": size,
                "prompt": f"Professional business image for corporate presentation {i+1}",
                "credits_deducted": size_credits[size],
                "status": GenerationStatus.COMPLETED.value,  # Enterprise has low failure
                "created_at": request_time,
                "updated_at": request_time + timedelta(seconds=random.randint(60, 180)),
                "completed_at": request_time + timedelta(seconds=random.randint(60, 180)),
                "image_url": f"https://storage.googleapis.com/feraset-images/{generation_id}.jpg",
                "error_message": None
            }
            
            requests.append(request_data)
        
        # Other new users with moderate activity
        new_users = ["promo_user1", "promo_user2", "viral_marketer"]
        for user in new_users:
            num_user_requests = random.randint(4, 8)
            for i in range(num_user_requests):
                days_offset = random.uniform(0, min(7, (current_time - current_week_start).days))
                request_time = current_week_start + timedelta(days=days_offset)
                
                generation_id = str(uuid.uuid4())
                size = random.choice(sizes)
                
                # Higher failure rate for Model B
                is_model_b = random.random() < 0.4
                should_fail = (is_model_b and random.random() < 0.35) or random.random() < 0.1
                
                request_data = {
                    "id": generation_id,
                    "user_id": user,
                    "model": AIModel.MODEL_B.value if is_model_b else AIModel.MODEL_A.value,
                    "style": random.choice(styles),
                    "color": random.choice(colors),
                    "size": size,
                    "prompt": random.choice(prompts),
                    "credits_deducted": size_credits[size],
                    "status": GenerationStatus.FAILED.value if should_fail else GenerationStatus.COMPLETED.value,
                    "created_at": request_time,
                    "updated_at": request_time + timedelta(seconds=random.randint(30, 300)),
                    "completed_at": request_time + timedelta(seconds=random.randint(30, 300))
                }
                
                if should_fail:
                    request_data["error_message"] = random.choice([
                        "Model B service degradation",
                        "GPU memory allocation failed",
                        "Model timeout - high load"
                    ])
                    request_data["image_url"] = None
                else:
                    request_data["image_url"] = f"https://storage.googleapis.com/feraset-images/{generation_id}.jpg"
                    request_data["error_message"] = None
                    
                requests.append(request_data)
        
        # Add some normal activity from existing users in current week
        existing_users = ["arda", "alex_designer", "sarah_artist", "emma_photo"]
        for user in existing_users:
            num_user_requests = random.randint(2, 5)
            for i in range(num_user_requests):
                days_offset = random.uniform(0, min(7, (current_time - current_week_start).days))
                request_time = current_week_start + timedelta(days=days_offset)
                
                generation_id = str(uuid.uuid4())
                size = random.choice(sizes)
                
                request_data = {
                    "id": generation_id,
                    "user_id": user,
                    "model": random.choice(models),
                    "style": random.choice(styles),
                    "color": random.choice(colors),
                    "size": size,
                    "prompt": random.choice(prompts),
                    "credits_deducted": size_credits[size],
                    "status": GenerationStatus.COMPLETED.value,  # Normal users have good success
                    "created_at": request_time,
                    "updated_at": request_time + timedelta(seconds=random.randint(30, 180)),
                    "completed_at": request_time + timedelta(seconds=random.randint(30, 180)),
                    "image_url": f"https://storage.googleapis.com/feraset-images/{generation_id}.jpg",
                    "error_message": None
                }
                
                requests.append(request_data)
        
        return requests
    
    def get_historical_transactions(self, generation_requests: List[Dict[str, Any]]) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Generate historical transactions based on generation requests."""
        transactions = []
        
        for request in generation_requests:
            user_id = request["user_id"]
            generation_id = request["id"]
            credits = request["credits_deducted"]
            created_at = request["created_at"]
            
            # Deduction transaction
            deduction_id = str(uuid.uuid4())
            deduction_data = {
                "id": deduction_id,
                "type": TransactionType.DEDUCTION.value,
                "credits": credits,
                "generation_request_id": generation_id,
                "timestamp": created_at,
                "user_id": user_id,
                "description": f"Credit deduction for {request['style']} {request['size']} image generation"
            }
            transactions.append((user_id, deduction_id, deduction_data))
            
            # Refund transaction if request failed
            if request["status"] == GenerationStatus.FAILED.value:
                refund_id = str(uuid.uuid4())
                refund_data = {
                    "id": refund_id,
                    "type": TransactionType.REFUND.value,
                    "credits": credits,
                    "generation_request_id": generation_id,
                    "timestamp": request["completed_at"],
                    "user_id": user_id,
                    "description": f"Refund for failed generation: {request['error_message']}"
                }
                transactions.append((user_id, refund_id, refund_data))
        
        return transactions
    
    def get_historical_weekly_reports(self) -> List[Dict[str, Any]]:
        """Generate historical weekly reports for anomaly detection baseline."""
        reports = []
        current_time = datetime.now()
        
        # Generate reports for the past 3 weeks
        for week in range(1, 4):  # 1-3 weeks ago
            report_date = current_time - timedelta(weeks=week)
            start_date = report_date - timedelta(days=7)
            end_date = report_date
            
            # Mock statistics based on week - establishing a low baseline for anomaly detection
            if week == 1:  # 1 week ago - normal activity
                total_requests = 28
                completed_requests = 26
                failed_requests = 2
                net_credits_consumed = 75
                active_users = 6
            elif week == 2:  # 2 weeks ago - low
                total_requests = 18
                completed_requests = 17
                failed_requests = 1
                net_credits_consumed = 48
                active_users = 5
            else:  # 3 weeks ago - low activity
                total_requests = 20
                completed_requests = 19
                failed_requests = 1
                net_credits_consumed = 55
                active_users = 5
            
            report_id = f"weekly_report_{report_date.strftime('%Y_%m_%d')}"
            
            report_data = {
                "id": report_id,
                "generated_at": report_date,
                "report_type": "weekly",
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generation_stats": {
                    "total_requests": total_requests,
                    "completed_requests": completed_requests,
                    "failed_requests": failed_requests,
                    "pending_requests": 0,
                    "success_rate": round((completed_requests / total_requests * 100), 2),
                    "failure_rate": round((failed_requests / total_requests * 100), 2),
                    "style_breakdown": {
                        "realistic": int(total_requests * 0.25),
                        "anime": int(total_requests * 0.20),
                        "oil_painting": int(total_requests * 0.15),
                        "sketch": int(total_requests * 0.15),
                        "cyberpunk": int(total_requests * 0.15),
                        "watercolor": int(total_requests * 0.10)
                    },
                    "size_breakdown": {
                        "512x512": int(total_requests * 0.4),
                        "1024x1024": int(total_requests * 0.4),
                        "1024x1792": int(total_requests * 0.2)
                    }
                },
                "credit_stats": {
                    "total_credits_deducted": net_credits_consumed + (failed_requests * 2),
                    "total_credits_refunded": failed_requests * 2,
                    "net_credits_consumed": net_credits_consumed,
                    "total_transactions": total_requests * 2,  # deduction + potential refund
                    "deduction_transactions": total_requests,
                    "refund_transactions": failed_requests,
                    "average_credits_per_request": round(net_credits_consumed / total_requests, 2)
                },
                "user_stats": {
                    "active_users_count": active_users,
                    "active_users": self._get_active_users_for_week(week, active_users),
                    "user_request_breakdown": self._get_user_breakdown_for_week(week, total_requests, active_users),
                    "average_requests_per_user": round(total_requests / active_users, 2)
                },
                "model_performance": {
                    "Model A": {
                        "total_requests": int(total_requests * 0.6),
                        "completed": int(completed_requests * 0.6),
                        "failed": int(failed_requests * 0.6),
                        "success_rate": 95.0,
                        "failure_rate": 5.0
                    },
                    "Model B": {
                        "total_requests": int(total_requests * 0.4),
                        "completed": int(completed_requests * 0.4),
                        "failed": int(failed_requests * 0.4),
                        "success_rate": 94.5,
                        "failure_rate": 5.5
                    }
                }
            }
            
            reports.append(report_data)
        
        return reports
    
    def _get_active_users_for_week(self, week: int, count: int) -> List[str]:
        """Get realistic active users for a given historical week."""
        # Only existing users for historical weeks (no new users)
        existing_users = ["arda", "havanur", "alex_designer", "sarah_artist", 
                         "mike_creative", "emma_photo", "david_dev", "lisa_marketing"]
        
        # Select random subset of existing users
        return random.sample(existing_users, min(count, len(existing_users)))
    
    def _get_user_breakdown_for_week(self, week: int, total_requests: int, active_users: int) -> Dict[str, int]:
        """Generate realistic user request breakdown for a week."""
        users = self._get_active_users_for_week(week, active_users)
        breakdown = {}
        
        # Distribute requests among users with some variation
        remaining_requests = total_requests
        for i, user in enumerate(users):
            if i == len(users) - 1:
                # Last user gets remaining requests
                breakdown[user] = remaining_requests
            else:
                # Random distribution with reasonable bounds
                max_requests = min(8, remaining_requests - (len(users) - i - 1))
                requests = random.randint(1, max(1, max_requests))
                breakdown[user] = requests
                remaining_requests -= requests
        
        return breakdown
    
    def seed_all_collections(self) -> dict:
        """Seed all collections with validated data including historical data."""
        try:
            # Start with basic collections
            batch = self.db.batch()
            
            # Seed styles collection
            validated_styles = self.get_validated_styles()
            styles_collection = self.db.collection(Config.get_collection_name("styles"))
            for style_id, style_model in validated_styles:
                doc_ref = styles_collection.document(style_id)
                batch.set(doc_ref, style_model.dict())
            
            # Seed colors collection
            validated_colors = self.get_validated_colors()
            colors_collection = self.db.collection(Config.get_collection_name("colors"))
            for color_id, color_model in validated_colors:
                doc_ref = colors_collection.document(color_id)
                batch.set(doc_ref, color_model.dict())
                
            # Seed sizes collection
            validated_sizes = self.get_validated_sizes()
            sizes_collection = self.db.collection(Config.get_collection_name("sizes"))
            for size_id, size_model in validated_sizes:
                doc_ref = sizes_collection.document(size_id)
                batch.set(doc_ref, size_model.dict())
                
            # Seed test users
            validated_users = self.get_validated_users()
            users_collection = self.db.collection(Config.get_collection_name("users"))
            for user_id, user_model in validated_users:
                doc_ref = users_collection.document(user_id)
                batch.set(doc_ref, user_model.dict())
            
            # Commit basic collections first
            batch.commit()
            
            # Seed historical data in separate batches to avoid size limits
            historical_requests = self.get_historical_generation_requests()
            
            # Seed generation requests in batches
            generation_collection = self.db.collection(Config.get_collection_name("generation_requests"))
            batch_size = 100  # Firestore batch limit is 500, use 100 for safety
            
            for i in range(0, len(historical_requests), batch_size):
                batch = self.db.batch()
                batch_requests = historical_requests[i:i+batch_size]
                
                for request_data in batch_requests:
                    doc_ref = generation_collection.document(request_data["id"])
                    batch.set(doc_ref, request_data)
                
                batch.commit()
            
            # Seed historical transactions
            historical_transactions = self.get_historical_transactions(historical_requests)
            
            for i in range(0, len(historical_transactions), batch_size):
                batch = self.db.batch()
                batch_transactions = historical_transactions[i:i+batch_size]
                
                for user_id, transaction_id, transaction_data in batch_transactions:
                    doc_ref = (
                        users_collection
                        .document(user_id)
                        .collection("transactions")
                        .document(transaction_id)
                    )
                    batch.set(doc_ref, transaction_data)
                
                batch.commit()
            
            # Skip seeding historical reports - start with clean slate
            
            return {
                "success": True,
                "counts": {
                    "styles": len(validated_styles),
                    "colors": len(validated_colors),
                    "sizes": len(validated_sizes),  
                    "users": len(validated_users),
                    "generation_requests": len(historical_requests),
                    "transactions": len(historical_transactions)
                },
                "historical_data": {
                    "weeks_of_data": 4,
                    "total_requests": len(historical_requests),
                    "total_transactions": len(historical_transactions)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }