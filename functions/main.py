"""Firebase Cloud Functions entry point with clean architecture."""

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
from controllers import SeedController, UserController, GenerationController, ReportController
from core import Config, setup_logging, cors_enabled

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
@cors_enabled
def seed_database(req: https_fn.Request) -> https_fn.Response:
    """
    Seed the database with initial data.
    """
    return seed_controller.seed_database(req)


@https_fn.on_request()
@cors_enabled
def getUserCredits(req: https_fn.Request) -> https_fn.Response:
    """
    Get user's current credits and transaction history.
    """
    return user_controller.get_user_credits(req)


@https_fn.on_request()
@cors_enabled
def validate_user(req: https_fn.Request) -> https_fn.Response:
    """
    Validate if a user exists in the system.
    """
    return user_controller.validate_user(req)


@https_fn.on_request()
@cors_enabled
def createGenerationRequest(req: https_fn.Request) -> https_fn.Response:
    """
    Create a new image generation request.
    """
    return generation_controller.create_generation_request(req)




@https_fn.on_request()
@cors_enabled
def getGenerationStatus(req: https_fn.Request) -> https_fn.Response:
    """
    Get the current status of a generation request.
    
    Accepts generationRequestId as query parameter or in request body.
    """
    return generation_controller.get_generation_status(req)


@https_fn.on_request()
@cors_enabled
def processImageGeneration(req: https_fn.Request) -> https_fn.Response:
    """
    Background worker function for processing image generation tasks from Cloud Tasks.
    
    This function is triggered by Cloud Tasks queue and should not be called directly.
    It processes AI image generation in the background.
    """
    return generation_controller.process_background_generation(req)


@https_fn.on_request()
@cors_enabled
def scheduleWeeklyReport(req: https_fn.Request) -> https_fn.Response:
    """
    Generate weekly usage and credit consumption report.
    
    This endpoint is designed to be triggered by a scheduler.
    TODO: will be updated with @scheduler_fn
    """
    return report_controller.schedule_weekly_report(req)