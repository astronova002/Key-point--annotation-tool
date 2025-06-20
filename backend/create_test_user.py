#!/usr/bin/env python
import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from user_auth.models import CustomUser

# Create test admin user
admin_user, created = CustomUser.objects.get_or_create(
    username='testadmin',
    defaults={
        'email': 'testadmin@example.com',
        'is_approved': True,
        'role': CustomUser.Role.ADMIN,
        'is_staff': True,
        'is_superuser': True
    }
)

if created:
    admin_user.set_password('testpass123')
    admin_user.save()
    print("Test admin user created successfully!")
    print("Username: testadmin")
    print("Password: testpass123")
    print("Role: ADMIN")
else:
    # Update existing user
    admin_user.is_approved = True
    admin_user.role = CustomUser.Role.ADMIN
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.set_password('testpass123')
    admin_user.save()
    print("Test admin user updated successfully!")
    print("Username: testadmin")
    print("Password: testpass123")
    print("Role: ADMIN")
