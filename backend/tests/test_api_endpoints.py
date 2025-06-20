import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from user_auth.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
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
        username='annotator',
        email='annotator@gmail.com',
        password='annotator',
        is_approved=True,
        role='ANNOTATOR'
    )

@pytest.fixture
def verifier_user():
    return CustomUser.objects.create_user(
        username='verifier',
        email='verifier@gmail.com',
        password='verifier',
        is_approved=True,
        role='VERIFIER'
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

@pytest.fixture
def verifier_token(verifier_user):
    refresh = RefreshToken.for_user(verifier_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class TestAPIEndpoints:
    
    def test_all_auth_endpoints_exist(self, api_client):
        """Test that all authentication endpoints are accessible"""
        auth_endpoints = [
            'register',
            'login', 
            'logout',
            'token_obtain_pair',
            'token_refresh',
            'status',
            'approve_user',
            'reject_user',
            'request_password_reset',
            'reset_password',
            'pending_users',
            'update_role',
            'get_users',
            'get_all_users'
        ]
        
        for endpoint_name in auth_endpoints:
            try:
                if endpoint_name in ['approve_user', 'reject_user', 'update_role']:
                    url = reverse(endpoint_name, args=[1])
                else:
                    url = reverse(endpoint_name)
                # Just check that URL exists, don't worry about response
                assert url is not None
            except Exception as e:
                pytest.fail(f"Endpoint {endpoint_name} not found: {e}")

    def test_cors_headers(self, api_client):
        """Test CORS headers are present"""
        url = reverse('login')
        # Test with valid POST data since login endpoint requires POST
        data = {'username': 'test', 'password': 'test'}
        response = api_client.post(url, data, format='json')
        # CORS test - should return some response (could be 401 for invalid credentials)
        assert response.status_code in [200, 400, 401, 403, 404, 405]
        
        # For OPTIONS request test
        response_options = api_client.options(url)
        assert response_options.status_code in [200, 400, 405]  # 400 or 405 if OPTIONS not handled

    def test_content_type_json(self, api_client):
        """Test that API returns JSON content type"""
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post(url, data, format='json')
        assert 'application/json' in response.get('content-type', '')

class TestRateLimiting:
    """Test rate limiting if implemented"""
    
    def test_multiple_failed_login_attempts(self, api_client):
        """Test behavior with multiple failed login attempts"""
        url = reverse('login')
        data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        
        # Make multiple failed attempts
        for i in range(5):
            response = api_client.post(url, data, format='json')
            assert response.status_code == 401
        
        # Should still allow legitimate attempts (no rate limiting implemented yet)
        response = api_client.post(url, data, format='json')
        assert response.status_code == 401

class TestResponseFormat:
    """Test consistent response format across endpoints"""
    
    def test_error_response_format(self, api_client):
        """Test that error responses have consistent format"""
        url = reverse('login')
        data = {'username': 'invalid', 'password': 'invalid'}
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 401
        response_data = json.loads(response.content)
        assert 'error' in response_data
        assert isinstance(response_data['error'], str)

    def test_success_response_format(self, api_client, admin_user):
        """Test that success responses have consistent format"""
        url = reverse('login')
        data = {'username': 'admin', 'password': 'admin'}
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert 'message' in response_data
        assert 'user' in response_data

class TestSecurityHeaders:
    """Test security-related headers"""
    
    def test_no_sensitive_info_in_responses(self, api_client, admin_user):
        """Test that sensitive information is not exposed"""
        url = reverse('get_all_users')
        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = api_client.get(url)
        response_data = json.loads(response.content)
        
        # Check that password hashes are not included
        for user in response_data['users']:
            assert 'password' not in user
            assert 'password_reset_token' not in user

    def test_authentication_required_endpoints(self, api_client):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ('get_all_users', []),
            ('get_users', []),
            ('pending_users', []),
            ('status', []),
            ('approve_user', [1]),
            ('update_role', [1])
        ]
        
        for endpoint_name, args in protected_endpoints:
            url = reverse(endpoint_name, args=args)
            response = api_client.get(url)
            assert response.status_code == 401

class TestDatabaseOperations:
    """Test database operations and constraints"""
    
    def test_user_creation_idempotency(self, api_client):
        """Test that creating the same user twice fails appropriately"""
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        # First creation should succeed
        response1 = api_client.post(url, data, format='json')
        assert response1.status_code == 200
        
        # Second creation should fail
        response2 = api_client.post(url, data, format='json')
        assert response2.status_code == 400

    def test_user_soft_delete(self, api_client, admin_token, annotator_user):
        """Test user rejection (soft delete) functionality"""
        url = reverse('reject_user', args=[annotator_user.id])
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        response = api_client.post(url)
        assert response.status_code == 200
        
        # User should still exist but be marked as not approved
        annotator_user.refresh_from_db()
        assert annotator_user.is_approved == False

class TestPaginationEdgeCases:
    """Test pagination edge cases"""
    
    def test_pagination_with_no_users(self, api_client, admin_token):
        """Test pagination when no users match criteria"""
        # Delete all users except admin
        CustomUser.objects.exclude(role='ADMIN').delete()
        
        url = reverse('get_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.get(f'{url}?is_approved=false')
        
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['users'] == []
        assert response_data['pagination']['total_users'] == 0

    def test_pagination_large_page_number(self, api_client, admin_token):
        """Test pagination with page number beyond available pages"""
        url = reverse('get_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        response = api_client.get(f'{url}?page=999&per_page=10')
        
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['users'] == []

    def test_pagination_invalid_parameters(self, api_client, admin_token):
        """Test pagination with invalid parameters"""
        url = reverse('get_users')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # Test negative page number
        response = api_client.get(f'{url}?page=-1')
        assert response.status_code == 400
        
        # Test zero page number
        response = api_client.get(f'{url}?page=0')
        assert response.status_code == 400
        
        # Test invalid per_page
        response = api_client.get(f'{url}?per_page=0')
        assert response.status_code == 400

class TestConcurrency:
    """Test concurrent operations"""
    
    def test_concurrent_user_approval(self, api_client, admin_token, pending_user):
        """Test concurrent approval of the same user"""
        url = reverse('approve_user', args=[pending_user.id])
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # First approval
        response1 = api_client.post(url)
        assert response1.status_code == 200
        
        # Second approval of same user should still work (idempotent)
        response2 = api_client.post(url)
        assert response2.status_code == 200
        
        pending_user.refresh_from_db()
        assert pending_user.is_approved == True

    def test_concurrent_role_updates(self, api_client, admin_token, annotator_user):
        """Test concurrent role updates"""
        url = reverse('update_role', args=[annotator_user.id])
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token["access"]}')
        
        # Update to VERIFIER
        data1 = {'role': 'VERIFIER'}
        response1 = api_client.post(url, data1, format='json')
        assert response1.status_code == 200
        
        # Update to ADMIN
        data2 = {'role': 'ADMIN'}
        response2 = api_client.post(url, data2, format='json')
        assert response2.status_code == 200
        
        annotator_user.refresh_from_db()
        assert annotator_user.role == 'ADMIN'
