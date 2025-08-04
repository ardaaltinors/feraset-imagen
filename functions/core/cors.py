"""CORS utility functions for Firebase Functions."""

from typing import Dict, Callable
from firebase_functions import https_fn
from functools import wraps


def get_cors_headers() -> Dict[str, str]:
    """
    Get standard CORS headers for API responses.
    """
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600"
    }


def cors_enabled(func: Callable) -> Callable:
    """
    Decorator to add CORS headers to Firebase Function responses.
    """
    @wraps(func)
    def wrapper(req: https_fn.Request) -> https_fn.Response:
        # Handle preflight OPTIONS requests
        if req.method == 'OPTIONS':
            return https_fn.Response(
                "",
                status=204,
                headers=get_cors_headers()
            )
        
        # Call the original function
        response = func(req)
        
        # Add CORS headers to the response
        if isinstance(response, https_fn.Response):
            # Merge existing headers with CORS headers
            existing_headers = response.headers or {}
            new_headers = {**existing_headers, **get_cors_headers()}
            
            return https_fn.Response(
                response.data,
                status=response.status_code,
                headers=new_headers
            )
        
        return response
    
    return wrapper