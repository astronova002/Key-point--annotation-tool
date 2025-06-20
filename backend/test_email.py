import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client, override_settings
from user_auth.models import CustomUser
from django.core.mail import send_mail
import json

def test_email_configuration():
    """Test email configuration"""
    print("🔧 Testing Email Configuration")
    print("=" * 40)
    
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'✅ SET' if settings.EMAIL_HOST_PASSWORD else '❌ NOT SET'}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if not settings.EMAIL_HOST_PASSWORD:
        print("❌ EMAIL_HOST_PASSWORD is not set!")
        return False
    
    if len(settings.EMAIL_HOST_PASSWORD) != 16:
        print(f"⚠️ App password should be 16 characters, got {len(settings.EMAIL_HOST_PASSWORD)}")
        return False
    
    print("✅ Email configuration looks good!")
    return True

def test_gmail_integration():
    """Test Gmail integration with real email"""
    print("\n📧 Testing Gmail Integration")
    print("=" * 40)
    
    try:
        # Use the correct email from settings
        test_email = settings.EMAIL_HOST_USER  # vivekbs.work.iisc@gmail.com
        
        print(f"📨 Sending test email to: {test_email}")
        
        send_mail(
            subject='🧪 KPA System - Gmail Integration Test',
            message='''
Hello!

This is a test email from the KPA Annotation Tool to verify Gmail integration.

✅ If you receive this email, the Gmail SMTP configuration is working correctly!

Email Configuration:
- Host: smtp.gmail.com  
- Port: 587
- TLS: Enabled
- From: vivekbs.work.iisc@gmail.com

Best regards,
KPA Annotation Tool Team
            '''.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        print("✅ Email sent successfully!")
        print("📬 Check your inbox for the test email")
        return True
        
    except Exception as e:
        print(f"❌ Gmail integration failed: {e}")
        print("\n🔧 Possible issues:")
        print("1. App password might be incorrect")
        print("2. 2FA might not be enabled on Gmail account") 
        print("3. Gmail account might be temporarily locked")
        print("4. Try generating a new App Password")
        return False

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1', 'vivekbs.work.iisc'])
def test_password_reset_flow():
    """Test complete password reset flow"""
    print("\n🔐 Testing Complete Password Reset Flow")
    print("=" * 40)
    
    client = Client()
    test_email = "vivekbs.work.iisc@gmail.com"
    
    try:
        # Get or create test user
        user, created = CustomUser.objects.get_or_create(
            email=test_email,
            defaults={
                'username': 'vivekbs_test',
                'is_approved': True
            }
        )
        
        if created:
            user.set_password('testpassword123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing user: {user.username}")
        
        # Test password reset request
        print(f"\n📧 Requesting password reset for: {test_email}")
        
        response = client.post('/api/auth/request-password-reset/', 
            data=json.dumps({'email': test_email}),
            content_type='application/json'
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Password reset request successful!")
            
            # Check if token was generated
            user.refresh_from_db()
            if user.password_reset_token:
                print(f"✅ Reset token generated: {user.password_reset_token[:10]}...")
                print("📧 Password reset email should be sent to your inbox!")
                
                # Test token usage
                print("\n🔑 Testing password reset with token...")
                reset_response = client.post('/api/auth/reset-password/',
                    data=json.dumps({
                        'token': user.password_reset_token,
                        'new_password': 'newtestpassword123'
                    }),
                    content_type='application/json'
                )
                
                print(f"Reset Response Status: {reset_response.status_code}")
                if reset_response.status_code == 200:
                    print("✅ Password reset successful!")
                    
                    # Verify password changed
                    user.refresh_from_db()
                    if user.check_password('newtestpassword123'):
                        print("✅ Password correctly updated!")
                        
                        # Reset back for future tests
                        user.set_password('testpassword123')
                        user.password_reset_token = None
                        user.save()
                        print("✅ Test user reset to original state")
                        
                        return True
                    else:
                        print("❌ Password was not updated")
                else:
                    print(f"❌ Password reset failed: {reset_response.content}")
            else:
                print("❌ No reset token was generated")
        else:
            print(f"❌ Password reset request failed:")
            print(f"Status: {response.status_code}")
            print(f"Content: {response.content}")
            
    except Exception as e:
        print(f"❌ Password reset flow failed: {e}")
        import traceback
        traceback.print_exc()
        
    return False

def run_complete_test():
    """Run all tests"""
    print("🧪 KPA Password Reset System - Complete Test")
    print("=" * 50)
    
    # Test 1: Configuration
    if not test_email_configuration():
        print("\n❌ Email configuration failed. Please fix before continuing.")
        return
    
    # Test 2: Gmail Integration
    gmail_works = test_gmail_integration()
    
    if not gmail_works:
        print("\n❌ Gmail integration failed. Please fix before testing API.")
        return
    
    # Test 3: Complete Password Reset Flow
    print("\n" + "="*50)
    flow_works = test_password_reset_flow()
    
    if flow_works:
        print("\n🎉 SUCCESS! Complete password reset system is working!")
        print("📧 Check your email inbox for the password reset email.")
        print("\n✅ All components verified:")
        print("  - Gmail SMTP integration")
        print("  - Password reset request API")
        print("  - Token generation")
        print("  - Password reset confirmation API")
        print("  - Email sending")
    else:
        print("\n⚠️ API flow has issues. Check the logs above.")

if __name__ == "__main__":
    run_complete_test()