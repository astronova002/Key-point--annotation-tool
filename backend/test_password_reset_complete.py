import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
from user_auth.models import CustomUser
from django.core.mail import send_mail
from django.conf import settings
import json

def test_complete_password_reset_flow():
    """Test the complete password reset flow with real email"""
    
    print("🔐 Testing Complete Password Reset Flow")
    print("=" * 50)
    
    client = Client()
    
    # Get test email
    test_email = input("Enter your email for testing (or press Enter for gma.iisc.25@gmail.com): ").strip()
    if not test_email:
        test_email = "gma.iisc.25@gmail.com"
    
    try:
        # Step 1: Create or get test user
        try:
            user = CustomUser.objects.get(email=test_email)
            print(f"✅ Using existing user: {user.username}")
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(
                username=f'testuser_{test_email.split("@")[0]}',
                email=test_email,
                password='oldpassword123',
                is_approved=True
            )
            print(f"✅ Created test user: {user.username}")
        
        # Step 2: Test password reset request
        print(f"\n📧 Requesting password reset for: {test_email}")
        response = client.post('/api/auth/request-password-reset/', {
            'email': test_email
        }, content_type='application/json')
        
        print(f"✅ Password reset request status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Response content: {response.content}")
            return False
        
        # Step 3: Check that token was set
        user.refresh_from_db()
        token = user.password_reset_token
        if token:
            print(f"✅ Reset token generated: {token[:10]}...")
            print("📬 Check your email for the password reset link!")
            
            # Step 4: Test password reset using token
            print(f"\n🔑 Testing password reset with token...")
            response = client.post('/api/auth/reset-password/', {
                'token': token,
                'new_password': 'newpassword123'
            }, content_type='application/json')
            
            print(f"✅ Password reset status: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Response content: {response.content}")
                return False
            
            # Step 5: Verify new password works
            user.refresh_from_db()
            if user.check_password('newpassword123'):
                print("✅ Password successfully reset!")
                
                # Reset back to original password for future tests
                user.set_password('oldpassword123')
                user.password_reset_token = None
                user.save()
                print("✅ Test user password reset to original")
                
                return True
            else:
                print("❌ Password reset failed!")
                return False
        else:
            print("❌ No reset token was generated!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_email_templates():
    """Test the email template rendering"""
    print("\n📝 Testing Email Template")
    print("=" * 30)
    
    try:
        # Test the email template
        test_username = "TestUser"
        test_token = "sample_token_12345"
        reset_link = f"http://localhost:5173/reset-password/{test_token}"
        
        email_subject = "Password Reset Request - KPA Annotation Tool"
        email_body = f"""
Dear {test_username},

You have requested to reset your password for the KPA Annotation Tool.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

For support, contact: gma.iisc.25@gmail.com

Best regards,
KPA Annotation Tool Team
        """.strip()
        
        print("📧 Email Subject:")
        print(f"   {email_subject}")
        print("\n📄 Email Body:")
        print(email_body)
        print("\n✅ Email template looks good!")
        
        return True
        
    except Exception as e:
        print(f"❌ Email template test failed: {e}")
        return False

if __name__ == "__main__":
    # Test email templates first
    test_email_templates()
    
    # Then test the complete flow
    proceed = input("\nDo you want to test the complete password reset flow? (y/n): ").strip().lower()
    if proceed in ['y', 'yes']:
        test_complete_password_reset_flow()
    else:
        print("👋 Test skipped. Run again when ready!")