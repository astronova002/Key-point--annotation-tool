import os
import django
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from user_auth.models import CustomUser

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass

@pytest.fixture(autouse=True)
def setup_test_environment():
    # Set up any test environment variables or settings here
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ['*']

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        is_approved=True,
        role='ADMIN'
    )

@pytest.fixture
def annotator_user(db):
    return CustomUser.objects.create_user(
        username='annotator',
        email='annotator@example.com',
        password='annotatorpass123',
        is_approved=True,
        role='ANNOTATOR'
    )

@pytest.fixture
def pending_user(db):
    return CustomUser.objects.create_user(
        username='pending',
        email='pending@example.com',
        password='pendingpass123',
        is_approved=False,
        role='ANNOTATOR'
    )

@pytest.fixture
def admin_token(admin_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(admin_user)
    return str(refresh.access_token)

@pytest.fixture
def annotator_token(annotator_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(annotator_user)
    return str(refresh.access_token) 