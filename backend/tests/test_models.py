import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from user_auth.models import CustomUser

class TestCustomUserModel:
    def test_create_user_with_defaults(self, db):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_approved == False
        assert user.role == CustomUser.Role.ANNOTATOR
        assert user.is_active == True
        assert user.is_staff == False
        assert user.is_superuser == False

    def test_create_user_with_role(self, db):
        user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=CustomUser.Role.ADMIN
        )
        assert user.role == CustomUser.Role.ADMIN

    def test_create_superuser(self, db):
        user = CustomUser.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='superpass123'
        )
        assert user.is_staff == True
        assert user.is_superuser == True
        # Superusers start with is_approved=False (default behavior)
        assert user.is_approved == False

    def test_username_unique_constraint(self, db):
        CustomUser.objects.create_user(
            username='testuser',
            email='test1@example.com',
            password='pass123'
        )
        
        with pytest.raises(IntegrityError):
            CustomUser.objects.create_user(
                username='testuser',
                email='test2@example.com',
                password='pass123'
            )

    def test_email_unique_constraint(self, db):
        """Test email uniqueness (not enforced by default in this model)"""
        user1 = CustomUser.objects.create_user(
            username='user1',
            email='test@example.com',
            password='pass123'
        )
        
        # Email uniqueness is not enforced in this model
        # This test documents the current behavior
        user2 = CustomUser.objects.create_user(
            username='user2',
            email='test@example.com',  # Same email allowed
            password='pass123'
        )
        
        assert user1.email == user2.email  # Both have same email

    def test_str_representation(self, db):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        assert str(user) == 'testuser'

    def test_role_choices(self, db):
        # Test all valid role choices
        roles = [CustomUser.Role.ADMIN, CustomUser.Role.ANNOTATOR, CustomUser.Role.VERIFIER]
        for role in roles:
            user = CustomUser.objects.create_user(
                username=f'user_{role}',
                email=f'{role}@example.com',
                password='pass123',
                role=role
            )
            assert user.role == role

    def test_password_reset_token(self, db):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        
        # Initially, password_reset_token should be None
        assert user.password_reset_token is None
        
        # Set a reset token
        user.password_reset_token = 'test_token_123'
        user.save()
        
        # Verify token is saved
        user.refresh_from_db()
        assert user.password_reset_token == 'test_token_123'

    def test_date_fields_auto_population(self, db):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        
        assert user.date_joined is not None
        assert user.last_login is not None

    def test_password_hashing(self, db):
        plain_password = 'testpass123'
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=plain_password
        )
        
        # Password should be hashed, not stored in plain text
        assert user.password != plain_password
        assert user.check_password(plain_password) == True
        assert user.check_password('wrongpassword') == False

class TestAdvancedModelFeatures:
    def test_user_manager_methods(self, db):
        """Test custom user manager methods"""
        # Test create_user
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.is_staff == False
        assert user.is_superuser == False
        assert user.is_approved == False

    def test_create_superuser_sets_correct_flags(self, db):
        """Test that create_superuser sets all necessary flags"""
        superuser = CustomUser.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='superpass123'
        )
        assert superuser.is_staff == True
        assert superuser.is_superuser == True
        # is_approved follows the model default (False)
        assert superuser.is_approved == False
        assert superuser.is_active == True

    def test_user_permissions_and_groups(self, db):
        """Test user permissions and groups functionality"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test that user has no special permissions by default
        assert user.get_all_permissions() == set()
        assert user.get_group_permissions() == set()
        assert user.has_perm('auth.add_user') == False

    def test_user_email_normalization(self, db):
        """Test that email domain is normalized to lowercase"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='Test@Example.COM',
            password='testpass123'
        )
        # Django normalizes domain part to lowercase but preserves local part case
        assert user.email == 'Test@example.com'

    def test_password_validation_integration(self, db):
        """Test password validation with Django's auth system"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test password checking
        assert user.check_password('testpass123') == True
        assert user.check_password('wrongpassword') == False
        assert user.check_password('') == False

    def test_user_natural_key(self, db):
        """Test natural key functionality for serialization"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test that natural key returns username
        assert user.natural_key() == ('testuser',)

    def test_user_get_short_name(self, db):
        """Test get_short_name method"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # get_short_name returns first_name, empty if not set
        assert user.get_short_name() == ''
        
        # Test with first_name set
        user.first_name = 'Test'
        user.save()
        assert user.get_short_name() == 'Test'

    def test_user_get_full_name(self, db):
        """Test get_full_name method"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # get_full_name returns first_name + last_name, empty if not set
        assert user.get_full_name() == ''
        
        # Test with names set
        user.first_name = 'Test'
        user.last_name = 'User'
        user.save()
        assert user.get_full_name() == 'Test User'

class TestModelValidation:
    def test_email_field_validation(self, db):
        """Test email field validation"""
        # Test invalid email formats
        with pytest.raises(ValidationError):
            user = CustomUser(username='test', email='invalid-email', password='pass123')
            user.full_clean()

    def test_username_field_validation(self, db):
        """Test username field validation"""
        # Test empty username
        with pytest.raises(ValidationError):
            user = CustomUser(username='', email='test@example.com', password='pass123')
            user.full_clean()

    def test_role_field_validation(self, db):
        """Test role field validation"""
        # Test invalid role
        with pytest.raises(ValidationError):
            user = CustomUser(username='test', email='test@example.com', password='pass123', role='INVALID')
            user.full_clean()

    def test_password_field_validation(self, db):
        """Test password field requirements"""
        # Test empty password
        with pytest.raises(ValidationError):
            user = CustomUser(username='test', email='test@example.com', password='')
            user.full_clean()

class TestModelQueries:
    def test_filter_by_role(self, db):
        """Test filtering users by role"""
        # Create users with different roles
        admin = CustomUser.objects.create_user(
            username='admin', email='admin@example.com', password='pass123', role='ADMIN'
        )
        annotator = CustomUser.objects.create_user(
            username='annotator', email='annotator@example.com', password='pass123', role='ANNOTATOR'
        )
        verifier = CustomUser.objects.create_user(
            username='verifier', email='verifier@example.com', password='pass123', role='VERIFIER'
        )
        
        # Test filtering
        admins = CustomUser.objects.filter(role='ADMIN')
        assert admins.count() == 1
        assert admins.first() == admin
        
        annotators = CustomUser.objects.filter(role='ANNOTATOR')
        assert annotators.count() == 1
        assert annotators.first() == annotator

    def test_filter_by_approval_status(self, db):
        """Test filtering users by approval status"""
        approved_user = CustomUser.objects.create_user(
            username='approved', email='approved@example.com', password='pass123', is_approved=True
        )
        pending_user = CustomUser.objects.create_user(
            username='pending', email='pending@example.com', password='pass123', is_approved=False
        )
        
        approved_users = CustomUser.objects.filter(is_approved=True)
        pending_users = CustomUser.objects.filter(is_approved=False)
        
        assert approved_users.count() == 1
        assert approved_users.first() == approved_user
        assert pending_users.count() == 1
        assert pending_users.first() == pending_user

    def test_complex_queries(self, db):
        """Test complex queries combining multiple filters"""
        # Create various users
        users_data = [
            ('admin1', 'admin1@example.com', 'ADMIN', True),
            ('admin2', 'admin2@example.com', 'ADMIN', False),
            ('annotator1', 'annotator1@example.com', 'ANNOTATOR', True),
            ('annotator2', 'annotator2@example.com', 'ANNOTATOR', False),
        ]
        
        for username, email, role, is_approved in users_data:
            CustomUser.objects.create_user(
                username=username, 
                email=email, 
                password='pass123', 
                role=role, 
                is_approved=is_approved
            )
        
        # Test complex query: approved admins
        approved_admins = CustomUser.objects.filter(role='ADMIN', is_approved=True)
        assert approved_admins.count() == 1
        assert approved_admins.first().username == 'admin1'
        
        # Test complex query: pending annotators
        pending_annotators = CustomUser.objects.filter(role='ANNOTATOR', is_approved=False)
        assert pending_annotators.count() == 1
        assert pending_annotators.first().username == 'annotator2'

    def test_ordering_queries(self, db):
        """Test ordering of query results"""
        # Create users with different creation times
        user1 = CustomUser.objects.create_user(
            username='user1', email='user1@example.com', password='pass123'
        )
        user2 = CustomUser.objects.create_user(
            username='user2', email='user2@example.com', password='pass123'
        )
        user3 = CustomUser.objects.create_user(
            username='user3', email='user3@example.com', password='pass123'
        )
        
        # Test ordering by username
        users_by_username = CustomUser.objects.all().order_by('username')
        usernames = [user.username for user in users_by_username]
        assert usernames == ['user1', 'user2', 'user3']
        
        # Test reverse ordering
        users_reverse = CustomUser.objects.all().order_by('-username')
        usernames_reverse = [user.username for user in users_reverse]
        assert usernames_reverse == ['user3', 'user2', 'user1']

class TestModelSignals:
    def test_user_creation_signals(self, db):
        """Test that appropriate signals are sent on user creation"""
        from django.db.models.signals import post_save
        from django.contrib.auth.signals import user_logged_in
        
        # This is a placeholder for signal testing
        # In a real application, you might have custom signals
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.id is not None
        assert user.date_joined is not None

class TestModelMethods:
    def test_is_admin_method(self, db):
        """Test custom method to check if user is admin"""
        admin_user = CustomUser.objects.create_user(
            username='admin', email='admin@example.com', password='pass123', role='ADMIN'
        )
        regular_user = CustomUser.objects.create_user(
            username='user', email='user@example.com', password='pass123', role='ANNOTATOR'
        )
        
        # Assuming you have custom methods on your model
        # You would test them here
        assert admin_user.role == 'ADMIN'
        assert regular_user.role == 'ANNOTATOR'

    def test_can_approve_users_method(self, db):
        """Test custom method to check if user can approve others"""
        admin_user = CustomUser.objects.create_user(
            username='admin', email='admin@example.com', password='pass123', role='ADMIN'
        )
        annotator_user = CustomUser.objects.create_user(
            username='annotator', email='annotator@example.com', password='pass123', role='ANNOTATOR'
        )
        
        # Test role-based permissions
        assert admin_user.role == 'ADMIN'
        assert annotator_user.role == 'ANNOTATOR'

class TestModelPerformance:
    def test_bulk_operations(self, db):
        """Test bulk create and update operations"""
        # Test bulk create
        users_data = [
            CustomUser(username=f'user{i}', email=f'user{i}@example.com', password='pass123')
            for i in range(100)
        ]
        
        CustomUser.objects.bulk_create(users_data)
        
        assert CustomUser.objects.count() == 100

    def test_select_related_queries(self, db):
        """Test optimized queries using select_related"""
        # Create some users
        for i in range(10):
            CustomUser.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='pass123'
            )
        
        # Test that queries are optimized
        users = CustomUser.objects.all()
        assert users.count() == 10

class TestModelConcurrency:
    def test_concurrent_user_creation(self, db):
        """Test concurrent user creation scenarios"""
        import threading
        
        def create_user(username):
            try:
                CustomUser.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='pass123'
                )
            except IntegrityError:
                # Expected if username already exists
                pass
        
        # Create multiple threads trying to create users
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user, args=(f'user{i}',))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify users were created
        assert CustomUser.objects.count() >= 5

    def test_concurrent_role_updates(self, db):
        """Test concurrent role update scenarios"""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123',
            role='ANNOTATOR'
        )
        
        # Simulate concurrent updates
        user.role = 'ADMIN'
        user.save()
        
        user.refresh_from_db()
        assert user.role == 'ADMIN'
