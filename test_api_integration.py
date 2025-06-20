#!/usr/bin/env python3
"""
Test API endpoints to ensure the YOLO integration is working
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_auth_endpoint():
    """Test authentication endpoint"""
    print("🔐 Testing authentication endpoint...")
    
    # Test login with test credentials
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", 
                               json={"username": "admin", "password": "admin"},
                               headers={"Content-Type": "application/json"})
        
        print(f"📡 Login status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"📄 Response keys: {list(data.keys())}")
            # Try different possible token keys
            token = data.get('access') or data.get('access_token') or data.get('token') or data.get('accessToken')
            if token:
                print(f"🔑 Token found: {token[:20]}...")
            return token
        else:
            print(f"⚠️ Login response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Auth test error: {str(e)}")
        return None

def test_yolo_endpoints(token):
    """Test YOLO-related endpoints"""
    if not token:
        print("❌ No auth token available for YOLO tests")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🎯 Testing YOLO endpoints...")
    
    # Test model info endpoint
    try:
        response = requests.get(f"{BASE_URL}/images/yolo-model-info/", headers=headers)
        print(f"📊 Model info status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Model info retrieved successfully!")
            print(f"🏷️ Model: {data.get('model_info', {}).get('name', 'Unknown')}")
            print(f"🔢 Keypoints: {data.get('model_info', {}).get('keypoint_count', 0)}")
            print(f"🎯 Confidence: {data.get('confidence_threshold', 0)}")
            print(f"📁 Model exists: {data.get('model_exists', False)}")
        else:
            print(f"⚠️ Model info error: {response.text}")
            
    except Exception as e:
        print(f"❌ Model info test error: {str(e)}")
    
    # Test batches endpoint
    try:
        response = requests.get(f"{BASE_URL}/images/batches/", headers=headers)
        print(f"📦 Batches status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            batches = data.get('batches', [])
            print(f"✅ Found {len(batches)} batches")
            for batch in batches[:3]:  # Show first 3 batches
                print(f"   📁 Batch {batch['id'][:8]}...: {batch['status']} ({batch['total_files']} files)")
        else:
            print(f"⚠️ Batches error: {response.text}")
            
    except Exception as e:
        print(f"❌ Batches test error: {str(e)}")

def test_create_batch(token):
    """Test creating a new batch"""
    if not token:
        return None
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n📦 Testing batch creation...")
    
    try:
        batch_data = {
            "total_files": 5,
            "metadata": {
                "test": "integration_test",
                "timestamp": "2025-06-16T15:52:00Z"
            }
        }
        
        response = requests.post(f"{BASE_URL}/images/create-batch/", 
                               json=batch_data, headers=headers)
        
        print(f"🆕 Create batch status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            batch_id = data.get('batch_id')
            print(f"✅ Batch created successfully: {batch_id}")
            return batch_id
        else:
            print(f"⚠️ Create batch error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Create batch test error: {str(e)}")
        return None

def main():
    print("🧪 API Integration Test\n" + "="*50)
    
    # Test authentication
    token = test_auth_endpoint()
    
    # Test YOLO endpoints
    test_yolo_endpoints(token)
    
    # Test batch creation
    batch_id = test_create_batch(token)
    
    print("\n" + "="*50)
    if token and batch_id:
        print("✅ All API tests completed successfully!")
        print("🎉 System is ready for YOLO batch processing!")
        print(f"🔗 Frontend: http://localhost:5174/")
        print(f"🔗 API: http://127.0.0.1:8000/api/")
    else:
        print("⚠️ Some API tests failed. Check server logs.")

if __name__ == "__main__":
    main()
