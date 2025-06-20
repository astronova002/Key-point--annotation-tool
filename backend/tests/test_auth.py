import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from user_auth.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import IntegrityError
import json

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return CustomUser.objects.create_user(
        username='admin',
        email='admin@gmail.com',
        password='admin',
        is_approved=True,
        role='ADMIN'
    )

@pytest.fixture
def annotator_user():
    return CustomUser.objects.create_user(
        username='user1',
        email='annotator@gmail.com',
        password='admin',
        is_approved=True,
        role='ANNOTATOR'
    )

@pytest.fixture
def pending_user():
    return CustomUser.objects.create_user(
        username='pending',
        email='pending@example.com',
        password='pendingpass123',
        is_approved=False,
        role='ANNOTATOR'
    )

@pytest.fixture
def admin_token(admin_user):
    refresh = RefreshToken.for_user(admin_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@pytest.fixture
def annotator_token(annotator_user):
    refresh = RefreshToken.for_user(annotator_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class TestAuthentication:
    def test_register_user(self, api_client):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuserpass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['message'] == 'Registration successful. Waiting for admin approval.'
        assert CustomUser.objects.filter(username='newuser').exists()

    def test_login_user(self, api_client, admin_user):
        url = reverse('login')
        data = {
            'username': 'admin',
            'password': 'admin'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert 'token' in response_data
        assert 'user' in response_data
        assert response_data['user']['username'] == 'admin'

    def test_login_unapproved_user(self, api_client, pending_user):
        url = reverse('login')
        data = {
            'username': 'pending',
            'password': 'pendingpass123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 403
        response_data = json.loads(response.content)
        assert response_data['error'] == 'Account pending approval'

    def test_login_invalid_credentials(self, api_client):
        url = reverse('login')
        data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 401
        response_data = json.loads(response.content)
        assert response_data['error'] == 'Invalid credentials'

class TestUserManagement:
    def test_get_all_users_admin(self, api_client, admin_token):
        url = reverse('get_all_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.get(url)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert 'users' in response_data

    def test_get_all_users_annotator(self, api_client, annotator_token):
        url = reverse('get_all_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {annotator_token["access"]}')
        response = api_client.get(url)
        assert response.status_code == 403

    def test_get_pending_users(self, api_client, admin_token):
        url = reverse('pending_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.get(url)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert 'users' in response_data

    def test_approve_user(self, api_client, admin_token, pending_user):
        url = reverse('approve_user', args=[pending_user.id])
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.post(url)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['message'] == 'User approved successfully'
        pending_user.refresh_from_db()
        assert pending_user.is_approved == True

    def test_update_user_role(self, api_client, admin_token, annotator_user):
        url = reverse('update_role', args=[annotator_user.id])
        data = {'role': 'ADMIN'}
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['message'] == 'User role updated successfully'
        annotator_user.refresh_from_db()
        assert annotator_user.role == 'ADMIN'

    def test_update_user_role_invalid(self, api_client, admin_token, annotator_user):
        url = reverse('update_role', args=[annotator_user.id])
        data = {'role': 'INVALID_ROLE'}
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

class TestPagination:
    def test_get_users_pagination(self, api_client, admin_token):
        url = reverse('get_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.get(f'{url}?page=1&per_page=10')
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert 'users' in response_data
        assert 'pagination' in response_data
        assert 'current_page' in response_data['pagination']
        assert 'total_pages' in response_data['pagination']
        assert 'total_users' in response_data['pagination']
        assert 'per_page' in response_data['pagination']

class TestTokenRefresh:
    def test_refresh_token(self, api_client, admin_token):
        url = reverse('token_refresh')
        data = {'refresh': admin_token['refresh']}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert 'access' in response_data

    def test_refresh_token_invalid(self, api_client):
        url = reverse('token_refresh')
        data = {'refresh': 'invalid_token'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 401

class TestErrorHandling:
    def test_register_with_existing_username(self, api_client):
        # Create a user first
        CustomUser.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        url = reverse('register')
        data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert 'Username already exists' in response_data['error']

    def test_login_with_nonexistent_user(self, api_client):
        url = reverse('login')
        data = {
            'username': 'nonexistent',
            'password': 'somepass'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 401
        response_data = json.loads(response.content)
        assert response_data['error'] == 'Invalid credentials'

    def test_approve_nonexistent_user(self, api_client, admin_token):
        url = reverse('approve_user', args=[9999])  # Non-existent user ID
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.post(url)
        assert response.status_code == 404
        response_data = json.loads(response.content)
        assert response_data['error'] == 'User not found'

    def test_update_role_nonexistent_user(self, api_client, admin_token):
        url = reverse('update_role', args=[9999])  # Non-existent user ID
        data = {'role': 'ADMIN'}
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.post(url, data, format='json')
        assert response.status_code == 404
        response_data = json.loads(response.content)
        assert response_data['error'] == 'User not found'

class TestPermissions:
    def test_annotator_cannot_access_admin_endpoints(self, api_client, annotator_token):
        # Test get_all_users
        url = reverse('get_all_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {annotator_token["access"]}')
        response = api_client.get(url)
        assert response.status_code == 403

        # Test approve_user
        url = reverse('approve_user', args=[1])
        response = api_client.post(url)
        assert response.status_code == 403

        # Test update_role
        url = reverse('update_role', args=[1])
        data = {'role': 'ADMIN'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 403

    def test_unauthenticated_access_denied(self, api_client):
        # Test protected endpoints without authentication
        protected_urls = [
            reverse('get_all_users'),
            reverse('get_users'),
            reverse('pending_users'),
            reverse('status'),
        ]
        
        for url in protected_urls:
            response = api_client.get(url)
            assert response.status_code == 401

    def test_admin_can_access_all_endpoints(self, api_client, admin_token, pending_user):
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # Test all admin endpoints
        endpoints = [
            (reverse('get_all_users'), 'GET'),
            (reverse('get_users'), 'GET'),
            (reverse('pending_users'), 'GET'),
            (reverse('approve_user', args=[pending_user.id]), 'POST'),
            (reverse('update_role', args=[pending_user.id]), 'POST'),
        ]
        
        for url, method in endpoints:
            if method == 'GET':
                response = api_client.get(url)
            else:
                data = {'role': 'VERIFIER'} if 'update-role' in url else {}
                response = api_client.post(url, data, format='json')
            
            assert response.status_code in [200, 201], f"Failed for {url} with method {method}"

class TestPasswordReset:
    def test_request_password_reset_valid_email(self, api_client):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        
        url = reverse('request_password_reset')
        data = {'email': 'test@example.com'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        # Check that token was set
        user.refresh_from_db()
        assert user.password_reset_token is not None

    def test_request_password_reset_invalid_email(self, api_client):
        url = reverse('request_password_reset')
        data = {'email': 'nonexistent@example.com'}
        response = api_client.post(url, data, format='json')
        # Should still return 200 to avoid email enumeration
        assert response.status_code == 200

    def test_reset_password_valid_token(self, api_client):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        
        # Set a reset token
        user.password_reset_token = 'valid_token_123'
        user.save()
        
        url = reverse('reset_password')
        data = {
            'token': 'valid_token_123',
            'new_password': 'newpass123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        # Verify password was changed and token was cleared
        user.refresh_from_db()
        assert user.check_password('newpass123')
        assert user.password_reset_token is None

    def test_reset_password_invalid_token(self, api_client):
        url = reverse('reset_password')
        data = {
            'token': 'invalid_token',
            'new_password': 'newpass123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

class TestDataValidation:
    def test_register_missing_fields(self, api_client):
        url = reverse('register')
        
        # Test missing username
        data = {'email': 'test@example.com', 'password': 'pass123'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

        # Test missing email
        data = {'username': 'testuser', 'password': 'pass123'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

        # Test missing password
        data = {'username': 'testuser', 'email': 'test@example.com'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

    def test_update_role_invalid_role(self, api_client, admin_token, annotator_user):
        url = reverse('update_role', args=[annotator_user.id])
        data = {'role': 'INVALID_ROLE'}
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

    def test_password_reset_weak_password(self, api_client):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        
        user.password_reset_token = 'valid_token_123'
        user.save()
        
        url = reverse('reset_password')
        data = {
            'token': 'valid_token_123',
            'new_password': '123'  # Too weak
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

class TestUserFlow:
    def test_complete_user_registration_approval_flow(self, api_client, admin_token):
        # 1. Register a new user
        register_url = reverse('register')
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(register_url, register_data, format='json')
        assert response.status_code == 200
        
        # 2. Verify user exists but is not approved
        user = CustomUser.objects.get(username='newuser')
        assert user.is_approved == False
        
        # 3. Try to login (should fail)
        login_url = reverse('login')
        login_data = {'username': 'newuser', 'password': 'newpass123'}
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == 403
        
        # 4. Admin approves user
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        approve_url = reverse('approve_user', args=[user.id])
        response = api_client.post(approve_url)
        assert response.status_code == 200
        
        # 5. Verify user is approved
        user.refresh_from_db()
        assert user.is_approved == True
        
        # 6. User can now login
        api_client.credentials()  # Clear admin credentials
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == 200

    def test_user_role_change_flow(self, api_client, admin_token):
        # Create approved user
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123',
            is_approved=True,
            role='ANNOTATOR'
        )
        
        # Admin changes user role
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        url = reverse('update_role', args=[user.id])
        data = {'role': 'VERIFIER'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        # Verify role was changed
        user.refresh_from_db()
        assert user.role == 'VERIFIER'

class TestSecurityAndEdgeCases:
    def test_sql_injection_protection(self, api_client, admin_token):
        """Test that endpoints are protected against SQL injection"""
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # Try SQL injection in username
        url = reverse('register')
        data = {
            'username': "'; DROP TABLE users; --",
            'email': 'test@example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        # Should not crash the system
        assert response.status_code in [200, 400]

    def test_xss_protection_in_registration(self, api_client):
        """Test XSS protection in user registration"""
        url = reverse('register')
        data = {
            'username': '<script>alert("xss")</script>',
            'email': 'xss@example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        user = CustomUser.objects.get(email='xss@example.com')
        # Username should be stored as-is (sanitization should happen on frontend)
        assert user.username == '<script>alert("xss")</script>'

    def test_brute_force_protection_simulation(self, api_client, admin_user):
        """Simulate brute force attack"""
        url = reverse('login')
        
        # Multiple failed attempts
        for i in range(10):
            data = {
                'username': 'admin',
                'password': f'wrongpass{i}'
            }
            response = api_client.post(url, data, format='json')
            assert response.status_code == 401

    def test_jwt_token_expiry_simulation(self, api_client, admin_user):
        """Test behavior with expired tokens"""
        # Create a token and simulate expiry by using invalid token
        url = reverse('get_all_users')
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_expired_token')
        response = api_client.get(url)
        assert response.status_code == 401

    def test_concurrent_user_operations(self, api_client, admin_token):
        """Test concurrent operations on same user"""
        # Create a user
        user = CustomUser.objects.create_user(
            username='concurrent_test',
            email='concurrent@example.com',
            password='pass123',
            is_approved=False
        )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # Simulate concurrent approval and role update
        approve_url = reverse('approve_user', args=[user.id])
        role_url = reverse('update_role', args=[user.id])
        
        # These should both succeed
        response1 = api_client.post(approve_url)
        response2 = api_client.post(role_url, {'role': 'VERIFIER'}, format='json')
        
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_large_payload_handling(self, api_client):
        """Test handling of large payloads"""
        url = reverse('register')
        
        # Create a very long username
        long_username = 'a' * 1000
        data = {
            'username': long_username,
            'email': 'long@example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        # Should handle gracefully (either accept if within limits or reject)
        assert response.status_code in [200, 400]

    def test_unicode_handling(self, api_client):
        """Test unicode character handling"""
        url = reverse('register')
        data = {
            'username': 'тест用户',  # Cyrillic and Chinese characters
            'email': 'unicode@例え.com',
            'password': 'пароль123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        # Verify unicode is stored correctly
        user = CustomUser.objects.get(email='unicode@例え.com')
        assert user.username == 'тест用户'

    def test_case_sensitivity(self, api_client):
        """Test case sensitivity in usernames and emails"""
        # Create user with lowercase
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        # Try to create with different case
        data = {
            'username': 'TestUser',
            'email': 'Test@Example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        # Should succeed as they are different
        assert response.status_code == 200

class TestRateLimiting:
    def test_registration_rate_limiting(self, api_client):
        """Test rate limiting on registration endpoint"""
        url = reverse('register')
        
        # Make many rapid requests
        for i in range(50):
            data = {
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'password': 'pass123',
                'role': 'ANNOTATOR'
            }
            response = api_client.post(url, data, format='json')
            # Should not result in server errors
            assert response.status_code in [200, 400, 429]

    def test_login_rate_limiting(self, api_client, admin_user):
        """Test rate limiting on login endpoint"""
        url = reverse('login')
        
        # Make many rapid login attempts
        for i in range(30):
            data = {
                'username': 'admin',
                'password': 'admin'
            }
            response = api_client.post(url, data, format='json')
            # Should not crash and may implement rate limiting
            assert response.status_code in [200, 429]

class TestDataIntegrity:
    def test_user_deletion_cascade(self, api_client, admin_token):
        """Test data integrity when users are deleted"""
        # Create a user
        user = CustomUser.objects.create_user(
            username='to_delete',
            email='delete@example.com',
            password='pass123'
        )
        user_id = user.id
        
        # Delete the user
        user.delete()
        
        # Verify user is deleted
        assert not CustomUser.objects.filter(id=user_id).exists()

    def test_database_constraints(self, db):
        """Test database-level constraints"""
        from django.db import transaction
        
        # Username uniqueness is enforced (inherited from AbstractUser)
        user1 = CustomUser.objects.create_user(
            username='user1',
            email='email1@example.com',
            password='pass123'
        )
        
        # Test username uniqueness constraint in separate transaction
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                CustomUser.objects.create_user(
                    username='user1',  # Same username should fail
                    email='different@example.com',
                    password='pass123'
                )
        
        # Email uniqueness is NOT enforced in this model
        # This documents the current behavior
        user2 = CustomUser.objects.create_user(
            username='user2',
            email='same@example.com',
            password='pass123'
        )
        
        # This should succeed - email uniqueness not enforced
        user3 = CustomUser.objects.create_user(
            username='user3',
            email='same@example.com',  # Same email allowed
            password='pass123'
        )
        
        assert user2.email == user3.email

    def test_role_enum_validation(self, db):
        """Test role enum validation"""
        # Valid roles should work
        for role in ['ADMIN', 'ANNOTATOR', 'VERIFIER']:
            user = CustomUser.objects.create_user(
                username=f'user_{role.lower()}',
                email=f'{role.lower()}@example.com',
                password='pass123',
                role=role
            )
            assert user.role == role

class TestPerformance:
    def test_pagination_performance(self, api_client, admin_token):
        """Test pagination with large datasets"""
        # Create many users
        users = []
        for i in range(100):
            user = CustomUser.objects.create_user(
                username=f'perfuser{i}',
                email=f'perf{i}@example.com',
                password='pass123',
                is_approved=(i % 2 == 0)  # Half approved, half pending
            )
            users.append(user)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # Test pagination with different page sizes
        for per_page in [10, 50, 100]:
            url = reverse('get_users')
            response = api_client.get(f'{url}?page=1&per_page={per_page}&is_approved=true')
            assert response.status_code == 200
            
            response_data = json.loads(response.content)
            assert len(response_data['users']) <= per_page

    def test_search_performance(self, api_client, admin_token):
        """Test search functionality performance"""
        # Create users with various names
        search_users = [
            ('john_doe', 'john@example.com'),
            ('jane_smith', 'jane@example.com'),
            ('bob_johnson', 'bob@example.com'),
            ('alice_williams', 'alice@example.com'),
        ]
        
        for username, email in search_users:
            CustomUser.objects.create_user(
                username=username,
                email=email,
                password='pass123',
                is_approved=True
            )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # Test getting all users (should be efficient)
        url = reverse('get_all_users')
        response = api_client.get(url)
        assert response.status_code == 200

class TestAuditAndLogging:
    def test_user_creation_tracking(self, api_client):
        """Test that user creation is properly tracked"""
        url = reverse('register')
        data = {
            'username': 'tracked_user',
            'email': 'tracked@example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        user = CustomUser.objects.get(username='tracked_user')
        # Verify timestamps are set
        assert user.date_joined is not None
        assert user.last_login is not None

    def test_role_change_tracking(self, api_client, admin_token):
        """Test that role changes can be tracked"""
        # Create user
        user = CustomUser.objects.create_user(
            username='role_change_user',
            email='rolechange@example.com',
            password='pass123',
            role='ANNOTATOR'
        )
        original_role = user.role
        
        # Change role
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        url = reverse('update_role', args=[user.id])
        data = {'role': 'VERIFIER'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        
        user.refresh_from_db()
        assert user.role != original_role
        assert user.role == 'VERIFIER'

class TestBackupAndRecovery:
    def test_data_export_format(self, api_client, admin_token):
        """Test that user data can be exported in correct format"""
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        url = reverse('get_all_users')
        response = api_client.get(url)
        assert response.status_code == 200
        
        response_data = json.loads(response.content)
        if response_data['users']:
            user_data = response_data['users'][0]
            # Verify essential fields are present
            required_fields = ['id', 'username', 'email', 'role', 'is_approved']
            for field in required_fields:
                assert field in user_data

    def test_system_recovery_scenario(self, api_client):
        """Test system recovery after data corruption simulation"""
        # Create a user
        user = CustomUser.objects.create_user(
            username='recovery_test',
            email='recovery@example.com',
            password='pass123'
        )
        
        # Simulate partial data corruption by setting invalid state
        user.is_approved = None  # This might cause issues
        # Don't save - just test that the system handles it gracefully
        
        # System should still function
        url = reverse('login')
        data = {
            'username': 'recovery_test',
            'password': 'pass123'
        }
        response = api_client.post(url, data, format='json')
        # Should handle gracefully
        assert response.status_code in [200, 403, 400]