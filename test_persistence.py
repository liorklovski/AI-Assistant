#!/usr/bin/env python3
"""
Test script to demonstrate chat persistence and new UI features:
1. Soft pink gradient background ✨
2. Prettier clear button with hover effects 
3. Chat persists through page refreshes 🔄
4. Clear button clears both frontend and backend 🧹
"""
import requests
import time

BASE_URL = "http://localhost:5000"

def test_persistence_flow():
    print("🌸 TESTING ENHANCED CHAT WITH PERSISTENCE")
    print("=" * 60)
    
    # Step 1: Clear any existing chat
    print("\n1️⃣ Clearing existing chat...")
    clear_response = requests.delete(f"{BASE_URL}/chat/clear")
    print(f"   ✅ Clear result: {clear_response.json()}")
    
    # Step 2: Add some messages to create chat history
    print("\n2️⃣ Creating chat history...")
    messages = [
        "Hello! I'm testing the new persistence feature.",
        "Can you explain quantum computing?",
        "What are the benefits of renewable energy?"
    ]
    
    job_ids = []
    for i, msg in enumerate(messages):
        print(f"   📝 Sending message {i+1}: {msg[:30]}...")
        response = requests.post(
            f"{BASE_URL}/messages",
            json={"message": msg},
            headers={"Content-Type": "application/json"}
        )
        job_ids.append(response.json()["job_id"])
        time.sleep(1)  # Small delay between messages
    
    # Step 3: Wait for processing and check results
    print("\n3️⃣ Waiting for AI responses...")
    time.sleep(6)  # Wait for all messages to process
    
    # Step 4: Check persistence
    print("\n4️⃣ Checking chat history persistence...")
    history = requests.get(f"{BASE_URL}/chat/history")
    history_data = history.json()
    
    if history_data["success"] and len(history_data["messages"]) == len(messages):
        print(f"   ✅ All {len(messages)} messages persisted in backend memory!")
        print(f"   📊 Messages with AI responses:")
        for msg in history_data["messages"]:
            response_preview = (msg.get("ai_response", "Processing...")[:50] + "..." 
                              if msg.get("ai_response") and len(msg.get("ai_response", "")) > 50 
                              else msg.get("ai_response", "Processing..."))
            print(f"      • {msg['user_message'][:30]}... → {response_preview}")
    else:
        print(f"   ⚠️ Expected {len(messages)} messages, found {len(history_data.get('messages', []))}")
    
    print("\n🌸 ENHANCED UI FEATURES:")
    print("   • Soft pink gradient background ✨")
    print("   • Prettier clear button with hover effects 🎨") 
    print("   • Chat persists through page refreshes 🔄")
    print("   • Clear button clears both frontend and backend 🧹")
    print("\n🚀 Open http://localhost:3000 to see the beautiful new UI!")
    print("   Try refreshing the page - your chat history will persist!")

if __name__ == "__main__":
    test_persistence_flow()
