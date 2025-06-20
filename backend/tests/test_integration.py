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
        email='admin@example.com',
        password='adminpass123',
        is_approved=True,
        role='ADMIN'
    )

@pytest.fixture
def admin_tokens(admin_user):
    refresh = RefreshToken.for_user(admin_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class TestCompleteUserWorkflow:
    """Test complete user lifecycle workflows"""
    
    def test_complete_user_registration_to_login_workflow(self, api_client, admin_tokens):
        """Test complete workflow from registration to login"""
        # Step 1: User registers
        register_url = reverse('register')
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(register_url, register_data, format='json')
        assert response.status_code == 200
        
        # Verify user exists but is not approved
        user = CustomUser.objects.get(username='newuser')
        assert user.is_approved == False
        
        # Step 2: User tries to login (should fail)
        login_url = reverse('login')
        login_data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == 403
        
        # Step 3: Admin views pending users
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        pending_url = reverse('pending_users')
        response = api_client.get(pending_url)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data['users']) == 1
        assert response_data['users'][0]['username'] == 'newuser'
        
        # Step 4: Admin approves user
        approve_url = reverse('approve_user', args=[user.id])
        response = api_client.post(approve_url)
        assert response.status_code == 200
        
        # Verify user is approved
        user.refresh_from_db()
        assert user.is_approved == True
        
        # Step 5: User can now login
        api_client.credentials()  # Clear admin credentials
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert 'token' in response_data
        assert response_data['user']['username'] == 'newuser'

    def test_admin_user_management_workflow(self, api_client, admin_tokens):
        """Test admin managing multiple users workflow"""
        # Create multiple users with different statuses
        users_data = [
            ('pending1', 'pending1@example.com', 'ANNOTATOR', False),
            ('pending2', 'pending2@example.com', 'VERIFIER', False),
            ('approved1', 'approved1@example.com', 'ANNOTATOR', True),
        ]
        
        created_users = []
        for username, email, role, is_approved in users_data:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password='pass123',
                role=role,
                is_approved=is_approved
            )
            created_users.append(user)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        
        # Step 1: Admin views all users
        all_users_url = reverse('get_all_users')
        response = api_client.get(all_users_url)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data['users']) >= 3
        
        # Step 2: Admin views pending users
        pending_url = reverse('pending_users')
        response = api_client.get(pending_url)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        pending_usernames = [user['username'] for user in response_data['users']]
        assert 'pending1' in pending_usernames
        assert 'pending2' in pending_usernames
        assert 'approved1' not in pending_usernames
        
        # Step 3: Admin approves pending users
        for user in created_users:
            if not user.is_approved:
                approve_url = reverse('approve_user', args=[user.id])
                response = api_client.post(approve_url)
                assert response.status_code == 200
        
        # Step 4: Admin changes user roles
        role_update_url = reverse('update_role', args=[created_users[0].id])
        role_data = {'role': 'ADMIN'}
        response = api_client.post(role_update_url, role_data, format='json')
        assert response.status_code == 200
        
        # Verify role was changed
        created_users[0].refresh_from_db()
        assert created_users[0].role == 'ADMIN'
        
        # Step 5: Verify all users are now approved
        for user in created_users:
            user.refresh_from_db()
            assert user.is_approved == True

    def test_password_reset_workflow(self, api_client):
        """Test complete password reset workflow"""
        # Step 1: Create user
        user = CustomUser.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='oldpass123',
            is_approved=True
        )
        
        # Step 2: User requests password reset
        reset_request_url = reverse('request_password_reset')
        reset_request_data = {'email': 'reset@example.com'}
        response = api_client.post(reset_request_url, reset_request_data, format='json')
        assert response.status_code == 200
        
        # Verify reset token was set
        user.refresh_from_db()
        assert user.password_reset_token is not None
        reset_token = user.password_reset_token
        
        # Step 3: User resets password with token
        reset_password_url = reverse('reset_password')
        reset_password_data = {
            'token': reset_token,
            'new_password': 'newpass123'
        }
        response = api_client.post(reset_password_url, reset_password_data, format='json')
        assert response.status_code == 200
        
        # Verify password was changed and token was cleared
        user.refresh_from_db()
        assert user.check_password('newpass123') == True
        assert user.check_password('oldpass123') == False
        assert user.password_reset_token is None
        
        # Step 4: User can login with new password
        login_url = reverse('login')
        login_data = {
            'username': 'resetuser',
            'password': 'newpass123'
        }
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == 200

class TestErrorRecoveryWorkflows:
    """Test error recovery and edge case workflows"""
    
    def test_duplicate_registration_recovery(self, api_client):
        """Test handling of duplicate registration attempts"""
        # Create initial user
        CustomUser.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='pass123'
        )
        
        # Attempt duplicate registration
        register_url = reverse('register')
        duplicate_data = {
            'username': 'existinguser',
            'email': 'different@example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(register_url, duplicate_data, format='json')
        assert response.status_code == 400
        
        # User should be able to register with different username
        valid_data = {
            'username': 'newuser',
            'email': 'different@example.com',
            'password': 'pass123',
            'role': 'ANNOTATOR'
        }
        response = api_client.post(register_url, valid_data, format='json')
        assert response.status_code == 200

    def test_invalid_token_recovery(self, api_client, admin_tokens):
        """Test recovery from invalid/expired tokens"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        # Should get 401 for invalid token
        url = reverse('get_all_users')
        response = api_client.get(url)
        assert response.status_code == 401
        
        # Should work with valid token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_concurrent_approval_workflow(self, api_client, admin_tokens):
        """Test concurrent operations on same user"""
        # Create pending user
        user = CustomUser.objects.create_user(
            username='concurrent_test',
            email='concurrent@example.com',
            password='pass123',
            is_approved=False,
            role='ANNOTATOR'
        )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        
        # Perform concurrent operations
        approve_url = reverse('approve_user', args=[user.id])
        role_url = reverse('update_role', args=[user.id])
        
        # Both operations should succeed
        response1 = api_client.post(approve_url)
        response2 = api_client.post(role_url, {'role': 'VERIFIER'}, format='json')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify final state
        user.refresh_from_db()
        assert user.is_approved == True
        assert user.role == 'VERIFIER'

class TestScalabilityWorkflows:
    """Test workflows under high load scenarios"""
    
    def test_bulk_user_operations(self, api_client, admin_tokens):
        """Test bulk operations on multiple users"""
        # Create many users
        users = []
        for i in range(50):
            user = CustomUser.objects.create_user(
                username=f'bulkuser{i}',
                email=f'bulk{i}@example.com',
                password='pass123',
                is_approved=False,
                role='ANNOTATOR'
            )
            users.append(user)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        
        # Approve all users
        for user in users:
            approve_url = reverse('approve_user', args=[user.id])
            response = api_client.post(approve_url)
            assert response.status_code == 200
        
        # Verify all users are approved
        for user in users:
            user.refresh_from_db()
            assert user.is_approved == True

    def test_pagination_workflow(self, api_client, admin_tokens):
        """Test pagination with large datasets"""
        # Clear existing users to get consistent results
        CustomUser.objects.filter(username__startswith='pageuser').delete()
        
        # Create exactly 100 users with mixed approval status
        for i in range(100):
            CustomUser.objects.create_user(
                username=f'pageuser{i}',
                email=f'page{i}@example.com',
                password='pass123',
                is_approved=(i % 2 == 0),  # Half approved, half pending
                role='ANNOTATOR'
            )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        
        # Test pagination for approved users
        url = reverse('get_users')
        response = api_client.get(f'{url}?page=1&per_page=10&is_approved=true')
        assert response.status_code == 200
        
        response_data = json.loads(response.content)
        assert len(response_data['users']) == 10
        # Calculate expected pages based on actual approved users count
        approved_count = CustomUser.objects.filter(is_approved=True).count()
        expected_pages = (approved_count + 9) // 10  # Ceiling division
        assert response_data['pagination']['total_pages'] == expected_pages
        
        # Test pagination for pending users  
        response = api_client.get(f'{url}?page=1&per_page=10&is_approved=false')
        assert response.status_code == 200
        
        response_data = json.loads(response.content)
        assert len(response_data['users']) == 10
        # Calculate expected pages based on actual pending users count
        pending_count = CustomUser.objects.filter(is_approved=False).count()
        expected_pages = (pending_count + 9) // 10  # Ceiling division
        assert response_data['pagination']['total_pages'] == expected_pages

class TestSecurityWorkflows:
    """Test security-related workflows"""
    
    def test_unauthorized_access_workflow(self, api_client):
        """Test unauthorized access attempts"""
        protected_endpoints = [
            reverse('get_all_users'),
            reverse('pending_users'),
            reverse('get_users'),
        ]
        
        # Test without authentication
        for endpoint in protected_endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == 401
        
        # Test with invalid token
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        for endpoint in protected_endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == 401

    def test_role_based_access_workflow(self, api_client):
        """Test role-based access control workflow"""
        # Create users with different roles
        annotator = CustomUser.objects.create_user(
            username='annotator',
            email='annotator@example.com',
            password='pass123',
            is_approved=True,
            role='ANNOTATOR'
        )
        
        admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123',
            is_approved=True,
            role='ADMIN'
        )
        
        # Get tokens for both users
        annotator_refresh = RefreshToken.for_user(annotator)
        admin_refresh = RefreshToken.for_user(admin)
        
        annotator_token = str(annotator_refresh.access_token)
        admin_token = str(admin_refresh.access_token)
        
        # Test annotator access (should be restricted)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {annotator_token}')
        response = api_client.get(reverse('get_all_users'))
        assert response.status_code == 403
        
        # Test admin access (should work)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = api_client.get(reverse('get_all_users'))
        assert response.status_code == 200

class TestDataConsistencyWorkflows:
    """Test data consistency across operations"""
    
    def test_user_state_consistency(self, api_client, admin_tokens):
        """Test that user state remains consistent across operations"""
        # Create user
        user = CustomUser.objects.create_user(
            username='consistency_test',
            email='consistency@example.com',
            password='pass123',
            is_approved=False,
            role='ANNOTATOR'
        )
        
        original_id = user.id
        original_email = user.email
        original_username = user.username
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        
        # Perform multiple operations
        # 1. Approve user
        approve_url = reverse('approve_user', args=[user.id])
        response = api_client.post(approve_url)
        assert response.status_code == 200
        
        # 2. Change role
        role_url = reverse('update_role', args=[user.id])
        response = api_client.post(role_url, {'role': 'ADMIN'}, format='json')
        assert response.status_code == 200
        
        # Verify consistency
        user.refresh_from_db()
        assert user.id == original_id
        assert user.email == original_email
        assert user.username == original_username
        assert user.is_approved == True
        assert user.role == 'ADMIN'
        
        # Verify user can login
        api_client.credentials()  # Clear admin credentials
        login_url = reverse('login')
        login_data = {
            'username': original_username,
            'password': 'pass123'
        }
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == 200
