#!/usr/bin/env python3
"""
Test script for the asynchronous image generation API.

This script demonstrates the new async workflow:
1. Create generation request (immediate response)
2. Poll for status updates
3. Get final result
"""

import requests
import json
import time

# Firebase emulator endpoints
BASE_URL = "http://127.0.0.1:5551/feraset-imagen/us-central1"

def test_async_generation():
    """Test the complete async generation workflow."""
    print("🚀 Testing Asynchronous Image Generation API")
    print("=" * 50)
    
    # Step 1: Create generation request
    print("\n1️⃣ Creating generation request...")
    
    payload = {
        "userId": "arda",
        "model": "Model A",
        "style": "realistic",
        "color": "vibrant", 
        "size": "1024x1024",
        "prompt": "A beautiful sunset over mountains"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/createGenerationRequest",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 202:
            print("✅ Request queued successfully!")
            generation_id = response.json()["generationRequestId"]
        else:
            print("❌ Request failed")
            return
            
    except Exception as e:
        print(f"❌ Error creating request: {str(e)}")
        return
    
    # Step 2: Poll for status updates
    print(f"\n2️⃣ Polling status for generation: {generation_id}")
    
    max_polls = 10
    poll_count = 0
    
    while poll_count < max_polls:
        try:
            status_response = requests.get(
                f"{BASE_URL}/getGenerationStatus",
                params={"generationRequestId": generation_id}
            )
            
            print(f"Poll {poll_count + 1}: Status {status_response.status_code}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data["status"]
                progress = status_data.get("progress", 0)
                
                print(f"   Status: {current_status} | Progress: {progress}%")
                
                if current_status in ["completed", "failed"]:
                    print(f"\n✅ Final result:")
                    print(json.dumps(status_data, indent=2))
                    
                    if current_status == "completed":
                        print(f"🖼️  Image URL: {status_data.get('imageUrl')}")
                    else:
                        print(f"❌ Error: {status_data.get('error_message')}")
                    break
            else:
                print(f"   ❌ Status check failed: {status_response.text}")
                
        except Exception as e:
            print(f"   ❌ Error checking status: {str(e)}")
        
        poll_count += 1
        if poll_count < max_polls:
            print("   ⏳ Waiting 2 seconds...")
            time.sleep(2)
    
    if poll_count >= max_polls:
        print(f"\n⏰ Timeout after {max_polls} polls")

def test_user_credits():
    """Test user credits endpoint."""
    print("\n💰 Testing User Credits API")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/getUserCredits?userId=arda")
        print(f"Status: {response.status_code}")
        print(f"Credits: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_background_worker():
    """Test the background worker endpoint directly."""
    print("\n⚙️  Testing Background Worker API")
    print("-" * 35)
    
    # Simulate a Cloud Tasks payload
    task_payload = {
        "generation_request_id": "test-direct-worker",
        "user_id": "arda",
        "model": "Model A",
        "style": "anime",
        "color": "pastel",
        "size": "512x512", 
        "prompt": "A cute anime character in a garden",
        "priority": "normal",
        "retry_count": 0
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/processImageGeneration",
            json=task_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🧪 Firebase Functions Async API Test Suite")
    print("==========================================")
    
    # Test user credits first
    test_user_credits()
    
    # Test the main async workflow
    test_async_generation()
    
    # Test background worker directly
    test_background_worker()
    
    print("\n🏁 Test completed!")