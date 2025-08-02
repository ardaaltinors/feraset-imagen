"""Firebase Cloud Functions entry point with clean architecture."""

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
from controllers import SeedController, UserController, GenerationController, ReportController
from core import Config, setup_logging

# Setup logging
setup_logging()

# Firebase configuration
set_global_options(max_instances=Config.MAX_INSTANCES)
initialize_app()

# Initialize controllers
seed_controller = SeedController()
user_controller = UserController()
generation_controller = GenerationController()
report_controller = ReportController()


@https_fn.on_request()
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    """Example endpoint."""
    return https_fn.Response("Hello world!")


@https_fn.on_request()
def seed_database(req: https_fn.Request) -> https_fn.Response:
    """
    Seed the database with validated initial data.
    
    This endpoint populates Firestore collections with strictly validated:
    - Image generation styles (realistic, anime, etc.)
    - Color palettes (vibrant, monochrome, etc.) 
    - Available image sizes and pricing
    - Test user accounts
    
    All data is validated using Pydantic models before insertion.
    
    Returns:
        https_fn.Response: Success message or detailed validation errors
    """
    return seed_controller.seed_database(req)


@https_fn.on_request()
def validate_seed_data(req: https_fn.Request) -> https_fn.Response:
    """
    Validate seed data without inserting to database.
    
    Returns:
        https_fn.Response: Validation results
    """
    return seed_controller.validate_seed_data(req)


@https_fn.on_request()
def getUserCredits(req: https_fn.Request) -> https_fn.Response:
    """
    Get user's current credits and transaction history.
    
    Accepts userId as query parameter (GET) or in request body (POST).
    
    Returns:
        https_fn.Response: JSON with currentCredits and transactions array
    """
    return user_controller.get_user_credits(req)


@https_fn.on_request()
def validate_user(req: https_fn.Request) -> https_fn.Response:
    """
    Validate if a user exists in the system.
    
    Returns:
        https_fn.Response: User validation results
    """
    return user_controller.validate_user(req)


@https_fn.on_request()
def createGenerationRequest(req: https_fn.Request) -> https_fn.Response:
    """
    Create a new image generation request.
    
    Expected JSON payload:
    {
        "userId": "string",
        "model": "Model A" | "Model B", 
        "style": "realistic" | "anime" | "oil painting" | "sketch" | "cyberpunk" | "watercolor",
        "color": "vibrant" | "monochrome" | "pastel" | "neon" | "vintage",
        "size": "512x512" | "1024x1024" | "1024x1792",
        "prompt": "string"
    }
    
    Returns:
        https_fn.Response: JSON with generationRequestId, deductedCredits, imageUrl
    """
    return generation_controller.create_generation_request(req)


@https_fn.on_request()
def getGenerationRequest(req: https_fn.Request) -> https_fn.Response:
    """
    Get generation request details by ID.
    
    Accepts generationRequestId as query parameter or in request body.
    
    Returns:
        https_fn.Response: Generation request details
    """
    return generation_controller.get_generation_request(req)


@https_fn.on_request()
def scheduleWeeklyReport(req: https_fn.Request) -> https_fn.Response:
    """
    Generate weekly usage and credit consumption report.
    
    This endpoint is designed to be triggered by a scheduler.
    No input parameters required.
    
    Returns:
        https_fn.Response: JSON with reportStatus and analytics data
    """
    return report_controller.schedule_weekly_report(req)