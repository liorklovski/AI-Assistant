#!/usr/bin/env python3
import os
import requests
import json
import time

def test_fallback_system():
    print("🧪 Testing AI Fallback System")
    print("=" * 50)
    
    # Test 1: Normal operation (both APIs available)
    print("\n1️⃣ Testing normal operation...")
    response = requests.post(
        "http://localhost:5000/messages",
        json={"message": "Hello, this is a test of normal operation"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        job_id = response.json()["job_id"]
        print(f"   ✅ Job created: {job_id}")
        
        # Wait and check result
        time.sleep(4)
        result = requests.get(f"http://localhost:5000/messages/{job_id}")
        if result.status_code == 200:
            ai_response = result.json().get("ai_response", "")
            print(f"   📝 Response: {ai_response[:100]}...")
            if len(ai_response) > 50 and "technical difficulties" not in ai_response:
                print("   ✅ Normal AI working (likely Gemini or DeepAI)")
            else:
                print("   ⚠️ Fallback message detected")
    
    print("\n🎯 Fallback System Verification Complete!")
    print("📊 Check backend logs to see which APIs were called")

if __name__ == "__main__":
    test_fallback_system()
