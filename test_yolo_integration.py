#!/usr/bin/env python3
"""
Test script to verify YOLO processor integration
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/run/media/vivek/Python/IISC/Job/GMM_ANOTATION_TOOL/KPA/backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from images.yolo_processor import YOLOProcessor
from django.conf import settings

def test_yolo_processor():
    """Test the YOLO processor functionality"""
    print("🔄 Testing YOLO Processor Integration...")
    
    # Check settings
    print(f"📁 Model path: {getattr(settings, 'YOLO_MODEL_PATH', 'Not set')}")
    print(f"🎯 Keypoint count: {getattr(settings, 'YOLO_KEYPOINT_COUNT', 'Not set')}")
    print(f"🔍 Confidence threshold: {getattr(settings, 'YOLO_CONFIDENCE_THRESHOLD', 'Not set')}")
    
    # Check if model file exists
    model_path = getattr(settings, 'YOLO_MODEL_PATH', None)
    if model_path and os.path.exists(model_path):
        print(f"✅ Model file exists: {model_path}")
        print(f"📊 Model size: {os.path.getsize(model_path) / (1024*1024):.2f} MB")
    else:
        print(f"❌ Model file not found: {model_path}")
        return False
    
    try:
        # Initialize YOLO processor
        print("🚀 Initializing YOLO processor...")
        processor = YOLOProcessor(use_26_keypoints=True)
        
        print(f"✅ Processor initialized successfully!")
        print(f"🏷️  Using model: {os.path.basename(processor.model_path)}")
        print(f"🔢 Keypoint labels: {len(processor.keypoint_labels)} points")
        print(f"🔗 Connections: {len(processor.connections)} connections")
        
        # Display some keypoint labels
        print("📍 First 10 keypoint labels:")
        for i, label in enumerate(processor.keypoint_labels[:10]):
            print(f"   {i}: {label}")
        
        if len(processor.keypoint_labels) > 10:
            print(f"   ... and {len(processor.keypoint_labels) - 10} more")
            
        return True
        
    except Exception as e:
        print(f"❌ Error initializing YOLO processor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_model_info_endpoint():
    """Test the model info API endpoint"""
    print("\n🌐 Testing YOLO Model Info API...")
    
    import requests
    
    try:
        # You would need a valid token for this test
        # For now, just test if the endpoint exists
        response = requests.get('http://127.0.0.1:8000/api/images/yolo-model-info/')
        print(f"📡 API endpoint status: {response.status_code}")
        
        if response.status_code == 401:
            print("🔐 Authentication required (expected)")
        elif response.status_code == 200:
            print("✅ API endpoint accessible")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Django server")
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")

if __name__ == "__main__":
    print("🧪 YOLO Integration Test\n" + "="*50)
    
    success = test_yolo_processor()
    test_model_info_endpoint()
    
    print("\n" + "="*50)
    if success:
        print("✅ YOLO integration test completed successfully!")
        print("🎉 Ready for batch processing!")
    else:
        print("❌ YOLO integration test failed!")
        print("🔧 Please check the model file and configuration.")
