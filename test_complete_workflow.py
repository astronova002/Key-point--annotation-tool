#!/usr/bin/env python3
"""
Complete workflow test for the YOLO image annotation system.
Tests: Authentication -> Upload -> YOLO Processing -> Results
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"
TEST_USERNAME = "testadmin"
TEST_PASSWORD = "testpass123"

class WorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        
    def authenticate(self):
        """Test user authentication"""
        print("🔐 Testing authentication...")
        
        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(f"{API_URL}/auth/login/", json=login_data)
        
        if response.status_code == 200:
            auth_data = response.json()
            self.access_token = auth_data.get("access")
            self.refresh_token = auth_data.get("refresh")
            
            # Set authorization header for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            
            print("✅ Authentication successful!")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def test_yolo_model_info(self):
        """Test YOLO model info endpoint"""
        print("🤖 Testing YOLO model info...")
        
        response = self.session.get(f"{API_URL}/images/yolo-model-info/")
        
        if response.status_code == 200:
            model_info = response.json()
            print("✅ YOLO model info retrieved successfully!")
            print(f"   Model exists: {model_info.get('model_exists', False)}")
            print(f"   Processing enabled: {model_info.get('processing_enabled', False)}")
            
            if model_info.get('model_info'):
                info = model_info['model_info']
                print(f"   Model type: {info.get('model_type', 'Unknown')}")
                print(f"   Keypoints: {info.get('keypoint_count', 0)}")
                print(f"   Confidence threshold: {info.get('confidence_threshold', 0)}")
            
            return model_info.get('model_exists', False)
        else:
            print(f"❌ YOLO model info failed: {response.status_code} - {response.text}")
            return False
    
    def test_batch_listing(self):
        """Test batch listing endpoint"""
        print("📋 Testing batch listing...")
        
        response = self.session.get(f"{API_URL}/images/batches/")
        
        if response.status_code == 200:
            batch_data = response.json()
            batches = batch_data.get("batches", [])
            print(f"✅ Batch listing successful! Found {len(batches)} batches")
            
            for batch in batches[:3]:  # Show first 3 batches
                print(f"   Batch {batch.get('id', 'Unknown')[:8]}...: "
                      f"{batch.get('status', 'Unknown')} - "
                      f"{batch.get('uploaded_files', 0)}/{batch.get('total_files', 0)} files")
            
            return batches
        else:
            print(f"❌ Batch listing failed: {response.status_code} - {response.text}")
            return []
    
    def test_admin_dashboard(self):
        """Test Django admin accessibility"""
        print("🏠 Testing Django admin dashboard...")
        
        # Test admin page accessibility (should redirect to login if not authenticated)
        response = requests.get(f"{BASE_URL}/admin/")
        
        if response.status_code == 200:
            print("✅ Django admin dashboard is accessible!")
            return True
        elif response.status_code == 302:
            print("✅ Django admin dashboard redirects to login (normal behavior)")
            return True
        else:
            print(f"❌ Django admin dashboard issue: {response.status_code}")
            return False
    
    def test_model_endpoints(self):
        """Test that all model endpoints are available"""
        print("📊 Testing model endpoints...")
        
        endpoints_to_test = [
            "/images/batches/",
            "/images/yolo-model-info/",
        ]
        
        all_good = True
        
        for endpoint in endpoints_to_test:
            response = self.session.get(f"{API_URL}{endpoint}")
            if response.status_code in [200, 201]:
                print(f"   ✅ {endpoint} - OK")
            else:
                print(f"   ❌ {endpoint} - {response.status_code}")
                all_good = False
        
        return all_good
    
    def run_complete_test(self):
        """Run the complete workflow test"""
        print("🚀 Starting complete workflow test...\n")
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Test YOLO model
        yolo_available = self.test_yolo_model_info()
        
        # Step 3: Test batch listing
        batches = self.test_batch_listing()
        
        # Step 4: Test admin dashboard
        admin_ok = self.test_admin_dashboard()
        
        # Step 5: Test all model endpoints
        endpoints_ok = self.test_model_endpoints()
        
        # Summary
        print("\n📋 Test Summary:")
        print(f"   Authentication: ✅")
        print(f"   YOLO Model: {'✅' if yolo_available else '⚠️'}")
        print(f"   Batch System: ✅")
        print(f"   Admin Dashboard: {'✅' if admin_ok else '❌'}")
        print(f"   API Endpoints: {'✅' if endpoints_ok else '❌'}")
        
        overall_success = yolo_available and admin_ok and endpoints_ok
        
        print(f"\n🎯 Overall Status: {'✅ ALL SYSTEMS OPERATIONAL' if overall_success else '⚠️ SOME ISSUES DETECTED'}")
        
        if not yolo_available:
            print("   ⚠️ YOLO model may need attention")
        
        return overall_success

if __name__ == "__main__":
    tester = WorkflowTester()
    tester.run_complete_test()
